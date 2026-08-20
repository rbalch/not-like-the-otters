# T8 — Pane peek

**Status:** not started.
**Source:** handoff README, "Interactions & behavior". The reference is static — there is
nothing to copy here, only a described behaviour.

## Goal

Click a pane to expand it over the wall; the rest of the wall stays visible at the edges,
dimmed; Esc closes back to the wall.

## Scope

1. **The peek overlay** — the clicked pane expands over the grid, inset enough that the
   wall reads at the edges, with the remainder dimmed. Classical's `--shadow-lg` and
   `--radius-md` are the right tools; the dim is a `color-mix` over `--color-text`, as a
   local token.
2. **Esc closes.** Keydown on the overlay, not a global document listener that outlives
   the component.
3. **Peek is a modal surface, so build it as one.** `role="dialog"`, `aria-modal`,
   labelled by the pane's kicker, focus moved into it on open, focus returned to the
   originating pane on close, focus trapped while open. Retrofitting this later is far
   more expensive than doing it now.
4. **Panes become buttons, or get a button inside them.** A `<div onClick>` is not
   keyboard-reachable; the whole wall would be mouse-only. Whichever shape is chosen, Tab
   must reach every pane and Enter must open it.
5. **Reduced motion** — if the expand animates, it does not under `prefers-reduced-motion`.
6. **Content, not a copy.** The peeked pane renders the *same* component with more room,
   not a duplicated markup variant that can drift.
7. **Tests.** `WallPeek.test.tsx`: clicking a pane opens a dialog labelled by that pane,
   Esc closes it, focus lands inside on open and returns to the trigger on close, the
   wall's other panes remain in the DOM (they are dimmed, not unmounted), keyboard alone
   can open and close.

## Non-scope

- Deep-linking a peek to a URL hash. The view switch in T1 handles screens, not panes.
- Any action inside a peek. Still read-only — the handoff says nothing in this UI ever
  writes to `governance/`, and that survives the peek.

## Files

- `app/src/components/wall/WallPeek.tsx` (+ test)
- `app/src/components/wall/Pane.tsx` (make it activatable)

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                       # expect EXIT=0
npm run test --prefix app
grep -rn "document.addEventListener" app/src/components/wall/ ; echo "EXIT=$?"
# a global listener is allowed only with a matching removal in the same effect's
# cleanup — if this matches, the reviewer checks the cleanup rather than assuming it
```

## Done when

Every pane opens on click and on Enter, the peek is a focus-trapped labelled dialog, Esc
returns focus to the pane that opened it, the wall stays visible behind, and no listener
outlives the component.

## What you'll see — after `git pull` on the host

The wall becomes interactive, and the header hint stops lying.

- **Click any pane.** It expands over the wall, inset enough that you still see the other
  panes at the edges, dimmed behind it and slightly darkened. Same content, more room —
  the gate's stage list and the run's log should simply have more space, not a different
  layout.
- **Press Esc.** It closes back to the wall.

**Then do the whole thing without touching the mouse**, because this is where peek
interactions usually fall down:

- Tab until a pane has focus — there should be a visible ring on the pane itself, not just
  on something inside it.
- Enter opens the peek. **Focus should already be inside the peek** — Tab from there should
  cycle within it and never reach the dimmed wall behind.
- Esc closes, and **focus should land back on the pane you opened**, not at the top of the
  document. Tab once to confirm you're where you started.

If Tab escapes into the dimmed background while a peek is open, the trap isn't wired and
the peek is a dialog in appearance only.

**With reduced motion on**, the expand should snap rather than animate. It should still
open and close normally.

**One last look:** open a peek, then resize the window. The peek should follow the window
and the wall behind should stay visible at the edges at any size.

## Manual QA — T8

_(written back by the build loop on close)_
