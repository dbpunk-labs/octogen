# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from setuptools import setup, find_packages

setup(
    name="og_serving",
    version="0.3.6",
    description="Open source code interpreter agent",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=[
        "og_serving",
    ],
    package_dir={
        "og_serving": "src/og_serving",
    },
    install_requires=["fastapi", "pydantic_settings"],
    package_data={},
    entry_points={
        "console_scripts": [
            "og_serving_http_server = og_serving.http_serving:run_serving",
        ]
    },
)
