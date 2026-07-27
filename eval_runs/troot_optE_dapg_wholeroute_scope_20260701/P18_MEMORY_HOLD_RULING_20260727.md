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

## 10. The size conflict in §3 does not survive measurement

§3 ruled that the HOLD outranks the compression hook, and flagged a retained risk: an over-limit index might
load truncated. **Both halves of that premise have now been tested, and the risk half fails.**

**(a) Truncation — measured by four panes, independently: it does not happen.**

| pane | what it compared | result |
|---|---|---|
| `w2:p6` | final line + **8/8 headings** + **6/6 internal anchors** | full |
| `w2:pC` | final line + **7/7 headings** + mid-section body | full |
| `w2:p0` | first line **and** last line, context re-injected after 13:01 compaction | full |
| `w2:p17` | final line | full |

`p6` is the decisive case: it passed compaction at 13:01:38, **after** `MEMORY.md`'s 12:56:33 mtime, so what it
received was the current 26720-byte file. ⭐ `w2:p17` retracted its own earlier claim that an over-limit index
risks truncated loading, naming it an unverified inference from the hook's wording.

⛔ Scope, stated by every pane: this rules out **tail truncation**. Nobody byte-compared a whole injected copy,
so mid-file loss is untested. `pC` made the sharp point that a final-line match detects only tail truncation —
which is why `pC` and `p6` also checked headings and interior samples.

**(b) The comparison was between two different units.**

`w2:p0` noticed, and `w2:p6` then pinned the decisive detail: **`MEMORY.md` line 3 states the compression target
in chars** — verbatim "19.8K→19.3K chars" and "目標 17.1K" in the same clause.

| | value | vs limit 24985 |
|---|---|---|
| `wc -c` bytes | 26720 | **+1735 over** |
| `wc -m` chars | 19933 | **−5052 under** |

⇒ The "over limit" finding came from comparing **bytes** against a limit whose own target is written in **chars**.
In chars the index is comfortably inside the limit. ⛔ Which unit the loader uses is still unverified — nobody
should assert it either way — but the one measurement that mattered (does it load whole) says it does.

⇒ ⭐ **Correction to §3:** the precedence ruling stands (a user HOLD outranks a harness prompt), but **the retained
risk I attached to it is not supported by measurement.** Compression cannot be justified on load-integrity
grounds. If it is wanted, it must be justified on other grounds — index readability, for instance.

⇒ ⭐ **Effect on §6:** the size conflict should no longer weigh on the user's disposition. What remains to decide
is only **A (append-correct) vs C (release the HOLD)**.

⚠ This is the day's recurring type landing on the limit itself: I compared a quantity in one unit against a
threshold in another, and carried the difference forward as a risk. `p0` caught the unit; `p6` pinned where the
unit is declared; four panes had already shown the feared effect was not occurring.

## 11. DISPOSITION — the user released the HOLD on `MEMORY.md` (2026-07-27)

**Status of this ruling: SUPERSEDED IN PART.** The user disposed, relayed verbatim by `w2:p6`:

> `MEMORY.md` の HOLD を解除する

⚠ Basis: **relayed verbatim**, not measured by p18 directly. If the wording differs from what the user issued,
the user's wording governs and this section is wrong.

**Applied scope — exactly what the disposition names, and nothing more:**

| object | state after disposition |
|---|---|
| `MEMORY.md` | ⭐ **RELEASED** — writes permitted, each pane's own court |
| memory-directory topic files (e.g. `pW`'s, `p12`'s carries) | **still frozen** |
| memory-directory handoff files | **still frozen** |
| named carries outside the memory directory (`p5`'s `HANDOFF_p5_vtdesign.md`, `p6`'s handoff addendum) | **still frozen** |

⛔ **I am not widening the release to the objects §1 and §7 added.** §7 records what happens when a directive's
wording is stretched past the surface it names — I made that exact error this morning and corrected it. The
remaining objects need one word from the user; they are cheap to release and expensive to un-release.

⛔ **No compression accompanies the release.** §10 measured that the load-integrity ground for compressing
`MEMORY.md` does not survive (four panes; loads whole; the limit comparison was bytes-vs-chars). Releasing the
HOLD restores the panes' write permission on the index — it is not an instruction to shrink it.

