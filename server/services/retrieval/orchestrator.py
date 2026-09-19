from loguru import logger
from sqlalchemy.orm import Session
from services.retrieval.embedder import embed_user_query
from services.retrieval.searcher import cosine_similarity_search, fetch_classes

def retrieval_orchestrator(user_query_text: str, db: Session):
    try:
        embedded_query = embed_user_query(user_query_text)
        print('Embedded Query: ', embedded_query)

        chunks = cosine_similarity_search(embedded_query, db)
        candidates = [chunk for chunk in chunks if chunk["similarity_score"] >= 0.20]

        if(len(candidates) == 0):
            return []

        class_fqns = set([candidate["parent_class_fqn"] for candidate in candidates])
        if len(class_fqns) == 0: 
            return candidates
        class_chunks = fetch_classes(class_fqns, db)
        candidates.extend(class_chunks)
        return candidates
    except Exception as e:
        logger.error(f"RAG process failed at retrieval step!")
        raise e


    
