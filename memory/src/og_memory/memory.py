# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

"""

"""
import json
import logging
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from og_proto.memory_pb2 import AgentMemory as AgentMemoryProto
from jinja2 import Environment
from jinja2.loaders import PackageLoader
import tiktoken
logger = logging.getLogger(__name__)

env = Environment(loader=PackageLoader("og_memory", "template"))
env.filters['from_json'] = lambda s: json.loads(s)
context_tpl = env.get_template("agent.jinja")
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def agent_memory_to_context(instruction, guide_memory, options):
    """
    Convert the agent memory to context
    :param instruction: the instruction
    :param guide_memory: the guide memory
    :return: string context for llm
    """
    return context_tpl.render(prompt=instruction, guides=guide_memory, options=options)

class BaseAgentMemory(ABC):
    """
    Base class for agent memory
    """
    @abstractmethod
    def append_chat_message(self, message):
        """
        Append chat message to the memory
        """
        pass

    @abstractmethod
    def append_guide(self, guide):
        """
        Append guide to the memory
        """
        pass

    @abstractmethod
    def update_options(self, options):
        """
        Update the options
        """
        pass

    @abstractmethod
    def swap_instruction(self, instruction):
        """
        Swap the instruction
        """
        pass

    @abstractmethod
    def to_messages(self):
        """
        Convert the memory to messages
        """
        pass

    @abstractmethod
    def reset_memory(self):
        """
        Reset the memory
        """
        pass

    @abstractmethod
    def get_functions(self):
        """
        return the function definitions for model that supports the function_call
        """
        pass


class AgentMemoryOption(BaseModel):
    """
    The agent memory option
    """
    show_function_instruction: bool = Field(False, description="Show the function instruction")
    disable_output_format: bool = Field(False, description="Disable the output format")

class MemoryAgentMemory(BaseAgentMemory):
    """
    The agent memory based on memory
    """
    def __init__(self, memory_id, user_name, user_id):
        self.memory_id = memory_id
        self.user_name = user_name
        self.user_id = user_id
        self.guide_memory = []
        self.chat_memory = []
        self.instruction = None
        self.options = AgentMemoryOption(show_function_instruction=True)

    def update_options(self, options):
        self.options = options

    def reset_memory(self):
        self.guide_memory = []
        self.chat_memory = []

    def append_guide(self, guide):
        self.guide_memory.append(guide)

    def append_chat_message(self, message):
        self.chat_memory.append(message)

    def swap_instruction(self, instruction):
        self.instruction = instruction

    def get_functions(self):
        return [{"name": action.name, "description": action.desc, "parameters":
          json.loads(action.parameters)} for action in self.instruction.actions]

    def to_messages(self):
        system_message = {
          "role":"system",
          "content":agent_memory_to_context(self.instruction, self.guide_memory, options = self.options)
        }
        logging.debug(f"system message: {system_message}")
        return [system_message] + self.chat_memory


