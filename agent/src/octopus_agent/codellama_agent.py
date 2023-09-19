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

import json
import logging
import io
from .codellama_client import CodellamaClient
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .base_agent import BaseAgent, TypingState
from .tokenizer import tokenize

logger = logging.getLogger(__name__)


class CodellamaAgent(BaseAgent):

    def __init__(self, client, kernel_sdk):
        super().__init__(kernel_sdk)
        self.client = client

    def _format_output(self, json_response):
        """
        format the response and send it to the user
        """
        answer = json_response["explanation"]
        if json_response["action"] == "no_action":
            return answer
        elif json_response["action"] == "print_message":
            if json_response["action_input"]:
                return json_response["action_input"]
            else:
                return json_response["explanation"]
        else:
            answer_code = """%s
```%s
%s
```
""" % (
                answer,
                json_response["language"],
                json_response["action_input"],
            )
            return answer_code

    async def handle_function(
        self, json_response, queue, token_usage=0, iteration=0, model_name=""
    ):
        code = json_response["action_input"]
        explanation = json_response["explanation"]
        saved_filenames = json_response.get("saved_filenames", [])
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
        async for (result, respond) in self.call_function(
            code,
            iteration=iteration,
            token_usage=token_usage,
            model_name=model_name,
        ):
            function_result = result
            if respond:
                await queue.put(respond)
        return function_result

    def _get_argument_new_typing(self, message):
        state = TypingState.START
        explanation_str = ""
        action_input_str = ""
        for token_state, token in tokenize(io.StringIO(message)):
            if token_state == None:
                if state == TypingState.EXPLANATION and token[0] == 1:
                    explanation_str = token[1]
                    state = TypingState.START
                if state == TypingState.CODE and token[0] == 1:
                    action_input_str = token[1]
                    state = TypingState.START
                if token[1] == "explanation":
                    state = TypingState.EXPLANATION
                if token[1] == "action_input":
                    state = TypingState.CODE
            else:
                # String
                if token_state == 9 and state == TypingState.EXPLANATION:
                    explanation_str = "".join(token)
                elif token_state == 9 and state == TypingState.CODE:
                    action_input_str = "".join(token)
        return (state, explanation_str, action_input_str)

    async def call_codellama(self, question, chat_history, queue):
        state = None
        message = ""
        text_content = ""
        code_content = ""
        async for line in self.client.prompt(question, chat_history=chat_history):
            if len(line) < 6:
                continue
            respond = json.loads(line[6:])
            message += respond["content"]
            logger.debug(f" message {message}")
            (
                state,
                explanation_str,
                action_input_str,
            ) = self._get_argument_new_typing(message)
            if explanation_str and text_content != explanation_str:
                typed_chars = explanation_str[len(text_content) :]
                text_content = explanation_str
                await queue.put(
                    TaskRespond(
                        token_usage=0,
                        iteration=0,
                        respond_type=TaskRespond.OnAgentTextTyping,
                        model_name="",
                        typing_content=typed_chars,
                    )
                )
            if action_input_str and code_content != action_input_str:
                typed_chars = action_input_str[len(code_content) :]
                code_content = action_input_str
                await queue.put(
                    TaskRespond(
                        token_usage=0,
                        iteration=0,
                        respond_type=TaskRespond.OnAgentCodeTyping,
                        model_name="",
                        typing_content=typed_chars,
                    )
                )
            logger.debug(
                f"argument explanation:{explanation_str} code:{action_input_str}"
            )
            if respond["stop"]:
                state = respond
        return (message, state)

    async def arun(self, question, queue, max_iteration=5):
        """
        run the agent
        """
        history = []
        current_question = question
        # TODO Streaming and reason action
        iteration = 0
        token_usage = 0
        model_name = ""
        try:
            while iteration < max_iteration:
                iteration += 1
                response = []
                chat_history = "\n".join(history)
                (message, state) = await self.call_codellama(
                    current_question, chat_history, queue
                )
                json_response = json.loads(message)
                logger.debug(f" codellama response {json_response}")
                if (
                    json_response["action"] == "execute_python_code"
                    and json_response["action_input"]
                ):
                    function_result = await self.handle_function(
                        json_response, queue, token_usage, iteration, model_name
                    )
                    logger.debug(f"the function result {function_result}")
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iteration,
                            respond_type=TaskRespond.OnAgentActionEndType,
                            model_name=model_name,
                            on_agent_action_end=OnAgentActionEnd(
                                output="", output_files=function_result.saved_filenames
                            ),
                        )
                    )
                    history.append("User:%s" % current_question)
                    history.append("Octopus:%s\n" % ("".join(response)))
                    ins = "Check if the following output meets the goal. If it does, explain it and stop respond. Otherwise, try a new solution."
                    # TODO limit the output size
                    if function_result.has_result:
                        current_question = f"{ins} \n {function_result.console_stdout}"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stdout
                        )
                    elif function_result.has_error:
                        current_question = f"{ins} \n {function_result.console_stderr}"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stderr
                        )
                    else:
                        current_question = f"{ins} \n {function_result.console_stdout}"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stdout
                        )
                else:
                    result = self._format_output(json_response)
                    await queue.put(
                        TaskRespond(
                            token_usage=token_usage,
                            iteration=iteration,
                            respond_type=TaskRespond.OnFinalAnswerType,
                            model_name=model_name,
                            final_respond=FinalRespond(answer=result),
                        )
                    )
                    break
        finally:
            await queue.put(None)
