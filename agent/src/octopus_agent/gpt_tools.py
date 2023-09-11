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


class PrintFinalAnswerInput(BaseModel):
    answer: str = Field(description="the final answer")


class PrintFinalAnswerTool(StructuredTool):
    name = "print_final_answer"
    description = """print the the final answer"""
    args_schema: Type[BaseModel] = PrintFinalAnswerInput
    return_direct = True

    def _run(
        self,
        answer: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> Any:
        return ""

    async def _arun(
        self, answer: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        return ""


class PrintCodeInput(BaseModel):
    code: str = Field(description="the code showed to the human")
    language: str = Field(description="the programing language")
    explanation: str = Field(description="the explanation of the code")


class PrintCodeTool(StructuredTool):
    name = "print_code"
    description = """print the code"""
    args_schema: Type[BaseModel] = PrintCodeInput

    def _run(
        self,
        code: str,
        language: str,
        explanation: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return ""

    async def _arun(
        self,
        code: str,
        language: str,
        explanation: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return ""


class ExecutePythonCodeInput(BaseModel):
    code: str = Field(description="the python code to be executed")
    explanation: str = Field(description="the explanation of the python code")
    saved_filenames: Optional[List[str]] = Field(description="the saved filename list")


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


class ExecuteShellCodeInput(BaseModel):
    code: str = Field(description="the shell code to be executed by bash")
    explanation: str = Field(description="the explanation of the shell code")


class ExecuteShellCodeTool(StructuredTool):
    name = "run_shell_code"
    description = """Execute arbitrary shell code Returns a Markdown format string including return code, result, stdout, stderr, error"""
    args_schema: Type[BaseModel] = ExecuteShellCodeInput
    octopus_api: OctopusAPIMarkdownOutput = None

    def _run(
        self,
        code: str,
        explanation: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        based_code = "%%bash" + "\n" + code
        result = self.octopus_api.run(based_code)
        return result

    async def _arun(
        self,
        code: str,
        explanation: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        based_code = "%%bash" + "\n" + code
        return await self.octopus_api.arun(based_code)


class ExecuteTypescriptCodeInput(BaseModel):
    code: str = Field(description="the typescript code to be executed")
    explanation: str = Field(description="the explanation of the typescript code")


class ExecuteTypescriptCodeTool(StructuredTool):
    name = "execute_ts_code"
    description = """Execute arbitrary typescript code Returns a Markdown format string including return code, result, stdout, stderr, error"""
    args_schema: Type[BaseModel] = ExecuteTypescriptCodeInput
    octopus_api: OctopusAPIMarkdownOutput = None

    def _run(
        self,
        code: str,
        explanation: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        result = self.octopus_api.run(code, **{"kernel_name": "tslab"})
        return result

    async def _arun(
        self,
        code: str,
        explanation: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.octopus_api.arun(code, **{"kernel_name": "tslab"})
