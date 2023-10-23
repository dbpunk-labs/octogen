#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
from og_terminal.terminal_chat import parse_numbers
from og_terminal.terminal_chat import handle_action_end
from og_terminal.terminal_chat import handle_action_output
from og_terminal.terminal_chat import handle_final_answer
from og_terminal.terminal_chat import handle_typing
from og_terminal.ui_block import TaskBlocks
from og_proto import agent_server_pb2


def test_parse_number():
    test_text = "/cc0"
    numbers = parse_numbers(test_text)
    assert numbers
    assert numbers[0] == "0"


def test_handle_final_answer_smoke_test():
    images = []
    values = []
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )
    respond_content = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnModelTypeText,
        typing_content=agent_server_pb2.TypingContent(
            content="hello world!", language="text"
        ),
    )
    respond_final = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnFinalAnswer,
        final_answer=agent_server_pb2.FinalAnswer(answer=""),
    )
    task_blocks = TaskBlocks(values)
    task_blocks.begin()
    handle_typing(task_blocks, respond_content)
    handle_final_answer(task_blocks, respond_final)
    segments = list(task_blocks.render())
    assert len(segments) == 1, "bad segment count"
    assert segments[0][1] == "🧠"
    assert values[0] == "hello world!"


def test_handle_action_end_boundary_test():
    # Setup
    images = []
    values = []
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )
    task_blocks = TaskBlocks(values)
    task_blocks.begin()

    # Create a response with a large number of output files
    respond = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
        on_step_action_end=agent_server_pb2.OnStepActionEnd(
            output="", output_files=["test.png"] * 1000, has_error=False
        ),
    )

    # Call the function
    handle_action_end(task_blocks, respond, images)

    # Check the results
    assert len(images) == 1000
    assert all(image == "test.png" for image in images)


def test_handle_action_end_smoke_test():
    images = []
    values = []
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )

    respond_stdout = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionStreamStdout,
        console_stdout="hello world!",
    )

    respond = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
        on_step_action_end=agent_server_pb2.OnStepActionEnd(
            output="", output_files=["test.png"], has_error=False
        ),
    )

    task_blocks = TaskBlocks(values)
    task_blocks.begin()
    handle_action_output(task_blocks, respond_stdout)
    handle_action_end(task_blocks, respond, images)
    segments = list(task_blocks.render())
    assert len(segments) == 2, "bad segment count"
    assert segments[0][1] == "✅"
    assert images[0] == "test.png"
    assert values[0] == "hello world!"


def test_error_handle_action_end():
    images = []
    values = []
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )
    task_blocks = TaskBlocks(values)
    task_blocks.begin()

    respond_stderr = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionStreamStderr,
        console_stderr="error",
    )

    respond = agent_server_pb2.TaskResponse(
        state=task_state,
        response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
        on_step_action_end=agent_server_pb2.OnStepActionEnd(
            output="", output_files=["test.png"], has_error=True
        ),
    )
    handle_action_output(task_blocks, respond_stderr)
    handle_action_end(task_blocks, respond, images)
    segments = list(task_blocks.render())
    assert len(segments) == 2, "bad segment count"
    assert segments[0][1] == "❌"
    assert len(images) == 0
    assert values[0] == "\nerror"


def test_handle_action_end_performance_test():
    # Setup
    images = []
    values = []
    task_state = agent_server_pb2.ContextState(
        output_token_count=10,
        llm_name="mock",
        total_duration=1,
        input_token_count=10,
        llm_response_duration=1000,
    )
    task_blocks = TaskBlocks(values)
    task_blocks.begin()

    # Create a large number of responses
    responses = [
        agent_server_pb2.TaskResponse(
            state=task_state,
            response_type=agent_server_pb2.TaskResponse.OnStepActionEnd,
            on_step_action_end=agent_server_pb2.OnStepActionEnd(
                output="",
                output_files=[
                    f"test{i}.png"
                ],  # Modify this line to create unique filenames
                has_error=False,
            ),
        )
        for i in range(1000)
    ]

    # Call the function with each response
    for respond in responses:
        handle_action_end(task_blocks, respond, images)

    # Check the results
    assert len(images) == 1000
    assert all(image == f"test{i}.png" for i, image in enumerate(images))
