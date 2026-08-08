# ⚠ FILED AFTER THE FACT — pZ verdict on `422ab807cd` (was NOT queryable when this artifact was superseded)

> **⚠ LATENESS DECLARED IN THE HEADING, ON PURPOSE.** This verdict was issued as a pane message (PZ-131) at **2026-08-09 ~06:01 JST** and existed **only** there. It was written to this repo surface at **2026-08-09 07:08 JST** — over an hour later, and **after** the artifact it covers had already been superseded. ⛔ **It was not available to any desk as a queryable file at the time it mattered.** A retro-filed verdict that does not declare its own lateness would manufacture the very ground it documents the absence of.

## 0. Artifact and its fate

| | |
|---|---|
| commit | `422ab807cd647cf4baed8db4ef93922e9c58e09e`, authored 2026-08-09 00:47:41 JST |
| `ur15_steps_wired.py` | `6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50` |
| `render_cell_overview.py` | `b1d528523821c73409cf5441c6f66342232632b5e8a78ad7c9a5d7c031eab69f` |
| merge-base with the lane | `df9d220b2fe4111c22ad28b63a2ac2a4a5718de0` |
| **landed?** | ⛔ **NO.** Measured: that render content appears in **0** commits of the file's history. It was superseded by `091d8bbc0c` before any landing. |

⇒ This verdict covers an artifact that never reached the lane. It is filed for the record of what was verified, not as evidence about lane content.

## 1. Confirmed

- **§7 (i)** `/tmp/claude` in both scripts: **0 hits, rc=1**, with per-leg positive controls (`Path(` → wired 3, render 2, rc=0). Each zero is discriminating because the same query returns nonzero on the same file.
- **§7 (iii)** executed under p4 ruling (a) — **wired never imported**. Seed = the tracked snapshot `asbuilt_snapshots/_steps_cell_full_asof_20260804_152626.xml`, sha256 `28c242410314b199042acd0349a00e5937ccb08dbcd53e336a13a0fa8b944cab`, identical to p4's banked figure. Run rc=0; `[cell] staged 8 meshes`; raster `UR15_CELL_OVERVIEW_20260729.png` 446,066 bytes, 2400×1760 RGB, sha256 `91a106d16b22e955666c4003b24205c6ff95d6629489e86730fde5287f380b4b`, 8,172 distinct colours ⇒ **non-degenerate raster**. ⚠ `WARNING: OpenGL error 0x502 in or before mjr_makeContext` observed; rendering completed. The pixel statistics were taken **because** that warning makes "a file exists" insufficient.
- **§7 (iv)** no consumer of the old path remains in the two files (same measurement as (i)).
- **§7 (v)** two files only, pathspec-limited, no C-2 edits mixed in.
- **Item 14** violations **0** over a complete 25-line target set, instrument pinned at addendum content sha256 `e5dd839672ae7692aeb85d5b54a133a0b43472e24dbba380a26f9ecab9a1148c` — byte-identical to the version p4 ruled.
- ⭐ **The design was wrong and the implementation right**: §7 says "gripper mesh 5 件"; the real generated XML asks for **8** bare-name STLs, all present in `MESH_SRC`. p0 reads the set off the XML rather than hardcoding a list.

## 2. Deferred by ruling, not by defect

**§7 (ii)** — requires importing `ur15_steps_wired.py`, which has **no `__name__` guard** and runs the whole route including the video write. Deferred by p4. ⛔ Not executed; no claim in either direction. The **producer side of the repair is undemonstrated**; (a) exercised the consumer side only.

## 3. Findings filed with this verdict (owners elsewhere)

1. `_gen` is **not gitignored** (`check-ignore` rc=1 both with and without `--no-index`) — **not a §7 violation** (§7 says do-not-track and nothing is tracked), but staging copies **8 STLs / 3.1 MB** of *already-tracked* content into a shared tree where a pathspec-wide `git add` would sweep them.
2. The output filename is hardcoded `UR15_CELL_OVERVIEW_20260729.png` — three dates in one artifact.
3. Two gaps in A-9's predicate: the assignment pattern misses `:2645 LX1, RX1 = …` and `:2646 LX2, RX2 = …` (comma-tuple, and `LX1`/`RX1` absent from the alternation); and the row anchor must be `STEPS = [`, not the `STEP table` comment 64 lines away — a literal reading captures **zero** rows and still reports zero violations.

## 4. Not claimed

Nothing about physical validity (Rs's court, role brief `:28`). The raster is evidence of **repair**, not of **result**, and **is not the C-2 cell**. Completeness of intent out of scope.

## 5. Provenance

All figures computed by pZ from the commit in pZ's own fresh detached worktree, removed afterwards; env pin `/home/rlrk/env_isaaclab7/bin/python` — newton 1.4.0 / mujoco 3.10.0 / warp 1.15.0. **Written by pZ; banking requested of a custodian — pZ has no measured grant to commit.**

---

## ⛔ CORRECTION 2026-08-09 07:20 JST — appended, nothing above is rewritten (ruling A)

**What is wrong, and it is in the sentence a reader takes away.** §0's row label reads `**landed?** | ⛔ **NO.**` and the line under the table reads *"This verdict covers an artifact that never reached the lane."* **Both are unqualified, and at file resolution the second is false.**

**Measured, 2026-08-09 07:20 JST — one commit, two files, two fates:**

| file | content at `422ab807cd` | on the lane now? |
|---|---|---|
| `ur15_steps_wired.py` | `6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50` | ✅ **YES** — identical content is the lane's `wired` today |
| `render_cell_overview.py` | `b1d528523821c73409cf5441c6f66342232632b5e8a78ad7c9a5d7c031eab69f` | ⛔ **NO** — appears in **0** commits of that file's history |

⇒ **`422ab807cd` gave the lane `wired` only.** The correct statement is per file, not per commit.

**Why the original wording was wrong even though its measurement was right.** The cell text says *"that **render** content appears in 0 commits"* — correctly scoped. The **row label**, the **bold NO**, and the **summary line** carry no such scope, and those are what a scanning reader reads. ⭐ Same shape as putting a marker where the reader does not land: *the qualification existed and was not where the claim was made.*

**Attribution.** The general form is p11's — hold it as *"is that file's content on the lane"*, never *"did the commit reach the lane"*, because a commit follows a different fate per file. p0 had already corrected their own chain table to *"`422ab807cd` gave the lane wired only"*. ⛔ This correction is not a new finding; it is that rule applied to this file, which I should have applied when writing it.

⚠ **Scope of the correction.** Nothing else in this verdict changes: every figure, every leg, every condition and every exclusion above stands as measured. What changes is one claim about the artifact's fate, from a commit-level *no* to a file-level *wired yes / render no*.
