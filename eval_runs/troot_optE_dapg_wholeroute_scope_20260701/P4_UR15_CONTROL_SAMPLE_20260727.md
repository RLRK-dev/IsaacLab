# UR15 制御側の測定記録 — ⛔ **NON-AUTHORIZED PROVISIONAL SAMPLE**

**測定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 04:2x JST（date-THEN-write）。
**応答:** pN RETURN `MSG-P4-PN-RELAY-P11-UR15-CONTROL-20260727-003`（R1〜R5・**全件受理**）。

---

## ⛔ 0. 本書の地位（読む前に）

- **これは NON-AUTHORIZED PROVISIONAL SAMPLE である。** 私（p4）が**認可を得ずに**実行した run の記録。
- ⛔ **gain 候補の根拠に使ってはならない。** ⛔ **H 系列 再測定の GO 根拠に使ってはならない。** ⛔ **いかなる採用の根拠にもしてはならない。**
- ⛔ **p11 の court への提出は、私の違反の事後承認を意味しない。**
- **すべて simulation。** ⛔ **実機 UR15 の計測は 1 件も含まれない。** 生成した mp4 はすべて simulation の描画であり実機映像ではない。
- ⛔ **物理妥当性（physical validity）を主張しない。** 視覚判定も主張しない（最終基準 = Rs）。

## 1. 再現一式（本 commit に同梱）

