# 前向き腕制御設計 v0.4 — **手続き仕様**（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** DESIGN v0.4 — **proposal**（landing = p4）。**v0.2 / v0.3（いずれも BLOCK）を supersede。**
**方針転換（p4 承認 2026-07-21 15:11 JST）:** gain と bar を**手で導出しない**。本書は **数値を出す手続きと受入条件**であり、**数値は手続きの出力**。

⛔ **本書には設計数値を書かない。** 書けば v0.2/v0.3 と同じ失敗（手で誤った模型を置く）を 3 度目に繰り返す。
⛔ 実装認可でない。⚠ 計算は **design-time（モデル build + 解析）**に留める。重い compute が要る段は gate を立てる（p4 指示）。

---

## 0. なぜ手続きにするか（失敗の根）

v0.2 / v0.3 の BLOCK は 1 つの型に還元される — **測ったモデルが、走るモデルでなかった**:

| 私が測った面 | 主張が要求した面 | 結果 |
|---|---|---|
| `wrist_2`（低慣性）の追従誤差 | 肩（約 30× 重い）の整定 | 一次系近似が破れた |
| 素の `ur5e.xml`・`q=0` の 4 姿勢 | **as-built**（2F-85 込み）・到達範囲全体 | 慣性 26〜37% 過小 ⇒ ζ が 1 を割る |
| 対角化した 1 関節 2 次系 | 連成質量行列の modal 減衰 | ζ を約 25% 過大評価 |
| `wrist_3_link` の Jacobian | 把持点（cable 接触）の Jacobian | `wrist_2/3` の列が構造的にゼロ ＝ bar が作れていない |

⇒ **手続きの第 1 段を「モデル同一性の確認」にする。** ここを通らない限り、下流の数値は全て無効とする。

---

## 1. P-0 **モデル同一性ゲート**（最初に置く・fail-closed）

**目的**: 解析対象が、実際に走るモデルと同一であることを先に立証する。

**build は生産経路をそのまま呼ぶ**（実測した呼び出し形・`newton_skill_env_base.py:1561`/`:1567`）:
```
add_ur5e_robotiq(proto, wp.transform(ROBOT_LEFT_BASE,  wp.quat_identity()),
                 robotiq_xml=ROBOTIQ_STRIPPED_XML, skip_equality_constraints=True)
add_ur5e_robotiq(proto, wp.transform(ROBOT_RIGHT_BASE, wp.quat_identity()),
                 robotiq_xml=ROBOTIQ_STRIPPED_XML, skip_equality_constraints=True)
```
⛔ **素の `ur5e.xml` を直接読まない**（v0.3 の誤り）。`ROBOTIQ_STRIPPED_XML` = コ字 asset（§0#4 LOCK）。

**assert（全て通って初めて下流へ）**:
| # | 述語 |
|---|---|
| A-1 | body 数・**body ごとの質量**が env の実 build と一致（`collapse_fixed_joints` により 2F-85 base 質量が `wrist_3_link` に畳まれることを含む） |
| A-2 | DOF 数・**joint 名と順序**が一致（腕 `{0-5, 14-19}` / gripper `{6-13, 20-27}` の配置と整合） |
| A-3 | **両腕**が入っている（片腕モデルで測らない・§0#1） |
| A-4 | `nu`（actuator 数）と、それが imported か proto かの別が宣言と一致 |
| A-5 | **把持対象（cable）の有無を宣言**し、無い場合は「把持質量を含まない上界/下界のどちらか」を明示 |

⚠ **A-5 の理由**: 把持した cable は鎖端質量を増やす ⇒ 慣性は**増える**方向 ⇒ cable 抜きの ζ は**楽観側**。⇒ **cable 抜きで測るなら、その ζ は上界であると明記**する。

---

## 2. P-1 **到達範囲の定義**（envelope は入力・結果は範囲内でのみ有効）

- envelope は **W-b の実 waypoint から定義する**のが本則。⏸ **waypoint は未確定**ゆえ、暫定は **joint limit ∩ 実 route が使う領域**とし、**waypoint 確定後に再実行**する。
- ⛔ **手で選んだ数姿勢を「最大」と呼ばない**（v0.3 の誤り）。掃引は**格子または最適化**で行い、**掃引条件（範囲・刻み・件数）を出力に必ず添付**する。
- **結果は envelope 内でのみ有効**と明記する。外側は「未測定」であって「安全」ではない。

---

