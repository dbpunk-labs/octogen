# vim:fenc=utf-8
#
# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>


""" """
import logging
import grpc
from grpc import aio
from og_proto import agent_server_pb2, common_pb2
from og_proto.agent_server_pb2_grpc import AgentServerStub
import aiofiles
from typing import AsyncIterable
from .utils import generate_chunk, generate_async_chunk

logger = logging.getLogger(__name__)


class AgentSyncSDK:

    def __init__(self, endpoint, api_key):
        self.endpoint = endpoint
        self.stub = None
        self.metadata = aio.Metadata(
            ("api_key", api_key),
        )
        self.channel = None

    def connect(self):
        if self.channel:
            return
        if self.endpoint.startswith("https"):
            channel_credential = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(
                self.endpoint.replace("https://", ""), channel_credential
            )
        else:
            self.channel = grpc.insecure_channel(self.endpoint)
        self.stub = AgentServerStub(self.channel)

    def assemble(self, name, code, language, desc="", saved_filenames=[]):
        request = agent_server_pb2.AssembleAppRequest(
            name=name,
            language=language,
            code=code,
            saved_filenames=saved_filenames,
            desc=desc,
        )
        response = self.stub.assemble(request, metadata=self.metadata)
        return response

    def run(self, name):
        # TODO support input files
        request = agent_server_pb2.RunAppRequest(name=name)
        for respond in self.stub.run(request, metadata=self.metadata):
            yield respond

    def query_apps(self):
        request = agent_server_pb2.QueryAppsRequest()
        return self.stub.query_apps(request, metadata=self.metadata)

    def add_kernel(self, key, endpoint):
        """
        add kernel instance to the agent and only admin can call this method
        """
        request = agent_server_pb2.AddKernelRequest(endpoint=endpoint, key=key)
        response = self.stub.add_kernel(request, metadata=self.metadata)
        return response

    def ping(self):
        request = agent_server_pb2.PingRequest()
        response = self.stub.ping(request, metadata=self.metadata)
        return response

    def download_file(self, filename, parent_path):
        request = common_pb2.DownloadRequest(filename=filename)
        fullpath = "%s/%s" % (parent_path, filename)
        with open(fullpath, "wb+") as fd:
            for chunk in self.stub.download(request, metadata=self.metadata):
                fd.write(chunk.buffer)

    def upload_file(self, filepath, filename):
        """
        upload file to agent
        """

        # TODO limit the file size

        return self.stub.upload(
            generate_chunk(filepath, filename), metadata=self.metadata
        )

    def prompt(self, prompt, files=[]):
        """
        ask the ai with prompt and  uploaded files
        """
        request = agent_server_pb2.SendTaskRequest(task=prompt, input_files=files)
        for respond in self.stub.send_task(request, metadata=self.metadata):
            yield respond


class AgentSDK:

    def __init__(self, endpoint, api_key):
        self.endpoint = endpoint
        self.stub = None
        self.metadata = aio.Metadata(
            ("api_key", api_key),
        )
        self.channel = None

    def connect(self):
        """
        Connect the agent service
        """
        if self.channel:
            return

        channel = aio.insecure_channel(self.endpoint)
        self.channel = channel
        self.stub = AgentServerStub(channel)

    async def ping(self):
        request = agent_server_pb2.PingRequest()
        response = await self.stub.ping(request, metadata=self.metadata)
        return response

    async def assemble(self, name, code, language, desc="", saved_filenames=[]):
        request = agent_server_pb2.AssembleAppRequest(
            name=name,
            language=language,
            code=code,
            saved_filenames=saved_filenames,
            desc=desc,
        )
        response = await self.stub.assemble(request, metadata=self.metadata)
        return response

    async def run(self, name):
        # TODO support input files
        request = agent_server_pb2.RunAppRequest(name=name)
        async for respond in self.stub.run(request, metadata=self.metadata):
            yield respond

    async def query_apps(self):
        """query all apps"""
        request = agent_server_pb2.QueryAppsRequest()
        return await self.stub.query_apps(request, metadata=self.metadata)

    async def add_kernel(self, key, endpoint):
        """
        add kernel instance to the agent and only admin can call this method
        """
        request = agent_server_pb2.AddKernelRequest(endpoint=endpoint, key=key)
        response = await self.stub.add_kernel(request, metadata=self.metadata)
        return response

    async def prompt(self, prompt, files=[]):
        """
        ask the ai with prompt and  uploaded files
        """
        request = agent_server_pb2.SendTaskRequest(task=prompt, input_files=files)
        async for respond in self.stub.send_task(request, metadata=self.metadata):
            yield respond

    async def download_file(self, filename, parent_path):
        request = common_pb2.DownloadRequest(filename=filename)
        fullpath = "%s/%s" % (parent_path, filename)
        async with aiofiles.open(fullpath, "wb+") as afd:
            async for chunk in self.stub.download(request, metadata=self.metadata):
                await afd.write(chunk.buffer)

    async def upload_binary(self, chunks: AsyncIterable[common_pb2.FileChunk]):
        try:
            return await self.stub.upload(chunks, metadata=self.metadata)
        except Exception as ex:
            logger.error("upload file ex %s", ex)

    async def upload_file(self, filepath, filename):
        """
        upload file to agent
        """
        # TODO limit the file size
        return await self.upload_binary(generate_async_chunk(filepath, filename))

    def close(self):
        if self.channel:
            self.channel.close()
            self.channel = None
