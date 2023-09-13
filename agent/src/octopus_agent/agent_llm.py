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

import logging
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.llms.fake import FakeListLLM

logger = logging.getLogger(__name__)


class LLMManager:

    def __init__(self, config):
        """
        llm_key=xxxx
        # the other optional
        """
        self.config = config
        self.llms = {}
        self.llm_key = self.config["llm_key"]
        if self.config["llm_key"] == "azure_openai":
            self._build_azure_openai()
        elif self.config["llm_key"] == "openai":
            self._build_openai()
        elif self.config["llm_key"] == "mock":
            self._build_mock_llm()

    def get_llm(self):
        return self.llms.get(self.llm_key, None)

    def get_llm_by_key(self, llm_key):
        """
        get llm with a key, the supported keys are 'mock', 'openai', 'azure_openai', 'codellama'
        """
        return self.llms.get(self.llm_key, None)

    def _no_empty_value_required(self, keys):
        for key in keys:
            if not self.config.get(key, None):
                raise Exception(f"the value of required {key} is empty")

    def _build_openai(self):
        self._no_empty_value_required([
            "openai_api_key",
            "openai_api_model",
        ])
        api_base = self.config.get("openai_api_base", None)
        api_key = self.config["openai_api_key"]
        api_model = self.config["openai_api_model"]
        temperature = self.config.get("temperature", 0)
        llm = ChatOpenAI(
            openai_api_base=api_base,
            openai_api_key=api_key,
            model_name=api_model,
            temperature=temperature,
        )
        self.llms[self.llm_key] = llm

    def _build_azure_openai(self):
        """
        build azure openai client from config
        """
        self._no_empty_value_required([
            "openai_api_base",
            "openai_api_version",
            "openai_api_key",
            "openai_api_type",
            "openai_api_deployment",
        ])
        api_base = self.config["openai_api_base"]
        api_version = self.config["openai_api_version"]
        api_type = self.config["openai_api_type"]
        api_key = self.config["openai_api_key"]
        api_deployment = self.config["openai_api_deployment"]
        temperature = self.config.get("temperature", 0)
        verbose = self.config.get("verbose", False)
        llm = AzureChatOpenAI(
            openai_api_base=api_base,
            openai_api_version=api_version,
            openai_api_key=api_key,
            openai_api_type=api_type,
            deployment_name=api_deployment,
            temperature=temperature,
            verbose=verbose,
        )
        self.llms[self.llm_key] = llm

    def _build_mock_llm(self):
        """
        build a mock llm
        """
        # the response to "how to get metadata from python grpc request"
        # TODO config the response
        responses = [
            """Final Answer: To get metadata from a Python gRPC request context, you can access the `context.invocation_metadata()` method. This method returns a list of key-value pairs representing the metadata associated with the request.

Here's an example of how you can retrieve metadata from a gRPC request context:

```python
def my_grpc_method(request, context):
    # Get the metadata from the request context
    metadata = dict(context.invocation_metadata())

    # Access specific metadata values
    value = metadata.get('key')

    # Print the metadata
    print(metadata)
```

In this example, `context.invocation_metadata()` returns a list of tuples representing the metadata. By converting it to a dictionary using `dict()`, you can easily access specific metadata values using their keys.

Note that the `context` parameter in the example represents the gRPC request context object passed to the gRPC method."""
        ]
        llm = FakeListLLM(responses=responses)
        self.llms["mock"] = llm
