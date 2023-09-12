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
import click
import asyncio
from octopus_agent.agent_sdk import AgentSDK


async def add_kernel(endpoint, api_key, kernel_endpoint, kernel_api_key):
    sdk = AgentSDK(endpoint, api_key)
    sdk.connect()
    try:
        await sdk.add_kernel(kernel_api_key, kernel_endpoint)
        print("add kernel %s done" % kernel_endpoint)
    except Exception as ex:
        print("add kernel %s failed %s" % (kernel_endpoint, ex))


@click.command()
@click.option("--kernel_endpoint", help="the endpoint of kernel")
@click.option("--kernel_api_key", help="the api key of kernel")
@click.option("--agent_endpoint", help="the endpoint of agent")
@click.option("--admin_key", help="the admin key of agent")
def setup(kernel_endpoint, kernel_api_key, agent_endpoint, admin_key):
    if not kernel_endpoint or not kernel_api_key or not admin_key or not agent_endpoint:
        print("kernel_endpoint or kernel_api_key or admin key is empty")
        return
    asyncio.run(add_kernel(agent_endpoint, admin_key, kernel_endpoint, kernel_api_key))
