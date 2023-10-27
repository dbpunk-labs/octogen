# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import click
import requests
import random
import string
import os
import subprocess
import sys
import time
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
from og_sdk.agent_sdk import AgentSyncSDK
from .utils import run_with_realtime_print

OCTOGEN_TITLE = "🐙[bold red]Octogen Up"
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
    for code, output in run_with_realtime_print(
        command=["pip", "install", "-U", "og_proto", "og_sdk", "og_chat"]
    ):
        outputs += output
        result_code = code
    if result_code == 0:
        segments.pop()
        segments.append(("✅", "Install octogen terminal cli", ""))
        refresh(live, segments)
        return True
    else:
        segments.pop()
        segments.append(("❌", "Install octogen terminal cli", outputs))
        refresh(live, segments)
        return False


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


def check_container_vender(vender):
    command = [vender, "version", "--help"]
    all_output = ""
    result_code = 0
    for code, output in run_with_realtime_print(command):
        result_code = code
        all_output += output
    if result_code != 0:
        return False, f"{vender} is required"
    if all_output.lower().find("json") < 0:
        return False, f"Upgrade the {vender} to support json format"
    # check alive
    command = [vender, "ps"]
    result_code = 0
    for code, _ in run_with_realtime_print(command):
        result_code = code
    if result_code != 0:
        return False, f"{vender} is not running"
    return True, "ok"


def check_the_env(live, segments, need_container=True, use_podman=False):
    # check the python version
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Check the environment"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    version_ctrl = sys.version.split(" ")[0].split(".")
    if version_ctrl[0] != "3":
        old_segment = segments.pop()
        segments.append(("❌", "Check the environment", "Python3 is required"))
        refresh(live, segments)
        return False, "Python3 is required"
    if int(version_ctrl[1]) < 10:
        old_segment = segments.pop()
        segments.append(("❌", "Check the environment", "Python3.10 is required"))
        refresh(live, segments)
        return False, "Python3.10 is required"
    if need_container:
        vender = "docker" if not use_podman else "podman"
        result, msg = check_container_vender(vender)
        if not result:
            old_segment = segments.pop()
            segments.append(("❌", "Check the environment", msg))
            refresh(live, segments)
            return False, msg
    old_segment = segments.pop()
    segments.append(("✅", "Check the environment", ""))
    refresh(live, segments)
    return True, ""


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
    version = r.json().get("name", "").strip()
    if not version:
        segments.append(("❌", "Get octogen latest version failed", version))
    else:
        segments.append(("✅", "Get octogen latest version", version))
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
    step = "Download codeLlama"
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


