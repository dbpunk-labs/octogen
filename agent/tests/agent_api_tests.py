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
from og_sdk.agent_sdk import AgentProxySDK
from og_sdk.utils import random_str
from og_proto.agent_server_pb2 import TaskRespond
from og_agent import agent_api_server

logger = logging.getLogger(__name__)
api_base = "127.0.0.1:9528"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"


@pytest.fixture
def agent_sdk():
    sdk = AgentProxySDK(api_base)
    sdk.connect()
    yield sdk


@pytest.mark.asyncio
async def test_helloworld_test(agent_sdk):
    await agent_sdk.add_kernel(api_key, "127.0.0.1:9527", api_key)
    agent_api_server.agent_sdk = agent_sdk
    request = agent_api_server.TaskRequest(
        prompt="hello", token_limit=0, llm_model_name="", input_files=[], context_id=""
    )
    responds = []
    async for respond in agent_api_server.run_task(request, api_key):
        responds.append(json.loads(respond))
    logger.debug(f"{responds}")
    assert len(responds) > 0, "no responds for the prompt"
    assert (
        responds[len(responds) - 1]["step_type"]
        == agent_api_server.StepResponseType.OnFinalAnswer
    )
    assert (
        responds[len(responds) - 1]["final_answer"]["answer"]
        == "how can I help you today?"
    )


@pytest.mark.asyncio
async def test_run_code_test(agent_sdk):
    agent_api_server.agent_sdk = agent_sdk
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527", api_key)
    request = agent_api_server.TaskRequest(
        prompt="write a hello world in python",
        token_limit=0,
        llm_model_name="",
        input_files=[],
        context_id="",
    )
    responds = []
    async for respond in agent_api_server.run_task(request, api_key):
        responds.append(json.loads(respond))
    logger.debug(f"{responds}")
    assert len(responds) > 0, "no responds for the prompt"
    assert (
        responds[len(responds) - 1]["step_type"]
        == agent_api_server.StepResponseType.OnFinalAnswer
    )
    assert (
        responds[len(responds) - 1]["final_answer"]["answer"]
        == "this code prints 'hello world'"
    )
