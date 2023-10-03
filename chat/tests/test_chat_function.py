#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

""" """

from og_terminal.terminal_chat import gen_a_random_emoji
from og_terminal.terminal_chat import parse_numbers


def test_gen_a_random_emoji():
    assert gen_a_random_emoji()


def test_parse_number():
    test_text = "/cc0"
    numbers = parse_numbers(test_text)
    assert numbers
    assert numbers[0] == "0"


