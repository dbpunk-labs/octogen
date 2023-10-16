# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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
import tempfile
from pathlib import Path
from typing import Awaitable, Callable, Optional, AsyncIterable
from grpc.aio import ServicerContext, server, ServerInterceptor
from google.rpc import status_pb2
from dotenv import dotenv_values
from ..kernel.kernel_mgr import KernelManager
from og_proto.kernel_server_pb2_grpc import KernelServerNodeServicer
from og_proto.kernel_server_pb2_grpc import add_KernelServerNodeServicer_to_server
from og_proto import kernel_server_pb2
from og_proto import common_pb2
from ..kernel.kernel_client import KernelClient
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
        os.makedirs(config["workspace"], exist_ok=True)
        config_root_path = config["config_root_path"]
        workspace = config["workspace"]
        logger.info(
            f"start kernel rpc with config root path {config_root_path} and workspace {workspace}"
        )

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
            logger.warning(
                "the request will be ignored for that the kernel has been started"
            )
            return kernel_server_pb2.StartKernelResponse(
                code=0, msg="the kernel has been started"
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
        filename = request.filename
        workspace = config["workspace"]
        target_filename = f"{workspace}{os.sep}{filename}"
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
        temp_dir = tempfile.mkdtemp(prefix="octogen")
        filename = "".join(random.choices(string.ascii_lowercase, k=16))
        tmp_full_path = f"{temp_dir}{os.sep}{filename}"
        target_filename = None
        logger.info(f"upload file to temp file {tmp_full_path}")
        length = 0
        async with aiofiles.open(tmp_full_path, "wb") as afp:
            async for chunk in request:
                length = length + await afp.write(chunk.buffer)
                logger.debug(f"write the {tmp_full_path} with {length}")
                if not target_filename:
                    target_filename = "%s/%s" % (config["workspace"], chunk.filename)
        if length != 0:
            logging.info(f"move file from {tmp_full_path} to  {target_filename}")
            await aio_os.rename(tmp_full_path, target_filename)
        else:
            logging.warning("empty file")
        await aio_os.rmdir(temp_dir)
        return common_pb2.FileUploaded(length=length)

    async def execute(
        self, request: kernel_server_pb2.ExecuteRequest, context: ServicerContext
    ) -> AsyncIterable[kernel_server_pb2.ExecuteResponse]:
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
        async for msg in self.kcs[kernel_name].read_response(context, 5):
            try:
                if context.cancelled() or not msg:
                    break
                if msg["parent_header"]["msg_id"] != msg_id:
                    continue
                if msg["msg_type"] in ["status", "execute_input"]:
                    continue
                respond = self._build_payload(msg, config["workspace"])
                yield respond
            except Exception as ex:
                logger.exception("fail to handle the result")

    def _build_payload(self, msg, workspace) -> kernel_server_pb2.ExecuteResponse:
        if msg["msg_type"] == "display_data":
            if "image/png" in msg["content"]["data"]:
                filename = "octopus_%s.png" % uuid.uuid4().hex
                fullpath = "%s/%s" % (workspace, filename)
                with open(fullpath, "wb+") as fd:
                    data = msg["content"]["data"]["image/png"].encode("ascii")
                    buffer = base64.b64decode(data)
                    fd.write(buffer)
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.ResultType,
                    output=json.dumps({"image/png": filename}),
                )
            elif "image/gif" in msg["content"]["data"]:
                filename = "octopus_%s.gif" % uuid.uuid4().hex
                fullpath = "%s/%s" % (workspace, filename)
                with open(fullpath, "wb+") as fd:
                    data = msg["content"]["data"]["image/gif"].encode("ascii")
                    buffer = base64.b64decode(data)
                    fd.write(buffer)
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.ResultType,
                    output=json.dumps({"image/gif": filename}),
                )
            elif "text/plain" in msg["content"]["data"]:
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.ResultType,
                    output=json.dumps(
                        {"text/plain": msg["content"]["data"]["text/plain"]}
                    ),
                )
            else:
                logger.warning(f" unsupported display_data {msg}")
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.ResultType,
                    output=json.dumps({}),
                )
                # keys = ",".join(msg["content"]["data"].keys())
                # raise Exception(
                #    f"unsupported display data type {keys} for the result {msg}"
                # )

        if msg["msg_type"] == "execute_result":
            logger.debug("result data %s", msg["content"]["data"]["text/plain"])
            return kernel_server_pb2.ExecuteResponse(
                output_type=kernel_server_pb2.ExecuteResponse.ResultType,
                output=json.dumps({"text/plain": msg["content"]["data"]["text/plain"]}),
            )
        elif msg["msg_type"] == "stream":
            if msg["content"]["name"] == "stdout":
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.StdoutType,
                    output=json.dumps({"text": msg["content"]["text"]}),
                )
            else:
                return kernel_server_pb2.ExecuteResponse(
                    output_type=kernel_server_pb2.ExecuteResponse.StderrType,
                    output=json.dumps({"text": msg["content"]["text"]}),
                )
        elif msg["msg_type"] == "error":
            if len(msg["content"]["traceback"]) > 6:
                traceback = "\n".join(msg["content"]["traceback"][:3])
                traceback = traceback + "\n".join(msg["content"]["traceback"][-3:])
            else:
                traceback = "\n".join(msg["content"]["traceback"])
            return kernel_server_pb2.ExecuteResponse(
                output_type=kernel_server_pb2.ExecuteResponse.TracebackType,
                output=json.dumps({"traceback": ansi_escape.sub("", traceback)}),
            )
        raise Exception(f"unsupported msg type {msg}")


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
