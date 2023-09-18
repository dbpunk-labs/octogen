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
from langchain.agents import initialize_agent
from langchain.schema.messages import SystemMessage
from .tools import OctopusAPIMarkdownOutput
from .gpt_tools import ExecutePythonCodeTool
from .mock_tools import PrintFinalAnswerTool as MockPrintFinalAnswerTool
from .prompt import OCTOPUS_FUNCTION_SYSTEM, OCTOPUS_CODELLAMA_SYSTEM
from .gpt_async_callback import AgentAsyncHandler
from langchain.agents import AgentType
from .codellama_agent import CodellamaAgent
from .openai_agent import OpenaiAgent
from .codellama_client import CodellamaClient


def build_codellama_agent(endpoint, key, sdk, grammer_path):
    with open(grammer_path, "r") as fd:
        grammar = fd.read()

    client = CodellamaClient(
        endpoint, key, OCTOPUS_CODELLAMA_SYSTEM, "Octopus", "User", grammar
    )
    """build openai function call agent"""
    # init the agent
    return CodellamaAgent(client, sdk)


def build_openai_agent(sdk, model_name):
    """build openai function call agent"""
    # TODO a data dir per user
    # init the agent

    agent = OpenaiAgent(model_name, sdk, OCTOPUS_FUNCTION_SYSTEM)
    return agent


def build_mock_agent(llm):
    tools = [
        MockPrintFinalAnswerTool(),
    ]
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
    return agent
