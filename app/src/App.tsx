import { useMemo, useRef, useState } from 'react'
import { GameScreen } from './components/GameScreen'
import { SetupScreen, type RandomState, type TeamPick } from './components/SetupScreen'
import { StatusMessage } from './components/StatusMessage'
import { DataLoadError, loadIndex, loadTeams } from './data/loaders'
import { useTeams, useVersions } from './data/useData'
import { RandomMatchupError, pickRandomMatchup, rememberMatchup } from './game/random'
import type { GameSide } from './game/sides'
import { sortVersionsNewestFirst } from './lib/teams'

type Screen = 'setup' | 'game'
type Mode = 'manual' | 'random'

const EMPTY_PICK: TeamPick = { versionId: null, teamId: null }

export default function App() {
  const versions = useVersions()
  const [screen, setScreen] = useState<Screen>('setup')
  const [mode, setMode] = useState<Mode>('manual')
  const [pickA, setPickA] = useState<TeamPick>(EMPTY_PICK)
  const [pickB, setPickB] = useState<TeamPick>(EMPTY_PICK)
  const [random, setRandom] = useState<RandomState>({ status: 'idle' })
  // Bumped for every game started, so a new game always gets fresh state
  const [gameSeq, setGameSeq] = useState(0)
  // Pairs of the last random matchups of this session, in memory only (D48)
  const randomHistory = useRef<string[]>([])

  const versionList = versions.status === 'ready' ? versions.data : null
  const sortedVersions = useMemo(() => (versionList ? sortVersionsNewestFirst(versionList) : []), [versionList])
  // Each team defaults to the newest version (D30)
  const newestId = sortedVersions[0]?.id ?? null
  const resolvedA: TeamPick = { ...pickA, versionId: pickA.versionId ?? newestId }
  const resolvedB: TeamPick = { ...pickB, versionId: pickB.versionId ?? newestId }
  const teamsA = useTeams(resolvedA.versionId)
  const teamsB = useTeams(resolvedB.versionId)

  // Random matchup (D49): load the index, pick two teams, load both versions, start the game at once
  const startRandom = async () => {
    if (random.status === 'loading') return
    setRandom({ status: 'loading' })
    try {
      const index = await loadIndex()
      const matchup = pickRandomMatchup(index, { history: randomHistory.current })
      await Promise.all([loadTeams(matchup.a.v), loadTeams(matchup.b.v)])
      randomHistory.current = rememberMatchup(randomHistory.current, matchup)
      setPickA({ versionId: matchup.a.v, teamId: matchup.a.id })
      setPickB({ versionId: matchup.b.v, teamId: matchup.b.id })
      setMode('random')
      setGameSeq((n) => n + 1)
      setScreen('game')
      setRandom({ status: 'idle' })
    } catch (error) {
      const message =
        error instanceof DataLoadError || error instanceof RandomMatchupError
          ? error.message
          : 'Could not start a random matchup.'
      setRandom({ status: 'error', message })
      setScreen('setup')
    }
  }

  if (versions.status === 'loading' || versions.status === 'idle') {
    return <StatusMessage kind="loading" message="Loading game versions…" />
  }
  if (versions.status === 'error') {
    return <StatusMessage kind="error" message={versions.message} onRetry={versions.retry} />
  }

  if (screen === 'game') {
    // Team files are already cached when a random game starts; this only shows for a moment
    if (teamsA.status === 'loading' || teamsB.status === 'loading') {
      return <StatusMessage kind="loading" message="Loading clubs…" />
    }
    if (teamsA.status === 'ready' && teamsB.status === 'ready') {
      const sideA = toGameSide('A', resolvedA, sortedVersions, teamsA.data.teams)
      const sideB = toGameSide('B', resolvedB, sortedVersions, teamsB.data.teams)
      if (sideA && sideB) {
        return (
          <GameScreen
            // A new game always starts with fresh state
            key={`${gameSeq}-${sideA.version.id}-${sideA.team.id}-${sideB.version.id}-${sideB.team.id}`}
            sideA={sideA}
            sideB={sideB}
            onBack={() => setScreen('setup')}
            onNewTeams={() => {
              // Keep both version picks, clear the clubs
              setPickA({ versionId: resolvedA.versionId, teamId: null })
              setPickB({ versionId: resolvedB.versionId, teamId: null })
              setScreen('setup')
            }}
            onAnotherRandom={mode === 'random' ? () => void startRandom() : undefined}
            randomBusy={random.status === 'loading'}
          />
        )
      }
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
      onStart={() => {
        setMode('manual')
        setGameSeq((n) => n + 1)
        setScreen('game')
      }}
      random={random}
      onRandom={() => void startRandom()}
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
