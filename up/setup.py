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
