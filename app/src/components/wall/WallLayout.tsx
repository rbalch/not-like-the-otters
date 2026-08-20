import type { ReactNode } from 'react'
import Pane from './Pane'
import './wall.css'

export interface WallLayoutProps {
  /** Icon rail content. Empty in T1 — the rail slot exists, its icons and
   * active/inactive states are T2's job, not this component's. */
  rail?: ReactNode
  /** Header's monospace branch/commit status line. A static placeholder
   * until a Tauri command exists to read it for real (M1/M5). */
  status?: ReactNode
  /** Header's right-aligned hint text. Aspirational until T8 wires the
   * peek interaction — the copy is intentionally accurate in advance. */
  hint?: ReactNode
  /** The gate column: the grid's narrow (268px) left pane. */
  gate?: ReactNode
  /** The run band: full width across the top of the right-hand side. */
  run?: ReactNode
  /** The promotion pane: left half of the bottom-right split. */
  promotion?: ReactNode
  /** The milestone pane: right half of the bottom-right split. */
  milestone?: ReactNode
}

/**
 * The wall's frame: icon rail, header bar, and the four-pane content grid
 * (gate / run / promotion / milestone). This component owns only the shape
 * — `gate`/`run`/`promotion`/`milestone` are empty until T3–T6 fill them in,
 * and `rail` is empty until T2 wires real icons. See
 * `docs/design_handoff_console_wall/README.md`, `reference.html#3a`.
 */
export default function WallLayout({
  rail,
  status = 'dev · static',
  hint = 'click a pane to peek · esc closes',
  gate,
  run,
  promotion,
  milestone,
}: WallLayoutProps) {
  return (
    <div className="wall">
      <div className="wall-rail" data-testid="wall-rail">
        {rail}
      </div>

      <div className="wall-main">
        <div className="wall-header" data-testid="wall-header">
          <span className="wall-header-title">The wall</span>
          <span className="wall-header-status">{status}</span>
          <span className="wall-header-hint">{hint}</span>
        </div>

        <div className="wall-grid">
          <Pane className="wall-gate" data-testid="wall-gate">
            {gate}
          </Pane>

          <div className="wall-right">
            <Pane className="wall-run" data-testid="wall-run">
              {run}
            </Pane>

            <div className="wall-bottom">
              <Pane className="wall-promotion" data-testid="wall-promotion">
                {promotion}
              </Pane>
              <Pane className="wall-milestone" data-testid="wall-milestone">
                {milestone}
              </Pane>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
