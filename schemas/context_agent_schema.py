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

class ConfluenceContext:
    """
    ConfluenceContext Schema
    """
    confluence_page: str
    confluence_page_id: str
    type: str # [dataset,table]
    