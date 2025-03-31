from agent_utils.connectors import ConfluenceConnector, BigQueryConnector, LLMConnector, GoogleCloudStorageConnector
from agent_utils.components.assistant import Assistant
from langgraph.graph import StateGraph
import schemas.context_agent_schema as context_agent_schema

from nodes.org_context import OrgContext

class AgentContext:
    """
    Populate shared context fiedl for all agents based on the incoming email
    Write the updated context to the inqueue in alloydb
    """

    def __init__(self):
        self.load_connectors()
        self.config = self.gcs_connector.load_toml("context-agent/config/bundled.toml")     
        self.assistant = Assistant(self.llm_connector, self.config) 
        pass

    def load_connectors(self):
        self.gcs_connector = GoogleCloudStorageConnector()
        self.config = self.gcs_connector.load_toml()        
        self.bq_connector = BigQueryConnector(self.config)
        self.confluence_connector = ConfluenceConnector(self.config)
        self.llm_connector = LLMConnector(self.config, "openai")

    async def compile_execution_graph(self,ctx):
        schema = context_agent_schema.ContextAgent
        graph_builder = StateGraph(schema)

        org_context_node = OrgContext(self)

        graph_builder.add_node("start", lambda ctx: ctx)
        graph_builder.add_node("org_context", org_context_node.run)
        graph_builder.add_node("end", lambda ctx: ctx)

        graph_builder.add_edge("start", "org_context")
        graph_builder.add_edge("org_context", "end")

        graph_builder.set_entry_point("start")
        agent_graph = graph_builder.compile()
        return agent_graph