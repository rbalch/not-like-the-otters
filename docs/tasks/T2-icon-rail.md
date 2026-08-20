# T2 — The icon rail

**Status:** not started.
**Source:** `reference.html#3a`, rail column; handoff README "Assets".

## Goal

The 52px left rail: otter sprite, hairline, five icon buttons, a vertical milestone tag
pinned to the bottom.

## Scope

1. **Icon source — decide and record.** The handoff says "All icons are Lucide … pick real
   Lucide icon names rather than the reference's hand-drawn stand-ins." Two options, and
   the choice needs stating in the commit message either way:
   - add `lucide-react` as a dependency (tree-shaken, ships offline, no CSP issue), or
   - vendor the five SVG paths into a local `icons.tsx`.
   **Recommended: `lucide-react`.** Five icons today, but the rail grows with every
   milestone and hand-vendoring paths is the kind of thing that quietly drifts from the
   design system. If the dependency is refused, vendoring is a clean fallback — say which
   and why.
2. **Five rail items**, mapped to real Lucide names: wall → `LayoutGrid`, rules → `Book`,
   decisions → `GitCommitVertical` (or `Milestone`-adjacent equivalent), findings →
   `Inbox`, milestones → `Flag`. 30×30 buttons, 15px icons, `gap: var(--space-3)`.
3. **Active and inactive states.** Active: `border: 1px solid var(--color-accent);
   color: var(--color-accent)`; inactive: the 45% text tint token from T1.
4. **The otter sprite at ~31px**, framed like the reference (3px `--color-surface` border,
   1px `--color-divider` outline, `--radius-sm`). Reuse `otters.ts` via `BrandMark` — see
   `README.md`; do **not** re-import the PNG or set `image-rendering: pixelated`.
5. **The findings badge** — a 5px `var(--color-accent)` dot, top-right of the findings
   icon, shown only when there is something to see. Prop-driven, defaults to off.
6. **The bottom milestone tag** — `writing-mode: vertical-rl`, 9px `var(--font-mono)`,
   `letter-spacing:.1em`, 35% text tint, `margin-top:auto`.
7. **Accessibility, and it is not optional.** The reference uses bare `<div title="…">`.
   These are navigation controls: real `<button>` elements with accessible names, the
   active one marked `aria-current="page"`. Test it by role and name.
8. **Tests.** `IconRail.test.tsx`: five buttons queryable by accessible name, exactly one
   `aria-current`, badge appears and disappears with its prop, clicking a button fires the
   view-switch callback.

## Non-scope

- Making the inert rail items navigate anywhere. Rules, findings and milestones have no
  screens until M1/M5 — they render, they are disabled or no-op, and the test says so.
- Pane content, peek, red state.

## Files

- `app/src/components/wall/IconRail.tsx` (+ test)
- `app/package.json` if the dependency route is taken
- `app/src/components/wall/icons.tsx` if the vendoring route is taken

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                       # expect EXIT=0
npm run test --prefix app
npm run build --prefix app                        # a new dep must not break the bundle
grep -rniE 'fonts\.(googleapis|gstatic)\.com|cdn' app/dist ; echo "EXIT=$?"
# expect EXIT=1 — an icon library that reaches for a network asset is disqualified
```

## Done when

The rail renders five named, keyboard-reachable icon buttons with the wall item active,
the otter above them and the milestone tag at the bottom, `make check` green, and the
bundle still contains no remote references.

## What you'll see — after `git pull` on the host

The left column fills in:

- The **green otter at ~31px** at the top, in a thin surface-coloured frame with a hairline
  outline. It should look smooth, not blocky — if it reads as chunky pixels, `pixelated`
  crept in against the README's instruction.
- A short hairline under it, then **five icon buttons** in a column: grid, book,
  commit-ish, inbox, flag. The **grid (wall) one is boxed in gold with gold strokes**; the
  other four are flat and dim.
- A small **gold dot** on the findings (inbox) icon, if the fixture turns the badge on.
- **"M1" running vertically** at the bottom of the rail, tiny and dim.

**Two checks worth doing by hand:**

- **Tab through the window.** Every rail item should take focus with a visible ring, and
  Enter on the wall or decisions item should switch views. If Tab skips the rail entirely,
  they shipped as `<div>`s and the whole wall is mouse-only.
- **Hover each icon.** The three inert items (rules, findings, milestones) should do
  nothing and not pretend to be clickable — no cursor change into a pointer over a dead
  control.

## Manual QA — T2

_(written back by the build loop on close)_
