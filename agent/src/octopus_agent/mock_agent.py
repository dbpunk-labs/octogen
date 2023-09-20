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

import logging
from .base_agent import BaseAgent, TypingState
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .tokenizer import tokenize

logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """
    a test agent for octopus
    """

    def __init__(self, messages, sdk):
        """
        the messages are the cases
        """
        super().__init__(sdk)
        self.messages = messages

    async def call_ai(self, prompt, queue, iteration):
        message = self.messages.get(prompt)[iteration]
        if message.get("explanation", None):
            await queue.put(
                TaskRespond(
                    token_usage=0,
                    iteration=0,
                    respond_type=TaskRespond.OnAgentTextTyping,
                    model_name="",
                    typing_content=message["explanation"],
                )
            )
        if message.get("code", None):
            await queue.put(
                TaskRespond(
                    token_usage=0,
                    iteration=0,
                    respond_type=TaskRespond.OnAgentCodeTyping,
                    model_name="",
                    typing_content=message["code"],
                )
            )
        return message

    async def handle_call_function(self, code, queue, explanation, saved_filenames=[]):
        tool_input = json.dumps({
            "code": code,
            "explanation": explanation,
            "saved_filenames": saved_filenames,
        })
        await queue.put(
            TaskRespond(
                token_usage=token_usage,
                iteration=iteration,
                respond_type=TaskRespond.OnAgentActionType,
                model_name=model_name,
                on_agent_action=OnAgentAction(
                    input=tool_input, tool="execute_python_code"
                ),
            )
        )
        function_result = None
        async for (result, respond) in self.call_function(code):
            function_result = result
            if respond:
                await queue.put(respond)
        return function_result

    async def arun(self, task, queue, max_iteration=5):
        """
        run the agent
        """
        iteration = 0
        try:
            while iteration < max_iteration:
                message = await self.call_ai(task, queue, iteration)
                if message.get("code", None):
                    function_result = await self.handle_call_function(
                        message["code"],
                        message["explanation"],
                        message.get("saved_filenames", []),
                    )
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iterations,
                            respond_type=TaskRespond.OnAgentActionEndType,
                            model_name=model_name,
                            on_agent_action_end=OnAgentActionEnd(
                                output="", output_files=function_result.saved_filenames
                            ),
                        )
                    )
                else:
                    await queue.put(
                        TaskRespond(
                            respond_type=TaskRespond.OnFinalAnswerType,
                            final_respond=FinalRespond(answer=message["explanation"]),
                        )
                    )
                    break
        finally:
            await queue.put(None)
