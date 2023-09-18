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
from setuptools import setup, find_packages

setup(
    name="octopus_chat",
    version="0.3.6",
    description="the chat client for open source code interpreter octopus",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octopus",
    packages=[
        "octopus_discord",
        "octopus_terminal",
    ],
    package_dir={
        "octopus_discord": "src/octopus_discord",
        "octopus_terminal": "src/octopus_terminal",
    },
    install_requires=[
        "octopus_agent>=0.1.0",
        "rich>=13.5.2",
        "prompt_toolkit>=3.0.0",
        "click>=8.0.0",
        "discord.py>=2.3.2",
        "clipboard>=0.0.4",
        "Pillow",
        "term-image>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "octopus = octopus_terminal.terminal_chat:app",
            "octopus_ping = octopus_terminal.ping:app",
            "octopus_discord_bot = octopus_discord.discord_chat:run_app",
        ]
    },
)
