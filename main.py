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

from schemas.models import EmailContent, ContextAgentResponse, ContextAgentState
# from langfuse.decorators import observe, langfuse_context

app = FastAPI()
context_agent = ContextAgent()
context_agent_graph = context_agent.compile_execution_graph()


@app.post("/process_email_content")
async def email_context(request: fastapi_request):
    #Verify the request body against the EmailContent schema
    request_json = await request.json()  # Pull email context from request
    try:
        email_content = dict(EmailContent(**request_json))
    except ValueError as e:
        return {"error": "Invalid request body"}

    logging.info("Context agent processing email...")
    
    context_agent_state = ContextAgentState(
        email_context=email_content,
        agent_context={}
    )
    # Execution of the LangGraph graph
    context_agent_result = await context_agent_graph.ainvoke(context_agent_state)
    response = ContextAgentResponse(**context_agent_result).format_org_context()
    return response


@app.get("/")
def health_check():
    return {"status": "Okay!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

