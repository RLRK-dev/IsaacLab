# 腕を制御器で駆動して route を実現する設計 v1.0（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** DESIGN v1.0 — **proposal**（landing = p4 → L3 + 設計 gate → p0 実装 → pZ 検証 → Rs 動画）。
**契機:** Rs 直接指示（emphatic・2 回連呼）「**kinematic は使用するな！完全削除！！**」（p4 relay 2026-07-21 21:16:41 JST）。p4 が現校正 route を実行し、**腕が kinematic 駆動である**ことを実証して Rs に提示した結果。
**任務:** **腕を制御器で駆動して route を成立させる**（kinematic 書込ゼロ）。**DoD = 腕・ハンド・フィンガを描画した動画で、route が制御器駆動で成立していること。**

⛔ **本書は構造の設計であり、ゲイン・bar・速度の数値を確定しない。** 数値は測定（既存 P-D1 実測 + 測定ハーネス）から取る。v0.2〜v0.4 の 3 連続失敗は「手で数値を導いた」ことに由来する。

---

## 1. 私が自分で確認したこと（relay を根拠にしない）

| # | 事実 | 実測（p11 が読んだ場所） |
|---|---|---|
| 1-a | **mujoco 枝は毎 substep、腕の関節座標を FK 値で上書きし速度を 0 にする** | `test_newton_clip_routing.py:1815-1838` 逐語「per-substep OVERWRITE joint_q=FK + zero joint_qd」+ `phys_jq[_ARM_OVERWRITE_IDX] = fk_state.joint_q…` / `phys_jqd[…] = 0.0` / `state_0.joint_q.assign(phys_jq)` |
| 1-b | **VBD 枝は FK の body 変換を physics へ複写する** | `:1752` `update_kinematic_bodies`（`phys_bq[:robot_body_count] = fk_bq[…]`） |
| 1-c | ⭐**指はすでに制御器駆動** — gripper 座標は DYNAMIC のまま servo が `control.joint_target_pos` で駆動 | 同 `:1826-1828` 逐語「leave the gripper coords … DYNAMIC so the servo drives them via `control.joint_target_pos`」 |
| 1-d | ⭐**RL env にも同じ kinematic 駆動が在る**（producer 限定ではない） | `newton_route_env.py:829-830`（`_broadcast_arm_jointq` = settle 中に毎フレーム）/ **`:1272-1273`（route 駆動の毎 physics サブフレーム）** |
| 1-e | 同 env の `:1096-1097` は **episode 開始時の re-pose**（reset） | `:1088-1097`（`env_ids` 単位の reset 再配置） |

⇒ **1-c が本設計の骨格**: 求められている機構は**同じ file の中に既に在り、指で動いている**。

## 2. ⭐ 削除範囲の分類（**これを誤ると IK が壊れる**）

| class | 内容 | 扱い |
|---|---|---|
| **A** | **制御ループ内**の physics state 書込（`_state_0.joint_q/qd.assign` で腕座標を上書き） | ⛔ **削除対象**（＝ Rs 指示の対象）。`route_env:829-830` / `:1272-1273`、`test:1815-1838`、`:1752` |
| **B** | **reset 直後**の初期化（episode 開始時 1 回） | ⚠ 現行規則では**許可**（`CLAUDE.md` の reset 例外）。⇒ **Rs の「完全」がここまで及ぶかは p4 → Rs 確認事項**（本設計は A を前提に組み、B の可否で構造は変わらない） |
| **C** | **FK state への書込**（`_fk_state.joint_q.assign(...)`） | ✅ **削除しない**。これは**目標を計算する側**であって physics の駆動ではない。⛔ ここまで消すと IK が目標を作れなくなる |

⚠ **class C を A と混同した「完全削除」は、指示の実現ではなく破壊になる。** 実装時の述語は「**physics state に書いているか**」であって「`assign` を含むか」ではない。

## 3. ⭐ 既存実装（**新規発明ではない** — §運用4 prior art）

`probe/pd1-arm-pd` に **腕の POSITION servo 経路が既に実装済**（環境変数 `ARM_PD_DRIVE=1` で切替）。p11 実測 = `git show probe/pd1-arm-pd:thread_isaac_lab/envs/newton_route_env.py`:

