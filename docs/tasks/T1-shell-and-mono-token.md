# T1 — Shell, view switch, and the mono token

**Status:** done — closed 2026-08-19, APPROVE 5/5 (boundary) and 4/5 (correctness).
**Source:** `docs/design_handoff_console_wall/README.md`, `reference.html#3a` (root layout only).

## Goal

Stand up the wall's frame and the primitives every pane needs, and settle the mono-font
question before any pane hardcodes a font stack. Nothing inside the panes — four empty
bordered boxes in the right grid positions is a complete T1.

## Scope

1. **`--font-mono` in `app/src/tokens-local.css`**, value `ui-monospace, Menlo, monospace`.
   Every later item references `var(--font-mono)`. See the DEC-1 trap in `README.md` —
   the raw stack in a component file fails the gate, measured.
2. **Local tokens for the repeated `color-mix` tints.** The reference uses
   `color-mix(in srgb, var(--color-text) N%, transparent)` at roughly 35/40/45/50/55/72%.
   Define them once in `tokens-local.css`; do not repeat the expression per component.
3. **A view switch.** The wall and the existing decisions screen must coexist.
   Recommended: a `useState` view key in `App.tsx` plus a `#hash` read on mount — no
   router dependency for two screens. `Wall` and `Decisions` are the only live views;
   the other rail items are inert until M1/M5.
4. **`WallLayout`** — `display:flex` root, rail slot (52px, `border-right` hairline),
   header bar (`padding: var(--space-2) var(--space-4)`, bottom hairline, app name in
   `var(--font-heading)` 600 15px, a monospace status line, right-aligned hint text), and
   the content grid: `grid-template-columns: 268px 1fr; gap:1px;
   background: var(--color-divider)`.
5. **`Pane`** — the shared pane box: `background: var(--color-bg)`,
   `padding: var(--space-4)`, `min-height:0; min-width:0`, flex column. The 1px grid gaps
   over a divider-coloured background are what draw the hairlines; panes must not draw
   their own borders.
6. **`Kicker`** — the section label: `font: 600 10px var(--font-heading);
   letter-spacing:.14em; text-transform:uppercase; color: var(--color-accent-700)`,
   followed by a 1px `var(--color-divider)` rule. Takes optional right-aligned meta text,
   which four of the five panes use.
7. **Tests.** `WallLayout.test.tsx` and `Pane.test.tsx`: the grid renders its named
   regions, the rail slot is present, `Kicker` renders label and meta and the rule.

## Non-scope

- Any pane content. T3–T6.
- The icon rail's icons and states. T2.
- The peek interaction. T8.
- Any new Tauri command or data fetch. The wall is read-only and fixture-fed until M1/M5.

## Files

- `app/src/tokens-local.css` — add tokens, never edit `classical.css`
- `app/src/App.tsx` — view switch
- `app/src/components/wall/WallLayout.tsx`, `Pane.tsx`, `Kicker.tsx` (+ tests)
- `app/src/App.css` or a wall stylesheet — classes, not inline styles

## Acceptance criteria

```sh
make check ; echo "EXIT=$?"                                  # expect EXIT=0
npm run test --prefix app                                    # existing 17 pass + new
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"   # expect ok / 0
grep -rn "Menlo" app/src --include=*.tsx --include=*.css | grep -v tokens-local.css
# expect NO output — the only literal Menlo in the tree is the token definition
```

Negative check — the exemption is doing real work, not the allowlist:

```sh
printf '.x { font-family: ui-monospace, Menlo, monospace; }\n' > app/src/__probe.css
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"   # expect FAIL / 1
rm -f app/src/__probe.css
```

## Done when

Navigating to the wall shows the rail column, the header bar, and a 268px + 1fr grid of
empty panes separated by hairlines, in Classical, with `make check` green. The decisions
screen still renders unchanged and `App.test.tsx` still passes untouched.

## What you'll see — after `git pull` on the host

```sh
npm run tauri dev
```

**A frame, and nothing in it.** That is the correct T1 result — resist judging it as
unfinished.

