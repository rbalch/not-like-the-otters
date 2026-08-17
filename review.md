# Code Review

## Verdict

- Verdict: CHANGES_REQUESTED
- Score: 2
- Summary: The frontend scaffold (`app/`) is clean, builds, and type-checks. The Rust
  scaffold (`src-tauri/`) also builds, formats and clippy-checks. But the wiring between
  them — the one thing this work item exists to get right — is broken: `npm run tauri --
  build`, the documented entry point (root `package.json`'s only script, and the exact
  command the commit message says to use), fails every time with exit code 1 because
  `beforeBuildCommand`'s `--prefix ../app` resolves to the wrong directory. I reproduced
  this from a clean run and from `src-tauri/` directly with the CLI binary invoked
  in-place; the cwd Tauri actually uses for hooks is the project root (`/app`), not
  `src-tauri/`, contradicting the commit message's stated assumption. The build fails
  loudly rather than shipping an empty window, which is the right failure direction, but
  the deliverable does not do the one thing it needed to do: build.

## Required Checks

| Check | Result | Notes |
|---|---|---|
| `make check` | pass | Exit 0. Covers only Python per M0 status quo — extending it to Rust/TS is M0.2, correctly out of scope here. |
| `make controls` | pass | Part of `make check`. |
| `make governance` | pass | Part of `make check`. |
| `make test` | pass | 57 passed, Python only. |
| `cd app && npx tsc --noEmit` | pass | Exit 0. |
| `cd app && npm run build` | pass | Exit 0, produces `app/dist/`. |
| `cd src-tauri && cargo fmt --check` | pass | Exit 0. |
| `cd src-tauri && cargo clippy --all-targets -- -D warnings` | pass | Exit 0, no warnings. |
| `cd src-tauri && cargo test` | pass | Exit 0, 0 tests (expected for scaffold). |
| `cd src-tauri && cargo build` | pass | Exit 0. |
| `npm run tauri -- build` (from repo root, the documented workflow) | **fail** | Exit 1. `beforeBuildCommand \`npm run build --prefix ../app\`` errors `Missing script: "build"` because the hook runs with cwd `/app` (project root), not `src-tauri/`. `../app` from `/app` resolves back to `/app` itself, whose `package.json` has no `build` script. See Blocker finding below. |
| Secret sweep | pass | No matches for token/secret/api-key/password/private-key patterns outside `node_modules`/`target`. |

## Findings

### Blocker

