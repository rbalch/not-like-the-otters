# T3 — The gate pane

**Status:** not started.
**Source:** `reference.html#3a`, 268px left column.

## Goal

The gate column: kicker, otter at 183px, a 52px status word, the timing line, a stage
list, the numbered check list, and the "rules in force" footer stat.

## Scope

1. **Types first, in `app/src/lib/wall.ts`.** This pane is where the data seam gets
   defined, so define it deliberately:
   ```ts
   type StageState = 'pass' | 'fail' | 'not-reached'
   interface GateStage { name: string; state: StageState; detail: string | null }
   interface GateStatus {
     ok: boolean
     stages: GateStage[]        // python, rust, typescript
     checks: GateCheck[]        // controls, views --check, governance, tests
     rulesInForce: { count: number; summary: string }
     lastRun: { durationSeconds: number; at: string } | null
   }
   ```
   Adjust the shape if the reference disagrees — but it is typed, it is in one file, and
   `GatePane` takes it as a prop.
2. **A fixture provider** in the same file, returning the reference's illustrative values.
   Named so nobody mistakes it for real data (`fixtureGateStatus`), with a comment saying
   M5 replaces it with a Tauri command.
3. **`GatePane`** rendering the whole column: kicker + rule, otter (`BrandMark`, 183px,
   `calm`), status word in `var(--font-heading)` weight 400, 52px, `line-height:1`,
   `letter-spacing:-.025em`, the mono timing line, the stage rows (name left, mark right),
   the four numbered check rows, and the footer stat with a 26px heading-font number.
4. **`lastRun: null` renders something sensible** — the gate has never run in a fresh
   clone. Not a crash, not "NaN s ago". Test it.
5. **Tests.** `GatePane.test.tsx`, written before the component (this is a rendering
   component, so tests-first is a preference, not the mandate — but the null case and the
   per-stage correspondence are worth writing first): status word tracks `ok`, each stage
   renders its own name against its own state (build the fixture so a transposition
   fails), the rules count and summary both render, `lastRun: null` renders the empty
   state.

## Non-scope

- **Any real gate data.** No `make check` invocation, no reading `governance/`, no new
  Tauri command. If the builder feels the pull to add one, that is a blocked-by-scope
  report, not a patch.
- The red variant. T7 — but do not paint yourself into a corner: `ok: boolean` and
  `StageState` exist in T3 precisely so T7 is a data change, not a rewrite.

## Files

- `app/src/lib/wall.ts` (new)
- `app/src/components/wall/GatePane.tsx` (+ test)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                                          # expect EXIT=0
npm run test --prefix app
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"  # expect ok / 0
grep -rn "invoke\|@tauri-apps/api" app/src/lib/wall.ts ; echo "EXIT=$?"
# expect EXIT=1 — the fixture seam must not have quietly grown an IPC call
```

## Done when

The gate column renders the reference's steady state from a fixture, the otter reads
green at 183px, `lastRun: null` degrades cleanly, and no data path was invented.

## What you'll see — after `git pull` on the host

The **left column fills in** and it is the first pane with real presence:

- Kicker **THE GATE** in small gold caps, then a hairline.
- The **green otter at 183px**, framed. Large enough that the code rain reads clearly as
  green — this is the status light, so if it looks brown-tinted, Classical's `.plate`
  filter got applied where it should not have been (see M2.4).
- The word **"Green"** underneath, huge (52px) in Cormorant, and in the *light* weight —
  not bold. If it looks heavy and cramped, the 600 label weight was used where 400 display
  weight belongs.
- A dim monospace line: `make check · 12.4s · 3m ago`.
- Three stage rows — python / rust / typescript — each with a gold ✓ hard right.
- Four numbered rows below: controls, views --check, governance, tests, each with a dim
  right-hand value.
- Pinned to the bottom: **RULES IN FORCE**, a large **2**, and `DEC-0, DEC-1 · both
  enforced`.

**The numbers are illustrative and will not match your repo.** That is expected — the pane
is fixture-fed. Do not report the timing or test count as wrong; report it as wrong only
if it claims to be live.

**Resize the window short.** The footer stat should stay pinned to the bottom and the
column should not spill past the grid.

## Manual QA — T3

_(written back by the build loop on close)_
