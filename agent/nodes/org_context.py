import logging
from schemas.context_agent_schema import PersonContext
import os
# from langfuse.decorators import observe, langfuse_context
class OrgContext:
    """"
    pull organizational context from the email, (from,to) | job title, department etc"
    """
    def __init__(self, agent):
        self.bq_connector = agent.bq_connector
        self.person_view = "agent_context.hmn"
        self.assistant = agent.assistant
        pass

    async def get_user_info(self, email):
        """
        get raw user information from bigquery
        """
        query = f"SELECT * FROM {self.person_view} WHERE (CAST(FROM_BASE64(encoded_address) as STRING)) = '{email}'"
        try:
            result = self.bq_connector.execute_query(query)
            result_dict = [dict(row) for row in result]
            if not result_dict:
                logging.error(f"User {email} not found in person context")
            result_dict[0]['email'] = result_dict[0]['encoded_address']
            person = PersonContext(**{
                "org_id": result_dict[0]['cost_centre_desc'],
                "region_id": result_dict[0]['region'],
                "area_id": result_dict[0]['area'],
                "context": {
                    "department_context": result_dict[0]['department_context']
                }
            })
            return person
        except Exception as e:
            logging.info(f"Error fetching user information from BigQuery: %s", e)
            return PersonContext()
    
    async def summarize_user_info(self, ctx):
        """
        LLM call to summarize user information
        """
        pass

    # @observe
    async def run(self, ctx):
        """
        pull organizational context from the email, (from,to) | job title, department etc
        """
        from_email = ctx.email_context['requestor_email']
        from_user = await self.get_user_info(from_email)
        ctx.agent_context['org_context'] = from_user.model_dump()
        return ctx