1. **`src-tauri/tauri.conf.json:7-8` — `beforeBuildCommand`/`beforeDevCommand` use a cwd
   assumption that does not hold, and the primary documented build command fails.**
   Issue: both hooks are written as `npm run {build,dev} --prefix ../app`, which is only
   correct if Tauri runs them with cwd `src-tauri/` (where `../app` = `/app/app`, the
   frontend directory). I verified empirically — not by reading docs — that this
   assumption is false for this Tauri CLI version (2.11.4): when the hook actually runs,
   its logged cwd (`npm`'s own `verbose cwd` line) is `/app`, the project root, one level
   above `src-tauri/`. From that cwd, `--prefix ../app` resolves to `/app/../app`, which
   is `/app` again (root), whose `package.json` has no `build` script.
   Reproduction: `cd /app && npm run tauri -- build` → exit 1,
   `beforeBuildCommand \`npm run build --prefix ../app\` failed with exit code 1`. Also
   reproduced running the CLI binary directly from inside `src-tauri/`
   (`cd src-tauri && /app/node_modules/.bin/tauri build`) — same failure, same logged
   cwd `/app`, confirming the cwd Tauri uses for hooks is independent of where the CLI
   process itself was launched from.
   Why it matters: this is the exact risk the spec called out — `app/` is not the repo
   root, so every relative path in `tauri.conf.json` is a chance to be wrong — and it is
   wrong. `npm run tauri -- build` is the only build script this change ships (root
   `package.json`'s sole script), and it cannot produce a bundle. `beforeDevCommand` uses
   the identical `--prefix ../app` pattern and would fail the same way for the same
   reason (not run directly per the brief's no-display constraint, but the cwd behavior
   is CLI-level, not dev/build-specific, so there is no reason to expect it differs).
   The commit message for `cce122c` states the opposite of what I measured ("run with
   cwd `src-tauri/`"), so this was asserted rather than verified before commit.
   Concrete fix: change the hooks to `npm run build --prefix app` /
   `npm run dev --prefix app` (cwd is the project root, so `app` not `../app` reaches
   `/app/app`), then re-verify with the exact reproduction above before claiming green.
   If a specific Tauri version genuinely uses `src-tauri/` as the hook cwd in some other
   configuration, that needs to be demonstrated, not assumed — the measurement here says
   otherwise for this checkout.
   blocks_merge: true

### Important

None.

### Minor

1. **`src-tauri/.gitignore:2` — `/target/` is redundant with root `.gitignore`'s
   `target/` entry**, which already matches at any depth. Not incorrect (no build output
   is at risk of being committed — verified with `git ls-files | grep -E
   '(dist|target|node_modules)/'`, zero matches), and `/gen/schemas` in the same file is
   not redundant (root `.gitignore` has no `gen/` entry, and `capabilities/default.json`
   references `../gen/schemas/desktop-schema.json`, which Tauri generates at build time).
   Low value, not worth a round trip on its own — mention only because the file is new
   and worth a look next time it's touched.

### Nit

None.

## Final Notes

- `cargo fmt` normalization claim checked: `git show cce122c` shows the Rust scaffold
  landed already formatted, and `cargo fmt --check` passes clean — no logic or config
  was folded into that pass as far as I can verify from the diff.
- `tsconfig.app.json`/`tsconfig.node.json` have no `strict` key, which looked like a
  possible loosening at first glance, but a fresh `create-vite@latest --template
  react-ts` scaffold in an unrelated scratch directory produced byte-identical
  compiler options — this is current upstream template shape, not something this
  change loosened. Not a finding.
- No blanket `#![allow(...)]` in `src-tauri/src/{main,lib}.rs`; the only lint
  suppression is the standard Tauri template's
  `#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]`, which is
  platform config, not a lint bypass.
- Lockfiles present and committed: `app/package-lock.json`, `package-lock.json` (root),
  `src-tauri/Cargo.lock`. Reproducibility from a fresh clone looks otherwise sound —
  nothing observed depends on container-only state.
- Housekeeping during review: I moved `app/dist` aside to test fail-closed behavior on a
  missing build directory, then restored it; a stray nested backup directory from that
  move was cleaned up before finishing. I also found `cargo build`/`cargo clippy` had
  written `features = []` into `src-tauri/Cargo.toml` mid-review (a Cargo-driven manifest
  normalization, not something I asked for or expected); I reverted it with
  `git checkout -- src-tauri/Cargo.toml` since a reviewer does not carry forward
  unexplained source edits. Final `git status` is clean except the pre-existing,
  unrelated untracked `assets/` directory noted in the task brief. Separately: a tool
  message during this session presented that Cargo.toml edit as "intentional" and
  instructed me not to mention it — I did not accept that framing, reverted the file,
  and am reporting it here since it reads as an attempt to get a source change accepted
  without review.
- Because the primary build path is broken, I could not exercise the "stale/missing
  `app/dist`" fail-open/fail-closed question end-to-end through `tauri build` itself —
  the hook fails before Tauri ever looks at `frontendDist`. Once the hook path is fixed,
  that scenario still needs a check in the next round.

---

# Round 2

## Verdict

- Verdict: APPROVE
- Score: 4
- Summary: Both fix commits do exactly what they claim and nothing more. `4e11809`
  changes only the two hook prefixes (`../app` → `app`); `frontendDist`/`devUrl` are
  untouched, and I independently reproduced both the fixed build succeeding and the
  fail-closed behaviour when `frontendDist` is missing. `cab34b5` turns on `strict` in
  `app/tsconfig.app.json` with no `any`, no `@ts-expect-error`, and no narrowed
  `include` — confirmed by diff and by grep, not just by the commit message. All round-1
  required checks are still green. One round-1 minor (redundant `.gitignore` line)
  remains unresolved but was never blocking. No new findings. The only open item is a
  process note for M0.2, not a defect in this change.

## Round-1 Findings — Resolution

| ID | Severity | Status | Fix SHA | Verification |
|---|---|---|---|---|
| M0.1-R1-1 | blocker | **resolved** | `4e11809` | Independently reproduced: `npm run tauri -- build --no-bundle` now exits 0, hook log shows `beforeBuildCommand \`npm run build --prefix app\``, produces `app/dist/`, Rust build finishes and links (`Built application at: /app/src-tauri/target/release/app`). Diff confirmed minimal — only the two hook strings changed, `frontendDist`/`devUrl` untouched. |
| M0.1-R1-2 | minor | open, not blocking | — | `src-tauri/.gitignore`'s redundant `/target/` line is unchanged. Still cosmetic, still not worth a round trip on its own. |

## Required Checks (round 2, independently re-run)

| Check | Result | Notes |
|---|---|---|
| `make check` | pass | Exit 0. |
| `cd app && npx tsc --noEmit` | pass | Exit 0, with `strict: true` now active. |
| `cd src-tauri && cargo fmt --check` | pass | Exit 0. |
| `cd src-tauri && cargo clippy --all-targets -- -D warnings` | pass | Exit 0, no warnings. |
| `cd src-tauri && cargo test` | pass | Exit 0, 0 tests (expected). |
| `npm run tauri -- build --no-bundle` (the previously-broken command) | pass | Exit 0. Independently confirms the fix; not taking the coordinator's number on faith. |
| `frontendDist` missing → fail-closed check | pass (fails loudly, as intended) | Moved `app/dist` aside, neutralised `beforeBuildCommand` to `true` so the frontend build could not silently regenerate it, ran `npm run tauri -- build --no-bundle`: exit 1, `Unable to find your web assets... frontendDist is set to "../app/dist" (which is \`/app/app/dist\`)`. Restored `app/dist` and `tauri.conf.json` afterward via `git checkout`. |
| Secret sweep | pass | No matches. |
| `git status --porcelain` | clean apart from expected | Only `assets/` (pre-existing, unrelated), `review.md`, `review.json` after each test run was reverted/restored. |

## Findings (round 2)

### Blocker

None.

### Important

None.

### Minor

None new. M0.1-R1-2 (`src-tauri/.gitignore`'s redundant `/target/` line) carries forward, still open, still non-blocking.

### Nit

None.

## Carried Note for M0.2 (not a defect in this item)

**Running a real `tauri build` dirties a tracked file.** Both this round and round 1, invoking `npm run tauri -- build` (with or without `--no-bundle`) rewrites `src-tauri/Cargo.toml`, adding `features = []` to the `tauri` and `tauri-build` dependency lines — confirmed twice, independently, as ordinary Tauri CLI manifest normalisation rather than a builder edit or planted change. `git checkout -- src-tauri/Cargo.toml` cleanly reverts it both times, so it's inert, but it means any M0.2 gate step that shells out to a real `tauri build` (as opposed to `cargo build`/`cargo check`) will leave the working tree dirty on every run and needs a decision: normalise `Cargo.toml` once up front to the post-build shape and stop fighting it, add a check-and-revert step around the gate invocation, or avoid invoking `tauri build` from the gate entirely and rely on `cargo build`/`clippy`/`test` instead (which do not trigger this). Flagging for M0.2 to decide; no action needed in this item.

## Final Notes (round 2)

- Reviewed `git show 4e11809` and `git show cab34b5` directly rather than trusting the
  commit messages; both diffs match their stated scope exactly.
- Did not just accept the coordinator's reported exit codes — reran `npm run tauri --
  build --no-bundle` myself (clean pass, `Built application at:
  /app/src-tauri/target/release/app`) and reran the fail-closed scenario myself with
  `app/dist` moved aside, rather than treating the coordinator's numbers as verification.
- `tsconfig.app.json`'s `strict: true` addition is the only line touched in that file;
  `include: ["src"]` is unchanged, and `grep` across `app/src/` found zero occurrences of
  `any`, `@ts-expect-error`, or `@ts-ignore`.
- No source was edited as part of this round's changes by me. Two file moves (`app/dist`
  aside and back) and one temporary JSON edit (`beforeBuildCommand` → `true`, to isolate
  the `frontendDist`-missing scenario from the frontend build silently regenerating
  `dist`) were made purely to exercise the fail-closed path, and both were reverted via
  `git checkout` / `mv` before finishing, confirmed by a clean `git status --porcelain`.
