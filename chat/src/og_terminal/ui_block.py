# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

from rich.markdown import Markdown
from og_sdk.utils import process_char_stream
from rich.spinner import Spinner
from rich.syntax import Syntax


class BaseBlock:

    def __init__(self, index):
        self.index = index
        self.finished = False
        self.has_error = False
        self.emoji = ""

    def is_finished(self):
        return self.finished

    def get_index(self):
        return self.index

    def finish(self, has_error=False):
        self.finished = True
        self.has_error = has_error

    def get_status(self):
        if self.has_error:
            return "❌"
        if self.finished:
            return self.emoji
        else:
            return Spinner("dots", style="status.spinner", speed=1.0, text="")

    def set_emoji(self, emoji):
        self.emoji = emoji


class StreamingBlock(BaseBlock):

    def __init__(self, index, content):
        super().__init__(index)
        self.content = content

    def append(self, new_content):
        if self.finished:
            return
        tmp_content = self.content + new_content
        self.content = process_char_stream(tmp_content)


class MarkdownBlock(StreamingBlock):

    def __init__(self, index, content):
        super().__init__(index, content)
        self.set_emoji("🧠")

    def render(self):
        if self.finished:
            return Markdown(self.content)
        else:
            return Markdown(self.content + "█")


class TerminalBlock(StreamingBlock):

    def __init__(self, index):
        super().__init__(index, "")
        self.set_emoji("✅")
        self.terminal_stdout = ""
        self.terminal_stderr = ""

    def render(self):
        output = self.terminal_stdout
        if self.terminal_stderr:
            output += "\n" + self.terminal_stderr
        if self.finished:
            return Syntax(output, "text", line_numbers=True)
        else:
            return Syntax(output + "█", "text", line_numbers=True)

    def write(self, terminal_stdout, terminal_stderr):
        if self.finished:
            return
        if terminal_stdout:
            tmp_content = self.terminal_stdout + terminal_stdout
            self.terminal_stdout = process_char_stream(tmp_content)
        if terminal_stderr:
            tmp_content = self.terminal_stderr + terminal_stderr
            self.terminal_stderr = process_char_stream(tmp_content)
        output = self.terminal_stdout
        if self.terminal_stderr:
            output += "\n" + self.terminal_stderr
        self.content = output


class CodeBlock(StreamingBlock):

    def __init__(self, index, content, language):
        super().__init__(index, content)
        self.language = language
        self.set_emoji("📖")

    def render(self):
        if self.finished:
            return Syntax(self.content, self.language, line_numbers=True)
        else:
            return Syntax(self.content + "█", self.language, line_numbers=True)


class LoadingBlock(BaseBlock):

    def __init__(self, index):
        super().__init__(index)

    def render(self):
        return ""


class UploadFilesBlock(BaseBlock):

    def __init__(self, index, filenames):
        super().__init__(index)
        self.filenames = filenames
        self.file_states = {}

    def update_progress(self, filename, uploaded, total):
        self.file_states[filename] = (uploaded, total)


class TaskBlocks:

    def __init__(self, values):
        self.blocks = []
        self.values = values

    def begin(self):
        self.blocks.append(LoadingBlock(0))

    def add_terminal(self, terminal_stdout, terminal_stderr):
        last_block = self.blocks[-1]
        if isinstance(last_block, LoadingBlock):
            self.blocks.pop()
            block = TerminalBlock(len(self.values))
            block.write(terminal_stdout, terminal_stderr)
            self.blocks.append(block)
            self.values.append(block.content)
        elif isinstance(last_block, TerminalBlock):
            if last_block.is_finished():
                block = TerminalBlock(len(self.values))
                block.write(terminal_stdout, terminal_stderr)
                self.blocks.append(block)
                self.values.append(block.content)
            else:
                last_block.write(terminal_stdout, terminal_stderr)
                self.values[last_block.get_index()] = last_block.content
        else:
            last_block.finish()
            block = TerminalBlock(len(self.values))
            block.write(terminal_stdout, terminal_stderr)
            self.blocks.append(block)
            self.values.append(block.content)

    def add_markdown(self, content):
        last_block = self.blocks[-1]
        if isinstance(last_block, LoadingBlock):
            self.blocks.pop()
            self.blocks.append(MarkdownBlock(len(self.values), content))
            self.values.append(content)

        elif isinstance(last_block, MarkdownBlock):
            if last_block.is_finished():
                self.blocks.append(MarkdownBlock(len(self.values), content))
                self.values.append(content)
            else:
                last_block.append(content)
                self.values[last_block.get_index()] = last_block.content
        else:
            last_block.finish()
            self.blocks.append(MarkdownBlock(len(self.values), content))
            self.values.append(content)

    def add_loading(self):
        last_block = self.blocks[-1]
        if isinstance(last_block, LoadingBlock) and not last_block.is_finished():
            return
        self.blocks.append(LoadingBlock(0))

    def finish_current_all_blocks(self):
        for block in self.blocks:
            if block.is_finished():
                continue
            block.finish()

    def get_last_block(self):
        return self.blocks[-1]

    def add_code(self, code, language):
        last_block = self.blocks[-1]
        if isinstance(last_block, LoadingBlock):
            self.blocks.pop()
            self.blocks.append(CodeBlock(len(self.values), code, language))
            self.values.append(code)
        elif isinstance(last_block, CodeBlock):
            if last_block.is_finished():
                self.blocks.append(CodeBlock(len(self.values), code, language))
                self.values.append(code)
            else:
                last_block.append(code)
                last_block.language = language
                self.values[last_block.get_index()] = last_block.content
        else:
            last_block.finish()
            self.blocks.append(CodeBlock(len(self.values), code, language))
            self.values.append(code)

    def render(self):
        for block in self.blocks:
            if isinstance(block, LoadingBlock) and block.is_finished():
                continue
            yield (block.get_index(), block.get_status(), block.render())
