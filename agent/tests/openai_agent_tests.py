# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import logging
import pytest
from og_sdk.agent_sdk import AgentSDK
from og_agent import openai_agent
from og_proto.agent_server_pb2 import ProcessOptions, TaskResponse
from openai.openai_object import OpenAIObject
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
            k = next(self.iter_keys)
            obj = OpenAIObject()
            delta = OpenAIObject()
            content = OpenAIObject()
            content.content = k
            delta.delta = content
            obj.choices = [delta]
            return obj
        except StopIteration:
            # raise stopasynciteration at the end of iterator
            raise StopAsyncIteration


class MockContext:

    def done(self):
        return False


@pytest_asyncio.fixture
async def agent_sdk():
    sdk = AgentSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    await sdk.close()


@pytest.mark.asyncio
async def test_openai_agent_smoke_test(mocker, agent_sdk):
    sentence = "Hello, how can I help you?"
    stream = PayloadStream(sentence)
    with mocker.patch(
        "og_agent.openai_agent.openai.ChatCompletion.acreate", return_value=stream
    ) as mock_openai:
        agent = openai_agent.OpenaiAgent("gpt4", "prompt", agent_sdk, is_azure=False)
        queue = asyncio.Queue()
        task_opt = ProcessOptions(
            streaming=True,
            llm_name="gpt4",
            input_token_limit=100000,
            output_token_limit=100000,
            timeout=5,
        )
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
        assert len(responses) == len(sentence) + 1, "bad response count"
        assert (
            responses[-1].response_type == TaskResponse.OnFinalAnswer
        ), "bad response type"
        assert responses[-1].state.input_token_count == 2
        assert responses[-1].state.output_token_count == 8
