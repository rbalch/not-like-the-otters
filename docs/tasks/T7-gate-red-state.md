# T7 — Gate red

**Status:** not started.
**Source:** `reference.html#4b`.

## Goal

The red state. **`#4b` is not a second screen** — the handoff lists it as "same grid,
differences only". It is the same components fed a failing `GateStatus` and a halted
`RunStatus`.

## Scope

1. **A red fixture**, not a red component. If T3 and T4 typed their data properly this
   item adds no new component files. If it turns out to need one, that is a T3/T4 design
   flaw worth reporting rather than papering over.
2. **The otter swaps to `alert`.** Via `otters.ts`'s existing map — this is the M1 flip
   `BrandMark`'s `otter` prop was built for, arriving early for the wall. Both the rail
   sprite and the 183px gate sprite swap together.
3. **Status word "Red"** in `var(--color-accent-900)`.
4. **Fail-fast stage rendering, and this is the load-bearing part.** The failing stage
   gets `var(--color-accent-800)` and an underline; **every stage after it reads "not
   reached"** in a dim tone. The handoff states the reason: `make check` fails at the
   first stage, so a red gate genuinely only knows about the earliest failure.
   A UI that showed later stages as passing, or as failing, would be inventing a result
   the gate never produced. Enforce it in the type or in a helper — a `GateStatus` with a
   `pass` after a `fail` is unrepresentable or normalised, not merely undrawn.
5. **The halted run** — the log stops mid-task, the last lines in
   `var(--color-accent-800)`, and the live caret is **gone**, because the loop is not
   running. A pulsing caret on a halted run is the same lie in miniature.
6. **Tests.** `GatePane.test.tsx` / `RunPane.test.tsx` extensions: a failing status
   renders "Red" and the alert otter; stages after the failure read "not reached" and
   never "✓"; a hand-built `GateStatus` with a pass following a fail is rejected or
   normalised (assert whichever you implemented); a halted run renders no caret.

## Non-scope

- Deciding *when* the gate is red. No data source. The fixture is switched by hand or by a
  dev-only toggle; if a toggle is added it must not ship in a release build.

## Files

- `app/src/lib/wall.ts` (red fixtures + the fail-fast normaliser)
- existing pane tests (extend)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                       # expect EXIT=0
npm run test --prefix app
git diff --stat                                   # expect NO new pane component files
```

Negative check — the fail-fast invariant is enforced, not just drawn:

```sh
# construct { stages: [fail, pass] } in a test and assert it cannot render a ✓ after
# the failure. Written as a committed case, not a probe.
```

## Done when

Feeding the red fixture produces `#4b` from the same components, the alert otter shows in
both places, no stage after the failure claims a result, the halted run has no caret, and
no new pane component was needed.

## What you'll see — after `git pull` on the host

**You need a way to flip the fixture, and it is part of this item.** A hash parameter
(`#wall?gate=red`) or an equivalent dev-only switch — whatever T7 implemented, it is named
in the commit message. Without one there is nothing to look at, so if the builder shipped
red fixtures with no way to reach them, that is a finding.

Flip it and compare against the green wall side by side:

- The otter goes **red in both places at once** — the 183px gate portrait and the 31px rail
  sprite. If only one swaps, they are not reading the same map.
- The status word reads **"Red"** in the deepest gold.
- **The stage list is the important part.** The failing stage is dark gold and underlined;
  **every stage below it reads "not reached"** and dim. There must be no ✓ anywhere below
  the failure. A tick under a failed stage is the UI claiming a result `make check` never
  computed, because it stopped.
- The run band's log **stops mid-task**, last lines in dark gold, and the **caret is gone**.
  A pulsing caret on a halted loop is the same lie in miniature — watch for a few seconds
  to be sure.

**Flip back to green and confirm nothing stuck.** The otter, the word, the stage ticks and
the caret should all return. State that leaks one way is the usual failure here.

## Manual QA — T7

_(written back by the build loop on close)_
