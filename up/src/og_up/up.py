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
import json
import click
import requests
import random
import string
import os
import subprocess
import sys
import io
from pathlib import Path
from tqdm import tqdm
from tempfile import gettempdir
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress_bar import ProgressBar
from rich.live import Live
from rich.spinner import Spinner
from rich.console import Group
from og_sdk.utils import process_char_stream

OCTOGEN_TITLE = "🐙[bold red]Octogen Up"
USE_SHELL = sys.platform.startswith("win")
OCTOGEN_GITHUB_REPOS = "dbpunk-labs/octogen"
Welcome = f"""
Welcome to use {OCTOGEN_TITLE}
"""


def random_str(n):
    # generating random strings
    res = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return str(res)


def run_install_cli(live, segments):
    """
    Install the octogen chat cli
    """
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Install octogen terminal cli"
    output = ""
    segments.append((spinner, step, ""))
    result_code = 0
    refresh(live, segments)
    outputs = ""
    for code, output in run_with_realtime_print(command=["pip", "install", "og_chat"]):
        outputs += output
        result_code = code
    if result_code == 0:
        segments.pop()
        segments.append(("✅", "Install octogen terminal cli", ""))
    else:
        segments.pop()
        segments.append(("❌", "Install octogen terminal cli", outputs))
    refresh(live, segments)


def run_with_realtime_print(
    command, universal_newlines=True, useshell=USE_SHELL, env=os.environ
):
    try:
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=useshell,
            env=env,
        )

        text_fd = io.TextIOWrapper(p.stdout, encoding="utf-8", newline=os.linesep, errors='replace')
        while True:
            chunk = text_fd.read(40)
            if not chunk:
                break
            yield 0, chunk
        p.wait()
        yield p.returncode, ""
    except Exception as ex:
        yield -1, str(ex)


def refresh(
    live,
    segments,
    title=OCTOGEN_TITLE,
):
    table = Table.grid(padding=(0, 1, 0, 0), pad_edge=True)
    table.add_column("Index", no_wrap=True, justify="center")
    table.add_column("Status", no_wrap=True, justify="left")
    table.add_column("Step", no_wrap=True, justify="left")
    table.add_column("Content", no_wrap=True, justify="left")
    for index, (status, step, segment) in enumerate(segments):
        table.add_row(str(index), status, step, segment)
    live.update(table)
    live.refresh()


def get_latest_release_version(repo_name, live, segments):
    """
    get the latest release version
    """
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Get octogen version"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    r = requests.get(f"https://api.github.com/repos/{repo_name}/releases/latest")
    old_segment = segments.pop()
    version = r.json()["name"]
    segments.append(("✅", "Get octogen version", version))
    refresh(live, segments)
    return version


def download_model(
    live,
    segments,
    socks_proxy="",
    repo="TheBloke/CodeLlama-7B-Instruct-GGUF",
    filename="codellama-7b-instruct.Q5_K_S.gguf",
):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Download CodeLlama"
    output = ""
    segments.append((spinner, step, ""))
    refresh(live, segments)
    result_code = 0
    for code, chunk in run_with_realtime_print(
        command=[
            "og_download",
            "--repo",
            repo,
            "--filename",
            filename,
            "--socks_proxy",
            socks_proxy,
        ]
    ):
        result_code = code
        output += chunk
        output = process_char_stream(output)
        old_segment = segments.pop()
        segments.append((old_segment[0], old_segment[1], output))
        refresh(live, segments)

    old_segment = segments.pop()
    if result_code == 0:
        segments.append(("✅", step, filename))
    else:
        segments.append(("❌", step, output))
    refresh(live, segments)
    return result_code


def load_docker_image(version, image_name, repo_name, live, segments, chunk_size=1024):
    """
    download the image file and load it into docker
    """
    full_name = f"{image_name}:{version}"
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Pull Octogen Image"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    return_code = 0
    output = ""
    for code, msg in run_with_realtime_print(command=["docker", "pull", full_name]):
        return_code = code
        output += msg

    old_segment = segments.pop()
    if return_code == 0:
        segments.append(("✅", old_segment[1], full_name))
    else:
        segments.append(("❌", old_segment[1], output))
    refresh(live, segments)
    return code


def choose_api_service(console):
    mk = """Choose your favourite LLM
1. OpenAI, Kernel, Agent and Cli will be installed
2. Azure OpenAI, Kernel, Agent and Cli will be installed
3. Codellama, Model Server, Kernel, Agent and Cli will be installed
4. Octogen(beta), Only Cli will be installed
"""
    console.print(Markdown(mk))
    choice = Prompt.ask("Choices", choices=["1", "2", "3", "4"], default="1:OpenAI")
    if choice == "1":
        key = Prompt.ask("Enter OpenAI Key", password=True)
        model = Prompt.ask("Enter OpenAI Model", default="gpt-3.5-turbo-16k-0613")
        return choice, key, model, ""
    elif choice == "2":
        key = Prompt.ask("Enter Azure OpenAI Key", password=True)
        deployment = Prompt.ask("Enter Azure OpenAI Deployment")
        api_base = Prompt.ask("Enter Azure OpenAI Base")
        return choice, key, deployment, api_base
    elif choice == "4":
        key = Prompt.ask("Enter Octogen Key", password=True)
        api_base = "https://agent.octogen.dev"
        return choice, key, "", api_base
    return choice, "", "", ""


