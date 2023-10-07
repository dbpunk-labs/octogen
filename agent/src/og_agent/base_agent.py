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
import json
import logging
import time
from typing import Any, Dict, List, Optional, Sequence, Union, Type
from pydantic import BaseModel, Field
from og_proto.kernel_server_pb2 import ExecuteResponse
from og_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond, TaskState
from og_sdk.utils import parse_image_filename, process_char_stream

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
    generated_token_count: int = 0
    sent_token_count: int = 0
    model_name: str = ""
    iteration_count: int = 0
    model_respond_duration: int = 0

    def to_task_state_proto(self):
        # in ms
        total_duration = int((time.time() - self.start_time) * 1000)
        return TaskState(
            generated_token_count=self.generated_token_count,
            iteration_count=self.iteration_count,
            model_name=self.model_name,
            total_duration=total_duration,
            sent_token_count=self.sent_token_count,
            model_respond_duration=self.model_respond_duration,
        )


class TypingState:
    START = 0
    EXPLANATION = 1
    CODE = 2


class BaseAgent:

    def __init__(self, sdk):
        self.kernel_sdk = sdk

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
                    TaskRespond(
                        state=task_context.to_task_state_proto()
                        if task_context
                        else None,
                        respond_type=TaskRespond.OnAgentActionStdout,
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
                    TaskRespond(
                        state=task_context.to_task_state_proto()
                        if task_context
                        else None,
                        respond_type=TaskRespond.OnAgentActionStderr,
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
                    TaskRespond(
                        state=task_context.to_task_state_proto()
                        if task_context
                        else None,
                        respond_type=TaskRespond.OnAgentActionStderr,
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
                    TaskRespond(
                        state=task_context.to_task_state_proto()
                        if task_context
                        else None,
                        respond_type=TaskRespond.OnAgentActionStdout,
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
