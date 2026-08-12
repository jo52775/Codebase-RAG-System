import os
from langchain_openai import OpenAIEmbeddings
from langsmith import AuthenticationError
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy.orm import Session
from database.models.chunk import Chunk
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

repo_name = os.getenv("REPO_NAME")
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Cannot find OPENAI_API_KEY.")

embed = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024,
    api_key=api_key
)

def embed_codebase(db: Session, chunked_files):
    total_rows_inserted = 0
    try:
        for filename, chunks in chunked_files.items():
            if not chunks:
                logger.info(f"Skipping file: {filename} \n")
                continue
            logger.info(f"Starting embedding process for {filename}. {len(chunks)} chunks found. \n")

            try:
                code_chunks = [chunk["text"] for chunk in chunks]
                vector_embeddings = embed.embed_documents(code_chunks)
                logger.info(f"Embedding successful for {filename}. {len(vector_embeddings)} vectors created. \n")
            except Exception as e:
                logger.error(f"OpenAI API generation failed for {filename}: {e}")
                raise e

            records = []
            for idx, chunk in enumerate(chunks):
                metadata = chunk["metadata"]
                record = {
                    "vector": vector_embeddings[idx],
                    "raw_code_text": chunk["text"],
                    "filename": metadata["filename"],
                    "start_line": metadata["start_line"],
                    "end_line": metadata["end_line"],
                    "entity_name": metadata["entity_name"],
                    "entity_type": metadata["entity_type"],
                    "code_repository": repo_name,
                }
                records.append(record)
            if records:
                try:
                    db.execute(insert(Chunk), records)
                    total_rows_inserted += len(records)
                    logger.info(f"Staged {len(records)} records for file: {filename} \n")
                except SQLAlchemyError as db_err:
                    logger.error(f"Database insert staging failed for {filename}: {db_err}")
                    raise db_err

        db.commit()
        logger.info("Successfully stored all embeddings and metadata for codebase. \n")
        return total_rows_inserted

    except AuthenticationError:
        db.rollback() 
        logger.error("Authentication Failed: OpenAI API key is invalid or has expired.")
        raise
    except Exception as e:
        db.rollback() 
        logger.error(f"Something went wrong with the codebase embedding: {e}")
        raise e