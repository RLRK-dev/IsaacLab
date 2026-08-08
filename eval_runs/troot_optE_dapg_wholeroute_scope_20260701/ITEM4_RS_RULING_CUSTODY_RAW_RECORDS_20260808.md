# Item 4 — Rs ruling: raw custody records (durable copy)

**Why this file exists.** Rs's instruction closing open-item 4 exists in only two places, and
both of them are inside a **session transcript**, which is pruned. Ledger §1151 recorded the
general form of this failure: *the one event with no permanent witness was the one event missing
from the permanent surface.* This file is the permanent surface for that event.

**Source.** `~/.claude/projects/-home-rlrk-IsaacLab/2dbed74a-e29c-45a7-ad8a-5c5af235885b.jsonl`
(w2:p6 = PLAN-KEEPER). Located by p6 (m-p6-43) with line numbers; every record read and verified
first-hand by p18 before extraction. Extracted verbatim, byte-for-byte, no reformatting.

**The two independent acts, 13 seconds apart, in agreement.**

| src line | type | timestamp (UTC) | what it is |
|---|---|---|---|
| 19966 | `queue-operation` (`enqueue`) | 2026-08-08T01:41:53.537Z | Rs types 「５件はすべて推奨で」 |
| 19967 | `queue-operation` (`remove`) | 2026-08-08T01:42:06.627Z | its delivery |
| 19969 | `assistant` / `tool_use` | 2026-08-08T01:41:59.414Z | p6 puts the ambiguity back as a labelled 3-option set (`AskUserQuestion`, id `toolu_01CDermmgKMNVWuJHFNb26zY`) |
| 19970 | `user` / `tool_result` | 2026-08-08T01:42:06.610Z | Rs's selection, verbatim: `="4・6 を close、7/8/9 は据置 (Recommended)"` |
| 19971 | `attachment` | 2026-08-08T01:41:53.537Z | `queued_command`, prompt identical, **`"origin": {"kind": "human"}`** |

`origin.kind = "human"` is a machine-written provenance field: it is the strongest custody
attestation handled in this ledger to date.

**Grade.** Both acts are first-hand objects read by p18 in p6's transcript. Neither is a relay.
p6 declined to bank them themselves on the ground that custody is p18's surface — correct.

**What it does not cover.** JST instants are UTC+9 of the above. This file preserves the ruling's
custody only; the disposition it produced is recorded in ledger §1167 and the item-4 close.

Raw records: `ITEM4_RS_RULING_CUSTODY_RAW_RECORDS_20260808.jsonl` (5 records, extracted verbatim).
