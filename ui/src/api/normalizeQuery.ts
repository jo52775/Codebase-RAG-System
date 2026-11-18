import { isRecord } from './guards'
import type { CodeChunk, Lexeme, LexicalBreakdown, QueryResult } from '../types'

/**
 * Maps a query response onto `QueryResult`.
 *
 * Current payload:
 * `{ llm_output, retrieved_candidates: { candidates, reranked } }`
 *
 * Also read when present, including under `retrieval`, `search`, or `debug`:
 * - semantic vector: `semantic_search_vector`, `semantic_vector`, `query_vector`, `embedding`
 * - lexemes: `lexical_search`, `lexical`, `lexeme_breakdown`, `tsquery`
 *   with `lexemes` / `tokens` / `terms`, and `tsquery` / `query`
 * - answer: `llm_output`, `llm_response`, `response`, `answer`
 * - chunks: `retrieved_candidates`, `chunks`, `candidates`
 *   chunk fields: `name`, `filename`, `start_line`, `end_line`, `text`, `type`
 */
const VECTOR_KEYS = ['semantic_search_vector', 'semantic_vector', 'query_vector', 'embedding']
const LEXICAL_KEYS = ['lexical_search', 'lexical', 'lexeme_breakdown', 'tsquery']
const ANSWER_KEYS = ['llm_output', 'llm_response', 'response', 'answer', 'output']
const CHUNK_KEYS = ['retrieved_candidates', 'chunks', 'candidates', 'results']
const NESTED_KEYS = ['retrieval', 'search', 'debug', 'retrieved_candidates']

export function normalizeQueryResponse(payload: unknown): QueryResult {
  if (!isRecord(payload)) {
    return { answer: null, chunks: [], reranked: null, vector: null, lexical: null }
  }

  return {
    answer: extractAnswer(payload),
    chunks: extractChunks(payload),
    reranked: extractReranked(payload),
    vector: extractVector(payload),
    lexical: extractLexical(payload),
  }
}

function contexts(root: Record<string, unknown>): Record<string, unknown>[] {
  const records = [root]
  for (const key of NESTED_KEYS) {
    const value = root[key]
    if (isRecord(value)) records.push(value)
  }
  return records
}

function pick(record: Record<string, unknown>, keys: string[]): unknown {
  for (const key of keys) {
    if (record[key] != null) return record[key]
  }
  return undefined
}

function extractAnswer(root: Record<string, unknown>): string | null {
  for (const record of contexts(root)) {
    const value = pick(record, ANSWER_KEYS)
    if (typeof value === 'string' && value.trim()) return value
    if (isRecord(value)) {
      const nested = firstString(value, ['text', 'content', 'output_text', 'message'])
      if (nested) return nested
    }
  }
  return null
}

function extractReranked(root: Record<string, unknown>): boolean | null {
  for (const record of contexts(root)) {
    if (typeof record.reranked === 'boolean') return record.reranked
  }
  return null
}

function extractVector(root: Record<string, unknown>): number[] | null {
  for (const record of contexts(root)) {
    const vector = asVector(pick(record, VECTOR_KEYS))
    if (vector && vector.length > 0) return vector
  }
  return null
}

function extractLexical(root: Record<string, unknown>): LexicalBreakdown | null {
  for (const record of contexts(root)) {
    const lexical = asLexical(pick(record, LEXICAL_KEYS))
    if (lexical) return lexical
  }
  return null
}

function extractChunks(root: Record<string, unknown>): CodeChunk[] {
  const fromRoot = chunkList(pick(root, CHUNK_KEYS))
  if (fromRoot.length > 0) return fromRoot
  for (const key of ['retrieval', 'search', 'debug']) {
    const nested = root[key]
    if (!isRecord(nested)) continue
    const found = chunkList(pick(nested, CHUNK_KEYS))
    if (found.length > 0) return found
  }
  return []
}

function chunkList(value: unknown): CodeChunk[] {
  const records = asChunkRecords(value)
  return records
    .map((record, index) => mapChunk(record, index))
    .filter((chunk): chunk is CodeChunk => chunk !== null)
}

