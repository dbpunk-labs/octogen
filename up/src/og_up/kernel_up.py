#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

""" """
import click
from .utils import run_with_realtime_print
from .up import check_the_env
from .up import load_docker_image
from .up import get_latest_release_version
from .up import ping_agent_service
from .up import stop_service
from .up import generate_kernel_env
from .up import random_str
from rich.spinner import Spinner
from rich.console import Group
from dotenv import dotenv_values
from og_sdk.agent_sdk import AgentSyncSDK


def get_config(console):
    console.print(Markdown(mk))
    key = Prompt.ask("Agent Key", password=True)
    endpoint = Prompt.ask("Agent Endpoint")
    name = Prompt.ask("Kernel Name")
    port = Prompt.ask("Kernel Port")
    return key, endpoint, name, port


def start_kernel_service(
    live, segments, install_dir, image_name, version, kernel_name, kernel_port
):
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    step = "Start kernel service"
    output = ""
    vender = "docker"
    segments.append((spinner, step, ""))
    refresh(live, segments)
    stop_service(kernel_name)
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
        f"127.0.0.1:{kernel_port}:{kernel_port}",
        "-v",
        f"{install_dir}:/app",
        "-dt",
        f"{full_name}",
        "bash",
        "/bin/start_kernel.sh",
        "/app",
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
        segments.append(("✅", "Start kernel service", ""))
    else:
        segments.append(("❌", "Start kernel service", output))
    refresh(live, segments)
    return result_code


@click.command("init")
@click.option("--image_name", default="dbpunk/octogen", help="the octogen image name")
@click.option(
    "--install_dir", default="~/kernel/apps", help="the install dir of kernel"
)
@click.option("--octogen_version", default="", help="the version of octogen")
def init_kernel(
    image_name,
    install_dir,
    octogen_version,
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
    key, agent_endpoint, kernel_name, kernel_port = get_config(console)
    kernel_dir = "/".join[real_install_dir, kernel_name]
    os.makedirs(kernel_dir, exist_ok=True)
    segments = []
    with Live(Group(*segments), console=console) as live:
        if octogen_version:
            version = octogen_version
        else:
            version = get_latest_release_version(repo_name, live, segments)
        check_result, _ = check_the_env(live, segments, need_container=True)
        if not check_result:
            segments.append(("❌", "Setup kernel service failed", ""))
            refresh(live, segments)
        code = load_docker_image(version, image_name, live, segments)
        if code != 0:
            return
        kernel_key = random_str(32)
        env_path = kernel_dir + "/kernel/" + ".env"
        if not os.path.exits(env_path):
            generate_kernel_env(live, segments, kernel_dir, kernel_key, kernel_port)
        else:
            config = dotenv_values(env_path)
            kernel_key = config.get("rpc_key", "")
            if kernel_key:
                segments.append(("✅", "Use the exist kernel config", ""))
                refresh(live, segments)
                kernel_port = config.get("rpc_port")
            else:
                segments.append(("❌", "Bad kernel config", ""))
                refresh(live, segments)
                return
        code = start_kernel_service(
            live, segments, kernel_dir, image_name, version, kernel_name, kernel_port
        )
        if code != 0:
            return
        if not add_kernel_endpoint(
            live, segments, key, agent_endpoint, kernel_key, f"127.0.0.1:{kernel_port}"
        ):
            segments.append(("❌", "Setup kernel service failed", ""))
            refresh(live, segments)
            return 

        if ping_agent_service(live, segments, kernel_key, api_base=agent_endpoint):
            segments.append(("👍", "Setup kernel service done", ""))
            refresh(live, segments)
        else:
            segments.append(("❌", "Setup kernel service failed", ""))
            refresh(live, segments)


