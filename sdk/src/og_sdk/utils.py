# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import re
import string
import random
import aiofiles
import logging
from og_proto import agent_server_pb2, common_pb2
from typing import AsyncIterable

logger = logging.getLogger(__name__)


def generate_chunk(filepath, filename) -> common_pb2.FileChunk:
    try:
        with open(filepath, "rb") as fp:
            while True:
                chunk = fp.read(1024 * 128)
                if not chunk:
                    break
                yield common_pb2.FileChunk(buffer=chunk, filename=filename)
    except Exception as ex:
        logger.error("fail to read file %s" % ex)


async def generate_async_chunk(
    filepath, filename
) -> AsyncIterable[common_pb2.FileChunk]:
    try:
        async with aiofiles.open(filepath, "rb") as afp:
            while True:
                chunk = await afp.read(1024 * 128)
                if not chunk:
                    break
                yield common_pb2.FileChunk(buffer=chunk, filename=filename)
    except Exception as ex:
        logger.error("fail to read file %s", ex)


def process_char_stream(stream):
    buffer = []
    i = 0

    def carriage_return(buf):
        pop_buf = []
        if "\n" in buf:
            for _ in range(buf[::-1].index("\n")):
                pop_buf.append(buf.pop())
            return pop_buf[::-1]
        else:
            pop_buf.extend(buf)
            buf.clear()
            return pop_buf

    last_pop_buf = []
    while i < len(stream):
        c = stream[i]
        if c == "\b":
            if buffer:
                buffer.pop()
            last_pop_buf = []
        elif c == "\r":
            last_pop_buf = carriage_return(buffer)
        elif c == "\n":
            if last_pop_buf:
                buffer.extend(last_pop_buf)
                last_pop_buf = []
            buffer.append(c)
        else:
            last_pop_buf = []
            buffer.append(c)
        i += 1
    if last_pop_buf:
        buffer.extend(last_pop_buf)
    return "".join(buffer)


def clean_code(code: str):
    start_tag = "```"
    end_tag = "```"
    index = code.find(start_tag)
    if index >= 0:
        last = code.rfind(end_tag)
        return code[index + len(start_tag) : last]
    return code


def parse_link(text):
    """Parses a link from markdown text.

    Args:
    text: The markdown text.

    Returns:
    The link text and href, or None if no link is found.
    """
    link_regex = r"\[(.+?)\]\((.+?)\)"
    match = re.search(link_regex, text)
    if match:
        return match.groups()
    else:
        return None, None


def parse_image_filename(string):
    """Parses the image filename from a string.

    Args:
      string: A string containing the image filename.

    Returns:
      The image filename, or None if the filename is not valid.
    """

    pattern = r"octopus_\w+\.(jpg|png|gif)"
    match = re.search(pattern, string)
    if match:
        return match.group()
    else:
        return None


def random_str(n):
    # using random.choices()
    # generating random strings
    res = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return str(res)
