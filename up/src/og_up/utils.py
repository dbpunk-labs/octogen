#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import subprocess
import os
import sys
import io

USE_SHELL = sys.platform.startswith("win")


def run_with_realtime_print(
    command, universal_newlines=True, useshell=USE_SHELL, env=os.environ
):
    try:
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=useshell,
            env=env,
        )

        text_fd = io.TextIOWrapper(
            p.stdout, encoding="utf-8", newline=os.linesep, errors="replace"
        )
        while True:
            chunk = text_fd.read(40)
            if not chunk:
                break
            yield 0, chunk
        p.wait()
        yield p.returncode, ""
    except Exception as ex:
        yield -1, str(ex)
