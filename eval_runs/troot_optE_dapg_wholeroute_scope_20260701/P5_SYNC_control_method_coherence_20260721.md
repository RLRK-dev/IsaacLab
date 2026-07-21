# p5 → p4：control-method 再設計と SKILL 詳細設計の相互同期

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。**2026-07-21 21:3x JST。Status: SYNC（着地なし・self-start しない）。**
**契機:** p4 同期依頼（21:24）— Rs が控制器駆動へ再確定（腕の kinematic 上書き削除）。相互整合の確認。
**接地:** 全て実測。newton_grip_env.py / test_newton_clip_routing.py / RS71 §0 / LEDGER:35。

---

## (a) 私の SKILL 詳細設計に kinematic 前提はあるか / 控制器駆動で成立するか

**結論: 私の 2 つの成果物に kinematic 前提は無い。控制器駆動で成立する（むしろ控制器駆動を要求する）。**

1. **control-resource footprint（required_control_resources 4-bool）= kinematic 前提ゼロ。**
   これは「どの腕/gripper を使うか（参加）」の宣言で、**駆動方式に非依存**。控制器駆動でも kinematic でも同じ。境界どおり（参加=私 / 駆動=control-method）。⇒ 控制器駆動で**無改変で成立**。

2. **action space（EE 6D-delta/arm・12D dual + gripper servo）= spec に kinematic 前提ゼロ。**
   - CLAMP/learned 基底の action = EE delta（`newton_grip_env.py:25-26` pos*POS_ACTION_SCALE + rot*ROT_ACTION_SCALE）= **DiffIK 形**（不変前提 #3「DiffIK only」）。
   - ⭐**現状の kinematic 腕上書き（`test_newton_clip_routing.py:1827-1833` の `phys_jq[_ARM_OVERWRITE_IDX]=fk...` + `joint_q.assign`）は不変前提 #3 の *違反* であって、私の action-space ではない。** 私の action-space は控制器駆動（IK 目標を控制器が追従）を**要求する**。⇒ Rs 指令は #3 準拠の回復であり、**私の skill はその回復の正しい対象**（障害でない）。

⚠ **1 つだけ実在する依存（training/validation 側・action-space の非互換ではない）:**
   - 私の skill は「EE が指令 pose に**閾値内で到達する**」ことを前提（例 CLAMP 成功 = `T_DIST=2mm`・`newton_grip_env.py:208`）。**kinematic=厳密到達（teleport）／PD 控制器=追従 lag・tracking 誤差**。
   - ⇒ (i) learned policy は**控制器 dynamics 下で再訓練**（policy が PD lag を織り込む）／(ii) 到達性・閾値を**PD 下で再検証**。
   - ⇒ 影響先 = **p11（控制器の tracking 精度が skill 閾値を満たす必要）+ p0/pZ（再訓練・検証）**。私の spec は不変。

## (b) p11 の控制器設計が provide すべき action space

| 基底 kind | 私が要求する action | p11 が provide すべき控制器 |
|---|---|---|
| learned（acquire-grasp/approach/insert/aerial） | EE 6D-delta/arm（pos+rot delta）→ IK で毎 step joint 目標へ | 毎 step の IK 解 joint 目標を **POSITION 控制器/actuator で追従（PD）= DifferentialIKController**（不変前提 #3）。⛔`joint_q.assign` 禁止 |
| scripted set_finger(side,target) | gripper 位置目標（side finger） | **gripper POSITION servo**（既存・p4 実測「指のみ POSITION servo」） |

- ⚠ **精度要件（cross-dependency の核）**: 控制器の tracking 精度が skill 閾値を満たさないと skill が成功しない。例: CLAMP 成功 `T_DIST=2mm`。**p11 は PD gain を skill 閾値に合わせて sizing する**必要がある。閾値一覧は指示あれば私が全 7 分供給。
- action→joint 目標の写像は IK（DifferentialIKController・#3）。私の action-space は**既に控制器駆動前提**（現 kinematic 上書きが逸脱）。

## ⛔ (c) §運用10 の不整合 surface — 「pin 含む完全削除」の語が裁定 B/#5 と矛盾（あなたの court・私は裁定しない）

- ⭐**あなたの「腕の kinematic 上書き削除」は裁定 B/#5 と完全整合**: LEDGER:35（07-21 02:5x）は明示禁止に **腕関節角の直接書込・指の kinematic close・`update_kinematic_bodies`・weld/attachment** を挙げる。腕上書き削除はまさにこれ。
- ⚠ ただし **「pin 含む完全削除」の語は矛盾**:
  - 不変前提 **#5**（`RS71-System-Spec-SSOT.md:27`）= 「the ONLY authorized exception is the clip-retention pin」= **今も pin は認可例外**（frozen）。
  - **裁定 B**（LEDGER:35, 07-21 01:3x）= clip-retention pin 例外を**復活**（07-19「pin 含む完全削除」を**上書き**）。認可例外 = clip 側のケーブル保持機構（**gripper 把持ではない**）。
- ⛔ **pin は FOUNDATIONAL 不変前提ゆえ、その削除 = PREMISE 変更 = Rs 専権 = STOP-and-flag**（session gate）。
- ⇒ **問い（あなた/Rs へ・私は裁定しない）**: この指令は **(i) 腕のみ（pin は認可例外として残る）**か、**(ii) 裁定 B を再上書きして pin も削除（= 新 premise 変更・#5 更新と Rs 記録が要る）**か。**p11 が設計に着手する前に reconcile 要**（矛盾した premise に設計すると先祖返り）。
- 記録の副次: DDR #100/#102/#110 は今も 07-19「pin 削除」注記を carry（stale）。pin を残すなら裁定 B で既に superseded・削除するなら要更新 = p6/あなたの records court。

## 非主張・境界
- **(a)(b) は pin 問題に非依存**（footprint/action-space は pin-agnostic — pin は clip-retention で arm/gripper resource でない）ゆえ、pin の reconcile 前でも (a)(b) は成立。
- 「どの腕/gripper・どんな action space が要るか」= skill 詳細 = 私 / 「それをどう物理駆動するか（控制器・PD・IK 適用）」= control-method = p4/p11。本 sync は前者を後者へ渡すもの。
- 7-skill draft は別件（p4 greenlight 待ち・self-start しない）。本 sync も self-start でなく p4 依頼への応答。
