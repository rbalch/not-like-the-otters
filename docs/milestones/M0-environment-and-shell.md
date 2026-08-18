# M0 — Environment and app shell

**Status:** complete. Both human gates closed on 2026-08-18 — CI ran green on its first
execution (200s, PR #1), and `cargo tauri dev` compiles and opens the window on a host
with a display.

## Goal

Prove the harness can govern a polyglot tree, and get a Tauri app on screen that reads
one thing from `governance/`.

## Done

- Dev container: Rust 1.97.1, cargo, `tauri` CLI 2.11.4, Node 24, gh 2.97.0,
  codegraph 1.5.0, webkit2gtk 4.1, uv-managed Python 3.13.
- Credentials in shared `dev-ssh` / `dev-gh` volumes, installed by `make init`.
- `flake.nix` for running the real window on a machine with a display.
- `make check` green — but only over Python.

## Remaining

1. ~~Scaffold the app: React + Vite + TypeScript frontend, `tauri init` for the Rust core.
   Frontend lives in `app/`, Rust in `src-tauri/`; `src/` stays the Python harness.~~
   **Done** — `951784e`, `cce122c`, `4e11809`, `cab34b5`. See Manual QA below.
2. ~~Extend `make check` to cover all three languages. Rust: `cargo fmt --check`,
   `cargo clippy -- -D warnings`, `cargo test`. TypeScript: `tsc --noEmit`, a formatter
   check, `vitest run`. Both fold into the existing `lint` and `test` targets so `check`
   stays the single entry point.~~
   **Done** — `8a10b7f`, `e87cac7`, `18910e9`, `655cad6`. Note the spec said
   `tsc --noEmit`; the gate uses **`tsc -b --noEmit`**, because the plain form checks
   nothing here (see Manual QA below and finding F-5).
3. ~~One window listing decisions read from `governance/`.~~
   **Done** — `6efebbd`, `c7f7091`. Reads the generated `registry.json`, not the decision
   markdown: parsing frontmatter in Rust would reimplement the harness's parser inside the
   app, which `AGENTS.md` forbids.

## Done when

`make check` exits 0 while genuinely checking Python, Rust and TypeScript, and the app
window lists the decisions on disk.

## Manual QA — step 1, the app scaffold

Run from the repo root inside the dev container. Copy-pasteable.

```sh
# 1. The whole build path, end to end. This is THE check — it exercises the
#    frontend build, the hook prefix, and the Rust link against webkit2gtk.
npm run tauri -- build --no-bundle
#    expect: exit 0, ending in
#    "Built application at: /app/src-tauri/target/release/app"

# 2. The Python gate is untouched and still green.
make check                       # expect: exit 0, 57 passed

# 3. Type checking, with strict mode now on.
#    NOTE the -b. Plain `tsc --noEmit` checks NOTHING here: the root tsconfig.json is
#    "files": [] plus project references, so it silently exits 0 with real type errors
#    present. Verified by injecting one. Always -b.
sh -c 'cd app && ./node_modules/.bin/tsc -b --noEmit'   # expect: exit 0, no output

# 4. Rust lint and format.
sh -c 'cd src-tauri && cargo fmt --check'                         # expect: exit 0
sh -c 'cd src-tauri && cargo clippy --all-targets -- -D warnings' # expect: exit 0
```

**After step 1, expect `src-tauri/Cargo.toml` to show as modified.** A real `tauri build`
adds `features = []` to two dependency lines every run. That is CLI behaviour, not drift.
Clear it with `git checkout -- src-tauri/Cargo.toml`.

### Negative checks — both should fail, loudly

```sh
# A. Missing frontend build must not silently ship an empty window.
mv app/dist app/dist.bak
sh -c 'cd src-tauri && cargo tauri build --no-bundle' 2>&1 | tail -2
#    expect: exit 1, "Unable to find your web assets ... frontendDist is set to
#    \"../app/dist\"". If this ever SUCCEEDS, that is a false success — stop and fix it.
mv app/dist.bak app/dist

# B. The hook prefix is the bug this round shipped and then fixed. To see it fail,
#    temporarily change beforeBuildCommand's "--prefix app" to "--prefix ../app":
#    expect: exit 1, 'Missing script: "build"'. Revert afterwards.
```

### What to look at with your own eyes

- `src-tauri/tauri.conf.json` — `frontendDist` is `../app/dist` (relative to the config
  file) while the hooks use `--prefix app` (relative to the project root). Those two
  looking inconsistent is correct; see the trap in `AGENTS.md`.
- `src-tauri/capabilities/default.json` — should still grant only `core:default`. M0.3
  will widen this, and that is the moment the webview/machine seam is either kept or lost.

### Human-only gates, not simulated

- **No window has ever been opened.** This container has no display, so `tauri dev` and
  any real GUI smoke test were never run. `cargo build` linking webkit2gtk is the closest
  available proxy. Running the app on a machine with a display — via `flake.nix` — is
  still outstanding and only a human can do it.

## Manual QA — step 2, the three-language gate

The claim to check is not "the targets exist". It is **the gate goes red when it should**.

```sh
# 1. The gate itself, all three languages under one entry point.
make check          # expect: exit 0, ~7.5s
#    Read the output and confirm you see all of:
#      ruff / ty                    (Python)
#      cargo fmt --check / clippy   (Rust)
#      oxlint / tsc -b / prettier   (TypeScript)
#      pytest 57 passed, cargo test 1 passed, vitest 1 passed

# 2. The gate must not dirty the tree. Run it, then look.
make check && git status --porcelain
#    expect: no modified TRACKED files from the gate. In particular
#    src-tauri/Cargo.toml must be unmodified — see the tauri build trap in AGENTS.md.
```

### Negative checks — the actual point. Each must go RED.

Break one thing at a time, run `make check`, confirm non-zero, then `git checkout --` it.

| Break | Expect |
|---|---|
| Add spaces inside a `fn` signature in `src-tauri/src/lib.rs` | fails at `cargo fmt --check` |
| Add `let x = 42;` (unused) to `src-tauri/src/lib.rs` | fails at `cargo clippy`, exit 101 |
| Flip the assertion in the `src-tauri/src/lib.rs` test | fails at `cargo test` |
| Add `const n: number = "str"` to `app/src/App.tsx` | fails at `npm run typecheck` |
| Mangle whitespace in `app/src/App.tsx` | fails at `npm run format:check` |
| Change the expected value in `app/src/App.test.tsx` | fails at `npm run test` |

```sh
# The most important negative check of all: a missing toolchain must fail LOUDLY,
# never skip to green.
mv app/node_modules app/node_modules.bak
make check          # expect: exit 2, "oxlint: not found", Error 127 — NOT a skip
mv app/node_modules.bak app/node_modules
```

**If any of these exits 0, the gate is lying and that is a stop-everything bug.**

### The trap this step exposed, worth knowing by hand

```sh
cd app
./node_modules/.bin/tsc --noEmit      # exits 0 even with real type errors — checks NOTHING
./node_modules/.bin/tsc -b --noEmit   # the real check
```
The root `tsconfig.json` is `"files": []` plus project references, so the plain form has
no files to look at and reports success. Always `-b`. The M0.1 Manual QA originally
told you to run the plain form; that was wrong and is now fixed.

### Human-only gates, still outstanding

- **CI has never actually run.** `.github/workflows/ci.yml` gained Rust, Node and the
  Tauri apt packages, verified only by reading and by local equivalence — there is no
  runner here. The first real push is the test. Expect it to be slow: three toolchains.
- **No window has ever been opened.** Still no display in this container. Carried from M0.1.

## Manual QA — step 3, the decisions window

```sh
# 1. The gate, now covering the new command and component.
make check     # expect: exit 0 — 57 pytest, 7 cargo, 2 vitest

# 2. It still bundles.
npm run tauri -- build --no-bundle    # expect: exit 0
git checkout -- src-tauri/Cargo.toml  # expected churn, see the trap in AGENTS.md
```

### The property that matters: it must fail loudly, never show an empty list

An empty table is indistinguishable from "there are no decisions". That is a false
success, and it is the specific thing this item was built to avoid.

```sh
mv governance/registry.json /tmp/registry.json.bak
sh -c 'cd src-tauri && cargo test real_registry_path_resolves_and_reads'
#    expect: FAILED, naming the exact path —
#    "could not read /app/src-tauri/../governance/registry.json: No such file or directory"
mv /tmp/registry.json.bak governance/registry.json
```

In the window, that same error renders in a `role="alert"` element. There is no code path
from a rejected `invoke` to a rendered empty list — the load state is a union, and failure
lands in the error arm.

### The visual gate — yours, and nobody has done it

**No window has ever been opened.** No display exists in this container, so every agent in
this loop verified through compilers and tests only. This step is real work, not a
formality, and it is the first time anyone sees whether this thing renders.

Per `flake.nix`: rsync the tree to the host (it excludes `target`, `node_modules`, `.venv`
— `governance/` is included, and must be), then **build and run in that copy**:

```sh
nix develop
npm run tauri dev
```

**Rebuild on the machine you run on.** The Rust side resolves `governance/registry.json`
from `CARGO_MANIFEST_DIR`, fixed at compile time. Recompiling on the host bakes in the
host path and everything lines up. Copying a container-built binary to the host and
running it will fail — loudly, naming `/app/src-tauri/...`, which does not exist there.
That is finding F-7, and it is a deliberate trade, not a bug.

What to look for:
- One row: **DEC-0**, "No generated file is named AGENTS.md", status `accepted`.
- A superseded decision, when one exists, must visibly show what superseded it. There are
  none yet, so this is untested by reality — the Vitest suite covers it with a fixture.
- Move `governance/registry.json` aside, reload: **an error naming the missing file**, not
  a blank table. If you get a blank table, that is a stop-everything bug.

### Closed after M0

- **CI ran green on its first execution** — PR #1, 200s, no fixes needed. The apt list
  was copied verbatim from `dev.Dockerfile` and the toolchains pinned to the container's
  versions, which is why it worked first time.
- **The window opens.** `cargo tauri dev` compiles and comes up on a host with a display.

The window renders and the decision text is on screen — confirmed by eye, 2026-08-18.
Still unexercised by hand: that moving `governance/registry.json` aside produces a named
error rather than a blank table. The Rust and Vitest suites both cover that path.

## Notes

Step 2 is the one that matters. Until it lands the gate is green while most of the repo
is unchecked, which is worse than a red gate because it looks like safety.
