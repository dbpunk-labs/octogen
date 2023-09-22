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
from grpc.aio import AioRpcError
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
from .agent_llm import LLMManager
from .agent_builder import build_mock_agent, build_openai_agent, build_codellama_agent
import databases
import orm
from datetime import datetime
from .utils import parse_image_filename

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
        agent = self.agents[metadata["api_key"]]["agent"]
        tool_input = json.dumps({
            "code": lite_app.code,
            "explanation": "",
            "saved_filenames": lite_app.saved_filenames.split(",")
            if lite_app.saved_filenames
            else [],
        })
        yield agent_server_pb2.TaskRespond(
            respond_type=agent_server_pb2.TaskRespond.OnAgentActionType,
            on_agent_action=agent_server_pb2.OnAgentAction(
                input=tool_input, tool="execute_python_code"
            ),
        )
        function_result = None
        async for (result, respond) in agent.call_function(lite_app.code):
            function_result = result
            if respond:
                logger.debug(f"the respond {respond}")
                yield respond
        output_files = (
            function_result.saved_filenames
            if function_result and function_result.saved_filenames
            else []
        )
        yield agent_server_pb2.TaskRespond(
            respond_type=agent_server_pb2.TaskRespond.OnAgentActionEndType,
            on_agent_action_end=agent_server_pb2.OnAgentActionEnd(
                output="", output_files=output_files
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
                desc=lite_app.desc,
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
            logger.info(f"create a codellama agent {request.endpoint}")
            grammer_path = os.path.join(
                pathlib.Path(__file__).parent.resolve(), "grammar.bnf"
            )
            agent = build_codellama_agent(
                config["llama_api_base"], config["llama_api_key"], sdk, grammer_path
            )
            self.agents[request.key] = {"sdk": sdk, "agent": agent}
        return agent_server_pb2.AddKernelResponse(code=0, msg="ok")

    async def send_task(
        self, request: agent_server_pb2.SendTaskRequest, context: ServicerContext
    ) -> AsyncIterable[agent_server_pb2.TaskRespond]:
        """
        process the task from the client
        """
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
        sdk = self.agents[metadata["api_key"]]["sdk"]
        queue = asyncio.Queue()

        async def worker(task, agent, queue, sdk):
            try:
                return await agent.arun(task, queue)
            except AioRpcError as rpc_ex:
                logger.exception("cancel the request worker")
                try:
                    await sdk.stop()
                except Exception as ex:
                    pass
                result = str(rpc_ex)
                return result
            except Exception as ex:
                logger.exception("fail to run agent")
                result = str(ex)
                return result

        logger.debug("create the agent task")
        task = asyncio.create_task(worker(request.task, agent, queue, sdk))
        try:
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
        except AioRpcError as rpc_ex:
            logger.exception("cancel the request")
            task.cancel()
            pass
        except Exception as ex:
            respond = agent_server_pb2.TaskRespond(
                token_usage=0,
                model_name="",
                iteration=1,
                respond_type=agent_server_pb2.TaskRespond.OnFinalAnswerType,
                final_respond=agent_server_pb2.FinalRespond(answer=str(ex)),
            )
            yield respond

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
