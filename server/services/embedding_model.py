import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class Embedding_Model:
    def __init__(self):
        self.model = "text-embedding-3-large"
        self.dimensions = 1024
        self.api_key = os.getenv("OPENAI_API_KEY")

    def initialize_embedding_model(self):
        embedder = OpenAIEmbeddings(
            model=self.model,
            dimensions=self.dimensions,
            api_key=self.api_key
        )
        return embedder