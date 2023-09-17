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

"""
the websocket server for the kernel
"""
import os
import json
import sys
import logging
import asyncio
import functools
import grpc
import re
import uuid
import random
import string
import base64
from pathlib import Path
from typing import Awaitable, Callable, Optional, AsyncIterable
from grpc.aio import ServicerContext, server, ServerInterceptor
from google.rpc import status_pb2
from dotenv import dotenv_values
from ..kernel.kernel_mgr import KernelManager
from octopus_proto.kernel_server_pb2_grpc import KernelServerNodeServicer
from octopus_proto.kernel_server_pb2_grpc import add_KernelServerNodeServicer_to_server
from octopus_proto import kernel_server_pb2
from octopus_proto import common_pb2
from ..kernel.kernel_client import KernelClient
from tempfile import gettempdir
import aiofiles
from aiofiles import os as aio_os

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
ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def _unary_unary_rpc_terminator(code, details):
    async def terminate(ignored_request, context):
        await context.abort(code, details)

    return grpc.unary_unary_rpc_method_handler(terminate)


class ApiKeyInterceptor(ServerInterceptor):
    """
    the api key interceptor
    """

    def __init__(self, header, value, code, error):
        self._header = header
        self._value = value
        self._terminator = _unary_unary_rpc_terminator(code, error)

    async def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        if (
            self._header,
            self._value,
        ) in handler_call_details.invocation_metadata:
            return await continuation(handler_call_details)
        else:
            return self._terminator


