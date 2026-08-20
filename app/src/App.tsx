import { useEffect, useState } from 'react'
import './App.css'
import { fetchDecisions, type Decision } from './lib/decisions'
import DecisionTable from './components/DecisionTable'
import BrandMark from './components/BrandMark'
import WallLayout from './components/wall/WallLayout'
import { viewFromHash, type View } from './lib/view'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; decisions: Decision[] }

interface AppProps {
  /** Which view an unrecognised (or empty) hash falls back to. The real
   * app's `main.tsx` passes `'wall'`; left at `'decisions'` here so `<App
   * />`, rendered with no hash, keeps rendering the decisions screen the
   * way `App.test.tsx` already expects. */
  defaultView?: View
}

function App({ defaultView = 'decisions' }: AppProps) {
  const [view, setView] = useState<View>(
    () => viewFromHash(window.location.hash) ?? defaultView,
  )
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    const onHashChange = () =>
      setView(viewFromHash(window.location.hash) ?? defaultView)
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [defaultView])

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

  if (view === 'wall') {
    return <WallLayout />
  }

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
