---
id: DEC-1
title: App source does not hardcode a design value Classical defines a token for
status: accepted
kind: negative
created: 2026-08-18
superseded_by: null
controls:
  - path: controls/fitness/design_adherence.py
    type: fitness_fn
    enforcement: block
    pragma: supported
---

## Rule

No file under `app/src/` may contain a raw hex colour literal, or a `font-family`
naming a family outside Cormorant Garamond and Lora. The vendored token file
`app/src/classical.css` and the local token file `app/src/tokens-local.css` are
exempt — they are where those literals are supposed to live.

## Context

Classical is ingested as tokens plus a cascade. The value of that is only realised if
app code refers to the tokens rather than restating their values. A hardcoded
`#b3261e` does not fail anything, renders fine, and quietly means the design system no
longer describes the app — the drift is invisible until someone retunes a token and
half the UI ignores it.

This is design drift becoming a gate failure by the same mechanism as governance
drift, which is the thesis of the project pointed at a new target.

**Enforcement lives here rather than in the linter, and that was not the plan.**
Classical ships `_adherence.oxlintrc.json` for exactly this job. It cannot be used:
all three of its real rules are `no-restricted-syntax`, which **oxlint 1.78 does not
implement** — the config fails to parse rather than under-enforcing. The other two
rules ship with empty `forbid: []` / `patterns: []` and are no-ops by construction.
Promoting everything from `warn` to `error`, which the milestone anticipated as the
fix, would have changed nothing. See ledger finding F-9. The config is kept as a
vendored reference artifact and is not wired into the gate.

**This is a seeded rule, not a discovered one** — the second, after DEC-0. It has one
sighting, not three. It is promoted on sight because M2's acceptance criterion is
literally *"a raw hex value in a `.tsx` turns `make check` red"*, and a milestone that
ships the appearance of adherence enforcement without the substance is the specific
failure M2 exists to avoid. Recorded as an exception rather than pretending the rule
of three was followed. (Human note, worth recording in the decision: the rule of three
is a rule of thumb rather than a hard gate — a known-good rule may be seeded on sight,
provided the seeding is stated plainly rather than disguised as a discovered pattern.)

**Raw `px` is deliberately not enforced, and this is the most important line in this
decision.** The third adherence rule bans raw `px` values. Applied to CSS it fires on
correct code immediately — Classical's own `styles.css` is full of raw px (`h1 {
font-size: 42px }`), as is any real stylesheet. A control that fires on correct code
is the most damaging failure available here, because it teaches everyone to route
around the harness. The rule is recorded as **understood and declined**, not
overlooked.

## Consequences

`controls/fitness/design_adherence.py` scans `app/src/**/*.{ts,tsx,css}`, skipping the
two token files, and goes **red** on any raw hex colour or non-Classical
`font-family`. It goes **green** on a tree that expresses every design value through
`var(--token)`.

`app/src/App.css:22` violated this rule with a raw `#b3261e` for the error state.
Classical defines no error or danger token. This is the first place the design system
does not cover what the app needs, and it is a genuine tier-3 fork point rather than
an oversight — so it is resolved by *extending* the system locally, not by exempting
the file.

A second token file is introduced: `app/src/tokens-local.css`, holding tokens the app
needs that Classical does not define, starting with `--color-danger`. It is separate
from `classical.css` because that file must stay byte-identical to upstream for tier-1
re-sync to diff cleanly. The split is the boundary between what re-syncs and what
forks, made physical: **anything in `classical.css` is upstream's and will be
overwritten; anything in `tokens-local.css` is ours and never will be.**

## Rejected alternatives

- **Scope the control to `.tsx` only.** Tempting, and it satisfies M2's wording
  exactly. Rejected: nearly all styling in this app is in `.css`, so a `.tsx`-only
  rule would go green on a codebase whose stylesheets had drifted entirely off the
  token set. That is enforcement theatre — it passes the acceptance criterion while
  policing the files least likely to contain the defect. *Positive recast:* scope to
  where the values actually live, and exempt the token files by name.
- **Exempt `App.css` so the control goes green immediately.** Rejected. The one real
  violation in the tree is the only evidence the control works on real code, and
  exempting it to get a green build is the pattern this repo exists to prevent.
- **Also ban raw `px`.** Rejected as specified above — it fires on correct code,
  including the design system's own source.
- **Wait for three sightings.** Rejected, explicitly. The rule of three is
  load-bearing and this decision is the second seeded exception to it. The defence is
  that this rule is not inferred from a dislike of agent output — it is an acceptance
  criterion of the milestone, written down before any code was reviewed. If seeded
  exceptions keep appearing, that is itself worth recording as evidence about the
  harness.
