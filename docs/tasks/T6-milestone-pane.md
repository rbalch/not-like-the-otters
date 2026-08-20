# T6 — The milestone pane

**Status:** not started.
**Source:** `reference.html#3a`, bottom-right of the right grid (`1fr`).

## Goal

The current-milestone pane: kicker with status, a 24px heading-font title, justified body
copy, a done/pending checklist, and the "next" footer.

## Scope

1. **Types and fixture** in `app/src/lib/wall.ts`:
   ```ts
   interface MilestoneItem { text: string; done: boolean }
   interface MilestoneState {
     id: string; status: string; title: string; summary: string
     items: MilestoneItem[]
     next: { id: string; title: string; blockedOn: string | null } | null
   }
   ```
2. **Title** in `var(--font-heading)` weight 400, 24px — note the weight: Classical's
   `--font-heading-weight` 600 is for small labels, display text goes lighter. The
   reference is explicit about this and it is easy to get wrong by reflex.
3. **Body copy** at 12.5px/1.6, 72% tint, `text-align: justify`, `text-wrap: pretty`.
4. **Checklist** — `✓` in `var(--color-accent-700)` for done items (dim text), `·` at the
   35% tint for pending (full-strength text). Note the inversion: **done items are dimmed
   and pending items are bright**, which is the opposite of the reflex and is correct —
   the pane is for reading what is left.
   The tick and dot are decoration; give the list real `<ul>`/`<li>` semantics and put the
   done/pending state somewhere a screen reader reaches, not in a glyph.
5. **The next footer** — "NEXT" kicker plus the following milestone, with its `blockedOn`
   note in mono at the 45% tint when present, and nothing when `null`.
6. **`next: null` and an empty `items` list both render.** The last milestone has no next.
7. **Tests.** `MilestonePane.test.tsx`: done and pending items are distinguishable by
   role/state rather than glyph, `next: null` renders no footer text, `blockedOn: null`
   renders the milestone without a blocker note, empty `items` does not crash.

## Non-scope

- Parsing `docs/milestones/*.md`. Same seam argument as T5 — fixtures only, M1 owns the
  data. (Note the reference's own fixture copy is stale, calling M2 "the outer gate";
  that is M5. Illustrative data, per the handoff. Do not treat it as the milestone list.)

## Files

- `app/src/lib/wall.ts` (extend)
- `app/src/components/wall/MilestonePane.tsx` (+ test)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                                          # expect EXIT=0
npm run test --prefix app
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"  # expect ok / 0
grep -rn "docs/milestones" app/src ; echo "EXIT=$?"                  # expect EXIT=1
```

## Done when

The pane renders title, copy, checklist and next footer from a fixture; done and pending
are distinguishable without seeing the glyph; `next: null` and empty items both render.

## What you'll see — after `git pull` on the host

The **bottom-right pane** fills in, completing the wall:

- Kicker **MILESTONE**, `M1 · in progress` dim on the right.
- The title **"Sightings to proposed rules"** at 24px in Cormorant — again in the *light*
  weight, not the semibold used for labels. Beside the 10px gold kicker above it the
  contrast in weight should be obvious.
- A short justified paragraph beneath it, softer than the body text elsewhere.
- A **four-item checklist**. Note the inversion and check it deliberately: **done items
  have a gold ✓ and dimmed text; pending items have a faint dot and full-strength text.**
  It looks backwards for about two seconds and then makes sense — the pane is for reading
  what's left, not admiring what's done. If done items are the bright ones, it got
  "corrected" by reflex.
- A footer: **NEXT** and the following milestone, with a dim monospace blocker note.

**One check by hand:** with a screen reader, or just by tabbing/inspecting, the done and
pending states must be reachable as *state*, not only as a ✓ or · glyph. A checklist whose
only signal is a decorative character conveys nothing to a screen reader.

At this point all four panes are populated — **stand back and look at the whole wall.**
The hairlines should form one continuous grid, all four panes should share the same
`--space-4` inset, and every kicker should sit on the same baseline as its neighbours'.

## Manual QA — T6

_(written back by the build loop on close)_