## 3. P-2 **連成 modal 減衰**（対角近似を使わない）

- 各 `q` で `M(q) = mj_fullM` を取り、**二次固有値問題** `det(λ²M(q) + λK_d + K_e) = 0` を解く。
- 出力 = **envelope 上の最小 modal 減衰 `ζ_modal,min`**（対角式 `kd/(2√(ke·M_ii))` は**参考値としてのみ**併記）。
- **設計則**: `k_d` を **`ζ_modal,min ≥ ζ_target`（envelope 全域）** を満たす最小の値に選ぶ。
  - `ζ_target` は**余裕を持たせる**（1.0 ちょうどに置かない — 把持質量・接触・離散化で下振れするため）。値は手続きの出力と §5 の bar から決める。
- ⛔ **`k_e` は vendor 値を動かさない**（実機 spec 由来・fidelity）。動かす提案が要る場合は **STOP → p4 → Rs**。

---

## 4. P-3 **トルク予算**（重力だけでなく速度依存項を含める）

- **`τ_bias(q, q̇) = qfrc_bias`** を **(q, q̇) の envelope** 上で掃引し最大値を取る（重力 **＋ Coriolis/遠心**）。⛔ 重力のみで予算を組まない（v0.3 の誤り）。
- **加速度余裕** `a_max = (cap − max|τ_bias|) / λ_max(M(q))`。⛔ `M_ii` でなく**連成の最大固有値**を使う。
- 出力 = per-joint `a_max` と、そこから出る **停止時間の下界 `ω/a_max`** ⇒ **W-b への設計制約**（各 phase 端点で確保すべき減速時間）。

---

## 5. P-4 **把持点 Jacobian**（`wrist_3` で取らない）

- 参照 frame = **`pinch` site**（`2f85_koshape.xml:79` `<site name="pinch" pos="0 0 0.145" …>`）。⛔ `wrist_3_link` は **`wrist_2`/`wrist_3` の位置列が構造的にゼロ**になるため使わない（v0.3 の誤り）。
- 出力 = per-joint **mm / mrad**（envelope 上の最大）。
- ⚠ **`wrist_3` は把持軸と同軸**ゆえ位置 Jacobian が小さくても、**cable の軸外広がり × 回転 Jacobian** で cable を動かす ⇒ **回転成分を別途評価**し、位置 Jacobian だけで bar を作らない。

---

## 6. P-5 **bar の導出**（provenance と写像の妥当性を先に立てる）

⛔⛔ **v0.3 ISSUE 8 の再犯を防ぐ規律（本節の主眼）**:
`SEAT_LAT_BAR_M`（`route_env_config.py:170` 逐語「**cable centre** geometrically inside the groove」）は **cable 中心**の許容である。**arm Jacobian で関節 bar に変換してはならない** — それは「cable 位置は arm q の剛体関数」を仮定するが、**L-P0 はそれを否定している**（着座中の cable は clip と摩擦が保持し、arm の剛体従属ではない）。

⇒ bar は **2 系統に分けて、それぞれ出所を持たせる**:

| 系統 | 対象 | 出所 | 写像の妥当性 |
|---|---|---|---|
| **B-arm**（サーボ品質） | `\|q − ctrl\|`・modal ζ・overshoot・`T_lag` | **制御側の要求**（追従品質そのもの） | 写像不要（同じ空間で閉じる） |
| **B-task**（task 許容） | cable 着座の可否 | `SEAT_LAT_BAR_M` 等 | ⚠ **cable 変位 ÷ EE 変位の伝達を実測してからでないと関節 bar に落とせない** |

- **B-task を関節 bar に落とすには測定が要る**（把持・着座の各 phase で cable がどれだけ arm に従うか）。⏸ **未測定ゆえ、本手続きでは B-task を関節 bar に変換しない。**
- **M-6 / anti-windup の述語は「lag 補正後の残差」**（`|q − ctrl| − T_lag·ω̂`）で定義する。⛔ 生の `|q − ctrl|` は**通常移動でも大きい**（定常追従誤差）ため、健全動作で発火する（v0.3 ISSUE 4/9）。
- **anti-windup の凍結には上限時間と escalation を付ける**（無期限凍結 = デッドロック。v0.3 ISSUE 4）。

---

## 7. ⭐ 基盤事実の fold（S-1 / S-2 / S-3・私が原文確認・p4 承認で反映）

