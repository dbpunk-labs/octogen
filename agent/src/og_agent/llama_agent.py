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
from .tokenizer import tokenize
from .prompt import OCTOGEN_CODELLAMA_SYSTEM
import tiktoken

logger = logging.getLogger(__name__)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


class LlamaAgent(BaseAgent):

    def __init__(self, client, kernel_sdk):
        super().__init__(kernel_sdk)
        self.client = client

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
                    input=tool_input, tool="execute_bash_code"
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

    async def handle_function(
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
                    input=tool_input, tool=json_response["action"]
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

    async def call_llama(self, messages, queue, context, task_context, task_opt):
        """
        call llama api
        """
        input_token_count = 0
        for message in messages:
            if not message["content"]:
                continue
            input_token_count += len(encoding.encode(message["content"]))
        task_context.input_token_count += input_token_count
        start_time = time.time()
        response = self.client.chat(messages, "codellama", max_tokens=2048)
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

    async def arun(self, question, queue, context, task_opt):
        """
        run the agent
        """
        messages = [
            {"role": "system", "content": OCTOGEN_CODELLAMA_SYSTEM},
            {"role": "user", "content": question},
        ]
        task_context = TaskContext(
            start_time=time.time(),
            output_token_count=0,
            input_token_count=0,
            llm_name="codellama",
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
                    messages,
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
                    json_response["action"]
                    in ["execute_python_code", "execute_bash_code"]
                    and json_response["code"]
                ):
                    messages.append(message)
                    tools_mapping = {
                        "execute_python_code": self.handle_function,
                        "execute_bash_code": self.handle_bash_code,
                    }
                    function_result = await tools_mapping[json_response["action"]](
                        json_response, queue, context, task_context, task_opt
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

                    action_output = "the output of %s:" % json_response["action"]
                    current_question = "Give me the final answer summary if the above output of action  meets the goal Otherwise try a new step"
                    if function_result.has_result:
                        messages.append({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stdout}",
                        })
                        messages.append({"role": "user", "content": current_question})
                    elif function_result.has_error:
                        messages.append({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stderr}",
                        })
                        current_question = f"Generate a new step to fix the above error"
                        messages.append({"role": "user", "content": current_question})
                    else:
                        messages.append({
                            "role": "user",
                            "content": f"{action_output} \n {function_result.console_stdout}",
                        })
                        messages.append({"role": "user", "content": current_question})
                elif (
                    json_response["action"] == "show_sample_code"
                    and json_response["code"]
                ):
                    await self.handle_show_sample_code(
                        json_response, queue, context, task_context
                    )
                    result = self._format_output(json_response)
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnFinalAnswer,
                            final_answer=FinalAnswer(answer=result),
                        )
                    )
                    break
                else:
                    result = self._format_output(json_response)
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnFinalAnswer,
                            final_answer=FinalAnswer(
                                answer=result if not task_opt.streaming else ""
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
