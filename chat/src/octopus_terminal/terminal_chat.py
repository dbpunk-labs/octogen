#! /usr/bin/env python3
# vim:fenc=utf-8
#

""" """
import sys
import os
import re
import time
import json
import asyncio
import click
import glob
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.console import Group
from rich.panel import Panel
from rich.progress import Progress
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession
from octopus_agent.agent_sdk import AgentSyncSDK
from dotenv import dotenv_values
from prompt_toolkit.completion import Completer, Completion
from .utils import parse_file_path


OCTOPUS_TITLE = "🐙[bold red]Octopus"


class FilePathCompleter(Completer):

    def get_completions(self, document, complete_event):
        index = document.current_line_before_cursor.find("/up ")
        if index >= 0:
            word_before_cursor = document.current_line_before_cursor[
                index + 3 :
            ].strip()
            if word_before_cursor:
                for comp in glob.glob(word_before_cursor + "*"):
                    yield Completion(comp, -len(word_before_cursor))


def check_parameter(octopus_config, console):
    """
    check the parameter
    """
    if "api_key" not in octopus_config or not octopus_config["api_key"]:
        content = """No api key was found, you can get api key from the following ways
* You can use your [self-hosted](https://github.com/dbpunk-labs) agent server api key
* You can apply the api key from [octopus waitlist](https://octopus.dbpunk.com]octopus) directly"""
        mk = Markdown(content)
        console.print(mk)
        return False
    return True


def clean_code(code: str):
    start_tag = "```python"
    end_tag = "```"
    index = code.find(start_tag)
    if index >= 0:
        last = code.rfind(end_tag)
        return code[index + len(start_tag) : last]
    elif code.find(end_tag) >= 0:
        return code.replace("```", "")
    elif code.find("`") == 0:
        return code.replace("`", "")
    else:
        return code


def handle_action_output(segments, respond, live, saved_images, output_images, spinner):
    if not respond.on_agent_action_end:
        return
    output = respond.on_agent_action_end.output
    if not output:
        return
    mk = output
    markdown = Markdown(mk)
    output_images.extend(respond.on_agent_action_end.output_files)
    segments.append(markdown)
    live.update(
        Group(
            Panel(
                Group(*segments),
                title=OCTOPUS_TITLE,
                title_align="left",
                subtitle="[bold]token:%s" % (respond.token_usage),
                subtitle_align="right",
            ),
            spinner,
        )
    )
    live.refresh()


def handle_action_start(segments, respond, live, saved_images, output_images, spinner):
    """Run on agent action."""
    if not respond.on_agent_action:
        return
    action = respond.on_agent_action
    if not action.input:
        return
    arguments = json.loads(action.input)
    if action.tool == "execute_python_code" and action.input:
        explanation = arguments["explanation"]
        markdown = Markdown("\n" + explanation + "\n")
        syntax = Syntax(clean_code(arguments["code"]), "python")
        segments.append(markdown)
        segments.append(syntax)
    elif action.tool == "execute_ts_code" and action.input:
        explanation = arguments["explanation"]
        markdown = Markdown("\n" + explanation + "\n")
        syntax = Syntax(clean_code(arguments["code"]), "ts")
        segments.append(markdown)
        segments.append(syntax)
    elif action.tool == "execute_shell_code" and action.input:
        explanation = arguments["explanation"]
        markdown = Markdown("\n" + explanation + "\n")
        syntax = Syntax(clean_code(arguments["code"]), "ts")
        segments.append(markdown)
        segments.append(syntax)
    elif action.tool == "print_code" and action.input:
        explanation = arguments["explanation"]
        markdown = Markdown("\n" + explanation + "\n")
        syntax = Syntax(clean_code(arguments["code"]), arguments["language"])
        segments.append(markdown)
        segments.append(syntax)
    elif action.tool == "print_final_answer" and action.input:
        mk = """%s""" % (arguments["answer"])
        markdown = Markdown(mk)
        segments.append(markdown)
    live.update(
        Group(
            Panel(
                Group(*segments),
                title=OCTOPUS_TITLE,
                title_align="left",
                subtitle="[bold]token:%s" % (respond.token_usage),
                subtitle_align="right",
            ),
            spinner,
        )
    )
    live.refresh()


def handle_final_answer(segments, respond, live, saved_images, output_images, spinner):
    if not respond.final_respond:
        return
    answer = respond.final_respond.answer
    if not answer:
        return
    mk = Markdown(answer)
    segments.append(mk)
    live.update(
        Group(
            Panel(
                Group(*segments),
                title=OCTOPUS_TITLE,
                title_align="left",
                subtitle="[bold]token:%s iteration:%s model:%s"
                % (respond.token_usage, respond.iteration, respond.model_name),
                subtitle_align="right",
            ),
            spinner,
        )
    )
    live.refresh()


