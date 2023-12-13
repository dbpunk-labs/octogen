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
from og_agent import openai_agent
from og_proto.agent_server_pb2 import ProcessOptions, TaskResponse, ProcessTaskRequest
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


class FunctionCallPayloadStream:

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __aiter__(self):
        # create an iterator of the input keys
        self.iter_keys = iter(self.arguments)
        return self

    async def __anext__(self):
        try:
            k = next(self.iter_keys)
            obj = OpenAIObject()
            delta = OpenAIObject()
            function_para = OpenAIObject()
            function_para.name = self.name
            function_para.arguments = k
            function_call = OpenAIObject()
            function_call.function_call = function_para
            delta.delta = function_call
            obj.choices = [delta]
            return obj
        except StopIteration:
            # raise stopasynciteration at the end of iterator
            raise StopAsyncIteration


class MockContext:

    def done(self):
        return False


class MultiCallMock:

    def __init__(self, responses):
        self.responses = responses
        self.index = 0

    def call(self, *args, **kwargs):
        if self.index >= len(self.responses):
            raise Exception("no more response")
        self.index += 1
        logger.debug("call index %d", self.index)
        return self.responses[self.index - 1]


@pytest.fixture
def kernel_sdk():
    endpoint = (
        "localhost:9527"  # Replace with the actual endpoint of your test gRPC server
    )
    return KernelSDK(endpoint, "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH")


@pytest.mark.asyncio
async def test_openai_agent_call_execute_bash_code(mocker, kernel_sdk):
    kernel_sdk.connect()
    arguments = {
        "explanation": "the hello world in bash",
        "code": "echo 'hello world'",
        "saved_filenames": [],
        "language": "bash",
    }
    stream1 = FunctionCallPayloadStream("execute", json.dumps(arguments))
    sentence = "The output 'hello world' is the result"
    stream2 = PayloadStream(sentence)
    call_mock = MultiCallMock([stream1, stream2])
    with mocker.patch(
        "og_agent.openai_agent.openai.ChatCompletion.acreate",
        side_effect=call_mock.call,
    ) as mock_openai:
        agent = openai_agent.OpenaiAgent("gpt4", kernel_sdk, is_azure=False)
        queue = asyncio.Queue()
        task_opt = ProcessOptions(
            streaming=True,
            llm_name="gpt4",
            input_token_limit=100000,
            output_token_limit=100000,
            timeout=5,
        )
        request = ProcessTaskRequest(
            input_files=[],
            task="write a hello world in bash",
            context_id="",
            options=task_opt,
        )
        await agent.arun(request, queue, MockContext(), task_opt)
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
async def test_openai_agent_call_execute_python_code(mocker, kernel_sdk):
    kernel_sdk.connect()
    arguments = {
        "explanation": "the hello world in python",
        "code": "print('hello world')",
        "language": "python",
        "saved_filenames": [],
    }
    stream1 = FunctionCallPayloadStream("execute", json.dumps(arguments))
    sentence = "The output 'hello world' is the result"
    stream2 = PayloadStream(sentence)
    call_mock = MultiCallMock([stream1, stream2])
    with mocker.patch(
        "og_agent.openai_agent.openai.ChatCompletion.acreate",
        side_effect=call_mock.call,
    ) as mock_openai:
        agent = openai_agent.OpenaiAgent("gpt4", kernel_sdk, is_azure=False)
        queue = asyncio.Queue()
        task_opt = ProcessOptions(
            streaming=True,
            llm_name="gpt4",
            input_token_limit=100000,
            output_token_limit=100000,
            timeout=5,
        )
        request = ProcessTaskRequest(
            input_files=[],
            task="write a hello world in python",
            context_id="",
            options=task_opt,
        )
        await agent.arun(request, queue, MockContext(), task_opt)
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
async def test_openai_agent_smoke_test(mocker, kernel_sdk):
    sentence = "Hello, how can I help you?"
    stream = PayloadStream(sentence)
    with mocker.patch(
        "og_agent.openai_agent.openai.ChatCompletion.acreate", return_value=stream
    ) as mock_openai:
        agent = openai_agent.OpenaiAgent("gpt4", kernel_sdk, is_azure=False)
        queue = asyncio.Queue()
        task_opt = ProcessOptions(
            streaming=True,
            llm_name="gpt4",
            input_token_limit=100000,
            output_token_limit=100000,
            timeout=5,
        )
        request = ProcessTaskRequest(
            input_files=[], task="hello", context_id="", options=task_opt
        )
        await agent.arun(request, queue, MockContext(), task_opt)
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
        assert responses[-1].state.input_token_count == 153
        assert responses[-1].state.output_token_count == 8
