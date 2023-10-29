# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
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
import tiktoken

logger = logging.getLogger(__name__)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
OCTOGEN_FUNCTIONS = [
    {
        "name": "execute_python_code",
        "description": "Safely execute arbitrary Python code and return the result, stdout, and stderr. ",
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
        "name": "execute_bash_code",
        "description": "Safely execute arbitrary Bash code and return the result, stdout, and stderr. sudo is not supported.",
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "the explanation about the bash code",
                },
                "code": {
                    "type": "string",
                    "description": "the bash code to be executed",
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
        logger.info(f"use openai model {model} is_azure {is_azure}")
        logger.info(f"use openai with system prompt {system_prompt}")
        self.is_azure = is_azure
        self.model_name = model if not is_azure else ""

    def _merge_delta_for_function_call(self, message, delta):
        if len(message.keys()) == 0:
            message.update(delta)
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
        if message["function_call"]["name"] == "python":
            return TypingState.CODE, "", message["function_call"].get("arguments", "")

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

    def _get_message_token_count(self, message):
        response_token_count = 0
        if "function_call" in message and message["function_call"]:
            arguments = message["function_call"].get("arguments", "")
            response_token_count += len(encoding.encode(arguments))
        if "content" in message and message["content"]:
            response_token_count += len(encoding.encode(message.get("content")))
        return response_token_count

    async def call_openai(self, messages, queue, context, task_context, task_opt):
        """
        call the openai api
        """
        logger.debug(f"call openai with messages {messages}")
        input_token_count = 0
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
                functions=OCTOGEN_FUNCTIONS,
                function_call="auto",
                stream=True,
            )
        else:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0,
                functions=OCTOGEN_FUNCTIONS,
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
            if function_name == "python":
                raw_code = message["function_call"]["arguments"]
                logger.debug(f"call function {function_name} with args {code}")
                code = raw_code
            else:
                arguments = json.loads(message["function_call"]["arguments"])
                logger.debug(f"call function {function_name} with args {arguments}")
                raw_code = arguments["code"]
                code = raw_code
                explanation = arguments["explanation"]
                saved_filenames = arguments.get("saved_filenames", [])
            if function_name == "execute_bash_code":
                language = "bash"
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

    async def arun(self, task, queue, context, task_opt):
        """
        process the task
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        iterations = 0
        task_context = TaskContext(
            start_time=time.time(),
            output_token_count=0,
            input_token_count=0,
            llm_name=self.model_name,
            llm_respond_duration=0,
        )
        try:
            while not context.done():
                if task_context.input_token_count >= task_opt.input_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnInputTokenLimitExceed,
                            error_msg="input token limit reached",
                        )
                    )
                    break
                if task_context.output_token_count >= task_opt.output_token_limit:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnOutputTokenLimitExceed,
                            error_msg="output token limit reached",
                        )
                    )
                    break
                logger.debug(f" the input messages {messages}")
                chat_message = await self.call_openai(
                    messages, queue, context, task_context, task_opt
                )
                logger.debug(f"the response {chat_message}")
                if "function_call" in chat_message:
                    if "content" not in chat_message:
                        chat_message["content"] = None
                    if "role" not in chat_message:
                        chat_message["role"] = "assistant"
                    messages.append(chat_message)
                    function_name = chat_message["function_call"]["name"]
                    if function_name not in [
                        "execute_python_code",
                        "python",
                        "execute_bash_code",
                    ]:
                        messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": "You can use the execute_python_code or execute_bash_code",
                        })
                        continue
                    function_result = await self.handle_function(
                        chat_message, queue, context, task_context, task_opt
                    )

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
                    # TODO optimize the token limitation
                    if function_result.has_result:
                        messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": function_result.console_stdout[0:500],
                        })
                    elif function_result.has_error:
                        messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": function_result.console_stderr[0:500],
                        })
                    else:
                        messages.append({
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
                        )
                    )
                    break
        except Exception as ex:
            logging.exception("fail process task")
            response = TaskResponse(
                response_type=TaskResponse.OnSystemError,
                error_msg=str(ex),
            )
            await queue.put(response)
        finally:
            await queue.put(None)
