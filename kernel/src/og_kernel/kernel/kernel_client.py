# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

import os
import logging
import inspect
import asyncio
import queue
import json
from jupyter_client import AsyncKernelClient

logger = logging.getLogger(__name__)

"""
the kernel client for watching the output of kernel
"""


class KernelClient:

    def __init__(self, connection_file):
        if not connection_file:
            raise ValueError(f"connection_file={connection_file} is empty")
        if not os.path.exists(connection_file):
            raise ValueError(f"connection_file={connection_file} do not exist")
        logger.info(
            "create a new kernel client with connection_file %s", connection_file
        )
        self.client = None
        self.is_running = False
        self.task = None
        self.connection_file = connection_file

    async def is_alive(self):
        return await self.client.is_alive()

    async def start_client(self):
        self.client = AsyncKernelClient(connection_file=self.connection_file)
        self.client.load_connection_file()
        self.client.start_channels()
        await self.client.wait_for_ready()

    async def _loop(self, on_message_fn):
        logger.debug("start loop the kernel message")
        try:
            while self.is_running and self.client:
                try:
                    logger.debug("start wait message")
                    msg = await self.client.get_iopub_msg(timeout=1)
                    logger.debug("msg %s", msg)
                    try:
                        await on_message_fn(msg)
                    except Exception as e:
                        logger.error("fail to call on message function for error %s", e)
                        continue
                except queue.Empty:
                    logger.debug("empty message")
                    continue
                except (ValueError, IndexError):
                    # get_iopub_msg suffers from message fetch errors
                    logger.error("fail to get message")
                    break
                except Exception as e:
                    logger.error("fail to wait for message %s", e)
                    break
        except Exception as e:
            logger.error("loop exception", e)

    async def watching(self, on_message_fn):
        """
        Watch the message from kernel, when a new message arrived , the `on_message_fn` will be
        called

        Arguments
        on_message_fn - when a new message arrived the function will be called
        """
        if self.is_running:
            raise ValueError(f"the watch is running, do not watch it again")
        if not on_message_fn or not self.client:
            raise ValueError(f"on_message_fn or clent is None")
        if not inspect.iscoroutinefunction(on_message_fn):
            raise ValueError(f"on_message_fn must be async function")
        self.is_running = True
        self.task = asyncio.create_task(self._loop(on_message_fn))

    async def read_response(self, context, tries=1):
        try:
            hit_empty = 0
            while self.client:
                try:
                    msg = await self.client.get_iopub_msg(timeout=1)
                    if context.done():
                        logger.debug("the client  has cancelled the request")
                        break
                    logger.debug(f"{msg}")
                    yield msg
                except queue.Empty:
                    hit_empty += 1
                    if hit_empty >= tries:
                        break
                except (ValueError, IndexError):
                    # get_iopub_msg suffers from message fetch errors
                    logger.error("fail to get message")
                    break
                except Exception as e:
                    logger.error("fail to wait for message %s", e)
                    break
            yield None
        except Exception as e:
            logger.error("loop exception", e)
            yield None

    def execute(self, code):
        """
        Execute the python code
        """
        if not self.client:
            raise ValueError(f"no client is avaliable")
        msg_id = self.client.execute(code)
        logger.debug("the execute msg id %s", msg_id)
        return msg_id

    async def stop_watch(self):
        if self.task and self.is_running:
            self.is_running = False
            logger.info(
                "stop the kernel client for connection_file %s", self.connection_file
            )
            try:
                self.task.cancel()
                await self.task
            except:
                pass

    def stop_client(self):
        if self.client:
            self.client.stop_channels()
            self.client = None
