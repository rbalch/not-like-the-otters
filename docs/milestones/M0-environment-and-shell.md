# M0 — Environment and app shell

**Status:** in progress. The environment half is done; the app does not exist yet.

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

1. Scaffold the app: React + Vite + TypeScript frontend, `tauri init` for the Rust core.
   Frontend lives in `app/`, Rust in `src-tauri/`; `src/` stays the Python harness.
2. Extend `make check` to cover all three languages. Rust: `cargo fmt --check`,
   `cargo clippy -- -D warnings`, `cargo test`. TypeScript: `tsc --noEmit`, a formatter
   check, `vitest run`. Both fold into the existing `lint` and `test` targets so `check`
   stays the single entry point.
3. One window listing decisions read from `governance/`.

## Done when

`make check` exits 0 while genuinely checking Python, Rust and TypeScript, and the app
window lists the decisions on disk.

## Notes

Step 2 is the one that matters. Until it lands the gate is green while most of the repo
is unchecked, which is worse than a red gate because it looks like safety.
