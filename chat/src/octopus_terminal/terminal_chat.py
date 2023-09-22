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
import random
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
from rich.emoji import EMOJI
from rich import box
from rich.style import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import CompleteStyle, clear
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession
from octopus_agent.agent_sdk import AgentSyncSDK
from octopus_agent.utils import process_char_stream
from octopus_proto import agent_server_pb2
from dotenv import dotenv_values
from prompt_toolkit.completion import Completer, Completion
from .utils import parse_file_path
from .markdown import CodeBlock
import clipboard
from PIL import Image
from term_image.image import AutoImage

Markdown.elements["fence"] = CodeBlock
Markdown.elements["code_block"] = CodeBlock
OCTOPUS_TITLE = "🐙[bold red]Octopus"
OCTOPUS_APP_TITLE = "🐙[bold red]App"

EMOJI_KEYS = list(EMOJI.keys())


def show_welcome(console):
    welcome = """
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press [bold yellow]esc + enter[/]
Use [bold yellow]/help[/] for help
"""
    console.print(welcome)


def show_help(console):
    help = """
### Keyboard Shortcut:
- **`ESC + ENTER`**: Submit your question to Octopus or execute your command.

### Commands:

- **`/clear`**: Clears the screen.
- **`/cc{number}`**: Copies the output of Octopus to your clipboard.
- **`/exit`**: Exits the Octopus CLI.
- **`/up`**: Uploads files from your local machine; useful for including in your questions.
- **`/assemble {name} {number1} {number2}`**: Assembles the specified code segments into an application.
- **`/run {name}`**: Executes an application with the specified name.
- **`/apps`**: Displays a list of all your apps.

### Need Help?

1. Create an issue on our GitHub page: [Octopus GitHub Issues](https://github.com/dbpunk-labs/octopus/issues)
2. Alternatively, you can email us at [codego.me@gmail.com](mailto:codego.me@gmail.com).
"""
    mk = Markdown(help, justify="left")
    console.print(mk)


def gen_a_random_emoji():
    index = random.randint(0, len(EMOJI_KEYS))
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


def refresh(
    live,
    segments,
    token_usage="0",
    iteration="0",
    model_name="",
    title=OCTOPUS_TITLE,
):
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
            subtitle=f"[bold yellow]token:{token_usage} interation:{iteration} model:{model_name}"
            if model_name
            else "",
            subtitle_align="right",
        )
    )
    live.refresh()


def handle_action_output(segments, respond, values):
    if respond.respond_type not in [
        agent_server_pb2.TaskRespond.OnAgentActionStdout,
        agent_server_pb2.TaskRespond.OnAgentActionStderr,
    ]:
        return

    value = values.pop()
    new_stdout = value[1][0]
    new_stderr = value[1][1]
    segment = segments.pop()
    if respond.respond_type == agent_server_pb2.TaskRespond.OnAgentActionStdout:
        new_stdout += respond.console_stdout
        new_stdout = process_char_stream(new_stdout)
    elif respond.respond_type == agent_server_pb2.TaskRespond.OnAgentActionStderr:
        new_stderr += respond.console_stderr
        new_stderr = process_char_stream(new_stderr)
    values.append(("text", (new_stdout, new_stderr), []))
    syntax = Syntax(
        f"{new_stdout}\n{new_stderr}",
        "text",
        line_numbers=True,  # background_color="default"
    )
    segments.append((len(values) - 1, segment[1], syntax))


def handle_action_end(segments, respond, images, values):
    if respond.respond_type != agent_server_pb2.TaskRespond.OnAgentActionEndType:
        return
    output = respond.on_agent_action_end.output
    has_error = "✅"
    segment = segments.pop()
    mk = segment[2].code
    # simple to handle error
    if mk.find("Traceback") >= 0:
        has_error = "❌"
    syntax = Syntax(
        mk,
        "text",
        line_numbers=True,  # background_color="default"
    )
    if not images:
        images.extend(respond.on_agent_action_end.output_files)
    segments.append((len(values) - 1, has_error, syntax))
    # add the next steps loading
    spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
    values.append(("text", "", []))
    segments.append((len(values) - 1, spinner, ""))


