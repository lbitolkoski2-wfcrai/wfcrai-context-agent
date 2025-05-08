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

def generate_routing_agent_context(task_content: TaskContent, task_context: TaskContext) -> RoutingAgentContext:
    """
    Determine which agent should handle the task based on the task context.
    Args:
        task_context (str): The context of the task.
    Returns:
        str: The name of the agent that should handle the task.
    """
    integration_source = task_content.email_content.integration_source

    # TODO: read from config
    integration_config = {
        "gmail.wfcrdata": "data_agent",
        "gmail.csa": "csa_agent",
    }
    if integration_source in integration_config:
        agent = integration_config[integration_source]
        return RoutingAgentContext(
            target_agent=agent,
            agent_tags=[],
        )
    else:
        PROMPT = f"""
        You are a task routing agent, you will receive a task context and you need to determine which agent should handle the task.
        The task content object: {task_content.model_dump()}.\
        The task context object: {task_context.model_dump()}.\
        Your job is to determine which agent should handle the task and output base on output schema."""

        response = client.models.generate_content(
            model=MODEL,
            contents=PROMPT,
            config={
            "response_mime_type": "application/json",
            "response_schema": RoutingAgentContext,
        },
        )
        return response.parsed