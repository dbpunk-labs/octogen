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
from .codellama_client import CodellamaClient
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd, FinalRespond
from .utils import parse_link

logger = logging.getLogger(__name__)


class CodellamaAgent:

    def __init__(self, client, tool):
        self.client = client
        self.tool = tool

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

    async def arun(self, question, queue, max_iteration=5):
        """
        run the agent
        """
        history = []
        current_question = question
        # TODO Streaming and reason action
        state = None
        iteration = 0
        try:
            while iteration < max_iteration:
                iteration += 1
                response = []
                async for line in self.client.prompt(
                    current_question, chat_history="\n".join(history)
                ):
                    if len(line) < 6:
                        continue
                    respond = json.loads(line[6:])
                    response.append(respond["content"])
                    if respond["stop"]:
                        state = respond
                json_respose = json.loads("".join(response))
                logger.info(f"{json_respose}")
                if (
                    json_respose["action"] == "execute_python_code"
                    and json_respose["action_input"]
                ):
                    tool_input = json.dumps({
                        "code": json_respose["action_input"],
                        "explanation": json_respose["explanation"],
                        "saved_filenames": json_respose["saved_filenames"],
                    })
                    await queue.put(
                        TaskRespond(
                            token_usage=state["tokens_cached"]
                            + state["tokens_evaluated"]
                            + state["tokens_predicted"],
                            iteration=iteration,
                            model_name=state["generation_settings"]["model"],
                            on_agent_action=OnAgentAction(
                                input=tool_input, tool="execute_python_code"
                            ),
                        )
                    )
                    output = await self.tool.arun(code=json_respose["action_input"])
                    output_files = []
                    name, link = parse_link(output)
                    if name and link:
                        output_files.append(link)
                    execute_result = TaskRespond(
                        token_usage=state["tokens_cached"]
                        + state["tokens_evaluated"]
                        + state["tokens_predicted"],
                        iteration=iteration,
                        model_name=state["generation_settings"]["model"],
                        on_agent_action_end=OnAgentActionEnd(
                            output=output, output_files=output_files
                        ),
                    )
                    await queue.put(execute_result)
                    if (
                        not json_respose["is_final_answer"]
                        or output.find("Traceback") >= 0
                    ):
                        history.append("User:%s" % current_question)
                        history.append("Octopus:%s\n" % ("".join(response)))
                        current_question = (
                            "the output of execute_python_code is \n%s" % output
                        )
                        logger.debug(
                            "continue to iterate with codellama with question %s"
                            % output
                        )
                    else:
                        break
                else:
                    result = self._format_output(json_respose)
                    await queue.put(
                        TaskRespond(
                            token_usage=state["tokens_cached"]
                            + state["tokens_evaluated"]
                            + state["tokens_predicted"],
                            iteration=iteration,
                            model_name=state["generation_settings"]["model"],
                            final_respond=FinalRespond(answer=result),
                        )
                    )
                    break
        finally:
            await queue.put(None)
