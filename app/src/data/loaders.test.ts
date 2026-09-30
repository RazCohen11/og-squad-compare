import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { clearDataCache, DataLoadError, loadTeams, loadVersions } from './loaders'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('loaders', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    clearDataCache()
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('fetches data relative to the base URL', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse([{ id: 24 }]))
    await loadVersions()
    expect(fetchMock).toHaveBeenCalledWith(`${import.meta.env.BASE_URL}data/versions.json`)
  })

  it('caches teams per version', async () => {
    fetchMock.mockImplementation(async () => jsonResponse({ version: 24, teams: [] }))
    const first = await loadTeams(24)
    const second = await loadTeams(24)
    expect(second).toBe(first)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    await loadTeams(23)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock).toHaveBeenLastCalledWith(`${import.meta.env.BASE_URL}data/23/teams.json`)
  })

  it('surfaces a readable error and fetches again on retry', async () => {
    fetchMock.mockResolvedValueOnce(new Response('missing', { status: 404 }))
    await expect(loadTeams(24)).rejects.toThrow(new DataLoadError('Could not load the clubs for this version (HTTP 404).'))

    fetchMock.mockResolvedValueOnce(jsonResponse({ version: 24, teams: [] }))
    await expect(loadTeams(24)).resolves.toEqual({ version: 24, teams: [] })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not cache a failed request', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('network down'))
    await expect(loadVersions()).rejects.toThrow('Could not load the game versions')
    fetchMock.mockResolvedValueOnce(jsonResponse([{ id: 24 }]))
    await expect(loadVersions()).resolves.toEqual([{ id: 24 }])
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
