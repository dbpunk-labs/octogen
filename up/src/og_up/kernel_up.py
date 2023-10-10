#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

"""

"""
import click
from .utils import run_with_realtime_print
from .up import check_the_env
from .up import load_docker_image
from .up import get_latest_release_version

def get_config(console):
    console.print(Markdown(mk))
    key = Prompt.ask("Agent Key", password=True)
    endpoint = Prompt.ask("Agent Endpoint")
    name = Prompt.ask("Kernel Name")
    return  key, endpoint, name

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
    key, agent_endpoint, kernel_name = get_config(console)
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
        code = load_docker_image(
            version, image_name, live, segments
        )
        if code != 0:
            return

