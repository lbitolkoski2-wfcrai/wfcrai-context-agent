from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class PersonContextInput(BaseModel):
    # org_id: Optional[str] = ""
    area: Optional[str] = ""
    region: Optional[str] = ""
    ops_or_support: Optional[str] = ""
    department_context: Optional[str] = ""
    area_count: Optional[int] = ""
    # context: Optional[str] = ""


class EmailContentInput(BaseModel):
    request_id: str
    request_inqueue_type: str
    request_inqueue_details: str
    requestor_email: str
    request_subject: Optional[str] = ""
    request_body: str
    integration_source: str
    attachments: List[str]

class TaskContent(BaseModel):
    email_content: EmailContentInput
    person_context: PersonContextInput

class TaskContext(BaseModel):
    request_micro_summary: str
    request_context_summary: str
    request_context: str
    requestor_context: str
    parsed_attachments: List[str]

class Agents(str, Enum):
    """
    Enum for the agents
    """
    DATA_AGENT = "data_agent"
    CSA_AGENT = "csa_agent"
    UNSUPPORTED = "unsupported"

class Priority(str, Enum):
    """
    Enum for the priority
    """
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RoutingAgentContext(BaseModel):
    target_agent: Agents
    agent_tags: Optional[List[str]] = []
    priority: Priority = Priority.LOW

class ContextAgentResponse(RoutingAgentContext, TaskContext):
    """
    ContextAgentResponse Schema
    """
    pass