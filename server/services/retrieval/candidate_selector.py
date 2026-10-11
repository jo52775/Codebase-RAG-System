from loguru import logger
import numpy as np
from kneed import KneeLocator
from sentence_transformers import CrossEncoder

def kneedle_algorithm(candidates: list[dict]) -> list[dict]:
    try:
        if len(candidates) <= 2:
            return candidates
        
        y = np.array([c["score"] for c in candidates], dtype=np.float64)
        x = np.arange(len(y), dtype=np.float64)

        knee_point = KneeLocator(x, y, curve="convex", direction="decreasing")

        logger.debug(f"Knee X: {knee_point.knee}, Knee Y: {knee_point.knee_y}")

        if knee_point.knee is None:
            return candidates

        cutoff_point = int(knee_point.knee)
        return candidates[: cutoff_point + 1]

    except Exception as e:
        logger.error(f"Error in Kneedle algorithm: {e}")
        raise e

def return_unique_candidates(candidates: list[dict]):
    unique_candidates = []
    unique_candidate_IDs = set()

    for c in candidates:
        candidate_id = c["id"]
        if candidate_id not in unique_candidate_IDs:
            unique_candidate_IDs.add(candidate_id)
            unique_candidates.append(c)
    return unique_candidates

def rerank_candidates(query: str, candidates: list[dict], reranker: CrossEncoder):
    try:
        if len(candidates) == 0:
            return candidates

        documents = [
            f"# File: {c.get('filename', '')}\n"
            f"# Symbol: {c.get('name', '')}\n\n"
            f"{c.get('text', '')}"
            for c in candidates
        ]

        ranked_results = reranker.rank(
        query=query,
        documents=documents,
        top_k=10,
        return_documents=False 
        )

        print("RANKED RESULTS: ", ranked_results)

        final_candidates = []
        for item in ranked_results:
            idx = item['corpus_id']
            candidate = candidates[idx]
            final_candidates.append(candidate)

        return final_candidates

    except Exception as e:
       logger.error(f"Error in re-ranking step: {e}")

        


    
        