import { describe, it, expect } from 'vitest'
import { formatBytes, formatDate, truncate, generateId } from '../utils/helpers'

describe('formatBytes', () => {
  it('formats bytes', () => expect(formatBytes(512)).toBe('512 B'))
  it('formats kilobytes', () => expect(formatBytes(2048)).toBe('2.0 KB'))
  it('formats megabytes', () => expect(formatBytes(5 * 1024 * 1024)).toBe('5.0 MB'))
})

describe('truncate', () => {
  it('returns original if short', () => expect(truncate('hello', 10)).toBe('hello'))
  it('truncates long text', () => expect(truncate('hello world', 5)).toBe('hello…'))
})

describe('generateId', () => {
  it('returns a non-empty string', () => expect(generateId().length).toBeGreaterThan(0))
  it('returns unique ids', () => expect(generateId()).not.toBe(generateId()))
})

describe('formatDate', () => {
  it('returns a formatted date string', () => {
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })
})
