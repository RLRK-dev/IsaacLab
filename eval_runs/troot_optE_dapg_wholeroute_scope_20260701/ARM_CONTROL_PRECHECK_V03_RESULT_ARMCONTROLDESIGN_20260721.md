# `/pre-check` 再実行 — 設計 v0.3 = **BLOCK（2 回連続）** + 手法の見直し（p11, 2026-07-21）

**対象:** `ARM_CONTROL_FORWARD_DESIGN_V03_ARMCONTROLDESIGN_20260721.md`（v0.2 BLOCK `cf02408202` の根治版）。
**Verdict: ⛔ BLOCK**（13 issues = CRITICAL 4 / HIGH 5 / MEDIUM 4）。
⚠ **前回の CRITICAL 4 件のうち、真に解決したのは 1 件（C-4）のみ。**

---

## 1. ⭐ 手法の問題（本書の主要な結論）

**2 回連続で BLOCK。しかも 2 回とも同じ型で落ちている:**

| 回 | 私が測った面 | 主張が必要とした面 |
|---|---|---|
| v0.2 | `wrist_2`（低慣性）の 0.512 rad | 肩（30× 重い）の整定 |
| v0.3 | **素の `ur5e.xml`・`q=0` の 4 姿勢** | **as-built モデル（UR5e + 2F-85）・到達範囲全体** |
| v0.3 | **対角化した 1 関節 2 次系** | **連成質量行列の modal 減衰** |
| v0.3 | **`wrist_3_link` の Jacobian** | **把持点（cable 接触）の Jacobian** |

⇒ **毎回「都合よく測れる面」で計算し、主張が要求する面で測っていない。** 同じ型を 1 session で 4 回踏んだ（§14.27 で他者に指摘した型と同一）。

⭐ **手法の結論**: **gain と bar を手で導出するのをやめる。**
> **as-built モデル（`add_ur5e_robotiq` 経由・2F-85 込み・collapse_fixed_joints）に対し、到達範囲を掃いて「連成 modal 減衰・`qfrc_bias`(q,q̇)・把持点 Jacobian」を計算する手続きを設計成果物にし、数値はその出力とする。**

⇒ 次版（v0.4）は「数値の集合」でなく「**数値を出す手続きと、その受入条件**」を出す。⛔ 3 回目の手計算はしない（`CLAUDE.md` ハードストップ「3 回失敗したら方針を疑え」の手前で方針を変える）。

---

## 2. CRITICAL 4 件（要点）

| # | 指摘 | 私の扱い |
|---|---|---|
| **1** | `M_worst` が **素の `ur5e.xml` の `q=0`**（最大でない・実 build 資産でもない）。as-built（2F-85 の base 質量が `wrist_3_link` に畳まれる）では **+26〜37%** ⇒ 私の `kd_crit` では真の最悪姿勢で **ζ = 0.87 = 不足減衰** | ✅ 受理。§1 の数値は無効 |
| **2** | 対角 `diag(M)` 近似が ζ を **約 25% 過大評価**。連成 modal ζ = **0.684**。⛔ **接触なしの sim で overshoot 5.5〜80.5 mrad**（私の bar 2.11〜3.56 mrad の 1.5〜38×）⇒ **「ζ≥1 なら overshoot=0」は既にディスク上で反証済** | ✅ 受理。§4 の H-2 解消は成立しない |
| **3** | ⭐**重力 FF が effort cap を迂回する** — `Control.joint_f` は `qfrc_applied` へ書かれ（`kernels.py:1423-1424`）、`actfrcrange` は **actuator force のみ**を clamp する（`solver_mujoco.py:5046` 逐語「Use actfrcrange to clamp total **actuator** force (P+D sum)」）⇒ **cap 超えの力が入る = 実機より強い sim = 非保守**。私自身の「cap は上げない」と「sim は現実世界」に抵触 | ✅ **受理（私が原文確認）**。⇒ 代替 = **`gravcomp` + `jnt_actgravcomp=True`**（actuator 経由ゆえ clamp される） |
| **4** | anti-windup の `W_HOLD` を 5 mrad 近傍に置くと、**定常追従誤差（22〜208 mrad）で通常移動のたびに発火**。しかも凍結は windup を**解消しない**（`ke·W_HOLD` を押し続ける）・**timeout も無い** ⇒ 障害が解けなければ**デッドロック** | ✅ 受理。W_HOLD は §4(ii) の lag から導くべきで、§4(iii) から導いたのが誤り |

---

## 3. ⭐ 私が独立確認した基盤事実（設計に関係なく有効・banked する価値あり）

