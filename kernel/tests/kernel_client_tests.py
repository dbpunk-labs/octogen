# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import os
import asyncio
import random
import pytest
import logging
from og_kernel.kernel.kernel_mgr import KernelManager
from og_kernel.kernel.kernel_client import KernelClient

logger = logging.getLogger(__name__)


class MockContext:
    """
    Mock the grpc request context
    """

    def done(self):
        return False


@pytest.fixture
def kernel_manager():
    config_path = os.path.join("/tmp", str(random.randint(1, 100000)))
    workspace = os.path.join("/tmp", str(random.randint(1, 100000)))
    kernel_manager = KernelManager(config_path, workspace)
    kernel_manager.start()
    yield kernel_manager
    kernel_manager.stop()


@pytest.fixture
def ts_kernel_manager():
    config_path = os.path.join("/tmp", str(random.randint(1, 100000)))
    workspace = os.path.join("/tmp", str(random.randint(1, 100000)))
    kernel_manager = KernelManager(config_path, workspace, "tslab")
    kernel_manager.start()
    yield kernel_manager
    kernel_manager.stop()


@pytest.mark.asyncio
async def test_watching(kernel_manager):
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())

    async def on_message_fn(msg):
        if "text" in msg:
            assert msg["text"] == "Hello, world!"

    await kernel_client.watching(on_message_fn)
    for i in range(1):
        kernel_client.execute("print('Hello, world!')")
        await asyncio.sleep(1)
    await asyncio.sleep(10)
    await kernel_client.stop_watch()
    kernel_client.stop_client()


@pytest.mark.asyncio
async def test_result_occurs(kernel_manager):
    """Test stdout occurs"""
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())
    code = """
5
"""
    kernel_client.execute(code)
    messages = []
    context = MockContext()
    async for msg in kernel_client.read_response(context):
        if not msg:
            break
        messages.append(msg)
    logger.info(f"{messages}")
    filtered = list(filter(lambda x: x["msg_type"] == "execute_result", messages))
    assert len(filtered) > 0
    await asyncio.sleep(2)
    await kernel_client.stop_watch()
    kernel_client.stop_client()


@pytest.mark.asyncio
async def test_stderr_occurs(kernel_manager):
    """Test stderr occurs"""
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())
    code = """
import sys
print('Hello world', file=sys.stderr)
"""
    kernel_client.execute(code)
    messages = []

    context = MockContext()
    async for msg in kernel_client.read_response(context):
        if not msg:
            break
        messages.append(msg)
    filtered = list(filter(lambda x: x["msg_type"] == "stream", messages))
    assert len(filtered) > 0
    assert filtered[0]["content"]["name"] == "stderr"
    await asyncio.sleep(2)
    await kernel_client.stop_watch()
    kernel_client.stop_client()


@pytest.mark.asyncio
async def test_stdout_occurs(kernel_manager):
    """Test stdout occurs"""
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())
    code = """
print("hello world!")
"""
    kernel_client.execute(code)
    messages = []

    context = MockContext()
    async for msg in kernel_client.read_response(context):
        if not msg:
            break
        messages.append(msg)
    filtered = list(filter(lambda x: x["msg_type"] == "stream", messages))
    assert len(filtered) > 0
    assert filtered[0]["content"]["name"] == "stdout"
    await asyncio.sleep(2)
    await kernel_client.stop_watch()
    kernel_client.stop_client()


@pytest.mark.asyncio
async def test_syntax_exception_occurs(kernel_manager):
    """Test exception occurs"""
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())
    code = """
a = 10
b = 20
if (a < b)
    print('a is less than b')
"""
    kernel_client.execute(code)
    messages = []

    context = MockContext()
    async for msg in kernel_client.read_response(context):
        if not msg:
            break
        messages.append(msg)
    assert len(list(filter(lambda x: x["msg_type"] == "error", messages))) > 0
    await asyncio.sleep(2)
    await kernel_client.stop_watch()
    kernel_client.stop_client()


@pytest.mark.asyncio
async def test_generate_pie_chart(kernel_manager):
    """Test generate pie output"""
    kernel_client = KernelClient(kernel_manager.config_path)
    await kernel_client.start_client()
    logger.info("is alive %s", await kernel_client.is_alive())

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
    kernel_client.execute(code)
    messages = []

    context = MockContext()
    async for msg in kernel_client.read_response(context):
        if msg:
            logger.debug(f"{msg}")
            messages.append(msg)
    assert len(list(filter(lambda x: x["msg_type"] == "display_data", messages))) > 0
    await asyncio.sleep(2)
    await kernel_client.stop_watch()
    kernel_client.stop_client()
