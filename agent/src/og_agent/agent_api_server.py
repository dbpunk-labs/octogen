# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import sys
import asyncio
import uvicorn
import json
import logging
from typing import List
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI, status, Response
from og_sdk.agent_sdk import AgentProxySDK
from og_proto import agent_server_pb2
from fastapi.responses import StreamingResponse
from fastapi.param_functions import Header, Annotated
from dotenv import dotenv_values

# the api server config
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

app = FastAPI()
# the agent endpoint
listen_addr = "%s:%s" % (
    config.get("rpc_host", "127.0.0.1"),
    config.get("rpc_port", "9528"),
)
if config.get("rpc_host", "") == "0.0.0.0":
    listen_addr = "127.0.0.1:%s" % config.get("rpc_port", "9528")
agent_sdk = AgentProxySDK(listen_addr)


class StepResponseType(str, Enum):
    OnStepActionStart = "OnStepActionStart"
    OnStepTextTyping = "OnStepTextTyping"
    OnStepCodeTyping = "OnStepCodeTyping"
    OnStepActionStdout = "OnStepActionStdout"
    OnStepActionStderr = "OnStepActionStderr"
    OnStepActionEnd = "OnStepActionEnd"
    OnFinalAnswer = "OnFinalAnswer"


class ContextState(BaseModel):
    output_token_count: int
    llm_name: str
    total_duration: int
    output_token_count: int
    llm_response_duration: int
    context_id: str | None = None

    @classmethod
    def new_from(cls, state):
        return cls(
            output_token_count=state.output_token_count,
            llm_name=state.llm_name,
            total_duration=state.total_duration,
            input_token_count=state.input_token_count,
            llm_response_duration=state.llm_response_duration,
        )


class StepActionEnd(BaseModel):
    output: str
    output_files: List[str]
    has_error: bool

    @classmethod
    def new_from(cls, step_action_end: agent_server_pb2.OnStepActionEnd):
        return cls(
            output=step_action_end.output,
            output_files=step_action_end.output_files,
            has_error=step_action_end.has_error,
        )


class FinalAnswer(BaseModel):
    answer: str

    @classmethod
    def new_from(cls, final_answer: agent_server_pb2.FinalAnswer):
        return cls(answer=final_answer.answer)


class StepActionStart(BaseModel):
    input: str
    tool: str

    @classmethod
    def new_from(cls, step_action_start: agent_server_pb2.OnStepActionStart):
        return cls(input=step_action_start.input, tool=step_action_start.tool)


class StepResponse(BaseModel):
    step_type: StepResponseType
    step_state: ContextState
    typing_content: str | None = None
    step_action_stdout: str | None = None
    step_action_stderr: str | None = None
    step_action_start: StepActionStart | None = None
    step_action_end: StepActionEnd | None = None
    final_answer: FinalAnswer | None = None

    @classmethod
    def new_from(cls, response: agent_server_pb2.TaskResponse):
        if response.response_type == agent_server_pb2.TaskResponse.OnStepActionStart:
            return cls(
                step_type=StepResponseType.OnStepActionStart,
                step_state=ContextState.new_from(response.state),
                step_action_start=StepActionStart.new_from(
                    response.on_step_action_start
                ),
            )
        elif response.response_type == agent_server_pb2.TaskResponse.OnModelTypeCode:
            return cls(
                step_type=StepResponseType.OnStepCodeTyping,
                step_state=ContextState.new_from(response.state),
                typing_content=response.typing_content.content,
            )

        elif response.response_type == agent_server_pb2.TaskResponse.OnModelTypeText:
            return cls(
                step_type=StepResponseType.OnStepTextTyping,
                step_state=ContextState.new_from(response.state),
                typing_content=response.typing_content.content,
            )
        elif (
            response.response_type
            == agent_server_pb2.TaskResponse.OnStepActionStreamStdout
        ):
            return cls(
                step_type=StepResponseType.OnStepActionStdout,
                step_state=ContextState.new_from(response.state),
                step_action_stdout=response.console_stdout,
            )
        elif (
            response.response_type
            == agent_server_pb2.TaskResponse.OnStepActionStreamStderr
        ):
            return cls(
                step_type=StepResponseType.OnStepActionStderr,
                step_state=ContextState.new_from(response.state),
                step_action_stderr=response.console_stderr,
            )
        elif response.response_type == agent_server_pb2.TaskResponse.OnStepActionEnd:
            return cls(
                step_type=StepResponseType.OnStepActionEnd,
                step_state=ContextState.new_from(response.state),
                step_action_end=StepActionEnd.new_from(response.on_step_action_end),
            )
        elif response.response_type == agent_server_pb2.TaskResponse.OnFinalAnswer:
            return cls(
                step_type=StepResponseType.OnFinalAnswer,
                step_state=ContextState.new_from(response.state),
                final_answer=FinalAnswer.new_from(response.final_answer),
            )


class TaskRequest(BaseModel):
    prompt: str
    token_limit: int
    llm_model_name: str
    input_files: List[str]
    context_id: str


async def run_task(task: TaskRequest, key):
    async for respond in agent_sdk.prompt(task.prompt, key, files=task.input_files, context_id=task.context_id):
        response = StepResponse.new_from(respond).model_dump(exclude_none=True)
        yield "data: %s\n" % json.dumps(response)

@app.post("/process")
async def process_task(
    task: TaskRequest,
    response: Response,
    api_token: Annotated[str | None, Header()] = None,
):
    if api_token is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    response.status_code = status.HTTP_200_OK
    response.media_type = "text/event-stream"
    agent_sdk.connect()
    return StreamingResponse(run_task(task, api_token))


async def run_server():
    logger.info(f"connect the agent server at {listen_addr}")
    port = int(config.get("rpc_port", "9528")) + 1
    server_config = uvicorn.Config(
        app, host=config.get("rpc_host", "127.0.0.1"), port=port
    )
    server = uvicorn.Server(server_config)
    await server.serve()


def run_app():
    asyncio.run(run_server())
