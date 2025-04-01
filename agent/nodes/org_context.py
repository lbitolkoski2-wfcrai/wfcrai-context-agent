import agent_utils.connectors.bq_connector as bq_connector
# from langfuse.decorators import observe, langfuse_context
class OrgContext:
    """"
    pull organizational context from the email, (from,to) | job title, department etc"
    """
    def __init__(self, agent):
        self.bq_connector = agent.bq_connector
        # self.person_view = agent.config['org_context']['person_view']
        self.person_view = 'agent_context.org_context_v'
        self.assistant = agent.assistant
        pass

    async def get_user_info(self, email):
        """
        get raw user information from bigquery
        """
        query = f"SELECT * FROM {self.person_view} WHERE user_email = '{email}'"
        try:
            result = self.bq_connector.execute_query(query)
            result_dict = [dict(row) for row in result]
            if not result_dict:
                raise ValueError(f"No user information found for email: {email}")
            return result_dict[0]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch user information for email: {email}. Error: {str(e)}")
    
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
        ctx.agent_context['org_context'] = from_user
        return ctx