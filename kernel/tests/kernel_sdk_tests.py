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
import asyncio
import pytest
import logging
import json
from octopus_kernel.sdk.kernel_sdk import KernelSDK
from octopus_proto.kernel_server_pb2 import ExecuteResponse

logger = logging.getLogger(__name__)


@pytest.fixture
def kernel_sdk():
    endpoint = (
        "localhost:9527"  # Replace with the actual endpoint of your test gRPC server
    )
    return KernelSDK(endpoint, "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH")


@pytest.fixture
def bad_kernel_sdk():
    endpoint = (
        "localhost:9527"  # Replace with the actual endpoint of your test gRPC server
    )
    return KernelSDK(endpoint, "ZCeI9cYtOCyLISoi488BgZHeBkHWuFU")


@pytest.mark.asyncio
async def test_bad_sdk(bad_kernel_sdk):
    try:
        kernel_sdk.connect()
        assert kernel_sdk.stub is not None  # Check that stub is initialized
        await kernel_sdk.start()
        assert False
    except Exception as e:
        assert True


@pytest.mark.asyncio
async def test_sdk_smoke_test(kernel_sdk):
    kernel_sdk.connect()
    assert kernel_sdk.stub is not None  # Check that stub is initialized
    if not await kernel_sdk.is_alive():
        await kernel_sdk.start()
    code = """print('hello world!')"""
    responds = []
    async for respond in kernel_sdk.execute(code):
        responds.append(respond)
    await kernel_sdk.stop()
    assert len(responds) == 1
    assert responds[0].output_type == ExecuteResponse.StdoutType
    assert json.loads(responds[0].output)["text"] == "hello world!\n"


@pytest.mark.asyncio
async def test_sdk_result_test(kernel_sdk):
    kernel_sdk.connect()
    assert kernel_sdk.stub is not None  # Check that stub is initialized
    if not await kernel_sdk.is_alive():
        await kernel_sdk.start()
    code = """print('hello world!')
5"""
    responds = []
    async for respond in kernel_sdk.execute(code):
        responds.append(respond)
    await kernel_sdk.stop()
    assert len(responds) == 2
    assert responds[0].output_type == ExecuteResponse.StdoutType
    assert responds[1].output_type == ExecuteResponse.ResultType
    assert json.loads(responds[0].output)["text"] == "hello world!\n"
    assert json.loads(responds[1].output)["text/plain"] == "5"

