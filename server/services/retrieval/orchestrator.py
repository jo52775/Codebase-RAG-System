from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from services.retrieval.query_transformer import user_query_to_tsquery, embed_user_query
from services.retrieval.searcher import lexical_similarity_search, semantic_similarity_search, fetch_classes

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
        chunks = semantic_similarity_search(embedded_query, db)
        semantic_candidates = [chunk for chunk in chunks if chunk["similarity_score"] >= 0.20]

        if(len(semantic_candidates) > 0):
            class_fqns = set([candidate["parent_class_fqn"] for candidate in semantic_candidates])
            class_chunks = fetch_classes(class_fqns, db)
            semantic_candidates.extend(class_chunks)

        return {"lexical_candidates": lexical_candidates, "semantic_candidates": semantic_candidates}
    except Exception as e:
        logger.error(f"RAG process failed at retrieval step!")
        raise e


    
