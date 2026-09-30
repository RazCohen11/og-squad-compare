import { describe, expect, it } from 'vitest'
import { displayName, initials, tierFor } from './cards'

describe('tierFor (D37)', () => {
  it('uses the FUT boundaries', () => {
    expect(tierFor(40)).toBe('bronze')
    expect(tierFor(64)).toBe('bronze')
    expect(tierFor(65)).toBe('silver')
    expect(tierFor(74)).toBe('silver')
    expect(tierFor(75)).toBe('gold')
    expect(tierFor(94)).toBe('gold')
  })
})

describe('displayName', () => {
  it('drops leading initials', () => {
    expect(displayName('L. Messi')).toBe('Messi')
    expect(displayName('K. De Bruyne')).toBe('De Bruyne')
    expect(displayName('M. ter Stegen')).toBe('ter Stegen')
    expect(displayName('Á. Di María')).toBe('Di María')
  })

  it('keeps names without an initial', () => {
    expect(displayName('Cristiano Ronaldo')).toBe('Cristiano Ronaldo')
    expect(displayName('Vini Jr.')).toBe('Vini Jr.')
    expect(displayName('Rodri')).toBe('Rodri')
    expect(displayName('Kim Min Jae')).toBe('Kim Min Jae')
  })
})

describe('initials', () => {
  it('builds two letters from the short name', () => {
    expect(initials('L. Messi')).toBe('LM')
    expect(initials('Cristiano Ronaldo')).toBe('CR')
    expect(initials('M. ter Stegen')).toBe('MS')
    expect(initials('Rodri')).toBe('RO')
    expect(initials('Éder Militão')).toBe('ÉM')
    expect(initials('Vini Jr.')).toBe('VJ')
  })
})
