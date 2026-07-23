import { motion } from 'framer-motion'
import { AgentType, workspaceLabel } from '../lib/workspace'

interface Props {
  agent: AgentType
  onEdit: () => void
  onClear: () => void
}

const ACCENT: Record<AgentType, string> = {
  sm: '#8B5CF6',
  cs: '#10B981',
  ca: '#F59E0B',
}

const ICON: Record<AgentType, string> = {
  sm: '📱',
  cs: '💬',
  ca: '🧮',
}

export default function WorkspaceBar({ agent, onEdit, onClear }: Props) {
  const { name, chips } = workspaceLabel(agent)
  const accent = ACCENT[agent]

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      style={{
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        padding: '8px 16px',
        background: `linear-gradient(90deg, ${accent}10, transparent)`,
        border: `1px solid ${accent}30`,
        borderRadius: 10, marginBottom: 16,
      }}
    >
      {/* Live dot + icon */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
        <span style={{ fontSize: 14 }}>{ICON[agent]}</span>
        <span style={{
          width: 7, height: 7, borderRadius: '50%', background: accent,
          boxShadow: `0 0 8px ${accent}`,
          display: 'inline-block',
        }} />
      </div>

      {/* Workspace name */}
      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', flexShrink: 0 }}>{name}</span>

      {/* Context chips */}
      {chips.map(chip => (
        <span key={chip} style={{
          fontSize: 11, padding: '2px 8px', borderRadius: 20,
          background: `${accent}18`, color: accent, fontWeight: 600,
        }}>{chip}</span>
      ))}

      <span style={{ flex: 1 }} />

      {/* Actions */}
      <button onClick={onEdit} style={{
        padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
        background: 'var(--surface-2)', border: '1px solid var(--border)',
        color: 'var(--text-2)', cursor: 'pointer', transition: 'all 0.15s',
        flexShrink: 0,
      }}>✏️ Edit Workspace</button>

      <button onClick={onClear} style={{
        padding: '4px 10px', borderRadius: 8, fontSize: 11,
        background: 'none', border: '1px solid var(--border)',
        color: 'var(--text-3)', cursor: 'pointer', flexShrink: 0,
        transition: 'all 0.15s',
      }} title="Clear workspace and reconfigure">✕</button>
    </motion.div>
  )
}