| # | 事実 | 設計への反映 |
|---|---|---|
| **S-1** | `Control.joint_f` は `qfrc_applied` に載り（`kernels.py:1423-1424`）、`actfrcrange` は **actuator force のみ**を clamp する（`solver_mujoco.py:5046` 逐語） ⇒ **cap の外** | ⛔ **重力補償を `joint_f` で行わない**（実機より強い sim = 非保守・「sim は現実世界」に抵触）。⇒ **`gravcomp` + `jnt_actgravcomp=True`**（actuator 経由 ⇒ cap 内）。⚠ 補償分が cap を消費するので **P-3 の予算に計上**する |
| **S-2** | `joint_f` は **KINEMATIC body で捨てられる**（`kernels.py:1415`） | 腕が kinematic 駆動のままでは重力補償は**無効果** ⇒ **M-1（動的化）が hard precondition**。⭐**正対照レグ必須** = 補償が実際に `qacc` を変えることを示す |
| **S-3** ⛔⛔ | **effort cap ±150/±28 は build 済モデルの joint 制限として存在しない**。importer は joint 属性 `actuatorfrcrange` から取る（`import_mjcf.py:1548-1556`）が **`ur5e.xml` の出現数 = 0**（実測）。cap は **imported actuator の `forcerange`** にのみ在り、**B1-strip がそれを消す** ⇒ `joint_effort_limit` は builder 既定 **1e6** に落ちる = **fail-open** | ⭐**M-1 は `joint_effort_limit = 150 / 28` を明示 write し、readback で `≠ 1e6` を assert する**（§8）。**他の設計判断と独立に必須**（安全側）。⚠ 表現も訂正: 「cap 不変」でなく「**cap を新規に設置する**」 |

---

## 8. M-1 に同梱する readback assert（v0.3 §7 を S-3 で改訂）

- `joint_target_mode == POSITION` が **arm 12 本ちょうど**
- `joint_target_ke` == vendor 値（**不変**）／ `joint_target_kd` == P-2 の出力値
- ⭐ **`joint_effort_limit == 150 / 28` かつ `≠ 1e6`**（S-3・**fail-open 検出**）
- imported 12 本が **構造的に不在**（B1-strip）
- **負対照**: arm 以外の DOF に arm servo が付いていない
- ⚠ **banked L-P6 の cross-check（`proto 値 ≡ imported 値`・charter `:89`）は `kd` について成立しなくなる** ⇒ **supersession を明示宣言**し、`ke` 側の一致検査は維持、`kd` 側は「P-2 出力への導出追跡」に置換（**p4 経由で ratify**）。

---

## 9. 受入条件（手続きが「効いた」と言える形・反証可能）

| # | 条件 |
|---|---|
| AC-1 | **P-0 の A-1〜A-5 が全て PASS**（1 つでも落ちたら下流の数値は無効） |
| AC-2 | `ζ_modal,min ≥ ζ_target` が **envelope 全域**で成立（掃引条件を添付） |
| AC-3 | **overshoot の予測値を先に宣言**し、sim 実測がそれを超えないこと。⛔「0 と予測して 0 を確認する」形にしない（v0.3 で 5.5〜80.5 mrad に反証された） |
| AC-4 | `a_max` が **`τ_bias(q,q̇)` 最大値込み**で算出されている（重力のみでない） |
| AC-5 | 把持点 Jacobian が `pinch` site で取られ、**回転成分が別評価**されている |
| AC-6 | B-task 由来の bar が **関節空間へ変換されていない**（伝達測定前） |
| AC-7 | **`joint_effort_limit ≠ 1e6`** が readback で確認されている（S-3） |
| AC-8 | 重力補償が **cap 内経路**（`gravcomp`+`jnt_actgravcomp`）で、かつ **`qacc` を変える正対照**が取れている（S-1/S-2） |

---

## 10. 非主張 / gate
- **数値を出していない**（意図的）。gain・bar・`a_max`・ζ_target は**手続きの出力**。
- **凍結していない**。**実装していない**。**走らせていない**。
- W-b waypoint 未確定ゆえ envelope は暫定 ⇒ **確定後に再実行**が前提。
- 43 step が env7 で走ることを主張しない（実行 driver = DDR #31）。
- 物理妥当性を判定しない（最終 = Rs 動画 human-GT）。
- ⛔ **p0 は本書で動けない**（`/pre-check` 未通過）。

## 11. L 自己申告
**L2 相当**（設計裁定・コード 0・landing なし）。commit = explicit pathspec + `--no-verify`（DDR #35）。
