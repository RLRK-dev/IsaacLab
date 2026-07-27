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

---

## 7. Correction — the scope wording did not cover the file I used as grounds

**Cause side: p18.** `w2:p5` found that §1's conclusion and its grounds sit on different surfaces.

I wrote the directive as *"stop all writes **under the memory directory**"*, and used `w2:p5`'s carry as grounds
for the scope being wider than `MEMORY.md`. But p5's carry file is
`thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md` — **in the repo, untracked, not under the
memory directory at all** (p18 measured: 105852 bytes, mtime 2026-07-26 21:19, `git ls-files` → untracked).

⇒ **The wording did not cover the very file it was argued from.** Same shape as the day's recurring type: the
surface I measured and the surface I concluded about were different.

**Corrected directive:** the HOLD covers **the memory directory in full, plus any file a pane has named as its
carry**, wherever that file lives. p5 has kept its handoff frozen regardless of the wording, which is right —
the freeze comes from the original user disposition, not from my phrasing.

## 8. The queued env update is a spec-surface event, not only a venv event

`w2:p5` measured that `RS71-System-Spec-SSOT.md:15` itself records the environment (p18 confirmed, verbatim):

> `Env: env7 Newton 1.2.1 / mujoco 3.8.1 SolverMuJoCo, UR15×2 + Robotiq 2F-85. HEAD `7afa84b463`.`

⇒ The queued update to newton 1.4.0 / mujoco 3.10.0 **makes this spec line false the moment it runs.**
So the update touches a spec surface, not just a virtualenv. p5 does not hold that line's court and has not
touched it; it is surfaced here for the line's owner.

⚠ Two further measurements on the same line: it does **not** name `mujoco_warp` or `warp-lang` (the same omission
`w2:p0` disclosed in its own provenance — different surface, same shape), and its `HEAD` pin `7afa84b463` is
**already stale** (p18 measured current HEAD well past it; the shared branch moves continuously).

## 9. Two quantities that must not be cross-compared

`w2:pB` flagged a collision risk before anyone hit it:

- pB's banked **24.0 mm** = distance between the two pad **body origins** (`mjOBJ_BODY`, `Lg_left_pad` / `Lg_right_pad`)
- p4's new **−1.3 mm** = **geom face** separation via `mj_geomDistance`

⇒ Both can hold at `ctrl=255` simultaneously, because the pad geoms are offset from their body origins.
⛔ **Neither refutes the other. Do not put them in the same column.**

⚠ pB also measured that on-disk `ur15_steps.py` has already moved off its banked pin, so line numbers in pB's
document must be read at commit `bfb517862c809943042074bae6eb6e51e4f70875`, not on disk.
