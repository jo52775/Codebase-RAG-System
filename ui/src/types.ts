export interface CodeChunk {
  id: string
  name: string
  filename: string
  startLine: number | null
  endLine: number | null
  code: string
  kind: 'function' | 'class' | null
}

export interface Lexeme {
  token: string
  weight: string | null
}

export interface LexicalBreakdown {
  tsquery: string | null
  lexemes: Lexeme[]
}

export interface SuggestedQuery {
  id: string
  repoId: string
  text: string
}

export interface RepositoryOption {
  id: string
  name: string
  githubUrl: string
  suggestions: SuggestedQuery[]
}

/** Stable shape the screen renders. The API adapter fills this from the wire payload. */
export interface QueryResult {
  answer: string | null
  chunks: CodeChunk[]
  reranked: boolean | null
  vector: number[] | null
  lexical: LexicalBreakdown | null
}
