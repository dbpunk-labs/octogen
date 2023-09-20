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
import re
import string
import random


def process_char_stream(stream):
    buffer = []
    i = 0
    while i < len(stream):
        c = stream[i]
        if c in ["\b", "\r"]:
            # Handle escape characters
            escape_dict = {
                "\b": lambda buf: buf.pop() if buf else None,  # backspace
                "\r": lambda buf: [
                    buf.pop() for _ in range(len(buf) - buf[::-1].index("\n") - 1)
                ]
                if "\n" in buf
                else buf.clear(),  # carriage return
            }
            escape_dict[c](buffer)
            i += 1
        else:
            buffer.append(c)
            i += 1
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
