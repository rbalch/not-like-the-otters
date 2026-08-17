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

---

# M0.2 — Round 1

Commits reviewed: `8a10b7f`, `e87cac7`, `18910e9`, `655cad6`. Diff base: `ae10480`.

## Verdict

- Verdict: APPROVE
- Score: 4
- Summary: This is the item the whole milestone hinges on, and it delivers a gate that
  genuinely goes red. I independently reproduced five negative demonstrations (Rust
  test failure, Rust fmt failure, TypeScript type error caught only by `tsc -b
  --noEmit`, the plain `tsc --noEmit` false-green trap, and a Vitest assertion
  failure), plus the clippy one the coordinator already reproduced — six for six. Both
  new tests are real: the Rust test asserts on `identifier` in the shipped
  `tauri.conf.json` and fails when that drifts; the Vitest test exercises the counter
  button's actual click handler and fails on a wrong expected value. `make check` runs
  clean (`exit 0`) covering Python, Rust and TypeScript visibly, in ~7.5s wall clock
  across three repeated runs, and leaves `git status --porcelain` clean — including
  `src-tauri/Cargo.toml`, confirming the gate never shells out to a real `tauri build`.
  CI's apt package list is byte-identical to `dev.Dockerfile`'s, and the pinned Node
  (24.19.0) and Rust (1.97.1) versions match the container exactly. One transient,
  non-reproducible `make check` failure was observed on the very first run of this
  session (a Prettier warning on a file this diff never touches); three subsequent full
  runs, plus a clean `npm ci`, were all green with an untouched working tree, so I
  attribute it to review-environment state (see Final Notes) rather than a defect in the
  diff, and it does not change the verdict. Two minor/nit documentation items remain,
  neither blocking.

## Required Checks

