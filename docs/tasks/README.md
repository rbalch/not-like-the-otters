# Tasks — the console wall

Work items porting `docs/design_handoff_console_wall/` into `app/`. Each file is one
`/build-loop` work item: scope, non-scope, acceptance criteria as runnable commands, and
an empty Manual QA section the loop writes back into on close.

**One at a time, in order.** T1 establishes the primitives every later item builds on;
T2–T6 are the four panes plus the rail; T7 and T8 are state and interaction.

| item | what | depends on |
|---|---|---|
| [T1](T1-shell-and-mono-token.md) | `--font-mono`, view switch, `WallLayout`, `Pane`, `Kicker` | — |
| [T2](T2-icon-rail.md) | icon rail, Lucide icons, active/inactive states | T1 |
| [T3](T3-gate-pane.md) | gate column — otter, status word, stage list, rules stat | T1 |
| [T4](T4-run-pane.md) | run band — pipeline breadcrumb, monospace log block | T1 |
| [T5](T5-promotion-pane.md) | promotion list — sighting bars, bin footer | T1 |
| [T6](T6-milestone-pane.md) | milestone pane — title, body, checklist, next | T1 |
| [T7](T7-gate-red-state.md) | the `#4b` red variant, driven by state not a second screen | T3, T4 |
| [T8](T8-pane-peek.md) | click a pane to peek, Esc closes | T2–T6 |

## The one thing to read first

**The wall is not the decisions window re-skinned.** `app/src/App.tsx` today is M2's
single screen: otter brand mark plus `DecisionTable`. The wall is the screen M1 and M5
need — gate status, the live build-loop run, promotion candidates, current milestone.
Of those four, **only decisions has a backend**: `list_decisions` is the sole
`#[tauri::command]` in `src-tauri/src/lib.rs`. Gate status, run logs, findings and
milestone state have no data source and will not get one here.

So every pane in T3–T6 is built **presentation-first against typed props**, fed by
fixtures in `app/src/lib/wall.ts`. That file is the seam: M1/M5 replace the fixture
providers with real IPC calls and the components do not change. A task that invents a
Tauri command to fill a pane is out of scope and should come back as blocked.

## The four sections in each task, and what each is for

They are not four ways of saying the same thing. Blur them and the loop starts
self-certifying.

| section | who runs it | when | answers |
|---|---|---|---|
| **Acceptance criteria** | the builder and both reviewers, in the container | every round | did the gate stay green, and do the named commands print what they should |
| **Done when** | the orchestrator | at close | is this item finished — one sentence, the bar the work is judged against |
| **What you'll see** | **you, on the NixOS box, after `git pull`** | after close | does it actually look right |
| **Manual QA** | written back by the loop | at close | the replayable record, including anything learned that the up-front sections got wrong |

**"Done when" is not the eye-check.** It is deliberately terse and mostly machine-checkable
— it exists so the orchestrator has an unambiguous stopping condition, not so a human can
verify a screen. That is what "What you'll see" is for, and it is written *before* the work
so it can't be quietly reshaped to match whatever got built. If the built screen and the
written expectation disagree, that is a finding, not a documentation update.

## Pulling and running on the host

Yes — every item ends with a commit and a green gate, so each one is a real pull-and-run
checkpoint:

```sh
git pull origin dev
npm ci --prefix app          # only after T2, if a dependency landed
npm run tauri dev
```

The container has no compositor, so **every visual check is host-only, by construction.**
That is not a gap in the loop; it is the one class of verification the loop structurally
cannot do, which is why each item names it explicitly rather than leaving it implied.

Two caveats on the checkpoints:

- **T1 looks like nothing.** Four empty boxes and a header bar. That is the correct result
  and the task says so — do not read it as an unfinished T1.
- **T7 needs a switch to be visible at all.** The red state is fixture-driven with no data
  source, so T7 must ship a dev-only way to reach it. If it doesn't, there is nothing to
  look at, and that is a finding against T7 rather than something to work around.

The first item that is genuinely worth stopping to look at is **T3** — the gate column is
the first pane with real presence, and the otter at 183px is the first time the wall reads
as the wall.


## Known trap — `Menlo` fails DEC-1, measured

The handoff README declares monospace "a deliberate exception to Classical's two-family
rule" and gives the stack as `ui-monospace, Menlo, monospace`. DEC-1's control does not
know about that exception. Measured on this tree:

```
$ printf '.log { font: 400 11.5px/1.75 ui-monospace, Menlo, monospace; }\n' > app/src/__probe.css
$ uv run python controls/fitness/design_adherence.py
FAIL [DEC-1] app/src/__probe.css:1 'Menlo'
    -> use var(--font-heading) or var(--font-body)
```

`ui-monospace` and `monospace` are both on the control's generic-family allowlist; the
named family `Menlo` is not. **The fix is T1's first scope item** and it is not a
workaround: `--font-mono` is defined in `app/src/tokens-local.css`, which DEC-1 exempts
by name, and every pane references `var(--font-mono)`. Verified green:

```
$ printf ':root { --font-mono: ui-monospace, Menlo, monospace; }\n' >> app/src/tokens-local.css
$ printf '.log { font-family: var(--font-mono); }\n' > app/src/__probe.css
$ uv run python controls/fitness/design_adherence.py
ok [DEC-1] no hardcoded design values under app/src/.
```

That is the tier-1/tier-3 boundary doing its job: Classical does not define a mono
family, the app needs one, so it lives in the local token file where a re-sync will never
overwrite it. **Never edit the control to admit `Menlo`** — that is evading a control.

## Rules that bite on every item

- **DEC-1**: no raw hex, no font family outside Cormorant Garamond / Lora, anywhere under
  `app/src/`. The reference HTML is already token-only — port `var(--token)` names across
  verbatim rather than resolving them.
- The reference's `color-mix(in srgb, var(--color-text) 45%, transparent)` appears a dozen
  times at four or five different percentages. Define those as local tokens
  (`--wall-text-45`, or whatever reads better) in `tokens-local.css` once, rather than
  repeating the expression in every component.
- **The seam holds**: nothing in `app/` touches `governance/` or `src-tauri/` internals.
  The wall is read-only by design — the handoff says so explicitly, and it is right.

## Divergences from the reference, decided up front

- **Inline styles do not come across.** The reference is flat markup with inline `style`
  attributes for iteration speed, and says so. Port to classes in `App.css` (or a
  component-local stylesheet), matching how `DecisionTable.tsx` and `BrandMark.tsx`
  already work.
- **Drop `image-rendering: pixelated`.** The handoff offers it conditionally. M2 measured
  the otters and they are continuous-tone renders that *depict* pixel art — ~47,000 unique
  colours, no block grid at any factor (ledger **F-12**). `pixelated` at 183px would be
  wrong. `BrandMark.tsx` already renders them smooth; the wall matches it.
- **Reuse `otters.ts` and `BrandMark.tsx`.** Do not add a third image variant and do not
  re-import the PNGs directly — `src` and `alt` are carried together in that map on
  purpose (ledger **F-17**).
- **Fixed pixel sizes are reference-frame, not literal.** The 1280×840 frame, 52px rail
  and 268px gate column are real; the 11.5px/12.5px type sizes are Classical's own scale
  and come across as-is.
