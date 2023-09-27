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
    name="og_chat",
    version="0.3.6",
    description="the chat client for open source code interpreter octopus",
    author="imotai",
    author_email="codego.me@gmail.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=[
        "og_discord",
        "og_terminal",
    ],
    package_dir={
        "og_discord": "src/og_discord",
        "og_terminal": "src/og_terminal",
    },
    install_requires=[
        "og_sdk>=0.1.0",
        "rich>=13.5.2",
        "prompt_toolkit>=3.0.0",
        "click>=8.0.0",
        "discord.py>=2.3.2",
        "clipboard>=0.0.4",
        "term-image>=0.7.0",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "og = og_terminal.terminal_chat:app",
            "og_ping = og_terminal.ping:app",
            "og_discord_bot = og_discord.discord_chat:run_app",
        ]
    },
)
