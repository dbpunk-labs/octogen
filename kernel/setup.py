# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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
