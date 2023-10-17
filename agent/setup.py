# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from setuptools import setup, find_packages

setup(
    name="og_agent",
    version="0.3.6",
    description="Open source code interpreter agent",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=[
        "og_agent",
    ],
    package_dir={
        "og_agent": "src/og_agent",
    },
    install_requires=[
        "og_proto",
        "og_kernel",
        "og_sdk",
        "grpcio-tools>=1.57.0",
        "grpc-google-iam-v1>=0.12.6",
        "aiofiles",
        "orm[sqlite]",
        "python-dotenv",
        "openai",
        "aiohttp>=3.8.5",
        "pydantic",
        "tiktoken",
    ],
    package_data={"og_agent": ["*.bnf"]},
    entry_points={
        "console_scripts": [
            "og_agent_rpc_server = og_agent.agent_server:server_main",
            "og_agent_setup = og_agent.agent_setup:setup",
            "og_agent_http_server = og_agent.agent_api_server:run_app",
        ]
    },
)