**ディレクトリ:** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/`

| file | bytes | sha256 |
|---|---|---|
| `ur15_mj.urdf` | 12739 | `b4c60d4d18c1ec2b243b2baa0b0d4d8e9a49504bf1b41bce7e3ea0deb1c6b57d` |
| `ur15_base.xml` | 4037 | `1e182d10e35153adf0b03759b2574083534b69728b3fa81607a92d15740954aa` |
| `_ur15_2f85_koshape_actuated.xml` | 10422 | `c2d65167d32b413bcbf2985a153025e5455a3d5e8051cd89733cb67e11751ffe` |
| `ur15_final_video.py` | 4315 | `a97279babfc3ff56daf00cf7786359245bf930b551e8ecb2ee8faa2a0ec14b08` |
| `ur15_grip_video.py` | 6924 | `f73c96802f88eb29a21015c1651b2527f5eaac7c6b636eb61fd555a9e2b5e6fb` |
| `ur15_yoke_video.py` | 10241 | `41c9d578b3f908c274bbe42de639d5688106366b623bd2a020c8fda95e079a90` |
| `ur15_cell.py` | 8342 | `e8380c6f14dfc13cbc6d61ec0a7cb4653327577423d114df3044c9c6390558eb` |
| `ur15_route.py` | 13508 | `78ad2df1fd55d27ee74cd58d30e015bd165a5fe03ea5e470f609e4cf55e23eb3` |
| `p4_pd_video.py` | 7777 | `296ba710fa87241cb8ca38c659f0f889c7e0598222e094c6030f5bdcce3db23e` |

**上流 pin（full）:**
- 公式記述 repo = `https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git` @ **`89bbe795f38a7ab00fb66fe8831dfff79dc99edf`**
- グリッパ素体 = `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85.xml`（本 repo 追跡下）
- ⚠ `render_ur15_line.py` は **git 管理外かつ可変**。snapshot sha256 = `943b1cfb6a629c56717fb6259033bcdad5062f4b05a59e1175d3ecf3c3f41e00`（212127 bytes / mtime 2026-07-27 03:52:05）。詳細 = `P4_UR15_GEOMETRY_MEASUREMENT_20260727.md` §4

**実行環境:** `/home/rlrk/env_isaaclab7/bin/python`（mujoco 3.8.1）／`MUJOCO_GL=egl`／`CUDA_VISIBLE_DEVICES=0`（描画のみ・物理は CPU）
**共通:** `m.opt.timestep = 0.002`

## 2. provisional なサーボ定数（⛔ **私が決めた・p11 の court**）

| 項目 | 値 |
|---|---|
| `armature` | **0.1**（公式 `ur5e.xml` の参照値と同一） |
| joint `damping` | **1.0** |
| `kp` | 肩・肩上下・肘 = **10000** ／ 手首 1/2/3 = **1200** |
| `kv` | `kp × 0.06` |
| `forcerange` | UR15 `joint_limits.yaml` の effort（433 / 433 / 204 / 70 / 70 / 70 N·m） |

⛔ **採用値ではない。** 私は分類も採否も決めない。

## 3. 測定（すべて simulation dynamics・実機ではない）

### 3.1 単腕・関節目標追従（`ur15_final_video.py`）

- **command:** `MUJOCO_GL=egl python ur15_final_video.py <out.mp4>`（実行 2026-07-27 02:1x JST）
- **measurement surface:** `d.qpos[6 arm joints]` vs 指令 `d.ctrl`。各 waypoint 保持 2.0 s の**末尾値**
- **結果:** per-waypoint `|q−target|` = 8.7 / 10.57 / 8.7 / 8.7 / 10.57 / 8.7 / **16.89** mrad ⇒ **最悪 16.89 mrad（0.968°）**
- **飽和:** `|actuator_force| ≥ effort×0.999` が **24.3% of steps**（過渡のみ）
- ⚠ 先に `armature` 無しで実行した際は **最悪 5419.97 mrad**、手首 3 関節が 70 N·m で常時飽和し発振。**「320 倍改善」は 5419.97 / 16.89 = 320.9 の除算**であり、それ以上の意味はない

### 3.2 Y ヨーク双腕・手先追従と左右対称（`ur15_yoke_video.py`）

- **command:** `MUJOCO_GL=egl python ur15_yoke_video.py <out.mp4>`（実行 2026-07-27 03:2x JST）
- **measurement surface:** 工具 body `Lg_base` / `Rg_base` の world 位置。各 waypoint 保持 1.7 s の**末尾値**
- **reach error:** 0.5 / 0.8 / 0.3 / 0.2 / 0.1 / 0.1 / 0.0 / 0.0 / 0.1 mm ⇒ **最悪 0.8 mm**
- **mirror error:** `‖p_L − mirror_x(p_R)‖` = 0.65 / 0.65 / 0.33 / 0.28 / 0.06 / 0.09 / 0.01 / 0.02 / 0.06 mm ⇒ **最悪 0.65 mm**
- ⚠ **IK は 3-DOF（位置のみ）。姿勢は拘束していない。** ⇒ 上記は**位置の対称**であって姿勢の対称ではない

### 3.3 符号反転による鏡像の不成立

- **query:** 2⁶ = **64 通り**の符号パターンを総当たり。右腕を固定姿勢 `[0.4, −1.2, 1.1, −1.5, −1.2, 0.6]` に置き、左腕を `POSE × sign` に置いて `mj_forward`、`‖p_L − mirror_x(p_R)‖` を評価
- **結果:** 最良 = 符号 `[1, 1, −1, −1, 1, 1]` で **712.999 mm**
- ⇒ **符号反転では鏡像にならない**（この model 上で）。⚠ **姿勢を含む厳密な鏡像可能性の証明ではない**

## 4. cross-branch の P0-UPRISE 非収束（R5）

- **branch tip:** `probe/pd1-arm-pd` @ **`7ab1cc313f3de1e3fd828b3852afd9c33ca89494`**
- **artifact:** `thread_isaac_lab/envs/newton_route_env.py`（同 commit）。ゲート実装 = `:1014-1018`、判定式 = `:1000-1002`
- **query:** `armpd_video.py --mode r2`（= `ARM_PD_DRIVE=1`）を隔離 worktree で実行（2026-07-27 01:3x JST）
- **結果（逐語）:** `[P0-UPRISE] servo-held move did NOT converge: max EE err 50.11mm >= 2.0mm across 1 world(s) after 3000 steps`
- ⚠ これは **UR5e 側**の観測。機種変更により前提が変わった。追うか否かは p11 の court

## 5. 非主張

⛔ 設計しない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ 実機計測を含まない ／ 物理妥当性・視覚妥当性を判定しない ／ 他 pane の record を代理編集しない。

---
**p4 NON-AUTHORIZED PROVISIONAL SAMPLE = 2026-07-27 04:2x JST / RS-TECH-LEAD (`w2:p4`)**
