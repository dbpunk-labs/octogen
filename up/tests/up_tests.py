#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

""" """

import os
import pytest
from rich.live import Live
from rich.console import Console
from og_up.up import run_with_realtime_print
from og_up.up import download_model
from og_up.up import load_docker_image
from rich.console import Group


def test_run_print():
    use_dir = os.path.expanduser("~")
    command = ["ls", use_dir]
    result_code = 0
    for code, output in run_with_realtime_print(command):
        result_code = code
    assert code == 0, "bad return code"


def test_download_model():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        result_code = download_model(
            live,
            segments,
            repo="TheBloke/CodeLlama-7B-Instruct-GGUF",
            filename="codellama-7b-instruct.Q2_K.gguf",
        )
        assert result_code == 0, "fail to download model"


def test_load_bad_docker_image():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        code = load_docker_image("xxx", "xxxx", live, segments)
        assert code != 0, "loading image should be failed"


def test_load_valid_docker_image():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        code = load_docker_image("v0.4.26", "dbpunk/octogen", live, segments)
        assert code == 0, "loading image should be ok"
