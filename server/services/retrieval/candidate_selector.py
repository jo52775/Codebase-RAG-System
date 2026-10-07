from loguru import logger
import numpy as np
from kneed import KneeLocator

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

    
        