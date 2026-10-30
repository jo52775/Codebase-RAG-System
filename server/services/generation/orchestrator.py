from typing import Any
from loguru import logger
from services.generation.input_manager import handle_llm_input
from services.generation.llm import Generative_LLM

def generation_orchestator(user_query: str, retrieval_results: Any):
    try:
        llm = Generative_LLM()
        candidates = retrieval_results.get("candidates")
        input = handle_llm_input(llm, user_query, candidates)
        llm.user_prompt = llm.user_prompt.format(query=user_query, formatted_chunks=input)
        output = llm.generate_response()
        return output

    except Exception as e:
        logger.error(f"RAG process failed at generation step: ", e)
        raise e



