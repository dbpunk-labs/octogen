# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import pytest

from og_kernel.kernel.kernel_mgr import KernelManager


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
