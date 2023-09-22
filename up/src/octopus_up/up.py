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

"""

"""
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
from octopus_agent.utils import process_char_stream

OCTOPUS_TITLE = "🐙[bold red]Octopus Up"
USE_SHELL = sys.platform.startswith( "win" )
OCTOPUS_GITHUB_REPOS="dbpunk-labs/octopus"
def random_str(n):
    # using random.choices()
    # generating random strings
    res = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return str(res)
def run_with_realtime_print(command,
                            universal_newlines = True,
                            useshell = USE_SHELL,
                            env = os.environ,
                            print_output = True):
    try:
        p = subprocess.Popen( command,
                              stdout = subprocess.PIPE,
                              stderr = subprocess.STDOUT,
                              shell = useshell,
                              env = env )
        text_fd = io.TextIOWrapper(p.stdout, newline=os.linesep)
        while True:
            chunk = text_fd.read(20)
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
    title=OCTOPUS_TITLE,
):
    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("Status", no_wrap=True, justify="center")
    table.add_column("Step", no_wrap=True, justify="center", style="bold red")
    table.add_column("Content", no_wrap=True, justify="center")
    for status, step, segment in segments:
        table.add_row(status, step, segment)
    live.update(
        table
    )
    live.refresh()

def get_latest_release_version(repo_name, live, segments):
    """
    get the latest release version
    """
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step ="Get octopus version"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    r = requests.get(f'https://api.github.com/repos/{repo_name}/releases/latest')
    old_segment = segments.pop()
    version = r.json()['name']
    segments.append(("✅", "Get octopus version", version))
    refresh(live, segments)
    return version

def download_model(live, segments, repo="TheBloke/CodeLlama-7B-Instruct-GGUF",
                                   filename="codellama-7b-instruct.Q4_K_M.gguf"):

    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step ="Download CodeLlama"
    output = ""
    segments.append((spinner, step, ""))
    for code, chunk in run_with_realtime_print(command = ["octopus_download", '--repo', repo, '--filename',
        filename]):
        output += chunk
        output = process_char_stream(output)
        old_segment = segments.pop()
        segments.append((old_segment[0], old_segment[1], output))
        refresh(live, segments)
    old_segment = segments.pop()
    segments.append(("✅", step, filename))
    refresh(live, segments)

def load_docker_image(version,
                      image_name,
                      repo_name,
                      live,
                      segments,
                      chunk_size=1024):
    """
    download the image file and load it into docker
    """
    full_name = f"{image_name}:{version}"
    output = ""
    for code, chunk in run_with_realtime_print(command=['docker', 'images',
        f'{image_name}:{version}']):
        output += chunk
    if output.find(image_name) >= 0:
        segments.append(("✅", "Load Octopus Image", f"{image_name}:{version}"))
        refresh(live, segments)
        return
    tmp_filename = Path(gettempdir()) / "".join(
        random.choices(string.ascii_lowercase, k=16)
    )
    url = f"https://github.com/{repo_name}/releases/download/{version}/octopus_image_{version}.tar.gz"
    resp = requests.get(url, stream=True, allow_redirects=True)
    total = int(resp.headers.get('content-length', 0))
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step ="Download Octopus Image"
    content_bar = ProgressBar(width=50, total=total)
    segments.append((spinner, step, content_bar))
    refresh(live, segments)
    downloaded_data = 0
    with open(tmp_filename, 'wb+') as fd:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = fd.write(data)
            downloaded_data += size
            content_bar.update(downloaded_data)
            refresh(live, segments)
    old_segment = segments.pop()
    segments.append(("✅", old_segment[1], f"{total/1024/1024}M"))
    refresh(live, segments)
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step ="Load Octopus Image"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    return_code = 0
    for code, msg in run_with_realtime_print(command=['docker', 'load', '-i', tmp_filename],
            print_output=False):
        return_code = code
    if return_code  == 0:
        old_segment = segments.pop()
        segments.append(("✅", old_segment[1], old_segment[2]))
    else:
        segments.append(("❌", old_segment[1], old_segment[2]))
    refresh(live, segments)
    return code

def choose_api_service(console):
    mk = """Choose your favourite LLM
1. Codellama-7B. this choice will download the model from huggingface
2. OpenAI. this choice will require the api key of OpenAI
"""
    console.print(Markdown(mk))
    choice = Prompt.ask("Choices", choices=["1", "2"], default="1:Codellama-7B")
    if choice == "2":
        key = Prompt.ask("Enter OpenAI Key")
        model = Prompt.ask("Enter OpenAI Model", default="gpt-3.5-turbo-16k-0613")
        return choice, key, model
    return choice, "", ""


def generate_agent_common(fd, rpc_key):
    fd.write("rpc_host=0.0.0.0\n")
    fd.write("rpc_port=9528\n")
    fd.write(f"admin_key={rpc_key}\n")
    fd.write("max_file_size=202400000\n")
    fd.write("max_iterations=8\n")
    fd.write("db_path=/app/agent/octopus.db\n")

def generate_agent_openai(live, segments, install_dir, admin_key,
        openai_key, openai_model):
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

def start_service(live, segments, install_dir, image_name, version, is_codellama="1"):
    full_name = f"{image_name}:{version}"
    command = ["docker", "run","-p", "127.0.0.1:9528:9528", "-v", f"{install_dir}:/app", "-dt", f"{full_name}", "bash",
            "/bin/start_all.sh","/app", is_codellama]
    result_code = 0
    output = ""
    for code, chunk in run_with_realtime_print(command=command):
        result_code = code
        output += chunk
        pass

    if result_code == 0:
        segments.append(("✅", "Start octopus service", ""))
    else:
        segments.append(("❌", "Start octopus service", output))
    refresh(live, segments)
    return result_code

def update_cli_config(live, segments, api_key, cli_dir):
    config_path = f"{cli_dir}/config"
    with open(config_path, "w+") as fd:
        fd.write("endpoint=127.0.0.1:9528\n")
        fd.write(f"api_key={api_key}\n")
    segments.append(("✅", "Update cli config", ""))
    refresh(live, segments)

@click.command("init")
@click.option('--image_name', default="ghcr.io/dbpunk-labs/octopus", help='the octopus image name')
@click.option('--repo_name', default=OCTOPUS_GITHUB_REPOS, help='the github repo of octopus')
@click.option('--install_dir', default="~/.octopus/app", help='the install dir of octopus')
@click.option('--cli_dir', default="~/.octopus/", help='the cli dir of octopus')
def init_octopus(image_name, repo_name, install_dir, cli_dir):
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
    choice, key, model = choose_api_service(console)
    segments = []
    with Live(Group(*segments), console=console) as live:
        version = get_latest_release_version(repo_name, live, segments)
        load_docker_image(version, image_name, repo_name, live, segments)
        download_model(live, segments)
        kernel_key = random_str(32)
        admin_key = random_str(32)
        generate_kernel_env(live, segments, real_install_dir, kernel_key)
        if choice == "1":
            generate_agent_codellama(live, segments, real_install_dir, admin_key)
            if start_service(live, segments, real_install_dir, image_name, version) == 0:
                update_cli_config(live, segments, kernel_key, real_cli_dir)
                console.log(f"👍 install octopus service done!")
        else:
            generate_agent_openai(live, segments, real_install_dir, admin_key, key, model)
            if start_service(live, segments, real_install_dir, image_name, version,
                    is_codellama="0") == 0:
                update_cli_config(live, segments, kernel_key, real_cli_dir)
                console.log(f"👍 install octopus service done!")
