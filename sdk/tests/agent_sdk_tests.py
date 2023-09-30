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
import pytest
import asyncio
import logging
import json
import random
from tempfile import gettempdir
from pathlib import Path
from og_sdk.agent_sdk import AgentSDK
from og_sdk.utils import random_str
from og_proto.agent_server_pb2 import TaskRespond

logger = logging.getLogger(__name__)
api_base = "127.0.0.1:9528"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"


@pytest.fixture
def agent_sdk():
    sdk = AgentSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    sdk.close()


def test_connect_bad_endpoint():
    try:
        sdk = AgentSDK("xxx", api_key)
        sdk.connect()
        assert 0, "should not go here"
    except Exception as ex:
        assert 1


@pytest.mark.asyncio
async def test_ping_test(agent_sdk):
    try:
        response = await agent_sdk.ping()
        assert response.code == 0
    except Exception as ex:
        assert 0, str(ex)


@pytest.mark.asyncio
async def test_upload_and_download_test(agent_sdk):
    try:
        sdk = agent_sdk
        await sdk.add_kernel(api_key, "127.0.0.1:9527")
        path = os.path.abspath(__file__)
        # upload file
        uploaded = await sdk.upload_file(path, "agent_sdk_tests.py")
        file_stats = os.stat(path)
        assert file_stats.st_size == uploaded.length, "bad upload_file size"
        # download file
        tmp_dir = gettempdir()
        fullpath = "%s%s%s" % (tmp_dir.os.sep, "agent_sdk_tests.py")
        await sdk.download_file("agent_sdk_tests.py", tmp_dir)
        file_stats2 = os.stat(fullpath)
        assert file_stats.st_size == file_stats2.st_size, "bad download_file size"
    except Exception as ex:
        assert 0, str(ex)


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
        assert responds[len(responds) - 1].respond_type == TaskRespond.OnFinalAnswerType
        assert (
            responds[len(responds) - 1].final_respond.answer
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
        assert responds[len(responds) - 1].respond_type == TaskRespond.OnFinalAnswerType
        assert (
            responds[len(responds) - 1].final_respond.answer
            == "this code prints 'hello world'"
        )
    except Exception as ex:
        assert 0, str(ex)


@pytest.mark.asyncio
async def test_assemble_test(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    try:
        code = "print('hello')"
        name = random_str(10)
        response = await sdk.assemble(name, code, "python")
        assert response.code == 0, "fail to assemble app"
        apps = await sdk.query_apps()
        app = list(filter(lambda x: x.name == name, apps.apps))
        assert len(app) == 1, "fail to get the app with name " + name
        responds = []
        async for respond in sdk.run(name):
            responds.append(respond)
        assert len(responds) == 3, "bad responds for run application"
        assert responds[0].respond_type == TaskRespond.OnAgentActionType
        assert responds[1].respond_type == TaskRespond.OnAgentActionStdout
        assert responds[2].respond_type == TaskRespond.OnAgentActionEndType
        assert (
            json.loads(responds[0].on_agent_action.input)["code"] == code
        ), "remote code !eq the local code"
        assert responds[1].console_stdout.find("hello") >= 0, "bad output"
    except Exception as ex:
        assert 0, str(ex)


display_image_test_code = """import matplotlib.pyplot as plt
import numpy as np

# Step 2: Create the dataset
categories = ['Category 1', 'Category 2', 'Category 3']
group1_values = [10, 15, 12]
group2_values = [8, 11, 9]

# Step 3: Set the width and positions
bar_width = 0.35
index = np.arange(len(categories))

# Step 4: Create the figure and axis
fig, ax = plt.subplots()

# Step 5: Plot the bars
rects1 = ax.bar(index, group1_values, bar_width, label='Group 1')
rects2 = ax.bar(index + bar_width, group2_values, bar_width, label='Group 2')

# Step 6: Set labels, title, and legend
ax.set_xlabel('Categories')
ax.set_ylabel('Values')
ax.set_title('Grouped Bar Chart')
ax.set_xticks(index + bar_width / 2)
ax.set_xticklabels(categories)
ax.legend()

# Step 7: Show the chart
plt.show()"""


@pytest.mark.asyncio
async def test_assemble_image_test(agent_sdk):
    sdk = agent_sdk
    await sdk.add_kernel(api_key, "127.0.0.1:9527")
    try:
        name = random_str(10)
        response = await sdk.assemble(name, display_image_test_code, "python")
        assert response.code == 0, "fail to assemble app"
        apps = await sdk.query_apps()
        app = list(filter(lambda x: x.name == name, apps.apps))
        assert len(app) == 1, "fail to get the app with name " + name
        responds = []
        async for respond in sdk.run(name):
            responds.append(respond)
        assert len(responds) == 3, "bad responds for run application"
        assert responds[0].respond_type == TaskRespond.OnAgentActionType
        assert responds[1].respond_type == TaskRespond.OnAgentActionStdout
        assert responds[2].respond_type == TaskRespond.OnAgentActionEndType
        assert (
            json.loads(responds[0].on_agent_action.input)["code"]
            == display_image_test_code
        )
        assert responds[1].console_stdout.find("png") > 0, "should output the files"
        assert (
            len(responds[2].on_agent_action_end.output_files) == 1
        ), "should output the files"

    except Exception as ex:
        assert 0, str(ex)
