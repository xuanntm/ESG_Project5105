from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)