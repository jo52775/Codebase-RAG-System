import os
from langchain_openai import OpenAIEmbeddings
from langsmith import AuthenticationError
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy.orm import Session
from database.models.chunk import FunctionModel, ClassModel
from sqlalchemy import delete, insert
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

def clear_database(db: Session):
    try:
        db.execute(
            delete(FunctionModel).where(FunctionModel.code_repository == repo_name)
        )
        db.execute(
                delete(ClassModel).where(ClassModel.code_repository == repo_name)
            )
        db.commit()
        logger.info("Database cleared successfully.")
    except SQLAlchemyError as db_err:
                    logger.error(f"Database insert staging failed for classes: {db_err}")
                    raise db_err 


def embed_classes(db: Session, classes: list[dict]):
    total_rows_inserted = 0
    valid_class_fqns = set()
    try:
        code_chunks = [class_chunk["raw_code_text"] for class_chunk in classes]
        try:
            if not classes:
                return 0, set()
            vector_embeddings = embed.embed_documents(code_chunks)
            logger.info(f"Embedding successful for classes. {len(vector_embeddings)} vectors created. \n")
        except Exception as e:
            logger.error(f"OpenAI API generation failed for classes: {e}")
            raise e

        records = []
        for idx, chunk in enumerate(classes):
            record = {
                "vector": vector_embeddings[idx],
                "fqn": chunk["fqn"],
                "raw_code_text": chunk["raw_code_text"],
                "filename": chunk["filename"],
                "skeleton_text": chunk["skeleton_text"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "code_repository": chunk["code_repository"],
            }
            records.append(record)
            valid_class_fqns.add(chunk["fqn"])

        if records:
            try:
                db.execute(insert(ClassModel), records)
                total_rows_inserted += len(records)
                logger.info(f"Staged {len(records)} class records \n")
            except SQLAlchemyError as db_err:
                logger.error(f"Database insert staging failed for classes: {db_err}")
                raise db_err

        db.commit()
        logger.info("Successfully stored all class embeddings and metadata from the codebase. \n")
        return total_rows_inserted, valid_class_fqns
                
    except AuthenticationError:
        db.rollback() 
        logger.error("Authentication Failed: OpenAI API key is invalid or has expired.")
        raise
    except Exception as e:
        db.rollback() 
        logger.error(f"Something went wrong with embedding and/or saving class chunks: {e}")
        raise e

def embed_functions(db: Session, functions: list[dict], valid_class_fqns: set[str]):
    total_rows_inserted = 0
    try:
        code_chunks = [function_chunk["raw_code_text"] for function_chunk in functions]
        try:
            vector_embeddings = embed.embed_documents(code_chunks)
            logger.info(f"Embedding successful for functions. {len(vector_embeddings)} vectors created. \n")
        except Exception as e:
            logger.error(f"OpenAI API generation failed for functions: {e}")
            raise e

        records = []
        for idx, chunk in enumerate(functions):
            chunk_parent_class_fqn = chunk["parent_class_fqn"]
            if chunk_parent_class_fqn not in valid_class_fqns:
                chunk_parent_class_fqn = None

            record = {
                "vector": vector_embeddings[idx],
                "raw_code_text": chunk["raw_code_text"],
                "filename": chunk["filename"],
                "entity_fqn": chunk["entity_fqn"],
                "parent_fqn": chunk["parent_fqn"],
                "parent_class_fqn": chunk_parent_class_fqn,
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "code_repository": chunk["code_repository"],
            }
            records.append(record)

        if records:
            try:
                db.execute(insert(FunctionModel), records)
                total_rows_inserted += len(records)
                logger.info(f"Staged {len(records)} function records \n")
            except SQLAlchemyError as db_err:
                logger.error(f"Database insert staging failed for functions: {db_err}")
                raise db_err

        db.commit()
        logger.info("Successfully stored all function embeddings and metadata from the codebase. \n")
        return total_rows_inserted
                
    except AuthenticationError:
        db.rollback() 
        logger.error("Authentication Failed: OpenAI API key is invalid or has expired.")
        raise
    except Exception as e:
        db.rollback() 
        logger.error(f"Something went wrong with embedding and/or saving function chunks: {e}")
        raise e