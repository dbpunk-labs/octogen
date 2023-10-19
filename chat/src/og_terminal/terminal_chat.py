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
from rich.emoji import EMOJI
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
from .markdown import CodeBlock
import clipboard

Markdown.elements["fence"] = CodeBlock
Markdown.elements["code_block"] = CodeBlock
OCTOGEN_TITLE = "🐙[bold red]Octogen"
OCTOGEN_APP_TITLE = "🐙[bold red]App"

EMOJI_KEYS = list(EMOJI.keys())


def show_welcome(console):
    welcome = """
Welcome to use octogen❤️ . To ask a programming question, simply type your question and press [bold yellow]esc + enter[/]
Use [bold yellow]/help[/] for help
"""
    console.print(welcome)


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


def gen_a_random_emoji():
    index = random.randint(0, len(EMOJI_KEYS) - 1)
    return EMOJI[EMOJI_KEYS[index]]


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


def refresh(live, segments, title=OCTOGEN_TITLE, task_state=None):
    speed = (
        task_state.output_token_count
        / ((task_state.llm_response_duration + 1) / 1000.0)
        if task_state
        else 0
    )
    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("Index", no_wrap=True, justify="center", style="bold red")
    table.add_column("Status", no_wrap=True, justify="center", style="bold red")
    table.add_column("Content")
    for index, status, segment in segments:
        table.add_row(f"{index}", status, segment)
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


def handle_action_output(segments, respond, values):
    if respond.response_type not in [
        agent_server_pb2.TaskResponse.OnStepActionStreamStdout,
        agent_server_pb2.TaskResponse.OnStepActionStreamStderr,
    ]:
        return
    value = values.pop()
    new_stdout = value[1][0]
    new_stderr = value[1][1]
    segment = segments.pop()
    if respond.response_type == agent_server_pb2.TaskResponse.OnStepActionStreamStdout:
        new_stdout += respond.console_stdout
        new_stdout = process_char_stream(new_stdout)
    elif (
        respond.response_type == agent_server_pb2.TaskResponse.OnStepActionStreamStderr
    ):
        new_stderr += respond.console_stderr
        new_stderr = process_char_stream(new_stderr)
    values.append(("text", (new_stdout, new_stderr), []))
    total_output = new_stdout
    if new_stderr:
        total_output = new_stdout + "\n" + new_stderr
    text = Text.from_ansi(total_output)
    syntax = Syntax(
        f"{text.plain}",
        "text",
        line_numbers=True,  # background_color="default"
    )
    segments.append((len(values) - 1, segment[1], syntax))


def handle_action_end(segments, respond, images, values):
    """
    Handles the end of an agent action.

    Args:
      segments: A list of segments in the current turn.
      respond: The response from the agent.
      images: A list of images to be displayed.
      values: A list of values to be copied

    Returns:
      None.
    """
    if respond.response_type != agent_server_pb2.TaskResponse.OnStepActionEnd:
        return
    output = respond.on_agent_action_end.output
    has_error = "✅" if not respond.on_step_action_end.has_error else "❌"
    old_value = values.pop()
    segment = segments.pop()
    if images and not has_error:
        images.extend(respond.on_step_action_end.output_files)
    values.append(old_value)
    segments.append((len(values) - 1, has_error, segment[2]))
    # add the next steps loading
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    values.append(("text", "", []))
    segments.append((len(values) - 1, spinner, ""))


def handle_typing(segments, respond, values):
    if respond.response_type not in [
        agent_server_pb2.TaskResponse.OnModelTypeText,
        agent_server_pb2.TaskResponse.OnModelTypeCode,
    ]:
        return
    value = values.pop()
    segment = segments.pop()
    if respond.response_type == agent_server_pb2.TaskResponse.OnModelTypeText:
        new_value = value[1] + respond.typing_content
        values.append(("text", new_value, []))
        markdown = Markdown("\n" + new_value + "█")
        segments.append((len(values) - 1, segment[1], markdown))
    else:
        # Start write the code
        if value[0] == "text":
            values.append(value)
            markdown = Markdown("\n" + value[1])
            new_segment = (segment[0], "🧠", markdown)
            segments.append(new_segment)
            new_value = respond.typing_content
            values.append(("python", new_value, []))
            syntax = Syntax(
                new_value,
                "python",
                line_numbers=True,  # background_color="default"
            )
            segments.append((len(values) - 1, "📖", syntax))
        else:
            # continue
            new_value = value[1] + respond.typing_content
            values.append(("python", new_value, []))
            syntax = Syntax(
                new_value + "█",
                "python",
                line_numbers=True,  # background_color="default"
            )
            segments.append((len(values) - 1, "📖", syntax))


