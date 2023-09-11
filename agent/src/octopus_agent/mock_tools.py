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

from typing import Any, Dict, List, Optional, Sequence, Union, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)


class PrintFinalAnswerInput(BaseModel):
    answer: str = Field(description="the final answer")


class PrintFinalAnswerTool(BaseTool):
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
