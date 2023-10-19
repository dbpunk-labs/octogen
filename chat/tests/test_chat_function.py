#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

from og_terminal.terminal_chat import gen_a_random_emoji
from og_terminal.terminal_chat import parse_numbers
from og_terminal.terminal_chat import handle_action_end
from og_proto import agent_server_pb2


def test_gen_a_random_emoji():
    assert gen_a_random_emoji()


def test_parse_number():
    test_text = "/cc0"
    numbers = parse_numbers(test_text)
    assert numbers
    assert numbers[0] == "0"


def test_ok_handle_action_end():
    segments = [(0, "", "")]
    images = []
    values = [()]
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )
    respond = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
        on_step_action_end=agent_server_pb2.OnStepActionEnd(
            output="", output_files=[], has_error=False
        ),
    )
    handle_action_end(segments, respond, images, values)
    assert segments[0][1] == "✅"


def test_error_handle_action_end():
    segments = [(0, "", "")]
    images = []
    values = [()]
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )

    respond = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
        on_step_action_end=agent_server_pb2.OnStepActionEnd(
            output="", output_files=[], has_error=True
        ),
    )

    handle_action_end(segments, respond, images, values)
    assert segments[0][1] == "❌"
