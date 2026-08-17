import { useEffect, useState } from 'react'
import './App.css'
import { fetchDecisions, type Decision } from './lib/decisions'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; decisions: Decision[] }

function DecisionRow({ decision }: { decision: Decision }) {
  return (
    <tr>
      <td className="id">{decision.id}</td>
      <td className="title">{decision.title}</td>
      <td className="status">{decision.status}</td>
      <td className="superseded-by">
        {decision.supersededBy ? `superseded by ${decision.supersededBy}` : ''}
      </td>
    </tr>
  )
}

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
      <h1>Governance decisions</h1>

      {state.status === 'loading' && <p role="status">Loading decisions…</p>}

      {state.status === 'error' && (
        <p role="alert" className="error">
          Could not load decisions: {state.message}
        </p>
      )}

      {state.status === 'ready' && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Status</th>
              <th>Superseded by</th>
            </tr>
          </thead>
          <tbody>
            {state.decisions.map((decision) => (
              <DecisionRow key={decision.id} decision={decision} />
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}

export default App
