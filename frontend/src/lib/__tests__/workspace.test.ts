import { describe, it, expect, beforeEach } from 'vitest'
import { getWorkspace, saveWorkspace, clearWorkspace, workspaceLabel } from '../workspace'

beforeEach(() => {
  localStorage.clear()
})

describe('getWorkspace', () => {
  it('returns null when nothing saved', () => {
    expect(getWorkspace('sm')).toBeNull()
    expect(getWorkspace('cs')).toBeNull()
    expect(getWorkspace('ca')).toBeNull()
  })

  it('returns saved workspace', () => {
    saveWorkspace('sm', { brand_name: 'TestBrand', industry: 'Tech' })
    const ws = getWorkspace<{ brand_name: string }>('sm')
    expect(ws?.brand_name).toBe('TestBrand')
  })

  it('returns null on corrupted localStorage', () => {
    localStorage.setItem('aaa_ws_sm', 'not-json{{{')
    expect(getWorkspace('sm')).toBeNull()
  })
})

describe('saveWorkspace / clearWorkspace', () => {
  it('persists and then clears', () => {
    saveWorkspace('ca', { firm_name: 'MyCA' })
    expect(getWorkspace('ca')).not.toBeNull()
    clearWorkspace('ca')
    expect(getWorkspace('ca')).toBeNull()
  })

  it('each agent has an isolated key', () => {
    saveWorkspace('sm', { brand_name: 'SM' })
    saveWorkspace('cs', { company_name: 'CS' })
    clearWorkspace('sm')
    expect(getWorkspace('sm')).toBeNull()
    expect(getWorkspace<{ company_name: string }>('cs')?.company_name).toBe('CS')
  })
})

describe('workspaceLabel', () => {
  it('returns empty label when no workspace saved', () => {
    const label = workspaceLabel('sm')
    expect(label.name).toBe('')
    expect(label.chips).toHaveLength(0)
  })

  it('SM label uses brand_name and chips', () => {
    saveWorkspace('sm', { brand_name: 'Acme', industry: 'Retail', tone: 'Friendly', platforms: ['linkedin'] })
    const label = workspaceLabel('sm')
    expect(label.name).toBe('Acme')
    expect(label.chips).toContain('Retail')
    expect(label.chips).toContain('Friendly')
    expect(label.chips).toContain('linkedin')
  })

  it('CS label uses company_name', () => {
    saveWorkspace('cs', { company_name: 'Support Co', business_type: 'SaaS', sla_first_response: '4' })
    const label = workspaceLabel('cs')
    expect(label.name).toBe('Support Co')
    expect(label.chips).toContain('SaaS')
    expect(label.chips).toContain('SLA 4h')
  })

  it('CA label falls back to client_name if no firm_name', () => {
    saveWorkspace('ca', { client_name: 'Ravi & Co', business_type: 'Partnership' })
    const label = workspaceLabel('ca')
    expect(label.name).toBe('Ravi & Co')
    expect(label.chips).toContain('Partnership')
  })
})
