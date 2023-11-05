# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
from .llama_agent import LlamaAgent
from .openai_agent import OpenaiAgent
from .llama_client import LlamaClient
from .mock_agent import MockAgent


def build_llama_agent(endpoint, key, sdk, grammer_path):
    """
    build llama agent
    """
    with open(grammer_path, "r") as fd:
        grammar = fd.read()
    client = LlamaClient(endpoint, key, grammar)
    # init the agent
    return LlamaAgent(client, sdk)


def build_openai_agent(sdk, model_name, is_azure=True):
    """build openai function call agent"""
    # TODO a data dir per user
    # init the agent

    agent = OpenaiAgent(model_name, sdk, is_azure=is_azure)
    return agent


def build_mock_agent(sdk, cases_path):
    """
    build the mock agent for testing
    """
    with open(cases_path, "r") as fd:
        messages = json.load(fd)
    agent = MockAgent(messages, sdk)
    return agent
