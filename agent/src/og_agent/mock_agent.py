# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import time
import logging
from .base_agent import BaseAgent, TypingState, TaskContext
from og_proto.agent_server_pb2 import OnStepActionStart, TaskResponse, OnStepActionEnd, FinalAnswer, TypingContent
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
                TaskResponse(
                    state=task_context.to_context_state_proto(),
                    response_type=TaskResponse.OnModelTypeText,
                    typing_content=TypingContent(
                        content=message["explanation"], language="text"
                    ),
                )
            )
        if message.get("code", None):
            await queue.put(
                TaskResponse(
                    state=task_context.to_context_state_proto(),
                    response_type=TaskResponse.OnModelTypeCode,
                    typing_content=TypingContent(
                        content=message["code"], language="python"
                    ),
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
            "language": "python",
        })
        await queue.put(
            TaskResponse(
                state=task_context.to_context_state_proto(),
                response_type=TaskResponse.OnStepActionStart,
                on_step_action_start=OnStepActionStart(
                    input=tool_input, tool="execute"
                ),
            )
        )
        function_result = None
        async for (result, respond) in self.call_function(code, context, task_context):
            function_result = result
            if respond:
                await queue.put(respond)
        return function_result

    async def arun(self, request, queue, context, task_opt):
        """
        run the agent

        """
        task = request.task
        task_context = TaskContext(
            start_time=time.time(),
            output_token_count=10,
            input_token_count=10,
            llm_name="mock",
            llm_respond_duration=1000,
        )
        iteration = 0
        try:
            while iteration <= 10:
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
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnStepActionEnd,
                            on_step_action_end=OnStepActionEnd(
                                output="",
                                output_files=function_result.saved_filenames,
                                has_error=function_result.has_error,
                            ),
                        )
                    )
                else:
                    await queue.put(
                        TaskResponse(
                            state=task_context.to_context_state_proto(),
                            response_type=TaskResponse.OnFinalAnswer,
                            final_answer=FinalAnswer(answer=message["explanation"]),
                        )
                    )
                    break
        finally:
            await queue.put(None)