def render_image(images, sdk, image_dir):
    cmd = None
    if "TERM_PROGRAM" in os.environ and os.environ["TERM_PROGRAM"] == "iTerm.app":
        # iterm2
        cmd = "viu -w 45"
    elif "TERM" in os.environ and os.environ["TERM"] == "xterm-kitty":
        # kitty
        cmd = "viu -w 45"
    elif "GNOME_SHELL_SESSION_MODE" in os.environ:
        # use open
        cmd = "open"
    else:
        # not supported
        return
    for image in images:
        sdk.download_file(image, image_dir)
        fullpath = "%s/%s" % (image_dir, image)
        cmd = cmd + " " + fullpath
        os.system(cmd)


def run_chat(prompt, sdk, session, console, spinner_name="hearts", filedir=None):
    """
    run the chat
    """
    segments = []
    saved_images = []
    output_images = []
    with Live(Group(*segments), console=console) as live:
        spinner = Spinner(spinner_name, text="Working...")
        live.update(spinner)
        live.refresh()
        token_usage = 0
        iteration = 0
        model_name = ""
        for respond in sdk.prompt(prompt):
            if not respond:
                break
            token_usage = respond.token_usage
            iteration = respond.iteration
            model_name = respond.model_name
            handle_action_start(
                segments, respond, live, saved_images, output_images, spinner
            )
            handle_action_output(
                segments, respond, live, saved_images, output_images, spinner
            )
            handle_final_answer(
                segments, respond, live, saved_images, output_images, spinner
            )
        live.update(
            Panel(
                Group(*segments),
                title=OCTOPUS_TITLE,
                title_align="left",
                subtitle="[bold]token:%s iteration:%s model:%s"
                % (token_usage, iteration, model_name),
                subtitle_align="right",
            )
        )
        live.refresh()
    # display the images
    render_image(output_images, sdk, filedir)


@click.command()
@click.option("--octopus_dir", default="~/.octopus", help="the root path of octopus")
def app(octopus_dir):
    console = Console()
    if octopus_dir.find("~") == 0:
        real_octopus_dir = octopus_dir.replace("~", os.path.expanduser("~"))
    else:
        real_octopus_dir = octopus_dir
    if not os.path.exists(real_octopus_dir):
        os.mkdir(real_octopus_dir)
    octopus_config = dotenv_values(real_octopus_dir + "/config")
    if not check_parameter(octopus_config, console):
        return
    filedir = real_octopus_dir + "/data"
    if not os.path.exists(filedir):
        os.mkdir(filedir)
    sdk = AgentSyncSDK(octopus_config["endpoint"], octopus_config["api_key"])
    sdk.connect()
    history = FileHistory(real_octopus_dir + "/history")
    completer = FilePathCompleter()
    session = PromptSession(
        history=history,
        # auto_suggest=AutoSuggestFromHistory(),
        # enable_history_search=True,
        completer=completer,
        complete_in_thread=True,
        complete_while_typing=True,
        complete_style=CompleteStyle.MULTI_COLUMN,
    )
    index = 0
    while True:
        real_prompt = session.prompt(
            "[%s]%s>" % (index, octopus_config["chat_emoji"]), multiline=True
        )
        # try to upload first⌛⏳❌
        filepaths = parse_file_path(real_prompt)
        if filepaths:
            real_prompt = real_prompt.replace("/up", "")
            spinner = Spinner(octopus_config.get("spinner", "hearts"), text="Upload...")
            segments = [spinner]
            mk = """The following files will be uploaded
"""
            with Live(Group(*segments), console=console) as live:
                live.update(spinner)
                for file in filepaths:
                    filename = file.split("/")[-1]
                    sdk.upload_file(file, filename)
                    mk += "* ✅%s\n" % file
                    live.update(Group(*[Markdown(mk), spinner]))
                    real_prompt = real_prompt.replace(file, "uploaded %s" % filename)
                # clear the spinner
                live.update(Group(*[Markdown(mk)]))
            # add the prompt to history
            # TODO remove the last prompt
            history.append_string(real_prompt)
        run_chat(
            real_prompt,
            sdk,
            session,
            console,
            spinner_name=octopus_config.get("spinner", "hearts"),
            filedir=filedir,
        )
        index = index + 1
