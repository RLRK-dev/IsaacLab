# OP030 production-line source checkpoint

Snapshot: 2026-09-10T20:44:45.897334+09:00.

The completed v05 review has three OP030 stations: support placement and M4 fastening (A), two-wire placement (B), and parallel M6/M14 fastening with replenishment (C). Robot motion and interference reports are auxiliary geometric checks; this checkpoint does not certify force, torque, grasp stability, or physical validity.

The v06 files are work in progress for a staggered B robot and supply table. The final static air-pipe candidate has been saved. At this checkpoint the final B connection/replay and integrated native checks are still pending; no completed v06 delivery is claimed. See `analysis/OP030_v06_scope.md` and the v06 process document for the intended change.

## Included source

The explicit entrypoints and local-import closure are recorded in `checkpoint/source_snapshot.json`: 85 files in the v05 authoring/replay closure, 76 in the v06 closure, with shared helpers deduplicated. The 19 proven v05 bake/review sources were copied from the completed delivery stage; their bytes matched the live originals at capture. Reused OP010/OP020 FK and gripper calibration are retained under `inputs/` because the OP030 planners import them.

The small selected JSON reports are observations at their recorded timestamps. Missing raw reports, binary meshes, native scenes, and motion arrays are deliberately referenced by SHA and local path rather than added to Git. This is a source/evidence checkpoint, not a self-contained build of the entire line. CLI-selected native inputs and mesh banks remain required.

## Completed v05 artifacts

Delivered local archive: `/home/rlrk/Downloads/UR15_JB_OP030_20260910_v05.zip`

SHA-256: `ee592e8c33faf3c596259419c48127c36cf3c5ee4311b61a49789241ef49eb87`

Size: 632161327 bytes. Its expanded directory contains the review page, movies, native scene, prepared arrays, provenance, and exact bake source. Local working material is under `/home/rlrk/IsaacLab/eval_runs/ur15_jb_harness_revision_20260907`. Artifact paths and digests are in `checkpoint/source_snapshot.json`; the ZIP and large assets are excluded from this Git branch.

Use the completed delivery README for the verified Blender bake/render commands. Python authoring uses existing NumPy/SciPy/FCL/OMPL and the existing original renderer dependencies; Blender provides bpy/mathutils. No new dependency or installation step is introduced here. The JSON profile under `inputs/` is small enough to retain; other runtime CAD/data inputs must be restored from the local artifacts before authoring can run.

## Branch and checks

This feature branch, `rlrk/ur15-op030-checkpoint-20260910`, starts at published `fork/main` commit `3e73d6dd79080fd7632488c061052a6edd52e230`. Exactly 136 staged checkpoint files were copied from the earlier isolated worktree through an explicit allowlist, preserving file modes. Every selected path is under `eval_runs/ur15_jb_harness_revision_20260907/`. The 19 unpublished commits on the active work branch are not included.

The earlier worktree used the unrelated published task branch `fork/rlrk/optE-s2-substrate-swap` at `1ab60539330f76b0ecb1c2d6097a3d1a37beadef`. Its 136 checkpoint files passed the selected-file hooks, but the full repository hooks reported 42 Ruff violations and seven executable-mode violations in that base. Moving this checkpoint to main avoids importing or repairing those unrelated task files. The old worktree and its full preflight logs remain preserved.

Checkpoint source digests and `formatter_review.json` describe the captured artifacts and their isolated formatted copies. They are retained as timestamped observations; moving the branch base does not change the original frozen sources or their physical-check provenance. The full repository hooks must pass on this main-based worktree before commit.

## Formatter review boundary

The isolated copies were formatted; the original frozen/live sources and motion artifacts were not changed. `checkpoint/formatter_review.json` records original and checkpoint SHA pairs. Existing reports still describe their original SHA inputs, not these formatted copies. Import order, unused imports, equivalent unlimited-cache decorators and future annotations changed under Ruff. Local face-offset variable names were expanded; the station-count page title gained one space; the connector manufacturer spelling was retained. Two archived authoring functions have explicit complexity annotations to preserve their control flow. Every copied Python file compiles, but the formatted source has not been rerun through the complete native pipeline. Mandatory hook results and pre-existing base violations must be reviewed before commit.
