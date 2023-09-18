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
    name="octopus_kernel",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octopus",
    packages=[
        "octopus_kernel",
        "octopus_kernel.kernel",
        "octopus_kernel.server",
        "octopus_kernel.sdk",
    ],
    package_dir={
        "octopus_kernel": "src/octopus_kernel",
        "octopus_kernel.kernel": "src/octopus_kernel/kernel",
        "octopus_kernel.server": "src/octopus_kernel/server",
        "octopus_kernel.sdk": "src/octopus_kernel/sdk",
    },
    install_requires=[
        "octopus_proto",
        "grpc-google-iam-v1>=0.12.6",
        "grpcio-tools>=1.57.0",
        "ipykernel>=6.25.1",
        "jupyter_client>=8.3.0",
        "matplotlib>=3.7.2",
        "imageio",
        "pillow",
        "yfinance",
        "pandas",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "octopus_kernel_rpc_server = octopus_kernel.server.kernel_rpc_server:server_main",
            "octopus_kernel_generate = octopus_kernel.server.kernel_env_sample:generate_sample_env",
            "octopus_kernel_app = octopus_kernel.kernel.kernel_app:run_app",
        ]
    },
)
