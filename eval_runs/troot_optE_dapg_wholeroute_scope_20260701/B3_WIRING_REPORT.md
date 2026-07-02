# ③ B2 cable-XY-offset wiring — report (design + byte-identity proof + wire-then-validate)

**test_newton_clip_routing.py** (Rs-LOCKED route file) に additive `cable_xy_offset=None` を配線。%12 ③ 授権範囲: additive wiring + **proof 1 run (offset UNSET, cuda:0) byte-identity**。0-commit (→ %12 diff 縮退 review → commit 判断)。**2026-07-03.**

## 設計 (rigid cable-XY translation; None → strictly legacy)

- **X follow = 自動 (無改修):** `settled_grasp_x = mean(measured cable_x)` (`test:6762`) → offset した cable は offset X に settle → grasp_x が追従。
- **Y follow = 明示 (`grasp_dy`):** grasp target Y = `WIDE_*_Y + grasp_dy`、`grasp_dy = scene_info["cable_xy_offset"][1]`。**unset → 0.0 → `WIDE_*_Y + 0.0` = float additive identity = byte-identical**。cable_y は測定しない (grasp は cable-center でなく特定 Y=0.15 の segment を掴むため、measured-center は不可 → explicit offset が正)。
- **cable placement:** `cable_start = (GRASP_X + dx, cable_y_start + dy, …)`、`_cxo = cable_xy_offset or (0,0)`。
- **per-run 供給:** call-site が env `CABLE_XY_OFFSET="dx,dy"[m]` を読む (unset → None → legacy)。explicit per-run、in-harness RNG 無 (§5.1 準拠)。

## diff (6 hunk, 全て additive / None-identity)

| hunk | 変更 | None 時 |
|---|---|---|
| build_scene sig (:1032) | `+cable_xy_offset=None` | 既存 call は default None |
| cable_start (:1365) | `+_cxo` offset | `+0.0` = identity |
| scene_info (:1666) | `+"cable_xy_offset"` key | `(0.0,0.0)` |
| do_p1_grasp (:2211,:2226,:2246) | `+grasp_dy` + approach/descend Y | `+0.0` = identity |
| do_p2_lift (:2477,:2494) | `+grasp_dy` + lift Y | `+0.0` = identity |
| call-site (:6587) | `+cable_xy_offset` env read | env unset → None |

**制約遵守:** ANTI-REVERT markers **4/4 不触** (my hunks は build_scene ~1032-1666 + grasp ~2211-2494 + call-site ~6587、markers は verdict/re-grasp ~4385-4500 = 無干渉、grep 確認)。Tier-0 prohibited.md: control API / kinematic-trick 無 (cable は physical placement、grasp follow は ik_move_both = DiffIK。write_joint_* / teleport 無、diff grep empty)。L-TRIAGE = L3 (locked route file path-match)。層2/層5 post = %12。

## byte-identity proof (offset UNSET, edited file, cuda:0)

**run:** run_canonical.sh と同 env (S6_GRASP_ROUTE=1 … CLIP2_X=0.40 CLIP2_Y=0.075)、**CABLE_XY_OFFSET UNSET** → None → legacy path。MUJOCO_GL=egl headless。baseline = `canonical_run_records/integrated_route/run_canonical/route_c2_pin.json` (committed-route 産、pre-edit)。

**RESULT: ✅ BYTE-IDENTICAL.** `diff -q` clean + **sha256 一致** (`e01ac1fad2ff415538a53c9786a9ed6060cb189b99a4ab6fc5fdda619717df6a` == baseline)。route_c2_pin.json 12 key 0 mismatch、regrasp verdict = `SUCCESS_R_GRIP_L_CAGE_AT_88` (canonical SUCCESS 再現)、finite/qvel_ok=True。run exit=0 (full C1→C2 route 完走)。

この proof は同時に「follow 配線は None 時 dead path」を実証する (offset unset で新 code path が全て identity → 全 fingerprint bit 一致)。

## ⚠ wire-then-validate — offset≠0 follow は ③ で未検証 (loud caveat)

③ proof は **offset UNSET のみ** (= byte-identity + dead-path)。offset≠0 の grasp follow (X-measured + Y-explicit) の物理的正しさは ③ で exercise されない → **未検証 (wire-then-validate)**。加えて approach **seed joints (`test:3839` seed_l/seed_r) は固定 warm-start のまま** (offset target への IK 収束に依存; ±20mm が収束するかは未検証)。検証 leg を事前登録 (%12):

- **(i) B2 pre-C1 reach screen:** harness の**実 target-derivation code path** (grasp_x=settled + `WIDE_*_Y+grasp_dy`) を consume して offset 別 target 算術を **IK-only 検証** (screen spec に 1 行: 「screen は build_scene(cable_xy_offset) 経由の実 grasp target を使う」)。
- **(ii) B2 収録 #1 = half-edge (+10,0) 先行:** grasp-close fail → **即 STOP early-abort** 順序 (nominal-fixed seed が offset cable を外す最悪ケースを最小 offset で先に検出、12/13 無駄収録を回避)。

## B2 usage

`CABLE_XY_OFFSET="0.01,0.0"` 等を per-run env で供給 → build_scene が cable を offset + grasp が follow。§5.3 scripted-SUCCESS filter が非収束 offset を除外。
