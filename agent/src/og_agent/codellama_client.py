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


class CodellamaClient(BaseStreamClient):

    def __init__(self, endpoint, key, prefix, ai_name, user_name, grammar):
        super().__init__(endpoint + "/completion", key)
        self.ai_name = ai_name
        self.user_name = user_name
        self.grammar = grammar
        self.prefix = prefix

    async def prompt(self, user_input, temperature=0, chat_history=""):
        prompt = f"""{self.prefix}
{chat_history}
{self.user_name}: {user_input}
{self.ai_name}:"""
        logging.info(f"{prompt}")
        data = {
            "n_predict": 1024,
            "grammar": self.grammar,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True,
            "repeat_last_n": 256,
            "top_p": 0.9,
            "stop": [
                "</s>",
                "\n",
                "%s:" % self.ai_name,
                "%s:" % self.user_name,
            ],
        }
        async for line in self.arun(data):
            yield line
