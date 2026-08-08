# ⚠ FILED AFTER THE FACT — pZ verdict on `091d8bbc0c` (was NOT queryable when p4 landed it)

> **⚠ LATENESS DECLARED IN THE HEADING, ON PURPOSE.**
> verdict issued as a pane message (PZ-138) **2026-08-09 ~05:49 JST** — pane message only
> artifact **landed** by `a025394b95` **2026-08-09 06:29:07 JST**
> this file written **2026-08-09 07:09 JST** — **40 minutes after the landing**
> ⛔ **At the moment p4 landed this change, no desk could query this verdict.** p4 landed on the *report* that a verdict existed, not on the verdict. That gap is real; this file ends it going forward and does not erase it.

## 0. Artifact

| | |
|---|---|
| commit | `091d8bbc0ceef04a5e89c6ccfbed4c3ce4d7d5be`, authored 2026-08-09 06:21:23 JST |
| `ur15_steps_wired.py` | `6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50` — **unchanged** from `422ab807cd` (measured: `git diff --numstat` returns **zero rows**) |
| `render_cell_overview.py` | `9027f7e2c09f0820c762c660731814e300600b6302cf113e570fc2a794ab9855` |
| scope | 1 file, 1/1 — the whole diff: |

```
-MESH_SRC = Path("/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets")
+MESH_SRC = HERE.parents[2] / "thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets"
```

## 1. The acceptance test, with its precondition re-measured rather than inherited

- precondition, re-measured at **06:24:31**: main-tree copies of the 8 staged STLs vs the blobs at the commit — **8 compared, 0 differing**
- render output sha256 `91a106d16b22e955666c4003b24205c6ff95d6629489e86730fde5287f380b4b` — **equal to expected**
- ⇒ **the sha did not move.** p4's condition — a value-identical change leaves the output unchanged — holds by measurement.

## 2. The fix verified as a fix, not merely as a diff

Inside pZ's worktree at this commit: `HERE.parents[2]` = the worktree root; `MESH_SRC` inside it; **8 STLs there**; the run printed `[cell] staged 8 meshes into <that worktree>/…`.

⇒ **The staged meshes come from the artifact under test.** The earlier run (on `422ab807cd`) read them from the shared main checkout via the absolute path. ⛔ **That was an isolation defect in pZ's own verification, reported by pZ against pZ** — measured afterwards as not having bitten (8 compared, 0 differing), which is *a fact about that day, not a property of the method*.

## 3. Legs re-run on this artifact

- **§7 (i)** `/tmp/claude` → wired 0 rc=1, render 0 rc=1; per-leg controls `Path(` → wired 3, render **1**. ⚠ render's control fell from 2 to 1 **because the revision removed a `Path(` call** — expected, consistent with the diff, control still fires.
- **§7 (iii)** rc=0, `staged 8 meshes`, non-degenerate raster at the sha above. ⚠ the same `OpenGL error 0x502` warning recurred; rendering completed.
- **§7 (iv)** as (i). **§7 (v)** one file, zero C-2 edits.
- **Item 14** transfers **on content** — `wired`'s sha is byte-identical to the artifact where violations were measured **0**. Re-hashed, not assumed.

## 4. Still deferred by ruling

**§7 (ii)** unchanged — requires importing `ur15_steps_wired.py`, no `__name__` guard, runs the whole route. Producer side undemonstrated; no claim either way.

## 5. Not claimed

Physical validity is Rs's court (`:28`). The raster is evidence of **repair**, not **result**, and **is not the C-2 cell**. ⛔ **Not machine-independent**: the fix removes one of two dependencies; the seeded XML still carries **7** mesh references under `/home/rlrk/src/ur15-line-render/`, outside any repository. The 8/8 asset equality is a fact about **06:24:31**, to be re-measured, not inherited.

## 6. Landing, confirmed by pZ from the lane (PZ-141, 06:33)

`a025394b95` at 06:29:07 — landed `wired` and `render` both **equal** to the figures in §0; two files only; C-2's `ur15_cell_spec.py`/`sweep_mounting.py` untouched at 2fba2dfd67 / 2bb1aad4e7. ⚠ The landing diff read **26/4** on render — the *first* commit's shape, because it carried both commits against the lane's prior state. **It does not matter: the acceptance test is content equality, not diff shape.**

## 7. Provenance

All figures computed by pZ from the commit in pZ's own fresh detached worktree, removed afterwards; env pin `/home/rlrk/env_isaaclab7/bin/python` — newton 1.4.0 / mujoco 3.10.0 / warp 1.15.0. **Written by pZ; banking requested of a custodian — pZ has no measured grant to commit.**
