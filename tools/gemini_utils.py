import logging
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langfuse.decorators import langfuse_context, observe

from constants import MODEL
from schemas.context_agent_schema import (RoutingAgentContext, TaskContent,
                                          TaskContext, Agents)

load_dotenv()
client = genai.Client()

# --- NEW: load shared.toml/integration_config ---
CONFIG_PATH = Path(__file__).parent.parent / "config" / "shared.toml"
try:
    with open(CONFIG_PATH, "rb") as f:
        _SHARED = tomllib.load(f)
except FileNotFoundError:
    _SHARED = {}
INTEGRATION_CONFIG = _SHARED.get("integration_config", {})
logging.info(f"Loaded integration_config: {INTEGRATION_CONFIG}")


@observe(as_type="generation")
def generate_genric_task_context(
    task_content_input: TaskContent, session_id: str
) -> TaskContext:
    """
    Summarize the task context into a string
    Args:
        task_context (str): the context of the requestor
    Returns:
        str: the summarized context
    """
    task_content_dict = task_content_input.model_dump()
    prompt = INTEGRATION_CONFIG.get("task_context").get("prompt", "")
    context_agent_prompt = prompt.format(
        task_content_dict=task_content_dict,
    )

    resp = client.models.generate_content(
        model=MODEL,
        contents=context_agent_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": TaskContext,
            "thinking_config": types.ThinkingConfig(
                thinking_budget=0,
            ),
        },
    )
    logging.debug(
        f"langyuse debug: input_tokens: {resp.usage_metadata.prompt_token_count}, output_tokens: {resp.usage_metadata.candidates_token_count}, total_tokens: {resp.usage_metadata.total_token_count}"
    )
    langfuse_context.update_current_observation(
        input=context_agent_prompt,
        model=MODEL,
        session_id=session_id,
        name="generate_genric_task_context",
        usage={
            "input": resp.usage_metadata.prompt_token_count,
            "output": resp.usage_metadata.candidates_token_count,
            "total_tokens": resp.usage_metadata.total_token_count,
        },
    )
    return resp.parsed


@observe(as_type="generation")
def generate_routing_agent_context(
    task_content: TaskContent, task_context: TaskContext, session_id: str
) -> RoutingAgentContext:
    """
    Determine which agent should handle the task based on the task context.
    """
    src = task_content.email_content.integration_source
    cfg = INTEGRATION_CONFIG.get(src)
    
    if not cfg:
        return RoutingAgentContext(
            target_agent=Agents.UNSUPPORTED, agent_tags=[], priority="low"
        )

    logging.info(f"Routing agent | integration config: {cfg}")

    DEFAULT_ROUTING_FIXED_PROMPT = """
    You are a Task Priority Agent. Your goal is to assign a priority to a task based on its context.

    **Input Context:**
    * You will receive task details in a structured format (derived from {task_context}).
    * The task is intended for agent: {target}.

    **Priority Levels:** `very_high`, `high`, `medium`, `low`

    **Rules (in order):**
    1. If purely informational with no enquiry asked → `low`
    2. Senior management involved → `high` (or `very_high` if explicitly urgent)
    3. Otherwise → `medium` (or `low` if minor)"""

    DEFAULT_ROUTING_INFER_PROMPT = """
    You are a Task Priority Agent. Your goal is to assign a priority to a task based on its context.

    **Input Context:**
    * You will receive task details in a structured format:
    {task_context}

    **Rules (in order):**
    1. If purely informational with no enquiry asked → `low`
    2. Senior management involved → `high` (or `very_high` if explicitly urgent)
    3. Otherwise → `medium` (or `low` if minor)
    4. Base on the task context, determine the target agent for the task from the agents avaliable in the output schema.
    """

    # build the prompt based on mode
    if cfg.get("mode") == "fixed":
        prompt = cfg.get("prompt", DEFAULT_ROUTING_FIXED_PROMPT)
        prompt = prompt.format(
            task_context=task_context.model_dump(), target=cfg["agent"]
        )
    else:
        prompt_template = cfg.get("prompt", DEFAULT_ROUTING_INFER_PROMPT)
        prompt = prompt_template.format(
            task_context=task_context.model_dump(),
        )

    # single generate_content call
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": RoutingAgentContext,
            "thinking_config": types.ThinkingConfig(thinking_budget=0),
        },
    )

    # record usage
    langfuse_context.update_current_observation(
        input=prompt,
        model=MODEL,
        session_id=session_id,
        name="routing_agent_context",
        usage={
            "input": resp.usage_metadata.prompt_token_count,
            "output": resp.usage_metadata.candidates_token_count,
            "total_tokens": resp.usage_metadata.total_token_count,
        },
    )
    return resp.parsed
