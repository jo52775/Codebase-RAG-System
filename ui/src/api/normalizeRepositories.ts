import { isRecord } from './guards'
import type { RepositoryOption, SuggestedQuery } from '../types'

/**
 * Maps GET /repo onto repositories with nested suggested queries.
 *
 * Expected payload:
 * `{ repositories: [{ id, name, url, suggested_queries: [{ id, repo_id, query_text }] }] }`
 *
 * Also accepted: a bare array, one repository object, or a map of repositories.
 * Query lists may be named `suggested_queries`, `suggestions`, or `queries`.
 * URLs may be `url` or `github_url`. Query text may be `query_text` or `text`.
 */
const LIST_KEYS = ['repositories', 'repos', 'data', 'results', 'items']
const QUERY_KEYS = ['suggested_queries', 'suggestedQueries', 'suggestions', 'queries']

export function normalizeRepositories(payload: unknown): RepositoryOption[] {
  return repositoryRecords(payload)
    .map((record, index) => mapRepository(record, index))
    .filter((repository): repository is RepositoryOption => repository !== null)
}

export function defaultRepositoryId(repositories: RepositoryOption[]): string {
  return (
    repositories.find((repository) => repository.name === 'Codebase-RAG-System')?.id ??
    repositories[0]?.id ??
    ''
  )
}

function repositoryRecords(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload.filter(isRecord)
  if (!isRecord(payload)) return []

  for (const key of LIST_KEYS) {
    const value = payload[key]
    if (Array.isArray(value)) return value.filter(isRecord)
  }

  if (looksLikeRepository(payload)) return [payload]

  const nested = Object.entries(payload)
    .filter((entry): entry is [string, Record<string, unknown>] => isRecord(entry[1]) && looksLikeRepository(entry[1]))
    .map(([key, record]) => ({ id: record.id ?? key, ...record }))

  return nested
}

function looksLikeRepository(record: Record<string, unknown>): boolean {
  return QUERY_KEYS.some((key) => key in record) || 'name' in record || 'url' in record || 'github_url' in record
}

function mapRepository(record: Record<string, unknown>, index: number): RepositoryOption | null {
  const id = asId(record.id) ?? `repository-${index}`
  const name = firstString(record, ['name', 'repository_name', 'repo_name'])
  if (!name) return null
  const suggestions = queryRecords(record)
    .map((query, queryIndex) => mapQuery(query, id, queryIndex))
    .filter((query): query is SuggestedQuery => query !== null)

  return {
    id,
    name,
    githubUrl: firstString(record, ['url', 'github_url', 'githubUrl']) ?? '',
    suggestions,
  }
}

function queryRecords(repository: Record<string, unknown>): Record<string, unknown>[] {
  for (const key of QUERY_KEYS) {
    const value = repository[key]
    if (Array.isArray(value)) return value.filter(isRecord)
  }
  return []
}

function mapQuery(
  record: Record<string, unknown>,
  repositoryId: string,
  index: number,
): SuggestedQuery | null {
  const text = firstString(record, ['query_text', 'text', 'query'])
  if (!text) return null
  return {
    id: asId(record.id) ?? `${repositoryId}-query-${index}`,
    repoId: asId(record.repo_id) ?? asId(record.repoId) ?? repositoryId,
    text,
  }
}

function asId(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return null
}

function firstString(record: Record<string, unknown>, keys: string[]): string | null {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return null
}
