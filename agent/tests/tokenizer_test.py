# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import logging
import io
from og_agent.tokenizer import tokenize

logger = logging.getLogger(__name__)


def test_parse_explanation():
    arguments = """{"function_call":"execute", "arguments": {"explanation":"h"""
    for token_state, token in tokenize(io.StringIO(arguments)):
        logger.info(f"token_state: {token_state}, token: {token}")
