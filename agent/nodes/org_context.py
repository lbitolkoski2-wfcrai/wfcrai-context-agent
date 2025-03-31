import agent_utils.connectors.bq_connector as bq_connector
class OrgContext:
    """"
    pull organizational context from the email, (from,to) | job title, department etc"
    """
    def __init__(self, agent):
        self.bq_connector = agent.bq_connector
        # self.person_view = agent.config['org_context']['person_view']
        self.person_view = 'testing.org_context_v'
        self.assistant = agent.assistant
        pass

    async def get_user_info(self, email):
        """
        get raw user information from bigquery
        """
        query = f"SELECT * FROM {self.person_view} WHERE user_email = '{email}'"
        result = self.bq_connector.execute_query(query)
        return await result

    async def summarize_user_info(self, ctx):
        """
        LLM call to summarize user information
        """

        pass

    async def run(self, ctx):
        """
        pull organizational context from the email, (from,to) | job title, department etc
        """
        from_email = ctx['from']
        to_email = ctx['to']
        from_user = await self.get_user_info(from_email)
        to_user = await self.get_user_info(to_email)
        ctx['org_context'] = {
            'from': from_user,
            'to': to_user
        }
        return ctx