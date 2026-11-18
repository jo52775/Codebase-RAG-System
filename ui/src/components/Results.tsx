import { PythonCode } from './PythonCode'
import type { QueryResult } from '../types'
import './Results.css'

interface ResultsProps {
  query: string
  result: QueryResult
  onTryAnother: () => void
}

export function Results({ query, result, onTryAnother }: ResultsProps) {
  return (
    <div className="results">
      <blockquote className="asked">
        <span>Query</span>
        <p>{query}</p>
      </blockquote>

      <SemanticVector vector={result.vector} />
      <LexemeBreakdown lexical={result.lexical} />
      <CodeChunks result={result} />
      <LlmResponse answer={result.answer} />

      <button type="button" className="try-again" onClick={onTryAnother}>
        Try Another Query
      </button>
    </div>
  )
}

export function QueryError({
  message,
  onTryAnother,
}: {
  message: string
  onTryAnother: () => void
}) {
  return (
    <div className="results">
      <div className="error-panel" role="alert">
        <h2>The query did not finish</h2>
        <p>{message}</p>
      </div>
      <button type="button" className="try-again" onClick={onTryAnother}>
        Try Another Query
      </button>
    </div>
  )
}

function SectionHeading({
  index,
  id,
  title,
  aside,
}: {
  index: string
  id: string
  title: string
  aside?: string
}) {
  return (
    <div className="section-heading">
      <h2 id={id}>
        <span>{index}</span>
        {title}
      </h2>
      {aside ? <p>{aside}</p> : null}
    </div>
  )
}

function SemanticVector({ vector }: { vector: number[] | null }) {
  const stats = vector ? vectorStats(vector) : null
  return (
    <section className="result-section" aria-labelledby="vector-heading">
      <SectionHeading
        index="01"
        id="vector-heading"
        title="Semantic search vector"
        aside={stats ? `${stats.count} dimensions` : undefined}
      />
      {vector && stats ? (
        <div className="vector-panel">
          <dl className="vector-stats">
            <div>
              <dt>Min</dt>
              <dd>{formatStat(stats.min)}</dd>
            </div>
            <div>
              <dt>Max</dt>
              <dd>{formatStat(stats.max)}</dd>
            </div>
            <div>
              <dt>Mean</dt>
              <dd>{formatStat(stats.mean)}</dd>
            </div>
            <div>
              <dt>L2 norm</dt>
              <dd>{formatStat(stats.norm)}</dd>
            </div>
          </dl>
          <VectorStrip values={vector} />
          <details className="vector-raw">
            <summary>Vector values</summary>
            <pre>{vector.map((value) => value.toFixed(4)).join('  ')}</pre>
          </details>
        </div>
      ) : (
        <p className="empty">No semantic vector was returned with this result.</p>
      )}
    </section>
  )
}

function VectorStrip({ values }: { values: number[] }) {
  const sample = magnitudeBuckets(values, 56)
  const peak = Math.max(...sample, 1e-9)
  return (
    <div className="vector-strip" aria-hidden="true">
      {sample.map((value, index) => (
        <span key={index} style={{ height: `${Math.max(6, (value / peak) * 100)}%` }} />
      ))}
    </div>
  )
}

function LexemeBreakdown({ lexical }: { lexical: QueryResult['lexical'] }) {
  const count = lexical?.lexemes.length ?? 0
  return (
    <section className="result-section" aria-labelledby="lexical-heading">
      <SectionHeading
        index="02"
        id="lexical-heading"
        title="Lexical search"
        aside={count > 0 ? `${count} ${count === 1 ? 'lexeme' : 'lexemes'}` : undefined}
      />
      {lexical && (lexical.lexemes.length > 0 || lexical.tsquery) ? (
        <div className="lexical-panel">
          {lexical.lexemes.length > 0 && (
            <ul className="lexemes">
              {lexical.lexemes.map((lexeme, index) => (
                <li key={`${lexeme.token}-${index}`}>
                  <code>{lexeme.token}</code>
                  {lexeme.weight ? <span>{lexeme.weight}</span> : null}
                </li>
              ))}
            </ul>
          )}
          {lexical.tsquery ? (
            <p className="tsquery">
              <span>tsquery</span>
              {lexical.tsquery}
            </p>
          ) : null}
        </div>
      ) : (
        <p className="empty">No lexeme breakdown was returned with this result.</p>
      )}
    </section>
  )
}

