# 腕を制御器で駆動して route を実現する設計 v1.0（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** DESIGN v1.0 — **proposal**（landing = p4 → L3 + 設計 gate → p0 実装 → pZ 検証 → Rs 動画）。
**契機:** Rs 直接指示（emphatic・2 回連呼）「**kinematic は使用するな！完全削除！！**」（p4 relay 2026-07-21 21:16:41 JST）。p4 が現校正 route を実行し、**腕が kinematic 駆動である**ことを実証して Rs に提示した結果。
**任務:** **腕を制御器で駆動して route を成立させる**（kinematic 書込ゼロ）。**DoD = 腕・ハンド・フィンガを描画した動画で、route が制御器駆動で成立していること。**

⛔ **本書は構造の設計であり、ゲイン・bar・速度の数値を確定しない。** 数値は測定（既存 P-D1 実測 + 測定ハーネス）から取る。v0.2〜v0.4 の 3 連続失敗は「手で数値を導いた」ことに由来する。

### p4 からの確定回答（2026-07-21 21:27:42 JST）

| 論点 | 確定 |
|---|---|
| 削除範囲 | ✅ **A（制御ループ内 physics 書込）= 削除 / C（FK 書込）= 削除しない** で確定。**B（reset 再配置 `:1096-1097`）＋ pin = Rs 裁定待ち** |
| 測定 | ✅ **HOLD 解除 = YES**。p0 の H-2 結線は継続。**測定は制御器設計に直結**（`kd/ke` と task bar を H-2 / H-5 が供給する） |
| 重力補償 | ✅ **入れない**（力は足りているため必要性の根拠が無い）で現状維持 |
| pin | p4 が spec 裏取りのうえ **Rs へ上程済**（(i) 残す / (ii) 消す + P-a/b/c）。⇒ **腕側は依存しないので先行** |
| 次段 | 数値が測定で埋まり次第 **L3 + 設計 gate**（`/diffik-trajectory` `/force-design` `/pre-check`） |

⭐ **測定 spec の被覆確認（p11 実測・追加要求なし）**: 本書 §6 が要る 4 量は **spec v1.3 が既に要求済** — `K_d`（`:130` 生 28×28 dump）/ `a_max` と `τ_bias`（`:141-142`, AC-4）/ **phase 別 伝達比**（`:154`, AC-6）/ `ζ`（`:138`）。⇒ **spec を触らない**（churn を作らない）。

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

1. **接触が効く瞬間の前に静定させる** — 目標を止めてから `t_dwell` 待つ。⇒ 把持・着座・押込みは **静定した状態で**起こす。
   - ⭐ **`t_dwell` の式は ζ で場合分けする**（**H-2 の ζ が要るのはここ**）: **ζ ≥ 1**（非振動）なら残差は概ね `exp(−t/T_lag)` ⇒ `t_dwell ≥ k·T_lag`（`k = ln(初期誤差/ε)`）。**ζ < 1**（振動）なら包絡は `exp(−ζ·ω_n·t)` で**行き過ぎと振動が残る** ⇒ `t_dwell ≥ k/(ζ·ω_n)` かつ **半周期の整数倍を待たない**（節で測ると静定して見える）。
   - ⚠ **`t_dwell` を「速く見えるまで」で決めない。** ⛔ **1 時点の速度が小さい ≠ 静定**（振動の折返しでも小さくなる）。判定は **窓で**（連続 N フレーム |q−target| ≤ ε かつ |q̇| ≤ ε̇）。
2. **連続精度が要る局面だけ速度を絞る** — その局面の `ω ≤ ε_task / T_lag`。自由移動区間は速くてよい（誤差は task に効かない）。

⚠ **旧 L-P1 の「連続 5 mrad」は task 要求ではなく、記録済み軌道への parity bar**。⇒ 本設計の bar は **task に効く量（着座時の cable 中心位置）× 効く瞬間**で立てる（測定 H-5 の伝達比が要る）。**⛔ 連続追従 bar を task bar に流用しない。**

### 5.3 削除で壊れる箇所（設計し直す対象）
| 箇所 | 現状 | 設計 |
|---|---|---|
| cable settle 中の腕保持（`route_env:829`） | 毎フレーム joint_q 書込 | **目標を home に固定して servo に保持させる**（外乱は物理として現れてよい） |
| route 駆動（`:1272`） | 毎サブフレーム joint_q 書込 | `control.joint_target_pos` へ（§5.1） |
| reset（`:1096`） | joint_q 再配置 | class B（§2）。**A の削除とは独立**に扱う |
| 監視 | — | **追従乖離ガード**（実現 q と目標の差が閾値を超えたら停止して報告）。⛔ 黙って続行しない |

### 5.4 ⭐ SKILL 側の到達閾値との結合（p5 が 7 SKILL 分を送付予定・2026-07-21 21:32 p4 relay）

SKILL は EE 到達閾値を持つ（例: CLAMP 2 mm）。⇒ **制御器の追従がそれを満たすように gain を決める**必要がある。⭐**ただし誤差は 2 種あり、効く対策が違う**:

| 誤差 | 式 | 静定で消えるか | 効くレバー |
|---|---|---|---|
| **動的な遅れ**（追従ラグ） | `≈ T_lag·ω = (kd/ke)·ω` | ✅ **消える**（目標を止めれば減衰・§5.2） | 指令速度 `ω` / `kd/ke` の比 |
| ⭐**静的なたわみ**（重力ドループ） | `≈ τ_bias(q)/ke`（純 PD） | ⛔ **消えない**（釣り合ってしまうため、いくら待っても残る） | **`ke` の大きさ**のみ（重力補償は §8 で除外済） |

