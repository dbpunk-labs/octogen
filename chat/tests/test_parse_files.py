#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

from og_terminal.utils import parse_file_path


def test_parse_file_path():
    prompt = "convert the file /up /home/test.pdf to text"
    paths = parse_file_path(prompt)
    assert len(paths) == 1, "bad file path count"
    assert paths[0] == "/home/test.pdf", "bad file path "