def handle_action_start(segments, respond, images, values):
    """Run on agent action."""
    if respond.response_type != agent_server_pb2.TaskResponse.OnStepActionStart:
        return
    action = respond.on_step_action_start
    if not action.input:
        return
    arguments = json.loads(action.input)
    value = values.pop()
    segment = segments.pop()
    images.extend(arguments.get("saved_filenames", []))
    if not value[1]:
        new_value = (
            arguments["language"],
            arguments["code"],
            arguments.get("saved_filenames", []),
        )
        values.append(new_value)
        syntax = Syntax(
            arguments["code"],
            arguments["language"],
            line_numbers=True,
        )
        new_segment = (segment[0], "📖", syntax)
        segments.append(new_segment)
    elif value[0] == "text":
        values.append(value)
        markdown = Markdown("\n" + value[1])
        new_segment = (segment[0], segment[1], markdown)
        segments.append(new_segment)
    else:
        values.append(value)
        syntax = Syntax(
            value[1],
            value[0],
            line_numbers=True,
        )
        new_segment = (segment[0], segment[1], syntax)
        segments.append(new_segment)
    # Add spinner for console
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    values.append(("text", ("", ""), []))
    syntax = Syntax(
        "",
        "text",
        line_numbers=True,  # background_color="default"
    )
    segments.append((len(values) - 1, spinner, syntax))


def find_code(content, segments, values):
    start_index = 0
    while start_index < len(content):
        first_pos = content.find("```", start_index)
        if first_pos >= 0:
            second_pos = content.find("```", first_pos + 1)
            if second_pos >= 0:
                sub_content = content[start_index:first_pos]
                values.append(("text", sub_content, []))
                segments.append((len(values) - 1, "🧠", Markdown(sub_content)))
                start_index = first_pos
                code_content = content[first_pos : second_pos + 3]
                clean_code_content = clean_code(code_content)
                # TODO parse language
                values.append(("python", clean_code_content, []))
                segments.append((len(values) - 1, "📖", Markdown(code_content)))
                start_index = second_pos + 3
        else:
            break
    if start_index < len(content):
        sub_content = content[start_index:]
        values.append(("text", sub_content, []))
        segments.append((len(values) - 1, "🧠", Markdown(sub_content)))


def handle_final_answer(segments, respond, values):
    if respond.response_type != agent_server_pb2.TaskResponse.OnFinalAnswer:
        return
    answer = respond.final_answer.answer
    values.pop()
    segments.pop()
    if not answer:
        return
    find_code(answer, segments, values)


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


def run_chat(
    prompt, sdk, session, console, values, spinner_name="hearts", filedir=None
):
    """
    run the chat
    """
    segments = []
    images = []
    token_usage = 0
    iteration = 0
    model_name = ""
    with Live(Group(*segments), console=console) as live:
        spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
        values.append(("text", "", []))
        segments.append((len(values) - 1, spinner, ""))
        refresh(live, segments)
        task_state = None
        for respond in sdk.prompt(prompt):
            if not respond:
                break
            handle_typing(segments, respond, values)
            handle_action_start(segments, respond, images, values)
            handle_action_output(segments, respond, values)
            handle_action_end(segments, respond, images, values)
            handle_final_answer(segments, respond, values)
            task_state = respond.state
            refresh(live, segments, task_state=respond.state)
        refresh(live, segments, task_state=task_state)
    # display the images
    render_image(images, sdk, filedir, console)


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
        real_prompt = session.prompt("[%s]%s>" % (index, "🎧"), multiline=True)
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
                    clipboard.copy(values[num][1])
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
