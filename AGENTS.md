# not-like-the-otters — agent contract

A Tauri desktop app that shows the state of its own development process: the decisions
that govern this repo, the findings the review loop produces, and which of those
findings are close to becoming rules. The app is deliberately the smaller half of the
project — it exists so the agentic build loop around it has something real to build, and
so that loop's output has somewhere to be read. When the app and the loop compete for
effort, the loop wins.

This repo runs a ledger governance harness: architectural rules live as decisions,
each decision is backed by an executable control, and CI fails on drift. Read
`docs/governance-harness.md` once for why.

## Read this first

**Binding rules live in `governance/views/RULES.md`.** It is generated. Read it before
writing code. Every rule in it is enforced by CI; violating one fails the build.

**Never read `governance/decisions/` for rules.** It retains superseded records on
purpose. A superseded rule in your context steers you toward the exact pattern this
project abandoned. History is for humans; the view is for you.

> The generated view is `RULES.md`, not `AGENTS.md`, so it can never be confused with
> this file. This file is the contract — how to behave. That file is the rules — what
> is true. See DEC-0.

**This file is hand-written, and it never restates an enforced rule.** The narrow hazard
is copying a `DEC-N` rule here, where the copy drifts from its control and quietly
becomes a lie. The `Always` / `Never` lists below are the *shape* of the design, for
orientation. The enforced wording lives in the view, and the view wins on any
disagreement.

## The contract

- **Never edit code to evade a control.** If a rule blocks you and you think it is
  wrong, supersede it: author `DEC-N+1`, set the old decision to `status: superseded`
  with `superseded_by: DEC-N+1`, update the control and its pragma, run `make views`,
  commit it together. A human reviews that diff. Changing a rule is a visible act, never
  a silent code tweak.
- **New rules ship with controls.** A governing rule arrives with an executable control
  and its `governance: enforces DEC-N` pragma in the same change, or is explicitly
  marked `enforcement: warn` with a justification.
- **One behavior, one decision.** State a rule in exactly one decision and reference its
  ID elsewhere. Never restate a rule in two places.
- **Do not author rules speculatively.** When asked to add a rule, apply the triage in
  the `finding-triage` skill first. Most dislikes are already lintable or are pure
  taste; only the articulable, recurring middle earns a control. A refusal to write a
  brittle rule is worth more than coverage.

## How work gets done here

**Use the `build-loop` skill.** It is how a scoped work item gets built: you
orchestrate, subagents write and review, and the findings feed the ledger instead of
evaporating.

```
ORCHESTRATOR (you)
  │   ┌───────────────────────────── the loop ─────────────────────────────┐
  ├──▶│ builder             writes code, ends on `make check` = 0           │
  ├──▶│ boundary-reviewer   live rules + this project's architectural seams │
  ├──▶│ reviewer            correctness, tests, maintainability             │
  └──◀│ findings → builder → re-review → APPROVE and score ≥ 4/5           │
      └─────────────────────────────────────────────────────────────────────┘
  │
  ▼  ═══ loop closed. The rest is what makes this a ledger repo. ═══
  ├─ triage every finding → Bin 1 (lintable) / Bin 2 (systemic) / Bin 3 (taste)
  ├─ log sightings in docs/ledger-findings.md
  ├─ a Bin 2 finding on its third sighting → control-author
  └─ make check, commit, Manual QA write-back
```

**The triage step is the point, and it is the one people skip.** A loop that fixes
findings and forgets them is exactly the problem the harness exists to solve: the
correction evaporates, the next session repeats it, and you review it again forever.
Skipping triage means running the experiment while discarding the data.

### The pieces

| | What it is for |
|---|---|
| `build-loop` (skill) | The whole loop. Start here for any scoped work item. |
| `builder` (agent) | Writes code. Reads `RULES.md` first, never evades a control. |
| `boundary-reviewer` (agent) | Live rules and this project's architectural seams. Reports; never edits. |
| `reviewer` (agent) | Correctness, tests, maintainability. Owns `review.md` / `review.json`. |
| `finding-triage` (skill) | Sort one dislike into a bin. Apply the rule of three. |
| `control-author` (agent) | Turn a thrice-sighted Bin 2 finding into a decision plus control. |
| `ledger-ops` (skill) | Harness mechanics: author, supersede, add a control, debug a red gate. |

### When not to use the loop

A one-line fix, a doc edit, or a question. The loop costs several subagent round-trips;
spending them on a typo is theatre. Run `make check` and commit. **But still triage
anything you disliked along the way** — sightings accumulate regardless of how the
change was made.

### Things that will bite you

- **`make check` fails fast.** A red gate reports only the *earliest* failing stage, not
  every failure. Re-run the whole gate after a fix rather than assuming one error was
  the only one.
