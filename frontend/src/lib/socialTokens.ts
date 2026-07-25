const KEY = 'aaa_social_tokens'

export interface SocialTokens {
  linkedin_access_token: string
  linkedin_person_urn: string   // urn:li:person:XXXXXXX
  buffer_access_token: string
  twitter_connected: boolean    // Twitter needs backend env vars — just a flag
  instagram_connected: boolean  // Instagram via Meta Graph — just a flag
}

const DEFAULTS: SocialTokens = {
  linkedin_access_token: '',
  linkedin_person_urn: '',
  buffer_access_token: '',
  twitter_connected: false,
  instagram_connected: false,
}

export function getSocialTokens(): SocialTokens {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS
  } catch {
    return DEFAULTS
  }
}

export function setSocialTokens(tokens: Partial<SocialTokens>): void {
  const current = getSocialTokens()
  localStorage.setItem(KEY, JSON.stringify({ ...current, ...tokens }))
}

export function clearSocialTokens(): void {
  localStorage.removeItem(KEY)
}

export function isLinkedInConnected(): boolean {
  const t = getSocialTokens()
  return !!(t.linkedin_access_token && t.linkedin_person_urn)
}

export function isBufferConnected(): boolean {
  return !!getSocialTokens().buffer_access_token
}
