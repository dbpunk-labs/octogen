# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import json
import logging
import io
import time
from .llama_client import LlamaClient
from og_proto.agent_server_pb2 import OnStepActionStart, TaskResponse, OnStepActionEnd, FinalAnswer, TypingContent
from .base_agent import BaseAgent, TypingState, TaskContext
from og_memory.memory import AgentMemoryOption
from .prompt import FUNCTION_DIRECT_MESSAGE, FUNCTION_EXECUTE
from .tokenizer import tokenize
import tiktoken

logger = logging.getLogger(__name__)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


class LlamaAgent(BaseAgent):

    def __init__(self, client, kernel_sdk):
        super().__init__(kernel_sdk)
        self.client = client
        self.memory_option = AgentMemoryOption(
            show_function_instruction=True, disable_output_format=False
        )

    def _output_exception(self):
        return (
            "Sorry, the LLM did return nothing, You can use a better performance model"
        )


    def _format_output(self, json_response):
        """
        format the response and send it to the user
        """
        answer = json_response["explanation"]
        if json_response["action"] == "no_action":
            return answer
        elif json_response["action"] == "show_sample_code":
            return ""
        else:
            code = json_response.get("code", None)
            answer_code = """%s
```%s
%s
```
""" % (
                answer,
                json_response.get("language", "python"),
                code if code else "",
            )
            return answer_code

    async def handle_show_sample_code(
        self, json_response, queue, context, task_context
    ):
        code = json_response["code"]
        explanation = json_response["explanation"]
        saved_filenames = json_response.get("saved_filenames", [])
        tool_input = json.dumps({
            "code": code,
            "explanation": explanation,
            "saved_filenames": saved_filenames,
            "language": json_response.get("language", "text"),
        })
        await queue.put(
            TaskResponse(
                state=task_context.to_context_state_proto(),
                response_type=TaskResponse.OnStepActionStart,
                on_step_action_start=OnStepActionStart(
                    input=tool_input, tool="show_sample_code"
                ),
            )
        )

    async def handle_bash_code(
        self, json_response, queue, context, task_context, task_opt
    ):
        commands = json_response["code"]
        code = f"%%bash\n {commands}"
        explanation = json_response["explanation"]
        saved_filenames = json_response.get("saved_filenames", [])
        tool_input = json.dumps({
            "code": commands,
            "explanation": explanation,
            "saved_filenames": saved_filenames,
            "language": json_response.get("language"),
        })
        await queue.put(
            TaskResponse(
                state=task_context.to_context_state_proto(),
                response_type=TaskResponse.OnStepActionStart,
                on_step_action_start=OnStepActionStart(
                    input=tool_input, tool="execute"
                ),
            )
        )
        function_result = None
        async for (result, respond) in self.call_function(code, context, task_context):
            if context.done():
                logger.debug("the client has cancelled the request")
                break
            function_result = result
            if respond and task_opt.streaming:
                await queue.put(respond)
        return function_result

    async def handle_python_function(
        self, json_response, queue, context, task_context, task_opt
    ):
        code = json_response["code"]
        explanation = json_response["explanation"]
        saved_filenames = json_response.get("saved_filenames", [])
        tool_input = json.dumps({
            "code": code,
            "explanation": explanation,
            "saved_filenames": saved_filenames,
            "language": json_response.get("language"),
        })
        await queue.put(
            TaskResponse(
                state=task_context.to_context_state_proto(),
                response_type=TaskResponse.OnStepActionStart,
                on_step_action_start=OnStepActionStart(
                    input=tool_input, tool='execute'
                ),
            )
        )
        function_result = None
        async for (result, respond) in self.call_function(code, context, task_context):
            if context.done():
                logger.debug("the client has cancelled the request")
                break
            function_result = result
            if respond and task_opt.streaming:
                await queue.put(respond)
        return function_result

    async def call_llama(self, agent_memory, queue, context, task_context, task_opt):
        """
        call llama api
        """
        input_token_count = 0
        messages = agent_memory.to_messages()
        for message in messages:
            if not message["content"]:
                continue
            input_token_count += len(encoding.encode(message["content"]))
        task_context.input_token_count += input_token_count
        start_time = time.time()
        response = self.client.chat(messages, "llama", max_tokens=2048)
        message = await self.extract_message(
            response,
            queue,
            context,
            task_context,
            task_opt,
            start_time,
            is_json_format=True,
        )
        return message

    async def arun(self, request, queue, context, task_opt):
        """
        run the agent
        """
        question = request.task
        context_id = (
            request.context_id
            if request.context_id
            else self.create_new_memory_with_default_prompt("", "", actions=[FUNCTION_EXECUTE,
                                                                             FUNCTION_DIRECT_MESSAGE])
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
            {"role": "user", "content": question},
        )
        task_context = TaskContext(
            start_time=time.time(),
            output_token_count=0,
            input_token_count=0,
            llm_name="llama",
            llm_respond_duration=0,
        )
        try:
            while not context.done():
                if task_context.input_token_count >= task_opt.input_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnInputTokenLimitExceed,
                            error_msg=f"input token limit reached {task_opt.input_token_limit}",
                        )
                    )
                    break
                if task_context.output_token_count >= task_opt.output_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnOutputTokenLimitExceed,
                            error_msg=f"output token limit reached {task_opt.output_token_limit}",
                        )
                    )
                    break
                message = await self.call_llama(
                    agent_memory,
                    queue,
                    context,
                    task_context,
                    task_opt,
                )
                try:
                    json_response = json.loads(message["content"])
                    if not json_response:
                        await queue.put(
                            TaskResponse(
                                state=task_context.to_context_state_proto(),
                                response_type=TaskResponse.OnModelOutputError,
                                error_msg=self._output_exception(),
                            )
                        )
                        break
                except Exception as ex:
                    logger.exception(f"fail to load message the message is {message}")
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnModelOutputError,
                            error_msg=str(ex),
                        )
                    )
                    break
                logger.debug(f" llama response {json_response}")
                if (
                    'function_call'in json_response and json_response["function_call"] == "execute"
                ):
                    agent_memory.append_chat_message(message)
                    tools_mapping = {
                        "python": self.handle_python_function,
                        "bash": self.handle_bash_code,
                    }

                    function_result = await tools_mapping[json_response["arguments"]['language']](
                        json_response['arguments'], queue, context, task_context, task_opt
                    )

                    logger.debug(f"the function result {function_result}")
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
                        )
                    )
                    action_output = "the output of %s:" % json_response["function_call"]
                    current_question = "Give me the final answer summary if the above output of action  meets the goal Otherwise try a new step"
                    if function_result.has_result:
                        agent_memory.append_chat_message({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stdout}",
                        })
                        agent_memory.append_chat_message({"role": "user", "content": current_question})
                    elif function_result.has_error:
                        agent_memory.append_chat_message({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stderr}",
                        })
                        current_question = f"Generate a new step to fix the above error"
                        agent_memory.append_chat_message({"role": "user", "content": current_question})
                    else:
                        agent_memory.append_chat_message({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stdout}",
                        })
                        agent_memory.append_chat_message({
                            "role": "user", "content": current_question})
                elif 'function_call' in json_response and json_response["function_call"] == "direct_message":
                    message = json_response['arguments']['message']
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnFinalAnswer,
                            final_answer=FinalAnswer(
                                answer=message if not task_opt.streaming else ""
                            ),
                        )
                    )
                    break
        except Exception as ex:
            logger.exception("fail to run the agent")
            response = TaskResponse(
                response_type=TaskResponse.OnSystemError,
                error_msg=str(ex),
            )
            await queue.put(response)
        finally:
            await queue.put(None)
