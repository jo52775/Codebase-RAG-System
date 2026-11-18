import { useEffect, useId, useRef, useState } from 'react'
import { displayGithubUrl, thisRepository } from '../data/repositories'
import type { RepositoryOption } from '../types'
import { ChevronIcon, GithubIcon } from './Icons'
import './Navbar.css'

interface NavbarProps {
  repositories: RepositoryOption[]
  selectedId: string
  onSelect: (id: string) => void
}

export function Navbar({ repositories, selectedId, onSelect }: NavbarProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const menuId = useId()
  const selected = repositories.find((repository) => repository.id === selectedId)

  useEffect(() => {
    if (!open) return
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  return (
    <aside className="navbar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <span />
          <span />
        </span>
        <span>
          <strong>Codebase RAG</strong>
          <em>Query interface</em>
        </span>
      </div>

      <div className="repo-select" ref={rootRef}>
        <p className="nav-label" id={`${menuId}-label`}>
          Repository
        </p>
        <div className="repo-control">
          <button
            type="button"
            className="repo-trigger"
            aria-expanded={open}
            aria-controls={menuId}
            onClick={() => setOpen((value) => !value)}
          >
            <span>{selected?.name ?? thisRepository.name}</span>
            <ChevronIcon />
          </button>
          {open && (
          <ul className="repo-menu" id={menuId} aria-labelledby={`${menuId}-label`}>
            {repositories.map((repository) => {
              const isSelected = repository.id === selectedId
              return (
                <li key={repository.id} className={isSelected ? 'is-selected' : undefined}>
                  <button
                    type="button"
                    aria-current={isSelected ? 'true' : undefined}
                    onClick={() => {
                      onSelect(repository.id)
                      setOpen(false)
                    }}
                  >
                    {repository.name}
                  </button>
                  {repository.githubUrl ? (
                    <a
                      href={repository.githubUrl}
                      target="_blank"
                      rel="noreferrer"
                      title={repository.githubUrl}
                      onClick={(event) => event.stopPropagation()}
                    >
                      {displayGithubUrl(repository.githubUrl)}
                    </a>
                  ) : (
                    <span className="url-missing">Add GitHub URL</span>
                  )}
                </li>
              )
            })}
          </ul>
          )}
        </div>
        <p className="repo-hint">Queries run against the selected repository.</p>
      </div>

      <div className="navbar-spacer" />

      <a
        className="project-link"
        href={thisRepository.githubUrl}
        target="_blank"
        rel="noreferrer"
        title={thisRepository.githubUrl}
      >
        <GithubIcon />
        <span>
          <span className="project-link-label">This repository</span>
          <span className="project-link-url">
            {thisRepository.githubUrl
              ? displayGithubUrl(thisRepository.githubUrl)
              : 'Add GitHub URL'}
          </span>
        </span>
      </a>
    </aside>
  )
}
