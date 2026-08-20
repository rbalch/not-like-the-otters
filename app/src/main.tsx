import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './classical.css'
import './tokens-local.css'
import './index.css'
import App from './App.tsx'

// The wall is what should be open all the time
// (docs/design_handoff_console_wall/README.md). That default lives here, as
// a prop, rather than as a `location.hash` write: mutating the URL at boot
// would leave a history entry and fight a user who bookmarks or hand-edits
// the hash. `App`'s own `viewFromHash` still wins whenever the hash names a
// real view — this only supplies what an unrecognised or empty hash falls
// back to.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App defaultView="wall" />
  </StrictMode>,
)
