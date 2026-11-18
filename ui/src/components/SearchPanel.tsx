import { useEffect, useId, useRef, type FormEvent, type KeyboardEvent } from 'react'
import { QUERY_LIMIT } from '../constants'
import type { SuggestedQuery } from '../types'
import { ArrowIcon, WheelIcon } from './Icons'
import './SearchPanel.css'

interface SearchPanelProps {
  value: string
  locked: boolean
  repositoryName: string
  suggestions: SuggestedQuery[]
  focusToken: number
  onChange: (value: string) => void
  onSubmit: (value: string) => void
}

export function SearchPanel({
  value,
  locked,
  repositoryName,
  suggestions,
  focusToken,
  onChange,
  onSubmit,
}: SearchPanelProps) {
  return (
    <div className="search-panel">
      <header className="intro">
        <h1>Ask the codebase</h1>
        <p>Semantic search, lexical search, retrieved code, and a generated answer.</p>
      </header>
      <SuggestionCards suggestions={suggestions} locked={locked} onPick={onSubmit} />
      <SearchBar
        value={value}
        locked={locked}
        repositoryName={repositoryName}
        focusToken={focusToken}
        onChange={onChange}
        onSubmit={onSubmit}
      />
    </div>
  )
}

function SuggestionCards({
  suggestions,
  locked,
  onPick,
}: {
  suggestions: SuggestedQuery[]
  locked: boolean
  onPick: (value: string) => void
}) {
  if (suggestions.length === 0) return null
  return (
    <div className="suggestions" aria-label="Suggested queries">
      {suggestions.map((suggestion) => (
        <button
          key={`${suggestion.repoId}-${suggestion.id}`}
          type="button"
          className="suggestion"
          disabled={locked}
          onClick={() => onPick(suggestion.text)}
        >
          <p>{suggestion.text}</p>
        </button>
      ))}
    </div>
  )
}

function SearchBar({
  value,
  locked,
  repositoryName,
  focusToken,
  onChange,
  onSubmit,
}: Omit<SearchPanelProps, 'suggestions'>) {
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const countId = useId()
  const canSubmit = !locked && value.trim().length > 0 && value.length <= QUERY_LIMIT
  const countClass =
    value.length >= QUERY_LIMIT ? 'at-limit' : value.length >= QUERY_LIMIT - 40 ? 'near-limit' : ''

  useEffect(() => {
    const node = inputRef.current
    if (!node) return
    node.style.height = '0px'
    node.style.height = `${Math.min(node.scrollHeight, 160)}px`
  }, [value])

  useEffect(() => {
    if (locked) return
    inputRef.current?.focus()
  }, [focusToken, locked])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (canSubmit) onSubmit(value)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (canSubmit) onSubmit(value)
    }
  }

  return (
    <form
      className={locked ? 'search-bar is-locked' : 'search-bar'}
      role="search"
      onSubmit={handleSubmit}
    >
      <label className="sr-only" htmlFor="codebase-query">
        Query {repositoryName}
      </label>
      <textarea
        id="codebase-query"
        ref={inputRef}
        rows={1}
        value={value}
        maxLength={QUERY_LIMIT}
        disabled={locked}
        placeholder={`Ask ${repositoryName}`}
        aria-describedby={countId}
        onChange={(event) => onChange(event.target.value.slice(0, QUERY_LIMIT))}
        onKeyDown={handleKeyDown}
      />
      <div className="search-foot">
        <span id={countId} className={`search-count ${countClass}`.trim()}>
          {value.length} / {QUERY_LIMIT}
        </span>
        {locked ? (
          <span className="pending" role="status">
            <WheelIcon />
            Searching
          </span>
        ) : (
          <button type="submit" className="send" disabled={!canSubmit} aria-label="Search">
            <ArrowIcon />
          </button>
        )}
      </div>
    </form>
  )
}