def generate_agent_common(fd, rpc_key):
    fd.write("rpc_host=0.0.0.0\n")
    fd.write("rpc_port=9528\n")
    fd.write(f"admin_key={rpc_key}\n")
    fd.write("max_file_size=202400000\n")
    fd.write("max_iterations=8\n")
    fd.write("db_path=/app/agent/octogen.db\n")


def generate_agent_azure_openai(
    live, segments, install_dir, admin_key, openai_key, deployment, api_base
):
    agent_dir = f"{install_dir}/agent"
    os.makedirs(agent_dir, exist_ok=True)
    with open(f"{agent_dir}/.env", "w+") as fd:
        generate_agent_common(fd, admin_key)
        fd.write("llm_key=azure_openai\n")
        fd.write(f"openai_api_type=azure\n")
        fd.write(f"openai_api_version=2023-07-01-preview\n")
        fd.write(f"openai_api_key={openai_key}\n")
        fd.write(f"openai_api_base={api_base}\n")
        fd.write(f"openai_api_deployment={deployment}\n")
        fd.write("max_file_size=202400000\n")
        fd.write("max_iterations=8\n")
        fd.write("log_level=debug\n")
    segments.append(("✅", "Generate Agent Config", f"{agent_dir}/.env"))
    refresh(live, segments)


def generate_agent_openai(
    live, segments, install_dir, admin_key, openai_key, openai_model
):
    agent_dir = f"{install_dir}/agent"
    os.makedirs(agent_dir, exist_ok=True)
    with open(f"{agent_dir}/.env", "w+") as fd:
        generate_agent_common(fd, admin_key)
        fd.write("llm_key=openai\n")
        fd.write(f"openai_api_key={openai_key}\n")
        fd.write(f"openai_api_model={openai_model}\n")
        fd.write("max_file_size=202400000\n")
        fd.write("max_iterations=8\n")
        fd.write("log_level=debug\n")
    segments.append(("✅", "Generate Agent Config", f"{agent_dir}/.env"))
    refresh(live, segments)


def generate_agent_codellama(live, segments, install_dir, admin_key):
    agent_dir = f"{install_dir}/agent"
    os.makedirs(agent_dir, exist_ok=True)
    with open(f"{agent_dir}/.env", "w+") as fd:
        generate_agent_common(fd, admin_key)
        fd.write("llm_key=codellama\n")
        fd.write("llama_api_base=http://127.0.0.1:8080\n")
        fd.write("llama_api_key=xxx\n")
        fd.write("max_file_size=202400000\n")
        fd.write("max_iterations=8\n")
        fd.write("log_level=debug\n")

    segments.append(("✅", "Generate Agent Config", f"{agent_dir}/.env"))
    refresh(live, segments)


def generate_kernel_env(live, segments, install_dir, rpc_key):
    kernel_dir = f"{install_dir}/kernel"
    kernel_ws_dir = f"{install_dir}/kernel/ws"
    kernel_config_dir = f"{install_dir}/kernel/config"
    os.makedirs(kernel_dir, exist_ok=True)
    os.makedirs(kernel_ws_dir, exist_ok=True)
    os.makedirs(kernel_config_dir, exist_ok=True)
    with open(f"{kernel_dir}/.env", "w+") as fd:
        fd.write("config_root_path=/app/kernel/config\n")
        fd.write("workspace=/app/kernel/ws\n")
        fd.write("rpc_host=127.0.0.1\n")
        fd.write("rpc_port=9527\n")
        fd.write(f"rpc_key={rpc_key}\n")
    segments.append(("✅", "Generate Kernel Config", f"{kernel_dir}/.env"))
    refresh(live, segments)


def stop_service(name):
    command = ["docker", "ps", "-f", f"name={name}", "--format", "json"]
    output = ""
    for _, chunk in run_with_realtime_print(command=command):
        output += chunk
        pass
    if output:
        for line in output.split(os.linesep):
            if not line:
                break
            row = json.loads(line.strip())
            id = row["ID"]
            command = ["docker", "kill", id]
            for _, chunk in run_with_realtime_print(command=command):
                pass

    command = ["docker", "container", "rm", name]
    for _, chunk in run_with_realtime_print(command=command):
        pass


