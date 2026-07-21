# 前向き腕制御設計 v0.2 — 骨格再批准 / bar 構造 / R-ROBUST / W-1（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** DESIGN v0.2 — **proposal**（landing = p4）。v0.1 = `bec159aec5` を継承・supersede しない（v0.1 = scope、本書 = 中身）。
**設計対象（確定）:** substrate = **env7-mujoco**（Rs 裁定 A）/ 振付 = **再工事 W-b**（Rs 裁定 B）/ robot = UR5e×2 + Robotiq 2F-85。
**原則:** **P-1 = 物理計算の結果を捨てない**（Rs 逐語「すてるなよ」・v0.1 §0.5）。
⛔⛔ **`/pre-check` VERDICT = BLOCK（2026-07-21）。本書 v0.2 は設計前提として使えない。** 詳細 = `ARM_CONTROL_PRECHECK_V02_RESULT_ARMCONTROLDESIGN_20260721.md`。
⛔ **実装認可でない。** `/force-design`（gains 確定時）は **未実施**。
**BLOCK の芯（3 件・私が独立に原文確認済）**: ①§2.3 の一次系近似は**高慣性関節で成立しない**（実測 0.512 rad は **wrist_2** = 低慣性 size1 の値・`…PD1_RESULT…:35` 逐語「worst joint = wrist_2」。肩に一般化したのは **同じ定数を別の測定面へ持ち込む誤り**）②**重力が入っている**（`test_newton_clip_routing.py:125` `GRAVITY = -9.81`）ため純 PD には恒久ドループが残り bar (i)(iii) が広い範囲で到達不能 ③飽和余裕の読み違い（下記 §2 訂正）。

---

## 1. 骨格 M-1〜M-6 の再批准（env7-mujoco + 裁定 A/B + P-1 下）

| 機構 | 判定 | 根拠 / 変更点 |
|---|---|---|
| **M-1** imported 12 本を strip（B1）+ proto 配線（`joint_target_mode=POSITION` + ke/kd + effort） | ✅ **維持** | env7 `SolverMuJoCo` が 3 者とも support（実測・`solvers.py:259/:297` + `solver_mujoco.py:4304/:4306`）。⭐**P-1 抵触なし** — strip は build 時のモデル構成であって物理結果の破棄ではない |
| **M-2** ctrl ストリーム置換（`phys_jqd=0` 零化は廃止） | ✅ **維持・P-1 が補強** | P-1 の主旨そのもの（状態を書かず target を与える） |
| **M-3** command-space（realized q から再 seed しない） | ✅ **維持・W-1 の土台** | ⚠ §4.2 で generic な「漸進目標」recipe と**衝突**するため解決を明記 |
| **M-4** teleport ⇒ target-sync | ✅ **維持** | 分類 B（reset/init）限定。**P-1 の適用外**（reset には捨てる物理結果が無い・v0.1 §0.5） |
| **M-5** ramp-in（指令不連続の漸進化） | ✅ **維持・重要度上昇** | W-1 では phase 境界が設計物になるため、不連続は**設計で消せる**（§4.3） |
| **M-6** tracking-divergence guard（持続 N_DIV 条件・非 reward 結合） | ✅ **維持** | bar 値は**未凍結**（C-1/C-2 実測後）。§2 (v) |

**§2 target-setting = per-physics-frame ctrl（採択 A）**: ✅ 維持。frame = **480 Hz**（`newton_skill_env_base.py:93` `DT = 1.0/480.0`）、RL substeps = 4（`:95`）。
**§4 16 sites 分類（A=11 migrate / B=5+1）**: 🔶 **再点検を継続**（裁定 B で pin 系 class が動き得る。⛔census 35 の数は動かさない）。

⚠ **M-3 の精緻化（W-b 由来）**: v1.x は「recorded/IK 軌道 = authoritative」と書いたが、W-b で recorded が消えるため **authoritative = IK が生成する目標軌道**に一本化する（§4）。矛盾でなく主語の確定。

---

## 2. ⭐ bar 構造（§13 R-2 の 5 本立て）— 一律 transient bar を捨てる理由の定量

