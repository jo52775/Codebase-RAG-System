import { fallbackCatalog } from '../data/repositories'
import type { RepositoryOption } from '../types'
import { isRecord } from './guards'
import { normalizeRepositories } from './normalizeRepositories'

/**
 * HTTP entry point for the UI.
 *
 * The dev server proxies `/api` to the FastAPI app. Set `VITE_API_BASE_URL`
 * to call a different origin.
 *
 * To add an endpoint, add a path to `endpoints` and a function beside `submitQuery`.
 * To change the query payload, edit `buildQueryBody` only.
 * To change how a response is read, edit `normalizeQuery.ts`.
 */
const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

export const endpoints = {
  query: '/query/',
  repos: '/repo',
} as const

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  signal?: AbortSignal
}

export async function apiRequest(path: string, options: RequestOptions = {}): Promise<unknown> {
  const response = await fetch(`${baseUrl}${path}`, {
    method: options.method ?? 'GET',
    headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  })

  if (!response.ok) {
    const detail = messageFromErrorBody(await readJson(response), response.status)
    throw new ApiError(response.status, detail)
  }

  return response.json()
}

export interface QuerySubmission {
  text: string
  repositoryId: string
}

/**
 * Body for POST /api/query/.
 * The live API reads `text`. `repository_id` is the selected repository
 * from GET /repo. Pydantic ignores unknown fields until the payload uses it.
 */
export function buildQueryBody(input: QuerySubmission): Record<string, unknown> {
  return {
    text: input.text,
    repository_id: input.repositoryId,
  }
}

/**
 * GET /api/repo. Repositories arrive with their suggested queries nested.
 * Until that route exists, the hardcoded catalog is used.
 */
export async function fetchRepositories(signal?: AbortSignal): Promise<RepositoryOption[]> {
  try {
    const payload = await apiRequest(endpoints.repos, { signal })
    const repositories = normalizeRepositories(payload)
    if (repositories.length > 0) return repositories
  } catch (error) {
    if (isAbort(error)) throw error
  }
  return normalizeRepositories(fallbackCatalog)
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

export function submitQuery(input: QuerySubmission, signal?: AbortSignal): Promise<unknown> {
  return apiRequest(endpoints.query, {
    method: 'POST',
    body: buildQueryBody(input),
    signal,
  })
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function messageFromErrorBody(body: unknown, status: number): string {
  if (!isRecord(body)) return `Request failed (${status}).`
  const { detail } = body
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (isRecord(item) && typeof item.msg === 'string' ? item.msg : null))
      .filter((item): item is string => item !== null)
    if (messages.length > 0) return messages.join(' ')
  }
  return `Request failed (${status}).`
}
