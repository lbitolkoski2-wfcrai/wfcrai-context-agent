from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PersonContextInput(BaseModel):
    # org_id: Optional[str] = ""
    area: Optional[str] = Field(
        description="area of the requestor in",
        default="",
    )
    region: Optional[str] = Field(
        description="region of the requestor in",
        default="",
    )
    ops_or_support: Optional[str] = Field(
        description="ops or support of the requestor in",
        default="",
    )
    department_context: Optional[str] = Field(
        description="department context of the requestor in",
        default="",
    )
    area_count: Optional[int] = Field(
        description="count of the people of the area",
        default="",
    )
    # context: Optional[str] = ""


class EmailContentInput(BaseModel):
    request_id: UUID = Field(
        description="request uuid",
    )
    request_inqueue_type: str = Field(description="request inqueue type")
    request_inqueue_details: str = Field(
        description="email that received the request",
    )
    requestor_email: str = Field(description="email of the requestor")
    request_subject: str = Field(
        description="subject of the email request",
    )
    request_body: str = Field(
        description="body of the email request",
    )
    integration_source: str = Field(
        description="integration source",
        examples=["gmail.wfcrdata", "gmail.policy"],
    )
    attachments: List[dict] = Field(
        description="attachments of the email request",
    )


class TaskContent(BaseModel):
    email_content: EmailContentInput = Field(
        description="Contains the email content of the request",
    )
    person_context: PersonContextInput = Field(
        description="Contains the person context of the requestor",
    )


class TaskContext(BaseModel):
    request_micro_summary: str = Field(
        description="micro summary of the request",
        default="",
    )
    request_context_summary: str = Field(
        description="summary of the request context",
        default="",
    )
    request_context: str = Field(
        description="context of the request, excluding personal information of the requestor like name, email, address, number etc.",
        default="",
    )
    requestor_context: str = Field(
        description="context of the requestor",
        default="",
    )
    parsed_attachments: List[str] = Field(
        default_factory=list,
        description="parsed attachments of the email request",
    )


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
    target_agent: Agents = Agents.UNSUPPORTED
    agent_tags: List[str] = Field(default_factory=list)
    priority: Priority = Priority.LOW


class ContextAgentResponse(RoutingAgentContext, TaskContext):
    """
    ContextAgentResponse Schema
    """

    pass