### 2.1 なぜ一律 5 mrad が誤りだったか（実測からの逆算）

banked 実測: **`T_lag = kd/ke` が 400/2000 = 100/500 = 0.2 s で一様**、lag 則 `err ≈ T_lag·ω`（§13 R-1）。
⇒ 一律 `err ≤ 5 mrad` は、実質 **`ω ≤ bar/T_lag` という指令速度の bar** になる:

| gains | T_lag | `ω_max`（err ≤ 5 mrad） | 記録軌道 peak `ω`（逆算 0.512/0.2） | 比 |
|---|---|---|---|---|
| vendor v0 | 0.2 s | **0.025 rad/s** | 2.56 rad/s | **102×** |
| C-1（kd×0.25） | 0.05 s | 0.100 rad/s | 〃 | 25.6× |
| C-2（kd×0.25・ke×2） | 0.025 s | 0.200 rad/s | 〃 | 12.8× |

⇒ **どの gain でも一律 bar は満たせない。** これは制御器の欠陥ではなく **bar が smooth-lag class を誤モデル化していた**（§13 R-2 の指摘の定量形）。
⛔ **だから bar を緩めるのではない** — **精度を要求する場所を、task が実際に精度を消費する点に置き直す**。

### 2.2 採る 5 本立て（構造を凍結・値は測定後）

| # | bar | 形 | 値 |
|---|---|---|---|
| (i) | **静的 / settle 窓** | `|q − ctrl| ≤ 2 mrad` | **2 mrad**（v1.x 実績値・維持） |
| (ii) | **lag 則 bar** | `T_lag = err/ω ≤ T_LAG_BAR`（速度非依存の実現品質量） | ⏸ **C-1/C-2 実測後に凍結** |
| (iii) | **phase 端点到達** | 各 phase 終端で `|q − ctrl| ≤ 5 mrad` | **5 mrad**（task が精度を消費する点） |
| (iv) | **no-ringing** | overshoot bar + M-6 持続 0 | ⏸ 実測後 |
| (v) | **M-6 divergence guard** | per-joint `|q − ctrl| > bar` が N_DIV=48 frame 持続で発火（physics-fault・⛔reward/timeouts 非結合） | ⏸ bar 実測後 |

### 2.3 ⭐ 結合量 = 整定時間（本設計の律速）

(ii)+(iii) を採ると、律速は **phase 端点での整定時間**になる。指令が止まった後、誤差は時定数 `T_lag` で減衰する〔**仮説 tag**: 一次系近似。lag 則は実測だが減衰形は未実測 — (iv) ringing leg が反証機会〕:

> `t_settle = T_lag · ln(err₀ / bar)`,  `err₀ = T_lag · ω`

| gains | peak 時 `err₀` | 5 mrad へ整定 |
|---|---|---|
| vendor 0.2 s | 0.512 rad | **0.93 s** |
| C-1 0.05 s | 0.128 rad | **0.16 s** |
| C-2 0.025 s | 0.064 rad | **0.064 s** |

⭐ **設計上の含意（本書の中心結論）**: 整定時間は **`T_lag` に線形・速度には対数でしか依存しない**。
⇒ **`T_lag` を下げる（C-1/C-2）のが高レバレッジ。振付を遅くするのは低レバレッジ**（速度を 1/10 にしても整定は `ln` 分しか縮まない）。
⇒ **C-1/C-2 の実走は「あれば良い」ではなく、振付設計の前提**。（prereg v1.4 `3793258e7c` が測る）

⛔ **effort cap は上げない**（±150/±28 N·m = 実機 spec、`ur5e.xml:10-11,19` 実測 `forcerange="-150 150"` / `"-28 28"`）。
⚠⚠ **訂正（pre-check ISSUE 3）**: 私は banked の「飽和 0.0% / worst 25.1 < 28 N·m」を**余裕がある**ように書いたが、**25.1/28 = cap の 89.6% を消費**しており余裕は **10.4%** しかない。⛔「FEASIBLE 確立」は言い過ぎ。しかも `ke` を上げる C-2 は **cap に当たる**（検証者 sim で shoulder_lift が 150 N·m = 100% 到達）⇒ **飽和すると servo は開ループになり、§2.1 の lag 則そのものが成立しなくなる** = bar 構造の前提が消える。⇒ **saturation leg は bar 凍結の「同時」でなく「前」**（prereg 再改訂が要る）。

