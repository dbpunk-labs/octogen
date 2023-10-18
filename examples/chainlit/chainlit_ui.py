# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import json
import chainlit as cl
import aiohttp
from chainlit.input_widget import TextInput
from og_sdk.utils import process_char_stream


@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings([
        TextInput(
            id="Endpoint", label="Octogen Endpoint", initial="http://127.0.0.1:9529"
        ),
        TextInput(id="API_KEY", label="Octogen KEY", initial=""),
    ]).send()
    await setup_agent(settings)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("Endpoint", settings["Endpoint"])
    cl.user_session.set("Key", settings["API_KEY"])


@cl.on_message
async def main(message):
    last_msg = cl.Message(
        content="",
        author="Octogen",
    )
    request = {
        "prompt": message,
        "token_limit": 0,
        "llm_model_name": "string",
        "input_files": [],
        "context_id": "string",
    }
    headers = {"api-token": cl.user_session.get("Key")}
    last_type = None
    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.post(
            cl.user_session.get("Endpoint") + "/process", json=request
        ) as r:
            async for line in r.content:
                if line:
                    text = str(line, encoding="utf-8")
                    response = json.loads(text)
                    if response["step_type"] == "OnStepTextTyping":
                        if last_type and last_type != "OnStepTextTyping":
                            if last_msg:
                                await last_msg.send()
                            new_msg = cl.Message(author="Octogen", content="")
                            last_msg = new_msg
                        await last_msg.stream_token(response["typing_content"])
                        last_type = "OnStepTextTyping"
                    elif response["step_type"] == "OnStepCodeTyping":
                        if last_type != "OnStepCodeTypeing":
                            await last_msg.send()
                            new_msg = cl.Message(
                                author="Octogen", language="text", content=""
                            )
                            last_msg = new_msg
                        await last_msg.stream_token(response["typing_content"])
                        last_type = "OnStepCodeTypeing"
                    elif response["step_type"] == "OnStepActionStart":
                        parent_id = last_msg.parent_id
                        await last_msg.remove()
                        tool = response["step_action_start"]["tool"]
                        if tool in ["execute_python_code", "show_sample_code"]:
                            tool_input = json.loads(
                                response["step_action_start"]["input"]
                            )
                            new_msg = cl.Message(
                                author="Octogen",
                                language=tool_input.get("language", "text"),
                                content="",
                            )
                            last_msg = new_msg
                            await last_msg.stream_token(tool_input["code"])
                        last_type = "OnStepActionStart"
                    elif response["step_type"] == "OnStepActionStdout":
                        if last_type not in [
                            "OnStepActionStdout",
                            "OnStepActionStderr",
                        ]:
                            await last_msg.send()
                            new_msg = cl.Message(
                                author="Octogen",
                                language="text",
                                content="",
                            )
                            last_msg = new_msg
                        last_type = "OnStepActionStdout"
                        temp_content = last_msg.content + response["step_action_stdout"]
                        new_content = process_char_stream(temp_content)
                        last_msg.content = new_content
                        await last_msg.update()
                    elif response["step_type"] == "OnStepActionStderr":
                        if last_type not in [
                            "OnStepActionStdout",
                            "OnStepActionStderr",
                        ]:
                            await last_msg.send()
                            new_msg = cl.Message(
                                author="Octogen", language="text", content=""
                            )
                            last_msg = new_msg
                        last_type = "OnStepActionStderr"
                        temp_content = last_msg.content + response["step_action_stderr"]
                        new_content = process_char_stream(temp_content)
                        last_msg.content = new_content
                        await last_msg.update()
                    elif response["step_type"] == "OnStepActionEnd":
                        await last_msg.send()
                        last_msg = None
                        last_type = "OnStepActionEnd"
                    elif response["step_type"] == "OnFinalAnswer":
                        await last_msg.send()
                        last_msg = None
                        last_type = "OnFinalAnswer"