function CodeChunks({ result }: { result: QueryResult }) {
  const count = result.chunks.length
  const ranking =
    result.reranked === true ? 'Reranked' : result.reranked === false ? 'Rank fusion' : null
  const noun = count === 1 ? 'chunk' : 'chunks'
  const aside = ranking && count > 0 ? `${count} ${noun} · ${ranking}` : `${count} ${noun}`

  return (
    <section className="result-section" aria-labelledby="chunks-heading">
      <SectionHeading index="03" id="chunks-heading" title="Retrieved code chunks" aside={aside} />
      {count > 0 ? (
        <div className="chunk-list">
          {result.chunks.map((chunk, index) => (
            <article key={`${chunk.id}-${index}`} className="chunk-card">
              <header>
                <div className="chunk-title">
                  <h3>{chunk.name}</h3>
                  {chunk.kind ? <span>{chunk.kind}</span> : null}
                </div>
                <p className="chunk-meta">
                  <span className="chunk-file" title={chunk.filename}>
                    {chunk.filename}
                  </span>
                  <span>{formatLines(chunk.startLine, chunk.endLine)}</span>
                </p>
              </header>
              {chunk.code ? (
                <div className="chunk-code">
                  <PythonCode
                    code={chunk.code}
                    startingLineNumber={chunk.startLine ?? undefined}
                  />
                </div>
              ) : (
                <p className="chunk-missing">No source text on this chunk.</p>
              )}
            </article>
          ))}
        </div>
      ) : (
        <p className="empty">No code chunks were retrieved.</p>
      )}
    </section>
  )
}

function LlmResponse({ answer }: { answer: string | null }) {
  const paragraphs = answer?.split(/\n{2,}/).filter((paragraph) => paragraph.trim()) ?? []
  return (
    <section className="result-section" aria-labelledby="llm-heading">
      <SectionHeading index="04" id="llm-heading" title="LLM-generated response" />
      {paragraphs.length > 0 ? (
        <div className="answer">
          {paragraphs.map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      ) : (
        <p className="empty">No generated response was returned.</p>
      )}
    </section>
  )
}

function formatLines(start: number | null, end: number | null): string {
  if (start == null && end == null) return 'Line numbers unavailable'
  if (start != null && end != null && start !== end) return `Lines ${start}–${end}`
  if (start != null) return `Line ${start}`
  return `Line ${end}`
}

function formatStat(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : '—'
}

function vectorStats(values: number[]) {
  let min = Infinity
  let max = -Infinity
  let sum = 0
  let sumSq = 0
  for (const value of values) {
    if (value < min) min = value
    if (value > max) max = value
    sum += value
    sumSq += value * value
  }
  return {
    count: values.length,
    min,
    max,
    mean: sum / values.length,
    norm: Math.sqrt(sumSq),
  }
}

function magnitudeBuckets(values: number[], count: number): number[] {
  if (values.length === 0) return []
  const size = values.length / count
  const buckets: number[] = []
  for (let index = 0; index < count; index += 1) {
    const start = Math.floor(index * size)
    const end = Math.max(start + 1, Math.floor((index + 1) * size))
    let peak = 0
    for (let cursor = start; cursor < end && cursor < values.length; cursor += 1) {
      peak = Math.max(peak, Math.abs(values[cursor]))
    }
    buckets.push(peak)
  }
  return buckets
}
