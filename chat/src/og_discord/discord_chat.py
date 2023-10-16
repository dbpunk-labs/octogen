# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import discord
import asyncio
import logging
import json
import sys
import os
import click
from datetime import datetime
from dotenv import dotenv_values
from og_proto import common_pb2
from og_sdk.agent_sdk import AgentSDK

LOG_LEVEL = logging.INFO
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class OctogenDiscordBot(discord.Client):

    def __init__(self, octogen_sdk, filedir, **kwargs):
        discord.Client.__init__(self, **kwargs)
        self.octogen_sdk = octogen_sdk
        self.filedir = filedir

    def handle_action_start(self, respond, saved_images):
        """Run on agent action."""
        segments = []
        if not respond.on_agent_action:
            return segments
        action = respond.on_agent_action
        if not action.input:
            return segments
        logger.info("handle action start return")
        arguments = json.loads(action.input)
        if action.tool == "execute_python_code" and action.input:
            explanation = arguments["explanation"]
            code = arguments["code"]
            saved_images.extend(arguments.get("saved_filenames", []))
            mk = f"""{explanation}\n
```python
{code}
```"""
            segments.append(mk)
        return segments

    def handle_final_answer(self, respond):
        segments = []
        if not respond.final_respond:
            return segments
        answer = respond.final_respond.answer
        if not answer:
            return segments
        state = "token:%s iteration:%s model:%s" % (
            respond.token_usage,
            respond.iteration,
            respond.model_name,
        )
        segments.append("%s\n%s" % (answer, state))
        return segments

    def handle_action_output(self, respond, saved_images):
        segments = []
        if not respond.on_agent_action_end:
            return segments
        mk = respond.on_agent_action_end.output
        if not mk:
            return segments
        saved_images.extend(respond.on_agent_action_end.output_files)
        segments.append(mk)
        return segments

    async def download_files(self, images):
        for image in images:
            await self.octogen_sdk.download_file(image, self.filedir)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def run_app(self, name, message):
        saved_images = []
        async for respond in self.octogen_sdk.run(name):
            if not respond:
                break
            if respond.on_agent_action_end:
                segments = self.handle_action_output(respond, saved_images)
                msg = "".join(segments)
                if msg:
                    await message.channel.send(msg)
            if respond.on_agent_action:
                segments = self.handle_action_start(respond, saved_images)
                msg = "".join(segments)
                if msg:
                    await message.channel.send(msg)
        saved_images = list(set(saved_images))
        if saved_images:
            await self.download_files(saved_images)
            for filename in saved_images:
                fullpath = "%s/%s" % (self.filedir, filename)
                await message.channel.send("", file=discord.File(fullpath))
                break

    async def show_apps(self):
        header = """Apps
"""
        rows = []
        apps = await self.octogen_sdk.query_apps()
        for index, app in enumerate(apps.apps):
            ctime = datetime.fromtimestamp(app.ctime).strftime("%m/%d/%Y")
            rows.append(f"{index+1}.{app.name}")
        table = header + "\n".join(rows)
        return table

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        try:
            if message.author.id == self.user.id:
                return
            if message.content.find("/apps") >= 0:
                apps = await self.show_apps()
                await message.channel.send(apps)
                return
            content = message.content
            if content.find("/run") >= 0:
                name = content.split(" ")[1]
                await self.run_app(name, message)
                return
            await message.channel.send("working...")
            files = []
            for att in message.attachments:

                async def generate_chunk(att):
                    # TODO split
                    chunk = await att.read()
                    yield common_pb2.FileChunk(buffer=chunk, filename=att.filename)

                await sdk.upload_binary(generate_chunk(att), att.filename)
                files.append("uploaded " + att.filename)
            if files:
                prompt = message.content + "\n" + "\n".join(files)
            else:
                prompt = message.content
            try:
                async for respond in self.octogen_sdk.prompt(prompt):
                    if not respond:
                        break
                    logger.info(f"{respond}")
                    if respond.on_agent_action_end:
                        saved_images = []
                        segments = self.handle_action_output(respond, saved_images)
                        msg = "".join(segments)
                        logger.info(f"action output {msg}")
                        if msg:
                            if saved_images:
                                await self.download_files(saved_images)
                                for filename in saved_images:
                                    fullpath = "%s/%s" % (self.filedir, filename)
                                    await message.channel.send(
                                        msg, file=discord.File(fullpath)
                                    )
                                    break
                            else:
                                await message.channel.send(msg)
                    if respond.on_agent_action:
                        saved_images = []
                        segments = self.handle_action_start(respond, saved_images)
                        msg = "".join(segments)
                        logger.info(f"action start {msg}")
                        if msg:
                            await message.channel.send(msg)
                    if respond.final_respond:
                        segments = self.handle_final_answer(respond)
                        msg = "".join(segments)
                        logger.info(f"final answer {msg}")
                        if msg:
                            await message.channel.send(msg)
            except Exception as ex:
                logger.error(f"fail to get file {ex}")
                await message.channel.send("I am sorry for the internal error")
        except Exception as ex:
            logging.exception(ex)


async def app():
    octogen_discord_bot_dir = "~/.octogen_discord_bot"
    if octogen_discord_bot_dir.find("~") == 0:
        real_octogen_dir = octogen_discord_bot_dir.replace("~", os.path.expanduser("~"))
    else:
        real_octogen_dir = octogen_discord_bot_dir
    if not os.path.exists(real_octogen_dir):
        os.mkdir(real_octogen_dir)
    octogen_config = dotenv_values(real_octogen_dir + "/config")
    filedir = real_octogen_dir + "/data"
    if not os.path.exists(filedir):
        os.mkdir(filedir)
    sdk = AgentSDK(octogen_config["endpoint"], octogen_config["api_key"])
    sdk.connect()
    intents = discord.Intents.default()
    intents.message_content = True
    client = OctogenDiscordBot(sdk, filedir, intents=intents)
    await client.start(octogen_config["discord_bot_token"])


def run_app():
    asyncio.run(app())
