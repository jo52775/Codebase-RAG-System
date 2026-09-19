import os
from langchain_openai import OpenAIEmbeddings
from langsmith import AuthenticationError
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Cannot find OPENAI_API_KEY.")

embed = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024,
    api_key=api_key
)

def embed_user_query(query_text: str):
    """Leverage the OpenAI API to embed user's query and return it."""
    try:
        query_vector = embed.embed_query(query_text)
        logger.info('Query text successfully embedded.')
        return query_vector
    except Exception as e:
        logger.error(f"OpenAI API embedding failed for user query: {e}")
        raise e

