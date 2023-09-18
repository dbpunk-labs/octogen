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
    name="octopus_proto",
    version="0.3.6",
    description="Open source code interpreter agent for LLM",
    author="imotai",
    author_email="wangtaize@dbpunk.com",
    url="https://github.com/dbpunk-labs/octopus",

    packages=[
        "octopus_proto",
    ],

    package_dir={
        "octopus_proto": "src/octopus_proto",
    },

    package_data={"octopus_proto": ["*.pyi"]},

    install_requires=[
        "grpc-google-iam-v1>=0.12.6",
        "grpcio-tools>=1.57.0",
    ],
    entry_points={
    },
)
