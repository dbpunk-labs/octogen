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
    name="octopus_up",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octopus",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",

    packages=[
        "octopus_up",
    ],

    package_dir={
        "octopus_up": "src/octopus_up",
    },
    install_requires=[
        "requests",
        "docker",
        "tqdm",
        "huggingface_hub"
    ],

    entry_points={
        "console_scripts": [
            "octopus_up = octopus_up.up:init_octopus",
            "octopus_download = octopus_up.model_downloader:download",
        ]
    },

)
