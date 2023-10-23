# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import json
import logging
import pytest

from og_sdk.kernel_sdk import KernelSDK
from og_agent.codellama_agent import CodellamaAgent
from og_proto.agent_server_pb2 import ProcessOptions, TaskResponse
import asyncio
import pytest_asyncio

api_base = "127.0.0.1:9528"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"
logger = logging.getLogger(__name__)


@pytest.fixture
def kernel_sdk():
    endpoint = (
        "localhost:9527"  # Replace with the actual endpoint of your test gRPC server
    )
    return KernelSDK(endpoint, "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH")


class PayloadStream:

    def __init__(self, payload):
        self.payload = payload

    def __aiter__(self):
        # create an iterator of the input keys
        self.iter_keys = iter(self.payload)
        return self

    async def __anext__(self):
        try:
            k = {"content": next(self.iter_keys)}
            output = "data: %s\n" % json.dumps(k)
            return output
        except StopIteration:
            # raise stopasynciteration at the end of iterator
            raise StopAsyncIteration


class MockContext:

    def done(self):
        return False


class CodellamaMockClient:

    def __init__(self, payloads):
        self.payloads = payloads
        self.index = 0

    async def prompt(self, question, chat_history=[]):
        if self.index >= len(self.payloads):
            raise StopAsyncIteration
        self.index += 1
        payload = self.payloads[self.index - 1]
        async for line in PayloadStream(payload):
            yield line


@pytest.mark.asyncio
async def test_codellama_agent_execute_bash_code(kernel_sdk):
    kernel_sdk.connect()
    sentence1 = {
        "explanation": "print a hello world using python",
        "action": "execute_bash_code",
        "action_input": "echo 'hello world'",
        "saved_filenames": [],
        "language": "python",
        "is_final_answer": False,
    }
    sentence2 = {
        "explanation": "the output matchs the goal",
        "action": "no_action",
        "action_input": "",
        "saved_filenames": [],
        "language": "en",
        "is_final_answer": False,
    }
    client = CodellamaMockClient([json.dumps(sentence1), json.dumps(sentence2)])
    agent = CodellamaAgent(client, kernel_sdk)
    task_opt = ProcessOptions(
        streaming=True,
        llm_name="codellama",
        input_token_limit=100000,
        output_token_limit=100000,
        timeout=5,
    )
    queue = asyncio.Queue()
    await agent.arun("write a hello world in bash", queue, MockContext(), task_opt)
    responses = []
    while True:
        try:
            response = await queue.get()
            if not response:
                break
            responses.append(response)
        except asyncio.QueueEmpty:
            break
    logger.info(responses)
    console_output = list(
        filter(
            lambda x: x.response_type == TaskResponse.OnStepActionStreamStdout,
            responses,
        )
    )
    assert len(console_output) == 1, "bad console output count"
    assert console_output[0].console_stdout == "hello world\n", "bad console output"


@pytest.mark.asyncio
async def test_codellama_agent_execute_python_code(kernel_sdk):
    kernel_sdk.connect()
    sentence1 = {
        "explanation": "print a hello world using python",
        "action": "execute_python_code",
        "action_input": "print('hello world')",
        "saved_filenames": [],
        "language": "python",
        "is_final_answer": False,
    }
    sentence2 = {
        "explanation": "the output matchs the goal",
        "action": "no_action",
        "action_input": "",
        "saved_filenames": [],
        "language": "en",
        "is_final_answer": False,
    }
    client = CodellamaMockClient([json.dumps(sentence1), json.dumps(sentence2)])
    agent = CodellamaAgent(client, kernel_sdk)
    task_opt = ProcessOptions(
        streaming=True,
        llm_name="codellama",
        input_token_limit=100000,
        output_token_limit=100000,
        timeout=5,
    )
    queue = asyncio.Queue()
    await agent.arun("write a hello world in python", queue, MockContext(), task_opt)
    responses = []
    while True:
        try:
            response = await queue.get()
            if not response:
                break
            responses.append(response)
        except asyncio.QueueEmpty:
            break
    logger.info(responses)
    console_output = list(
        filter(
            lambda x: x.response_type == TaskResponse.OnStepActionStreamStdout,
            responses,
        )
    )
    assert len(console_output) == 1, "bad console output count"
    assert console_output[0].console_stdout == "hello world\n", "bad console output"


@pytest.mark.asyncio
async def test_codellama_agent_show_demo_code(kernel_sdk):
    sentence = {
        "explanation": "Hello, how can I help you?",
        "action": "show_demo_code",
        "action_input": "echo 'hello world'",
        "saved_filenames": [],
        "language": "shell",
        "is_final_answer": True,
    }
    client = CodellamaMockClient([json.dumps(sentence)])
    agent = CodellamaAgent(client, kernel_sdk)
    task_opt = ProcessOptions(
        streaming=True,
        llm_name="codellama",
        input_token_limit=100000,
        output_token_limit=100000,
        timeout=5,
    )
    queue = asyncio.Queue()
    await agent.arun("hello", queue, MockContext(), task_opt)
    responses = []
    while True:
        try:
            response = await queue.get()
            if not response:
                break
            responses.append(response)
        except asyncio.QueueEmpty:
            break
    logger.info(responses)
    assert (
        responses[-1].response_type == TaskResponse.OnFinalAnswer
    ), "bad response type"


@pytest.mark.asyncio
async def test_codellama_agent_smoke_test(kernel_sdk):
    sentence = {
        "explanation": "Hello, how can I help you?",
        "action": "no_action",
        "action_input": "",
        "saved_filenames": [],
        "language": "en",
        "is_final_answer": True,
    }
    client = CodellamaMockClient([json.dumps(sentence)])
    agent = CodellamaAgent(client, kernel_sdk)
    task_opt = ProcessOptions(
        streaming=True,
        llm_name="codellama",
        input_token_limit=100000,
        output_token_limit=100000,
        timeout=5,
    )
    queue = asyncio.Queue()
    await agent.arun("hello", queue, MockContext(), task_opt)
    responses = []
    while True:
        try:
            response = await queue.get()
            if not response:
                break
            responses.append(response)
        except asyncio.QueueEmpty:
            break
    logger.info(responses)
    assert len(responses) == len(sentence["explanation"]) + 1, "bad response count"
    assert (
        responses[-1].response_type == TaskResponse.OnFinalAnswer
    ), "bad response type"
    assert responses[-1].state.input_token_count == 388
    assert responses[-1].state.output_token_count == 43
