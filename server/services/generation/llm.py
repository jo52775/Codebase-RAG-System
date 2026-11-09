from openai import OpenAI
class Generative_LLM:
    def __init__(self):
        self.model_name = "gpt-6-luna"
        self.encoding_scheme = "o200k_base"
        self.token_limit = 5000
        self.system_prompt = """You are a specialized generative AI assistant for a Python Codebase RAG System. 
                        Your sole job is to generate an accurate, concise technical response answering the user's query.

                        CRITICAL CONSTRAINTS:
                        1. Base your answer STRICTLY on the provided code chunks and metadata below. Do NOT use external knowledge.
                        2. Do NOT make assumptions or extrapolate beyond what is explicitly shown in the code context.
                        3. If the provided information is absolutely insufficient to answer the query, explicitly state: "The provided codebase context is insufficient to answer this query."
                        4. Keep the answer summary under 1,000 tokens.
                        5. Do not include raw code blocks or code snippets in your response. 
                        Instead, describe the logic, behavior, and implementation entirely in clear prose, 
                        explicitly referencing the names of relevant classes, functions, and variables to explain how they work."""
        self.user_prompt = """User Query: "{query}"

                        Retrieved Codebase Context:
                        {formatted_chunks}

                        Please analyze the context above and provide your response in the required format."""

    def generate_response(self):
        try:
            client = OpenAI()
            response = client.responses.create(
                model=self.model_name, instructions=self.system_prompt, input=self.user_prompt
            )
            return response.output_text
        except Exception as e:
            raise e