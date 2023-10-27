# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import io
import logging
import time
from typing import List
from pydantic import BaseModel, Field
from og_proto.kernel_server_pb2 import ExecuteResponse
from og_proto.agent_server_pb2 import TaskResponse, ContextState
from og_sdk.utils import parse_image_filename, process_char_stream
from og_proto.agent_server_pb2 import OnStepActionStart, TaskResponse, OnStepActionEnd, FinalAnswer, TypingContent
from .tokenizer import tokenize
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
logger = logging.getLogger(__name__)


class FunctionResult(BaseModel):
    console_stderr: str = ""
    console_stdout: str = ""
    saved_filenames: List[str] = Field(
        description="A list of filenames that were created by the code", default=[]
    )
    has_result: bool = False
    has_error: bool = False


class TaskContext(BaseModel):
    start_time: float = 0
    output_token_count: int = 0
    input_token_count: int = 0
    llm_name: str = ""
    llm_response_duration: int = 0

    def to_context_state_proto(self):
        # in ms
        total_duration = int((time.time() - self.start_time) * 1000)
        return ContextState(
            output_token_count=self.output_token_count,
            input_token_count=self.input_token_count,
            llm_name=self.llm_name,
            total_duration=total_duration,
            llm_response_duration=self.llm_response_duration,
        )


class TypingState:
    START = 0
    EXPLANATION = 1
    CODE = 2


