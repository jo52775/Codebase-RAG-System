/** Stand-in queries used until GET /repo returns its own list. */
export const fallbackSuggestedQueries = [
  {
    id: 'retrieval',
    repo_id: 'codebase-rag-system',
    query_text:
      'How does retrieval combine lexical search and semantic search before an answer is generated?',
  },
  {
    id: 'chunks',
    repo_id: 'codebase-rag-system',
    query_text: 'What metadata is stored with each function and class chunk?',
  },
  {
    id: 'lexical',
    repo_id: 'codebase-rag-system',
    query_text: 'How is a user question converted into a PostgreSQL tsquery?',
  },
  {
    id: 'ranking',
    repo_id: 'codebase-rag-system',
    query_text: 'What happens to candidate chunks when the reranker model is unavailable?',
  },
]
