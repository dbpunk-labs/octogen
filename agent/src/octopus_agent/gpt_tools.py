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
from pydantic import BaseModel, Field
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)


class AskQuestionInput(BaseModel):
    question: str = Field(description="the question")


class AskQuestionTool(StructuredTool):
    name = "ask_question"
    description = """ask the question from the human"""
    args_schema: Type[BaseModel] = AskQuestionInput
    return_direct = True

    def _run(
        self,
        question: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        return "Yes"

    async def _arun(
        self,
        question: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return "Yes"


class ExecutePythonCodeInput(BaseModel):
    code: str = Field(description="the python code to be executed")
    explanation: str = Field(description="the explanation of the python code")
    saved_filenames: Optional[List[str]] = Field(
        description="the saved filename list", default=[]
    )


class ExecutePythonCodeTool(StructuredTool):
    name = "execute_python_code"
    description = """Execute arbitrary Python code Returns a Markdown format string including return code, result, stdout, stderr, error"""
    args_schema: Type[BaseModel] = ExecutePythonCodeInput
    octopus_api: OctopusAPIMarkdownOutput = None

    def _run(
        self,
        code: str,
        explanation: str,
        saved_filenames: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if not self.octopus_api:
            self.octopus_api = OctopusAPIMarkdownOutput()
        code = code
        result = self.octopus_api.run(code)
        return result

    async def _arun(
        self,
        code: str,
        explanation: str,
        saved_filenames: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        if not self.octopus_api:
            self.octopus_api = OctopusAPIMarkdownOutput()
        return await self.octopus_api.arun(code)
