from fastapi import FastAPI
from loguru import logger
from api.codebaseEmbedding import router as codebase_embedding_router

app = FastAPI()

app.include_router(codebase_embedding_router, prefix="/api")