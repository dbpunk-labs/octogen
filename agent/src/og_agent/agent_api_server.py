# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

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

logger = logging.getLogger(__name__)

# the agent config
config = dotenv_values(".env")

app = FastAPI()
# the agent endpoint
listen_addr = "%s:%s" % (config["rpc_host"], config["rpc_port"])
if config["rpc_host"] == "0.0.0.0":
    listen_addr = "127.0.0.1:%s" % config["rpc_port"]

logger.info(f"connect the agent server at {listen_addr}")
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
    generated_token_count: int
    iteration_count: int
    llm_model_name: str
    total_duration: int
    sent_token_count: int
    llm_model_response_duration: int
    context_id: str | None = None

    @classmethod
    def new_from(cls, state):
        return cls(
            generated_token_count=state.generated_token_count,
            iteration_count=state.iteration_count,
            llm_model_name=state.model_name,
            total_duration=state.total_duration,
            sent_token_count=state.sent_token_count,
            llm_model_response_duration=state.model_respond_duration,
        )


class StepActionEnd(BaseModel):
    output: str
    output_files: List[str]
    has_error: bool

    @classmethod
    def new_from(cls, step_action_end: agent_server_pb2.OnAgentActionEnd):
        return cls(
            output=step_action_end.output,
            output_files=step_action_end.output_files,
            has_error=step_action_end.has_error,
        )


class FinalAnswer(BaseModel):
    answer: str

    @classmethod
    def new_from(cls, final_answer: agent_server_pb2.FinalRespond):
        return cls(answer=final_answer.answer)


class StepActionStart(BaseModel):
    input: str
    tool: str

    @classmethod
    def new_from(cls, step_action_start: agent_server_pb2.OnAgentAction):
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
    def new_from(cls, response: agent_server_pb2.TaskRespond):
        if response.respond_type == agent_server_pb2.TaskRespond.OnAgentActionType:
            return cls(
                step_type=StepResponseType.OnStepActionStart,
                step_state=ContextState.new_from(response.state),
                step_action_start=StepActionStart.new_from(response.on_agent_action),
            )
        elif response.respond_type == agent_server_pb2.TaskRespond.OnAgentCodeTyping:
            return cls(
                step_type=StepResponseType.OnStepCodeTyping,
                step_state=ContextState.new_from(response.state),
                typing_content=response.typing_content,
            )

        elif response.respond_type == agent_server_pb2.TaskRespond.OnAgentTextTyping:
            return cls(
                step_type=StepResponseType.OnStepTextTyping,
                step_state=ContextState.new_from(response.state),
                typing_content=response.typing_content,
            )
        elif response.respond_type == agent_server_pb2.TaskRespond.OnAgentActionStdout:
            return cls(
                step_type=StepResponseType.OnStepActionStdout,
                step_state=ContextState.new_from(response.state),
                step_action_stdout=response.console_stdout,
            )
        elif response.respond_type == agent_server_pb2.TaskRespond.OnAgentActionStderr:
            return cls(
                step_type=StepResponseType.OnStepActionStdout,
                step_state=ContextState.new_from(response.state),
                step_action_stdout=response.console_stderr,
            )
        elif response.respond_type == agent_server_pb2.TaskRespond.OnAgentActionEndType:
            return cls(
                step_type=StepResponseType.OnStepActionEnd,
                step_state=ContextState.new_from(response.state),
                step_action_end=StepActionEnd.new_from(response.on_agent_action_end),
            )
        elif response.respond_type == agent_server_pb2.TaskRespond.OnFinalAnswerType:
            return cls(
                step_type=StepResponseType.OnFinalAnswer,
                step_state=ContextState.new_from(response.state),
                final_answer=FinalAnswer.new_from(response.final_respond),
            )


class TaskRequest(BaseModel):
    prompt: str
    token_limit: int
    llm_model_name: str
    input_files: List[str]
    context_id: str

async def run_task(task: TaskRequest, key):
    index = 0
    async for respond in agent_sdk.prompt(task.prompt, key, files=task.input_files):
        response = StepResponse.new_from(respond).model_dump(exclude_none=True)
        yield "\n" + json.dumps(response) if index > 0 else json.dumps(response)
        index += 1


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
    response.media_type = "application/json"
    agent_sdk.connect()
    return StreamingResponse(run_task(task, api_token))

async def run_server():
    port = int(config["rpc_port"]) + 1
    server_config = uvicorn.Config(app, host=config["rpc_host"], port=port)
    server = uvicorn.Server(server_config)
    await server.serve()

def run_app():
    asyncio.run(run_server())
