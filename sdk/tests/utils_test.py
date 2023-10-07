#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

""" """
import pytest
import json
from og_sdk.utils import process_char_stream


def test_process_char_stream():
    stream0 = "  Downloading pyfiglet-1.0.2-py3-none-any.whl (1.1 MB)\r\n\x1b[?25l     \x1b[38;5;237m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\x1b[0m \x1b[32m0.0/1.1 MB\x1b[0m \x1b[31m?\x1b[0m eta \x1b[36m-:--:--\x1b[0m"
    stream1 = "\r\x1b[2K     \x1b[38;5;237m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\x1b[0m \x1b[32m0.0/1.1 MB\x1b[0m \x1b[31m?\x1b[0m eta \x1b[36m-:--:--\x1b[0m"
    output1 = process_char_stream(stream0 + stream1)
    output2 = process_char_stream(output1 + stream1)
    assert output1 == output2


