# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import time
import logging
from .base_agent import BaseAgent, TypingState, TaskContext
from og_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .tokenizer import tokenize

logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """
    a test agent for octogen
    """

    def __init__(self, messages, sdk):
        """
        the messages are the cases
        """
        super().__init__(sdk)
        self.messages = messages

    async def call_ai(self, prompt, queue, iteration, task_context):
        message = self.messages.get(prompt)[iteration]
        if message.get("explanation", None):
            await queue.put(
                TaskRespond(
                    state=task_context.to_task_state_proto(),
                    respond_type=TaskRespond.OnAgentTextTyping,
                    typing_content=message["explanation"],
                )
            )
        if message.get("code", None):
            await queue.put(
                TaskRespond(
                    state=task_context.to_task_state_proto(),
                    respond_type=TaskRespond.OnAgentCodeTyping,
                    typing_content=message["code"],
                )
            )
        return message

    async def handle_call_function(
        self, code, queue, explanation, context, task_context, saved_filenames=[]
    ):
        tool_input = json.dumps({
            "code": code,
            "explanation": explanation,
            "saved_filenames": saved_filenames,
        })
        await queue.put(
            TaskRespond(
                state=task_context.to_task_state_proto(),
                respond_type=TaskRespond.OnAgentActionType,
                on_agent_action=OnAgentAction(
                    input=tool_input, tool="execute_python_code"
                ),
            )
        )
        function_result = None
        async for (result, respond) in self.call_function(code, context, task_context):
            function_result = result
            if respond:
                await queue.put(respond)
        return function_result

    async def arun(self, task, queue, context, max_iteration=5):
        """
        run the agent
        """
        iteration = 0
        task_context = TaskContext(
            start_time=time.time(),
            generated_token_count=10,
            sent_token_count=10,
            model_name="mock",
            iteration_count=1,
            model_respond_duration=1000,
        )
        try:
            while iteration < max_iteration:
                message = await self.call_ai(task, queue, iteration, task_context)
                iteration = iteration + 1
                if message.get("code", None):
                    function_result = await self.handle_call_function(
                        message["code"],
                        queue,
                        message["explanation"],
                        context,
                        task_context,
                        message.get("saved_filenames", []),
                    )
                    await queue.put(
                        TaskRespond(
                            state=task_context.to_task_state_proto(),
                            respond_type=TaskRespond.OnAgentActionEndType,
                            on_agent_action_end=OnAgentActionEnd(
                                output="",
                                output_files=function_result.saved_filenames,
                                has_error=function_result.has_error,
                            ),
                        )
                    )
                else:
                    await queue.put(
                        TaskRespond(
                            state=task_context.to_task_state_proto(),
                            respond_type=TaskRespond.OnFinalAnswerType,
                            final_respond=FinalRespond(answer=message["explanation"]),
                        )
                    )
                    break
        finally:
            await queue.put(None)
