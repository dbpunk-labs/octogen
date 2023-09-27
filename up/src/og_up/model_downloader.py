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
import os
import click
from huggingface_hub import hf_hub_download


@click.command()
@click.option("--repo", help="the repo of huggingface")
@click.option("--filename", help="the filename of model")
@click.option(
    "--cache_dir", default="~/.octogen/app/cache", help="the cache_dir of huggingface"
)
@click.option(
    "--local_dir", default="~/.octogen/app/model", help="the local dir of huggingface"
)
@click.option("--socks_proxy", default="", help="the socks proxy url")
def download(repo, filename, cache_dir, local_dir, socks_proxy):
    if local_dir.find("~") == 0:
        real_local_dir = local_dir.replace("~", os.path.expanduser("~"))
    else:
        real_local_dir = local_dir
    if cache_dir.find("~") == 0:
        real_cache_dir = cache_dir.replace("~", os.path.expanduser("~"))
    else:
        real_cache_dir = cache_dir

    os.makedirs(real_cache_dir, exist_ok=True)
    os.makedirs(real_local_dir, exist_ok=True)
    proxies = {}
    if socks_proxy:
        proxies = {"http": socks_proxy, "https": socks_proxy}
    hf_hub_download(
        repo_id=repo,
        filename=filename,
        cache_dir=real_cache_dir,
        local_dir=real_local_dir,
        proxies=proxies,
    )
