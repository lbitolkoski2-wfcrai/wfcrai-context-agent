from pydantic import BaseModel
from typing import List, Optional

class ContextAgentState(BaseModel):
    """
    ContextAgent StateGraph LangGraph Schema
    """
    email_context: dict
    agent_context: dict

    @property
    def format_org_context(self):
        return {
            "region_id": self.agent_context["org_context"]["region"],
            "area_id": self.agent_context["org_context"]["area"],
            "org_id": self.agent_context["org_context"]["cost_centre_desc"],
            "context": {
                "department_context": self.agent_context["org_context"]["department_context"],
            }
        }

class SummarizeEmail(BaseModel):
    """
    SummarizeEmail Schema
    """
    summary: str
    user_reasoning: str


class EmailContent(BaseModel):
    request_id: str
    request_inqueue_type: str
    request_inqueue_details: str
    requestor_email: str
    request_subject: str
    request_body: str
    attachments: List[dict]


class ContextAgentResponse(BaseModel):
    org_id: str
    region_id: str
    area_id: str
    context: dict
