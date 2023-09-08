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
import pytest

from octopus_kernel.kernel.kernel_mgr import KernelManager


@pytest.mark.parametrize(
    "config_path, workspace",
    [
        ("", ""),
        ("kernel_connection_file.json", ""),
        ("", "/tmp/workspace1"),
    ],
)
def test_init_with_invalid_args(config_path, workspace):
    with pytest.raises(ValueError):
        KernelManager(config_path, workspace)


def test_init_with_valid_args():
    km = KernelManager(
        config_path="/tmp/kernel_connection_file.json",
        workspace="/tmp/workspace1",
    )
    assert km.config_path == "/tmp/kernel_connection_file.json"
    assert km.workspace == "/tmp/workspace1"
    assert km.process is None
    assert not km.is_running


def test_start_kernel():
    km = KernelManager(
        config_path="/tmp/kernel_connection_file1.json",
        workspace="/tmp/workspace1",
    )
    km.start()
    assert km.is_running
    assert km.process is not None
    km.stop()


def test_stop_kernel():
    km = KernelManager(
        config_path="/tmp/kernel_connection_file2.json",
        workspace="/tmp/workspace2",
    )
    km.start()
    km.stop()
    assert not km.is_running
    assert km.process is None
