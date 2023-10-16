# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import os
import logging
import subprocess
import json
import sys
import pathlib
from time import sleep

logger = logging.getLogger(__name__)

"""
The jupytor kernel manager used for
- create kernel instance
- start kernel instance
- stop kernel instance

Typical usage example:
    config_path = "kernel_connection_file.json"
    workspace = "/mnt/workspace1"
    km = KernelManager(config_path, workspace)
    # start the kernel
    km.start()
"""


class KernelManager:

    def __init__(self, config_path: str, workspace: str, kernel: str = "python3"):
        if not config_path or not workspace:
            raise ValueError(
                f"config path={config_path} or workspace={workspace} is empty"
            )
        self.config_path = config_path
        self.workspace = workspace
        self.process = None
        self.is_running = False
        logger.info(
            "new kernel manager with config path %s and worksapce %s",
            config_path,
            workspace,
        )
        self.kernel = kernel

    def start(self):
        """
        Start a kernel instance and generate the kernel connection file
        """
        self.is_running = True

        os.makedirs(self.workspace, exist_ok=True)
        launch_kernel_script_path = os.path.join(
            pathlib.Path(__file__).parent.resolve(), "launch_kernel.py"
        )
        self.process = subprocess.Popen(
            [
                sys.executable,
                launch_kernel_script_path,
                "--connection_file=" + self.config_path,
                "--kernel=" + self.kernel,
            ],
            cwd=self.workspace,
        )
        logger.info("Start the kernel with process id %s", str(self.process.pid))
        while True:
            if not os.path.isfile(self.config_path):
                sleep(1)
            else:
                try:
                    with open(self.config_path, "r") as fp:
                        logger.info("connection file content %s", json.load(fp))
                    break
                except json.JSONDecodeError:
                    pass

    def stop(self):
        """
        stop the kernel instance
        """
        self.is_running = False
        logger.info("stop the kernel with process id %s", str(self.process.pid))
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def __str__(self):
        return f'KernelManager(config_path="{self.config_path}", workspace="{self.workspace}")'