def handle_typing(segments, respond, values):
    if respond.respond_type not in [
        agent_server_pb2.TaskRespond.OnAgentTextTyping,
        agent_server_pb2.TaskRespond.OnAgentCodeTyping,
    ]:
        return
    value = values.pop()
    segment = segments.pop()
    if respond.respond_type == agent_server_pb2.TaskRespond.OnAgentTextTyping:
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
    if respond.respond_type != agent_server_pb2.TaskRespond.OnAgentActionType:
        return
    action = respond.on_agent_action
    if not action.input:
        return
    arguments = json.loads(action.input)
    if action.tool == "execute_python_code" and action.input:
        images.extend(arguments.get("saved_filenames", []))
        value = values.pop()
        segment = segments.pop()
        if value[0] == "text":
            values.append(value)
            markdown = Markdown("\n" + value[1])
            new_segment = (segment[0], segment[1], markdown)
            segments.append(new_segment)
        elif value[0] == "python":
            values.append(value)
            syntax = Syntax(
                value[1],
                "python",
                line_numbers=True,  # background_color="default"
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
                values.append(("python", clean_code_content))
                segments.append((len(values) - 1, "📖", Markdown(code_content)))
                start_index = second_pos + 3
        else:
            break
    if start_index < len(content):
        sub_content = content[start_index:]
        values.append(("text", sub_content, []))
        segments.append((len(values) - 1, "🧠", Markdown(sub_content)))


def handle_final_answer(segments, respond, values):
    if respond.respond_type != agent_server_pb2.TaskRespond.OnFinalAnswerType:
        return
    answer = respond.final_respond.answer
    values.pop()
    segments.pop()
    find_code(answer, segments, values)


def render_image(images, sdk, image_dir, console):
    image_set = set(images)
    for image in image_set:
        try:
            sdk.download_file(image, image_dir)
            fullpath = "%s/%s" % (image_dir, image)
            pil_image = Image.open(fullpath)
            auto_image = AutoImage(image=pil_image, width=int(pil_image.size[0] / 15))
            print(f"{auto_image:1.1#}")
        except Exception as ex:
            pass


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
        refresh(live, segments, spinner)
        for respond in sdk.prompt(prompt):
            if not respond:
                break
            token_usage = respond.token_usage
            iteration = respond.iteration
            model_name = respond.model_name
            handle_typing(segments, respond, values)
            handle_action_start(segments, respond, images, values)
            handle_action_output(segments, respond, values)
            handle_action_end(segments, respond, images, values)
            handle_final_answer(segments, respond, values)
            refresh(
                live,
                segments,
                token_usage=token_usage,
                iteration=iteration,
                model_name=model_name,
            )
        refresh(
            live,
            segments,
            token_usage=token_usage,
            iteration=iteration,
            model_name=model_name,
        )
    # display the images
    render_image(images, sdk, filedir, console)


def run_app(name, sdk, session, console, values, filedir=None):
    segments = []
    images = []
    with Live(Group(*segments), console=console) as live:
        spinner = Spinner("dots", style="status.spinner", speed=1.0, text="")
        values.append(("text", "", []))
        segments.append((len(values) - 1, spinner, ""))
        refresh(live, segments, title=OCTOPUS_APP_TITLE + f":{name}")
        for respond in sdk.run(name):
            if not respond:
                break
            handle_action_start(segments, respond, images, values)
            handle_action_output(segments, respond, values)
            handle_action_end(segments, respond, images, values)
            refresh(live, segments, title=OCTOPUS_APP_TITLE + f":{name}")
        values.pop()
        segments.pop()
        refresh(live, segments, title=OCTOPUS_APP_TITLE + f":{name}")
    # display the images
    render_image(images, sdk, filedir, console)


def gen_app_panel(app):
    desc = app.desc if app.desc else ""
    date_str = datetime.fromtimestamp(app.ctime).strftime("%m/%d/%Y")
    markdonw = f"""### {app.desc}{app.name}
created at {date_str} with {app.language}"""
    style = Style(bgcolor="#2e2e2e")
    return Panel(Markdown(markdonw), box=box.SIMPLE, title_align="left", style=style)


def query_apps(sdk, console):
    table = Table.grid(padding=1, pad_edge=True)
    table.add_column("col1", no_wrap=True, justify="center")
    table.add_column("col2", no_wrap=True, justify="center")
    table.add_column("col3", no_wrap=True, justify="center")
    table.add_column("col3", no_wrap=True, justify="center")

    apps = sdk.query_apps()
    for index in range(0, len(apps.apps), 4):
        table.add_row(
            gen_app_panel(apps.apps[index]) if index < len(apps.apps) else "",
            gen_app_panel(apps.apps[index + 1]) if index + 1 < len(apps.apps) else "",
            gen_app_panel(apps.apps[index + 2]) if index + 2 < len(apps.apps) else "",
            gen_app_panel(apps.apps[index + 3]) if index + 3 < len(apps.apps) else "",
        )
    console.print(Panel(table, title=OCTOPUS_APP_TITLE, title_align="left"))


def assemble_app(sdk, name, numbers, values):
    code = []
    language = "python"
    saved_filenames = []
    for number in numbers:
        if values[number][0] == "text":
            continue
        if values[number][0] == "python":
            code.append(values[number][1])
            saved_filenames.extend(values[number][2])
            language = values[number][0]
    try:
        response = sdk.assemble(
            name,
            "\n".join(code),
            language,
            desc=gen_a_random_emoji(),
            saved_filenames=list(set(saved_filenames)),
        )
        if response.code == 0:
            return True, response.msg
        return False, response.msg
    except Exception as ex:
        return False, str(ex)


@click.command()
@click.option("--octopus_dir", default="~/.octopus", help="the root path of octopus")
def app(octopus_dir):
    console = Console()
    if octopus_dir.find("~") == 0:
        real_octopus_dir = octopus_dir.replace("~", os.path.expanduser("~"))
    else:
        real_octopus_dir = octopus_dir
    os.makedirs(real_octopus_dir, exist_ok=True)
    octopus_config = dotenv_values(real_octopus_dir + "/config")
    if not check_parameter(octopus_config, console):
        return
    filedir = real_octopus_dir + "/data"
    os.makedirs(filedir, exist_ok=True)
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
        if real_prompt.find("/assemble") >= 0:
            parts = real_prompt.split(" ")
            if len(parts) < 3:
                console.print(f"❌ please add at least on code segment number")
                continue
            try:
                name = parts[1]
                numbers = [int(number) for number in parts[2:]]
                (status, msg) = assemble_app(sdk, name, numbers, values)
                if status:
                    console.print(
                        f"👍 the app {name} has been assembled! use /run {name} to run this app."
                    )
                    continue
                else:
                    console.print(f"❌ fail to assemble the app {name} for error {msg}")
                    continue
            except Exception as ex:
                console.print(f"❌ invalid numbers {ex}")
                continue
        if real_prompt.find("/run") >= 0:
            parts = real_prompt.split(" ")
            if len(parts) < 2:
                console.print(f"❌ please specify the name of app")
                continue

            try:
                name = parts[1]
                run_app(name, sdk, session, console, values, filedir=filedir)
                continue
            except Exception as ex:
                console.print(f"❌ exception {ex}")
                continue
        if real_prompt.find("/apps") >= 0:
            query_apps(sdk, console)
            continue

        # try to upload first⌛⏳❌
        filepaths = parse_file_path(real_prompt)
        if filepaths:
            real_prompt = real_prompt.replace("/up", "")
            spinner = Spinner(octopus_config.get("spinner", "dots2"), text="Upload...")
            segments = [spinner]
            mk = """The following files will be uploaded
"""
            with Live(Group(*segments), console=console, screen=True) as live:
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
