from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import CrossEncoder
from loguru import logger

@asynccontextmanager
async def initialize_reranker(app: FastAPI):
    reranker_model = None
    use_cross_encoder = False
    try:
        if use_cross_encoder:
            logger.info("Attempting to load reranker model into memory...")
            reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3")
            logger.info("Re-ranker model loaded successfully!")
    except Exception as e:
        logger.warning(f"Warning: Failed to load reranker model: {e}")
        reranker_model = None

    yield {"reranker": reranker_model}
    
    print("Cleaning up server resources...")