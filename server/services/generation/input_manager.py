from loguru import logger
import tiktoken
from services.generation.llm import Generative_LLM

def handle_llm_input(llm: Generative_LLM, user_query: str, candidates: list[dict]):
    scheme = llm.encoding_scheme
    token_limit = llm.token_limit
    system_prompt = llm.system_prompt

    encoding = tiktoken.get_encoding(scheme)
    total_token_count = 0

    system_prompt_tokens = count_tokens(system_prompt, encoding)
    user_prompt_template = (
      f'User Query: "{user_query}"\n\nRetrieved Codebase'
      " Context:\n\nPlease analyze the context above and provide your response"
      " in the required format."
    )
    user_prompt_tokens = count_tokens(user_prompt_template, encoding)
    total_token_count = system_prompt_tokens + user_prompt_tokens
    logger.info(f"Estimated token count before processing candidates: {total_token_count} tokens")

    input = []
    for idx, candidate in enumerate(candidates):
        formatted_candidate = format_candidate_for_llm(candidate)
        candidate_token_count = count_tokens(formatted_candidate, encoding)
        logger.info(f"Candidate {idx} token count: {candidate_token_count}")
        if((total_token_count + candidate_token_count) <= token_limit):
            input.append(formatted_candidate)
            total_token_count += candidate_token_count
    logger.info(f"Total token count: {total_token_count}")
    return "\n\n".join(input)

def format_candidate_for_llm(c: dict) -> str:
    return f"""<code_snippet id="{c.get('id')}">
            **File:** `{c.get('filename')}` (Lines {c.get('start_line')}-{c.get('end_line')})
            **Name:** `{c.get('name')}`
            **Symbol:** `{c.get('fqn')}`
            **Type:** {c.get('type')}

            ```python
            {c.get('text')}
            </code_snippet>"""

def count_tokens(text: str, encoding: tiktoken.Encoding):
    return len(encoding.encode(text))
   