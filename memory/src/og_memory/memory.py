# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

"""

"""


# import the agent memory
from og_proto.memory_pb2 import AgentMemory
from jinja2 import Environment
from jinja2.loaders import PackageLoader

env = Environment(loader=PackageLoader("og_memory", "template"))
context_tpl = env.get_template("agent.jinja")

def agent_memory_to_context(memory: AgentMemory):
    """
    Convert the agent memory to context
    :param memory : AgentMemory
    :return: string context for llm
    """
    return context_tpl.render(prompt=memory.instruction, guides=memory.guide_memory)



