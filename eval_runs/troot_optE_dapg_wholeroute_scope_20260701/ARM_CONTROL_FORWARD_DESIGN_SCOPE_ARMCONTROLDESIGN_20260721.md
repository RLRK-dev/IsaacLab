# 前向き腕制御設計 — scope + 骨子 v0.1（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** SCOPE v0.1 — **proposal**（landing = p4 経由・実装認可でない）。
**設計対象（Rs 裁定で確定・p4 relay 2026-07-21 13:18 JST）:**
- **A = substrate: env7-mujoco に確定**（移管費用・B0/B1 影響は私の court 外）
- **B = 振付: 再工事 W-b**。⭐**摂動耐性 leg（≥ trainer residual / DR scale）を必須要件として内蔵**（`§13 R-3` 付帯・「1 mrad で flip する振付を再 bank しない」）

⛔ 本書は **scope + 骨子**。実装しない・走らせない・bar を凍結しない。**design-gate（`/force-design` 等）+ `/pre-check` は未実施** — p0 実装前に必ず通す（p4 guardrail）。

---

## 0. 何が確定し、何が私の仕事として残ったか

| | 状態 |
|---|---|
| 任務（裁定 A `LEDGER:36`） | 43 step の動作を**腕とコントローラで物理的に実現**。DoD = **腕・ハンド・フィンガを描画した動画**。robot = UR5e×2 + Robotiq 2F-85 |
| substrate | ✅ **env7-mujoco 確定**（Newton 1.2.1 / `SolverMuJoCo`） |
| 駆動 API の可用性 | ✅ **実測済・阻害なし**（`joint_target_mode` / `joint_target_ke,kd` / `joint_effort_limit` / equality / mimic = `SolverMuJoCo` support。`…GROUNDING_SUBSTRATE_CAPABILITY…20260721.md` §3） |
| 振付 | ✅ **再工事 W-b 確定**（+ 摂動耐性 leg 必須） |
| 実行 driver（43 step を env7 env-core に載せる実体） | ⛔ **私の court 外**（DDR #31 = pX+pS）。⚠ **私の制御設計だけでは 43 step は走らない** |
| kinematic 例外 | clip-retention pin のみ（裁定 B）。⛔腕関節角 直接書込 / 指の kinematic close / `update_kinematic_bodies` / weld・attachment は不許可 |

---

## 1. ⭐ 本設計の中心問題 — 振付と制御器の相互依存（W-b 確定で顕在化）

**銀行済の事実から出る構造的な問題**（新規測定でなく既存 banked 材料の帰結）:

1. FF path は **recorded `arm_q` を毎 frame の指令として直結**する（charter §2「FF path: `ctrl := jq_ff[frame]`」「recorded `arm_q` 直結は FF path のみ」）。
2. その recorded 軌道 = **kinematic で実現された状態の記録**ゆえ、移行時に**再記録必須**（charter §7-2 逐語「demos は kinematic 実現状態の記録ゆえ S-2 で再記録必須」）。
3. 裁定 B により、**再記録を kinematic 再生で作ることはできない**（腕関節角の直接書込 = 不許可）。
4. さらに L-P0 が「清潔基盤では banked 振付の連鎖が **kinematic でも**成立しない」を evidence 級で確定（§13 R-3）⇒ **旧振付をそのまま再生する道は塞がっている**。

⇒ **「制御器は振付（指令ストリーム）を要求し、振付は制御器がないと物理的に作れない」** という循環。W-b が確定した以上、**この循環をどう断つかが本設計の第一問**である。

### 1.1 断ち方の候補（⚠ 選定は次段・design-gate 対象）

| 案 | 内容 | 効き | 主な risk |
|---|---|---|---|
| **W-1** 指令空間で振付を作る | 振付を「記録された **状態**」でなく「**IK が生成する目標軌道**」として再定義。PD が追従した結果を記録＝ demo とする | charter M-3（command-space 原則）と**同型**・kinematic を一切使わない・§0#3 の「IK が target 源」を保存 | 追従誤差ぶん、実現軌道が設計軌道からずれる（= lag-law bar が支配的な受入条件になる） |
| **W-2** 旧 recorded 軌道を **目標**として再利用 | 旧 demo の `arm_q` を状態でなく**目標**として食わせ、PD に追従させる | 実装が最小・既存資産を活かす | ⛔ L-P0 が「旧振付は清潔基盤で連鎖しない」を示済 ⇒ **そのままでは成立しない公算が高い**。摂動耐性 leg も満たさない |
| **W-3** 最適化・探索で振付を生成 | 軌道最適化 / RL で clean 基盤上の実現可能軌道を求める | 摂動耐性を目的関数に入れられる | 費用大・DDR #31（実行 driver）と依存が絡む |

**現時点の私の傾き = W-1**（M-3 と整合し、kinematic を経由せず、§0#3 を保存する唯一の案）。⚠ **裁定はしない** — design-gate + `/pre-check` を経て確定する。

---

## 2. banked 骨格の再批准（M-1〜M-6・env7-mujoco 下）