- **Touched a decision? Run `make views`.** The view and `registry.json` are generated
  from `governance/decisions/`. A stale one fails the *next* task's gate for reasons
  that look unrelated to it.
- **Blocked by a rule is a valid, wanted outcome.** Say so and stop. Do not raise a
  threshold, delete a pragma, or reach for `# noqa`. Reporting it is the most useful
  thing you can do; working around it quietly corrupts the experiment and nobody finds
  out for weeks.

### Environment traps, each one already paid for

- **The Tauri CLI is `tauri`, not `cargo tauri`.** It is installed from npm, which ships
  the binary under that name; `cargo tauri` needs a differently-named binary that only
  the Rust crate provides, and a symlink shim does not work because cargo prepends the
  subcommand name. Once `package.json` exists, `npm run tauri` is the command that works
  both in the container and on a machine with a display.
- **Use `sh -c` in the container, never `sh -lc`.** The login profile resets `PATH` and
  hides rust, node and the user-local binaries, which reads exactly like a broken image.
- **devcontainer features do not exist under `docker compose up`.** They are applied only
  by the devcontainer CLI. Anything that must work in both places — `git`, `gh` — is
  installed in `dev.Dockerfile` on purpose. Do not "simplify" it back to a feature.
- **The repo is `/app` here and `/home/ryan/code/not-like-the-otters` on the host.** Git
  worktrees record absolute paths in both directions, so a worktree created on one side
  is broken on the other. This matters at M5: `no-mistakes` creates disposable worktrees,
  so it must run consistently on one side of that boundary.
- **`make init` runs on the host, not in here.** It is guarded and will refuse.
- **`tauri.conf.json` uses two different base directories, and mixing them up is silent.**
  Path-valued keys (`frontendDist`, `devUrl`) resolve relative to the config file's own
  directory, so `../app/dist` is correct. Hook command strings (`beforeDevCommand`,
  `beforeBuildCommand`) run with cwd at the **project root**, so they take `--prefix app`
  with no `../`. Measured, not read from docs. `tauri info` echoes back the first kind and
  tells you nothing about the second — verify hooks by running
  `npm run tauri -- build --no-bundle` and nothing else.
- **A real `tauri build` rewrites `src-tauri/Cargo.toml`.** It adds `features = []` to the
  `tauri` and `tauri-build` dependency lines every run. Ordinary CLI normalisation, not
  drift and not something an agent did. It will show up as an unstaged diff; `git checkout
  -- src-tauri/Cargo.toml` clears it. Any gate that runs a real build has to decide what
  to do about this rather than leaving the tree dirty.

## Architectural shape

Two halves that never import each other, and one seam inside the app.

```
  ┌─ the harness (Python) ───────────┐        ┌─ the app (Rust + TypeScript) ──────┐
  │                                  │        │                                    │
  │  governance/  controls/  tests/  │ ─────▶ │   webview (TS)                     │
  │  src/not_like_the_otters/        │governs │        │                           │
  │                                  │        │        │ Tauri IPC commands ◀── the│
  │  emits: RULES.md, registry.json  │        │        ▼   only way across         │
  │         proposed rules, stubs    │        │   core (Rust)                      │
  └──────────────────────────────────┘        │        │                           │
                    ▲                         └────────┼───────────────────────────┘
                    │                                  │
                    └──────── on-disk state ◀──────────┘
                     governance/, docs/ledger-findings.md,
                     .codegraph/codegraph.db, `no-mistakes axi status`
```

**The harness governs the app; the app never governs the harness.** Python reads and
checks the Rust and TypeScript trees. Nothing under `governance/`, `controls/`, or
`src/not_like_the_otters/` may import from, or be built by, the app. The point is that a
refactor inside the app cannot break the thing that polices it. This is the seam most
worth protecting and the first one a well-meaning change will erode.

**The webview reaches the machine only through Tauri IPC commands.** No file reads, no
database handles, no shell, no network on the TypeScript side. That surface is a small,
listable set of typed commands, which is also what makes it the natural place to hang
contracts and generated tests later.

**The app reads on-disk state; it does not own it.** Decisions, findings, the code graph
and gate status all belong to tools that write them. The app watches those paths and
renders them. Anything that mutates governance state goes through the harness CLIs, not
through the UI, until there is a decision saying otherwise.

## Always

- Keep the dependency direction one way: harness → app, frontend → IPC → core, app →
  on-disk state as a reader.
- Put every crossing between the webview and the machine behind a named Tauri command.
- Treat generated artifacts as build output: change the source and regenerate.
- Prefer a query to the code graph over crawling files. Fewer tokens is a project goal,
  not an optimisation.

## Never

- Never hand-edit a generated file (`governance/views/**`, `governance/registry.json`).
- Never edit a control to make a failing change pass.
- Never let app logic drift into the Python package, or harness logic into the Rust
  crate. If a job seems to need both, say so and stop.
