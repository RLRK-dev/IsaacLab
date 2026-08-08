# ⚠ FILED AFTER THE FACT — pZ verdict on `3b4ddfd7ff` (was NOT queryable when p4 landed it)

> **⚠ LATENESS DECLARED IN THE HEADING, ON PURPOSE.**
> verdict issued as a pane message (PZ-144) **2026-08-09 06:46 JST** — pane message only
> artifact **landed** by `79d2f2be47` **2026-08-09 06:48:22 JST**
> this file written **2026-08-09 07:10 JST** — **22 minutes after the landing**
> ⛔ **At the moment p4 landed this change, no desk could query this verdict.** This file ends that going forward; it does not erase it.

## 0. Artifact

| | |
|---|---|
| commit | `3b4ddfd7ff1fb268db8335164861e436fa8adb40`, authored 2026-08-09 06:40:49 JST, parent `2d16acdd68` |
| `ur15_steps_wired.py` | `6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50` — **unchanged** |
| `render_cell_overview.py` | `4a37a966d4c98818f8a717fa5b05a555576feadb81316ebce378fcaff7c58e5e` |
| scope | **1 file, 1/1**, measured against **its own parent** — the whole diff: |

```
-    out = HERE / "UR15_CELL_OVERVIEW_20260729.png"
+    out = _GEN / "UR15_CELL_OVERVIEW_20260729.png"
```

⛔ **A scope figure pZ nearly reported wrong, caught before sending**: `git diff --numstat HEAD..3b4ddfd7ff` returned **four files** — render plus three docs at 0/25, 0/66, 0/26. That is a **diff-direction artifact**: the branch point is `2d16acdd68` and the lane had moved past it, so doc sections landing *after* the branch point appear as deletions when a moving tip is the base. ⇒ **The correct base for "what does this commit change" is its own parent, never a branch tip that keeps moving.**

## 1. The three conditions

1. **raster at the new path** `_gen/UR15_CELL_OVERVIEW_20260729.png` = `91a106d16b22e955666c4003b24205c6ff95d6629489e86730fde5287f380b4b` — **equal**. Same bytes at a different path, which is the correct form for a relocation.
2. **the tracked PNG at the old path is not dirty** — `git status --porcelain` **empty before and after** the run; the file is still present, content `100078c8435fe9be…`, equal to the tracked blob. ⇒ **met by invariance, not by absence.** ⛔ A checker phrased as "no file at the old path" would **fail this correct implementation**.
3. **(2) is meaningful** because the same check returned `" M "` on the pre-fix code — demonstrated at **06:39:25** (PZ-143), *before the fix made that demonstration impossible*. ⭐ **The control for a test can have a shorter lifetime than the test.**

## 2. The rest, re-run rather than assumed

- **no route to the tracked PNG survives**: `HERE / "UR15` occurrences **0, rc=1**; control `_GEN /` **3, rc=0**
- **§7 (i)** `/tmp/claude` → wired 0 rc=1, render 0 rc=1; controls `Path(` → 3 and 1
- **precondition, re-measured in a stronger form**: the 8 STLs compared **worktree-copy vs commit blob** — 8 compared, 0 differing. Since `MESH_SRC` now derives from the worktree, this is the comparison that governs.
- run rc=0, `staged 8 meshes into <worktree>/…`, `[out] <worktree>/…` — both inside the artifact under test
- **Item 14** transfers **on content** — `wired`'s sha byte-identical to the artifact where violations were **0**. Re-hashed.

## 3. Not claimed

Physical validity is Rs's court (`:28`); the raster is evidence of **repair**, not **result**, and **is not the C-2 cell**; not machine-independent (7 mesh refs under `/home/rlrk/src/…`); the 8/8 equality is a fact about **06:44:46**, to be re-measured.

## 4. Landing, confirmed by pZ from the lane (PZ-145, 06:49)

`79d2f2be47` at 06:48:22 — both files **equal** to §0; lane route to the tracked PNG **0**.

⚠ **The commit pZ verified is NOT an ancestor of the lane**: `git merge-base --is-ancestor 3b4ddfd7ff HEAD` → **NO**. The branch commit was not merged or cherry-picked; the same one-line change was re-authored on the lane, and the resulting content is byte-identical.

⇒ ⭐⭐ **A lineage-based acceptance condition would have reported a false failure on this correct landing.** "Is the verified commit an ancestor?" answers NO. "Is the landed content what was verified?" answers YES, both files, to the byte. This is the third unpredicted shape the content condition absorbed — after a squashed landing carrying two commits, and a diff reading 26/4 when the revision was 1/1.

## 5. Provenance

All figures computed by pZ from the commit in pZ's own fresh detached worktree, removed afterwards; env pin `/home/rlrk/env_isaaclab7/bin/python` — newton 1.4.0 / mujoco 3.10.0 / warp 1.15.0. **Written by pZ; banking requested of a custodian — pZ has no measured grant to commit.**
