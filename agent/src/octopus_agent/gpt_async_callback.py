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
import asyncio
from uuid import UUID
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from langchain.callbacks.base import AsyncCallbackHandler, BaseCallbackHandler
from octopus_proto.agent_server_pb2 import OnAgentAction, TaskRespond, OnAgentActionEnd
from langchain.schema.agent import AgentAction, AgentFinish
from langchain.schema import LLMResult
from .utils import parse_link

logger = logging.getLogger(__name__)


class AgentAsyncHandler(AsyncCallbackHandler):
    """the agent async callback handler"""

    def __init__(self, queue):
        self.token_usage = 0
        self.model_name = ""
        self.iteration = 0
        self.images = []
        self.saved_images = []
        self.queue = queue
        self.stack = []

    async def exit_the_queue(self):
        await self.queue.put(None)

    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        logger.debug(f"on_tool_end {output}")
        self.stack.append("on_tool_end")
        output_files = []
        name, link = parse_link(output)
        if name and link:
            output_files.append(link)
        respond = TaskRespond(
            token_usage=self.token_usage,
            on_agent_action_end=OnAgentActionEnd(
                output=output, output_files=output_files
            ),
        )
        await self.queue.put(respond)

    async def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        logger.debug(f"on agent action {action}")
        self.stack.append("on_agent_action")
        respond = TaskRespond(
            token_usage=self.token_usage,
            on_agent_action=OnAgentAction(
                input=json.dumps(action.tool_input), tool=action.tool
            ),
        )
        await self.queue.put(respond)

    async def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        # end of the queue
        logger.debug(f"on_agent_finish {finish}")
        self.stack.append("on_agent_finish")
        logger.debug("the stack %s" % ("\n".join(self.stack)))
        await self.queue.put(None)

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.stack.append("on_llm_start")

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM ends running."""
        logger.debug(f"on_llm_end {response.llm_output}")
        try:
            self.stack.append("on_llm_end")
            self.token_usage += response.llm_output["token_usage"]["total_tokens"]
            self.model_name = response.llm_output["model_name"]
            self.iteration += 1
        except Exception as ex:
            pass
