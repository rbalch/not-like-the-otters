# M1 — Sightings to proposed rules

**Status:** not started.

## Goal

Close the loop end to end. Today the only fully manual link in the harness is
sighting → proposed rule; this milestone automates the bookkeeping and leaves the
judgement to a human.

## Scope

- Fingerprint findings logged in `docs/ledger-findings.md` so repeat sightings of the
  same thing group together.
- Apply the rule of three: at the third sighting, emit a proposed-decision stub.
- Surface proposals in the app.
- Approving a proposal dispatches `control-author` to write the decision and its control.

Each sighting records file, commit, date, who raised it, and the offending snippet. The
evidence is the point: at promotion time those three sightings are three ready-made red
test cases for the control, and without them you are staring at a counter trying to
remember what annoyed you in April.

## Done when

A finding seen three times appears in the app as a proposal, and approving it produces a
decision plus a control that goes red on the logged examples and green on clean code.

## Notes

Built before M5 (the outer gate) even though M5 feeds it. Hand-fed until then — and at
current volume hand-feeding is not straining: 8 findings, none past two sightings.
