import os
import re
from langchain_openai import OpenAIEmbeddings
from langsmith import AuthenticationError
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import func

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Cannot find OPENAI_API_KEY.")

embed = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024,
    api_key=api_key
)

def user_query_to_tsquery(query_text: str):
    cleaned_query = re.sub(r'[^\w\s.\-"]', '', query_text)
    tokens = [t[:1000] for t in cleaned_query.split() if t.strip()]
    if not tokens:
        return func.to_tsquery("english", "''")

    or_string = " | ".join(tokens)
    return func.to_tsquery("english", or_string)

def embed_user_query(query_text: str):
    """Leverage the OpenAI API to embed user's query and return it."""
    try:
        query_vector = embed.embed_query(query_text)
        logger.info('Query text successfully embedded.')
        return query_vector
    except Exception as e:
        logger.error(f"OpenAI API embedding failed for user query: {e}")
        raise e

