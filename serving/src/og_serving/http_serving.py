# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import os
import sys
import uvicorn
import logging
from dotenv import dotenv_values
from .server_app import create_app, Settings
from llama_cpp.llama_chat_format import register_chat_format, ChatFormatterResponse, _map_roles, _format_add_colon_single
from llama_cpp import llama_types
from typing import Any, List

config = dotenv_values(".env")

settings = Settings(_env_file="model.env")
LOG_LEVEL = (
    logging.DEBUG if config.get("log_level", "info") == "debug" else logging.INFO
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@register_chat_format("phind")
def format_phind(
    messages: List[llama_types.ChatCompletionRequestMessage],
    **kwargs: Any,
) -> ChatFormatterResponse:
    _roles = dict(user="### User Message", assistant="### Assistant")
    _sep = "\n\n"
    _system_message = "### System Prompt\nYou are an intelligent programming assistant."
    for message in messages:
        if message["role"] == "system" and message["content"]:
            _system_message = f"""### System Prompt\n{message['content']}"""
    _messages = _map_roles(messages, _roles)
    _messages.append((_roles["assistant"], None))
    _prompt = _format_add_colon_single(_system_message, _messages, _sep)
    return ChatFormatterResponse(prompt=_prompt)


def run_serving():
    app = create_app(settings)
    host = config.get("host", "localhost")
    port = int(config.get("port", "8080"))
    logger.info(f"Starting serving at {host}:{port}")
    uvicorn.run(app, host=host, port=port)