function asChunkRecords(value: unknown): Record<string, unknown>[] {
  if (Array.isArray(value)) return value.filter(isRecord)
  if (!isRecord(value)) return []
  const nested = pick(value, ['candidates', 'chunks', 'results', 'items'])
  if (Array.isArray(nested)) return nested.filter(isRecord)
  return []
}

function mapChunk(record: Record<string, unknown>, index: number): CodeChunk | null {
  const code = firstCode(record)
  const name = firstString(record, ['name', 'entity_name', 'function_name', 'fqn'])
  if (!name && !code) return null
  const kindText = firstString(record, ['type', 'kind'])?.toLowerCase() ?? null
  const kind = kindText === 'function' || kindText === 'class' ? kindText : null
  return {
    id: firstString(record, ['id']) ?? `chunk-${index}`,
    name: name ?? 'Untitled chunk',
    filename: firstString(record, ['filename', 'file', 'path']) ?? 'Unknown file',
    startLine: firstNumber(record, ['start_line', 'startLine', 'line_start']),
    endLine: firstNumber(record, ['end_line', 'endLine', 'line_end']),
    code: code ?? '',
    kind,
  }
}

function asVector(value: unknown): number[] | null {
  if (Array.isArray(value)) {
    const numbers = value.filter((item): item is number => typeof item === 'number' && Number.isFinite(item))
    if (numbers.length === value.length) return numbers
    return null
  }
  if (isRecord(value)) return asVector(pick(value, ['values', 'vector', 'embedding', 'data']))
  return null
}

function asLexical(value: unknown): LexicalBreakdown | null {
  if (typeof value === 'string' && value.trim()) {
    return { tsquery: value.trim(), lexemes: lexemesFromQuery(value) }
  }
  if (Array.isArray(value)) {
    const lexemes = value.map(asLexeme).filter((item): item is Lexeme => item !== null)
    return lexemes.length > 0 ? { tsquery: null, lexemes } : null
  }
  if (!isRecord(value)) return null

  const tsquery = firstString(value, ['tsquery', 'query', 'ts_query', 'output'])
  const rawLexemes = pick(value, ['lexemes', 'tokens', 'terms', 'breakdown'])
  let lexemes: Lexeme[] = []
  if (Array.isArray(rawLexemes)) {
    lexemes = rawLexemes.map(asLexeme).filter((item): item is Lexeme => item !== null)
  } else if (typeof rawLexemes === 'string') {
    lexemes = lexemesFromQuery(rawLexemes)
  }
  if (lexemes.length === 0 && tsquery) lexemes = lexemesFromQuery(tsquery)
  if (!tsquery && lexemes.length === 0) return null
  return { tsquery, lexemes }
}

function asLexeme(value: unknown): Lexeme | null {
  if (typeof value === 'string' && value.trim()) return { token: value.trim(), weight: null }
  if (!isRecord(value)) return null
  const token = firstString(value, ['token', 'lexeme', 'term', 'text', 'word'])
  if (!token) return null
  return { token, weight: weightOf(value) }
}

function weightOf(record: Record<string, unknown>): string | null {
  const value = pick(record, ['weight', 'rank', 'label'])
  if (typeof value === 'string' && value.trim()) return value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return null
}

function lexemesFromQuery(query: string): Lexeme[] {
  const seen = new Set<string>()
  const lexemes: Lexeme[] = []
  for (const piece of query.split(/[|&]/)) {
    const token = piece.replace(/[!'():*<>"]/g, '').replace(/'/g, '').trim()
    const key = token.toLowerCase()
    if (!token || seen.has(key)) continue
    seen.add(key)
    lexemes.push({ token, weight: null })
  }
  return lexemes
}

function firstString(record: Record<string, unknown>, keys: string[]): string | null {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return null
}

function firstCode(record: Record<string, unknown>): string | null {
  for (const key of ['text', 'raw_code_text', 'code', 'snippet', 'skeleton_text']) {
    const value = record[key]
    if (typeof value === 'string' && value.trim()) return value
  }
  return null
}

function firstNumber(record: Record<string, unknown>, keys: string[]): number | null {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) return Number(value)
  }
  return null
}
