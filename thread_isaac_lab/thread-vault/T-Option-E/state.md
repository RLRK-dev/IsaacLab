---
node_id: T-Option-E
node_name: "Option-E substrate re-base (env7 MuJoCo)"
goal: "Re-base the THREAD substrate onto env7 (Newton 1.2.1 / MuJoCo 3.8.1 SolverMuJoCo, UR5e x2 + Robotiq 2F-85)."
goal_verification: |
  COMPLETE. Option-E re-base onto env7 done (R1 IK-motion byte-identical to env6 baseline, R2 K2, S8 cable surf_min 0.7999 PASS). Substrate foundation established. No product claim.
status: COMPLETE
parent_node: T-L1X-Substrate-Realism
children_nodes: []
dependencies:
  precedent: []
  blocker: []
created: 2026-06-23T21:38:08+09:00
last_updated: 2026-06-23T21:38:08+09:00
spec_version: LTM-1 v1.1
---

# Option-E substrate re-base (env7 MuJoCo) — COMPLETE

env7 / Newton 1.2.1 track (CLAUDE.md Newton VBD section). Re-base verified 2026-06-16.

*NEST live-spine re-seed (Stage-A, 2026-06-23). Minimal-schema node; primary record = `thread-vault/log.md` + the cited eval_runs / design docs. View: `docs/nest-tracker/` (regenerated from this state.md via `scripts/build_nest_snapshot.py`).*

## ⚠ 2026-07-27 注記 — robot は UR15 へ変更（本 goal は書き換えない）

本 node の goal に残る **UR5e x2** は、**2026-06-23 の完了時点で実際に re-base した対象**の記録である。
robot は 2026-07-27 の Rs 裁定で **UR15 ×2 + Robotiq 2F-85** に変更された（接地 = `07-Design/00-DESIGN-STATUS-LEDGER.md` 統治ブロック）。
⇒ **完了記録を書き換えると「その時 何を re-base したか」が偽になる**ため goal は不変とし、本注記で現在との差分を示す。
現行の robot 定義は `04-Specs/RS71-System-Spec-SSOT.md` §0（UR15 ×2）を見ること。
