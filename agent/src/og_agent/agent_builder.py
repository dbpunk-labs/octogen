# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
from .prompt import OCTOGEN_FUNCTION_SYSTEM, OCTOGEN_CODELLAMA_SYSTEM
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
        endpoint, key, OCTOGEN_CODELLAMA_SYSTEM, "Octogen", "User", grammar
    )

    # init the agent
    return CodellamaAgent(client, sdk)


def build_openai_agent(sdk, model_name, is_azure=True):
    """build openai function call agent"""
    # TODO a data dir per user
    # init the agent

    agent = OpenaiAgent(model_name, OCTOGEN_FUNCTION_SYSTEM, sdk, is_azure=is_azure)
    return agent


def build_mock_agent(sdk, cases_path):
    """
    build the mock agent for testing
    """
    with open(cases_path, "r") as fd:
        messages = json.load(fd)
    agent = MockAgent(messages, sdk)
    return agent
