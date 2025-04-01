from pydantic import BaseModel
from typing import List, Optional

class ContextAgent(BaseModel):
    """
    ContextAgent StateGraph LangGraph Schema
    """
    email_context: dict
    agent_context: dict

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
