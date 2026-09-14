from fastapi import APIRouter
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.database import get_db
from scripts.getFiles import getCodeFiles
from scripts.chunk import splitCodebase
from scripts.embed import embed_classes, embed_functions, clear_database
from loguru import logger

router = APIRouter(prefix="/codebase-embedding")

@router.get("/", status_code=status.HTTP_200_OK)
def embedCodebase(db: Session = Depends(get_db)):
    try:
        # Fetch repository code files
        logger.info("Retrieving code files from GitHub repository...")
        codefiles = getCodeFiles()
        
        # Split code from each file into 'function' or 'class' code chunks
        logger.info("Starting code splitting process with tree-sitter...")
        functions, classes = splitCodebase(codefiles)

        # Clearing database before storing code chunks and metadata
        clear_database(db)

        # Embed classes, store code chunks and metadata into database
        logger.info("Starting class chunks embedding and storage process...")
        total_class_rows_inserted, valid_class_fqns = embed_classes(db, classes) 

        # Embed functions, store code chunks and metadata into database
        logger.info("Starting function chunks embedding and storage process...")
        total_function_rows_inserted = embed_functions(db, functions, valid_class_fqns)
        return {
            "status": "success",
            "message": "Codebase successfully chunked and stored.",
            "class_rows_inserted": total_class_rows_inserted,
            "function_rows_inserted": total_function_rows_inserted
        }
    except Exception as e:
        logger.error(f"Codebase chunking task failed: , {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the codebase."
        )