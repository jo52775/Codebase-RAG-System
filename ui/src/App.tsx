import { useEffect, useRef, useState } from 'react'
import { ApiError, fetchRepositories, submitQuery } from './api/client'
import { defaultRepositoryId, normalizeRepositories } from './api/normalizeRepositories'
import { normalizeQueryResponse } from './api/normalizeQuery'
import { Navbar } from './components/Navbar'
import { QueryError, Results } from './components/Results'
import { SearchPanel } from './components/SearchPanel'
import { QUERY_LIMIT } from './constants'
import { displayGithubUrl, fallbackCatalog, thisRepository } from './data/repositories'
import type { QueryResult, RepositoryOption } from './types'
import './App.css'

type Phase = 'compose' | 'loading' | 'results' | 'error'

interface RepoNotice {
  token: number
  message: string
}

const initialRepositories = normalizeRepositories(fallbackCatalog)

function App() {
  const [repositoryList, setRepositoryList] = useState<RepositoryOption[]>(initialRepositories)
  const [repositoryId, setRepositoryId] = useState(defaultRepositoryId(initialRepositories))
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [phase, setPhase] = useState<Phase>('compose')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [notice, setNotice] = useState<RepoNotice | null>(null)
  const [focusToken, setFocusToken] = useState(0)
  const abortRef = useRef<AbortController | null>(null)
  const requestRef = useRef(0)

  const repository = repositoryList.find((item) => item.id === repositoryId) ?? repositoryList[0]

  useEffect(() => {
    const controller = new AbortController()
    fetchRepositories(controller.signal)
      .then((next) => {
        setRepositoryList(next)
        setRepositoryId((current) =>
          next.some((item) => item.id === current) ? current : defaultRepositoryId(next),
        )
      })
      .catch((error: unknown) => {
        if (!isAbort(error)) return
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!notice) return
    const timeout = window.setTimeout(() => setNotice(null), 5200)
    return () => window.clearTimeout(timeout)
  }, [notice])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [phase])

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  async function ask(text: string) {
    const trimmed = text.trim()
    if (!trimmed || phase === 'loading') return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const requestId = requestRef.current + 1
    requestRef.current = requestId

    setQuery(trimmed.slice(0, QUERY_LIMIT))
    setSubmittedQuery(trimmed)
    setPhase('loading')
    setErrorMessage('')

    try {
      const payload = await submitQuery(
        { text: trimmed, repositoryId: repository?.id ?? repositoryId },
        controller.signal,
      )
      if (requestId !== requestRef.current) return
      setResult(normalizeQueryResponse(payload))
      setPhase('results')
    } catch (error) {
      if (requestId !== requestRef.current || isAbort(error)) return
      setResult(null)
      setErrorMessage(messageFor(error))
      setPhase('error')
    }
  }

  function restoreComposer() {
    requestRef.current += 1
    setQuery('')
    setPhase('compose')
    setResult(null)
    setErrorMessage('')
    setFocusToken((token) => token + 1)
  }

  function changeRepository(id: string) {
    if (id === repositoryId) return
    const next = repositoryList.find((item) => item.id === id)
    if (!next) return
    abortRef.current?.abort()
    requestRef.current += 1
    setRepositoryId(id)
    setPhase('compose')
    setResult(null)
    setErrorMessage('')
    setNotice({
      token: requestRef.current,
      message: `Repository changed. Queries now run against ${next.name}.`,
    })
    setFocusToken((token) => token + 1)
  }

  const showResults = phase === 'results' || phase === 'error'

  return (
    <div className="app">
      <Navbar
        repositories={repositoryList}
        selectedId={repository?.id ?? repositoryId}
        onSelect={changeRepository}
      />
      <main className="main">
        <div className={showResults ? 'stage is-results' : 'stage'}>
          <div className={phase === 'results' ? 'column is-wide' : 'column'}>
            <RepositoryStatus
              name={repository?.name ?? thisRepository.name}
              githubUrl={repository?.githubUrl ?? thisRepository.githubUrl}
              notice={notice}
            />
            {phase === 'results' && result ? (
              <Results query={submittedQuery} result={result} onTryAnother={restoreComposer} />
            ) : phase === 'error' ? (
              <QueryError message={errorMessage} onTryAnother={restoreComposer} />
            ) : (
              <SearchPanel
                value={query}
                locked={phase === 'loading'}
                repositoryName={repository?.name ?? thisRepository.name}
                suggestions={repository?.suggestions ?? []}
                focusToken={focusToken}
                onChange={setQuery}
                onSubmit={ask}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function RepositoryStatus({
  name,
  githubUrl,
  notice,
}: {
  name: string
  githubUrl: string
  notice: RepoNotice | null
}) {
  return (
    <div className="repo-status">
      <div key={notice?.token ?? 'steady'} className={notice ? 'repo-chip is-live' : 'repo-chip'}>
        <span className="repo-dot" aria-hidden="true" />
        <span>Querying</span>
        <strong>{name}</strong>
        {githubUrl ? (
          <a href={githubUrl} target="_blank" rel="noreferrer">
            {displayGithubUrl(githubUrl)}
          </a>
        ) : null}
      </div>
      {notice ? (
        <div className="repo-banner" role="status">
          {notice.message}
        </div>
      ) : null}
    </div>
  )
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

function messageFor(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof TypeError) return 'The server could not be reached. Check that the API is running.'
  return 'The query could not be completed.'
}

export default App
