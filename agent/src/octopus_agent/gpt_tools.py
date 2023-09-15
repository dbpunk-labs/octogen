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

from langchain.tools import StructuredTool
from .tools import OctopusAPIMarkdownOutput
from typing import Any, Dict, List, Optional, Sequence, Union, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)


class ExecutePythonCodeInput(BaseModel):
    code: str = Field(description="the python code to be executed")
    explanation: str = Field(description="the explanation about the python code")
    saved_filenames: List[str] = Field(
        description="A list of filenames that were created by the code", default=[]
    )


class ExecutePythonCodeTool(StructuredTool):
    name = "execute_python_code"
    description = """Execute arbitrary Python code Returns a markdown format string including result, stdout, stderr, error"""
    args_schema: Type[BaseModel] = ExecutePythonCodeInput
    octopus_api: Optional[OctopusAPIMarkdownOutput] = None

    def _run(
        self,
        code: str,
        explanation: str,
        saved_filenames: List[str] = [],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        code = code
        result = self.octopus_api.run(code)
        return result

    async def _arun(
        self,
        code: str,
        explanation: str,
        saved_filenames: List[str] = [],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.octopus_api.arun(code)
