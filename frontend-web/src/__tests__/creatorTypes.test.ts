import { describe, it, expect } from 'vitest'
import {
  CREATOR_TYPES,
  getCreatorType,
  getAllCreators,
  getDefaultCreatorType,
} from '@/types/creator'
import type { CreatorType } from '@/types/creator'

describe('Creator Types', () => {
  it('has exactly 6 creator types', () => {
    const keys = Object.keys(CREATOR_TYPES) as CreatorType[]
    expect(keys).toHaveLength(6)
  })

  it('includes all expected creator types', () => {
    const types = Object.keys(CREATOR_TYPES) as CreatorType[]
    expect(types).toContain('illustrator')
    expect(types).toContain('photographer')
    expect(types).toContain('video')
    expect(types).toContain('craftsman')
    expect(types).toContain('musician')
    expect(types).toContain('writer')
  })

  it('each creator type has required fields', () => {
    for (const [type, info] of Object.entries(CREATOR_TYPES)) {
      expect(info.type).toBe(type)
      expect(typeof info.label).toBe('string')
      expect(info.label.length).toBeGreaterThan(0)
      expect(typeof info.icon).toBe('string')
      expect(typeof info.color).toBe('string')
      expect(typeof info.description).toBe('string')
      expect(Array.isArray(info.routes)).toBe(true)
      expect(info.routes.length).toBeGreaterThan(0)
      expect(Array.isArray(info.features)).toBe(true)
      expect(info.features.length).toBeGreaterThan(0)
    }
  })

  it('all creator types share common routes', () => {
    const commonRoutes = ['works', 'rights', 'monitor', 'business']
    for (const info of Object.values(CREATOR_TYPES)) {
      for (const route of commonRoutes) {
        expect(info.routes).toContain(route)
      }
    }
  })

  it('each creator type has a unique specific route', () => {
    const specificRoutes = Object.values(CREATOR_TYPES).map(c => c.routes[4])
    const unique = new Set(specificRoutes)
    expect(unique.size).toBe(6)
  })

  it('getCreatorType returns default for undefined route', () => {
    expect(getCreatorType(undefined)).toBe('illustrator')
  })

  it('getCreatorType returns default for empty string', () => {
    expect(getCreatorType('')).toBe('illustrator')
  })

  it('getCreatorType matches illustrator route', () => {
    expect(getCreatorType('illustrator')).toBe('illustrator')
  })

  it('getCreatorType matches photographer route', () => {
    expect(getCreatorType('photographer')).toBe('photographer')
  })

  it('getCreatorType matches video route', () => {
    expect(getCreatorType('video')).toBe('video')
  })

  it('getCreatorType matches craftsman route', () => {
    expect(getCreatorType('craftsman')).toBe('craftsman')
  })

  it('getAllCreators returns array of all types', () => {
    const creators = getAllCreators()
    expect(creators).toHaveLength(6)
    expect(creators.map(c => c.type)).toEqual(['illustrator', 'photographer', 'video', 'craftsman', 'musician', 'writer'])
  })

  it('getDefaultCreatorType returns illustrator', () => {
    expect(getDefaultCreatorType()).toBe('illustrator')
  })

  it('each creator has a valid hex color', () => {
    for (const info of Object.values(CREATOR_TYPES)) {
      expect(info.color).toMatch(/^#[0-9A-Fa-f]{6}$/)
    }
  })
})
