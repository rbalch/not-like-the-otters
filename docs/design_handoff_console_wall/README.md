# Handoff: Console wall (M1/M5 direction)

## Overview
Design reference for the "wall" layout — the multi-pane console (gate status, active build-loop run, promotion candidates, current milestone) that M1 (sightings→proposed rules) and M5 (outer gate) will need a screen for. **The app today (M2, done) has only the single decisions window** (`app/src/App.tsx` — otter brand mark + `DecisionTable`). This package is *not* a re-skin of that screen; it's the target layout for the screen(s) M1/M5 add next.

## About the design files
The bundled HTML (`reference.html`) is a **design reference**, built as flat markup with inline styles for speed of iteration — not code to copy in. Recreate it in `app/` as React components using the app's existing conventions (see `App.tsx`, `DecisionTable.tsx`) and Classical via `var(--token)`, same as the rest of `app/src/`.

**Why the previous pass didn't parse for the builder agent:** the reference file is a `.dc.html` — a design-tool authoring format (custom `<x-import>`/`<helmet>` tags, a runtime script) that only renders inside this design tool. It is not valid standalone HTML/CSS a Read/Grep-only agent can parse as source. `reference.html` in this package is the same visuals exported to plain, static HTML+CSS — open it in any browser, view-source it, grep it.

## Fidelity
**Hifi**, and already Classical-token-only — every color, weight and radius below is a `var(--token)` name from `app/src/classical.css`, not an invented value. No raw hex, no font outside Cormorant Garamond/Lora — this reference was built under the same constraint `controls/fitness/design_adherence.py` enforces, so porting it should not trip DEC-1.

Data shown (run logs, finding IDs, milestone copy) is illustrative, not real — M1's actual data model should drive the real component.

## Screens
`reference.html` has two: `#3a` (steady state) and its `#4b` variant (gate red). Jump to either with the URL hash.

### `#3a` — the wall, steady state
**Purpose:** at-a-glance status; this is what's open all the time.

**Layout** (1280×840 reference frame; scale to window size):
- Root: `display:flex`, full height.
- **Icon rail**, 52px fixed width, `border-right:1px solid var(--color-divider)`, column of 30×30 icon buttons (Lucide icons), `gap: var(--space-3)`. The active item (Wall) gets `border:1px solid var(--color-accent); color:var(--color-accent)`; inactive items `color: color-mix(in srgb, var(--color-text) 45%, transparent)`.
- **Header bar**: `padding: var(--space-2) var(--space-4)`, bottom hairline, app name in `var(--font-heading)` 600 15px, a monospace status line, right-aligned hint text.
- **Content grid**: `grid-template-columns: 268px 1fr; gap:1px; background:var(--color-divider)` (the 1px gaps read as hairlines between panes).
  - **Gate column** (268px): kicker label, otter sprite (see Assets), `var(--font-heading)` 52px status word ("Green"/"Red"), a 4-row stage list, a "rules in force" footer stat.
  - **Right side**: `grid-template-rows: 1fr 1fr` — **Run** band on top (full width), then a second row split `1.1fr 1fr` into **Promotion** and **Milestone**.
    - Run band: pipeline breadcrumb (builder → boundary-reviewer → reviewer → findings → re-review), then a monospace log block, `font: 11.5px/1.75 ui-monospace`, `white-space:nowrap`, one line per event, non-nowrap wrapping avoided by giving this pane the full width.
    - Promotion: ranked list of findings, each row = id + text + a 3-cell "sighting" bar (filled cells = `var(--color-accent)`, empty = `1px solid var(--color-divider)`), earned ones get a small pill (`background:var(--color-accent-100); color:var(--color-accent-800)`).
    - Milestone: kicker, `var(--font-heading)` 24px title, justified body copy, a checklist (✓ in `var(--color-accent-700)` for done, `·` dim for pending), a "next" footer.

All panes: `padding: var(--space-4)`, section kicker = `font:600 10px var(--font-heading); letter-spacing:.14em; text-transform:uppercase; color:var(--color-accent-700)`, followed by a `1px` `var(--color-divider)` rule.

### `#4b` — gate red
Same grid. Differences only:
- Otter swaps to the alert/red sprite (see Assets).
- Gate word → "Red", color `var(--color-accent-900)`.
- Stage list: failing stage gets `color:var(--color-accent-800)` + underline; stages after it read "not reached" in a dim tone — **the gate fails fast; only the earliest failure is ever shown.**
- Run band shows the loop halted mid-task, last log lines in `var(--color-accent-800)`.

## Interactions & behavior
Static reference — no clicks wired. Intended behavior for the real build: click a pane to expand it (a "peek") over the wall; the rest of the wall stays visible at the edges, dimmed; Esc closes back to the wall. Read-only throughout — nothing in this UI ever writes to `governance/`.

## Design tokens used
All from `app/src/classical.css` (already vendored — nothing new to add):
- Color: `--color-bg`, `--color-text`, `--color-surface`, `--color-divider`, `--color-accent`, `--color-accent-100/700/800/900`, `--color-neutral-300/400/800`.
- Type: `--font-heading` (Cormorant Garamond, weight `--font-heading-weight` = 600 for labels; headline sizes go lighter/normal per Classical's rule), `--font-body` (Lora). Monospace (log lines, ids, stats) is a deliberate exception to Classical's two-family rule — use the system UI-monospace stack (`ui-monospace, Menlo, monospace`), never a third serif/sans.
- Spacing: `--space-2/3/4/6/8`. Radius: `--radius-sm/md`.

No `--color-danger` (that's `tokens-local.css`, unrelated to this screen).

## Assets
- **Otter sprites**: `reference.html` already uses the app's real assets (`assets/otter-green.png` / `otter-red.png` in this package — same files as `app/src/assets/otter-green.png` / `otter-red.png`, via `BrandMark.tsx` / `otters.ts`'s `otters` map). Green = calm/steady, red = alert. Reuse that same map — don't add a third image variant. Two sizes shown: ~31px in the icon rail, ~183px in the gate column; both are fine off the existing 256px masters (`image-rendering:pixelated` matches the app's existing treatment, drop it if the port renders these as photographic rather than pixel-art at this size).
- All icons are Lucide, per the design system guide — pick real Lucide icon names for rail items (wall/grid, rules/book, decisions/git-commit, findings/inbox, milestones/flag) rather than the reference's hand-drawn stand-ins.

## Files
- `reference.html` — both screens, plain HTML/CSS, no build step. Open directly or view-source. Anchors: `#3a` (steady), `#4b` (gate red).
- `assets/otter-green.png`, `assets/otter-red.png` — the same files already vendored at `app/src/assets/`, included here only so `reference.html` renders standalone.
