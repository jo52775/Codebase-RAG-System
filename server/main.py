from fastapi import FastAPI
from loguru import logger
from api.codebase import router as codebase_router
from api.query import router as query_router

app = FastAPI()

app.include_router(codebase_router, prefix="/api")
app.include_router(query_router, prefix="/api")