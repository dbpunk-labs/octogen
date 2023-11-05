# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import asyncio
import logging
import sys
import os
import pathlib
import hashlib
import grpc
import json
from grpc.aio import AioRpcError
from og_proto.agent_server_pb2_grpc import AgentServerServicer
from og_proto.agent_server_pb2_grpc import add_AgentServerServicer_to_server
from og_proto import agent_server_pb2
from og_proto import common_pb2
from og_proto import kernel_server_pb2
from dotenv import dotenv_values
from typing import AsyncIterable, Any, Dict, List, Optional, Sequence, Union, Type
from tempfile import gettempdir
from grpc.aio import ServicerContext, server
from og_sdk.kernel_sdk import KernelSDK
from og_sdk.utils import parse_image_filename
from .agent_llm import LLMManager
from .agent_builder import build_mock_agent, build_openai_agent, build_llama_agent
import databases
import orm
from datetime import datetime

config = dotenv_values(".env")

LOG_LEVEL = (
    logging.DEBUG if config.get("log_level", "info") == "debug" else logging.INFO
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
# the database instance for agent
database = databases.Database("sqlite:///%s" % config["db_path"])
models = orm.ModelRegistry(database=database)


class LiteApp(orm.Model):
    tablename = "lite_app"
    registry = models
    fields = {
        "id": orm.Integer(primary_key=True),
        "key_hash": orm.String(max_length=64, index=True),
        "name": orm.String(max_length=20, index=True),
        "language": orm.String(max_length=20, allow_null=False),
        "code": orm.Text(),
        "time": orm.DateTime(),
        "desc": orm.String(max_length=100, allow_null=True),
        "saved_filenames": orm.String(max_length=512, allow_null=True),
    }


class AgentRpcServer(AgentServerServicer):

    def __init__(self):
        self.agents = {}
        self.max_file_size = int(config["max_file_size"])
        self.verbose = config.get("verbose", False)
        self.llm_manager = LLMManager(config)
        self.llm = self.llm_manager.get_llm()

    async def ping(
        self, request: agent_server_pb2.PingRequest, context: ServicerContext
    ) -> agent_server_pb2.PongResponse:
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            return agent_server_pb2.PongResponse(
                code=-1, msg="Your API Key is invalid!"
            )
        else:
            return agent_server_pb2.PongResponse(
                code=0, msg="Connect to Octopus Agent Ok!"
            )

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
        try:
            sdk.connect()
            await sdk.is_alive()
        except Exception as ex:
            await context.abort(10, f"Connecting to kernel {request.endpoint} failed")
        if config["llm_key"] == "azure_openai" or config["llm_key"] == "openai":
            logger.info(f"create a openai agent {request.endpoint}")
            agent = build_openai_agent(
                sdk,
                config["openai_api_model"],
                is_azure=True if config["llm_key"] == "azure_openai" else False,
            )
            self.agents[request.key] = {"sdk": sdk, "agent": agent}
        elif config["llm_key"] == "mock":
            logger.info(f"create a mock agent to kernel {request.endpoint}")
            agent = build_mock_agent(sdk, config["cases_path"])
            self.agents[request.key] = {"sdk": sdk, "agent": agent}
        elif config["llm_key"] == "codellama":
            logger.info(f"create a llama agent {request.endpoint}")
            grammer_path = os.path.join(
                pathlib.Path(__file__).parent.resolve(), "grammar.bnf"
            )
            agent = build_llama_agent(
                config["llama_api_base"], config["llama_api_key"], sdk, grammer_path
            )
            self.agents[request.key] = {"sdk": sdk, "agent": agent}
        return agent_server_pb2.AddKernelResponse(code=0, msg="ok")

    async def process_task(
        self, request: agent_server_pb2.ProcessTaskRequest, context
    ) -> AsyncIterable[agent_server_pb2.TaskResponse]:
        """
        process the task from the client
        """
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            logger.debug("invalid api key")
            await context.abort(10, "invalid api key")

        logger.debug("receive the task %s ", request.task)
        agent = self.agents[metadata["api_key"]]["agent"]
        sdk = self.agents[metadata["api_key"]]["sdk"]
        queue = asyncio.Queue()

        async def worker(request, agent, queue, context, task_opt):
            return await agent.arun(request, queue, context, task_opt)

        options = (
            request.options
            if request.options
            and request.options.input_token_limit != 0
            and request.options.output_token_limit != 0
            else agent_server_pb2.ProcessOptions(
                streaming=True,
                llm_name="",
                input_token_limit=4000
                if not request.options.input_token_limit
                else request.options.input_token_limit,
                output_token_limit=4000
                if not request.options.output_token_limit
                else request.options.output_token_limit,
                timeout=10,
            )
        )

        logger.debug("create the agent task")
        task = asyncio.create_task(worker(request, agent, queue, context, options))
        while True:
            logger.debug("start wait the queue message")
            # TODO add timeout
            respond = await queue.get()
            if not respond:
                logger.debug("exit the queue")
                break
            logger.debug(f"respond {respond}")
            queue.task_done()
            yield respond
        await task

    async def download(
        self, request: common_pb2.DownloadRequest, context: ServicerContext
    ) -> AsyncIterable[common_pb2.FileChunk]:
        """
        download file from kernel and send it to client
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
        upload file to the kernel workspace
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
    await models.create_all()
    serv = server()
    add_AgentServerServicer_to_server(AgentRpcServer(), serv)
    listen_addr = "%s:%s" % (config["rpc_host"], config["rpc_port"])
    serv.add_insecure_port(listen_addr)
    await serv.start()
    await serv.wait_for_termination()


def server_main():
    asyncio.run(serve())
