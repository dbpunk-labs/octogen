#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

"""
"""

import os
from og_up.up import run_with_realtime_print

import pytest

def test_run_print():
    use_dir = os.path.expanduser("~")
    command = ["ls", use_dir]
    result_code = 0
    for code , output in run_with_realtime_print(command):
        result_code = code
    assert code == 0, "bad return code"



