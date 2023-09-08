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
import secrets


def generate_sample_env():
    print("#the root path used to store the kernel connection config")
    print("config_root_path=/tmp")
    print("#the workspace path used as the notebook workspace")
    print("workspace=/tmp/ws")
    print("#the rpc host")
    print("rpc_host=127.0.0.1")
    print("#rpc key used to verify the request")
    print("rpc_key=%s" % secrets.token_urlsafe(32))