---

## 3. R-ROBUST（Rs 裁定 B の必須要件）— 構造

**要件**: 新振付は摂動耐性を持つ。scale ≥ trainer residual / DR。
**由来**: §13 R-3「1 mrad 級で連鎖が flip する振付は DR/residual（15 mm 級）/noise 下の訓練に耐えない」。

⛔⛔ **訂正（pre-check ISSUE 4 — 私の誤読）**: 私は「**arm q 差 ≤1.1 mrad で連鎖が全滅**する」と書いたが、**原文は逆**である。
> `ARM_CONTROL_PD1_RESULT_RSTECHLEAD_20260719.md:20-24` 逐語: 「Same build, same seed, **kinematic drive both**; ONLY the imported-actuator tug removed … Arm q divergence R0-vs-R1 ≤ **1.1 mrad**（**the kinematic drive forces the same arm poses**）⇒ the flip is carried **entirely by the CABLE-side physics response** to the hidden saturated tug.」

⇒ **arm q は「動かさなかった側（統制変数）」**であり、1.1 mrad はその残差。**arm q 感度の証拠ではない。** 実証された感度は **cable 側の接触/引張応答**。
⇒ ⛔**R-ROBUST の摂動軸が間違っていた**: 下表の 2 leg（cable 初期姿勢・毎ステップ指令）は、**実証された故障ドライバ（cable 側の持続力）を一切励起しない**。
⇒ **摂動軸は cable 側の接触力/摩擦/保持へ再導出する**（次版）。⚠ charter `:334` の「1mrad 級で flip する振付」も同じ緩い言い方で、charter `:331` の正しい記述（「flip は cable 側 knife-edge 応答」）と食い違う ⇒ **charter 側も訂正対象**（現 owner = p11・proposal で p4 へ）。

| leg | 摂動 | 受入 |
|---|---|---|
| **R-ROBUST-1** 初期条件 | cable 初期 pos/pose を DR scale で振る（⚠ pos/pose-random は **DEPLOY 要件**・RS71 §0#4 注） | 述語連鎖の完了率 ≥ 宣言値（N seed） |
| **R-ROBUST-2** 毎ステップ指令 | residual scale の指令摂動を上乗せ | 同上 |

⛔ **数値は置かない**: DR scale / residual scale は **trainer 側の値**（%12/pQ court）。⇒ **借りる側**であり本書で確定しない（v0.1 §6 flag と同じ）。
⭐ **設計への反映（今できる形）**: §2.3 の整定余裕は residual 分だけ食われる ⇒ **phase 端点に整定時間の余裕を明示的に確保する**（振付が端点で「すぐ次へ行かない」）。⇒ **W-b への設計制約として渡す**。
⚠ **単発成功を受入にしない**（「別様に出得ない test」回避）— 受入は **率**で定義する。

---

## 4. W-1 の設計ゲート（`/diffik-trajectory` protocol 適用）

**W-1** = 振付を「記録された状態の再生」でなく「**IK が生成する目標軌道**」として定義する。PD が追従した結果を demo として記録する。

⚠ **substrate 差の明示（規約混同の回避）**: 本 skill の Franka Panda 値（J1-J4 2.62 rad/s、J3 < −65° で NaN、Overlap region 座標、PhysX articulation、DiffIK の λ）は **PhysX/Franka 環境の所見**。本設計は **env7-mujoco / UR5e×2 / Newton `IKSolver`** ゆえ**流用しない**。以下は env7 実測に置換した形。

### 4.1 移動量（Step 1）
- frame = **480 Hz**（`DT = 1/480`）。EE 速度 `v` に対し 1 frame の EE 移動 = `v/480`。⇒ **1 mm/frame 以内なら `v ≤ 0.48 m/s`**（EE 空間は余裕）。
- ⭐**律速は EE 空間でなく joint 空間**: §2.3 より `T_lag` と整定時間が支配。⇒ **step size でなく「phase 端点で止まる時間」を設計変数にする**。

