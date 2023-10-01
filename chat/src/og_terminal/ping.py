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
import sys
import os
import click
from og_sdk.agent_sdk import AgentSyncSDK
from rich.console import Console
from dotenv import dotenv_values


@click.command()
@click.option("--octogen_dir", default="~/.octogen", help="the root path of octogen")
def app(octogen_dir):
    console = Console()
    if octogen_dir.find("~") == 0:
        real_octogen_dir = octogen_dir.replace("~", os.path.expanduser("~"))
    else:
        real_octogen_dir = octogen_dir
    if not os.path.exists(real_octogen_dir):
        os.mkdir(real_octopus_dir)
    octogen_config = dotenv_values(real_octogen_dir + "/config")
    console = Console()
    try:
        if "api_key" not in octogen_config or "endpoint" not in octogen_config:
            console.print(
                f"❌ api key and endpoint are required! please check your config {octogen_dir}/config"
            )
            sys.exit(1)
        sdk = AgentSyncSDK(octogen_config["endpoint"], octogen_config["api_key"])
        sdk.connect()
        response = sdk.ping()
        if response.code == 0:
            console.print(f"👍 {response.msg}")
            sys.exit(0)
        else:
            console.print(f"❌ {response.msg}")
            sys.exit(1)
    except Exception as ex:
        console.print(
            f"❌ please check your config {octogen_dir}/config with error {ex}"
        )