⇒ ⭐**閾値が「静定した瞬間」に効くもの（CLAMP 等は到達してから掴む）なら、gain sizing を縛るのは遅れではなく たわみ**: **`ke ≥ τ_bias(q)/ε_joint`**（envelope 上の最大 `τ_bias` で）。⇒ **H-3 の `τ_bias` が gain の下限を決める。**
⚠ 逆に、閾値が**動いている最中**に効くもの（連続追従が要る局面）なら §5.2 の速度制限が効く。⇒ **どちらかは閾値ごとに違う。**

⭐ **閾値一覧の受領時に必ず添えて貰う 3 項**（無いと変換できない・v0.2/v0.3 の失敗の型そのもの）:
1. **どの点か** — 手首フランジ / 指先 / pad / **cable 中心**。⚠ `ee_pos_*` は**手首フランジ**であり指先ではない（掴んでいても物体まで 268 mm と出る）。
2. **どの瞬間か** — 静定後 / 動作中。⇒ 上表のどちらの誤差に当たるかが決まる。
3. **何に対する距離か** — 目標姿勢との差 / 物体との距離。

⇒ 変換経路: **cable 中心の量は H-5 の伝達比**で、**腕 EE の量は H-4 の Jacobian**で関節 bar に落とす。⛔ **cable の量を腕 Jacobian で変換しない**（cable は腕の剛体従属ではない）。

#### 5.4.1 p5 から受領した閾値表（`P5_EE_REACH_THRESHOLDS_for_p11_20260721.md` @ `49a6f66323`・sha256 `e93ee3d799f0bb0d…`・**p11 が code 側を独立確認**）

| skill | 閾値 | 点 | 瞬間 | routing |
|---|---|---|---|---|
| acquire-grasp | pos **2 mm**（`task_config.py:362` `T_DIST=0.002`）/ ori **10°**（`:364` `T_ALIGN=0.1745`） | 指先 | **保持 K=5**（静定） | **H-4** |
| approach | pos **12 mm**（`:363` `T_DIST_APPROACH=0.012`） | 指先 | — | **H-4 + H-5**（基準が cable 分節ゆえ分離） |
| insert 着座 | pos **3 mm**（`:368` `T_GROOVE=0.003`）/ ori `cos > 0.85`（`:369` `T_SEAT`） | ⭐**cable 分節 body**（腕でない） | 着座 | ⛔**H-5 のみ**。腕側の押込目標 `PUSH_Z=1.025` は H-4 |
| aerial | 落下不可 `min(cable z) > 0.82` | cable body | — | ⛔**H-5** |
| carry | 明示数値なし（下流継承 = grasp の 2 mm 予算内） | 指先 | — | H-4 |
| hold / wait | grasp の 2 mm 保持を継承 | 指先 | **静定** | H-4 |
| set_finger | `0.002 / 0.006 / 0.04` | **指 joint** | — | **H-4/H-5 とも N/A**（gripper servo・腕 EE 量ゼロ） |

⭐ **結論（sizing の核）**: **ほぼ全ての成功閾値が「保持・静定」で評価される** ⇒ §5.4 の表より **縛るのは重力たわみ = `ke` の大きさ**（`kd` ではない）。
⚠ **`T_SEAT = 0.85` は段階的引き締めの初期値**（`:369` 逐語「0.85→0.9→0.95」）⇒ **sizing は最終側 0.95 で見る**（保守側）。p5 の指摘どおり。

#### 5.4.2 ⛔⛔ 実測で見つけた測定面のずれ（**p5/Rs へ escalate・私は裁定しない**）

閾値が測る「指先」は `ee_pos + R(ee_q)·[0,0,**0.220**]`（`newton_skill_env_base.py:899-905`）。⚠ **その 0.220 は自身のコメントで Franka legacy と明記**（`task_config.py:78` / `:84`「Franka value; **re-derive S6**」/ `:324`）。⚠ **同 file に実測のコ字値が別に在る**: `EE_TO_PINCH_CLOSED = 0.2548`（`:320`）/ `EE_TO_PINCH_TIP_CLOSED = 0.2757`（`:321`）。

⇒ ⭐ **「指先」という同じ語が 2 点を指し、差は 34.8〜55.7 mm = 2 mm 閾値の 17〜28 倍。**
- **sizing への影響**: 腕の手先までの長さが変わる ⇒ **mrad あたりの mm が変わる** ⇒ 関節 bar が変わる。⇒ **H-4 を 3 点で出させる**（spec v1.4 §H-4.1: J-a 閾値の点 0.220 / J-b pad body / J-c 爪先 0.2757）。**sizing は「閾値と同じ面」= J-a で行う**。
- **task への影響**: 目標も同じ 0.220 で作られていれば**腕と目標の一致には相殺**するが、**cable との接触は物理の世界で起きる**ので相殺しない。⇒ **どの点で閾値を評価すべきかは p5/Rs の court。**
- ⚠ **私が確認していないこと**: 「live の acquire-grasp 成功判定が `compute_clamp_pos` を呼ぶ」は **p5 帰属**。私の `grep` では `T_DIST` の live 消費は tests / `mpc_config_ic.py` に見え、env 側の判定行は特定できていない。⇒ **p5 に live consumer の file:line を照会**（判定に効くため）。⭐ **本設計はこの未確認に依存しない** — H-4 を 3 点で出せば、どの点でも bar を立てられる。

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
