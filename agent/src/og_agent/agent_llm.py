# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """

import logging
import openai

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
        if self.config.get("openai_api_base", None):
            openai.api_base = self.config.get("openai_api_base", None)
        openai.api_key = self.config["openai_api_key"]

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
        openai.api_base = self.config["openai_api_base"]
        openai.api_version = self.config["openai_api_version"]
        openai.api_type = self.config["openai_api_type"]
        openai.api_key = self.config["openai_api_key"]
        self.config["openai_api_model"] = self.config["openai_api_deployment"]
