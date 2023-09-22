# vim:fenc=utf-8
#
# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" """
import openai
import io
import json
import logging
from pydantic import BaseModel, Field
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .base_agent import BaseAgent, TypingState
from .tokenizer import tokenize

logger = logging.getLogger(__name__)

OCTOPUS_FUNCTIONS = [
    {
        "name": "execute_python_code",
        "description": "Safely execute arbitrary Python code and return the result, stdout, and stderr.",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "the explanation about the python code",
                },
                "code": {
                    "type": "string",
                    "description": "the python code to be executed",
                },
                "saved_filenames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of filenames that were created by the code",
                },
            },
            "required": ["explanation", "code"],
        },
    },
    {
        "name": "python",
        "description": "this function must not be used",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "the explanation about the python code",
                },
                "code": {
                    "type": "string",
                    "description": "the python code to be executed",
                },
                "saved_filenames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of filenames that were created by the code",
                },
            },
            "required": ["explanation", "code"],
        },
    },
]


class OpenaiAgent(BaseAgent):

    def __init__(self, model, system_prompt, sdk, is_azure=True):
        super().__init__(sdk)
        self.model = model
        self.system_prompt = system_prompt
        logger.info(f"use openai model {model}")
        logger.info(f"use openai with system prompt {system_prompt}")
        self.is_azure = True

    def _merge_delta_for_function_call(self, message, delta):
        if not delta:
            return
        if "function_call" not in message:
            message["function_call"] = delta["function_call"]
            return
        old_arguments = message["function_call"].get("arguments", "")
        if delta["function_call"]["arguments"]:
            message["function_call"]["arguments"] = (
                old_arguments + delta["function_call"]["arguments"]
            )

    def _merge_delta_for_content(self, message, delta):
        if not delta:
            return
        content = message.get("content", "")
        if delta.get("content"):
            message["content"] = content + delta["content"]

    def _get_function_call_argument_new_typing(self, message):
        arguments = message["function_call"].get("arguments", "")
        state = TypingState.START
        explanation_str = ""
        code_str = ""
        for token_state, token in tokenize(io.StringIO(arguments)):
            if token_state == None:
                if state == TypingState.EXPLANATION and token[0] == 1:
                    explanation_str = token[1]
                    state = TypingState.START
                if state == TypingState.CODE and token[0] == 1:
                    code_str = token[1]
                    state = TypingState.START
                if token[1] == "explanation":
                    state = TypingState.EXPLANATION
                if token[1] == "code":
                    state = TypingState.CODE
            else:
                # String
                if token_state == 9 and state == TypingState.EXPLANATION:
                    explanation_str = "".join(token)
                elif token_state == 9 and state == TypingState.CODE:
                    code_str = "".join(token)
        return (state, explanation_str, code_str)

    async def call_openai(self, messages, queue):
        """
        call the openai api
        """
        if self.is_azure:
            response = await openai.ChatCompletion.acreate(
                engine=self.model,
                messages=messages,
                temperature=0,
                functions=OCTOPUS_FUNCTIONS,
                function_call="auto",
                stream=True,
            )
        else:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0,
                functions=OCTOPUS_FUNCTIONS,
                function_call="auto",
                stream=True,
            )
        message = None
        text_content = ""
        code_content = ""
        async for chunk in response:
            if not chunk["choices"]:
                continue
            delta = chunk["choices"][0]["delta"]
            logger.debug(f"{delta}")
            if not message:
                message = delta
            else:
                if "function_call" in delta:
                    self._merge_delta_for_function_call(message, delta)
                    arguments = message["function_call"].get("arguments", "")
                    (
                        state,
                        explanation_str,
                        code_str,
                    ) = self._get_function_call_argument_new_typing(message)
                    if explanation_str and text_content != explanation_str:
                        typed_chars = explanation_str[len(text_content) :]
                        text_content = explanation_str
                        await queue.put(
                            TaskRespond(
                                token_usage=0,
                                iteration=0,
                                respond_type=TaskRespond.OnAgentTextTyping,
                                model_name="",
                                typing_content=typed_chars,
                            )
                        )
                    if code_str and code_content != code_str:
                        typed_chars = code_str[len(code_content) :]
                        code_content = code_str
                        await queue.put(
                            TaskRespond(
                                token_usage=0,
                                iteration=0,
                                respond_type=TaskRespond.OnAgentCodeTyping,
                                model_name="",
                                typing_content=typed_chars,
                            )
                        )
                    logger.debug(
                        f"argument explanation:{explanation_str} code:{code_str}"
                    )
                else:
                    self._merge_delta_for_content(message, delta)
                    if delta.get("content") != None:
                        await queue.put(
                            TaskRespond(
                                token_usage=0,
                                iteration=0,
                                respond_type=TaskRespond.OnAgentTextTyping,
                                model_name="",
                                typing_content=delta["content"],
                            )
                        )
        return message

    async def handle_function(
        self, message, queue, token_usage=0, iteration=0, model_name=""
    ):
        if "function_call" in message:
            function_name = message["function_call"]["name"]
            arguments = json.loads(message["function_call"]["arguments"])
            logger.debug(f"call function {function_name} with args {arguments}")
            code = arguments["code"]
            explanation = arguments["explanation"]
            saved_filenames = arguments.get("saved_filenames", [])
            tool_input = json.dumps({
                "code": code,
                "explanation": explanation,
                "saved_filenames": saved_filenames,
            })
            # send the respond to client
            await queue.put(
                TaskRespond(
                    token_usage=token_usage,
                    iteration=iteration,
                    respond_type=TaskRespond.OnAgentActionType,
                    model_name=model_name,
                    on_agent_action=OnAgentAction(
                        input=tool_input, tool="execute_python_code"
                    ),
                )
            )
            function_result = None
            async for (result, respond) in self.call_function(
                code,
                iteration=iteration,
                token_usage=token_usage,
                model_name=model_name,
            ):
                function_result = result
                if respond:
                    await queue.put(respond)
            return function_result
        else:
            raise Exception("bad message, function message expected")

    async def arun(self, task, queue, max_iteration=5):
        """ """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        iterations = 0
        token_usage = 0
        model_name = ""
        try:
            while iterations < max_iteration:
                iterations += 1
                logger.debug(f" the input messages {messages}")
                chat_message = await self.call_openai(messages, queue)
                # model_name = response.get()"model"]
                # token_usage += response["usage"]["total_tokens"]
                logger.debug(f"the response {chat_message}")
                if "function_call" in chat_message:
                    chat_message["content"] = None
                    messages.append(chat_message)
                    function_name = chat_message["function_call"]["name"]
                    if function_name not in ["execute_python_code", "python"]:
                        messages.append({
                            "role": "function",
                            "name": "execute_python_code",
                            "content": "You can use the execute_python_code only",
                        })
                        continue
                    # call function
                    function_result = await self.handle_function(
                        chat_message, queue, token_usage, iterations, model_name
                    )
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iterations,
                            respond_type=TaskRespond.OnAgentActionEndType,
                            model_name=model_name,
                            on_agent_action_end=OnAgentActionEnd(
                                output="", output_files=function_result.saved_filenames
                            ),
                        )
                    )
                    # TODO optimize the token limitation
                    if function_result.has_result:
                        messages.append({
                            "role": "function",
                            "name": "execute_python_code",
                            "content": function_result.console_stdout[0:500],
                        })
                    elif function_result.has_error:
                        messages.append({
                            "role": "function",
                            "name": "execute_python_code",
                            "content": function_result.console_stderr[0:500],
                        })
                    else:
                        messages.append({
                            "role": "function",
                            "name": "execute_python_code",
                            "content": function_result.console_stdout[0:500],
                        })
                else:
                    # end task
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iterations,
                            respond_type=TaskRespond.OnFinalAnswerType,
                            model_name=model_name,
                            final_respond=FinalRespond(answer=chat_message["content"]),
                        )
                    )
                    break
        finally:
            await queue.put(None)
