// frontend/src/pages/CodePage.tsx — Code Assistant Vertical
import { useState } from 'react'
import { PageShell, Card, Btn, Input, Select, ResultBox, TwoCol, useApi, SectionHead, Badge } from '../components/ui'
import { apiFetch } from '../lib/api'

const codeAction = (action: string, code: string, prompt: string, language: string) =>
  apiFetch('/verticals/code/action', {
    method: 'POST',
    body: JSON.stringify({ action, code, prompt, language }),
  }, 360_000)

const LANGUAGES = ['python', 'javascript', 'typescript', 'go', 'java', 'sql', 'bash']

const EXAMPLES: Record<string, { prompt: string; code: string }> = {
  generate: {
    prompt: 'Write a FastAPI endpoint that accepts a JSON body with name and email, validates them, and saves to PostgreSQL using asyncpg. Include proper error handling and type hints.',
    code: '',
  },
  debug: {
    prompt: 'This function returns wrong totals for negative numbers.',
    code: `def calculate_total(items):
    total = 0
    for item in items:
        if item > 0:
            total += item
    return total`,
  },
  review: {
    prompt: 'Review this for security and best practices.',
    code: `import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE username = '{username}'")
    return cur.fetchone()`,
  },
  test: {
    prompt: 'Write comprehensive pytest tests with edge cases.',
    code: `def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b`,
  },
  explain: {
    prompt: 'Explain this code step by step for a junior developer.',
    code: `async def retry(func, retries=3, delay=1.0):
    for attempt in range(retries):
        try:
            return await func()
        except Exception as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay * (2 ** attempt))`,
  },
}

const ACTION_META = [
  { id: 'generate', label: 'Generate',  icon: '✨', desc: 'Write code from description' },
  { id: 'debug',    label: 'Debug',     icon: '🐛', desc: 'Find and fix bugs' },
  { id: 'review',   label: 'Review',    icon: '🔍', desc: 'Security & quality review' },
  { id: 'test',     label: 'Tests',     icon: '🧪', desc: 'Write unit tests' },
  { id: 'explain',  label: 'Explain',   icon: '📖', desc: 'Plain-language explanation' },
]