| 項目 | env7-mujoco 下の判定 | 根拠 |
|---|---|---|
| **M-1** imported 12 本 無効化 + proto 配線（**B1 strip-at-import = PRIMARY**） | ✅ **維持**。`joint_target_mode=POSITION` + ke/kd + effort が `SolverMuJoCo` で support ⇒ 機構が成立 | 実測（capability doc §3）+ charter v1.4-③ |
| **M-2** ctrl ストリーム置換（`phys_jqd=0` 零化は廃止） | ✅ **維持**。裁定 B 下でも「realization を物理化する」方向は不変 | charter §1 |
| **M-3** command-space 原則（realized から再 seed しない） | ✅ **維持・重要度上昇**。§1 の W-1 案の土台 | charter §1 |
| **M-4** teleport⇒target-sync 不変条件 | ✅ 維持（分類 B の reset/restore に arm ctrl 同期を付す） | charter §1 / §4 |
| **M-5** 指令不連続の ramp-in | ✅ 維持 | charter §1 |
| **M-6** tracking-divergence guard（持続条件つき・非 reward 結合） | ✅ 維持。⚠ bar 値は **clean 基盤実測から導出して run 前凍結**（未凍結） | charter §1 / §3.2 |
| **§2** per-physics-frame ctrl（採択 A） | ✅ 維持 | charter §2 |
| **§4** 16 sites 分類（A=11 migrate / B=5+1） | 🔶 **再点検要** — 裁定 B で pin 系 class が動き得る（`LEDGER:35` 逐語「census 35 の disposition に波及」）。⚠ **census 35 の数は動かさない**（設計軸で class のみ） | charter §4 + LEDGER |

### 2.1 §3 gains / bar — P-D1 実測を折り込んだ現在地

- 力 = **FEASIBLE**（飽和 0.0% / worst 25.1 < 28 N·m）⇒ effort cap ±150 / ±28 N·m は**実機 spec のまま維持**。⛔**引上げ禁止**（fidelity 非保守方向・charter §9）。
- 速度帯域 = vendor gains では不足。**lever = kd/ke 比**、`T_lag = kd/ke` 実測 **0.2 s 一様**。
- 授権済 re-probe（未起動・prereg v1.3 凍結 `b3ddfbab1c`）= **C-1 `kd×0.25`**（T_lag 0.05 s）/ **C-2 `kd×0.25 + ke×2`**（T_lag 0.025 s）。
  ⇒ **W-b 確定により再走の意味が変わった**: 旧振付への追従性能でなく、**新振付の設計 envelope（どの速度域なら bar 内に収まるか）を決める測定**になる。⚠ prereg の再凍結が要る。
- **bar 構造 = 一律 transient 5 mrad を捨て、§13 R-2 の 5 本立てへ**:
  (i) 静的/settle ≤2 mrad（維持）/ (ii) **lag-law bar `T_lag = err/ω ≤ T_LAG_BAR`**（速度非依存の realization 品質量）/ (iii) phase 端点到達 ≤5 mrad / (iv) no-ringing（overshoot bar + M-6 持続 0）/ (v) M-6 divergence guard。
  ⛔ **凍結は run 前**（結果を見て bar を後決めしない — charter §3.2）。

### 2.2 ⭐ 追加要件（Rs 裁定 B 由来・新規）

**R-ROBUST（必須）**: 新振付は **摂動耐性 leg** を満たすこと。摂動スケール = **trainer residual / DR scale 以上**。
- 由来 = §13 R-3 付帯「1 mrad 級で連鎖が flip する振付は DR/residual（15mm 級）/noise 下の訓練に耐えない」。
- ⇒ **受入条件に組み込む**（振付が bar を満たすだけでなく、摂動下でも述語連鎖が生き残ることを要求）。
- ⚠ 具体の摂動量・試験形は **未定**（trainer residual / DR scale の実値を測って決める。次段）。

---

## 3. 指（Robotiq 2F-85）側 — 未解決として明示

裁定 A の DoD は **フィンガを描画した動画**、Rs ② は「kinematic で実現できていたフィンガ動作を**コントローラで実現する**」。

- **現在地**: 指令経路（`set_gripper_target` → `joint_target_pos`）は在るが、**忠実 actuation は未実装**（MJCF `<actuator>` = parse 時 skip・4-bar `<equality>` = drop・`task_config.py:336-337` 逐語 deferred）。⛔「指が閉じる」を根拠にしない（`LEDGER:37`）。
- **lead（結論でない）**: env7 `SolverMuJoCo` は **equality / mimic（REVOLUTE・PRISMATIC）を support**、`parse_mjcf` の `skip_equality_constraints` 既定 = False。env6 の `_init_tendons` は env7 に無く tendon 経路は再構成済。
  ⇒ **「substrate が禁じている」わけではない**。⛔ ただし 2f85 を equality/mimic 付きで build して忠実 close が出るかは **build 実測前**。
- ⚠ **gripper 形状（コ字）は human-LOCKED**（§0#4）。形を変える案が出たら **STOP → p4 → Rs**。

---

## 4. 私が次にやること（順序）

1. **§4 の 16 sites 分類を裁定 B 下で再点検**（pin 系 class・census 35 は不変）。
2. **W-1/W-2/W-3 の選定** — `/force-design` + `/pre-check` を通す。⚠ ここが本設計の分岐点。
3. **bar の最終形**（§2.1 の 5 本立て）+ **R-ROBUST の具体化**（摂動量を実測から）。
4. p4 経由で Rs 供覧 → design-gate → `/pre-check` → **その後に** p0 実装。

## 5. 非主張 / gate 状態

- **裁定していない**: W-1/W-2/W-3・bar 値・class の再割当・摂動量。
- **未実施の gate**: `/force-design`・`/pre-check`・L3 chain・CC Debate。⇒ **p0 は本書では動けない**（実装認可でない）。
- 43 step が env7 上で走ることを主張していない（実行 driver = DDR #31・私の court 外）。
- 物理妥当性を判定していない（最終基準 = Rs の動画 human-GT）。

## 6. L 自己申告

**L1**（新規 file 1 本・scope/骨子・コード 0・landing なし・数値凍結なし）。
⚠ 本書が扱う内容（gains / 制御方式 / 成功条件に接する）は**確定時に L3 + design-gate**へ上がる。本書は its scope 宣言に留め、**確定を含めていない**。
commit = explicit pathspec + `--no-verify`（DDR #35）。
