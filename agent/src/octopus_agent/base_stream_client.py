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
import json
import aiohttp
import logging

logger = logging.getLogger(__name__)


class BaseStreamClient:

    def __init__(self, endpoint, key):
        self.endpoint = endpoint
        self.key = key

    async def arun(self, request_data):
        logging.debug(f"{request_data}")
        data = json.dumps(request_data)
        headers = {"Authorization": self.key}
        async with aiohttp.ClientSession(
            headers=headers, raise_for_status=True
        ) as session:
            async with session.post(self.endpoint, data=data) as r:
                async for line in r.content:
                    if line:
                        yield line
