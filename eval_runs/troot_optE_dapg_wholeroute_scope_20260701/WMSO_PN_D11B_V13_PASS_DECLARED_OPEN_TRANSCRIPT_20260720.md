# WMSO D1.1-B v13 — pN PASS-WITH-DECLARED-OPEN transcript

**Transcript type:** custody records-only; exact-pin evidence/design readback

**Verdict measured:** 2026-07-20 23:18:34 JST

## Pins

- v13 design: commit `07250f4a02`; SHA256 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6`
- pS §31 record: commit `3ae8dc3a4c`; SHA256 `7da4bc10269c0c7e103a123a906625fe530d8a346cec94f5f13ffb524c78096c`
- Builder and four fixture pins: unchanged from the preceding verified version.

## Verdict

**PASS-WITH-DECLARED-OPEN.** v13 is a records-only precision correction. The `stats_key` risk is correctly narrowed: length-mismatched sharing is fail-closed, while same-length sharing has no uniqueness detector and can silently pass under a unique-required reading. The design semantics, builder, and fixtures are unchanged.

## Remaining boundary

B1 remains CLOSED. Freeze is a separate Rs-only gate. Implementation, training, and authority remain CLOSED.

## Procedure note

This exact-pin verdict is not itself the OPS-SUP consultation GO. The consultation leg is a separate explicit procedural step before any Rs freeze/push decision.
