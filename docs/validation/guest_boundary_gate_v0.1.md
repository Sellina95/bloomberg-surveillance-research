# Guest Boundary Gate v0.1

## Status

CLOSED — PASS

## Purpose

Validate deterministic guest-interview boundaries from the normalized
transcript using explicit broadcast transition signals.

## Validated Date

2026-08-14

## Boundary Rule

A guest interview unit begins at an explicit guest-introduction signal
such as:

- `joins us now`
- `joins us`

The interview continues through the subsequent host/guest exchange.

The unit ends at an explicit transition signal such as:

- `stay with us`
- `coming up`
- `thank you so much`
- `thanks for having me`

## Validation Result

| Guest Unit | Start Segment | End Segment | Duration | Result |
|---|---:|---:|---:|---|
| 1 | 4 | 46 | 456.1s | PASS |
| 2 | 48 | 54 | 98.0s | PASS |
| 3 | 55 | 69 | 281.8s | PASS |
| 4 | 70 | 71 | 32.0s | PASS |

## Evidence

All four validated guest candidates contained:

- explicit start signal
- identifiable end signal
- deterministic start/end segment selection

Result:

**4 / 4 PASS**

## Scope

This gate validates the rule on the 2026-08-14 transcript.

It does not establish universal validity across all Bloomberg
Surveillance episodes.

Additional dates are required before treating this rule as
production-generalized.

## Gate Decision

CLOSED — PASS
