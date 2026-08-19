import { useEffect, useState } from 'react'
import './App.css'
import { fetchDecisions, type Decision } from './lib/decisions'
import DecisionTable from './components/DecisionTable'
import BrandMark from './components/BrandMark'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; decisions: Decision[] }

function App() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    fetchDecisions()
      .then((decisions) => {
        if (!cancelled) setState({ status: 'ready', decisions })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : String(error)
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main id="decisions">
      <BrandMark />
      <h1>Governance decisions</h1>

      {state.status === 'loading' && <p role="status">Loading decisions…</p>}

      {state.status === 'error' && (
        <p role="alert" className="error">
          Could not load decisions: {state.message}
        </p>
      )}

      {state.status === 'ready' && (
        <DecisionTable decisions={state.decisions} />
      )}
    </main>
  )
}

export default App