export default function CodePage() {
  const [action, setAction]     = useState('generate')
  const [language, setLanguage] = useState('python')
  const [prompt, setPrompt]     = useState(EXAMPLES['generate'].prompt)
  const [code, setCode]         = useState(EXAMPLES['generate'].code)
  const api                     = useApi()

  const selectAction = (a: string) => {
    setAction(a)
    setPrompt(EXAMPLES[a]?.prompt || '')
    setCode(EXAMPLES[a]?.code || '')
    api.call(() => Promise.resolve(null))  // clear result
  }

  const data = api.data as any

  return (
    <PageShell
      icon="💻"
      title="AI Code Assistant"
      subtitle="Generate, debug, review, test, and explain code with sandboxed execution"
    >
      <TwoCol>
        {/* Left: Input panel */}
        <div>
          {/* Action selector */}
          <Card style={{ marginBottom: 12 }}>
            <SectionHead title="Action" sub="What do you need?" />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {ACTION_META.map(m => (
                <button
                  key={m.id}
                  onClick={() => selectAction(m.id)}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center',
                    padding: '10px 16px', borderRadius: 8, cursor: 'pointer',
                    background: action === m.id ? 'rgba(16,185,129,0.15)' : '#0f1117',
                    border: `1px solid ${action === m.id ? '#10b981' : '#1e2535'}`,
                    color: action === m.id ? '#5eead4' : '#6b7280',
                    transition: 'all 0.15s', minWidth: 90,
                  }}
                >
                  <span style={{ fontSize: 20, marginBottom: 4 }}>{m.icon}</span>
                  <span style={{ fontSize: 12, fontWeight: action === m.id ? 600 : 400 }}>{m.label}</span>
                  <span style={{ fontSize: 10, color: '#4b5563', marginTop: 2 }}>{m.desc}</span>
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <SectionHead title="Input" sub="Describe what you need or paste your code" />

            <Select
              label="Language"
              value={language}
              onChange={setLanguage}
              options={LANGUAGES.map(l => ({ value: l, label: l.charAt(0).toUpperCase() + l.slice(1) }))}
            />

            <Input
              label={action === 'generate' ? 'Describe what to build' : 'Instructions / Question'}
              value={prompt}
              onChange={setPrompt}
              rows={3}
            />

            {action !== 'generate' && (
              <Input
                label="Code"
                value={code}
                onChange={setCode}
                rows={10}
              />
            )}

            <Btn
              onClick={() => api.call(() => codeAction(action, code, prompt, language))}
              loading={api.loading}
            >
              {ACTION_META.find(m => m.id === action)?.icon} {ACTION_META.find(m => m.id === action)?.label} Code
            </Btn>
          </Card>
        </div>

        {/* Right: Output panel */}
        <div>
          {/* Metadata card */}
          {data && !api.loading && (
            <Card style={{ marginBottom: 12 }}>
              <SectionHead title="Execution Info" sub="" />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                <Badge text={`Action: ${data.action || action}`} color="blue" />
                {data.metadata?.task_type && (
                  <Badge text={`Type: ${data.metadata.task_type}`} color="green" />
                )}
                {data.metadata?.had_execution && (
                  <Badge text="Sandboxed execution ✓" color="green" />
                )}
                {data.metadata?.had_review && (
                  <Badge text="Code review included ✓" color="yellow" />
                )}
                {data.metadata?.code_length > 0 && (
                  <Badge text={`${data.metadata.code_length} chars`} color="blue" />
                )}
                {data.latency_ms && (
                  <span style={{ fontSize: 11, color: '#4b5563' }}>
                    ⏱ {Math.round(data.latency_ms)}ms
                  </span>
                )}
              </div>

              {/* Sandbox info box */}
              <div style={{
                marginTop: 12, padding: 10,
                background: 'rgba(34,197,94,0.08)',
                borderRadius: 8, border: '1px solid rgba(34,197,94,0.2)',
              }}>
                <div style={{ fontSize: 11, color: '#22c55e', fontWeight: 600, marginBottom: 4 }}>
                  🛡️ RestrictedPython Sandbox
                </div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>
                  Generated code is executed in an isolated sandbox — no file system or network access.
                  Execution timeout: 30 seconds.
                </div>
              </div>
            </Card>
          )}

          <ResultBox
            data={data?.content ? { output: data.content } : null}
            loading={api.loading}
            error={api.error}
            title="Code Assistant Output"
          />
        </div>
      </TwoCol>

      {/* Capabilities section */}
      {!data && !api.loading && (
        <Card style={{ marginTop: 16 }}>
          <SectionHead title="Capabilities" sub="What the Code Assistant can do" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {[
              { icon: '✨', title: 'Code Generation',     desc: 'Production-quality code from plain English — type hints, error handling, docstrings included' },
              { icon: '🐛', title: 'Self-Healing Debug',  desc: 'Detects errors, attempts auto-fix, re-runs to verify the fix works' },
              { icon: '🔍', title: 'Security Review',     desc: 'Detects SQL injection, insecure deserialization, missing validation, and more' },
              { icon: '🧪', title: 'Test Generation',     desc: 'Writes pytest tests covering happy path, edge cases, and error conditions' },
              { icon: '📖', title: 'Code Explanation',    desc: 'Plain-language walkthrough for any code — great for onboarding and code reviews' },
              { icon: '🛡️', title: 'Sandboxed Execution', desc: 'Code runs in RestrictedPython — safe, isolated, no shell or network access' },
            ].map(({ icon, title, desc }) => (
              <div key={title} style={{
                padding: 14, background: '#0f1117', borderRadius: 8,
                border: '1px solid #1e2535',
              }}>
                <div style={{ fontSize: 20, marginBottom: 6 }}>{icon}</div>
                <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{title}</div>
                <div style={{ color: '#6b7280', fontSize: 11 }}>{desc}</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </PageShell>
  )
}
