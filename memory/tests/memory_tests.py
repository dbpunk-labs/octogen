# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

"""

"""
import json
from og_memory.memory import agent_memory_to_context, AgentMemoryOption
from og_proto.memory_pb2 import AgentMemory, ChatMessage, GuideMemory, Feedback
from og_proto.prompt_pb2 import AgentPrompt, ActionDesc
# defina a logger variable
import logging
logger = logging.getLogger(__name__)

def test_agent_memory_to_context_smoke_test():
    """
    test the gent_memory_to_contex for smoke test
    """

    action = ActionDesc(name="execute_python_code", desc="run python code", parameters=json.dumps({
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "the explanation about the bash code",
                },
                "code": {
                    "type": "string",
                    "description": "the bash code to be executed",
                },
                "language": {
                    "type": "string",
                    "description": "the language of the code",
                },
                "saved_filenames": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of filenames that were created by the code",
                },
            },
            "required": ["explanation", "code", "language"],
        }))   
    rules = ["To complete the goal, write a plan and execute it step-by-step, limiting the number of steps to five. the following are examples", "rule2"]
    prompt = AgentPrompt(actions=[action, action], rules=rules, 
                         role="You are the QA engineer",
                         role_name="Kitty", output_format="")
    context = agent_memory_to_context(prompt, [], AgentMemoryOption(show_function_instruction=True))
    expected_context="""You are the QA engineer
Follow the rules
1.To complete the goal, write a plan and execute it step-by-step, limiting the number of steps to five. the following are examples
2.rule2
Use the following actions to help you finishing your task

1.execute_python_code: run python code, the following are parameters
    explanation(string):the explanation about the bash code
    code(string):the bash code to be executed
    language(string):the language of the code
    saved_filenames(array):A list of filenames that were created by the code
    
2.execute_python_code: run python code, the following are parameters
    explanation(string):the explanation about the bash code
    code(string):the bash code to be executed
    language(string):the language of the code
    saved_filenames(array):A list of filenames that were created by the code
    """
    assert context == expected_context, "context is not expected"
