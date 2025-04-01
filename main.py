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

from schemas.context_agent_schema import EmailContent
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
    return context_agent_result

@app.get("/")
def health_check():
    return {"status": "Okay!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

