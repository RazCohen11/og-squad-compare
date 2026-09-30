import { useMemo, useState } from 'react'
import { GameScreen } from './components/GameScreen'
import { SetupScreen } from './components/SetupScreen'
import { StatusMessage } from './components/StatusMessage'
import { useTeams, useVersions } from './data/useData'
import { sortVersionsNewestFirst } from './lib/teams'

type Screen = 'setup' | 'game'

export default function App() {
  const versions = useVersions()
  const [screen, setScreen] = useState<Screen>('setup')
  const [pickedVersionId, setPickedVersionId] = useState<number | null>(null)
  const [teamAId, setTeamAId] = useState<number | null>(null)
  const [teamBId, setTeamBId] = useState<number | null>(null)

  const versionList = versions.status === 'ready' ? versions.data : null
  const sortedVersions = useMemo(() => (versionList ? sortVersionsNewestFirst(versionList) : []), [versionList])
  // Default version = newest
  const versionId = pickedVersionId ?? sortedVersions[0]?.id ?? null
  const version = sortedVersions.find((v) => v.id === versionId) ?? null
  const teams = useTeams(versionId)

  if (versions.status === 'loading' || versions.status === 'idle') {
    return <StatusMessage kind="loading" message="Loading game versions…" />
  }
  if (versions.status === 'error') {
    return <StatusMessage kind="error" message={versions.message} onRetry={versions.retry} />
  }

  const changeVersion = (id: number) => {
    // Changing the version clears the club picks
    setPickedVersionId(id)
    setTeamAId(null)
    setTeamBId(null)
  }

  if (screen === 'game' && version && teams.status === 'ready') {
    const teamA = teams.data.teams.find((t) => t.id === teamAId)
    const teamB = teams.data.teams.find((t) => t.id === teamBId)
    if (teamA && teamB) {
      return <GameScreen version={version} teamA={teamA} teamB={teamB} onBack={() => setScreen('setup')} />
    }
  }

  return (
    <SetupScreen
      versions={sortedVersions}
      versionId={versionId}
      onVersionChange={changeVersion}
      teams={teams}
      teamAId={teamAId}
      teamBId={teamBId}
      onTeamAChange={setTeamAId}
      onTeamBChange={setTeamBId}
      onStart={() => setScreen('game')}
    />
  )
}
