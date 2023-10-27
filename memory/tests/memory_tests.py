# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

"""

"""
from og_memory.memory import agent_memory_to_context
from og_proto.memory_pb2 import AgentMemory, ChatMessage, GuideMemory, Feedback
from og_proto.prompt_pb2 import AgentPrompt, ActionDesc
# defina a logger variable
import logging
logger = logging.getLogger(__name__)

def test_agent_memory_to_context_smoke_test():
    """
    test the gent_memory_to_contex for smoke test
    """
    action = ActionDesc(name="execute_python_code", desc="run python code")   
    rules = ["To complete the goal, write a plan and execute it step-by-step, limiting the number of steps to five. the following are examples"]
    prompt = AgentPrompt(actions=[action], rules=rules, 
                         role="You are the QA engineer",
                         role_name="Kitty", output_format="")
    agent_memory = AgentMemory(instruction=prompt, user_id = "1", user_name="tai", guide_memory=[], chat_memory=[],
                memory_id="2")
    context = agent_memory_to_context(agent_memory)
    logger.info(context)
