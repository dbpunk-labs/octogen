# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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
        headers = {"Authorization": self.key}
        async with aiohttp.ClientSession(
            headers=headers, raise_for_status=True
        ) as session:
            async with session.post(self.endpoint, json=request_data) as r:
                async for line in r.content:
                    if line:
                        yield line
