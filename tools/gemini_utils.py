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
You are a Task Context Agent. Your primary function is to analyze a provided task context object and generate a concise, factual summary.

**Input:**
* You will receive a JSON object representing the task context: `{task_context_dict}`. This object contains various details about a task.

**Primary Goal:**
* Generate a concise summary of the task based *only* on the information present in the `{task_context_dict}`.

**Instructions for Summary Generation:**

1.  **Identify Core Information (Include if present):**
    * **Task Title:** Extract the main title or subject of the task. If no explicit title field exists, try to infer a short descriptive title from available text fields (e.g., 'subject', 'description' - prioritize in that order if multiple exist). If no title can be determined, state "Untitled Task".
    * **Department Details:** Include relevant department information if available (e.g., department name, team name, section). If not present, omit this without comment.

2.  **Handling Task Nature (Request vs. Informational):**
    * Analyze the content of `{task_context_dict}` to determine if it primarily represents a direct request for action/information or if it's an informational statement/update.
    * **If it's a Request:** The summary should briefly state the nature of the request (e.g., "Request for X," "Inquiry about Y").
    * **If it's Informational/Statement:** The summary should reflect this (e.g., "Informational update on X," "Status: Y"). If ambiguous, err on the side of summarizing the core information factually.
    * **Example Output Prefix:**
        * For requests: "Task Request: [Summary]"
        * For informational: "Task Information: [Summary]" or "Task Status: [Summary]"

3.  **Strict PII Exclusion (CRITICAL):**
    * **DO NOT include any Personally Identifiable Information (PII) in the summary.** This is a strict requirement.
    * **PII to EXCLUDE includes (but is not limited to):**
        * Full names of individuals (use initials or roles if essential and generic, e.g., "J.D." or "Project Manager," but prefer to omit if possible)
        * Phone numbers
        * Physical addresses (street, city, state, zip code, country)
        * Email addresses
        * Dates of birth
        * Social Security Numbers (or national ID equivalents)
        * Driver's license numbers
        * Financial account numbers
        * Any other data that could uniquely identify an individual.
    * **Focus on summarizing the *task* itself, not the people involved, unless it's their role (e.g., "Assigned to: Engineering Team").**

4.  **Style & Tone:**
    * **Concise:** The summary must be brief and to the point. Aim for 1-3 sentences or a few key bullet points.
    * **Factual & Professional:** Maintain an objective, professional tone. Avoid speculation or adding information not present in the input object.

5.  **Handling Missing Information:**
    * If critical information (like a task title or primary purpose) is entirely missing and cannot be inferred, the summary should state "Insufficient information to summarize task details beyond [mention any non-PII contextual info available, like department if present]."
    * For non-critical optional details (like department if not found), simply omit them.

**Example of thinking process (for the agent):**
1.  Examine `{task_context_dict}`.
2.  Is there a title? Yes, "Update website homepage."
3.  Is there department info? Yes, "Marketing Department, Web Team."
4.  Does it seem like a request? Yes, context implies action needed. So, "Task Request:".
5.  Any PII? Yes, "user_email: john.doe@example.com". EXCLUDE THIS.
6.  Construct summary: "Task Request: Update website homepage for the Marketing Department, Web Team."

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
You are a Task Priority Agent. Your goal is to assign a priority to a task based on its context.

**Input Context:**
* You will receive task details in a structured format (derived from `{task_context.model_dump()}`).
* The task is intended for agent: '{target}'. (Note: This information is for context only and does not directly alter the priority assignment rules below, unless the task description itself ties the target agent to urgency/impact).

**Priority Levels:** `very_high`, `high`, `medium`, `low`

**Priority Assignment Rules (apply in order):**

1.  **Non-Task Content:**
    * If the input context appears to be purely informational (e.g., a log entry, a comment without a clear action, a general statement) and not a direct, actionable task:
        * Set `priority` to `low`.

2.  **Senior Management Involvement:**
    * Check the task context for information about the requester or key stakeholders (e.g., look for fields like `requester_role`, `user_title`, `stakeholder_level`).
    * If a key person involved is identified as senior management (e.g., terms like "CEO", "VP", "Director", "Head of Department", "President", "C-level"):
        * Set `priority` to `high`.
        * Consider changing to `very_high` ONLY if the task context ALSO explicitly states or strongly implies critical urgency (e.g., "system down," "urgent," "deadline critical") or major business impact.
    * If no clear indication of senior management involvement: Proceed to rule 3.

3.  **Default Priority:**
    * For all other actionable tasks not meeting the criteria above:
        * Set `priority` to `medium`.
        * Consider changing to `low` if the task seems minor, routine, or has no implied urgency or impact.

**Important:**
* Base your decisions SOLELY on the provided task context. Do not make assumptions beyond the given information.
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