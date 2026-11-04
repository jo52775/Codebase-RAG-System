from fastapi import APIRouter
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.database import get_db
from services.repository import Repository
from services.embedding_model import Embedding_Model
from services.ingestion_pipeline.getFiles import getCodeFiles
from services.ingestion_pipeline.chunk import splitCodebase
from services.ingestion_pipeline.ingest import ingest_classes, ingest_functions, clear_database
from loguru import logger

router = APIRouter(prefix="/process-codebase")

@router.get("/", status_code=status.HTTP_200_OK)
def processCodebase(db: Session = Depends(get_db)):
    try:
        repository = Repository()
        repo_name = repository.name

        e = Embedding_Model()
        embedder = e.initialize_embedding_model()

        # Fetch repository code files
        logger.info("Retrieving code files from GitHub repository...")
        codefiles = getCodeFiles(repository)
        
        # Split code from each file into 'function' or 'class' code chunks
        logger.info("Starting code splitting process with tree-sitter...")
        functions, classes = splitCodebase(codefiles, repo_name)

        # Clearing database before storing code chunks and metadata
        clear_database(db)

        # Handle creation and storage of search vectors and metadata for class chunks
        logger.info("Starting class chunks processing and storage process...")
        total_class_rows_inserted, valid_class_fqns = ingest_classes(db, classes, embedder) 

        # Handle creation and storage of search vectors and metadata for function chunks
        logger.info("Starting function chunks processing and storage process...")
        total_function_rows_inserted = ingest_functions(db, functions, valid_class_fqns, embedder)

        return {
            "status": "success",
            "message": "Codebase successfully chunked and stored.",
            "class_rows_inserted": total_class_rows_inserted,
            "function_rows_inserted": total_function_rows_inserted
        }
    except Exception as e:
        logger.error(f"Codebase processing task failed: , {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the codebase."
        )