### 4.2 ⛔ 補間方式（Step 2）— generic recipe と M-3 の衝突を解決
- skill の推奨「漸進目標」は **実 EE 位置から** step を作る（`ee_pos = robot.data.body_pos_w …`）= **realized state からの再 seed**。
- ⛔ これは **M-3（command-space・realized から再 seed しない）に抵触**する。理由（M-3 原文）= lag 下で measured-q 再 seed は軌道を歪め noise を target に結合する。
- ⭐ **解決 = 前回の *指令* からの漸進**（realized でなく command を state に持つ）:
  ```
  cmd[k+1] = cmd[k] + clamp(target − cmd[k], max_step)
  ctrl     = IK(cmd[k+1])          # realized q は読まない
  ```
  ⇒ **position-based（time-based 禁止は満たす）** かつ **command-space（M-3 保存）**。
- ⛔ **time-based 補間は不採用**（skill 原則・velocity clamping との正帰還）。

### 4.3 IK 実体（Step 3）— env7 の実測値
- **DiffIK/λ ではない**: env7 は Newton `IKSolver` + `IKObjectivePosition` / `IKObjectiveRotation` / `IKObjectiveJointLimit`（`newton_route_env.py:76,870-885,987`）。
- 実測パラメータ = **`IK_ITERATIONS_RL = 30`**、**`IK_STEP_SIZE = 1.0`**（`newton_skill_env_base.py:99-100`）。⇒ skill の λ 表は**適用しない**。
- ⭐ joint limit は **objective として IK に入っている**（`IKObjectiveJointLimit`）⇒ 軌道側で limit 回避を二重に作らない。

### 4.4 THREAD 固有リスク（Step 4・env7 版）
| リスク | 本設計での扱い |
|---|---|
| 把持中の cable 張力急変 | 端点整定 + M-5 ramp で指令側を平滑化（§2.3 / M-5） |
| `RL_SIM_SUBSTEPS = 4` | ctrl は frame 保持・substep は内部積分（charter §5 の仮説 tag を継承・S-2 で native 確認） |
| joint limit | `IKObjectiveJointLimit` が担当（§4.3） |
| ⛔ Franka の J3 −65° / Overlap 座標 | **適用しない**（PhysX/Franka 所見・substrate 混同禁止） |
| コ字 gripper 幾何 | **human-LOCKED**。触れる案が出たら **STOP → p4 → Rs** |

### 4.5 W-1 の判定
- **採択（提案）**: W-1。理由 = ①kinematic を経由しない（裁定 B / P-1 適合）②M-3 と同型 ③§0#3「IK が target 源」を保存 ④W-2 は L-P0 が既に否定（旧振付は清潔基盤で連鎖しない）⑤W-3 は費用大で DDR#31 と絡む。
- ⏸ **確定は `/pre-check` 通過後**（§5）。

---

## 5. `/pre-check` 併載（失敗モード）— §6 に結果

## 6. 非主張 / gate 状態
- **凍結していない**: `T_LAG_BAR` / (iv)(v) の値 / R-ROBUST の摂動量 / gains 最終値。
- **未実施 gate**: `/force-design`（gains 確定時に必須）・L3 chain・CC Debate。⇒ **p0 は本書で動けない**。
- §2.3 の整定式は **一次系近似の仮説**（lag 則は実測・減衰形は未実測）。(iv) ringing leg が反証機会。
- 43 step が env7 で走ることを主張しない（実行 driver = DDR#31・私の court 外）。
- 物理妥当性を判定しない（最終 = Rs 動画 human-GT）。

## 7. L 自己申告
**L2 相当**（設計裁定を含む・新規 file 1・コード 0・landing なし）。⇒ **CC Debate は p0 実装前の L3 chain で実施**（本書は proposal 段）。commit = explicit pathspec + `--no-verify`（DDR #35）。
