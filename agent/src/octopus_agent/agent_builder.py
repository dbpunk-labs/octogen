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
import json
from .prompt import OCTOPUS_FUNCTION_SYSTEM, OCTOPUS_CODELLAMA_SYSTEM
from .codellama_agent import CodellamaAgent
from .openai_agent import OpenaiAgent
from .codellama_client import CodellamaClient
from .mock_agent import MockAgent


def build_codellama_agent(endpoint, key, sdk, grammer_path):
    """
    build codellama agent
    """
    with open(grammer_path, "r") as fd:
        grammar = fd.read()

    client = CodellamaClient(
        endpoint, key, OCTOPUS_CODELLAMA_SYSTEM, "Octopus", "User", grammar
    )

    # init the agent
    return CodellamaAgent(client, sdk)


def build_openai_agent(sdk, model_name, is_azure=True):
    """build openai function call agent"""
    # TODO a data dir per user
    # init the agent

    agent = OpenaiAgent(model_name, OCTOPUS_FUNCTION_SYSTEM, sdk, is_azure=is_azure)
    return agent


def build_mock_agent(sdk, cases_path):
    """
    build the mock agent for testing
    """
    with open(cases_path, "r") as fd:
        messages = json.load(fd)
    agent = MockAgent(messages, sdk)
    return agent