| 機構 | 実装場所（同 branch） |
|---|---|
| XML actuator の無力化（M-1 相当） | `:449` `ARM_XML_ACT_NEUTRALIZE` |
| 起動時の目標同期（M-4 相当） | `:452` `_arm_pd_ramp_q0`（活性時の実現 q を snapshot） |
| 立ち上げの傾斜（M-5 相当） | `:450` `ARM_PD_RAMP_FRAMES` / `:1390-1391` |
| POSITION mode + ke/kd 実配線 | `:301-304`（`joint_target_ke` / `JointTargetMode.POSITION`）/ `:833-834` |
| 毎フレームの目標書込 | `:1380-1391`（`control.joint_target_pos`・qd-indexed） |
| reset / hold も target 経路へ | `:909-914` / `:1183-1226` |

⇒ ⭐**設計課題は「機構を作る」ではなく「(a) 分岐を唯一の経路へ昇格し kinematic 側を削除する」「(b) 数値を決める」「(c) 削除で壊れる箇所を設計し直す」。**

## 4. ⭐ 実測が既に答えていること（`ARM_CONTROL_PD1_RESULT_RSTECHLEAD_20260719.md`・6 run）

| 問い | 実測の答え | 出典（逐語） |
|---|---|---|
| 制御器駆動でトルクは足りるか | ✅ **足りる** — 飽和 **0.0%**、最悪関節 **25.1 N·m < 28 cap** | §3「L-P3 saturation: PASS — 0.0% on every joint」 |
| では何が問題か | ⭐ **粘性の追従遅れ**（力不足ではない）。`err ≈ (kd/ke)·ω` | §3「the error is a **viscous velocity-tracking lag**, not force starvation」 |
| 遅れは残るのか | ⛔**残らない — 速度に比例し、遅い局面で消える**。実測 profile **0.45 → 0.51 → 0.20 → 0.02 → 0.005 → 0.001 rad** | §3 |
| どのレバーを引くべきか | **`kd/ke` の比**（`ke` の大きさではない）。effort cap は触らない | §5「suggests the **kd/ke ratio, not ke magnitude**, as the lever … effort caps stay untouched」 |
| 旧振付は清潔基盤で成立するか | ⛔**しない**（kinematic 駆動でも把持連鎖が形成されない） | §2「the clean substrate does not carry the banked chain even kinematically」 |

⚠ **私の過去の誤読を撤回済**: 「arm q 差 ≤1.1 mrad で連鎖が全滅」は誤り。原文は **両 run とも kinematic 駆動ゆえ腕姿勢は強制一致**し、**flip は cable 側**が担う、である。

## 5. 設計（構造のみ・数値は §6 の測定から）

### 5.1 制御路（唯一の経路）
- 腕関節 = **POSITION target mode** + `joint_target_ke` / `joint_target_kd` / `joint_effort_limit`。
- IK が出した関節目標を **毎 physics frame `control.joint_target_pos` に書く**（指と同一機構・§1-c）。
- ⛔ physics state（`joint_q` / `joint_qd` / `body_q`）への制御ループ内書込は**行わない**（class A 全廃）。
- 起動 = **M-4 同期**（活性時の実現 q を目標の初期値にする）→ **M-5 傾斜**（既存実装）。

### 5.2 ⭐ 振付は「制御器が追える形」で書く（W-b 再工事の中心）
`err ≈ T_lag·ω`（`T_lag = kd/ke`）ゆえ、**遅れは指令速度で決まり、止まれば消える**。⇒ 振付側に 2 つの要求:

1. **接触が効く瞬間の前に静定させる** — 目標を止めてから `t_dwell ≥ k·T_lag` 待つ（`k` は許容誤差から決める。⚠ **`k` と `T_lag` は測定値**）。⇒ 把持・着座・押込みは **静定した状態で**起こす。
2. **連続精度が要る局面だけ速度を絞る** — その局面の `ω ≤ ε_task / T_lag`。自由移動区間は速くてよい（誤差は task に効かない）。

⚠ **旧 L-P1 の「連続 5 mrad」は task 要求ではなく、記録済み軌道への parity bar**。⇒ 本設計の bar は **task に効く量（着座時の cable 中心位置）× 効く瞬間**で立てる（測定 H-5 の伝達比が要る）。**⛔ 連続追従 bar を task bar に流用しない。**

