# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import os
import pytest
import asyncio
import logging
import json
import random
import logging
from tempfile import gettempdir
from pathlib import Path
from og_sdk.agent_sdk import AgentSDK
from og_sdk.utils import random_str
from og_proto.agent_server_pb2 import TaskResponse
import pytest_asyncio

logger = logging.getLogger(__name__)
api_base = "127.0.0.1:9528"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"


@pytest_asyncio.fixture
async def agent_sdk():
    sdk = AgentSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    await sdk.close()

def test_connect_bad_endpoint():
    try:
        sdk = AgentSDK("xxx", api_key)
        sdk.connect()
        assert 0, "should not go here"
    except Exception as ex:
        assert 1


@pytest.mark.asyncio
async def test_ping_test_with_bad_kernel_api_key(agent_sdk):
    """
    the ping method will throw an exception if the kernel api key is not valid
    """
    try:
        await agent_sdk.add_kernel("bad_kernel_api_key", "127.0.0.1:9527")
        response = await agent_sdk.ping()
        assert 0, "should not go here"
    except Exception as ex:
        assert 1

@pytest.mark.asyncio
async def test_ping_test(agent_sdk):
    try:
        await agent_sdk.add_kernel(api_key, "127.0.0.1:9527")
        response = await agent_sdk.ping()
        assert response.code == 0
    except Exception as ex:
        assert 0, str(ex)


@pytest.mark.asyncio
async def test_upload_and_download_test(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    path = os.path.abspath(__file__)
    # upload file
    uploaded = await sdk.upload_file(path, "agent_sdk_tests.py")
    assert uploaded
    file_stats = os.stat(path)
    assert file_stats.st_size == uploaded.length, "bad upload_file size"
    # download file
    tmp_dir = gettempdir()
    fullpath = "%s%s%s" % (tmp_dir, os.sep, "agent_sdk_tests.py")
    await sdk.download_file("agent_sdk_tests.py", tmp_dir)
    file_stats2 = os.stat(fullpath)
    assert file_stats.st_size == file_stats2.st_size, "bad download_file size"


@pytest.mark.asyncio
async def test_prompt_smoke_test(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    try:
        responds = []
        async for respond in sdk.prompt("hello"):
            responds.append(respond)
        logger.debug(f"{responds}")
        assert len(responds) > 0, "no responds for the prompt"
        assert responds[len(responds) - 1].response_type == TaskResponse.OnFinalAnswer
        assert (
            responds[len(responds) - 1].final_answer.answer
            == "how can I help you today?"
        )
    except Exception as ex:
        assert 0, str(ex)


@pytest.mark.asyncio
async def test_run_code_test(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    try:
        responds = []
        async for respond in sdk.prompt("write a hello world in python"):
            responds.append(respond)
        logger.debug(f"{responds}")
        assert len(responds) > 0, "no responds for the prompt"
        assert responds[len(responds) - 1].response_type == TaskResponse.OnFinalAnswer
        assert (
            responds[len(responds) - 1].final_answer.answer
            == "this code prints 'hello world'"
        )
    except Exception as ex:
        assert 0, str(ex)


@pytest.mark.asyncio
async def test_run_code_with_error(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    try:
        responds = []
        async for respond in sdk.prompt("error function"):
            responds.append(respond)
        logger.debug(f"{responds}")
        assert len(responds) > 0, "no responds for the prompt"
        assert responds[len(responds) - 3].response_type == TaskResponse.OnStepActionEnd
        assert responds[
            len(responds) - 3
        ].on_step_action_end.has_error, "bad has error result"
        assert responds[len(responds) - 1].response_type == TaskResponse.OnFinalAnswer
        assert (
            responds[len(responds) - 1].final_answer.answer
            == "this code prints 'hello world'"
        )
    except Exception as ex:
        assert 0, str(ex)
