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

""" """
import asyncio
import json
import uuid
import base64
import logging
from typing import Any, Dict, List, Optional
from octopus_kernel.sdk.kernel_sdk import KernelSDK
from langchain.utils import get_from_dict_or_env

logger = logging.getLogger(__name__)


class OctopusAPIBase:
    """Wrap the Octopus Kernel API"""

    def __init__(self, sdk):
        self.sdk = sdk

    def run(self, code: str, **kwargs: Any) -> str:
        """Run python code

        Arguments:
        code  -- the python code to be executed
        """
        return asyncio.run(self.arun(code, **kwargs))

    async def arun(self, code: str, **kwargs: Any) -> str:
        """Run python code in async

        Arguments:
        code  -- the python code to be executed
        """
        kernel_name = (
            kwargs["kernel_name"]
            if "kernel_name" in kwargs and kwargs["kernel_name"]
            else "python3"
        )
        is_alive = await self.sdk.is_alive()
        if not is_alive:
            await self.sdk.start(kernel_name=kernel_name)
        messages = []
        response = await self.sdk.execute(code, kernel_name=kernel_name)
        # render the response to markdown
        output = self.render(response)
        return output

    def render(self, response, data_dir):
        raise NotImplementedError


class OctopusAPIMarkdownOutput(OctopusAPIBase):
    """Wrap the octopus kernel api with markdown output format

    You create the api key from octopus.dbpunk.com
    """

    def render(self, response):
        """
        reader the response to a markdown

        Args:
            response (object): The response object from the kernel client.

        Returns:
            str: The response data in Markdown format.
        """
        if response.traceback:
            return (
                "The code is `1` with the error\n```\n%s\n```"
                % json.loads(response.traceback)["data"]
            )

        output = ""
        if response.stdout:
            output = json.loads(response.stdout)["data"]
        if response.stderr:
            output += json.loads(response.stderr)["data"]
        if output:
            output = "The stdout/stderr \n```\n%s\n```" % output

        if response.result:
            result = json.loads(response.result)
            if result["msg_type"] == "execute_result":
                output = "The code is 0 and the result \n```\n%s\n``` \n %s" % (
                    result["data"]["text/plain"],
                    output,
                )
            elif result["msg_type"] == "display_data":
                if "image/png" in result["data"]:
                    filename = result["data"]["image/png"]
                    output = (
                        f"The code is 0 and the display data is saved to file `{filename}` \n%s"
                        % output
                    )
                elif "image/gif" in result["data"]:
                    filename = result["data"]["image/gif"]
                    output = (
                        f"The code is 0 and the display data is saved to file `{filename}` \n%s"
                        % output
                    )
                else:
                    keys = ",".join(result["data"].keys())
                    raise Exception(
                        f"unsupported display data type {keys} for the result"
                    )
            else:
                raise Exception(
                    f"unsupported messsage type {result['msg_type']} for the result"
                )
        return output


class OctopusAPIJsonOutput(OctopusAPIBase):
    """Wrap the octopus kernel api with json output format

    You create the api key from octopus.dbpunk.com
    """

    def render(self, response):
        """
        reader the response to a json

        Args:
            response (object): The response object from the kernel client.

        Returns:
            dict: The response data in JSON format.
        """
        output = {
            "code": 0,
            "result": None,
            "stdout": None,
            "stderr": None,
            "error": None,
        }
        if response.stdout:
            output["stdout"] = json.loads(response.stdout)["data"]
        if response.stderr:
            output["stderr"] = json.loads(response.stderr)["data"]
        if response.traceback:
            output["error"] = json.loads(response.traceback)["data"]
            output["code"] = 1
        if response.result:
            result = json.loads(response.result)
            if result["msg_type"] == "execute_result":
                output["result"] = result["data"]["text/plain"]
            elif result["msg_type"] == "display_data":
                if "image/png" in result["data"]:
                    filename = result["data"]["image/png"]
                    output[
                        "result"
                    ] = f"the image/png format data has been saved to file `{filename}`"
                elif "image/gif" in result["data"]:
                    filename = result["data"]["image/gif"]
                    output[
                        "result"
                    ] = f"the image/gif format data has been saved to file `{filename}`"
                else:
                    keys = ",".join(result["data"].keys())
                    raise Exception(
                        f"unsupported display data type {keys} for the result"
                    )
            else:
                raise Exception(
                    f"unsupported messsage type {result['msg_type']} for the result"
                )
        return output
