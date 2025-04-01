"""
Cloud Run Entry Point WebServer for the context-agent
Responsible for initializing the FastAPI server and defining the endpoints for the context-agent
Initializes the required DataAdapters and Actors for processing the requests
"""
from agent.context_agent import ContextAgent
from fastapi import FastAPI, Request as fastapi_request
import dotenv
dotenv.load_dotenv()

import json
import uuid
import logging

from schemas.context_agent_schema import EmailContent, ContextAgentResponse
# from langfuse.decorators import observe, langfuse_context

app = FastAPI()
context_agent = ContextAgent()
context_agent_graph = context_agent.compile_execution_graph()


@app.post("/process_email_content")
async def data_request(request: fastapi_request):
    #Verify the request body against the EmailContent schema
    request_json = await request.json()  # Pull email context from request
    try:
        email_content = EmailContent(**request_json) 
        email_content = dict(email_content)
    except ValueError as e:
        logging.error("Data Agent | Invalid request body: " + str(e))
        return {"error": "Invalid request body"}

    logging.info("Data Agent | processing job:" + str(email_content))
    context_agent_state = {
        "email_context": email_content,
        "agent_context":{}
    }
    # Execution of the LangGraph graph
    context_agent_result = await context_agent_graph.ainvoke(context_agent_state)
    response = validate_and_format_result(context_agent_result)
    return response

@app.post("/bulk_confluence_context")
async def bulk_confluence_context(request: fastapi_request):
    return {"status": "up!"}


def validate_and_format_result(result):
    """
    Validate the response from the context agent
    """
    response = {
        "region_id": result["agent_context"]["org_context"]["region"],
        "area_id": result["agent_context"]["org_context"]["area"],
        "org_id": result["agent_context"]["org_context"]["cost_centre_desc"],
        "context": {
            "department_context": result["agent_context"]["org_context"]["department_context"],
        }
    }

    try:
        formatted_response = dict(ContextAgentResponse(**response))
    except ValueError as e:
        return {"error": "Validation error in agent response"}
    return formatted_response


@app.get("/")
def health_check():
    return {"status": "Okay!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

