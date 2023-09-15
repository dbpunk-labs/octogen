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
import pathlib
import hashlib
import grpc
import json
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
from .langchain_agent_builder import build_mock_agent, build_openai_agent, build_codellama_agent
from .tools import OctopusAPIMarkdownOutput
import langchain
import databases
import orm
from datetime import datetime
from .utils import parse_link


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

langchain.verbose = config.get("verbose", False)
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

    async def assemble(
        self, request: agent_server_pb2.AssembleAppRequest, context: ServicerContext
    ) -> agent_server_pb2.AssembleAppResponse:
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            await context.abort(10, "invalid api key")
        key = metadata["api_key"]
        key_hash = hashlib.sha256(key.encode("UTF-8")).hexdigest()
        if await LiteApp.objects.filter(key_hash=key_hash, name=request.name).first():
            await context.abort(10, f"the app name {request.name} exist")

        logger.debug(
            f"the code {request.code} key {key_hash}, language {request.language}"
        )
        await LiteApp.objects.create(
            key_hash=key_hash,
            name=request.name,
            language=request.language,
            code=request.code,
            time=datetime.now(),
            desc=request.desc,
            saved_filenames=",".join(request.saved_filenames)
            if request.saved_filenames
            else "",
        )
        return agent_server_pb2.AssembleAppResponse(code=0, msg="ok")

    async def run(
        self, request: agent_server_pb2.RunAppRequest, context: ServicerContext
    ) -> AsyncIterable[agent_server_pb2.TaskRespond]:
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            logger.debug("invalid api key")
            await context.abort(10, "invalid api key")
        logger.debug(f"run application {request.name}")
        key = metadata["api_key"]
        key_hash = hashlib.sha256(key.encode("UTF-8")).hexdigest()
        lite_app = await LiteApp.objects.filter(
            key_hash=key_hash, name=request.name
        ).first()
        if not lite_app:
            await context.abort(10, f"no application with name {request.name}")
        tool = self.agents[metadata["api_key"]]["tool"]
        tool_input = json.dumps({
            "code": lite_app.code,
            "explanation": "",
            "saved_filenames": lite_app.saved_filenames.split(",")
            if lite_app.saved_filenames
            else [],
        })
        yield agent_server_pb2.TaskRespond(
            on_agent_action=agent_server_pb2.OnAgentAction(
                input=tool_input, tool="execute_python_code"
            ),
        )
        output = await tool.arun(lite_app.code)
        output_files = []
        name, link = parse_link(output)
        if name and link:
            output_files.append(link)
        yield agent_server_pb2.TaskRespond(
            on_agent_action_end=agent_server_pb2.OnAgentActionEnd(
                output=output, output_files=output_files
            ),
        )

    async def query_apps(
        self, request: agent_server_pb2.QueryAppsRequest, context: ServicerContext
    ) -> agent_server_pb2.QueryAppsResponse:
        metadata = dict(context.invocation_metadata())
        if (
            "api_key" not in metadata
            or metadata["api_key"] not in self.agents
            or not self.agents[metadata["api_key"]]
        ):
            logger.debug("invalid api key")
            await context.abort(10, "invalid api key")
        key = metadata["api_key"]
        key_hash = hashlib.sha256(key.encode("UTF-8")).hexdigest()
        lite_apps = (
            await LiteApp.objects.filter(key_hash=key_hash).order_by("-time").all()
        )
        apps = [
            agent_server_pb2.AppInfo(
                name=lite_app.name,
                language=lite_app.language,
                ctime=int(lite_app.time.timestamp()),
            )
            for lite_app in lite_apps
        ]
        return agent_server_pb2.QueryAppsResponse(apps=apps)

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
        tool = OctopusAPIMarkdownOutput(sdk)
        if config["llm_key"] == "azure_openai" or config["llm_key"] == "openai":
            logger.info("create a openai agent")
            agent = build_openai_agent(
                self.llm,
                sdk,
                config.get("max_iterations", 5),
                self.verbose,
            )
            self.agents[request.key] = {"sdk": sdk, "agent": agent, "tool": tool}
        elif config["llm_key"] == "mock":
            logger.info("create a mock agent")
            agent = build_mock_agent(self.llm)
            self.agents[request.key] = {"sdk": sdk, "agent": agent, "tool": tool}
        elif config["llm_key"] == "codellama":
            logger.info("create a codellama agent")
            grammer_path = os.path.join(
                pathlib.Path(__file__).parent.resolve(), "grammar.bnf"
            )
            agent = build_codellama_agent(
                config["llama_api_base"], config["llama_api_key"], sdk, grammer_path
            )
            self.agents[request.key] = {"sdk": sdk, "agent": agent, "tool": tool}
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
        if config["llm_key"] == "codellama":

            async def worker(task, agent, queue):
                try:
                    return await agent.arun(task, queue)
                except Exception as ex:
                    logger.exception("fail to run agent")
                    result = str(ex)
                    return result

            logger.debug("create the agent task")
            try:
                task = asyncio.create_task(worker(request.task, agent, queue))
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
            except Exception as ex:
                respond = agent_server_pb2.TaskRespond(
                    token_usage=0,
                    model_name="",
                    iteration=1,
                    final_respond=agent_server_pb2.FinalRespond(answer=str(ex)),
                )
                yield respond
        else:
            handler = AgentAsyncHandler(queue)

            async def worker(task, agent, handler):
                try:
                    return await agent.arun(task, callbacks=[handler])
                except Exception as ex:
                    logger.error("fail to run agent for %s", ex)
                    result = str(ex)
                    await handler.exit_the_queue()
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
    await models.create_all()
    serv = server()
    add_AgentServerServicer_to_server(AgentRpcServer(), serv)
    listen_addr = "%s:%s" % (config["rpc_host"], config["rpc_port"])
    serv.add_insecure_port(listen_addr)
    await serv.start()
    await serv.wait_for_termination()


def server_main():
    asyncio.run(serve())
