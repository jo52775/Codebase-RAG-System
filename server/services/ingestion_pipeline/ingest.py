from langchain_openai import OpenAIEmbeddings
from langsmith import AuthenticationError
from loguru import logger
from sqlalchemy.orm import Session
from database.models.chunk import FunctionModel, ClassModel
from sqlalchemy import delete, insert
from sqlalchemy.exc import SQLAlchemyError

def clear_database(db: Session):
    try:
        db.execute(delete(FunctionModel))
        db.execute(delete(ClassModel))
        db.commit()
        logger.info("Database cleared successfully.")
    except SQLAlchemyError as db_err:
        logger.error(f"Database clearing failed: {db_err}")
        raise db_err


def ingest_classes(db: Session, classes: list[dict], embedder: OpenAIEmbeddings):
    total_rows_inserted = 0
    valid_class_fqns = set()
    try:
        code_chunks = [class_chunk["raw_code_text"] for class_chunk in classes]
        try:
            if not classes:
                return 0, set()
            
            vector_embeddings = embedder.embed_documents(code_chunks)
            logger.info(f"Embedding successful for classes. {len(vector_embeddings)} vectors created. \n")
        except Exception as e:
            logger.error(f"OpenAI API generation failed for classes: {e}")
            raise e

        records = []
        for idx, chunk in enumerate(classes):
            record = {
                "semantic_search_vector": vector_embeddings[idx],
                "entity_name": chunk["entity_name"],
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
        logger.info("Successfully stored vectors and metadata for all classes in the codebase. \n")
        return total_rows_inserted, valid_class_fqns
                
    except AuthenticationError:
        db.rollback() 
        logger.error("Authentication Failed: OpenAI API key is invalid or has expired.")
        raise
    except Exception as e:
        db.rollback() 
        logger.error(f"Something went wrong with embedding and/or saving class chunks: {e}")
        raise e

def ingest_functions(db: Session, functions: list[dict], valid_class_fqns: set[str], embedder: OpenAIEmbeddings):
    total_rows_inserted = 0
    try:
        code_chunks = [function_chunk["raw_code_text"] for function_chunk in functions]
        try:
            vector_embeddings = embedder.embed_documents(code_chunks)
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
                "semantic_search_vector": vector_embeddings[idx],
                "entity_name": chunk["entity_name"],
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
        logger.info("Successfully stored vectors and metadata for all functions in the codebase. \n")
        return total_rows_inserted
                
    except AuthenticationError:
        db.rollback() 
        logger.error("Authentication Failed: OpenAI API key is invalid or has expired.")
        raise
    except Exception as e:
        db.rollback() 
        logger.error(f"Something went wrong with embedding and/or saving function chunks: {e}")
        raise e