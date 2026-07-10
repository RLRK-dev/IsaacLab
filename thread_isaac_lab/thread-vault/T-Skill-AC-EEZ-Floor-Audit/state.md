---
node_id: T-Skill-AC-EEZ-Floor-Audit
node_name: "AC env EE-Z floor 監査 (EE_Z_FLOOR_KO 同 class 潜在欠陥チェック)"
goal: "AC env (thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py) に、route-executor comp3 G1 で発覚した env-core EE_Z_FLOOR_KO clip 潜在欠陥 (G1 run-1 NUMERIC_NOGO 根因、lane-aware floor fix `65b5b9dd21` で解消) と同 class の EE-Z floor clip 欠陥が無いかを監査し、有れば同 class の lane-aware 修正を提案 (修正実装は別承認)、無ければ CLEAN と bank する。"
goal_verification: |
  DoD: ① AC env の EE-Z floor / z-clip 系 code path を全数列挙 (grep + code read、absence-claim は全 build path 検索 [[feedback-absence-claims-grep-all-build-paths]]) ② env-core EE_Z_FLOOR_KO 欠陥 mechanism (route-executor node session_history 07-10 13:36 entry + `65b5b9dd21` diff) との照合表 ③ verdict = CLEAN or DEFECT-FOUND (+ 修正提案、実装は別承認)。
status: PENDING
parent_node: T-Skill-AC
children_nodes: []
dependencies:
  precedent:
    - "route-executor comp3 G1 根因確定 = EE_Z_FLOOR_KO clip (env-core 潜在欠陥) + lane-aware floor fix `65b5b9dd21` (2026-07-10 13:36-14:1x、node T-ROOT-optE-route-dapg-C1C2-P2-routeexec session_history)"
    - "Rs 裁定 2026-07-10 19:2x #4「AC env 床監査 = 別タスク登録」(Rs 承認済; 小監査、手隙時実行; bank = routeexec node/LEDGER)"
  blocker: []
created: 2026-07-10T23:36:00+09:00
last_updated: 2026-07-10T23:36:00+09:00
spec_version: LTM-1 v1.1
session_history:
  - "2026-07-10 23:36 p6 (PLAN-KEEPER, w2:p6): node 登録 (計画登録のみ、%12 dispatch 23:33 / Rs 裁定 19:2x #4 提示)。実行 = 手隙時、担当未 bind。着手時は §運用2 [DEFINE] から。"
---

## goal / means / status
- **goal:** AC env の EE-Z floor 系に env-core EE_Z_FLOOR_KO 同 class の潜在欠陥が無いか監査 (小監査、no-GPU code read 主体)。
- **means:** grep + code read で floor/z-clip path 全数列挙 → env-core 欠陥 mechanism との照合 → verdict bank。修正が必要な場合は提案のみ (実装 = 別承認)。
- **status:** PENDING (Rs 承認済・手隙時実行、担当未 bind)。
