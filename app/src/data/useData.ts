import { useCallback, useEffect, useState } from 'react'
import { DataLoadError, loadTeams, loadVersions } from './loaders'
import type { TeamsFile, VersionInfo } from './types'

export type LoadState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: T }

export type LoadResult<T> = LoadState<T> & { retry: () => void }

interface Settled<A, T> {
  arg: A
  attempt: number
  state: LoadState<T>
}

function errorMessage(error: unknown): string {
  return error instanceof DataLoadError ? error.message : 'Something went wrong while loading the data.'
}

// Runs `loader(arg)` whenever `arg` changes; `arg === null` means nothing to load yet.
// `loader` must be a stable (module-level) function.
function useLoader<A, T>(arg: A | null, loader: (arg: A) => Promise<T>): LoadResult<T> {
  const [attempt, setAttempt] = useState(0)
  const [settled, setSettled] = useState<Settled<A, T> | null>(null)

  useEffect(() => {
    if (arg === null) return
    let cancelled = false
    loader(arg).then(
      (data) => {
        if (!cancelled) setSettled({ arg, attempt, state: { status: 'ready', data } })
      },
      (error: unknown) => {
        if (!cancelled) setSettled({ arg, attempt, state: { status: 'error', message: errorMessage(error) } })
      },
    )
    return () => {
      cancelled = true
    }
  }, [arg, attempt, loader])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])

  let state: LoadState<T>
  if (arg === null) state = { status: 'idle' }
  else if (settled && settled.arg === arg && settled.attempt === attempt) state = settled.state
  else state = { status: 'loading' }
  return { ...state, retry }
}

const loadVersionsOnce = () => loadVersions()

export function useVersions(): LoadResult<VersionInfo[]> {
  return useLoader(true, loadVersionsOnce)
}

export function useTeams(version: number | null): LoadResult<TeamsFile> {
  return useLoader(version, loadTeams)
}
