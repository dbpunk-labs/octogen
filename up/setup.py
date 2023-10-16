# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from setuptools import setup, find_packages

setup(
    name="og_up",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="codego.me@gmail.com",
    url="https://github.com/dbpunk-labs/octogen",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=[
        "og_up",
    ],
    package_dir={
        "og_up": "src/og_up",
    },
    install_requires=["og_sdk", "requests", "huggingface_hub", "rich", "click"],
    entry_points={
        "console_scripts": [
            "og_up = og_up.up:init_octogen",
            "og_kernel_up = og_up.kernel_up:init_kernel",
            "og_download = og_up.model_downloader:download",
        ]
    },
)
