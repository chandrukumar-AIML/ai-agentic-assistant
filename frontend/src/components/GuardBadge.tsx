// frontend/src/components/GuardBadge.tsx
/**
 * Guardian safety + compliance badge for each AI message.
 *
 * Handles both:
 *  - Legacy guard-engine flags: "safe" | "blocked" | "warned" | "redacted"
 *  - New Guardian compliance verdicts: "APPROVE" | "WARN" | "REJECT" | "ESCALATE_TO_HUMAN"
 *
 * Shows nothing if everything is safe/approved.
 */
import { useState } from 'react'

interface Props {
  inputFlag?:   string    // guard_engine OR compliance verdict
  outputFlag?:  string
  piiMasked?:   boolean
  hallucination?: boolean
  violations?:  string[]  // human-readable compliance violation descriptions
}

type FlagConfig = { label: string; color: string; bg: string; icon: string }

const FLAG_MAP: Record<string, FlagConfig> = {
  // Legacy guard-engine flags
  safe:     { label: 'Safe',        color: '#166534', bg: '#dcfce7', icon: '✓'  },
  blocked:  { label: 'Blocked',     color: '#991b1b', bg: '#fee2e2', icon: '✗'  },
  warned:   { label: 'Low conf.',   color: '#92400e', bg: '#fef3c7', icon: '⚠'  },
  redacted: { label: 'PII masked',  color: '#1e4d8c', bg: '#dbeafe', icon: '🔒' },

  // Guardian compliance verdicts (uppercase)
  APPROVE:            { label: 'Compliant',   color: '#166534', bg: '#dcfce7', icon: '✅' },
  WARN:               { label: 'Cautioned',   color: '#92400e', bg: '#fef3c7', icon: '⚠️' },
  REJECT:             { label: 'Blocked',     color: '#991b1b', bg: '#fee2e2', icon: '🛡️' },
  ESCALATE_TO_HUMAN:  { label: 'In Review',   color: '#1e40af', bg: '#dbeafe', icon: '👤' },
}

function isSilent(flag: string | undefined | null): boolean {
  return !flag || flag === 'safe' || flag === 'APPROVE'
}

export default function GuardBadge({ inputFlag, outputFlag, piiMasked, hallucination, violations }: Props) {
  const [showViolations, setShowViolations] = useState(false)
  const badges: Array<{ key: string } & FlagConfig> = []

  // Input flag — skip if safe/approved
  if (!isSilent(inputFlag) && inputFlag) {
    const cfg = FLAG_MAP[inputFlag] ?? { label: inputFlag, color: '#6b7280', bg: '#f3f4f6', icon: '?' }
    badges.push({ key: 'input', ...cfg, label: `Input: ${cfg.label}` })
  }

  // Output flag — skip if safe/approved
  if (!isSilent(outputFlag) && outputFlag) {
    const cfg = FLAG_MAP[outputFlag] ?? { label: outputFlag, color: '#6b7280', bg: '#f3f4f6', icon: '?' }
    badges.push({ key: 'output', ...cfg, label: `Output: ${cfg.label}` })
  }

  // PII masking
  if (piiMasked) {
    badges.push({ key: 'pii', ...FLAG_MAP.redacted, label: 'PII masked' })
  }

  // Hallucination warning
  if (hallucination) {
    badges.push({ key: 'hall', ...FLAG_MAP.warned, label: 'Low confidence' })
  }

  if (badges.length === 0) return null

  return (
    <div style={{ marginTop: '4px' }}>
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
        {badges.map(badge => (
          <span
            key={badge.key}
            style={{
              display:      'inline-flex',
              alignItems:   'center',
              gap:          '3px',
              fontSize:     '10px',
              fontWeight:   600,
              padding:      '2px 7px',
              borderRadius: '20px',
              background:   badge.bg,
              color:        badge.color,
              border:       `1px solid ${badge.color}25`,
              whiteSpace:   'nowrap',
            }}
          >
            <span>{badge.icon}</span>
            <span>{badge.label}</span>
          </span>
        ))}

        {/* Violation detail toggle */}
        {violations && violations.length > 0 && (
          <button
            onClick={() => setShowViolations(v => !v)}
            style={{
              background:     'none',
              border:         'none',
              cursor:         'pointer',
              fontSize:       '10px',
              color:          '#6b7280',
              padding:        '2px 4px',
              textDecoration: 'underline',
            }}
          >
            {showViolations ? 'hide' : `${violations.length} violation${violations.length !== 1 ? 's' : ''}`}
          </button>
        )}
      </div>

      {showViolations && violations && violations.length > 0 && (
        <div
          style={{
            marginTop:    '6px',
            padding:      '8px 10px',
            borderRadius: '6px',
            background:   '#fff7ed',
            border:       '1px solid #fed7aa',
            fontSize:     '11px',
            color:        '#9a3412',
            lineHeight:   1.5,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: '4px' }}>🛡️ Compliance Violations</div>
          <ul style={{ margin: 0, paddingLeft: '14px' }}>
            {violations.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
