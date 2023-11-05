# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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


class AgentSyncSession:

    def __init__(self, agent_sdk):
        self.context_id = None
        self.agent_sdk = agent_sdk

    def prompt(self, prompt, files=[]):
        """
        ask the ai with prompt and  uploaded files
        """
        for respond in self.agent_sdk.prompt(prompt, files, self.context_id):
            if respond.context_id:
                self.context_id = respond.context_id
            yield respond

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context_id = None


class AgentAsyncSession:

    def __init__(self, agent_sdk):
        self.context_id = None
        self.agent_sdk = agent_sdk

    async def prompt(self, prompt, files=[]):
        """
        ask the ai with prompt and  uploaded files
        """
        async for respond in self.agent_sdk.prompt(prompt, files, self.context_id):
            if respond.context_id:
                self.context_id = respond.context_id
            yield respond

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context_id = None


class AgentBaseSDK:

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.stub = None
        self.channel = None

    def connect_sync(self):
        """
        Connect the agent service with sync mode
        """
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

    def connect_async(self):
        """
        Connect the agent service with async mode
        """
        if self.channel:
            return
        if self.endpoint.startswith("https"):
            channel_credential = grpc.ssl_channel_credentials()
            self.channel = aio.secure_channel(
                self.endpoint.replace("https://", ""), channel_credential
            )
        else:
            self.channel = aio.insecure_channel(self.endpoint)
        self.stub = AgentServerStub(self.channel)


class AgentSyncSDK(AgentBaseSDK):

    def __init__(self, endpoint, api_key):
        super().__init__(endpoint)
        self.metadata = aio.Metadata(
            ("api_key", api_key),
        )

    def connect(self):
        self.connect_sync()

    def create_session(self):
        """
        create a session for the agent
        """
        return AgentSyncSession(self)

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

    def prompt(self, prompt, files=[], context_id=None):
        """
        ask the ai with prompt and  uploaded files
        """
        request = agent_server_pb2.ProcessTaskRequest(
            task=prompt, input_files=files, context_id=context_id
        )
        for respond in self.stub.process_task(request, metadata=self.metadata):
            yield respond

    def close(self):
        if self.channel:
            self.channel.close()
            self.channel = None


class AgentProxySDK(AgentBaseSDK):

    def __init__(self, endpoint):
        super().__init__(endpoint)
        self.endpoint = endpoint

    def connect(self):
        self.connect_async()

    async def add_kernel(self, key, endpoint, api_key):
        """
        add kernel instance to the agent and only admin can call this method
        """
        metadata = aio.Metadata(
            ("api_key", api_key),
        )
        request = agent_server_pb2.AddKernelRequest(endpoint=endpoint, key=key)
        response = await self.stub.add_kernel(request, metadata=metadata)
        return response

    async def prompt(self, prompt, api_key, files=[], context_id=None):
        metadata = aio.Metadata(
            ("api_key", api_key),
        )
        request = agent_server_pb2.ProcessTaskRequest(task=prompt, input_files=files, context_id=context_id)
        async for respond in self.stub.process_task(request, metadata=metadata):
            yield respond

    async def close(self):
        if self.channel:
            await self.channel.close()
            self.channel = None


class AgentSDK(AgentBaseSDK):

    def __init__(self, endpoint, api_key):
        super().__init__(endpoint)
        self.metadata = aio.Metadata(
            ("api_key", api_key),
        )

    def connect(self):
        self.connect_async()

    async def ping(self):
        request = agent_server_pb2.PingRequest()
        response = await self.stub.ping(request, metadata=self.metadata)
        return response

    async def add_kernel(self, key, endpoint):
        """
        add kernel instance to the agent and only admin can call this method
        """
        request = agent_server_pb2.AddKernelRequest(endpoint=endpoint, key=key)
        response = await self.stub.add_kernel(request, metadata=self.metadata)
        return response

    def create_session(self):
        """
        create a session for the agent
        """
        return AgentAsyncSession(self)

    async def prompt(self, prompt, files=[], context_id=None):
        """
        ask the ai with prompt and  uploaded files
        """
        request = agent_server_pb2.ProcessTaskRequest(
            task=prompt, input_files=files, context_id=context_id
        )
        async for respond in self.stub.process_task(request, metadata=self.metadata):
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

    async def close(self):
        if self.channel:
            await self.channel.close()
            self.channel = None