| # | 事実 | 実測 |
|---|---|---|
| **S-1** | **`Control.joint_f` は effort cap の外**（`qfrc_applied` 経由） | `kernels.py:1398,1423-1424` + `solver_mujoco.py:5046` |
| **S-2** | **`joint_f` は KINEMATIC body では捨てられる**（`if body_flags & KINEMATIC: return`） | `kernels.py:1415` ⇒ **腕が kinematic 駆動のままでは重力 FF は無効果**（M-1 が hard precondition） |
| **S-3** | ⛔⛔ **effort cap ±150/±28 は build されたモデルの joint 制限として存在しない** | importer は **joint 属性 `actuatorfrcrange`** から `effort_limit` を取る（`import_mjcf.py:1548-1556`）が、**`ur5e.xml` の `actuatorfrcrange` 出現数 = 0**（実測）。±150/±28 は **imported actuator の `forcerange`** にのみ在る ⇒ **B1-strip がそれを消すと `joint_effort_limit` は builder 既定の 1e6 に落ちる = fail-open** |

⭐ **S-3 は安全側の発見**: 私は「effort cap = 実機 spec、⛔上げない」を**不変条件として扱ってきた**が、**B1-strip 後はその cap が存在しない**。⇒ **M-1 は `joint_effort_limit = 150/28` を明示的に書き、1e6 既定でないことを assert しなければならない**（さもないと「上げない」どころか**無制限**になる）。

---

## 4. HIGH / MEDIUM（要点）

| # | 指摘 | 扱い |
|---|---|---|
| 5 | `|τ_g|max` 過小（52.41 → **62.36**）。**elbow 10.33 / wrist_1 5.43 mrad も bar(iii) 5 mrad を超える**（私は shoulder_lift だけの問題として書いた）。`a_max` は 30〜50% 楽観 | ✅ 受理 |
| 6 | `a_max` が **Coriolis/遠心力を無視**。ω=2.56 rad/s で **48.2 N·m**（重力と同程度）を消費 ⇒ `a_max` は約半分 | ✅ 受理。`cap − max|qfrc_bias(q,q̇)|` へ |
| 7 | Jacobian が `wrist_3_link` — **wrist_2/3 の位置列が構造的にゼロ**（回転のみの手首）。把持点では 32〜175% 過小 | ✅ 受理。⚠**bar が作れていなかった関節が `wrist_2`** = 元の 0.512 rad の当該関節 |
| **8** | ⭐**bar(iv) が C-4 と同じ反転を再犯** — `SEAT_LAT_BAR` は **cable 中心**の許容（`route_env_config.py:170` 逐語）なのに、**arm Jacobian** で関節 bar に変換した ＝「cable 位置は arm q の剛体関数」を仮定。**同じ doc の §5 がそれを否定している** | ✅ **受理（最も痛い）**。C-4 を直した節の隣で同型を再犯 |
| 9 | `q − q_equilibrium` は §2（厳密重力補償）下で `q − ctrl` と**恒等** ⇒ 空振り。M-6 の真の誤発火（通常 slew 22〜208 mrad vs trip 15 mrad）は未解決 | ✅ 受理 |
| 10-13 | cap 不在（S-3）/ banked L-P6 cross-check（「proto 値 ≡ imported 値」）を `kd` 変更が破る・supersession 未宣言 / `joint_f` KINEMATIC 落ち（S-2）/ 2.56 rad/s は**実測でなく逆算**・行番号 `:883`→実体 `:882` | ✅ 受理 |

---

## 5. 前回 CRITICAL 4 件の解決状況

| | 状態 |
|---|---|
| C-1 一次系近似 | ⛔ **未解決** — 方法（最悪慣性で ζ を留める）の**向きは正しい**が、実行した数値が誤った資産・姿勢集合・対角近似で出ている |
| C-2 重力ドループ | 🔶 **部分** — 必須化は正しく `joint_f` の可用性も真。ただし**機構が cap を破る**（S-1）・大きさ過小・対象関節を取りこぼし |
| C-3 飽和 | 🔶 **部分** — **加速度制限への読み替えは正しい**（検証者が `f_act = M·a + τ_bias` を実測確認）。ただし数値が 30〜50% 楽観・Coriolis 欠落 |
| **C-4 R-ROBUST 摂動軸** | ✅ **解決**（唯一）。cable 側へ移し、arm 側を降格し、W-2 却下根拠の撤回も明示。⚠ ただし **bar(iv) で同型を再犯**（ISSUE 8） |

---

## 6. 非主張
- 検証者の sim 値（modal ζ 0.684 / overshoot 5.5-80.5 mrad / as-built M / Coriolis / 把持点 Jacobian）は **私は再現していない** ⇒ **検証者帰属**。私が独立確認したのは **S-1 / S-2 / S-3 の 3 件**（原文・実測）。
- 設計を修正していない（本書は gate 記録 + 手法の見直し）。
- ⛔ **p0 は動けない**（BLOCK 継続）。
