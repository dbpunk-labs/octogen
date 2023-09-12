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
from octopus_agent.tools import OctopusAPIMarkdownOutput
from octopus_kernel.sdk.kernel_sdk import KernelSDK

logger = logging.getLogger(__name__)
api_base = "127.0.0.1:9527"
api_key = "ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH"


@pytest.fixture
def kernel_sdk():
    sdk = KernelSDK(api_base, api_key)
    sdk.connect()
    yield sdk
    sdk.close()


@pytest.mark.asyncio
async def test_sync_smoke_test_markdown(kernel_sdk):
    sdk = kernel_sdk
    code = "print('hello world!')"
    api = OctopusAPIMarkdownOutput(sdk)
    result = await api.arun(code)
    assert result.find("The result") < 0
    assert result.find("The stdout") >= 0
    logger.info(result)


@pytest.mark.asyncio
async def test_get_result_markdown(kernel_sdk):
    sdk = kernel_sdk
    code = "5"
    api = OctopusAPIMarkdownOutput(sdk)
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
    api = OctopusAPIMarkdownOutput(sdk)
    result = await api.arun(code)
    logger.info(result)
    assert result.find("png") >= 0


@pytest.mark.asyncio
async def test_display_gif_result(kernel_sdk):
    sdk = kernel_sdk
    test_gif_code = """
import numpy as np

import matplotlib.pyplot as plt 
import matplotlib.animation as animation

# Fixing random state for reproducibility
np.random.seed(19680801)
# Fixing bin edges
HIST_BINS = np.linspace(-4, 4, 100)

# histogram our data with numpy
data = np.random.randn(1000)
n, _ = np.histogram(data, HIST_BINS)

def prepare_animation(bar_container):

    def animate(frame_number):
        # simulate new data coming in
        data = np.random.randn(1000)
        n, _ = np.histogram(data, HIST_BINS)
        for count, rect in zip(n, bar_container.patches):
            rect.set_height(count)
        return bar_container.patches
    return animate

fig, ax = plt.subplots()
_, _, bar_container = ax.hist(data, HIST_BINS, lw=1,
                              ec="yellow", fc="green", alpha=0.5)
ax.set_ylim(top=55)  # set safe limit to ensure that all data is visible.

ani = animation.FuncAnimation(fig, prepare_animation(bar_container), 50, 
                              repeat=False, blit=True)
plt.show() 
"""
    api = OctopusAPIMarkdownOutput(sdk)
    result = await api.arun(test_gif_code)
    logger.info(result)
    assert result.find("png") >= 0
