"""
Cloud Run Entry Point WebServer for the context-agent
Responsible for initializing the FastAPI server and defining the endpoints for the context-agent
Initializes the required DataAdapters and Actors for processing the requests
"""

import logging
import os
import uuid

import dotenv
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi import Request as fastapi_request
from langfuse.decorators import observe

from schemas.context_agent_schema import (ContextAgentResponse,
                                          EmailContentInput, TaskContent)
from tools.bq_utils import get_sender_context
from tools.gemini_utils import (generate_genric_task_context,
                                generate_routing_agent_context)

dotenv.load_dotenv()
app = FastAPI()
logging.basicConfig(level=logging.DEBUG)


@app.post("/context")
@observe(name="context-agent")
async def generate_task_context(request: fastapi_request):
    session_id = str(uuid.uuid4())

    request_json = await request.json()
    try:
        email_content = EmailContentInput.model_validate(request_json)
    except ValueError as e:
        logging.error("error validating email content: " + str(e))
        raise HTTPException(status_code=400, detail="Invalid request body")

    logging.info(f"Context agent | processing job: {email_content.request_id}")
    sender_context = get_sender_context(email_content.requestor_email)
    task_content = TaskContent(
        email_content=email_content, person_context=sender_context
    )
    task_context_response = generate_genric_task_context(
        task_content, session_id=session_id
    )
    logging.info(f"Context agent | task context: {task_context_response.model_dump()}")
    routing_agent_response = generate_routing_agent_context(
        task_content=task_content,
        task_context=task_context_response,
        session_id=session_id,
    )
    logging.info(
        f"Context agent | routing agent response: {routing_agent_response.model_dump()}"
    )

    # Combine the task context and routing agent response into a single response
    task_context_response_dict = task_context_response.model_dump()
    routing_agent_response_dict = routing_agent_response.model_dump()
    task_context_response_dict.update(routing_agent_response_dict)
    return ContextAgentResponse.model_validate(task_context_response_dict).model_dump()


@app.get("/")
def health_check():
    return {"status": "Okay!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
