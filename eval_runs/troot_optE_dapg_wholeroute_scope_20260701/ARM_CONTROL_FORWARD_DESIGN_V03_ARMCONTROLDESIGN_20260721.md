# 前向き腕制御設計 v0.3 — BLOCK 6 件の根治（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** DESIGN v0.3 — **proposal**（landing = p4）。**v0.2 = BLOCK（`cf02408202`）を supersede。**
**設計対象:** env7-mujoco / UR5e×2 + Robotiq 2F-85 / 振付 = 再工事 W-b / 原則 **P-1 = 物理結果を捨てない**。
⛔ **実装認可でない**（`/pre-check` 再実行の結果は §8）。

**⚠ 本書の数値は全て p11 が env7 の MuJoCo で自ら実測**（`mj_fullM` / `mj_jac` / `qfrc_bias`、asset = `ur5e.xml`）。v0.2 pre-check の検証者値と**独立に一致**（M = 3.498 / 3.294、ζ vendor 2.39 / 2.46、ドループ 26.2 mrad）。

---

## 0. 何を直したか（BLOCK 6 件との対応）

| BLOCK | 根治 | 節 |
|---|---|---|
| C-1 一次系近似が高慣性で不成立 | gain 基準を **`kd/ke` 比 → 関節ごとの `ζ`** へ。C-1/C-2 は**却下** | §1 |
| C-2 重力ドループで bar 到達不能 | **重力フィードフォワードを必須化**（剛性だけでは不可能と定量） | §2 |
| C-3 飽和 | 飽和を **加速度制限**として定式化（速度制限ではない） | §3 |
| C-4 R-ROBUST の摂動軸誤り | 摂動軸を **cable 側**へ再導出 + 数値化 | §5 |
| H-2 bar(iv) が probe 出力で決まる | bar(iv) を **task 許容値から先に決める** | §4 |
| H-4 anti-windup 無し | **M-3 非破壊**の凍結条件を追加 | §6 |
| M-3 readback 空洞化 | M-1 に **arm DOF readback assert** 同梱 | §7 |

---

## 1. ⭐ gain 基準の置換 — `kd/ke` 比から関節ごとの臨界減衰へ

**却下**: C-1（一律 `kd×0.25`）/ C-2（`kd×0.25` + `ke×2`）。
理由（実測）= 肩が**不足減衰**に入る ⇒ `ζ = kd/(2√(ke·M))`:

| gains | ζ sh_pan / sh_lift（最悪配置） | 判定 |
|---|---|---|
| vendor | 2.39 / 2.46 | 過減衰（振動なし・ただし `T_lag` 0.2 s と遅い） |
| **C-1** | **0.60 / 0.62** | ⛔ 不足減衰 |
| **C-2** | **0.42 / 0.44** | ⛔ 不足減衰（かつ減衰率は `kd/2M` で **`ke` に依存しない** ⇒ C-2 の利得は存在しない） |

**採る基準（提案）= 関節ごとに `ζ = 1`（最悪配置の慣性で）**:

> **`kd_crit = 2·√(ke · M_worst)`** ⇒ **`T_lag = kd/ke = 2·√(M_worst/ke)`**

| joint | `ke` | `kd` vendor | **`kd_crit`** | `T_lag` vendor | **`T_lag` crit** | 改善 |
|---|---|---|---|---|---|---|
| shoulder_pan | 2000 | 400 | **167.3** | 0.200 s | **0.0836 s** | 2.39× |
| shoulder_lift | 2000 | 400 | **162.3** | 0.200 s | **0.0812 s** | 2.46× |
| elbow | 2000 | 400 | **77.6** | 0.200 s | **0.0388 s** | 5.15× |
| wrist_1 | 500 | 100 | **15.5** | 0.200 s | **0.0310 s** | 6.44× |
| wrist_2 | 500 | 100 | **14.4** | 0.200 s | **0.0288 s** | 6.95× |
| wrist_3 | 500 | 100 | **14.2** | 0.200 s | **0.0283 s** | 7.07× |

⭐ **`ke` は vendor のまま**（実機 spec 由来・fidelity を触らない）。**変えるのは `kd` のみ**、しかも一律でなく**慣性から導出**。
⭐ **振動なし（ζ=1）で `T_lag` が 2.4〜7.1× 改善** ⇒ C-1/C-2 が狙った効果を、**不足減衰に落ちずに**得る。
⚠ `T_lag` は**関節ごとに非一様**になる（0.028〜0.084 s）。lag 則 bar は元から per-joint なので問題ない。
⚠ **`M_worst` は配置依存**（実測 4 配置の最大）。W-b の実 waypoint 確定後に**再計算して凍結**する（本書は基準と手順を固定し、値は暫定）。

---

## 2. ⭐ 重力フィードフォワード = 必須（剛性では解けないことの定量）