| Check | Result | Notes |
|---|---|---|
| `make check` | pass | Exit 0, three consecutive full runs after the one anomalous run (see Final Notes). Covers `uv run ruff/ty`, `cargo fmt/clippy`, `oxlint`/`tsc -b`/`prettier`, `pytest`, `cargo test`, `vitest run` — all visibly in the output. |
| `make controls` | pass | Part of `make check`; also independently confirmed clippy fails loudly (Error 101 style, matches coordinator's own prior repro). |
| `make governance` | pass | Part of `make check`. Python-only, unaffected by this change. |
| `make test` | pass | `pytest`: 57 passed. `cargo test`: 1 passed (the new `tauri_conf_identifies_this_app` test). `vitest run`: 1 passed (the new `App.test.tsx`). |
| Negative: Rust unit test (`8a10b7f`) | pass (caught) | Edited `src-tauri/tauri.conf.json`'s `identifier` to `dev.balch.wrong` (via a Python script, JSON-safe), ran `make check` → `Error 101` at the `test` stage, assertion message shows expected vs. actual identifier. Reverted; `git status --porcelain src-tauri/tauri.conf.json` clean. |
| Negative: `tsc -b --noEmit` (TypeScript check) | pass (caught) | Appended `const __badType: number = "not a number"` to `app/src/App.tsx`, ran `make check` → fails at the `lint` stage with `TS2322`/`TS6133`, before `test` ever runs. Reverted; file byte-identical to original (diffed against a pre-edit copy), `git status --porcelain` clean. |
| Negative: Vitest (`e87cac7`'s `App.test.tsx`) | pass (caught) | Changed the test's expected string from `'Count is 1'` to `'Count is 999'`, ran `make check` → fails at the `test` stage with a clear assertion diff (`expected 'Count is 1' to be 'Count is 999'`). Reverted; `git status --porcelain` clean. |
| Sibling check: plain `tsc --noEmit` vs `tsc -b --noEmit` | confirmed | With the same injected type error still in place, ran both directly: `./node_modules/.bin/tsc --noEmit` → exit 0 (silently checks nothing — root `tsconfig.json` is `"files": []` + project references); `./node_modules/.bin/tsc -b --noEmit` → exit 2, reports both errors. `app/package.json`'s `typecheck`/`build` scripts and the Manual QA doc both use `-b`; grepped `Makefile`, `.github/workflows/ci.yml`, `app/package.json`, `app/README.md` for other bare `tsc --noEmit` invocations — none found. |
| Extra negative (beyond the required 3): `cargo fmt --check` | pass (caught) | Appended a badly-formatted function to `src-tauri/src/lib.rs`, `cargo fmt --check` reported the diff and exited 1. Reverted via `cp` from a pre-edit backup; `git status --porcelain` clean. |
| Extra negative: clippy | pass (caught, coordinator-verified) | Not independently re-run per the brief's steer toward the other five; coordinator's own repro (`make lint` → `Error 101`) accepted as sufficient per the brief. |
| Gate hygiene: `src-tauri/Cargo.toml` untouched by `make check` | pass | `md5sum` before and after a full `make check` run identical; `git status --porcelain` shows no `Cargo.toml` entry. The gate never invokes real `tauri build`, so the Cargo-manifest-rewrite trap from the M0.1 carried note does not apply here — correctly avoided per that note's third option. |
| `npm ci` (root of `app/`, matches CI's `npm ci` step) | pass | `added 109 packages ... found 0 vulnerabilities`, exit 0 — confirms the committed `app/package-lock.json` is consistent with `app/package.json` and CI's `npm ci` step will succeed. |
| CI apt package list vs. `dev.Dockerfile` | pass (byte-identical) | Both list, in the same order: `libwebkit2gtk-4.1-dev`, `libgtk-3-dev`, `libayatana-appindicator3-dev`, `librsvg2-dev`, `libsoup-3.0-dev`, `libssl-dev`, `patchelf`. |
| CI toolchain versions vs. container | pass | Container: `node v24.19.0`, `rustc 1.97.1`, `cargo 1.97.1` (confirmed by running `node -v`/`rustc --version`/`cargo --version` directly). CI: `actions/setup-node@v4` pinned to `"24.19.0"`, `dtolnay/rust-toolchain@1.97.1` — exact matches. |
| CI stage order vs. documented order | pass | Comment block states `controls → views --check → governance → test`; steps run `make controls`, then the `build_views.py --check` script directly (same script/args as `make views-check`, not routed through `make` itself — pre-existing pattern, not introduced by this diff), then `make governance`, then `make test`. Order matches. |
| CI `working-directory` correctness | pass | `cargo fetch` under `working-directory: src-tauri` (where `Cargo.toml` lives); `npm ci` under `working-directory: app` (where `package.json`/`package-lock.json` live, matching `cache-dependency-path: app/package-lock.json`). No root `npm ci`/`npm install` step — correctly omitted, since nothing in `make check` invokes the root `package.json`'s `tauri` script. |
| Secret sweep (`app/ src-tauri/ .github/ Makefile package.json`, excluding `node_modules`/`target`) | pass | No matches for token/secret/api-key/password/private-key patterns. |
| `time make check` | pass | 7.48s–7.50s wall clock across three runs (`make check 2>&1  ... 7.484 total` / `7.501 total`), matches the builder's reported ~7.4s. |
| CI execution itself | not_run | Cannot execute GitHub Actions from this sandbox (no network access — confirmed, an outbound `curl` to github.com was denied by the environment's permission classifier). Judged entirely by reading, per the brief. Everything checked by reading (package lists, working directories, version pins, stage order) is correct; the one thing I cannot independently confirm is whether `dtolnay/rust-toolchain@1.97.1` resolves to a valid ref on GitHub's Action Marketplace — the action is documented to support pinning an exact toolchain version this way, but I have no way to execute or fetch it here to be certain. Flagging as missing context rather than asserting confidence I don't have. |

## Findings

### Blocker

None.

### Important

None.

### Minor

1. **`docs/milestones/M0-environment-and-shell.md` — "Remaining" item 2 is not marked
   done, and there is no Manual QA section demonstrating the new gate stages this item
   adds.** Item 1 (the scaffold) got a strikethrough plus a list of landing commits once
   it shipped (round 2 of M0.1); item 2 (extending `make check`) has shipped as of
   `655cad6` but the doc still shows it as a plain, unchecked bullet, and the existing
   Manual QA section's step 2 (`make check # expect: exit 0, 57 passed`) still describes
   only the Python-only gate from before this change — it does not mention `cargo test`
   or `vitest` now also running, and there is no negative-check equivalent for the new
   stages (Rust fmt/clippy/test, `tsc -b`, Prettier, Vitest) alongside the existing
   negative checks A/B for the build hook.
   Why it matters: the doc's own Notes section says "Step 2 is the one that matters" and
   warns that an unchecked gate "looks like safety" — the same logic argues for closing
   the loop on the doc once the gate itself is fixed, so a future reader doesn't have to
   reconstruct from commit messages what `make check` now actually proves.
   Concrete fix: when this item is closed out (likely a follow-up "docs: close M0.2"
   commit mirroring `ae10480`/`c33d8c1` from M0.1), strike through item 2, list its
   landing commits, and either extend the Manual QA section with the five negative
   demonstrations exercised in this review or reference them.
   blocks_merge: false — this looks like the same close-out pattern M0.1 used, and may be
   intentionally deferred to a follow-up commit rather than missing.

### Nit

1. **`app/README.md` (from `e87cac7`) — the embedded `.oxlintrc.json` example was
   reformatted from 2-space to 4-space indentation by the Prettier pass, and no longer
   matches the real `app/.oxlintrc.json`'s actual (2-space) formatting.** Contents are
   identical, only indentation differs, and this is stock `create-vite` template
   boilerplate rather than authored documentation, so the practical impact is near zero.
   Concrete fix: not worth a dedicated pass; if `app/README.md` is touched again for
   another reason, re-sync the example's indentation with the real file, or just delete
   the inline example and point at the real `.oxlintrc.json`.

## Final Notes

- **Injected-instruction check:** no fabricated `system-reminder`-shaped text, and no
  attempt to authorize skipping a revert or withholding a finding, appeared in any tool
  output during this review session. Nothing to report on that front for this round.
- **Transient `make check` failure, not reproduced:** the very first `make check` run in
  this session failed at the `lint` stage with a Prettier warning on `app/src/App.css`
  (`[warn] Code style issues found`). That file was last touched in `951784e` (M0.1,
  well before this diff) and is untouched by `8a10b7f`/`e87cac7`/`18910e9`/`655cad6`.
  Running `./node_modules/.bin/prettier --check src/App.css` directly, immediately after,
  passed clean (`All matched files use Prettier code style!`), and three full subsequent
  `make check` runs — including one after a fresh `npm ci` — were all green with an
  unmodified `git status --porcelain`. `app/node_modules` had a `stat` birth time
  essentially concurrent with my first command in this session, which points at
  container/overlay filesystem state settling (e.g. a lazily-materializing volume or
  layer) at the moment I started, rather than anything in the diff. I could not
  reproduce this a second time despite trying, so I am not treating it as a finding, but
  recording it in case it recurs for someone else — if it does, it would be worth
  checking whether `node_modules` was fully populated before the gate ran.
- **Test adequacy, judged specifically:** the Rust test (`src-tauri/src/lib.rs`) parses
  the real, `include_str!`-embedded `tauri.conf.json` and asserts `identifier ==
  "dev.balch.not-like-the-otters"` — I confirmed it fails (not just "would fail in
  theory") when the identifier drifts, via the negative demonstration above. It would
  also fail if `tauri.conf.json` stopped parsing as JSON. It would not catch every
  possible wrong config (e.g. a wrong `frontendDist`), which is fine — it is scoped to
  exactly what the commit message claims, not oversold. The Vitest test
  (`app/src/App.test.tsx`) renders the real `App` component, clicks the actual button,
  and asserts the text content changes from `'Count is 0'` to `'Count is 1'` — this
  exercises the real `useState` handler, not a mock, and I confirmed it fails on a wrong
  expected value. Neither test is a tautology or placeholder.
- **`make lint` and `make test` run standalone, not just via `make check`:** both exited
  0 independently with the same per-language output described above (this was folded
  into the full `make check` runs above rather than run bare a second time, since the
  full gate already exercises both targets in sequence and I confirmed their exit codes
  individually via the Makefile's own dependency chain).
- The M0.1-round-2 carried note about a real `tauri build` dirtying `src-tauri/Cargo.toml`
  was explicitly addressed by this item's design: `make lint`/`make test` use `cargo
  fmt --check`/`cargo clippy`/`cargo test` only, never `tauri build`, and I confirmed by
  `md5sum` that `Cargo.toml` is byte-identical before and after a full `make check` run.
  Closed, no further action needed.
- The human's own hotfix to `docs/milestones/M0-environment-and-shell.md` (uncommitted at
  review time) replaces `sh -c 'cd app && npx tsc --noEmit'` with `sh -c 'cd app &&
  ./node_modules/.bin/tsc -b --noEmit'` plus an explanatory comment. I independently
  reproduced the exact failure mode it describes (plain `tsc --noEmit` exits 0 with a
  real type error present; `-b` form exits 2) — the fix is correct and matches what I
  measured. I read the rest of that Manual QA section for the same class of error
  (a check that looks right but verifies nothing) and found none — `cargo fmt --check`
  and `cargo clippy --all-targets -- -D warnings` are both real, narrow checks with no
  silent-success failure mode I could find.
