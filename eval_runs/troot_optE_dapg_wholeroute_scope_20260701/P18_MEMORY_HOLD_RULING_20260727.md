# p18 ruling — memory-directory HOLD (scope, precedence, and why this record lives here)

**Author:** `w2:p18` T-ROOT-OPS-SUPERVISOR (routing / evidence gate).
**Issued:** 2026-07-27 (JST, `date`-measured at write time; see commit author time for the authoritative stamp).
**Status:** ACTIVE until the user issues a disposition.

## 0. Why this file exists (read this first)

`w2:pC` identified a self-defeating loop in my ruling `MSG-P18-HOLD-SCOPE-RULING-20260727-086`:

- The ruling says "record this ruling as your reason for not complying with the compression hook."
- The HOLD covers the **whole memory directory**, including `handoff` files.
- ⇒ **The only places a pane would normally record it are themselves under the HOLD.**
- ⇒ After `/clear` or compaction, a pane does not know the ruling, and may comply with the hook.

This is the same shape as the conflict in §3 below: **the HOLD blocks the record needed to keep the HOLD.**

Fix: this ruling is banked **outside** the memory directory, in the repo, where it is git-tracked and
survives session boundaries. Panes may read it without writing anything under HOLD.

## 1. Scope of the HOLD

**The HOLD covers the entire memory directory** — `MEMORY.md` (index) **+ topic files + handoff files.**
It is not limited to `MEMORY.md`.

Grounds (each pane's carry names a non-`MEMORY.md` file, so the HOLD was never index-only):

| pane | carry object |
|---|---|
| `w2:pW` | `reference-herdr-dispatch-2step-replaces-dispatch-to-pane-2026-07-04.md` (topic) + `MEMORY.md` |
| `w2:p5` | `02-Workflow/HANDOFF_p5_vtdesign.md` (handoff) + `MEMORY.md` |
| `w2:p12` | `reference-codex-pane-long-dispatch-paste-mode-2026-07-18.md` (topic) |

**Directive:** no writes anywhere under the memory directory until the user disposes.
**No revert is required or wanted** — a revert is itself a write under HOLD.

## 2. Pre-notification writes are not violations

The existence and scope of the HOLD were broadcast to all panes for the first time in `-086`.
Before that, only `w2:p16` had been notified individually. **Writes made before that broadcast are recorded, not charged.**

Self-disclosed footprints (received as declarations): `p17` 5 edits; `pC` one `MEMORY.md` edit 07-26 plus 2 topic
files today; `p16` line 13 plus 3 topic files; `p12` one topic file (held unchanged since); `pB` two `MEMORY.md`
edits 07-26, none since.

⚠ **The memory directory is not under version control** (`git rev-parse` → not a git repository).
⇒ Authorship cannot be verified and content cannot be recovered from it. **All footprint statements above are
declarations, not diffs.** `pC` and `pW` both flagged this limit about their own statements; that is the correct posture.

## 3. Precedence: the user's HOLD outranks the harness compression hook

`MEMORY.md` exceeds the session read limit, so an automatic instruction to compress fires on edit.
Under HOLD that instruction cannot be obeyed, and obeying it would breach the HOLD.

**Ruling: the user's HOLD takes precedence. Do not compress.** Cite this file as the reason.

Measured (p18, 2026-07-27): `MEMORY.md` = 26720 bytes; read limit 24.4 KB = 24985 bytes ⇒ **1735 bytes over**;
the hook's target of 17.1 KB = 17510 bytes would require **−9210 bytes**.

⚠ Risk retained and surfaced to the user: an over-limit index may load truncated in every session.

## 4. Corrections to my own earlier statements

- ⛔ I wrote "there is no recovery source" for `MEMORY.md`. **Too strong** (`w2:p17`): 19 `MEMORY.md.bak_*` files exist,
  newest `MEMORY.md.bak_pre_p6owner_20260721` (2026-07-21 17:24, 24521 bytes).
  ⭐ What survives: **no snapshot exists at the HOLD boundary** (newest is ~6 days before the current file),
  so a revert would roll back not just HOLD-period writes but ~6 days of every pane's work.
  For **topic files** the original claim stands: the carried topic files have **0** backups.
- ⛔ I attributed to `w2:p12` a measurement it had not made (byte-identity of the §0 #1 predicate clause).
  `p12` declined the attribution and then measured it. Corrected.

## 5. Open discriminator (nobody has run it)

`w2:p12` proposes a one-step test that decides whether compression is needed at all:
**a newly starting pane checks whether its in-context `MEMORY.md` ends with the same final line as on-disk.**
If it matches, an over-limit index still loads whole; if not, truncation is real.

⚠ `p12` also measured that being over the limit is **not new** — backups show 2 weeks of operation above 24985 bytes.
⇒ "over limit" has been the normal state, not an emerging failure.

## 6. What the user is being asked to decide

- **A) Append-correct** — keep the old text, add the transfer and UR15 notes. Needs no recovery source.
- **C) Release the HOLD** — return each file to its pane's court. Does not depend on a recovery source.
- ⛔ **B) revert is not cleanly available** — no HOLD-boundary snapshot, and the memory directory is
  git-unmanaged, so any revert rests on panes' recollection rather than verified content.

Plus: the §3 size conflict, and (per `pC`) where a ruling like this one should live so it survives `/clear`.

## Non-claims

This file records a routing/gate ruling and its grounds. It takes no design position, flips no gate, authorises
no run, and changes no status. Numbers attributed to other panes are their measurements unless marked as mine.