**実測**: `τ_g`(shoulder_lift) 最大 **52.41 N·m** ⇒ 純 PD の恒久ドループ `= τ_g/ke`:

| `ke` | ドループ | bar(iii) 5 mrad |
|---|---|---|
| 2000（vendor） | **26.2 mrad** | ⛔ FAIL |
| 4000 | 13.1 mrad | ⛔ FAIL |
| 8000 | 6.6 mrad | ⛔ FAIL |
| 16000（vendor の 8×） | 3.3 mrad | ○ |

⇒ **剛性だけで bar を満たすには `ke` を 8× にする必要があり、実機 spec 由来の値を捨てることになる（fidelity 非保守）。⛔ 採らない。**
⇒ **重力補償で発生源ごと消す**（ドループ項が消えるので `ke` は vendor のまま）。

**可用性（実測）**: `Control.joint_f`（feedforward forces）= `SolverMuJoCo` support（`solvers.py:304`）。`gravcomp` / `jnt_actgravcomp` の custom attribute も存在（`solver_mujoco.py:717-724` / `:779-785`）。
⛔ **route env では未使用**（閉クエリ: `newton_route_env.py` / `newton_skill_env_base.py` に `Control.joint_f` の使用 0 件。※ grep hit の `joint_facts` は別物）。
⇒ **本設計で新規に配線する**。⚠ **P-1 抵触なし** — 力を足すのであって、solver の出した状態を捨てない。

⭐ **副次効果**: 重力ぶんの torque が空くので加速度余裕が増える（§3）。

---

## 3. ⭐ 飽和 = 速度制限でなく**加速度制限**

定常速度では PD の torque は重力ぶんに落ち着く。cap に当たるのは**加速・減速**時。⇒ 制約は:

> **`a_max = (cap − |τ_g|_max) / M_worst`**

| joint | cap | `|τ_g|`max | `M_worst` | **`a_max`** | 重力補償後（`cap/M`） |
|---|---|---|---|---|---|
| shoulder_pan | 150 | 0.00 | 3.498 | **42.9 rad/s²** | 42.9 |
| shoulder_lift | 150 | 52.41 | 3.294 | **29.6 rad/s²** | **45.5**（+54%） |
| elbow | 150 | 15.86 | 0.753 | **178.1** | 199.2 |
| wrist_1/2/3 | 28 | ≤1.38 | ≤0.120 | **221 / 271 / 280** | 〃 |

⇒ **W-b への設計制約（本書の主要な出力）**: 各関節は `|a| ≤ a_max`。速度 `ω` からの停止に **最低 `ω/a_max`** の時間が要る:

| `ω` | shoulder_pan | shoulder_lift | elbow |
|---|---|---|---|
| 0.5 rad/s | 12 ms | 17 ms | 3 ms |
| 1.0 rad/s | 23 ms | 34 ms | 6 ms |
| 2.56 rad/s（旧記録 peak 相当） | 60 ms | **86 ms** | 14 ms |

⛔ **effort cap は上げない**（±150/±28 N·m = 実機 spec、`ur5e.xml:10-11,19`）。
⚠ **旧 banked の「飽和 0.0%」を根拠に使わない** — あれは `wrist_2` 支配の記録再生で得た値、かつ `25.1/28 = cap の 89.6% 消費`。**肩 × 重力負荷では未測定**。

---

## 4. bar 5 本立て（**probe 前に task 要件から決める**）

| # | bar | 値 | 出所 |
|---|---|---|---|
| (i) | 静的/settle `|q−ctrl|` | ⏸ **未凍結** — **重力補償後に PD 面で再導出** | ⛔旧 2 mrad は kinematic 面（`|q−ctrl|≈0` が恒等）で得た値ゆえ PD 面の情報を持たない |
| (ii) | lag 則 `T_lag = err/ω` | **`T_lag ≤ 2√(M_worst/ke)`**（＝ ζ=1 の値・§1 表） | 設計から決まる（probe は確認） |
| (iii) | phase 端点到達 | **5 mrad** | task が精度を消費する点（維持） |
| (iv) | **no-ringing / overshoot** | **EE 1.75 mm**（= `SEAT_LAT_BAR` 3.5 mm の 50%）<br>関節換算: sh_pan **2.11** / sh_lift **2.13** / elbow **3.56** / wrist_1 **17.5** mrad | ⭐**task 許容値から**（`route_env_config.py:174` `SEAT_LAT_BAR_M = 0.0035`「cable centre max off-axis, in-groove」）。EE 換算は `mj_jac` 実測（1 mrad → 最大 0.83 mm） |
| (v) | M-6 divergence guard | ⏸ 未凍結。⭐**述語を `q − q_equilibrium`（重力補償後）へ**変更し、**飽和フラグと接触フラグで分離** | 旧 `|q−ctrl|` はドループ/障害/飽和/真の故障を判別しない |

