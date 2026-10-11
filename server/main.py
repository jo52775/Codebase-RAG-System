from fastapi import FastAPI
from loguru import logger
from api.codebase import router as codebase_router
from api.query import router as query_router
from startup import initialize_reranker_model

app = FastAPI(lifespan=initialize_reranker_model)

app.include_router(codebase_router, prefix="/api")
app.include_router(query_router, prefix="/api")