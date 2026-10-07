from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from services.retrieval.query_transformer import user_query_to_tsquery, embed_user_query
from services.retrieval.searcher import lexical_similarity_search, semantic_similarity_search, fetch_classes
from services.retrieval.candidate_selector import kneedle_algorithm

def retrieval_orchestrator(user_query_text: str, db: Session):
    try:
        lexical_candidates = []
        semantic_candidates = []

        # TEXT (LEXICAL) SIMILARITY SEARCH
        tsquery = user_query_to_tsquery(user_query_text)

        output_string = db.scalar(select(tsquery))
        print(f"Raw Input: {user_query_text}")
        print(f"TSQuery Output: {output_string}")

        lexical_candidates = lexical_similarity_search(tsquery, db)

        # VECTOR (SEMANTIC) SIMILARITY SEARCH
        embedded_query = embed_user_query(user_query_text)
        semantic_candidates = semantic_similarity_search(embedded_query, db)

        # APPLY KNEEDLE ALGORITHM
        new_lexical_candidates = kneedle_algorithm(lexical_candidates)
        new_semantic_candidates = kneedle_algorithm(semantic_candidates)

        return {"new lexical_candidates": new_lexical_candidates, "new semantic_candidates": new_semantic_candidates}
    except Exception as e:
        logger.error(f"RAG process failed at retrieval step: ", e)
        raise e


    
