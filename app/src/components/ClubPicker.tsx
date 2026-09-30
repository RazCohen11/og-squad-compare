import { useId, useMemo, useRef, useState } from 'react'
import { filterGroups, type LeagueGroup } from '../lib/teams'
import styles from './ClubPicker.module.css'

interface Props {
  // Visible label of the trigger, e.g. "Club"
  label: string
  // Accessible context, e.g. "Team A"
  owner: string
  groups: LeagueGroup[]
  selectedId: number | null
  // Club already picked by the other side; it cannot be picked here
  takenId: number | null
  takenBy: string
  onSelect: (id: number) => void
}

export function ClubPicker({ label, owner, groups, selectedId, takenId, takenBy, onSelect }: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelId = useId()
  const searchId = useId()

  const selectedGroup = groups.find((g) => g.teams.some((t) => t.id === selectedId))
  const selectedTeam = selectedGroup?.teams.find((t) => t.id === selectedId)
  const selected = selectedGroup && selectedTeam ? { team: selectedTeam, league: selectedGroup.league } : null

  const visible = useMemo(() => filterGroups(groups, query), [groups, query])

  const close = () => {
    setOpen(false)
    setQuery('')
    triggerRef.current?.focus()
  }

  return (
    <div className={styles.picker}>
      <button
        ref={triggerRef}
        type="button"
        className={`${styles.trigger} ${selected ? styles.hasValue : ''}`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => (open ? close() : setOpen(true))}
      >
        <span className={styles.triggerLabel}>
          {label}
          <span className="visually-hidden"> for {owner}</span>
        </span>
        <span className={styles.triggerValue}>{selected ? selected.team.name : 'Choose a club'}</span>
        {selected && <span className={styles.triggerLeague}>{selected.league.name}</span>}
        <span className={styles.chevron} aria-hidden="true">
          {open ? '▲' : '▼'}
        </span>
      </button>

      {open && (
        <div
          id={panelId}
          className={styles.panel}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              e.preventDefault()
              close()
            }
          }}
        >
          <label htmlFor={searchId} className="visually-hidden">
            Search clubs for {owner}
          </label>
          <input
            id={searchId}
            type="search"
            className={styles.search}
            placeholder="Search clubs"
            autoComplete="off"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className={styles.list}>
            {visible.length === 0 && <p className={styles.empty}>No clubs match “{query}”.</p>}
            {visible.map((group) => (
              <section key={group.league.id} className={styles.group} aria-label={group.league.name}>
                <h3 className={styles.groupTitle}>{group.league.name}</h3>
                <ul className={styles.options}>
                  {group.teams.map((team) => {
                    const taken = team.id === takenId
                    const isSelected = team.id === selectedId
                    return (
                      <li key={team.id}>
                        <button
                          type="button"
                          className={styles.option}
                          aria-pressed={isSelected}
                          disabled={taken}
                          onClick={() => {
                            onSelect(team.id)
                            close()
                          }}
                        >
                          <span>{team.name}</span>
                          {taken && <span className={styles.takenNote}>{takenBy}</span>}
                          {isSelected && (
                            <span className={styles.check} aria-hidden="true">
                              ✓
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </section>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
