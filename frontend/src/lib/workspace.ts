// Workspace context — persisted per agent in localStorage

export interface SMWorkspace {
  brand_name:        string
  industry:          string
  target_audience:   string
  tone:              string
  platforms:         string[]
  competitor_brands: string
  content_pillars:   string
  hashtag_style:     string
  // Brand Brain fields
  products_services: string
  usp:               string
  icp:               string
  pricing:           string
}

export interface CSWorkspace {
  company_name:       string
  business_type:      string
  products_services:  string
  whatsapp_number:    string
  business_hours:     string
  escalation_email:   string
  sla_first_response: string
  support_tone:       string
}

export interface CAWorkspace {
  firm_name:        string
  client_name:      string
  gstin:            string
  pan:              string
  state:            string
  business_type:    string
  financial_year:   string
  filing_frequency: string
  taxpayer_type:    string
}

export type AgentType = 'sm' | 'cs' | 'ca'

const KEYS: Record<AgentType, string> = {
  sm: 'aaa_ws_sm',
  cs: 'aaa_ws_cs',
  ca: 'aaa_ws_ca',
}

export function getWorkspace<T>(agent: AgentType): T | null {
  try {
    const raw = localStorage.getItem(KEYS[agent])
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export function saveWorkspace(agent: AgentType, data: any): void {
  localStorage.setItem(KEYS[agent], JSON.stringify(data))
}

export function clearWorkspace(agent: AgentType): void {
  localStorage.removeItem(KEYS[agent])
}

// Human-readable label for a workspace
export function workspaceLabel(agent: AgentType): { name: string; chips: string[] } {
  const ws = getWorkspace<any>(agent)
  if (!ws) return { name: '', chips: [] }

  if (agent === 'sm') {
    return {
      name: ws.brand_name || 'My Brand',
      chips: [
        ws.industry,
        ws.tone,
        ...(ws.platforms ?? []),
      ].filter(Boolean),
    }
  }
  if (agent === 'cs') {
    return {
      name: ws.company_name || 'My Company',
      chips: [
        ws.business_type,
        ws.whatsapp_number ? `WA: ${ws.whatsapp_number}` : '',
        ws.sla_first_response ? `SLA ${ws.sla_first_response}h` : '',
      ].filter(Boolean),
    }
  }
  // ca
  return {
    name: ws.firm_name || ws.client_name || 'My Firm',
    chips: [
      ws.business_type,
      ws.gstin ? `GSTIN: ${ws.gstin}` : '',
      ws.state,
      ws.financial_year,
    ].filter(Boolean),
  }
}