- Never add a long-lived process. Everything the app needs is on disk or already served
  by a tool that has its own daemon.

## Working context (keep this current)

**Why this exists.** The author is testing an agentic development loop — this harness,
the build/review subagents, spec-first tests, and an external push gate — by running it
on a real project. The app's subject matter was chosen to be low-stakes on purpose. If
you find yourself deep in product design, you have drifted.

**Audience.** One developer, on one machine. No users, no distribution, no
multi-tenancy. Do not build for scale that does not exist.

**Stack.** Tauri (Rust core, TypeScript webview) for the app. Python for the harness —
`uv`, `ruff`, `ty`, `pytest`. Three toolchains in one repo is a known cost, accepted
because the harness must not share a compiler with the code it polices; the harness is
small and self-contained enough to port later if the cost outgrows the benefit.

**Prior art in use.**
- `codegraph` (https://github.com/colbymchenry/codegraph) — tree-sitter index in local
  SQLite, exposed to agents over MCP. Installed for token and tool-call savings.
- `no-mistakes` (https://github.com/kunchenguid/no-mistakes) — a local git proxy that
  runs `intent → rebase → review → test → document → lint → push → pr → ci` in a
  disposable worktree before forwarding to the real remote. Planned as the outer gate.

**Decided on 2026-08-13, with the reasoning, so it is not relitigated:**
- Python stays as the governance language, because the harness must not be breakable by
  the app it governs, and every job left in it is text munging.
- `codegraph` is installed for agent token savings. That justification stands alone and
  does not depend on any visualisation work. It is indexed and served over MCP; query it
  before crawling files. Whether it actually earns its keep is still unmeasured — judge
  that on M1 and say so either way.
- The container no longer mounts the parent of every sibling project. That mount existed
  to hold git worktrees and to work around broken ssh; ssh works in the container now,
  and worktree paths cannot resolve on both sides of the `/app` boundary anyway. When
  worktrees are genuinely wanted, mount one dedicated directory at the *same absolute
  path* inside and out — not the parent of a hundred repositories, which handed every
  agent in here write access to unrelated work.
- No bespoke daemon. Every piece of state the app needs is already on disk or served by
  a tool with its own daemon. The rule to revisit: build one only when there is state
  that is not on disk.
- The local reviewer stays even once the gate exists. A gate round-trip costs a full
  pipeline; a subagent read costs one call. Cheap filter first, expensive judge second.
- When the gate lands, `boundary-reviewer` becomes the command its `review` step runs, so
  there is one reviewer with one rule set rather than two with opinions.
- Gate findings must be filed as sightings in `docs/ledger-findings.md`. Silent auto-fix
  would starve the rule of three of its evidence.

**Rejected, and why:**
- Full yaml-to-test generation for everything — it becomes a compiler you maintain
  instead of use. The plan is two tiers: full generation only for serializable
  input/output cases, and stub generation elsewhere, where the generator emits a named
  failing test and a human writes the body. Anything that fits neither is hand-written
  in `tests/written/` with no ceremony.
- Moving the review loop wholesale into the gate — it trades cheap iterations for one
  expensive verdict.
- Rendering C4 diagrams early. The levels that matter (containers, components) cannot be
  parsed out of source anyway; they are claims a decision has to make first. Worth doing
  once boundaries are declared and enforced, not before.

**Out of scope:** packaging, signing, distribution, auto-update, any second user,
diagram rendering.

**Known risks.** Five interesting sub-projects (app, spec compiler, gate, graph,
diagrams) and one developer; scope creep is the likeliest failure. A project whose
subject is its own process invites mushy requirements — keep milestones small enough to
finish. Three toolchains make CI and the devcontainer heavier than they look.

**Planned work lives in `docs/milestones/`, one file each — not in this file.** A roadmap
here would be spec wearing the costume of context, and it goes stale the first time a
plan changes. This file describes how the project behaves; that directory describes what
is next.

**Current work: M0.** The environment is built and verified; the app itself does not
exist yet. Read `docs/milestones/M0-environment-and-shell.md` before starting.

**Open, small:** `main` is still at the scaffold commit and has no upstream; only `dev`
is pushed. Whether M0 lands on `main` through a PR shapes whether the outer gate has a
target later.

## Commands

```bash
make check       # the single gate: controls → views --check → governance → tests
make views       # regenerate governance/views/RULES.md + registry.json
make governance  # integrity + drift check (the linchpin)
make controls    # every controls/fitness/*.py, plus ruff and ty
make test        # pytest
```

`make check` is the only gate. Run it before you say a change is done.

---

Rules come from `governance/views/RULES.md`. Change a rule by supersession, never by
edit.
