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
the Rust core headlessly with `cargo test`.

To see the real window, rsync the source to a machine with a display. `flake.nix`
provides a shell there with the same Rust and Node versions as the container, plus the
NixOS-specific fixes webkitgtk needs:

```bash
rsync -a --delete --exclude target --exclude node_modules --exclude .venv \
  server:/path/to/not-like-the-otters/ ./not-like-the-otters/
cd not-like-the-otters && nix develop -c cargo tauri dev
```

Flakes only see git-tracked files, so `git add` a new file before `nix develop` will
resolve it.

### Container credentials

`~/.ssh` and `~/.config/gh` are **named volumes**, not bind mounts of your host dotfiles.
The host ssh config is a home-manager symlink into `/nix/store`, which does not resolve
inside a Debian container, and a bind mount would hand the container every key you own
rather than the one this project needs.

One-time setup, after the first `make build`:

```bash
docker compose up -d
docker compose cp ~/.ssh/<your-github-key> dev:/home/dev/.ssh/id_github
docker compose exec dev chmod 600 /home/dev/.ssh/id_github
docker compose exec dev ssh -T git@github.com     # expect "Hi <user>!"
docker compose exec dev gh auth login
```

The image ships `/home/dev/.ssh/config` pointing at `id_github`, plus a `known_hosts`
entry for github.com. Both persist from then on.

Two things to know. A named volume is seeded from the image **only while it is empty**,
so changing the starter config in `dev.Dockerfile` will not reach a volume that already
exists — `docker volume rm not-like-the-otters_dev-ssh` first. And `docker compose down
-v` destroys both volumes, which means redoing the two steps above.

### Updating tools

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
