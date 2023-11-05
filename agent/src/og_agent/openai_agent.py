# SPDX-FileCopyrightText: 2023 ghf5t565698```\\\\\\\\\-=[-[9oi86y53e12motai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import openai
import io
import json
import logging
import time
from pydantic import BaseModel, Field
from og_proto.agent_server_pb2 import OnStepActionStart, TaskResponse, OnStepActionEnd, FinalAnswer, TypingContent
from .base_agent import BaseAgent, TypingState, TaskContext
from .tokenizer import tokenize
from og_memory.memory import AgentMemoryOption
import tiktoken

logger = logging.getLogger(__name__)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


class OpenaiAgent(BaseAgent):

    def __init__(self, model, sdk, is_azure=True):
        super().__init__(sdk)
        self.model = model
        logger.info(f"use openai model {model} is_azure {is_azure}")
        self.is_azure = is_azure
        self.model_name = model if not is_azure else ""
        self.memory_option = AgentMemoryOption(
            show_function_instruction=False, disable_output_format=True
        )

    async def call_openai(self, agent_memory, queue, context, task_context, task_opt):
        """
        call the openai api
        """
        input_token_count = 0
        messages = agent_memory.to_messages()
        logger.debug(f"call openai with messages {messages}")
        for message in messages:
            if not message["content"]:
                continue
            input_token_count += len(encoding.encode(message["content"]))
        task_context.input_token_count += input_token_count
        start_time = time.time()
        if self.is_azure:
            response = await openai.ChatCompletion.acreate(
                engine=self.model,
                messages=messages,
                temperature=0,
                functions=agent_memory.get_functions(),
                function_call="auto",
                stream=True,
            )
        else:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0,
                functions=agent_memory.get_functions(),
                function_call="auto",
                stream=True,
            )
        message = await self.extract_message(
            response, queue, context, task_context, task_opt, start_time
        )
        return message

    async def handle_function(self, message, queue, context, task_context, task_opt):
        if "function_call" in message:
            if context.done():
                logging.debug("the client has cancelled the request")
                return
            function_name = message["function_call"]["name"]
            raw_code = ""
            code = ""
            explanation = ""
            saved_filenames = []
            language = "python"
            if function_name == "direct_message":
                arguments = json.loads(message["function_call"]["arguments"])
                await queue.put(
                    TaskResponse(
                        state=task_context.to_context_state_proto(),
                        response_type=TaskResponse.OnFinalAnswer,
                        final_answer=FinalAnswer(
                            answer=arguments["message"]
                            if not task_opt.streaming
                            else ""
                        ),
                        context_id=task_context.context_id,
                    )
                )
                return None
            if function_name == "python":
                raw_code = message["function_call"]["arguments"]
                logger.debug(f"call function {function_name} with args {code}")
                code = raw_code
            else:
                arguments = json.loads(message["function_call"]["arguments"])
                raw_code = arguments["code"]
                code = raw_code
                explanation = arguments["explanation"]
                saved_filenames = arguments.get("saved_filenames", [])
                language = arguments.get("language")
            if language == "bash":
                code = f"%%bash\n{raw_code}"

            tool_input = json.dumps({
                "code": raw_code,
                "explanation": explanation,
                "saved_filenames": saved_filenames,
                "language": language,
            })
            # send the respond to client
            await queue.put(
                TaskResponse(
                    state=task_context.to_context_state_proto(),
                    response_type=TaskResponse.OnStepActionStart,
                    on_step_action_start=OnStepActionStart(
                        input=tool_input, tool=function_name
                    ),
                    context_id=task_context.context_id,
                )
            )
            function_result = None
            async for (result, respond) in self.call_function(
                code, context, task_context
            ):
                if context.done():
                    logger.debug("the client has cancelled the request")
                    break
                function_result = result
                if respond and task_opt.streaming:
                    await queue.put(respond)
            return function_result
        else:
            raise Exception("bad message, function message expected")

    async def arun(self, request, queue, context, task_opt):
        """
        process the task
        """
        task = request.task
        context_id = (
            request.context_id
            if request.context_id
            else self.create_new_memory_with_default_prompt("", "")
        )
        task_context = TaskContext(
            start_time=time.time(),
            output_token_count=0,
            input_token_count=0,
            llm_name=self.model_name,
            llm_respond_duration=0,
            context_id=context_id,
        )
        if context_id not in self.agent_memories:
            await queue.put(
                TaskResponse(
                    state=task_context.to_context_state_proto(),
                    response_type=TaskResponse.OnSystemError,
                    error_msg="invalid context id",
                    context_id=context_id,
                )
            )
            return
        agent_memory = self.agent_memories[context_id]
        agent_memory.update_options(self.memory_option)
        agent_memory.append_chat_message(
            {"role": "user", "content": task},
        )
        try:
            while not context.done():
                if task_context.input_token_count >= task_opt.input_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnInputTokenLimitExceed,
                            error_msg="input token limit reached",
                            context_id=context_id,
                        )
                    )
                    break
                if task_context.output_token_count >= task_opt.output_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnOutputTokenLimitExceed,
                            error_msg="output token limit reached",
                            context_id=context_id,
                        )
                    )
                    break
                chat_message = await self.call_openai(
                    agent_memory, queue, context, task_context, task_opt
                )
                logger.debug(f"the response {chat_message}")
                if "function_call" in chat_message:
                    if "content" not in chat_message:
                        chat_message["content"] = None
                    if "role" not in chat_message:
                        chat_message["role"] = "assistant"
                    agent_memory.append_chat_message(chat_message)
                    function_result = await self.handle_function(
                        chat_message, queue, context, task_context, task_opt
                    )
                    if not function_result:
                        break
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnStepActionEnd,
                            on_step_action_end=OnStepActionEnd(
                                output=""
                                if task_opt.streaming
                                else function_result.console_stderr
                                + function_result.console_stdout,
                                output_files=function_result.saved_filenames,
                                has_error=function_result.has_error,
                            ),
                            context_id=context_id,
                        )
                    )
                    function_name = chat_message["function_call"]["name"]
                    # TODO optimize the token limitation
                    if function_result.has_result:
                        agent_memory.append_chat_message({
                            "role": "function",
                            "name": function_name,
                            "content": function_result.console_stdout[0:500],
                        })
                    elif function_result.has_error:
                        agent_memory.append_chat_message({
                            "role": "function",
                            "name": function_name,
                            "content": function_result.console_stderr[0:500],
                        })
                    else:
                        agent_memory.append_chat_message({
                            "role": "function",
                            "name": function_name,
                            "content": function_result.console_stdout[0:500],
                        })
                else:
                    # end task
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnFinalAnswer,
                            final_answer=FinalAnswer(
                                answer=chat_message["content"]
                                if not task_opt.streaming
                                else ""
                            ),
                            context_id=context_id,
                        )
                    )
                    break
        except Exception as ex:
            logging.exception("fail process task")
            response = TaskResponse(
                response_type=TaskResponse.OnSystemError,
                error_msg=str(ex),
                context_id=context_id,
            )
            await queue.put(response)
        finally:
            await queue.put(None)
