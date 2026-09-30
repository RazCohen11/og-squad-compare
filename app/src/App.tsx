import { useMemo, useState } from 'react'
import { GameScreen } from './components/GameScreen'
import { SetupScreen, type TeamPick } from './components/SetupScreen'
import { StatusMessage } from './components/StatusMessage'
import { useTeams, useVersions } from './data/useData'
import type { GameSide } from './game/sides'
import { sortVersionsNewestFirst } from './lib/teams'

type Screen = 'setup' | 'game'

const EMPTY_PICK: TeamPick = { versionId: null, teamId: null }

export default function App() {
  const versions = useVersions()
  const [screen, setScreen] = useState<Screen>('setup')
  const [pickA, setPickA] = useState<TeamPick>(EMPTY_PICK)
  const [pickB, setPickB] = useState<TeamPick>(EMPTY_PICK)

  const versionList = versions.status === 'ready' ? versions.data : null
  const sortedVersions = useMemo(() => (versionList ? sortVersionsNewestFirst(versionList) : []), [versionList])
  // Each team defaults to the newest version (D30)
  const newestId = sortedVersions[0]?.id ?? null
  const resolvedA: TeamPick = { ...pickA, versionId: pickA.versionId ?? newestId }
  const resolvedB: TeamPick = { ...pickB, versionId: pickB.versionId ?? newestId }
  const teamsA = useTeams(resolvedA.versionId)
  const teamsB = useTeams(resolvedB.versionId)

  if (versions.status === 'loading' || versions.status === 'idle') {
    return <StatusMessage kind="loading" message="Loading game versions…" />
  }
  if (versions.status === 'error') {
    return <StatusMessage kind="error" message={versions.message} onRetry={versions.retry} />
  }

  if (screen === 'game' && teamsA.status === 'ready' && teamsB.status === 'ready') {
    const sideA = toGameSide('A', resolvedA, sortedVersions, teamsA.data.teams)
    const sideB = toGameSide('B', resolvedB, sortedVersions, teamsB.data.teams)
    if (sideA && sideB) {
      return (
        <GameScreen
          // A new matchup always starts a fresh game
          key={`${sideA.version.id}-${sideA.team.id}-${sideB.version.id}-${sideB.team.id}`}
          sideA={sideA}
          sideB={sideB}
          onBack={() => setScreen('setup')}
          onNewTeams={() => {
            // Keep both version picks, clear the clubs
            setPickA({ versionId: resolvedA.versionId, teamId: null })
            setPickB({ versionId: resolvedB.versionId, teamId: null })
            setScreen('setup')
          }}
        />
      )
    }
  }

  return (
    <SetupScreen
      versions={sortedVersions}
      pickA={resolvedA}
      pickB={resolvedB}
      teamsA={teamsA}
      teamsB={teamsB}
      onPickAChange={setPickA}
      onPickBChange={setPickB}
      onStart={() => setScreen('game')}
    />
  )
}

function toGameSide(
  side: GameSide['side'],
  pick: TeamPick,
  versions: GameSide['version'][],
  teams: GameSide['team'][],
): GameSide | null {
  const version = versions.find((v) => v.id === pick.versionId)
  const team = teams.find((t) => t.id === pick.teamId)
  return version && team ? { side, team, version } : null
}
