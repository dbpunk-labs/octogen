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
    name="og_kernel",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="codego.me@gmail.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=[
        "og_kernel",
        "og_kernel.kernel",
        "og_kernel.server",
    ],
    package_dir={
        "og_kernel": "src/og_kernel",
        "og_kernel.kernel": "src/og_kernel/kernel",
        "og_kernel.server": "src/og_kernel/server",
    },
    install_requires=[
        "og_proto",
        "grpc-google-iam-v1>=0.12.6",
        "grpcio-tools>=1.57.0",
        "ipykernel>=6.25.1",
        "jupyter_client>=8.3.0",
        "matplotlib>=3.7.2",
        "pandas",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "og_kernel_rpc_server = og_kernel.server.kernel_rpc_server:server_main",
            "og_kernel_app = og_kernel.kernel.kernel_app:run_app",
        ]
    },
)
