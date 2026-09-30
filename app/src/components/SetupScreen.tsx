import { useMemo } from 'react'
import type { TeamsFile, VersionInfo } from '../data/types'
import type { LoadResult } from '../data/useData'
import { groupTeamsByLeague } from '../lib/teams'
import { ClubPicker } from './ClubPicker'
import styles from './SetupScreen.module.css'
import { StatusMessage } from './StatusMessage'

interface Props {
  versions: VersionInfo[]
  versionId: number | null
  onVersionChange: (id: number) => void
  teams: LoadResult<TeamsFile>
  teamAId: number | null
  teamBId: number | null
  onTeamAChange: (id: number) => void
  onTeamBChange: (id: number) => void
  onStart: () => void
}

export function SetupScreen({
  versions,
  versionId,
  onVersionChange,
  teams,
  teamAId,
  teamBId,
  onTeamAChange,
  onTeamBChange,
  onStart,
}: Props) {
  const version = versions.find((v) => v.id === versionId)
  const teamList = teams.status === 'ready' ? teams.data.teams : null
  const groups = useMemo(
    () => (teamList && version ? groupTeamsByLeague(teamList, version.leagues) : []),
    [teamList, version],
  )
  const canStart = teams.status === 'ready' && teamAId !== null && teamBId !== null && teamAId !== teamBId

  return (
    <main className={styles.screen}>
      <header className={styles.header}>
        <h1 className={styles.title}>OG Squad Compare</h1>
        <p className={styles.subtitle}>
          Pick a game and two clubs. Guess which player had the higher rating, slot by slot.
        </p>
      </header>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault()
          if (canStart) onStart()
        }}
      >
        <div className={styles.field}>
          <label htmlFor="version-select" className={styles.label}>
            Game version
          </label>
          <select
            id="version-select"
            className={styles.select}
            value={versionId ?? ''}
            onChange={(e) => onVersionChange(Number(e.target.value))}
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
          </select>
        </div>

        {teams.status === 'loading' && <StatusMessage kind="loading" message="Loading clubs…" inline />}
        {teams.status === 'error' && (
          <StatusMessage kind="error" message={teams.message} onRetry={teams.retry} inline />
        )}
        {teams.status === 'ready' && (
          <>
            {/* Keyed by version so an open picker and its search reset when the version changes */}
            <ClubPicker
              key={`a-${versionId}`}
              label="Team A"
              groups={groups}
              selectedId={teamAId}
              takenId={teamBId}
              takenBy="Team B"
              onSelect={onTeamAChange}
            />
            <ClubPicker
              key={`b-${versionId}`}
              label="Team B"
              groups={groups}
              selectedId={teamBId}
              takenId={teamAId}
              takenBy="Team A"
              onSelect={onTeamBChange}
            />
          </>
        )}

        <button type="submit" className={styles.start} disabled={!canStart}>
          Start
        </button>
      </form>
    </main>
  )
}
