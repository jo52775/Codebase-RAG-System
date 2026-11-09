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
            .limit(20)
        )
    
        class_results = db.execute(class_stmt).all()
        func_results = db.execute(func_stmt).all()
    
        candidates = []
    
        for item, rank_score in class_results:
            candidates.append({
                "id": item.id,
                "name": item.entity_name,
                "fqn": item.fqn,  
                "text": item.skeleton_text,
                "score": rank_score,
                "filename": item.filename,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "type": "class",
            })

        for item, rank_score in func_results:
            candidates.append({
                "id": item.id,
                "name": item.entity_name,
                "fqn": item.entity_fqn,
                "text": item.raw_code_text,
                "score": rank_score,
                "parent_fqn": item.parent_fqn,
                "parent_class_fqn": item.parent_class_fqn,
                "filename": item.filename,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "type": "function",
            })
    
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates
    except SQLAlchemyError as db_err:
            logger.error(f"Database failed during lexical similarity search: {db_err}")
            raise db_err


def semantic_similarity_search(embedded_query: list[float], db: Session):
  try:
    func_distance = FunctionModel.semantic_search_vector.cosine_distance(embedded_query)
    func_score = (1 - func_distance).label("similarity_score")
    func_stmt = (select(FunctionModel, func_score).order_by(func_distance).limit(20))
    func_results = db.execute(func_stmt).all()

    class_distance = ClassModel.semantic_search_vector.cosine_distance(embedded_query)
    class_score = (1 - class_distance).label("similarity_score")
    class_stmt = select(ClassModel, class_score).order_by(class_distance).limit(20)
    class_results = db.execute(class_stmt).all()

    chunks = []
    for result, score in func_results:
      chunks.append({
          "id": result.id,
          "name": result.entity_name,
          "fqn": result.entity_fqn,
          "text": result.raw_code_text,
          "score": float(score),
          "parent_fqn": getattr(result, "parent_fqn", None),
          "parent_class_fqn": getattr(result, "parent_class_fqn", None),
          "filename": result.filename,
          "start_line": result.start_line,
          "end_line": result.end_line,
          "type": "function",
      })

    for result, score in class_results:
      chunks.append({
          "id": result.id,
          "name": result.entity_name,
          "fqn": result.fqn,  
          "text": result.raw_code_text,
          "score": float(score),
          "parent_fqn": None,  
          "parent_class_fqn": None,
          "filename": result.filename,
          "start_line": result.start_line,
          "end_line": result.end_line,
          "type": "class",
      })

    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks[:20]
  except SQLAlchemyError as db_err:
    logger.error(
        f"Database failed during semantic similarity search for functions and"
        f" classes: {db_err}"
    )
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