### 5.3 削除で壊れる箇所（設計し直す対象）
| 箇所 | 現状 | 設計 |
|---|---|---|
| cable settle 中の腕保持（`route_env:829`） | 毎フレーム joint_q 書込 | **目標を home に固定して servo に保持させる**（外乱は物理として現れてよい） |
| route 駆動（`:1272`） | 毎サブフレーム joint_q 書込 | `control.joint_target_pos` へ（§5.1） |
| reset（`:1096`） | joint_q 再配置 | class B（§2）。**A の削除とは独立**に扱う |
| 監視 | — | **追従乖離ガード**（実現 q と目標の差が閾値を超えたら停止して報告）。⛔ 黙って続行しない |

## 6. 数値（**測定待ち** — 決めない）

| 量 | 出所 |
|---|---|
| per-joint `T_lag = kd/ke`（as-built） | 測定ハーネス H-2（`K_e`/`K_d` 実測。⚠ 既知の vendor 値は size1 = 100/500・size3 = 400/2000 ＝ **どちらも 0.2 s** — as-built で照合する） |
| 到達可能な `ω`・加速度余裕 | H-3（`τ_bias` + `λ_max(M)`。cap は H-6a の実測値） |
| `ε_task`（着座許容） → 関節 bar | **H-5 の伝達比**（⛔ arm Jacobian で変換しない） |
| ζ（減衰） | H-2（§H-2.2 の (i) 固定縮約が bar） |
| `k`（静定待ち時間の係数） | 上記 `T_lag` と `ε_task` から決まる |

## 7. ⚠⚠ pin — **私の court 外の衝突を先に出す**（p4 → Rs）

Rs「**完全**」は pin を含む（p4 relay）。⚠ **これは銀行済の 2 決定と衝突する**:

1. `RS71-System-Spec-SSOT.md:27` §0#5 = 「唯一の認可例外 = clip-retention pin」＋ **2026-07-15 Rs 決定**「クリップ**のみ** pin を RL env に恒久配線しろ」。
2. 同 §4 `:62`（Rs DECISION B2, 2026-06-25）= cable は **鉛直面のみ曲がる 1-DOF ベンダ**ゆえ**水平方向の配線曲率を表現できない** ⇒ **staggered clip 通しは kinematic**であり、⭐**pin の無い RL env は task を表現できない**。

⇒ **pin を消すなら、次のどれかが必要**（いずれも私の court 外・設計選択肢の提示のみ）:
| | 案 | 影響 |
|---|---|---|
| P-a | 保持を**物理拘束**で実現（clip 形状・摩擦・接触で保持させる） | substrate/asset 側の設計。⚠ コ字 asset は human-LOCKED ⇒ 触れるなら Rs |
| P-b | **cable モデルを変更**（水平曲率を表現できる形へ） | §4:62 の前提そのものの変更 ＝ Rs 専権 |
| P-c | **task 表現を変更**（clip 通しの定義を変える） | SOMA/工程表側 ＝ Rs 専権 |

⭐ **本設計は pin の可否に依存しない**: §5 は**腕の駆動**のみを扱い、pin は保持機構として直交する。⇒ **pin 裁定を待たずに腕側を進められる**（p4 の「それまで削除方向で設計継続」と整合）。
⛔ **私は §0#5 を解釈しない。** 衝突の所在を示すのみ。

## 8. gate / 手続き

- **L 自己申告 = L3**（diff 内容キーワード `newton` / `ik` / `solver` 該当・制御方式の実装形変更）。⇒ `/rule-check stage1` は p4 court で確定。
- **設計 gate**（`/reward-design` は非該当・`/pre-check` は実装前に必須）＝ p4 が起動。
- ⚠ **重力補償は本設計に含めない**（制御則の変更 ＝ Rs 承認事項。未承認ゆえ入れない）。§4 のとおり**力は足りている**ので、現時点で必要性の根拠も無い。

## 9. 非主張

- ゲイン・速度・dwell の**数値を出していない**（測定待ち）。
- P-D1 の 6 run は **p4 の実測**であり、p11 は**再現していない**（doc を読んだ）。私が独立に読んだのは §1 の 5 点と §3 の branch 実装。
- 「制御器駆動で route が成立する」とは**まだ言えない**。実測が言うのは「**トルクは足り、遅れは速度依存で静定すれば消える**」まで。成立の判定は **Rs の動画**（DoD）。
