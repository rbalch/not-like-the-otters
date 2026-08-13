# not-like-the-otters

A Tauri desktop app that shows the state of its own development process — the decisions
that govern this repo, the findings its review loop produces, and which findings are
close to becoming enforced rules. The app is the smaller half of the project. It exists
so that an agentic build loop has something real to build, and so that loop's output has
somewhere to be read.

Not a product. One developer, one machine, no distribution.

## Development

All work happens inside the devcontainer. `uv` manages the Python harness and its
Python toolchain; `cargo` and `npm` manage the app.

The box is headless, so the Tauri window cannot open here. Develop the frontend against
the vite dev server on port 8010 and view it in a browser on your client machine; test
the Rust core headlessly with `cargo test`. To see the real window, rsync the source to
a machine with a display and run `cargo tauri dev` there.

Every CLI installs under `$HOME`, so updating one needs no rebuild and no sudo:

```bash
rustup update                                  # Rust
npm update -g @tauri-apps/cli @colbymchenry/codegraph
claude update                                  # Claude Code
uv self update                                 # uv
```

Those updates live in the container layer, not a volume — a rebuild resets them to the
versions pinned in `dev.Dockerfile`.

```bash
make check       # the single gate: controls → views --check → governance → tests
make views       # regenerate governance/views/RULES.md + registry.json
make governance  # integrity + drift check
make controls    # every controls/fitness/*.py, plus ruff and ty
make test        # pytest
```

## Governance

This repo runs a ledger governance harness. Architectural rules live as decisions under
`governance/decisions/`, each backed by an executable control under `controls/`, and CI
fails on any drift between them.

- **Agents read `governance/views/RULES.md`** — generated, live rules only. Never read
  `governance/decisions/` for rules; it retains superseded records on purpose.
- **`AGENTS.md`** is the hand-written contract: architecture, working context, and how
  work gets done here.
- **`docs/governance-harness.md`** explains why the harness exists and how to tell
  whether it is earning its keep.
- **`docs/ledger-findings.md`** is the experiment log.

Change a rule by supersession, never by edit. See the `ledger-ops` skill.
