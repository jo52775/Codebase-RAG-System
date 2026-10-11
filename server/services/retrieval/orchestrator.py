from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session
from services.retrieval.query_transformer import user_query_to_tsquery, embed_user_query
from services.retrieval.searcher import lexical_similarity_search, semantic_similarity_search, fetch_classes
from services.retrieval.candidate_selector import kneedle_algorithm, return_unique_candidates, rerank_candidates
from sentence_transformers import CrossEncoder

def retrieval_orchestrator(user_query_text: str, db: Session, reranker_model: CrossEncoder | None):
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

        # RE-RANKING CANDIDATES USING LOCAL CROSS-ENCODER
        if(reranker_model is None):
            # In the case that the reranker model is not available
            return {"lexical_candidates": new_lexical_candidates, 
                    "semantic_candidates": new_semantic_candidates, 
                    "reranked": False}
        else:
            unique_candidates = return_unique_candidates(new_lexical_candidates + new_semantic_candidates)
            final_ranked_candidates = rerank_candidates(user_query_text, unique_candidates, reranker_model)
            return {"candidates": final_ranked_candidates, "reranked": True}

    except Exception as e:
        logger.error(f"RAG process failed at retrieval step: ", e)
        raise e


    
