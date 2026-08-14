# M3 — The spec compiler

**Status:** not started. Deliberately last.

## Goal

Make a human-skimmable spec the binding source of the tests, so a builder has to satisfy
tests it did not author.

## Why last

A spec written for a feature that does not exist teaches nothing. This lands once there
is enough real work to know what a spec should have said.

## Scope

The yaml's job is **compression, not correctness** — it turns a couple of hundred lines
of test code into a dozen a human reads in thirty seconds. A skim only binds if the chain
below it is mechanical, so there is no reviewer agent confirming the tests match the
spec; there is a generator that makes them match.

Two tiers, so the generator never becomes a compiler:

- **Full generation** — table-driven cases with serializable input and output. Tauri IPC
  commands fit this almost exactly. The generator emits real test bodies.
- **Stub generation** — the yaml declares a case exists; the generator emits a named
  failing stub and nothing else. A human or the builder writes the body.

Tier B is the answer to "interfaces are hard to express in yaml": you do not express
them. You express that a case must exist and must not be skipped. The freshness check
enforces the mapping — every case has a live test, every generated test traces to a case
— and never inspects the body.

Anything fitting neither tier is hand-written in `tests/written/` with no ceremony.

## Done when

Approving a yaml file is equivalent to approving its tests, because editing a generated
test turns the gate red — the same pattern `build_views.py --check` already uses.

## Notes

Keep the yaml at contract altitude. The moment it specifies mock call counts it has
failed; write that test by hand.

This is design *by codegen*, not design by contract. Real DbC is runtime pre/post
conditions and invariants. If that is what is wanted, say so — it is a different
milestone.
