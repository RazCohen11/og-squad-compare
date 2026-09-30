import type { TeamsFile, VersionInfo } from './types'

// Error with a message that can be shown to the user as-is
export class DataLoadError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DataLoadError'
  }
}

function dataUrl(path: string): string {
  // BASE_URL is './' with the relative base (D27), so data resolves next to index.html
  return `${import.meta.env.BASE_URL}data/${path}`
}

async function fetchJson<T>(path: string, what: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(dataUrl(path))
  } catch {
    throw new DataLoadError(`Could not load ${what}. Check your connection and try again.`)
  }
  if (!response.ok) {
    throw new DataLoadError(`Could not load ${what} (HTTP ${response.status}).`)
  }
  try {
    return (await response.json()) as T
  } catch {
    throw new DataLoadError(`The ${what} file is not valid JSON.`)
  }
}

let versionsCache: Promise<VersionInfo[]> | null = null
const teamsCache = new Map<number, Promise<TeamsFile>>()

// Loads versions.json once; a failed load is not cached, so a retry fetches again
export function loadVersions(): Promise<VersionInfo[]> {
  if (!versionsCache) {
    const request = fetchJson<VersionInfo[]>('versions.json', 'the game versions').then((versions) => {
      if (!Array.isArray(versions) || versions.length === 0) {
        throw new DataLoadError('The game versions file is empty or malformed.')
      }
      return versions
    })
    versionsCache = request
    request.catch(() => {
      if (versionsCache === request) versionsCache = null
    })
  }
  return versionsCache
}

// Loads <version>/teams.json once per version; a failed load is not cached
export function loadTeams(version: number): Promise<TeamsFile> {
  let request = teamsCache.get(version)
  if (!request) {
    request = fetchJson<TeamsFile>(`${version}/teams.json`, `the clubs for this version`).then((file) => {
      if (!file || !Array.isArray(file.teams)) {
        throw new DataLoadError('The clubs file is malformed.')
      }
      return file
    })
    teamsCache.set(version, request)
    const cached = request
    cached.catch(() => {
      if (teamsCache.get(version) === cached) teamsCache.delete(version)
    })
  }
  return request
}

// Test helper: forget all cached requests
export function clearDataCache(): void {
  versionsCache = null
  teamsCache.clear()
}
