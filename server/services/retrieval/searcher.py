from loguru import logger
from sqlalchemy.orm import Session
from database.models.chunk import FunctionModel, ClassModel
from sqlalchemy import desc, select, func, text
from sqlalchemy.exc import SQLAlchemyError

def lexical_similarity_search(ts_query, db: Session):
    try:
        class_rank = func.ts_rank(
            text("'{0.1, 0.2, 0.4, 1.0}'::float4[]"),
            ClassModel.text_search_vector,
            ts_query
        ).label("rank")
    
        func_rank = func.ts_rank(
            text("'{0.1, 0.2, 0.4, 1.0}'::float4[]"),
            FunctionModel.text_search_vector,
            ts_query
        ).label("rank")
    
        class_stmt = (
            select(ClassModel, class_rank)
            .where(ClassModel.text_search_vector.op("@@")(ts_query))
            .order_by(desc(class_rank))
            .limit(10)
        )
    
        func_stmt = (
            select(FunctionModel, func_rank)
            .where(FunctionModel.text_search_vector.op("@@")(ts_query))
            .order_by(desc(func_rank))
            .limit(10)
        )
    
        class_results = db.execute(class_stmt).all()
        func_results = db.execute(func_stmt).all()
    
        candidates = []
    
        for item, rank_score in class_results:
            candidates.append({
                "type": "class",
                "model_obj": item,
                "rank_score": rank_score,
            })
    
        for item, rank_score in func_results:
            candidates.append({
                "type": "function",
                "model_obj": item,
                "rank_score": rank_score,
            })
    
        candidates.sort(key=lambda x: x["rank_score"], reverse=True)
        return candidates
    except SQLAlchemyError as db_err:
            logger.error(f"Database failed during lexical similarity search: {db_err}")
            raise db_err


def semantic_similarity_search(embedded_query: list[float], db: Session):
    try:
        cosine_distance = FunctionModel.semantic_search_vector.cosine_distance(embedded_query)
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
        logger.error(f"Database failed during semantic similarity search: {db_err}")
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

