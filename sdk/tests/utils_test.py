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


def test_process_char_stream_case2():
    stream1 = "\rt:   0%|          | 0/518 [00:00<?, ?it/s, now=None]"
    output1 = process_char_stream(stream1)
    stream2 = "\rt:   3%|▎         | 15/518 [00:00<00:03, 137.85it/s, now=None]"
    output2 = process_char_stream(output1 + stream2)
    assert output2 == "t:   3%|▎         | 15/518 [00:00<00:03, 137.85it/s, now=None]"


def test_process_char_stream():
    stream0 = "  Downloading pyfiglet-1.0.2-py3-none-any.whl (1.1 MB)\r\n\x1b[?25l     \x1b[38;5;237m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\x1b[0m \x1b[32m0.0/1.1 MB\x1b[0m \x1b[31m?\x1b[0m eta \x1b[36m-:--:--\x1b[0m"
    stream1 = "\r\x1b[2K     \x1b[38;5;237m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\x1b[0m \x1b[32m0.0/1.1 MB\x1b[0m \x1b[31m?\x1b[0m eta \x1b[36m-:--:--\x1b[0m"
    output1 = process_char_stream(stream0 + stream1)
    output2 = process_char_stream(output1 + stream1)
    assert output1 == output2
    final_stream = "\r1.1 MB 100%\r\n"
    output3 = process_char_stream(output2 + final_stream)
    final_ouput_expected = (
        "  Downloading pyfiglet-1.0.2-py3-none-any.whl (1.1 MB)\n1.1 MB 100%\n"
    )
    assert final_ouput_expected == output3


def test_empty_string():
    assert process_char_stream("") == ""


def test_single_character():
    assert process_char_stream("a") == "a"


def test_multiple_characters():
    assert process_char_stream("abc") == "abc"


def test_backspace():
    assert process_char_stream("ab\b") == "a"


def test_carriage_return():
    assert process_char_stream("ab\r") == "ab"


def test_carriage_return_with_newline():
    assert process_char_stream("ab\r\n") == "ab\n"


def test_backspace_and_carriage_return():
    assert process_char_stream("ab\b\r") == "a"


def test_mixed_escape_characters_and_regular_characters():
    assert process_char_stream("ab\b\r\ncde") == "a\ncde"


def test_special_characters():
    assert (
        process_char_stream("ab!@#$%^&*()_+{}|:\";'<>,.?/`~")
        == "ab!@#$%^&*()_+{}|:\";'<>,.?/`~"
    )
