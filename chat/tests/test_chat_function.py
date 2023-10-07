#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2023 imotai <imotai@imotai-ub>
#
# Distributed under terms of the MIT license.

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
    task_state = agent_server_pb2.TaskState(
        generated_token_count=10,
        iteration_count=1,
        model_name="mock",
        total_duration=1,
        sent_token_count=10,
        model_respond_duration=1000,
    )
    respond = agent_server_pb2.TaskRespond(
        state=task_state,
        respond_type=agent_server_pb2.TaskRespond.OnAgentActionEndType,
        on_agent_action_end=agent_server_pb2.OnAgentActionEnd(
            output="", output_files=[], has_error=False
        ),
    )
    handle_action_end(segments, respond, images, values)
    assert segments[0][1] == "✅"


def test_error_handle_action_end():
    segments = [(0, "", "")]
    images = []
    values = [()]
    task_state = agent_server_pb2.TaskState(
        generated_token_count=10,
        iteration_count=1,
        model_name="mock",
        total_duration=1,
        sent_token_count=10,
        model_respond_duration=1000,
    )
    respond = agent_server_pb2.TaskRespond(
        state=task_state,
        respond_type=agent_server_pb2.TaskRespond.OnAgentActionEndType,
        on_agent_action_end=agent_server_pb2.OnAgentActionEnd(
            output="", output_files=[], has_error=True
        ),
    )
    handle_action_end(segments, respond, images, values)
    assert segments[0][1] == "❌"
