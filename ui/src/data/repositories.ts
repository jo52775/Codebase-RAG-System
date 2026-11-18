import { fallbackSuggestedQueries } from './suggestions'

/** This application repository. The navbar footer always links here. */
export const thisRepository = {
  name: 'Codebase-RAG-System',
  githubUrl: 'https://github.com/jo52775/Codebase-RAG-System',
}

/**
 * Nested stand-in for GET /repo.
 * Each repository carries its own suggested queries.
 */
export const fallbackCatalog = {
  repositories: [
    {
      id: 'codebase-rag-system',
      name: thisRepository.name,
      url: thisRepository.githubUrl,
      suggested_queries: fallbackSuggestedQueries,
    },
  ],
}

export function displayGithubUrl(url: string): string {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}
