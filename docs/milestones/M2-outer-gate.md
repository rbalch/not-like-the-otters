# M2 — The outer gate

**Status:** not started. Blocked on M0 step 2.

## Goal

Put `no-mistakes` in front of the remote so a finished branch is validated and turned
into a PR without hand-holding, and so its findings feed the ledger instead of
evaporating.

## Scope

- Wire `no-mistakes` as the push gate.
- Its test and lint steps run `make check`. One quality bar, not two — this is why M0
  step 2 has to land first.
- Its `review` step runs `boundary-reviewer` with `governance/views/RULES.md`. One
  reviewer with one rule set, invoked cheaply in the inner loop and authoritatively at
  the gate, rather than two reviewers with opinions that can disagree.
- Every finding it raises is filed as a sighting, feeding M1.
- Intent is passed explicitly via `--intent`: the objective in the user's words, not a
  description of the diff.

## Done when

A branch pushed to the `no-mistakes` remote is validated, opens a PR, and leaves its
findings in `docs/ledger-findings.md`.

## Notes

Auto-fix is the risk. The harness changes rules only by supersession in a diff a human
reads; a gate that silently fixes the same slop forty times starves the rule of three of
its evidence. Keep auto-fix attempts low and prefer escalation.

Worktrees are the other trap: `no-mistakes` creates disposable ones, and a worktree
records absolute paths. The repo is `/app` in the container and
`/home/ryan/code/not-like-the-otters` on the host, so the gate must run consistently on
one side of that boundary.

Prerequisite outside the code: `main` currently has no upstream and sits at the scaffold
commit. The gate needs a real target.
