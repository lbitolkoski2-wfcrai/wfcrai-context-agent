# from google.cloud import bigquery
import logging

from google.cloud import bigquery

from constants import GCP_LOCATION, GCP_PROJECT
from schemas.context_agent_schema import EmailContentInput, PersonContextInput

# from agent_utils.connectors import BigQueryConnector



bq_client = bigquery.Client()


def get_sender_context(requestor_email: str) -> PersonContextInput:
    """
    Get requestor context from bigquery base on the requestor email

    Args:
        requestor_email (str): the email of the requestor
    Returns:
        PersonContext: the context of the requestor
    """
    # config = {
    #     "bigquery": {
    #         "project_id": GCP_PROJECT,
    #         "region": GCP_LOCATION,
    #     }
    # }
    # bq_connector = BigQueryConnector(config=config)
    query = f"SELECT * FROM test.person_context WHERE employee_corporate_email = '{requestor_email}'"
    try:
        result = bq_client.query_and_wait(query)
        rows = [dict(row) for row in result]
        logging.info(f"Query result: {rows}")
        if not rows:
            logging.error(f"User {requestor_email} not found in person context")
            return PersonContextInput()
        first_row = rows[0]
        person = PersonContextInput(**first_row)
        return person
    except Exception as e:
        logging.info(f"Error fetching user information from BigQuery: %s", e)
        return PersonContextInput()
