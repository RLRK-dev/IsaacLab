# p0 提出書 — 測定ハーネス H-4 / H-3.1（pN 経由・再提出）

**re:** `MSG-PN-P0-H4-ROUTING-20260726T151246JST-001`（RETURNED）への再提出。
**送信元:** `w2:p0` IMPL-BUILDER。**提出先:** `w2:pN` T-ROOT-OPS-SUPERVISOR-CODEX。
**作成:** 2026-07-26 15:2x JST。⛔ 本書は測定の報告であり、設計判断・訓練・制御方式変更を含まない。

## 宛先別 message ID（B1 / B2）

| ID | 宛先 | 求めるもの（B3） |
|---|---|---|
| `MSG-P0-P4-H4LAND-20260726-001` | `w2:p4` RS-TECH-LEAD | **landing 可否の判定**と、下記「未達 3 件」を landing 前提に含めるか外すかの **scope 判定** |
| `MSG-P0-PZ-H4VERIFY-20260726-001` | `w2:pZ` IMPL-VERIFIER | 下記 **exact bar 3 本**の独立 verify（clean worktree 再現 + 別手法） |
| `MSG-P0-P11-SWEEP-20260726-001` | `w2:p11` ARM-CONTROL-DESIGN | **掃引方針の指示**（設計判断ゆえ私は決めない）と **doc の stale 数値 1 件**の訂正可否 |

**B2 の確定:** p11 を **第 3 宛先**とする（p4 経由 relay にしない）。理由 = 依頼 2 件はいずれも p11 自身の court（掃引方針の決定・p11 所管 doc の記載）であり、p4 を経由しても p4 は転送するだけで判断材料を持たないため。

## B1 — pin / 再現性

| 項目 | 値 |
|---|---|
| commit（本提出の対象） | `746f049e8357aead0f28c48be1588c9ef2fee005` |
| 直前 commit（H-4 + caveat 分） | `908ac4674576c3b936fe66866254d17691b6cc8e` |
| branch | `rlrk/optE-s2-substrate-swap` |
| report 完全 path | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json` |
| harness 完全 path | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` |
| **測定時 HEAD** | `0025fd32b69038ca61e77db059191afa19765f27`（harness が run 時に自己記録） |
| **測定時 worktree** | **dirty = True / 3250 件**（同上・自己記録） |

report / harness の SHA256 は下記 B5 の再現 command で取得すること（本書に転記すると本書自身の commit 前後で腐るため、`sha256sum` の実行を指定する）。

### ⛔ source-closure — clean 再現できない（最重要）

測定の import closure に **未コミットの 2 file** が入る:

| file | git status | closure 根拠 |
|---|---|---|
| `thread_isaac_lab/envs/route_env_config.py` | **M** | `thread_isaac_lab/envs/newton_route_env.py:103` `import route_env_config as rc` |
| `thread_isaac_lab/scripts/test_newton_clip_routing.py` | **M** | `thread_isaac_lab/envs/newton_skill_env_base.py:75` `from test_newton_clip_routing import (` |
| `newton_route_env.py` / `newton_skill_env_base.py` / `task_config.py` | clean | — |

⇒ **commit `746f049e83` だけからは clean worktree で再現できない。** 差分は計 5 insert / 11 delete と小さく、私が読む記号（`ROBOTIQ_STRIPPED_XML` / `add_ur5e_robotiq` / `skip_equality` / 剛性・減衰・質量系）には触れていないことを grep で確認したが、⚠ **これは「触れていない」の確認であって「結果が同じ」の証明ではない。** 2 file の landing 前後で pZ が再現差を見る可能性がある。

## B3 — 各宛先に求めるもの（exact）

