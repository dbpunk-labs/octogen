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
import os
import asyncio
import pytest
import logging
import json
from og_sdk.kernel_sdk import KernelSDK
from og_sdk.utils import generate_async_chunk
from og_proto.kernel_server_pb2 import ExecuteResponse
import aiofiles
from typing import AsyncIterable

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
async def test_upload_and_download_smoke_test(kernel_sdk):
    kernel_sdk.connect()
    path = os.path.abspath(__file__)
    response = await kernel_sdk.upload_binary(
        generate_async_chunk(path, "kernel_sdk_tests.py")
    )
    assert response
    file_stats = os.stat(path)
    assert response.length == file_stats.st_size, "bad upload file size"
    length = 0
    async for chunk in kernel_sdk.download_file("kernel_sdk_tests.py"):
        length += len(chunk.buffer)
    assert length == file_stats.st_size, "bad upload file size"


@pytest.mark.asyncio
async def test_stop_kernel(kernel_sdk):
    kernel_sdk.connect()
    assert kernel_sdk.stub is not None  # Check that stub is initialized
    if not await kernel_sdk.is_alive():
        await kernel_sdk.start()
    assert await kernel_sdk.is_alive()
    response = await kernel_sdk.stop()
    assert response.code == 0
    assert not await kernel_sdk.is_alive()


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
