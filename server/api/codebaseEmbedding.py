from fastapi import APIRouter
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.database import get_db
from scripts.getFiles import getCodeFiles
from scripts.chunk import splitCodebase
from scripts.embed import embed_codebase
from loguru import logger

router = APIRouter(prefix="/codebase-embedding")

@router.get("/", status_code=status.HTTP_200_OK)
def embedCodebase(db: Session = Depends(get_db)):
    try:
        # Fetch repository code files
        logger.info("Retrieving code files from GitHub repository...")
        codefiles = getCodeFiles()
        
        # Split code from each file into chunks
        logger.info("Starting code splitting process with tree-sitter...")
        chunked_files = splitCodebase(codefiles)

        # Embed code chunks and store into database
        logger.info("Starting code chunks embedding and storage process...")
        total_rows_inserted = embed_codebase(db, chunked_files) 
        return {
            "status": "success",
            "message": "Codebase successfully chunked and stored.",
            "rows_inserted": total_rows_inserted
        }
    except Exception as e:
        logger.error(f"Codebase chunking task failed: , {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the codebase."
        )