### p4（landing / scope 判定）
1. commit `746f049e83` を land してよいか。
2. **未達 3 件を landing 前提に含めるか外すか**:
   - **H-5**（伝達測定）未実装 — phase を踏む走行が要る
   - **H-5.1**（把持状態の ζ・spec v1.5）未実装 — H-5 と同一走行に乗る
   - **envelope 掃引**未実装 — H-3 / H-4 とも単一姿勢（下記 B4 参照）
3. 上記 source-closure（未コミット 2 file）を landing 条件にどう扱うか。

### pZ（独立 verify する exact bar — この 3 本のみ）
| bar | 値 | 出力先 key |
|---|---|---|
| **B-1 静的たわみ arm0** | `14.593809385` mm（sum of abs） / worst single `8.837687520` mm | `static_tip_droop_H3_1_x_H4.per_arm[0]` |
| **B-2 静的たわみ arm1** | `4.074094093` mm / worst single `2.000042576` mm | `static_tip_droop_H3_1_x_H4.per_arm[1]` |
| **B-3 J-a 最大並進** | arm0 `649.34` / arm1 `224.26` mm/rad | `h4_grasp_jacobian.arms[].J_a_threshold_point_0.220.max_translation_mm_per_rad` |

⚠ `2.000042576` は **2 mm ちょうどではなく偶然の近接**（フル桁を上に示す）。丸めて `2.000` と引用しないこと。
⚠ B-1/B-2 は **2 つの測定の積**（`Dq_i` × J-a）。積そのものの独立再導出を求める。
参考の自己整合: wrist_1 列が `220.000` mm/rad ちょうど = `EE_TO_FINGERTIP` 0.220 m を Jacobian が再現。

### p11（設計判断ゆえ私が決めない 2 件）
1. **掃引方針の指示**。素直な格子は `5 サンプル × 12 腕関節 = 5^12 = 244,140,625` 姿勢で不成立。無作為抽出 / 1 関節ずつ / 最大値の最適化 のいずれか（または別案）を指示されれば実装する。
2. `ARM_CONTROL_CONTROLLER_DRIVEN_ROUTE_DESIGN_V1_ARMCONTROLDESIGN_20260721.md:146` が **「3 縮約が 0.02% 一致」のまま**。正しくは **0.023%**（pZ の N1・私が検算し確認）。同 doc の N2 / N5 併記は既に正しく入っている。doc は p11 所管ゆえ私は編集していない。

## B4 — 定義 artifact / section / pin（未定義は UNDEFINED TERM）

**支配 spec:** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md`
**版 = v1.6** / **content pin = sha256 `22bf42c6908ad07a9e147ed334266a6a5ecd9e513128346680fa01dacf3ee928`** / **着地 commit = `0025fd32b6`**
（版だけでは同定できない。本 spec は 1 日で v1.4 → v1.5 → v1.6 と 3 回改訂されている。）

| 用語 | 定義の在り処 | 状態 |
|---|---|---|
| H-0 / H-1 / H-2 / H-3 / H-4 / H-6 | 上記 spec §1 / §2 / §3 各節 | 実装済 |
| **H-2.1 / H-2.2 / H-2.3** | 同 spec（v1.2 で新設） | 実装済 |
| **H-3.1** | 同 spec `#### H-3.1`（**v1.6・2026-07-26 新設**） | **本 commit で実装** |
| **H-4.1**（J-a / J-b / J-c） | 同 spec `#### H-4.1`（v1.4 新設）の 3 行表 | 実装済 |
| **H-5** | 同 spec `### H-5` | **未実装** |
| **H-5.1** | 同 spec `#### H-5.1`（**v1.5 新設**・pZ の N5 への応答） | **未実装** |
| **J-a** | spec H-4.1 = `ee_pos + 0.220·ẑ_ee`（閾値が測る点）。定数 = `thread_isaac_lab/configs/task_config.py:78` `EE_TO_FINGERTIP = 0.220`（同 `:84` / `:324` に **Franka legacy・re-derive S6** と自己申告） | 実装済 |
| **J-b** | spec H-4.1 = pad body（実接触点）。本実装は **2 pad body の中点** | 実装済 |
| **J-c** | spec H-4.1 = `EE_TO_PINCH_TIP_CLOSED`。定数 = `task_config.py:321` `0.27574726696`（実測コ字爪先） | 実装済 |
| **SSOT index**（stride 14 / EE +5 / pad +9,+13） | ⭐**実コードに実在**: `thread_isaac_lab/envs/newton_route_env.py:149-151`（`ROBOT_BODIES_PER_ARM` = 14 / `_LEFT_EE_BODY` = 5 / `_RIGHT_EE_BODY` = 19）。裏づけ `task_config.py:84`「IK target = wrist_3 (EE body 5)」 | 実装済 |
| **caveat (a)(b)(c)(d)** | ⚠ **artifact でなく pane message 由来**（p4 2026-07-21 21:57 の承認 / pZ verdict の N1-N5）。banked artifact を私は知らない | 実装済・出所を明記 |
| **W-b** | ⛔ **UNDEFINED TERM** — spec §2「envelope は W-b の実 waypoint から定義する」に現れるが、**spec 内に W-b の定義が無い**。私からは同定不能ゆえ envelope は暫定のまま | 未解決 |

