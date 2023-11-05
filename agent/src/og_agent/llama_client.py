# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import json
import aiohttp
import logging
from .base_stream_client import BaseStreamClient

logger = logging.getLogger(__name__)


class LlamaClient(BaseStreamClient):

    def __init__(self, endpoint, key, grammar):
        super().__init__(endpoint + "/v1/chat/completions", key)
        self.grammar = grammar

    async def chat(self, messages, model, temperature=0, max_tokens=1024, stop=[]):
        data = {
            "messages": messages,
            "temperature": temperature,
            "grammar": self.grammar,
            "stream": True,
            "model": model,
            "max_tokens": max_tokens,
            "top_p": 0.9,
        }
        if stop:
            data["stop"] = stop
        async for line in self.arun(data):
            if len(line) < 6:
                continue
            try:
                content = line[6:]
                logger.debug(f"llama response content: {content}")
                message = json.loads(content)
                yield message
            except Exception as e:
                logger.error("error: %s, content: %s", e, content)
                continue