def start_service(
    live,
    segments,
    install_dir,
    image_name,
    version,
    is_codellama="1",
    model_filename="",
):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Start octogen service"
    output = ""
    segments.append((spinner, step, ""))
    refresh(live, segments)
    stop_service("octogen")
    # TODO stop the exist service
    full_name = f"{image_name}:{version}"
    command = [
        "docker",
        "run",
        "--name",
        "octogen",
        "-p",
        "127.0.0.1:9528:9528",
        "-v",
        f"{install_dir}:/app",
        "-dt",
        f"{full_name}",
        "bash",
        "/bin/start_all.sh",
        "/app",
        is_codellama,
        model_filename,
    ]
    result_code = 0
    output = ""
    for code, chunk in run_with_realtime_print(command=command):
        result_code = code
        output += chunk
        pass
    segments.pop()
    if result_code == 0:
        segments.append(("✅", "Start octogen service", ""))
    else:
        segments.append(("❌", "Start octogen service", output))
    refresh(live, segments)
    return result_code


def update_cli_config(live, segments, api_key, cli_dir, api_base="127.0.0.1:9528"):
    config_path = f"{cli_dir}/config"
    with open(config_path, "w+") as fd:
        fd.write(f"endpoint={api_base}\n")
        fd.write(f"api_key={api_key}\n")
    segments.append(("✅", "Update cli config", ""))
    refresh(live, segments)


@click.command("init")
@click.option("--image_name", default="dbpunk/octogen", help="the octogen image name")
@click.option(
    "--repo_name", default=OCTOGEN_GITHUB_REPOS, help="the github repo of octogen"
)
@click.option(
    "--install_dir", default="~/.octogen/app", help="the install dir of octogen"
)
@click.option("--cli_dir", default="~/.octogen/", help="the cli dir of octogen")
@click.option("--octogen_version", default="", help="the version of octogen")
@click.option("--socks_proxy", default="", help="the socks proxy url")
@click.option(
    "--codellama_repo",
    default="TheBloke/CodeLlama-7B-Instruct-GGUF",
    help="the codellama repo of huggingface",
)
@click.option(
    "--model_filename",
    default="codellama-7b-instruct.Q5_K_S.gguf",
    help="the model filename in model repo",
)
def init_octogen(
    image_name,
    repo_name,
    install_dir,
    cli_dir,
    octogen_version,
    socks_proxy,
    codellama_repo,
    model_filename,
):
    if cli_dir.find("~") == 0:
        real_cli_dir = cli_dir.replace("~", os.path.expanduser("~"))
    else:
        real_cli_dir = cli_dir
    if install_dir.find("~") == 0:
        real_install_dir = install_dir.replace("~", os.path.expanduser("~"))
    else:
        real_install_dir = install_dir
    os.makedirs(real_install_dir, exist_ok=True)
    console = Console()
    console.print(Welcome)
    choice, key, model, api_base = choose_api_service(console)
    segments = []
    with Live(Group(*segments), console=console) as live:
        if choice == "4":
            update_cli_config(live, segments, key, real_cli_dir, api_base)
            segments.append(("👍", "Setup octogen done", ""))
            refresh(live, segments)
            return
        if octogen_version:
            version = octogen_version
        else:
            version = get_latest_release_version(repo_name, live, segments)
        code = load_docker_image(version, image_name, repo_name, live, segments)
        if code != 0:
            return
        kernel_key = random_str(32)
        admin_key = random_str(32)
        generate_kernel_env(live, segments, real_install_dir, kernel_key)
        run_install_cli(live, segments)
        if choice == "3":
            if (
                download_model(
                    live, segments, socks_proxy, codellama_repo, model_filename
                )
                != 0
            ):
                segments.append(("❌", "Setup octogen failed", ""))
                refresh(live, segments)
                return
            generate_agent_codellama(live, segments, real_install_dir, admin_key)
            if (
                start_service(
                    live,
                    segments,
                    real_install_dir,
                    image_name,
                    version,
                    is_codellama="1",
                    model_filename=model_filename,
                )
                == 0
            ):
                update_cli_config(live, segments, kernel_key, real_cli_dir)
                segments.append(("👍", "Setup octogen done", ""))
            else:
                segments.append(("❌", "Setup octogen failed", ""))
            refresh(live, segments)
        elif choice == "2":
            generate_agent_azure_openai(
                live, segments, real_install_dir, admin_key, key, model, api_base
            )
            if (
                start_service(
                    live,
                    segments,
                    real_install_dir,
                    image_name,
                    version,
                    is_codellama="0",
                )
                == 0
            ):
                update_cli_config(live, segments, kernel_key, real_cli_dir)
                segments.append(("👍", "Setup octogen done", ""))
            else:
                segments.append(("❌", "Setup octogen failed", ""))
            refresh(live, segments)

        else:
            generate_agent_openai(
                live, segments, real_install_dir, admin_key, key, model
            )
            if (
                start_service(
                    live,
                    segments,
                    real_install_dir,
                    image_name,
                    version,
                    is_codellama="0",
                )
                == 0
            ):
                update_cli_config(live, segments, kernel_key, real_cli_dir)
                segments.append(("👍", "Setup octogen done", ""))
            else:
                segments.append(("❌", "Setup octogen failed", ""))
            refresh(live, segments)
