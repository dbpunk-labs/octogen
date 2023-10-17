# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import json
import logging
import io
import time
from .codellama_client import CodellamaClient
from og_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .base_agent import BaseAgent, TypingState, TaskContext
from .tokenizer import tokenize
import tiktoken

logger = logging.getLogger(__name__)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


class CodellamaAgent(BaseAgent):

    def __init__(self, client, kernel_sdk):
        super().__init__(kernel_sdk)
        self.client = client

    def _output_exception(self):
        return (
            "Sorry, the LLM did return nothing, You can use a better performance model"
        )

    def _format_output(self, json_response):
        """
        format the response and send it to the user
        """
        answer = json_response["explanation"]
        if json_response["action"] == "no_action":
            return answer
        elif json_response["action"] == "show_sample_code":
            return ""
        else:
            code = json_response.get("action_input", None)
            answer_code = """%s
```%s
%s
```
""" % (
                answer,
                json_response.get("language", "python"),
                code if code else "",
            )
            return answer_code

    async def handle_show_sample_code(
        self, json_response, queue, context, task_context
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
                state=task_context.to_task_state_proto(),
                respond_type=TaskRespond.OnAgentActionType,
                on_agent_action=OnAgentAction(
                    input=tool_input, tool="show_sample_code"
                ),
            )
        )

    async def handle_install_package(self, json_response, queue, context, task_context):
        package = json_response["action_input"]
        code = f"!pip install {package}"
        explanation = json_response["explanation"]
        saved_filenames = json_response.get("saved_filenames", [])
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
            if context.done():
                logger.debug("the client has cancelled the request")
                break
            function_result = result
            if respond:
                await queue.put(respond)
        return function_result

    async def handle_function(self, json_response, queue, context, task_context):
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
                state=task_context.to_task_state_proto(),
                respond_type=TaskRespond.OnAgentActionType,
                on_agent_action=OnAgentAction(
                    input=tool_input, tool="execute_python_code"
                ),
            )
        )
        function_result = None

        async for (result, respond) in self.call_function(code, context, task_context):
            if context.done():
                logger.debug("the client has cancelled the request")
                break
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

    async def call_codellama(
        self, question, chat_history, queue, context, task_context
    ):
        """
        call codellama api
        """
        start_time = time.time()
        num_tokens = len(encoding.encode(question)) + len(encoding.encode(chat_history))
        task_context.sent_token_count += num_tokens
        state = None
        message = ""
        text_content = ""
        code_content = ""
        async for line in self.client.prompt(question, chat_history=chat_history):
            if len(line) < 6:
                continue
            if context.done():
                logger.debug("the client has cancelled the request")
                break
            respond = json.loads(line[6:])
            task_context.generated_token_count += len(
                encoding.encode(respond["content"])
            )
            task_context.model_respond_duration += int(
                (time.time() - start_time) * 1000
            )
            start_time = time.time()
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
                        state=task_context.to_task_state_proto(),
                        respond_type=TaskRespond.OnAgentTextTyping,
                        typing_content=typed_chars,
                    )
                )
            if action_input_str and code_content != action_input_str:
                typed_chars = action_input_str[len(code_content) :]
                code_content = action_input_str
                await queue.put(
                    TaskRespond(
                        state=task_context.to_task_state_proto(),
                        respond_type=TaskRespond.OnAgentCodeTyping,
                        typing_content=typed_chars,
                    )
                )
            logger.debug(
                f"argument explanation:{explanation_str} code:{action_input_str}"
            )
            if respond["stop"]:
                state = respond

        return (message, state)

    async def arun(self, question, queue, context, max_iteration=5):
        """
        run the agent
        """
        history = []
        current_question = question
        task_context = TaskContext(
            start_time=time.time(),
            generated_token_count=0,
            sent_token_count=0,
            model_name="codellama",
            iteration_count=0,
            model_respond_duration=0,
        )
        iteration = 0
        try:
            while iteration < max_iteration:
                if context.done():
                    logger.debug("the client has cancelled the request")
                    break
                iteration += 1
                task_context.iteration_count = iteration
                chat_history = "\n".join(history)
                (message, state) = await self.call_codellama(
                    current_question, chat_history, queue, context, task_context
                )
                try:
                    json_response = json.loads(message)
                    if not json_response:
                        await queue.put(
                            TaskRespond(
                                state=task_context.to_task_state_proto(),
                                respond_type=TaskRespond.OnFinalAnswerType,
                                final_respond=FinalRespond(
                                    answer=self._output_exception()
                                ),
                            )
                        )
                        break
                except Exception as ex:
                    logger.exception(f"fail to load message the message is {message}")
                    await queue.put(
                        TaskRespond(
                            state=task_context.to_task_state_proto(),
                            respond_type=TaskRespond.OnFinalAnswerType,
                            final_respond=FinalRespond(
                                answer="The model made an invalid respone"
                            ),
                        )
                    )
                    break
                logger.debug(f" codellama response {json_response}")
                if (
                    json_response["action"] == "execute_python_code"
                    and json_response["action_input"]
                ):
                    function_result = await self.handle_function(
                        json_response, queue, context, task_context
                    )
                    logger.debug(f"the function result {function_result}")
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
                    history.append("User:%s" % current_question)
                    action_output = "the output of execute_python_code:"
                    # TODO limit the output size
                    if function_result.has_result:
                        octogen_response = f"Octogen:{message}\n{action_output}\n{function_result.console_stdout}"
                        history.append(octogen_response)
                        current_question = "Give me the final answer summary if the above output of action  meets the goal Otherwise try a new step"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stdout
                        )
                    elif function_result.has_error:
                        octogen_response = f"Octogen:{message}\n{action_output}\n{function_result.console_stderr}"
                        history.append(octogen_response)
                        current_question = f"Generate a new step to fix the above error"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stderr
                        )
                    else:
                        octogen_response = f"Octogen:{message}\n{action_output}\n{function_result.console_stdout}"
                        history.append(octogen_response)
                        current_question = "Give me the final answer summary if the above output of action  meets the goal Otherwise try a new step"
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % function_result.console_stdout
                        )

                elif (
                    json_response["action"] == "show_sample_code"
                    and json_response["action_input"]
                ):
                    await self.handle_show_sample_code(
                        json_response, queue, context, task_context
                    )
                    result = self._format_output(json_response)
                    await queue.put(
                        TaskRespond(
                            state=task_context.to_task_state_proto(),
                            respond_type=TaskRespond.OnFinalAnswerType,
                            final_respond=FinalRespond(answer=result),
                        )
                    )
                    break
                elif (
                    json_response["action"] == "install_python_package"
                    and json_response["action_input"]
                ):
                    function_result = await self.handle_install_package(
                        json_response, queue, context, task_context
                    )
                    logger.debug(f"the function result {function_result}")
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
                    history.append("User:%s" % current_question)
                    history.append("Octogen:%s" % message)
                    ins = "the output of install_python_package:"
                    # TODO limit the output size
                    if function_result.has_result:
                        current_question = f"{ins}\n{function_result.console_stdout}"
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
                            state=task_context.to_task_state_proto(),
                            respond_type=TaskRespond.OnFinalAnswerType,
                            final_respond=FinalRespond(answer=result),
                        )
                    )
                    break
        finally:
            await queue.put(None)
