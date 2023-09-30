#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

"""

"""

from og_terminal.utils import  parse_file_path


def test_parse_file_path():
    prompt = "convert the file /up /home/test.pdf to text"
    paths = parse_file_path(prompt)
    assert len(paths) == 1, "bad file path count"
    assert paths[0] == '/home/test.pdf', "bad file path "