def load_docker_image(
    version, image_name, live, segments, chunk_size=1024, use_podman=False
):
    """
    download the image file and load it into docker
    """
    full_name = (
        f"{image_name}:{version}"
        if not use_podman
        else f"docker.io/{image_name}:{version}"
    )
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Pull octogen image"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    return_code = 0
    output = ""
    vender = "docker" if not use_podman else "podman"
    for code, msg in run_with_realtime_print(command=[vender, "pull", full_name]):
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
    mk = """Choose your favourite Large Language Model
1. OpenAI, Kernel, Agent and Cli will be installed
2. Azure OpenAI, Kernel, Agent and Cli will be installed
3. Codellama, Llama.cpp Model Server, Kernel, Agent and Cli will be installed
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
    fd.write("db_path=/app/agent/db/octogen.db\n")


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
    segments.append(("✅", "Generate agent config", f"{agent_dir}/.env"))
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
    segments.append(("✅", "Generate agent config", f"{agent_dir}/.env"))
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
    segments.append(("✅", "Generate agent config", f"{agent_dir}/.env"))
    refresh(live, segments)


def generate_kernel_env(
    live, segments, install_dir, rpc_key, rpc_port=9527, rpc_host="127.0.0.1"
):
    kernel_dir = f"{install_dir}/kernel"
    kernel_ws_dir = f"{install_dir}/kernel/ws"
    kernel_config_dir = f"{install_dir}/kernel/config"
    os.makedirs(kernel_dir, exist_ok=True)
    os.makedirs(kernel_ws_dir, exist_ok=True)
    os.makedirs(kernel_config_dir, exist_ok=True)
    with open(f"{kernel_dir}/.env", "w+") as fd:
        fd.write("config_root_path=/app/kernel/config\n")
        fd.write("workspace=/app/kernel/ws\n")
        fd.write(f"rpc_host={rpc_host}\n")
        fd.write(f"rpc_port={rpc_port}\n")
        fd.write(f"rpc_key={rpc_key}\n")
    segments.append(("✅", "Generate kernel config", f"{kernel_dir}/.env"))
    refresh(live, segments)


def stop_service(name, use_podman=False):
    vender = "docker" if not use_podman else "podman"
    command = [vender, "ps", "-f", f"name={name}", "--format", "json"]
    output = ""
    for _, chunk in run_with_realtime_print(command=command):
        output += chunk
        pass
    if use_podman and output:
        rows = json.loads(output.strip())
        for row in rows:
            id = row["Id"]
            command = [vender, "kill", id]
            for _, chunk in run_with_realtime_print(command=command):
                pass
    elif output:
        for line in output.split(os.linesep):
            if not line:
                break
            row = json.loads(line.strip())
            id = row["ID"]
            command = [vender, "kill", id]
            for _, chunk in run_with_realtime_print(command=command):
                pass
    command = [vender, "container", "rm", name]
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
    use_podman=False,
):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Start octogen service"
    output = ""
    vender = "docker" if not use_podman else "podman"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    stop_service("octogen", use_podman=use_podman)
    full_name = (
        f"{image_name}:{version}"
        if not use_podman
        else f"docker.io/{image_name}:{version}"
    )
    command = [
        vender,
        "run",
        "--name",
        "octogen",
        "-p",
        "127.0.0.1:9528:9528",
        "-p",
        "127.0.0.1:9529:9529",
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
    time.sleep(6)
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


def add_kernel_endpoint(live, segments, admin_key, kernel_endpoint, api_key, api_base):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Register the kernel endpoint"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    retry_count = 0
    result_code = 0
    msg = ""
    while retry_count <= 10:
        retry_count += 1
        try:
            sdk = AgentSyncSDK(api_base, admin_key)
            sdk.connect()
            response = sdk.add_kernel(api_key, kernel_endpoint)
            result_code = response.code
            if result_code == 0:
                break
            msg = response.msg
            time.sleep(3)
        except Exception as ex:
            result_code = 1
            msg = f"connect to {api_base} failed {ex}"
            time.sleep(3)
    segments.pop()
    if result_code == 0:
        segments.append(("✅", step, ""))
        refresh(live, segments)
        return True
    else:
        segments.append(("❌", step, msg))
        refresh(live, segments)
        return False


def ping_agent_service(live, segments, api_key, api_base="127.0.0.1:9528"):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Ping octogen agent service"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    try:
        sdk = AgentSyncSDK(api_base, api_key)
        sdk.connect()
        response = sdk.ping()
        segments.pop()
        if response.code == 0:
            segments.append(("✅", "Ping octogen agent service", ""))
            return True
        else:
            segments.append(("❌", "Ping octogen agent service", response.msg))
            return False
    except Exception as ex:
        segments.append(("❌", "Ping octogen agent service", str(ex)))
        return False


def start_octogen_for_openai(
    live,
    segments,
    install_dir,
    cli_install_dir,
    admin_key,
    kernel_key,
    image_name,
    version,
    api_key,
    model,
    use_podman=False,
):
    generate_agent_openai(live, segments, install_dir, admin_key, api_key, model)
    if (
        start_service(
            live,
            segments,
            install_dir,
            image_name,
            version,
            is_codellama="0",
            use_podman=use_podman,
        )
        == 0
    ):
        if not add_kernel_endpoint(
            live, segments, admin_key, "127.0.0.1:9527", kernel_key, "127.0.0.1:9528"
        ):
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
        update_cli_config(live, segments, kernel_key, cli_install_dir)
        if ping_agent_service(live, segments, kernel_key):
            segments.append(("👍", "Setup octogen service done", ""))
            refresh(live, segments)
            return True
        else:
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
    else:
        segments.append(("❌", "Setup octogen failed", ""))
        refresh(live, segments)
        return False


def start_octogen_for_azure_openai(
    live,
    segments,
    install_dir,
    cli_install_dir,
    admin_key,
    kernel_key,
    image_name,
    version,
    api_key,
    model,
    api_base,
    use_podman=False,
):
    generate_agent_azure_openai(
        live, segments, install_dir, admin_key, api_key, model, api_base
    )
    if (
        start_service(
            live,
            segments,
            install_dir,
            image_name,
            version,
            is_codellama="0",
            use_podman=use_podman,
        )
        == 0
    ):
        if not add_kernel_endpoint(
            live, segments, admin_key, "127.0.0.1:9527", kernel_key, "127.0.0.1:9528"
        ):
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
        update_cli_config(live, segments, kernel_key, cli_install_dir)
        if ping_agent_service(live, segments, kernel_key):
            segments.append(("👍", "Setup octogen service done", ""))
            refresh(live, segments)
            return True
        else:
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
    else:
        segments.append(("❌", "Setup octogen failed", ""))
        refresh(live, segments)
        return False


def start_octogen_for_codellama(
    live,
    segments,
    model_repo,
    model_filename,
    install_dir,
    cli_install_dir,
    admin_key,
    kernel_key,
    image_name,
    version,
    socks_proxy="",
    use_podman=False,
):
    """
    start the octogen service for codellama
    """

    if download_model(live, segments, socks_proxy, model_repo, model_filename) != 0:
        segments.append(("❌", "Setup octogen service failed", ""))
        refresh(live, segments)
        return False

    generate_agent_codellama(live, segments, install_dir, admin_key)
    if (
        start_service(
            live,
            segments,
            install_dir,
            image_name,
            version,
            is_codellama="1",
            model_filename=model_filename,
            use_podman=use_podman,
        )
        == 0
    ):
        if not add_kernel_endpoint(
            live, segments, admin_key, "127.0.0.1:9527", kernel_key, "127.0.0.1:9528"
        ):
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
        update_cli_config(live, segments, kernel_key, cli_install_dir)
        if ping_agent_service(live, segments, kernel_key):
            segments.append(("👍", "Setup octogen service done", ""))
            refresh(live, segments)
            return True
        else:
            segments.append(("❌", "Setup octogen service failed", ""))
            refresh(live, segments)
            return False
    else:
        segments.append(("❌", "Setup octogen service failed", ""))
        refresh(live, segments)
        return False


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
    default="codellama-7b-instruct.Q5_K_M.gguf",
    help="the model filename in model repo",
)
@click.option(
    "--use_podman",
    is_flag=True,
    help="use podman as the container engine",
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
    use_podman,
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
        run_install_cli(live, segments)
        if choice == "4":
            check_result, _ = check_the_env(live, segments, need_container=False)
            if not check_result:
                segments.append(("❌", "Setup octogen cli failed", ""))
                refresh(live, segments)
                return
            update_cli_config(live, segments, key, real_cli_dir, api_base)
            if ping_agent_service(live, segments, key, api_base):
                segments.append(("👍", "Setup octogen cli done", ""))
            else:
                segments.append(("❌", "Setup octogen cli failed", ""))
            refresh(live, segments)
            return
        check_result, _ = check_the_env(
            live, segments, need_container=True, use_podman=use_podman
        )
        if not check_result:
            segments.append(("❌", "Setup octogen agent service failed", ""))
            refresh(live, segments)
            return
        if octogen_version:
            version = octogen_version
        else:
            version = get_latest_release_version(repo_name, live, segments)

        code = load_docker_image(
            version, image_name, live, segments, use_podman=use_podman
        )
        if code != 0:
            return
        kernel_key = random_str(32)
        admin_key = random_str(32)
        generate_kernel_env(live, segments, real_install_dir, kernel_key)
        if choice == "3":
            # start for codellama
            start_octogen_for_codellama(
                live,
                segments,
                codellama_repo,
                model_filename,
                real_install_dir,
                real_cli_dir,
                admin_key,
                kernel_key,
                image_name,
                version,
                socks_proxy,
                use_podman=use_podman,
            )
        elif choice == "2":
            # start azure openai
            start_octogen_for_azure_openai(
                live,
                segments,
                real_install_dir,
                real_cli_dir,
                admin_key,
                kernel_key,
                image_name,
                version,
                key,
                model,
                api_base,
                use_podman=use_podman,
            )
        else:
            # start for openai
            start_octogen_for_openai(
                live,
                segments,
                real_install_dir,
                real_cli_dir,
                admin_key,
                kernel_key,
                image_name,
                version,
                key,
                model,
                use_podman=use_podman,
            )
