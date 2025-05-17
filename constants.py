import os

import dotenv

dotenv.load_dotenv()

GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "gcp-wow-food-wfc-ai-dev")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL = os.getenv("MODEL", "gemini-2.5-flash-preview-04-17")
