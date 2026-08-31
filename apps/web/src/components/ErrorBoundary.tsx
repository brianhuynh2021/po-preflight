import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

// Catches render errors from a page and shows a clear message with a retry
// action instead of a blank screen (requirement FR-009).
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  private retry = () => {
    this.setState({ error: null })
  }

  render() {
    if (this.state.error) {
      return (
        <div className="panel" role="alert" style={{ padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ fontWeight: 560, marginBottom: 6 }}>This page failed to load</div>
          <div className="faint" style={{ fontSize: 12.5, marginBottom: 16 }}>
            {this.state.error.message || 'An unexpected error occurred.'}
          </div>
          <button type="button" className="btn" onClick={this.retry}>
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
