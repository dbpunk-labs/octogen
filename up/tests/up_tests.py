#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

""" """

import os
import sys
import pytest
import tempfile
from rich.live import Live
from rich.console import Console
from og_up.up import run_with_realtime_print
from og_up.up import download_model
from og_up.up import load_docker_image
from og_up.up import get_latest_release_version
from og_up.up import start_octogen_for_codellama
from og_up.up import random_str
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


def test_get_version():
    repo = "imotai/test_repos"
    console = Console()
    segments = []
    temp_dir = tempfile.mkdtemp(prefix="octogen")
    with Live(Group(*segments), console=console) as live:
        version = get_latest_release_version(repo, live, segments)
        assert "v0.1.0" == version


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_start_codellama_smoketest():
    console = Console()
    segments = []
    install_dir = tempfile.mkdtemp(prefix="octogen")
    cli_install_dir = tempfile.mkdtemp(prefix="octogen")
    admin_key = random_str(32)
    kernel_key = random_str(32)
    with Live(Group(*segments), console=console) as live:
        code = load_docker_image("v0.4.26", "dbpunk/octogen", live, segments)
        assert code == 0, "bad result code of loading docker image"
        result = start_octogen_for_codellama(
            live,
            segments,
            "TheBloke/CodeLlama-7B-Instruct-GGUF",
            "codellama-7b-instruct.Q2_K.gguf",
            install_dir,
            cli_install_dir,
            admin_key,
            kernel_key,
            "dbpunk/octogen",
            "v0.4.26",
        )
        assert result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_load_bad_docker_image():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        code = load_docker_image("xxx", "xxxx", live, segments)
        assert code != 0, "loading image should be failed"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_load_valid_docker_image():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        code = load_docker_image("v0.4.26", "dbpunk/octogen", live, segments)
        assert code == 0, "loading image should be ok"
