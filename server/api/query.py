from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from database.database import get_db
from loguru import logger
from pydantic import BaseModel, Field
from services.retrieval.orchestrator import retrieval_orchestrator

router = APIRouter(prefix="/query")

class UserQuery(BaseModel):
    text: str = Field(..., min_length=1)

@router.post("/", status_code=status.HTTP_200_OK)
def process_user_query(user_query: UserQuery, request: Request, db: Session = Depends(get_db)):
    try:
        reranker_model = request.state.reranker
        chunks = retrieval_orchestrator(user_query.text, db, reranker_model)
        return chunks
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An internal error occurred during RAG system process: {e}"
            )
