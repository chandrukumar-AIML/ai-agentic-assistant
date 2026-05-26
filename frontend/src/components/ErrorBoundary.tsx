import { Component, ErrorInfo, ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean; error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production: send to error tracking (Sentry etc.)
    if (import.meta.env.MODE !== 'production') {
      console.error('ErrorBoundary caught:', error, info)
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '100vh', gap: '12px',
          background: 'var(--color-background-tertiary)',
        }}>
          <span style={{ fontSize: '32px' }}>⚠️</span>
          <p style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Something went wrong
          </p>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            {this.state.error?.message ?? 'Unexpected error'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '8px 16px', borderRadius: '8px',
              background: '#534AB7', color: '#fff', border: 'none', cursor: 'pointer',
            }}
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