⭐ **H-2（別様に出得ない test）の解消**: `ζ ≥ 1` を採ると**線形 2 次系では overshoot = 0 が予測される**。⇒ probe は「bar を決める run」でなく「**予測されたゼロを反証する run**」になる。⚠ 実系は接触・連成があるので**予測が破れ得る** ⇒ 反証機会が実在する。

---

## 5. ⭐ R-ROBUST の摂動軸を cable 側へ再導出（C-4 の根治）

**根拠の訂正（v0.2 §3 の誤りを是正）**: L-P0 で **arm q は統制変数**（`kinematic drive both` ⇒ 姿勢は強制一致・残差 1.1 mrad）。実証された故障ドライバは **cable 側の物理応答**（隠れた飽和 tug の除去で連鎖が消えた）。⇒ **arm 側を振る leg では、実証された故障を再現できない。**

| leg | 摂動軸 | 根拠 |
|---|---|---|
| **RB-1（主）** | **cable 側の持続外力/接触**（tug 相当の定常力を印加して連鎖が生き残るか） | L-P0 が実際に操作した変数そのもの |
| **RB-2** | **摩擦係数**（cable-clip / cable-finger） | 保持は摩擦拘束（`log.md:6534` の F-1 所見「retention = gravity+lateral+condim-friction」） |
| **RB-3** | cable 初期 pos/pose | DEPLOY 要件（RS71 §0#4 注）。⚠ **主 leg ではない**（実証ドライバでない） |

**受入（反証可能な形にする）**: 各 leg で **N seed の述語連鎖完了率 ≥ 宣言値**。
⛔ **摂動量と完了率を数値で置くまで、R-ROBUST を他案の却下根拠に使わない**（v0.1 の W-2 却下理由から本項を撤回済）。
⚠ **摂動量の出所**: tug 相当力は **L-P0 の実測から逆算できる**（私の court）。DR/residual scale は trainer 側（%12/pQ court）— ⭐**借りるのでなく、§3 の `a_max` と §1 の `ζ` から「制御側が吸収できる外乱 budget」を宣言して trainer へ上限として渡す**（M-1 指摘の循環を切る）。

---

## 6. anti-windup（M-3 を壊さない形）

**問題**: `cmd[k+1] = cmd[k] + clamp(target−cmd[k], max_step)` は realized q を読まないので、**障害物で `q` が止まっても `cmd` は進み続け**、torque が cap に張り付いたまま押し込む。`IKObjectiveJointLimit` は weight=10 の**軟**目的（`newton_route_env.py:883`）で硬拘束ではない。

**解（提案）**:
> `|q − ctrl| > W_HOLD` **または** actuator 飽和 が継続 ⇒ **`cmd` の前進を凍結**（⛔ reset も再 seed もしない）。解消したら再開。

⭐ **M-3 は保存される**: M-3 が禁じたのは「**realized q を target の種にする**」こと（軌道が歪み noise が target に結合する）。本条件は realized q を**スカラーの停止判定**にのみ使い、**target 値には一切入れない**。⇒ 種でなく**番人**。
⚠ `W_HOLD` は §4(iii) の 5 mrad より大きく、§4(v) の M-6 発火より小さく置く（3 段: 追従誤差 → 前進凍結 → physics-fault）。値は probe 後。

---

## 7. M-1 に readback assert を同梱（M-3 指摘）

現 `servo_readback_assert`（`newton_route_env.py:268`）の負対照は「**arm** / 4-bar follower に servo は無い」を主張し、gripper の `ke=66.7` に紐づく。⇒ **M-1 で arm に servo を張ると、この負対照は arm について空洞化する**（落ちないが、覆わなくなる）。

⇒ **M-1 と同一変更で** 12 本の arm DOF に対する readback assert を出す:
- `joint_target_mode == POSITION`（12 本ちょうど）
- `joint_target_ke/kd` == §1 の設計値（per-joint）
- `jnt_actfrcrange` == ±150 / ±28（**cap 不変の機械確認**）
- imported 12 本が **構造的に不在**（B1-strip）
- **負対照**: 上記以外の DOF に arm servo が付いていないこと

---

## 8. `/pre-check` 再実行 — 結果は §8-R

## 9. 非主張 / gate
- **凍結していない**: `M_worst`（W-b waypoint 後に再計算）/ bar(i)(v) / `W_HOLD` / RB の摂動量・完了率。
- **未実施**: `/force-design`（gains 確定時に必須）・L3 chain・CC Debate。⇒ **p0 は動けない**。
- ζ=1 の overshoot 0 は**線形 2 次系の予測**。接触・連成下では破れ得る（§4 の反証 leg）。
- 43 step が env7 で走ることを主張しない（実行 driver = DDR #31）。
- 物理妥当性を判定しない（最終 = Rs 動画 human-GT）。

## 10. L 自己申告
**L2 相当**（設計裁定・コード 0・landing なし）。commit = explicit pathspec + `--no-verify`（DDR #35）。
