from google import genai
from dotenv import load_dotenv
from constants import MODEL
from pathlib import Path
import tomllib
from schemas.context_agent_schema import TaskContent, TaskContext, RoutingAgentContext
import logging

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
print(f"Loaded integration_config: {INTEGRATION_CONFIG}")


def generate_genric_task_context(task_context_input: TaskContent) -> TaskContext:
    """
    Summarize the task context into a string
    Args:
        task_context (str): the context of the requestor
    Returns:
        str: the summarized context
    """
    task_context_dict = task_context_input.model_dump()
    PROMPT = f"""
    You are a Task Context Agent. Your primary function is to generate a concise summary from a provided task context object.

    **Instructions for Summary Generation:**

    1.  **Input:** You will receive a task context object: `{task_context_dict}`.
    2.  **Core Task:** Summarize this object.
    3.  **Information to INCLUDE:**
        * The task's title.
        * Relevant department details (e.g., department name, team, section).
    4.  **Information to EXCLUDE (Strictly):**
        * DO NOT include any sensitive Personally Identifiable Information (PII). This includes, but is not limited to:
            * Phone numbers
            * Physical addresses (street, city, zip code, country, etc.)
            * Email addresses
            * (Consider if other items like full names of individuals, specific financial data, etc., should also be excluded based on your definition of "sensitive" for this task).
    5.  **Style & Tone:**
        * The summary must be **concise** and **to the point**.
        * Maintain a professional and factual tone.
    6.  **Output Format:**
        * Present the summary in a clear, readable text format. 
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=PROMPT,
        config={
            "response_mime_type": "application/json",
            "response_schema": TaskContext,
        },
    )
    return response.parsed


def generate_routing_agent_context(
    task_content: TaskContent, task_context: TaskContext
) -> RoutingAgentContext:
    """
    Determine which agent should handle the task based on the task context.
    """
    src = task_content.email_content.integration_source
    cfg = INTEGRATION_CONFIG.get(src)
    if cfg:
        logging.info(f"Routing agent | integration config: {cfg}")
        if cfg["mode"] == "fixed":
            target = cfg["agent"]
            priority_prompt = f"""
You are a task‐priority agent. Task context: {task_context.model_dump()}. \
The task will be handled by agent '{target}'.
Leave tags an empty list.
If the person is in senior management, choose 'very_high' or 'high'. \
Otherwise choose 'medium' or 'low'.
Response according to the output schema.
"""
            resp = client.models.generate_content(
                model=MODEL,
                contents=priority_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RoutingAgentContext,
                },
            )
            return resp.parsed

        elif cfg["mode"] == "infer":
            tmpl = cfg.get("prompt", "")
            prompt = tmpl.format(
                task_content_dump=task_content.model_dump(),
                task_context_dump=task_context.model_dump(),
            )
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RoutingAgentContext,
                },
            )
            return resp.parsed

    # fallback
    return RoutingAgentContext(
        target_agent="unsupported",
        agent_tags=[],
        priority="low",
    )