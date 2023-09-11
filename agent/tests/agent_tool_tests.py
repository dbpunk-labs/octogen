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
from octopus_agent.tools import OctopusAPIJsonOutput, OctopusAPIMarkdownOutput
from octopus_kernel.sdk.kernel_sdk import KernelSDK

logger = logging.getLogger(__name__)
api_base = "127.0.0.1:9527"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"
api_data_dir = "/tmp/ws1"


@pytest.fixture
def kernel_sdk():
    sdk = KernelSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    sdk.close()


@pytest.mark.asyncio
async def test_async_smoke_test(kernel_sdk):
    code = "print('hello world!')"
    sdk = kernel_sdk
    api = OctopusAPIJsonOutput(sdk, api_data_dir)
    result = await api.arun(code)
    assert not result["result"]
    assert result["stdout"] == "hello world!\n"


@pytest.mark.asyncio
async def test_get_result(kernel_sdk):
    sdk = kernel_sdk
    code = "5"
    api = OctopusAPIJsonOutput(sdk, api_data_dir)
    result = await api.arun(code)
    assert result["result"]
    assert result["result"] == "5"
    assert not result["stdout"]
    assert not result["stderr"]
    assert not result["error"]


@pytest.mark.asyncio
async def test_sync_smoke_test_markdown(kernel_sdk):
    sdk = kernel_sdk
    code = "print('hello world!')"
    api = OctopusAPIMarkdownOutput(sdk, api_data_dir)
    result = await api.arun(code)
    assert result.find("The result") < 0
    assert result.find("The stdout") >= 0
    logger.info(result)


@pytest.mark.asyncio
async def test_get_result_markdown(kernel_sdk):
    sdk = kernel_sdk
    code = "5"
    api = OctopusAPIMarkdownOutput(sdk, api_data_dir)
    result = await api.arun(code)
    assert result
    logger.info(result)


@pytest.mark.asyncio
async def test_display_result(kernel_sdk):
    sdk = kernel_sdk
    code = """
import matplotlib.pyplot as plt 
import numpy as np

# Create a pie chart
data = np.array([10, 20, 30, 40])
labels = ['Category 1', 'Category 2', 'Category 3', 'Category 4']

plt.pie(data, labels=labels, autopct='%1.1f%%')
plt.title('Pie Chart')
plt.show() 
"""
    api = OctopusAPIJsonOutput(sdk, api_data_dir)
    result = await api.arun(code)
    assert result["result"]
    assert result["result"].find("image/png") >= 0
    assert not result["stdout"]
    assert not result["stderr"]
    assert not result["error"]