class KernelRpcServer(KernelServerNodeServicer):

    def __init__(self):
        self.kms = {}
        self.kcs = {}
        self.auth_failed_status = status_pb2.Status(
            code=grpc.StatusCode.INVALID_ARGUMENT.value[0],
            message="api key is required",
            details=[],
        )

        os.makedirs(config["config_root_path"], exist_ok=True)

    async def stop(
        self, request: kernel_server_pb2.StopKernelRequest, context: ServicerContext
    ) -> kernel_server_pb2.StopKernelResponse:
        """
        Stop the kernel
        """

        kernel_name = request.kernel_name if request.kernel_name else "python3"
        if kernel_name not in self.kms or not self.kms[kernel_name]:
            logger.warning("no started kernel")
            return kernel_server_pb2.StopKernelResponse(
                key="k", code=1, msg="no started kernel"
            )
        self.kms[kernel_name].stop()
        self.kcs[kernel_name].stop_client()
        self.kms[kernel_name] = None
        self.kcs[kernel_name] = None
        return kernel_server_pb2.StopKernelResponse(code=0, msg="ok")

    async def get_status(
        self, request: kernel_server_pb2.GetStatusRequest, context: ServicerContext
    ) -> kernel_server_pb2.GetStatusResponse:
        kernel_name = request.kernel_name if request.kernel_name else "python3"
        logger.debug("check the kernel %s status", kernel_name)
        if kernel_name not in self.kms or not self.kms[kernel_name]:
            return kernel_server_pb2.GetStatusResponse(is_alive=False, code=0, msg="ok")
        is_alive = await self.kcs[kernel_name].is_alive()
        return kernel_server_pb2.GetStatusResponse(is_alive=is_alive, code=0, msg="ok")

    async def start(
        self, request: kernel_server_pb2.StartKernelRequest, context: ServicerContext
    ) -> kernel_server_pb2.StartKernelResponse:
        """
        Start the kernel
        """
        kernel_name = request.kernel_name if request.kernel_name else "python3"
        if kernel_name in self.kms and self.kms[kernel_name]:
            logger.warning("the kernel has been started")
            return kernel_server_pb2.StartKernelResponse(
                code=1, msg="the kernel has been started"
            )
        logging.info("create a new kernel with kernel_name %s" % kernel_name)
        connection_file = "%s/kernel-%s.json" % (
            config["config_root_path"],
            uuid.uuid4(),
        )
        km = KernelManager(connection_file, config["workspace"], kernel=kernel_name)
        km.start()
        kc = KernelClient(connection_file)
        await kc.start_client()
        self.kms[kernel_name] = km
        self.kcs[kernel_name] = kc
        return kernel_server_pb2.StartKernelResponse(code=0, msg="ok")

    async def download(
        self, request: common_pb2.DownloadRequest, context: ServicerContext
    ) -> AsyncIterable[common_pb2.FileChunk]:
        """
        download file
        """
        target_filename = "%s/%s" % (config["workspace"], request.filename)
        if not await aio_os.path.exists(target_filename):
            await context.abort(10, "%s filename do not exist" % request.filename)
        async with aiofiles.open(target_filename, "rb") as afp:
            while True:
                chunk = await afp.read(1024 * 128)
                if not chunk:
                    break
                yield common_pb2.FileChunk(buffer=chunk, filename=request.filename)

    async def upload(
        self,
        request: AsyncIterable[common_pb2.FileChunk],
        context: ServicerContext,
    ) -> common_pb2.FileUploaded:
        """
        upload file
        """
        tmp_filename = Path(gettempdir()) / "".join(
            random.choices(string.ascii_lowercase, k=16)
        )
        target_filename = None
        logger.info(f"upload file to temp file {tmp_filename}")
        length = 0
        async with aiofiles.open(tmp_filename, "wb+") as afp:
            async for chunk in request:
                length = length + await afp.write(chunk.buffer)
                if not target_filename:
                    target_filename = "%s/%s" % (config["workspace"], chunk.filename)
        logging.info(f"move file from {tmp_filename} to  {target_filename}")
        await aio_os.rename(tmp_filename, target_filename)
        return common_pb2.FileUploaded(length=length)

    async def execute(
        self, request: kernel_server_pb2.ExecuteRequest, context: ServicerContext
    ) -> kernel_server_pb2.ExecuteResponse:
        """
        Execute the python code and return a stream response
        """
        kernel_name = request.kernel_name if request.kernel_name else "python3"
        if not request.code:
            raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "Invalid argument")
        if (
            kernel_name not in self.kms
            or not self.kms[kernel_name]
            or not self.kcs[kernel_name]
        ):
            logger.warning(
                "no started kernel for executing code for kernel name %s" % kernel_name
            )
            raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "Invalid argument")
        logger.debug("the code %s with kernel %s", request.code, kernel_name)
        # TODO check the busy status
        msg_id = self.kcs[kernel_name].execute(request.code)
        response_args = {
            "result": None,
            "stdout": None,
            "stderr": None,
            "traceback": None,
        }
        async for msg in self.kcs[kernel_name].read_response(5):
            if not msg:
                break
            (key, payload) = self._build_payload(msg, config["workspace"])
            if not key or not payload:
                continue
            response_args[key] = json.dumps(payload)
        return kernel_server_pb2.ExecuteResponse(**response_args)

    def _build_payload(self, msg, workspace):
        if msg["msg_type"] == "display_data":
            if "image/png" in msg["content"]["data"]:
                filename = "%s.png" % uuid.uuid4().hex
                fullpath = "%s/%s" % (workspace, filename)
                with open(fullpath, "wb+") as fd:
                    data = msg["content"]["data"]["image/png"].encode("ascii")
                    buffer = base64.b64decode(data)
                    fd.write(buffer)
                return (
                    "result",
                    {
                        "data": {"image/png": filename},
                        "msg_type": msg["msg_type"],
                    },
                )
            elif "image/gif" in msg["content"]["data"]:
                filename = "%s.png" % uuid.uuid4().hex
                fullpath = "%s/%s" % (workspace, filename)
                with open(fullpath, "wb+") as fd:
                    data = msg["content"]["data"]["image/gif"].encode("ascii")
                    buffer = base64.b64decode(data)
                    fd.write(buffer)
                return (
                    "result",
                    {
                        "data": {"image/gif": filename},
                        "msg_type": msg["msg_type"],
                    },
                )
            else:
                logger.warning(f" unsupported display_data {msg}")
                return (
                    "result",
                    {
                        "data": msg["content"]["data"],
                        "msg_type": msg["msg_type"],
                    },
                )
                # keys = ",".join(msg["content"]["data"].keys())
                # raise Exception(
                #    f"unsupported display data type {keys} for the result {msg}"
                # )

        if msg["msg_type"] == "execute_result":
            logger.debug("result data %s", msg["content"]["data"]["text/plain"])
            return (
                "result",
                {
                    "data": msg["content"]["data"],
                    "msg_type": msg["msg_type"],
                },
            )
        elif msg["msg_type"] == "stream":
            lines = msg["content"]["text"].split("\n")
            return (
                msg["content"]["name"],
                {
                    "data": msg["content"]["text"],
                    "content_type": msg["content"]["name"],  # stdout or stderr
                    "msg_type": msg["msg_type"],
                },
            )
        elif msg["msg_type"] == "error":
            if len(msg["content"]["traceback"]) > 6:
                traceback = "\n".join(msg["content"]["traceback"][:3])
                traceback = traceback + "\n".join(msg["content"]["traceback"][-3:])
            else:
                traceback = "\n".join(msg["content"]["traceback"])
            return (
                "traceback",
                {
                    "data": ansi_escape.sub("", traceback),
                    "content_type": "error",
                    "msg_type": msg["msg_type"],
                },
            )
        return (None, None)


async def serve() -> None:
    logger.info(
        "start kernel rpc server with host %s and port %s",
        config["rpc_host"],
        config["rpc_port"],
    )
    interceptors = [
        ApiKeyInterceptor(
            "api_key",
            config["rpc_key"],
            grpc.StatusCode.ABORTED.value[0],
            "api key is required or invalid",
        )
    ]
    serv = server(interceptors=interceptors)
    add_KernelServerNodeServicer_to_server(KernelRpcServer(), serv)
    listen_addr = "%s:%s" % (config["rpc_host"], config["rpc_port"])
    serv.add_insecure_port(listen_addr)
    await serv.start()
    await serv.wait_for_termination()


def server_main():
    asyncio.run(serve())
