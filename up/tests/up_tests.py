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
import logging
from rich.live import Live
from rich.console import Console
from og_up.up import run_with_realtime_print
from og_up.up import download_model
from og_up.up import load_docker_image
from og_up.up import get_latest_release_version
from og_up.up import start_octogen_for_codellama
from og_up.up import start_octogen_for_azure_openai
from og_up.up import start_octogen_for_openai
from og_up.up import random_str
from og_up.up import generate_agent_common, generate_agent_azure_openai, generate_agent_openai, generate_agent_codellama
from og_up.up import generate_kernel_env
from og_up.up import check_the_env
from og_up.up import run_install_cli
from rich.console import Group
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def test_generate_kernel_env():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        temp_dir = tempfile.mkdtemp(prefix="octogen")
        rpc_key = "rpc_key"
        generate_kernel_env(live, segments, temp_dir, rpc_key)
        fullpath = f"{temp_dir}/kernel/.env"
        config = dotenv_values(fullpath)
        assert config["rpc_key"] == rpc_key, "bad rpc key"
        assert config["rpc_port"] == "9527", "bad rpc port"


def test_generate_agent_codellama():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        temp_dir = tempfile.mkdtemp(prefix="octogen")
        admin_key = "admin_key"
        generate_agent_codellama(live, segments, temp_dir, admin_key)
        fullpath = f"{temp_dir}/agent/.env"
        config = dotenv_values(fullpath)
        assert config["llm_key"] == "codellama", "bad llm key"
        assert (
            config["llama_api_base"] == "http://127.0.0.1:8080"
        ), "bad codellama server endpoint"
        assert config["admin_key"] == admin_key, "bad admin key"


def test_generate_agent_env_openai():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        temp_dir = tempfile.mkdtemp(prefix="octogen")
        admin_key = "admin_key"
        openai_key = "openai_key"
        model = "gpt-4-0613"
        generate_agent_openai(live, segments, temp_dir, admin_key, openai_key, model)
        fullpath = f"{temp_dir}/agent/.env"
        config = dotenv_values(fullpath)
        assert config["llm_key"] == "openai", "bad llm key"
        assert config["openai_api_key"] == openai_key, "bad api key"
        assert config["openai_api_model"] == model, "bad model"
        assert config["admin_key"] == admin_key, "bad admin key"


def test_generate_agent_env_azure_openai():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        temp_dir = tempfile.mkdtemp(prefix="octogen")
        admin_key = "admin_key"
        openai_key = "openai_key"
        deployment = "octogen"
        api_base = "azure"
        generate_agent_azure_openai(
            live, segments, temp_dir, admin_key, openai_key, deployment, api_base
        )
        fullpath = f"{temp_dir}/agent/.env"
        config = dotenv_values(fullpath)
        assert config["llm_key"] == "azure_openai", "bad llm key"
        assert config["openai_api_base"] == api_base, "bad api base"
        assert config["openai_api_key"] == openai_key, "bad api key"
        assert config["openai_api_deployment"] == deployment, "bad deployment"
        assert config["admin_key"] == admin_key, "bad admin key"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_check_the_env():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        result, msg = check_the_env(live, segments)
        assert result


def test_check_the_env_win():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        result, msg = check_the_env(live, segments, need_container=False)
        assert result


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


def test_install_cli():
    console = Console()
    segments = []
    with Live(Group(*segments), console=console) as live:
        assert run_install_cli(live, segments)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_start_azure_openai_smoketest():
    console = Console()
    segments = []
    install_dir = tempfile.mkdtemp(prefix="octogen")
    cli_install_dir = tempfile.mkdtemp(prefix="octogen")
    admin_key = random_str(32)
    kernel_key = random_str(32)
    with Live(Group(*segments), console=console) as live:
        generate_kernel_env(live, segments, install_dir, kernel_key)
        code = load_docker_image("v0.4.27", "dbpunk/octogen", live, segments)
        assert code == 0, "bad result code of loading docker image"
        result = start_octogen_for_azure_openai(
            live,
            segments,
            install_dir,
            cli_install_dir,
            admin_key,
            kernel_key,
            "dbpunk/octogen",
            "v0.4.27",
            "azure_open_api_key",
            "test_deployment",
            "https://azure_base",
        )
        assert result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_start_openai_smoketest():
    console = Console()
    segments = []
    install_dir = tempfile.mkdtemp(prefix="octogen")
    cli_install_dir = tempfile.mkdtemp(prefix="octogen")
    admin_key = random_str(32)
    kernel_key = random_str(32)
    with Live(Group(*segments), console=console) as live:
        generate_kernel_env(live, segments, install_dir, kernel_key)
        code = load_docker_image("v0.4.27", "dbpunk/octogen", live, segments)
        assert code == 0, "bad result code of loading docker image"
        result = start_octogen_for_openai(
            live,
            segments,
            install_dir,
            cli_install_dir,
            admin_key,
            kernel_key,
            "dbpunk/octogen",
            "v0.4.27",
            "openai_api_key",
            "gpt-3.5-turbo",
        )
        assert result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skip on windows")
def test_start_codellama_smoketest():
    console = Console()
    segments = []
    install_dir = tempfile.mkdtemp(prefix="octogen")
    cli_install_dir = tempfile.mkdtemp(prefix="octogen")
    admin_key = random_str(32)
    kernel_key = random_str(32)
    with Live(Group(*segments), console=console) as live:
        generate_kernel_env(live, segments, install_dir, kernel_key)
        code = load_docker_image("v0.4.27", "dbpunk/octogen", live, segments)
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
            "v0.4.27",
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
