import { useId, useMemo } from 'react'
import type { TeamsFile, VersionInfo } from '../data/types'
import type { LoadResult } from '../data/useData'
import type { Side } from '../game/game'
import { groupTeamsByLeague } from '../lib/teams'
import { ClubPicker } from './ClubPicker'
import { Footer } from './Footer'
import styles from './SetupScreen.module.css'
import { StatusMessage } from './StatusMessage'

export interface TeamPick {
  versionId: number | null
  teamId: number | null
}

interface Props {
  versions: VersionInfo[]
  pickA: TeamPick
  pickB: TeamPick
  teamsA: LoadResult<TeamsFile>
  teamsB: LoadResult<TeamsFile>
  onPickAChange: (pick: TeamPick) => void
  onPickBChange: (pick: TeamPick) => void
  onStart: () => void
}

// The same club is blocked only when both sides use the same version (D30)
function isSameClub(a: TeamPick, b: TeamPick): boolean {
  return a.teamId !== null && a.teamId === b.teamId && a.versionId === b.versionId
}

export function SetupScreen({ versions, pickA, pickB, teamsA, teamsB, onPickAChange, onPickBChange, onStart }: Props) {
  const canStart =
    teamsA.status === 'ready' &&
    teamsB.status === 'ready' &&
    pickA.teamId !== null &&
    pickB.teamId !== null &&
    !isSameClub(pickA, pickB)

  return (
    <main className={styles.screen}>
      <header className={styles.header}>
        <h1 className={styles.title}>OG Squad Compare</h1>
        <p className={styles.subtitle}>
          Pick two clubs, each from any game. Guess which player had the higher rating, slot by slot.
        </p>
      </header>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault()
          if (canStart) onStart()
        }}
      >
        <TeamSetup
          side="A"
          versions={versions}
          pick={pickA}
          otherPick={pickB}
          teams={teamsA}
          onChange={onPickAChange}
        />
        <TeamSetup
          side="B"
          versions={versions}
          pick={pickB}
          otherPick={pickA}
          teams={teamsB}
          onChange={onPickBChange}
        />

        <button type="submit" className={styles.start} disabled={!canStart}>
          Start
        </button>
      </form>
      <Footer />
    </main>
  )
}

interface TeamSetupProps {
  side: Side
  versions: VersionInfo[]
  pick: TeamPick
  otherPick: TeamPick
  teams: LoadResult<TeamsFile>
  onChange: (pick: TeamPick) => void
}

function TeamSetup({ side, versions, pick, otherPick, teams, onChange }: TeamSetupProps) {
  const selectId = useId()
  const label = `Team ${side}`
  const otherLabel = `Team ${side === 'A' ? 'B' : 'A'}`
  const version = versions.find((v) => v.id === pick.versionId)
  const teamList = teams.status === 'ready' ? teams.data.teams : null
  const groups = useMemo(
    () => (teamList && version ? groupTeamsByLeague(teamList, version.leagues) : []),
    [teamList, version],
  )
  // A club is taken only if the other side picked it in the same version
  const takenId = otherPick.versionId === pick.versionId ? otherPick.teamId : null

  return (
    <fieldset className={`${styles.team} ${side === 'A' ? styles.teamA : styles.teamB}`}>
      <legend className={styles.legend}>
        <span className={styles.marker} aria-hidden="true" />
        {label}
      </legend>

      <div className={styles.field}>
        <label htmlFor={selectId} className={styles.label}>
          Game version
        </label>
        <select
          id={selectId}
          className={styles.select}
          value={pick.versionId ?? ''}
          // Changing this team's version clears only this team's club
          onChange={(e) => onChange({ versionId: Number(e.target.value), teamId: null })}
        >
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              {v.label}
            </option>
          ))}
        </select>
      </div>

      {teams.status === 'loading' && <StatusMessage kind="loading" message="Loading clubs…" inline />}
      {teams.status === 'error' && <StatusMessage kind="error" message={teams.message} onRetry={teams.retry} inline />}
      {teams.status === 'ready' && (
        <ClubPicker
          // Keyed by version so an open picker and its search reset when the version changes
          key={pick.versionId}
          label="Club"
          owner={label}
          groups={groups}
          selectedId={pick.teamId}
          takenId={takenId}
          takenBy={otherLabel}
          onSelect={(teamId) => onChange({ versionId: pick.versionId, teamId })}
        />
      )}
    </fieldset>
  )
}
