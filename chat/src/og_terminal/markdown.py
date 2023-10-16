# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

from rich.markdown import TextElement, Markdown
from rich.syntax import Syntax
from rich.console import Console, ConsoleOptions, RenderResult
from markdown_it.token import Token


class CodeBlock(TextElement):
    """A code block with syntax highlighting."""

    style_name = "markdown.code_block"

    @classmethod
    def create(cls, markdown: "Markdown", token: Token) -> "CodeBlock":
        node_info = token.info or ""
        lexer_name = node_info.partition(" ")[0]
        return cls(lexer_name or "default", markdown.code_theme)

    def __init__(self, lexer_name: str, theme: str) -> None:
        self.lexer_name = lexer_name
        self.theme = theme

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        code = str(self.text).rstrip()
        syntax = Syntax(
            code,
            self.lexer_name,
            # background_color="default",
            line_numbers=True,
            theme=self.theme,
            word_wrap=True,
            padding=1,
        )
        yield syntax
