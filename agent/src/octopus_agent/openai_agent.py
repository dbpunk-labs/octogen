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
import openai
import logging
from pydantic import BaseModel, Field
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

OCTOPUS_FUNCTIONS = [{
    "name": "execute_python_code",
    "description": "Safely execute arbitrary Python code and return the result, stdout, and stderr.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "the python code to be executed"},
            "explanation": {
                "type": "string",
                "description": "the explanation about the python code",
            },
            "saved_filenames": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of filenames that were created by the code",
            },
        },
        "required": ["code", "explanation"],
    },
}]


class OpenaiAgent(BaseAgent):

    def __init__(self, model, system_prompt, sdk):
        super().__init__(sdk)
        self.model = model
        self.system_prompt = system_prompt
        logger.info(f"use openai model {model}")
        logger.info(f"use openai with system prompt {system_prompt}")

    async def call_openai(self, messages):
        """
        call the openai api
        """
        response = await openai.ChatCompletion.acreate(
            engine=self.model,
            messages=messages,
            temperature=0,
            functions=OCTOPUS_FUNCTIONS,
            function_call="auto",
        )
        return response

    async def handle_function(
        self, message, queue, token_usage=0, iteration=0, model_name=""
    ):
        if "function_call" in message:
            function_name = message["function_call"]["name"]
            arguments = message["function_call"]["arguments"]
            logger.debug(f"call function {function_name} with args {arguments}")
            code = arguments["code"]
            explanation = arguments["explanation"]
            saved_filenames = arguments.get("saved_filenames", [])
            tool_input = json.dumps({
                "code": code,
                "explanation": explanation,
                "saved_filenames": saved_filenames,
            })
            # send the respond to client
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
            async for (result, respond) in self.call_function(
                code,
                iteration=iteration,
                token_usage=token_usage,
                model_name=model_name,
            ):
                function_result = result
                if respond:
                    await queue.put(respond)
        else:
            raise Exception("bad message, function message expected")

    async def arun(self, task, queue, max_iteration=5):
        """ """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        iterations = 0
        token_usage = 0
        model_name = ""
        try:
            while iterations < max_iteration:
                iterations += 1
                response = self.call_openai(messages)
                model_name = response["model"]
                token_usage += response["usage"]["total_tokens"]
                chat_message = response["choices"][0]["message"]
                if "function_call" in chat_message:
                    # call function
                    function_result = await self.handle_function(
                        message, queue, token_usage, iterations, model_name
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
                    # TODO optimize the token limitation
                    if function_result.has_result:
                        messages.append({
                            "role": "function",
                            "name": chat_message["function_call"]["name"],
                            "content": function_result.console_stdout[0:500],
                        })
                    elif function_result.has_error:
                        messages.append({
                            "role": "function",
                            "name": chat_message["function_call"]["name"],
                            "content": function_result.console_stderr[0:500],
                        })
                    else:
                        messages.append({
                            "role": "function",
                            "name": chat_message["function_call"]["name"],
                            "content": function_result.console_stdout[0:500],
                        })
                else:
                    # end task
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iteration,
                            respond_type=TaskRespond.OnFinalAnswerType,
                            model_name=model_name,
                            final_respond=FinalRespond(answer=chat_message["content"]),
                        )
                    )
                    break
        finally:
            await queue.put(None)
