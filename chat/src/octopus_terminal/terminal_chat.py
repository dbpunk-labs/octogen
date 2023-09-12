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
from rich.table import Table
from rich.progress import Progress
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle, clear
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession
from octopus_agent.agent_sdk import AgentSyncSDK
from dotenv import dotenv_values
from prompt_toolkit.completion import Completer, Completion
from .utils import parse_file_path
import clipboard

OCTOPUS_TITLE = "🐙[bold red]Octopus"


def show_welcome(console):
    welcome = """
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press [bold yellow]esc + enter[/]
You can use [bold yellow]/help[/] to look for help
"""
    console.print(welcome)


def show_help(console):
    help = """
Shortcut:
    [bold yellow]esc+enter[/]   submit your question to octopus

Commands:
    [bold yellow]/clear[/]      clear the screen
    [bold yellow]/cc{number}[/] copy the output of octopus to clipboard
    [bold yellow]/exit[/]       exit the octopus cli
    [bold yellow]/up[/]         upload the files from local, you can use it in your question

Ask for help:
    1. You can create an issue from https://github.com/dbpunk-labs/octopus/issues
    2. You can send mail to codego.me@gmail.com
"""
    console.print(help)


def parse_numbers(text):
    """Parses numbers from a string.

    Args:
    text: The string to parse.

    Returns:
    A list of numbers found in the string.
    """
    pattern = r"\d+\.\d+|\d+"
    numbers = re.findall(pattern, text)
    return numbers


class OctopusCompleter(Completer):

    def __init__(self, values):
        Completer.__init__(self)
        self.values = values

    def get_completions(self, document, complete_event):
        index = document.current_line_before_cursor.find("/up ")
        if index >= 0:
            word_before_cursor = document.current_line_before_cursor[
                index + 3 :
            ].strip()
            if word_before_cursor:
                for comp in glob.glob(word_before_cursor + "*"):
                    yield Completion(comp, -len(word_before_cursor))
        # elif document.current_line_before_cursor.find("/cc") >= 0:
        #    index = document.current_line_before_cursor.find("/cc")
        #    word_before_cursor = document.current_line_before_cursor[index + 3:]
        #    numbers = list(parse_numbers(word_before_cursor))


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
    return code


def refresh(live, segments, spinner, token_usage="0", iteration="0", model_name=""):
    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("Index", no_wrap=True, justify="center", style="bold red")
    table.add_column("Content")
    for index, segment in segments:
        table.add_row(f"/cc{index}", segment)
    if spinner:
        live.update(
            Group(
                Panel(
                    table,
                    title=OCTOPUS_TITLE,
                    title_align="left",
                    subtitle=f"[bold yellow]token:{token_usage} interation:{iteration} model:{model_name}",
                    subtitle_align="right",
                ),
                spinner,
            )
        )
    else:
        live.update(
            Panel(
                table,
                title=OCTOPUS_TITLE,
                title_align="left",
                subtitle=f"[bold yellow]token:{token_usage} interation:{iteration} model:{model_name}",
                subtitle_align="right",
            )
        )
    live.refresh()


def handle_action_output(segments, respond, live, images, spinner, values):
    if not respond.on_agent_action_end:
        return
    output = respond.on_agent_action_end.output
    if not output:
        return
    mk = output
    markdown = Markdown(mk)
    images.extend(respond.on_agent_action_end.output_files)
    values.append(mk)
    segments.append((len(values) - 1, markdown))
    refresh(live, segments, spinner)


def handle_action_start(segments, respond, live, images, spinner, values):
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
        syntax = Syntax(arguments["code"], "python")
        values.append(explanation)
        segments.append((len(values) - 1, markdown))
        values.append(arguments["code"])
        segments.append((len(values) - 1, syntax))
        images.extend(arguments.get("saved_filenames", []))
        refresh(live, segments, spinner)


def find_code(content, segments, values):
    start_index = 0
    while start_index < len(content):
        first_pos = content.find("```", start_index)
        if first_pos >= 0:
            second_pos = content.find("```", first_pos + 1)
            if second_pos >= 0:
                sub_content = content[start_index:first_pos]
                values.append(sub_content)
                segments.append((len(values) - 1, Markdown(sub_content)))
                start_index = first_pos
                code_content = content[first_pos : second_pos + 3]
                clean_code_content = clean_code(code_content)
                values.append(clean_code_content)
                segments.append((len(values) - 1, Markdown(code_content)))
                start_index = second_pos + 3
        else:
            break
    if start_index < len(content):
        sub_content = content[start_index:]
        values.append(sub_content)
        segments.append((len(values) - 1, Markdown(sub_content)))


def handle_final_answer(segments, respond, live, spinner, values):
    if not respond.final_respond:
        return
    answer = respond.final_respond.answer
    if not answer:
        return
    find_code(answer, segments, values)
    refresh(
        live,
        segments,
        spinner,
        token_usage=respond.token_usage,
        iteration=respond.iteration,
        model_name=respond.model_name,
    )


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


def run_chat(
    prompt, sdk, session, console, values, spinner_name="hearts", filedir=None
):
    """
    run the chat
    """
    segments = []
    images = []
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
            handle_action_start(segments, respond, live, images, spinner, values)
            handle_action_output(segments, respond, live, images, spinner, values)
            handle_final_answer(segments, respond, live, spinner, values)
        refresh(
            live,
            segments,
            None,
            token_usage=token_usage,
            iteration=iteration,
            model_name=model_name,
        )
    # display the images
    render_image(images, sdk, filedir)


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
    values = []
    completer = OctopusCompleter(values)
    session = PromptSession(
        history=history,
        completer=completer,
        complete_in_thread=True,
        complete_while_typing=True,
        complete_style=CompleteStyle.MULTI_COLUMN,
    )
    index = 0
    show_welcome(console)
    while True:
        real_prompt = session.prompt("[%s]%s>" % (index, "🎧"), multiline=True)
        if real_prompt.find("/help") >= 0:
            show_help(console)
            continue
        if real_prompt.find("/exit") >= 0:
            console.print("👋👋!")
            return
        if real_prompt.find("/clear") >= 0:
            clear()
            continue
        if real_prompt.find("/cc") >= 0:
            # handle copy
            for number in parse_numbers(real_prompt):
                num = int(number)
                if num < len(values):
                    clipboard.copy(values[num])
                    console.print(f"👍 /cc{number} has been copied to clipboard!")
                    break
                else:
                    console.print(f"❌ /cc{number} was not found!")
            continue
        # try to upload first⌛⏳❌
        filepaths = parse_file_path(real_prompt)
        if filepaths:
            real_prompt = real_prompt.replace("/up", "")
            spinner = Spinner(octopus_config.get("spinner", "dots2"), text="Upload...")
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
            values,
            spinner_name=octopus_config.get("spinner", "dots2"),
            filedir=filedir,
        )
        index = index + 1
