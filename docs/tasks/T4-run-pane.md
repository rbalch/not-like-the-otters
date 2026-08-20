# T4 — The run pane

**Status:** not started.
**Source:** `reference.html#3a`, full-width band, top of the right grid.

## Goal

The build-loop run band: kicker with intent text and a live dot, the pipeline breadcrumb,
and the monospace log block.

## Scope

1. **Types and fixture** in `app/src/lib/wall.ts`:
   ```ts
   type PipelineStage = 'builder' | 'boundary-reviewer' | 'reviewer' | 'findings' | 're-review' | 'approve'
   interface RunLogLine { at: string; source: string; text: string; emphasis: 'normal' | 'flag' | 'finding' | 'live' }
   interface RunStatus { intent: string; stage: PipelineStage; live: boolean; findings: number; log: RunLogLine[] }
   ```
2. **The breadcrumb** — six steps with `→` separators, past steps in `var(--color-text)`,
   current in `var(--color-accent-700)` with a `1px solid var(--color-accent)` underline,
   future in the 45% tint. Right-aligned finding count.
3. **The log block** — bordered, `--radius-sm`, `padding: var(--space-3)`,
   `font: 400 11.5px/1.75 var(--font-mono)`, `font-variant-numeric: tabular-nums`,
   `white-space: nowrap`, `overflow: hidden`. One line per event.
   **The reference pads its source column with `&nbsp;` runs.** Do not port that — align
   the timestamp and source columns with CSS (fixed-width spans), so a longer agent name
   never wraps the layout and a screen reader does not read a wall of spaces.
4. **The streaming caret** on the last line when `live` is true — the reference animates a
   `▋` with `streampulse 1.2s ease-in-out infinite`. Port the keyframes; respect
   `prefers-reduced-motion` and drop the animation there.
5. **Emphasis colours** — `flag` and `finding` markers in `var(--color-accent-700)`, the
   live line in full `var(--color-text)`, the rest at the 72% tint.
6. **Overflow is a real case, not a nicety.** A real run emits hundreds of lines into a
   fixed-height pane. Decide and implement: newest-last with the block scrolled to the
   bottom, or a capped tail. Say which in the commit; test that N+1 lines does not blow
   the grid row's height.
7. **Tests.** `RunPane.test.tsx`: breadcrumb marks exactly one current stage and past vs
   future correctly, each log line renders its own time/source/text (transposition-proof),
   the caret appears only when `live`, an oversized log does not escape the pane.

## Non-scope

- Reading a real build-loop run from anywhere. There is no such data source and this task
  does not create one.
- The halted/red run. T7.

## Files

- `app/src/lib/wall.ts` (extend)
- `app/src/components/wall/RunPane.tsx` (+ test)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                                          # expect EXIT=0
npm run test --prefix app
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"  # expect ok / 0
grep -c "&nbsp;" app/src/components/wall/RunPane.tsx   # expect 0
```

## Done when

The run band renders the reference's log and breadcrumb from a fixture, columns align
without `&nbsp;` padding, the caret animates only when live and never under reduced
motion, and a 500-line fixture leaves the grid intact.

## What you'll see — after `git pull` on the host

The **wide band across the top-right** fills in:

- Kicker **THE RUN**, the intent text in monospace beside it, and a small gold dot with a
  status word hard right.
- A **breadcrumb**: builder → boundary-reviewer → reviewer → findings → re-review →
  approve ≥ 4/5. Steps already passed are full-strength, the current one is **gold with a
  gold underline**, and the ones ahead are dim. Exactly one should be underlined.
- A **bordered log block** filling the rest of the band: timestamped monospace lines, one
  per event. The timestamps must form a **clean left column** and the agent names a clean
  second column — if the source names look ragged or drift right, the `&nbsp;` padding got
  ported instead of CSS alignment.
- The **last line ends in a pulsing block caret**. Watch it for a few seconds; it should
  breathe, not blink hard.

**Two checks by hand:**

- **Narrow the window a lot.** Log lines must clip at the pane edge, not wrap. A wrapped
  log line means `white-space: nowrap` was lost and the band's row height will fight the
  grid.
- **Turn on reduced motion** (NixOS: your desktop's accessibility setting, or launch with
  the GTK/portal preference set). The caret should go static. It stays visible — it just
  stops animating.

## Manual QA — T4

_(written back by the build loop on close)_
