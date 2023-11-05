#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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
import random
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.style import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle, clear
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession
from og_sdk.agent_sdk import AgentSyncSDK
from og_sdk.utils import process_char_stream
from og_proto import agent_server_pb2
from dotenv import dotenv_values
from prompt_toolkit.completion import Completer, Completion
from .utils import parse_file_path
from .markdown import CodeBlock as SyntaxBlock
from .ui_block import TaskBlocks, TerminalBlock
import clipboard

Markdown.elements["fence"] = SyntaxBlock
Markdown.elements["code_block"] = SyntaxBlock

USER_TITLE = "✍[bold yellow]User"
OCTOGEN_TITLE = "🤖[bold green]Octogen"
SYSTEM_TITLE = "🔨[bold red]System"


def show_welcome(console):
    welcome = """
Welcome to use octogen❤️ . To ask a programming question, simply type your question and press [bold yellow]esc + enter[/]
Use [bold yellow]/help[/] for help
"""
    console.print(welcome)


def prompt_continuation(width, line_number, is_soft_wrap):
    return "." * width


def show_help(console):
    help = """
### Keyboard Shortcut:
- **`ESC + ENTER`**: Submit your question to Octogen or execute your command.

### Commands:

- **`/clear`**: Clears the screen.
- **`/cc{number}`**: Copies the output of Octogen to your clipboard.
- **`/exit`**: Exits the Octogen CLI.
- **`/up`**: Uploads files from your local machine; useful for including in your questions.

### Need Help?

1. Create an issue on our GitHub page: [Octogen GitHub Issues](https://github.com/dbpunk-labs/octogen/issues)
2. Alternatively, you can email us at [codego.me@gmail.com](mailto:codego.me@gmail.com).
"""
    mk = Markdown(help, justify="left")
    console.print(mk)


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


class OctogenCompleter(Completer):

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


def check_parameter(octopus_config, console):
    """
    check the parameter
    """
    if "api_key" not in octopus_config or not octopus_config["api_key"]:
        content = """No api key was found, you can get api key from the following ways
* You can use your [self-hosted](https://github.com/dbpunk-labs) agent server api key
* You can apply the api key from [octogen waitlist](https://octogen.dev) directly"""
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


def refresh(live, task_blocks, title=OCTOGEN_TITLE, task_state=None):
    speed = (
        task_state.output_token_count
        / ((task_state.llm_response_duration + 1) / 1000.0)
        if task_state
        else 0
    )
    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("Index", no_wrap=True, justify="center")
    table.add_column("Status", no_wrap=True, justify="center")
    table.add_column("Content")
    count = 0
    for index, status, block in task_blocks.render():
        table.add_row(f"{index}", status, block)
        count += 1
    if count:
        live.update(
            Panel(
                table,
                title=title,
                title_align="left",
                subtitle="[gray] Speed:%.1ft/s Input:%d Output:%d Model:%s"
                % (
                    speed,
                    task_state.input_token_count,
                    task_state.output_token_count,
                    task_state.llm_name,
                )
                if task_state
                else "",
                subtitle_align="left",
            )
        )
        live.refresh()
    else:
        live.update(Group(*[]))
        live.refresh()


def handle_action_output(task_blocks, respond):
    if respond.response_type not in [
        agent_server_pb2.TaskResponse.OnStepActionStreamStdout,
        agent_server_pb2.TaskResponse.OnStepActionStreamStderr,
    ]:
        return
    if respond.response_type == agent_server_pb2.TaskResponse.OnStepActionStreamStdout:
        task_blocks.add_terminal(respond.console_stdout, "")
    elif (
        respond.response_type == agent_server_pb2.TaskResponse.OnStepActionStreamStderr
    ):
        task_blocks.add_terminal("", respond.console_stderr)


def handle_action_end(task_blocks, respond, images):
    """
    Handles the end of an agent action.

    Args:
      segments: A list of segments in the current turn.
      respond: The response from the agent.
      images: A list of images to be displayed.

    Returns:
      None.
    """
    if respond.response_type != agent_server_pb2.TaskResponse.OnStepActionEnd:
        return
    has_error = respond.on_step_action_end.has_error
    if not has_error:
        images.extend(respond.on_step_action_end.output_files)
    if isinstance(task_blocks.get_last_block(), TerminalBlock):
        task_blocks.get_last_block().finish(has_error)
    task_blocks.finish_current_all_blocks()
    # wait for the next steps
    task_blocks.add_loading()


def handle_typing(task_blocks, respond):
    if respond.response_type not in [
        agent_server_pb2.TaskResponse.OnModelTypeText,
        agent_server_pb2.TaskResponse.OnModelTypeCode,
    ]:
        return
    if respond.response_type == agent_server_pb2.TaskResponse.OnModelTypeText:
        task_blocks.add_markdown(respond.typing_content.content)
    else:
        task_blocks.add_code(
            respond.typing_content.content, respond.typing_content.language
        )


def handle_action_start(task_blocks, respond, images):
    """start to execute the action"""
    if respond.response_type != agent_server_pb2.TaskResponse.OnStepActionStart:
        return
    action = respond.on_step_action_start
    if not action.input:
        return
    arguments = json.loads(action.input)
    images.extend(arguments.get("saved_filenames", []))
    task_blocks.finish_current_all_blocks()
    # wait for the action to be finished
    task_blocks.add_loading()


