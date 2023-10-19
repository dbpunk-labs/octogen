# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import json
import logging
import pytest
from og_sdk.agent_sdk import AgentSDK
from og_agent.codellama_agent import CodellamaAgent
from og_proto.agent_server_pb2 import ProcessOptions, TaskResponse
import asyncio
import pytest_asyncio

api_base = "127.0.0.1:9528"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"
logger = logging.getLogger(__name__)


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

    def __init__(self, payload):
        self.payload = payload

    async def prompt(self, question, chat_history=[]):
        async for line in PayloadStream(self.payload):
            yield line


@pytest_asyncio.fixture
async def agent_sdk():
    sdk = AgentSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    await sdk.close()


@pytest.mark.asyncio
async def test_codellama_agent_smoke_test(agent_sdk):
    sentence = {
        "explanation": "Hello, how can I help you?",
        "action": "no_action",
        "action_input": "",
        "saved_filenames": [],
        "language": "en",
        "is_final_answer": True,
    }
    client = CodellamaMockClient(json.dumps(sentence))
    agent = CodellamaAgent(client, agent_sdk)
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
    assert responses[-1].state.input_token_count == 1
    assert responses[-1].state.output_token_count == 43
