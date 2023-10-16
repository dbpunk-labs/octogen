# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from setuptools import setup, find_packages

setup(
    name="og_chat",
    version="0.3.6",
    description="the chat client for open source code interpreter octogen",
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
