// frontend/src/components/GuardianBadge.tsx
/**
 * Guardian compliance verdict badge.
 * Shows APPROVE / WARN / REJECT / ESCALATE status for each AI message.
 *
 * Props:
 *   inputFlag   — verdict on user's input (pre-check)
 *   outputFlag  — verdict on AI's response (post-check)
 *   piiMasked   — was PII stripped from input?
 *   violations  — array of violation descriptions for tooltip
 */
import { useState } from 'react'

type Verdict = 'APPROVE' | 'WARN' | 'REJECT' | 'ESCALATE_TO_HUMAN' | undefined | null

interface Props {
  inputFlag?:   Verdict
  outputFlag?:  Verdict
  piiMasked?:   boolean
  violations?:  string[]
}

const VERDICT_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  APPROVE:            { label: 'Safe',      color: '#15803d', bg: '#dcfce7', icon: '✅' },
  WARN:               { label: 'Warned',    color: '#92400e', bg: '#fef3c7', icon: '⚠️' },
  REJECT:             { label: 'Blocked',   color: '#b91c1c', bg: '#fee2e2', icon: '🛡️' },
  ESCALATE_TO_HUMAN:  { label: 'Review',    color: '#1d4ed8', bg: '#dbeafe', icon: '👤' },
}

const DEFAULT_CONFIG = { label: 'Unknown', color: '#6b7280', bg: '#f3f4f6', icon: '❓' }

function VerdictChip({ flag, label }: { flag: Verdict; label: string }) {
  if (!flag || flag === 'APPROVE') return null
  const cfg = VERDICT_CONFIG[flag] ?? DEFAULT_CONFIG

  return (
    <span
      style={{
        display:        'inline-flex',
        alignItems:     'center',
        gap:            '3px',
        fontSize:       '10px',
        fontWeight:     600,
        padding:        '2px 6px',
        borderRadius:   '20px',
        background:     cfg.bg,
        color:          cfg.color,
        border:         `1px solid ${cfg.color}20`,
        letterSpacing:  '0.02em',
        whiteSpace:     'nowrap',
      }}
      title={`${label}: ${cfg.label}`}
    >
      {cfg.icon} {cfg.label}
    </span>
  )
}

export default function GuardianBadge({ inputFlag, outputFlag, piiMasked, violations }: Props) {
  const [showViolations, setShowViolations] = useState(false)

  // Only render if there's something non-trivial to show
  const hasWarning = (
    (inputFlag  && inputFlag  !== 'APPROVE') ||
    (outputFlag && outputFlag !== 'APPROVE') ||
    piiMasked
  )

  if (!hasWarning) return null

  return (
    <div style={{ marginTop: '4px' }}>
      <div
        style={{
          display:    'flex',
          alignItems: 'center',
          gap:        '4px',
          flexWrap:   'wrap',
        }}
      >
        {/* Input check badge */}
        <VerdictChip flag={inputFlag} label="Input" />

        {/* Output check badge */}
        <VerdictChip flag={outputFlag} label="Output" />

        {/* PII masked indicator */}
        {piiMasked && (
          <span
            style={{
              display:      'inline-flex',
              alignItems:   'center',
              gap:          '3px',
              fontSize:     '10px',
              fontWeight:   600,
              padding:      '2px 6px',
              borderRadius: '20px',
              background:   '#f0f9ff',
              color:        '#0369a1',
              border:       '1px solid #0369a120',
              whiteSpace:   'nowrap',
            }}
            title="PII was detected and masked from your input"
          >
            🔒 PII Masked
          </span>
        )}

        {/* Violations toggle */}
        {violations && violations.length > 0 && (
          <button
            onClick={() => setShowViolations(v => !v)}
            style={{
              background:   'none',
              border:       'none',
              cursor:       'pointer',
              fontSize:     '10px',
              color:        '#6b7280',
              padding:      '2px 4px',
              textDecoration: 'underline',
            }}
          >
            {showViolations ? 'hide' : `${violations.length} violation${violations.length > 1 ? 's' : ''}`}
          </button>
        )}
      </div>

      {/* Violations list */}
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
          <div style={{ fontWeight: 700, marginBottom: '4px' }}>
            🛡️ Guardian Compliance Violations
          </div>
          <ul style={{ margin: 0, paddingLeft: '14px' }}>
            {violations.map((v, i) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
