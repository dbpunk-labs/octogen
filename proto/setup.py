# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from setuptools import setup, find_packages

setup(
    name="og_proto",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="codego.me@gmail.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description= open('README.md').read(),
    long_description_content_type='text/markdown',

    packages=[
        "og_proto",
    ],

    package_dir={
        "og_proto": "src/og_proto",
    },

    package_data={"og_proto": ["*.pyi"]},

    install_requires=[
        "grpc-google-iam-v1>=0.12.6",
        "grpcio-tools>=1.57.0",
    ],

    entry_points={
    },

)