## B5 — clean / 一致 の測定時刻・再現 command・rc

すべて 2026-07-26、tree `/home/rlrk/IsaacLab`、`python = /home/rlrk/env_isaaclab7/bin/python`（venv 環境変数は未設定）。
版 = Newton `1.2.1` / mujoco `3.8.1` / warp `1.13.0`（harness が run 時に自己記録）。

```bash
# 1) lint            -> rc 0 (All checks passed)
ruff check --output-format=concise eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py

# 2) 測定 run        -> rc 0（15:2x JST 完了）
CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python \
  /home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py \
  --stage all --world-count 1 --device cuda:0 \
  --out /home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json

# 3) 実行内容 == commit 内容 の確認 -> 出力が空であること（commit 直後に実行・空を確認済）
git status --porcelain -- \
  eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py \
  eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json

# 4) commit scope    -> 2 files のみであること（他 974 を巻き込んでいない）
git show --stat --format="" 746f049e83

# 5) 本提出の SHA256（受領側で取得）
sha256sum eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_{harness.py,h2_report.json}
```

⚠ **「clean」の射程**: 上記 3) が空であることは *この 2 file* が commit と一致することのみを示す。**tree 全体は dirty（3250 件）** であり、上記 source-closure の 2 file を含む。

## B6 — source 変更 / authorization

- **source 変更なし。** 本 commit `746f049e83` と前 commit `908ac46745` はいずれも `eval_runs/…` 配下の 2 file（harness + report）のみ。`thread_isaac_lab/` 配下は 1 行も変更していない（`git show --stat` で検証可）。
- **測定 authorization の出所** ⚠ いずれも **pane message であり banked artifact ではない**:
  - 実装 GO = p4 2026-07-21 15:49（測定ハーネス spec v1 の実装指示）
  - run 認可 = p4 2026-07-21 20:29:19（`--stage h0` run 可）
  - H-2 結線認可 = p4 2026-07-21 21:27:42（measurement HOLD 解除）
  - caveat (a)-(d) 承認 + H-4 優先 = p4 2026-07-21 21:57:05
- ⛔ 上記を artifact 化した record を私は持たない。artifact 接地が要るなら p4 に発行を依頼されたい。

## 未達（landing 判断に要る・黙って落としていない）

1. **H-5**（伝達測定）— 未実装。
2. **H-5.1**（把持状態の ζ・v1.5）— 未実装。H-5 と同一走行。
3. **envelope 掃引** — H-3 / H-4 とも**単一姿勢**。report の `h3_torque_budget.pose_coverage` と `h4_grasp_jacobian.pose_coverage` に `envelope_max_implemented: false` として明記済。**数値は上界でなく標本**。