def extract_the_code(content, task_blocks):
    start_index = 0
    while start_index < len(content):
        first_pos = content.find("```", start_index)
        if first_pos >= 0:
            second_pos = content.find("```", first_pos + 1)
            if second_pos >= 0:
                sub_content = content[start_index:first_pos]
                task_blocks.add_markdown(sub_content)
                task_blocks.get_last_block().finish()
                start_index = first_pos
                code_content = content[first_pos : second_pos + 3]
                clean_code_content = clean_code(code_content)
                task_blocks.add_code(clean_code_content, "python")
                task_blocks.get_last_block().finish()
                # TODO parse language
                start_index = second_pos + 3
        else:
            break
    if start_index < len(content):
        sub_content = content[start_index:]
        task_blocks.add_markdown(sub_content)
        task_blocks.get_last_block().finish()


def handle_final_answer(task_blocks, respond):
    if respond.response_type != agent_server_pb2.TaskResponse.OnFinalAnswer:
        return
    answer = respond.final_answer.answer
    task_blocks.finish_current_all_blocks()
    if not answer:
        return
    extract_the_code(answer, task_blocks)


def render_image(images, sdk, image_dir, console):
    try:
        from PIL import Image
        from term_image.image import AutoImage

        image_set = set(images)
        for image in image_set:
            if image.endswith("jpg") or image.endswith("png") or image.endswith("gif"):
                try:
                    sdk.download_file(image, image_dir)
                    fullpath = "%s/%s" % (image_dir, image)
                    pil_image = Image.open(fullpath)
                    auto_image = AutoImage(
                        image=pil_image, width=int(pil_image.size[0] / 15)
                    )
                    print(f"{auto_image:1.1#}")
                    return True
                except Exception as ex:
                    return False
    except Exception as ex:
        return False


def upload_file(prompt, console, history_prompt, sdk, values):
    filepaths = parse_file_path(prompt)
    if not filepaths:
        return prompt
    task_blocks = TaskBlocks(values)
    task_blocks.begin()
    real_prompt = prompt.replace("/up", "")
    with Live(Group(*[]), console=console) as live:
        mk = """The following files will be uploaded
"""
        task_blocks.add_markdown(mk)
        refresh(live, task_blocks, title=SYSTEM_TITLE)
        for file in filepaths:
            filename = file.split("/")[-1]
            sdk.upload_file(file, filename)
            mk = "* ✅%s\n" % file
            task_blocks.add_markdown(mk)
            real_prompt = real_prompt.replace(file, "uploaded %s" % filename)
            refresh(live, task_blocks, title=SYSTEM_TITLE)
        task_blocks.get_last_block().finish()
        refresh(live, task_blocks, title=SYSTEM_TITLE)
    history_prompt.append_string(real_prompt)
    return real_prompt


def run_chat(prompt, session, console, values, filedir=None):
    """
    run the chat
    """
    task_blocks = TaskBlocks(values)
    task_blocks.begin()
    images = []
    error_responses = []
    with Live(Group(*[]), console=console) as live:
        refresh(live, task_blocks)
        task_state = None
        for respond in session.prompt(prompt):
            if not respond:
                break
            if respond.response_type in [
                agent_server_pb2.TaskResponse.OnSystemError,
                agent_server_pb2.TaskResponse.OnInputTokenLimitExceed,
                agent_server_pb2.TaskResponse.OnOutputTokenLimitExceed,
            ]:
                error_responses.append(respond)
                task_blocks.finish_current_all_blocks()
                break
            handle_typing(task_blocks, respond)
            handle_action_start(task_blocks, respond, images)
            handle_action_output(task_blocks, respond)
            handle_action_end(task_blocks, respond, images)
            handle_final_answer(task_blocks, respond)
            task_state = respond.state
            refresh(live, task_blocks, task_state=respond.state)
        refresh(live, task_blocks, task_state=task_state)
    if error_responses:
        task_blocks = TaskBlocks(values)
        task_blocks.begin()
        with Live(Group(*[]), console=console) as live:
            for respond in error_responses:
                task_blocks.add_markdown(respond.error_msg)
                task_blocks.get_last_block().finish()
            refresh(live, task_blocks, title=SYSTEM_TITLE)
    # display the images
    # render_image(images, sdk, filedir, console)


@click.command()
@click.option("--octogen_dir", default="~/.octogen", help="the root path of octogen")
def app(octogen_dir):
    console = Console()
    if octogen_dir.find("~") == 0:
        real_octogen_dir = octogen_dir.replace("~", os.path.expanduser("~"))
    else:
        real_octogen_dir = octogen_dir
    os.makedirs(real_octogen_dir, exist_ok=True)
    octopus_config = dotenv_values(real_octogen_dir + "/config")
    if not check_parameter(octopus_config, console):
        return
    filedir = real_octogen_dir + "/data"
    os.makedirs(filedir, exist_ok=True)
    sdk = AgentSyncSDK(octopus_config["endpoint"], octopus_config["api_key"])
    sdk.connect()
    with sdk.create_session() as agent_session:
        history = FileHistory(real_octogen_dir + "/history")
        values = []
        completer = OctogenCompleter(values)
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
            index = index + 1
            real_prompt = session.prompt(
                "[%s]%s>" % (index, "🎧"),
                multiline=True,
                prompt_continuation=prompt_continuation,
            )
            if not "".join(real_prompt.strip().split("\n")):
                continue
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
            real_prompt = upload_file(real_prompt, console, history, sdk, values)
            run_chat(
                real_prompt,
                agent_session,
                console,
                values,
                filedir=filedir,
            )
