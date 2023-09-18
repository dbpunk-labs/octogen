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
from typing import Any, Dict, List, Optional, Sequence, Union, Type
from pydantic import BaseModel, Field
from octopus_proto.kernel_server_pb2 import ExecuteResponse
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .utils import parse_image_filename, process_char_stream

logger = logging.getLogger(__name__)


class FunctionResult(BaseModel):
    console_stderr: str = ""
    console_stdout: str = ""
    saved_filenames: List[str] = Field(
        description="A list of filenames that were created by the code", default=[]
    )
    has_result: bool = False
    has_error: bool = False


class BaseAgent:

    def __init__(self, sdk):
        self.kernel_sdk = sdk

    async def call_function(
        self, code, queue, iteration=1, token_usage=0, model_name=""
    ) -> FunctionResult:
        """
        run code with kernel
        """
        console_stdout = ""
        console_stderr = ""
        has_result = False
        has_error = False
        async for kernel_respond in self.kernel_sdk.execute(code=code):
            # process the stdout
            if kernel_respond.output_type == ExecuteResponse.StdoutType:
                kernel_output = json.loads(kernel_respond.output)["text"]
                console_stdout += kernel_output
                console_stdout = process_char_stream(console_stdout)
                await queue.put(
                    TaskRespond(
                        token_usage=token_usage,
                        iteration=iteration,
                        respond_type=TaskRespond.OnAgentActionStdout,
                        model_name=model_name,
                        console_stdout=kernel_output,
                    )
                )
            # process the stderr
            elif kernel_respond.output_type == ExecuteResponse.StderrType:
                kernel_err = json.loads(kernel_respond.output)["text"]
                console_stderr += kernel_err
                console_stderr = process_char_stream(console_stderr)
                await queue.put(
                    TaskRespond(
                        token_usage=token_usage,
                        iteration=iteration,
                        respond_type=TaskRespond.OnAgentActionStderr,
                        model_name=model_name,
                        console_stderr=kernel_err,
                    )
                )
            elif kernel_respond.output_type == ExecuteResponse.TracebackType:
                traceback = json.loads(kernel_respond.output)["traceback"]
                console_stderr += traceback
                has_error = True
                await queue.put(
                    TaskRespond(
                        token_usage=token_usage,
                        iteration=iteration,
                        respond_type=TaskRespond.OnAgentActionStderr,
                        model_name=model_name,
                        console_stderr=traceback,
                    )
                )
            else:
                has_result = True
                result = json.loads(kernel_respond.output)
                if "image/gif" in result:
                    console_stdout = result["image/gif"]
                elif "image/png" in result:
                    console_stdout = result["image/png"]
                elif "text/plain" in result:
                    console_stdout = result["text/plain"]
                await queue.put(
                    TaskRespond(
                        token_usage=token_usage,
                        iteration=iteration,
                        respond_type=TaskRespond.OnAgentActionStdout,
                        model_name=model_name,
                        console_stdout=console_stdout,
                    )
                )
        output_files = []
        filename = parse_image_filename(console_stdout)
        if filename:
            output_files.append(filename)
        return FunctionResult(
            console_stderr=console_stderr,
            console_stdout=console_stdout,
            saved_filenames=output_files,
            has_error=has_error,
            has_result=has_result,
        )