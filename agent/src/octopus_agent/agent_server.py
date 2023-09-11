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

import asyncio
import logging
import sys
import os
import grpc
from octopus_proto.agent_server_pb2_grpc import AgentServerServicer
from octopus_proto.agent_server_pb2_grpc import add_AgentServerServicer_to_server
from octopus_proto import agent_server_pb2
from octopus_proto import common_pb2
from octopus_proto import kernel_server_pb2
from dotenv import dotenv_values
from typing import AsyncIterable, Any, Dict, List, Optional, Sequence, Union, Type
from tempfile import gettempdir
from grpc.aio import ServicerContext, server
from octopus_kernel.sdk.kernel_sdk import KernelSDK
from .gpt_async_callback import AgentAsyncHandler
from .agent_llm import LLMManager
from .langchain_agent_builder import build_mock_agent, build_openai_agent

config = dotenv_values(".env")
LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class AgentRpcServer(AgentServerServicer):

    def __init__(self):
        self.agents = {}
        self.max_file_size = int(config["max_file_size"])
        self.verbose = config["verbose"]
        self.llm_manager = LLMManager(config)
        self.llm = self.llm_manager.get_llm()

    async def add_kernel(
        self, request: agent_server_pb2.AddKernelRequest, context: ServicerContext
    ) -> agent_server_pb2.AddKernelResponse:
        """Create a token, only the admin can call this method"""
        metadata = dict(context.invocation_metadata())
        if "api_key" not in metadata or metadata["api_key"] != config["admin_key"]:
            await context.abort(10, "You are not the admin")
        if request.key in self.agents and self.agents[request.key]:
            return agent_server_pb2.AddKernelResponse(code=0, msg="ok")
        # init the sdk
        sdk = KernelSDK(request.endpoint, request.key)
        sdk.connect()
        if config["llm_key"] == "azure_openai":
            logger.info("create a azure openai agent for kernel")
            agent = build_openai_agent(
                self.llm,
                sdk,
                request.workspace,
                config.get("max_iterations", 5),
                self.verbose,
            )
            # TODO a data dir per user
            self.agents[request.key] = {
                "sdk": sdk,
                "workspace": request.workspace,
                "agent": agent,
            }
        elif config["llm_key"] == "mock":
            logger.info("create a mock agent for kernel")
            agent = build_mock_agent(self.llm)
            self.agents[request.key] = {
                "sdk": sdk,
                "workspace": request.workspace,
                "agent": agent,
            }
        return agent_server_pb2.AddKernelResponse(code=0, msg="ok")

    async def send_task(
        self, request: agent_server_pb2.SendTaskRequest, context: ServicerContext
    ) -> AsyncIterable[agent_server_pb2.TaskRespond]:
        logger.debug("receive the task %s ", request.task)
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            logger.debug("invalid api key")
            await context.abort(10, "invalid api key")
        agent = self.agents[metadata["api_key"]]["agent"]
        queue = asyncio.Queue()
        handler = AgentAsyncHandler(queue)

        async def worker(task, agent, handler):
            try:
                return await agent.arun(task, callbacks=[handler])
            except Exception as ex:
                logger.error("fail to run agent for %s", ex)
                result = str(ex)
                return result

        logger.debug("create the agent task")
        try:
            task = asyncio.create_task(worker(request.task, agent, handler))
            token_usage = 0
            while True:
                try:
                    logger.debug("start wait the queue message")
                    # TODO add timeout
                    respond = await queue.get()
                    if not respond:
                        logger.debug("exit the queue")
                        break
                    logger.debug(f"respond {respond}")
                    queue.task_done()
                    yield respond
                except Exception as ex:
                    logger.error(f"fail to get respond for {ex}")
                    break
            await task
            respond = agent_server_pb2.TaskRespond(
                token_usage=handler.token_usage,
                model_name=handler.model_name,
                iteration=handler.iteration,
                final_respond=agent_server_pb2.FinalRespond(answer=task.result()),
            )
            logger.debug(f"respond {respond}")
            yield respond
        except Exception as ex:
            respond = agent_server_pb2.TaskRespond(
                token_usage=0,
                model_name="",
                iteration=1,
                final_respond=agent_server_pb2.FinalRespond(answer=str(ex)),
            )
            yield respond

    async def download(
        self, request: common_pb2.DownloadRequest, context: ServicerContext
    ) -> AsyncIterable[common_pb2.FileChunk]:
        """
        download file
        """
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            await context.abort(10, "invalid api key")
        sdk = self.agents[metadata["api_key"]]["sdk"]
        async for chunk in sdk.download_file(request.filename):
            yield chunk

    async def upload(
        self,
        request: AsyncIterable[common_pb2.FileChunk],
        context: ServicerContext,
    ) -> common_pb2.FileUploaded:
        """
        upload file
        """
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            await context.abort(10, "invalid arguments")
        sdk = self.agents[metadata["api_key"]]["sdk"]

        async def generate_chunk(proxy_request, context, limit):
            length = 0
            async for chunk in proxy_request:
                if length + len(chunk.buffer) > limit:
                    await context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT.value[0],
                        "exceed the max file limit",
                    )
                length += len(chunk.buffer)
                yield chunk

        return await sdk.upload_binary(
            generate_chunk(request, context, self.max_file_size)
        )


async def serve() -> None:
    logger.info(
        "start agent rpc server with host %s and port %s",
        config["rpc_host"],
        config["rpc_port"],
    )
    serv = server()
    add_AgentServerServicer_to_server(AgentRpcServer(), serv)
    listen_addr = "%s:%s" % (config["rpc_host"], config["rpc_port"])
    serv.add_insecure_port(listen_addr)
    await serv.start()
    await serv.wait_for_termination()


def server_main():
    asyncio.run(serve())