- The window opens on the **wall**, not the decisions table. A 52px empty column down the
  left with a hairline on its right edge; a header bar across the top reading "The wall"
  in Cormorant Garamond, a monospace branch/commit line beside it, and dim right-aligned
  hint text ("click a pane to peek · esc closes" — it lies until T8, which is fine).
- Below that, **four empty boxes**: a narrow one down the left at 268px, and three to its
  right stacked one-over-two. They are separated by **hairlines, not gaps** — the 1px grid
  gutters show the divider colour through from behind. If you see white or grey channels
  between panes, the pane backgrounds or the grid background are wrong.
- Warm off-white ground throughout. No purple, no pure white.

**The old screen must still be reachable and unchanged.** However the view switch landed
(hash or a rail click), get to the decisions table and confirm it looks exactly as it did
at M2 close: green otter, Cormorant heading, Lora table, status pills. T1 adds a screen;
it does not touch that one.

**Resize the window narrow and tall.** The grid should hold its proportions and the panes
should not spill. Content overflow is not yet testable — there is no content.

## Manual QA — T1

Run from the repo root unless noted. The container cannot open a window — everything
under **On the host** is a human-only gate.

### In the container

```sh
make check ; echo "EXIT=$?"                 # expect EXIT=0
npm run test --prefix app                   # expect 8 files, 35 tests, all passing
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"   # expect ok / 0
```

The 35 break down as 17 pre-existing + 13 wall primitives + 5 view switch.

**The mono literal appears exactly once in the tree:**

```sh
grep -rn "Menlo" app/src --include=*.tsx --include=*.css --include=*.ts | grep -v tokens-local.css
# expect NO output
```

**The M2 screen's test was never touched:**

```sh
git diff 64c5d62..HEAD -- app/src/App.test.tsx    # expect empty
```

### Two negative checks — cheap, and they prove the guards are live

DEC-1's exemption is doing real work rather than being an inert allowlist:

```sh
printf '.x { font-family: ui-monospace, Menlo, monospace; }\n' > app/src/__probe.css
uv run python controls/fitness/design_adherence.py ; echo "EXIT=$?"
# expect FAIL [DEC-1] app/src/__probe.css:1 'Menlo'  and  EXIT=1
rm -f app/src/__probe.css                   # then confirm `git status` is clean
```

The view switch fails **closed** — an unrecognised hash falls back to the caller's
default rather than guessing a screen:

```sh
node -e "console.log(require('fs').readFileSync('app/src/lib/view.ts','utf8'))" | grep -A3 "export function viewFromHash"
# expect exact-match only: '#wall' and '#decisions', everything else null
```

### On the host — human-only gates

```sh
git pull && npm run tauri dev
```

- **The window opens on the wall**, not the decisions table. Expect a 52px empty column
  down the left with a hairline on its right edge, and a header bar reading "The wall" in
  Cormorant Garamond, a monospace status line (`dev · static`), and dim right-aligned hint
  text. The hint lies until T8 — that is intended.
- **Four empty boxes**: one narrow at 268px down the left, three to its right stacked
  one-over-two. **A frame with nothing in it is the correct T1 result.**
- Separated by **hairlines, not gaps**. White or grey channels between panes mean a pane
  background or the grid background is wrong. Panes draw no borders of their own; the 1px
  grid gutters show `--color-divider` through from behind.
- Warm off-white ground throughout. No purple, no pure white.
- **Resize narrow and tall.** The grid holds its proportions and panes do not spill.
  Content overflow is not yet testable — there is no content.

**The old screen is still reachable and unchanged.** In devtools, set
`location.hash = '#decisions'`. Expect the M2 decisions table exactly as it was at M2
close: green otter, Cormorant heading, Lora table, status pills. Then set
`location.hash = '#wall'` to go back.

**The fail-closed check, by hand.** From the decisions screen, run `location.hash = ''`
in the console. Expect it to land on **the wall** — the app's real default — not the
decisions screen. This is the T2/T8 regression the round was spent on; a rail click or an
Esc handler that clears the hash must not strand the user on the wrong screen.

**Not wired yet, by design:** the rail has no icons (T2), the panes have no content
(T3–T6), and clicking a pane does nothing (T8). No Tauri command was added; the header
status is a static string until M1/M5.
