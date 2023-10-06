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
        ]
    },
)
