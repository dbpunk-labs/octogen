# vim:fenc=utf-8
#
# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" """
"""An application to launch a kernel by name in a local subprocess."""
import os
import signal
import uuid

from jupyter_core.application import JupyterApp, base_flags
from tornado.ioloop import IOLoop
from traitlets import Unicode
from jupyter_client.kernelspec import NATIVE_KERNEL_NAME, KernelSpecManager
from jupyter_client.manager import KernelManager


class KernelApp(JupyterApp):
    """Launch a kernel by name in a local subprocess."""

    description = "Run a kernel locally in a subprocess"
    classes = [KernelManager, KernelSpecManager]
    aliases = {
        "kernel": "KernelApp.kernel_name",
        "ip": "KernelManager.ip",
        "connection_file": "KernelApp.connection_file",
    }
    flags = {"debug": base_flags["debug"]}
    kernel_name = Unicode(
        NATIVE_KERNEL_NAME, help="The name of a kernel type to start"
    ).tag(config=True)
    connection_file = Unicode("", help="The connection file path of the kernel").tag(
        config=True
    )

    def initialize(self, argv=None):
        """Initialize the application."""
        super().initialize(argv)
        cf_basename = (
            self.connection_file
            if self.connection_file
            else "kernel-%s.json" % uuid.uuid4()
        )
        self.config.setdefault("KernelManager", {}).setdefault(
            "connection_file", os.path.join(self.runtime_dir, cf_basename)
        )
        self.km = KernelManager(kernel_name=self.kernel_name, config=self.config)

        self.loop = IOLoop.current()
        self.loop.add_callback(self._record_started)

    def setup_signals(self) -> None:
        """Shutdown on SIGTERM or SIGINT (Ctrl-C)"""
        if os.name == "nt":
            return

        def shutdown_handler(signo, frame):
            self.loop.add_callback_from_signal(self.shutdown, signo)

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, shutdown_handler)

    def shutdown(self, signo: int) -> None:
        """Shut down the application."""
        self.log.info("Shutting down on signal %d", signo)
        self.km.shutdown_kernel()
        self.loop.stop()

    def log_connection_info(self) -> None:
        """Log the connection info for the kernel."""
        cf = self.km.connection_file
        self.log.info("Connection file: %s", cf)
        self.log.info("To connect a client: --existing %s", os.path.basename(cf))

    def _record_started(self) -> None:
        """For tests, create a file to indicate that we've started

        Do not rely on this except in our own tests!
        """
        fn = os.environ.get("JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE")
        if fn is not None:
            with open(fn, "wb"):
                pass

    def start(self) -> None:
        """Start the application."""
        self.log.info("Starting kernel %r", self.kernel_name)
        try:
            self.km.start_kernel()
            self.log_connection_info()
            self.setup_signals()
            self.loop.start()
        finally:
            self.km.cleanup_resources()


def run_app():
    KernelApp.launch_instance()
