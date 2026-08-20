# T5 — The promotion pane

**Status:** not started.
**Source:** `reference.html#3a`, bottom-left of the right grid (`1.1fr`).

## Goal

The ranked promotion list: finding id, text, a three-cell sighting bar, an earned pill,
and the bin-count footer.

## Scope

1. **Types and fixture** in `app/src/lib/wall.ts`:
   ```ts
   interface PromotionCandidate { id: string; text: string; sightings: number; earned: boolean }
   interface PromotionState { candidates: PromotionCandidate[]; bins: { one: number; two: number; three: number }; open: number }
   ```
   `earned` is derived from `sightings >= 3` — derive it in one place and test that,
   rather than letting a fixture set the two independently. The rule of three is the whole
   point of this pane and a row showing two filled cells beside an "earned" pill would be
   a lie about the harness's central mechanic.
2. **Rows** — 30px mono id column at the 45% tint, 12.5px body text, right-aligned
   sighting bar. Hairline `border-bottom` on every row but the last.
3. **The sighting bar** — three 7×14 cells. Filled: `background: var(--color-accent)`.
   Empty: `1px solid var(--color-divider)`. **`sightings` above 3 must not render a fourth
   cell** and must not overflow — clamp, and test the clamp.
4. **The earned pill** — `background: var(--color-accent-100);
   color: var(--color-accent-800)`, on rows at three sightings.
5. **The footer** — `bin 1 · N`, `bin 2 · N` (in `var(--color-accent-800)`), `bin 3 · N`,
   and the right-aligned "% middle" figure. **Compute the percentage, do not store it** —
   bin 2 over the total. Zero findings must render something, not `NaN%`. Test both.
6. **Tests.** `PromotionPane.test.tsx`: filled-cell count matches each row's sightings,
   the pill appears at exactly three and not at two, `sightings: 7` renders three cells,
   the percentage matches the bin counts, an empty state renders.

## Non-scope

- Reading `docs/ledger-findings.md`. That parse is **M1's job**, and doing it here would
  put a governance-file reader in the webview — the seam the boundary reviewer exists to
  catch. Fixtures only.
- Any approve/promote action. The wall is read-only; the handoff says so and it is right.

## Files

- `app/src/lib/wall.ts` (extend)
- `app/src/components/wall/PromotionPane.tsx` (+ test)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                                          # expect EXIT=0
npm run test --prefix app
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"  # expect ok / 0
grep -rn "ledger-findings\|governance/" app/src ; echo "EXIT=$?"     # expect EXIT=1
```

## Done when

The list renders the reference's five candidates with correct sighting bars, the earned
pill fires only at three, the bin footer computes its own percentage, and no code under
`app/src/` names a governance path.

## What you'll see — after `git pull` on the host

The **bottom-left pane of the right grid** fills in:

- Kicker **PROMOTION**, with `bin 2 · 9 open · 1 earned` dim on the right.
- **Five rows**, each: a dim monospace finding id (F-7, F-4, F-9, F-2, F-11), the finding
  text, and a **three-cell bar** hard right — filled cells solid gold, empty cells a
  hairline outline. Hairline dividers between rows.
- The row with **three filled cells** carries a small pale-gold pill. Rows with two or
  fewer must not.
- A footer: `bin 1 · N`, `bin 2 · N` (darker gold), `bin 3 · N`, and a right-aligned
  percentage.

**The one thing to actually check with your eyes:** count filled cells against the pill.
A row showing two filled cells beside an "earned" pill is the pane lying about the rule of
three, which is the mechanic this entire project is built on. It should be impossible by
construction — the pill is derived, not stored — but this is the cheapest place to catch
it if it isn't.

**The findings are illustrative**, not your real ledger. F-7 in this pane is not F-7 in
`docs/ledger-findings.md`. Reading real findings is M1's job.

## Manual QA — T5

_(written back by the build loop on close)_