class BaseAgent:

    def __init__(self, sdk):
        self.kernel_sdk = sdk
        self.model_name = ""

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

    def _parse_arguments(
        self,
        arguments,
        is_code=False,
        first_field_name="explanation",
        second_field_name="code",
    ):
        """
        parse the partial key with string value from json
        """
        if is_code:
            return TypingState.CODE, "", arguments
        state = TypingState.START
        explanation_str = ""
        code_str = ""
        logger.debug(f"the arguments {arguments}")
        for token_state, token in tokenize(io.StringIO(arguments)):
            if token_state == None:
                if state == TypingState.EXPLANATION and token[0] == 1:
                    explanation_str = token[1]
                    state = TypingState.START
                if state == TypingState.CODE and token[0] == 1:
                    code_str = token[1]
                    state = TypingState.START
                if token[1] == first_field_name:
                    state = TypingState.EXPLANATION
                if token[1] == second_field_name:
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

    async def _read_function_call_message(
        self, message, queue, old_text_content, old_code_content, task_context, task_opt
    ):
        typing_language = "text"
        if message["function_call"].get("name", "") in [
            "execute_python_code",
            "python",
        ]:
            typing_language = "python"
        elif message["function_call"].get("name", "") == "execute_bash_code":
            typing_language = "bash"
        is_code = False
        if message["function_call"].get("name", "") == "python":
            is_code = True
        arguments = message["function_call"].get("arguments", "")
        return await self._send_typing_message(
            arguments,
            queue,
            old_text_content,
            old_code_content,
            typing_language,
            task_context,
            task_opt,
            is_code=is_code,
        )

    async def _read_json_message(
        self, message, queue, old_text_content, old_code_content, task_context, task_opt
    ):
        arguments = message.get("content", "")
        typing_language = "text"
        if arguments.find("execute_python_code") >= 0:
            typing_language = "python"
        elif arguments.find("execute_bash_code") >= 0:
            typing_language = "bash"

        return await self._send_typing_message(
            arguments,
            queue,
            old_text_content,
            old_code_content,
            typing_language,
            task_context,
            task_opt,
        )

    async def _send_typing_message(
        self,
        arguments,
        queue,
        old_text_content,
        old_code_content,
        language,
        task_context,
        task_opt,
        is_code=False,
    ):
        """
        send the typing message to the client
        """
        (state, explanation_str, code_str) = self._parse_arguments(arguments, is_code)
        logger.debug(
            f"argument explanation:{explanation_str} code:{code_str} text_content:{old_text_content}"
        )
        if explanation_str and old_text_content != explanation_str:
            typed_chars = explanation_str[len(old_text_content) :]
            new_text_content = explanation_str
            if task_opt.streaming and len(typed_chars) > 0:
                task_response = TaskResponse(
                    state=task_context.to_context_state_proto(),
                    response_type=TaskResponse.OnModelTypeText,
                    typing_content=TypingContent(content=typed_chars, language="text"),
                )
                await queue.put(task_response)
            return new_text_content, old_code_content
        if code_str and old_code_content != code_str:
            typed_chars = code_str[len(old_code_content) :]
            code_content = code_str
            if task_opt.streaming and len(typed_chars) > 0:
                await queue.put(
                    TaskResponse(
                        state=task_context.to_context_state_proto(),
                        response_type=TaskResponse.OnModelTypeCode,
                        typing_content=TypingContent(
                            content=typed_chars, language=language
                        ),
                    )
                )
            return old_text_content, code_content
        return old_text_content, old_code_content

    async def extract_message(
        self,
        response_generator,
        queue,
        rpc_context,
        task_context,
        task_opt,
        start_time,
        is_json_format=False,
    ):
        """
        extract the chunk from the response generator
        """
        message = {}
        text_content = ""
        code_content = ""
        context_output_token_count = task_context.output_token_count
        start_time = time.time()
        async for chunk in response_generator:
            if rpc_context.done():
                logger.debug("the client has cancelled the request")
                break
            if not chunk["choices"]:
                continue
            logger.debug(f"the chunk {chunk}")
            task_context.llm_name = chunk.get("model", "")
            self.model_name = chunk.get("model", "")
            delta = chunk["choices"][0]["delta"]
            if "function_call" in delta:
                self._merge_delta_for_function_call(message, delta)
                response_token_count = self._get_message_token_count(message)
                task_context.output_token_count = (
                    response_token_count + context_output_token_count
                )
                task_context.llm_response_duration += int(
                    (time.time() - start_time) * 1000
                )
                start_time = time.time()
                (
                    new_text_content,
                    new_code_content,
                ) = await self._read_function_call_message(
                    message,
                    queue,
                    text_content,
                    code_content,
                    task_context,
                    task_opt,
                )
                text_content = new_text_content
                code_content = new_code_content
            else:
                self._merge_delta_for_content(message, delta)
                task_context.llm_response_duration += int(
                    (time.time() - start_time) * 1000
                )
                start_time = time.time()
                if message.get("content") != None:
                    response_token_count = self._get_message_token_count(message)
                    task_context.output_token_count = (
                        response_token_count + context_output_token_count
                    )
                    if is_json_format:
                        (
                            new_text_content,
                            new_code_content,
                        ) = await self._read_json_message(
                            message,
                            queue,
                            text_content,
                            code_content,
                            task_context,
                            task_opt,
                        )
                        text_content = new_text_content
                        code_content = new_code_content

                    elif task_opt.streaming and delta.get("content"):
                        await queue.put(
                            TaskResponse(
                                state=task_context.to_context_state_proto(),
                                response_type=TaskResponse.OnModelTypeText,
                                typing_content=TypingContent(
                                    content=delta["content"], language="text"
                                ),
                            )
                        )
        logger.info(
            f"call the {self.model_name} with input token {task_context.input_token_count} and output token count {task_context.output_token_count}"
        )
        return message

    async def call_function(self, code, context, task_context=None):
        """
        run code with kernel
        """
        console_stdout = ""
        console_stderr = ""
        has_result = False
        has_error = False
        is_alive = await self.kernel_sdk.is_alive()
        if not is_alive:
            await self.kernel_sdk.start(kernel_name="python3")
        async for kernel_respond in self.kernel_sdk.execute(code=code):
            if context.done():
                logger.debug(
                    "the context is not active and the client cancelled the request"
                )
                break
            # process the stdout
            if kernel_respond.output_type == ExecuteResponse.StdoutType:
                kernel_output = json.loads(kernel_respond.output)["text"]
                console_stdout += kernel_output
                console_stdout = process_char_stream(console_stdout)
                logger.debug(f"the new stdout {console_stdout}")
                yield (
                    None,
                    TaskResponse(
                        state=task_context.to_context_state_proto()
                        if task_context
                        else None,
                        response_type=TaskResponse.OnStepActionStreamStdout,
                        console_stdout=kernel_output,
                    ),
                )
            # process the stderr
            elif kernel_respond.output_type == ExecuteResponse.StderrType:
                kernel_err = json.loads(kernel_respond.output)["text"]
                console_stderr += kernel_err
                console_stderr = process_char_stream(console_stderr)
                logger.debug(f"the new stderr {console_stderr}")
                yield (
                    None,
                    TaskResponse(
                        state=task_context.to_context_state_proto()
                        if task_context
                        else None,
                        response_type=TaskResponse.OnStepActionStreamStderr,
                        console_stderr=kernel_err,
                    ),
                )
            elif kernel_respond.output_type == ExecuteResponse.TracebackType:
                traceback = json.loads(kernel_respond.output)["traceback"]
                console_stderr += traceback
                logger.debug(f"the new traceback {console_stderr}")
                has_error = True
                yield (
                    None,
                    TaskResponse(
                        state=task_context.to_context_state_proto()
                        if task_context
                        else None,
                        response_type=TaskResponse.OnStepActionStreamStderr,
                        console_stderr=traceback,
                    ),
                )
            else:
                has_result = True
                result = json.loads(kernel_respond.output)
                logger.debug(f"the result {result}")
                if "image/gif" in result:
                    console_stdout = result["image/gif"]
                elif "image/png" in result:
                    console_stdout = result["image/png"]
                elif "text/plain" in result:
                    console_stdout = result["text/plain"]
                    console_stdout = bytes(console_stdout, "utf-8").decode(
                        "unicode_escape"
                    )
                    if console_stdout.startswith("'") and console_stdout.endswith("'"):
                        console_stdout = console_stdout[1 : len(console_stdout) - 1]
                yield (
                    None,
                    TaskResponse(
                        state=task_context.to_context_state_proto()
                        if task_context
                        else None,
                        response_type=TaskResponse.OnStepActionStreamStdout,
                        console_stdout=console_stdout,
                    ),
                )
        output_files = []
        filename = parse_image_filename(console_stdout)
        if filename:
            output_files.append(filename)
        yield (
            FunctionResult(
                console_stderr=console_stderr,
                console_stdout=console_stdout,
                saved_filenames=output_files,
                has_error=has_error,
                has_result=has_result,
            ),
            None,
        )