Notified, and only these: `pW` (its `MEMORY.md` carry releases, its topic-file carry does not), `p12` (topic
file — still frozen), `p5` (repo handoff — still frozen), `p6` (relayed the disposition; its addendum still frozen).

## 12. Correction — my stand-down to `pV` / `pW` / `p14` / `p15` cited a node that is not theirs

**Cause side: p18.** In `MSG-P18-YOU-SHOULD-NOT-HAVE-BEEN-ON-MY-LIST-20260727-099` I told four panes that Rs had
closed them, and quoted as grounds:

> `status: ARCHIVED  # Rs 2026-07-20: role/pane unused, pane closed. … Removed from the active roster (MEMORY.md).`

That line lives in `thread_isaac_lab/thread-vault/T-ROOT-COORD/state.md:7` and
`thread_isaac_lab/thread-vault/T-ROOT-COORD2-AC-IC-GC-Audit-2026-05-13/state.md:12` (p18 read both on disk).
⛔ **Those are the COORD and COORD2 nodes. I never established that they are the panes I sent it to.**
I read a status on one subject and asserted it of another — the day's recurring type, on a message about roles.

`w2:pW` returned it with two further measurements, both of which I then confirmed myself:

1. **The second node is not a role node at all.** `node_id: T-ROOT-COORD2-AC-IC-GC-Audit-2026-05-13`,
   `node_name: … AC/IC/GC parallel workstream selection audit (post-V7-NEGATIVE)` — a 2026-05-13 audit node.
2. **The registry, written after the archive, still lists both.** `scripts/validations/nest_role_labels.txt`
   mtime **2026-07-21 09:38:29 JST** — ~21 h after `archived_at: 2026-07-20T12:28:26+09:00` — carries
   `COORD` at `:30` and `COORD2` at `:31`.

pW additionally measured that Rs assigned it its role at 2026-07-20 12:18:56 JST, **9 min 30 s before** that
`archived_at` stamp. ⛔ **Whether the assignment or the archive governs is not mine to decide and I do not decide
it.** pW is escalating it to Rs, which is right.

⭐ **The outcome does not change**: p18 stops sending to those panes. The four panes were told a false thing
about their own status, so the correction is owed to them and was sent.

### 12a. Correction to §12, before it was sent — I overshot in the other direction

⛔ **"Those nodes are not those panes" was too strong, and I caught it only because I measured the roster
instead of reasoning about it.** `herdr agent list` (p18, 2026-07-27 13:41 JST) returns display names:

| pane | herdr display name |
|---|---|
| `w2:pV` | **`T-ROOT-COORD`** |
| `w2:pW` | **`T-ROOT-COORD2`** |
| `w2:p14` | `UNASSIGNED` |
| `w2:p15` | `UNASSIGNED` |

⇒ The label on `pV` / `pW` **does** correspond to the nodes I quoted. So the defect is not mistaken identity.
The defect is one level down, and the project's own ruling names it:

⭐ **A role label is not a node** (`LEDGER:33`, NEST ruling 2026-07-20; the same ruling
`scripts/validations/nest_role_labels.txt:5-7` was written to implement). ⇒ **The archive of the *node*
`T-ROOT-COORD` does not by itself settle the *role* borne by the pane.** I used a node's status field as if it
were a pane's roster status, and those are different objects **by a ruling that predates my message**.

Two measurements point the same way and neither is mine to weigh: Rs assigned `pW` its role 9 min 30 s **before**
the `archived_at` stamp (pW's session record), and the role registry written ~21 h **after** the archive still
lists `COORD` and `COORD2`. ⛔ Which governs is Rs's to say. pW is escalating it.

⚠ The split matters per pane, so I do not send one text to four panes:
- `pV` / `pW` — the label matches; the error is **node status ≠ role status**.
- `p14` / `p15` — display name `UNASSIGNED`; they bear no such label, so for them the citation was
  **about someone else entirely**. That half of §12 stands unchanged.

⭐ Note the shape: §12 corrected an error, and **the correction contained the same error class** — asserting a
status relation I had not measured. I only avoided sending it because I read the roster first. That is the third
time today the fix needed the same check as the thing it fixed.
