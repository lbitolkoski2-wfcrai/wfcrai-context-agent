from google import genai
from dotenv import load_dotenv
from constants import MODEL
from pydantic import BaseModel
from schemas.context_agent_schema import TaskContent, TaskContext, RoutingAgentContext

load_dotenv()

client = genai.Client()


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
    You are a task context agent. Your job is to generate a summary of the task context object based on the output schema.
    DO NOT include any sensitive information like phone number or address at all. But include the title, department details. 
    The task context object is: {task_context_dict}.The summary should be concise and to the point."""

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
    integration_source = task_content.email_content.integration_source

    # TODO: load this from env or a config file
    integration_config = {
        "gmail.wfcrdata": {"mode": "fixed", "agent": "data_agent"},
        "gmail.policy": {"mode": "fixed", "agent": "policy_agent"},
        "custom.system": {
            "mode": "infer",
            "prompt": """
        You are the routing agent for Custom System. Your job is to determine which agent should handle the task based on the task content and context.
        Given the following task content and context, output the RoutingAgentContext JSON:
        Task content: {task_content_dump}
        Task context: {task_context_dump}""",
        },
    }

    cfg = integration_config.get(integration_source)
    if cfg:
        if cfg["mode"] == "fixed":
            target_agent = cfg["agent"]
            # --- new: call LLM to pick a priority tag ---
            priority_prompt = f"""
        You are a task‐priority agent. Task context: {task_context.model_dump()}. The task will be handled by agent '{target_agent}'.
        Leave tags an empty list.
        If the person is in senior management, choose 'very_high' or 'high'. Otherwise choose 'medium' or 'low'.
        Response according to the output schema."""
            resposne = client.models.generate_content(
                model=MODEL,
                contents=priority_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RoutingAgentContext,
                },
            )
            return resposne.parsed

        elif cfg["mode"] == "infer":
            # use per‐integration prompt if present, else fallback
            tmpl = cfg.get("prompt")
            prompt = (
                tmpl.format(
                    task_content_dump=task_content.model_dump(),
                    task_context_dump=task_context.model_dump(),
                )
                if tmpl
                else f"""You are a task routing agent.
            Task content: {task_content.model_dump()}
            Task context: {task_context.model_dump()}
            Determine which agent to call and return a RoutingAgentContext JSON."""
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

    # fallback to generic LLM routing
    # default_prompt = f"""You are a task routing agent.
    # Task content: {task_content.model_dump()}
    # Task context: {task_context.model_dump()}
    # Determine which agent to call and return according to the output schema."""
    # resp = client.models.generate_content(
    #     model=MODEL,
    #     contents=default_prompt,
    #     config={
    #         "response_mime_type": "application/json",
    #         "response_schema": RoutingAgentContext,
    #     },
    # )
    return RoutingAgentContext(
        target_agent="unsupported",
        agent_tags=[],
        priority="low",
    )


#     )
