from agent.context_agent import ContextAgent
import asyncio
context_agent = ContextAgent()
context_agent_graph = context_agent.compile_execution_graph()

async def run_agent(email_context):
    return await context_agent_graph.run(email_context)

email_context = {
    "from": "dsearle3@woolworths.com.au",
    "to": "wfcrdata@woolworths.com.au",
    ":task_prompt": "Please pull me all hotdog products"
}

result = asyncio.run(run_agent(email_context))
print(result)