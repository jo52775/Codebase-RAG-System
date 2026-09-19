from loguru import logger
from sqlalchemy.orm import Session
from database.models.chunk import FunctionModel, ClassModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

def cosine_similarity_search(embedded_query: list[float], db: Session):
    try:
        cosine_distance = FunctionModel.vector.cosine_distance(embedded_query)
        similarity_score = (1 - cosine_distance).label("similarity_score")

        stmt = (
            select(FunctionModel, similarity_score)
            .order_by(cosine_distance)
            .limit(10)
        )
        results = db.execute(stmt).all()

        chunks = []
        for result, similarity_score in results:
            chunk = {
                "id": result.id,
                "fqn": result.entity_fqn,
                "text": result.raw_code_text,
                "similarity_score": float(similarity_score),
                "parent_fqn": result.parent_fqn,
                "parent_class_fqn": result.parent_class_fqn,
                "filename": result.filename,
                "start_line": result.start_line,
                "end_line": result.end_line,
                "type": "function"
            }
            chunks.append(chunk)
        return chunks
    except SQLAlchemyError as db_err:
        logger.error(f"Database failed during initial similarity search: {db_err}")
        raise db_err


def fetch_classes(class_fqn_set: set[str], db: Session):
    try:
        stmt = (
            select(ClassModel)
            .where(ClassModel.fqn.in_(class_fqn_set))
        )

        results = db.execute(stmt).scalars().all()

        chunks = []
        for result in results:
            chunk = {
                "id": result.id,
                "fqn": result.fqn,
                "skeleton_text": result.skeleton_text,
                "filename": result.filename,
                "start_line": result.start_line,
                "end_line": result.end_line,
                "type": "class"
            }
            chunks.append(chunk)
        return chunks
    except SQLAlchemyError as db_err:
            logger.error(f"Database failed during class fetching: {db_err}")
            raise db_err

