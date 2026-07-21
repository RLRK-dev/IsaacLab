# p5 提案：各 skill の required_control_resources 宣言形（腕/gripper 参加）

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。**2026-07-21 12:4x JST。Status: PROPOSAL（着地しない・granularity は pX と整合）。**
**契機:** p4 surface（12:33）— 凍結契約が各 skill に required_control_resources 4-bool を要求するが機械宣言源が不在。
**接地:** 全て実測。契約 `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md`（sha256 `00192d20…`）/ `skill_contracts_manifest.json` / `step_table.py` / skill 実装。出典 provenance = p4（pQ 整合回答・LEDGER §DDR F4）。

---

## 1. 要件（実測）
- 契約 `:142` `required_control_resources: ControlResourceSpec`（各 SkillDefinition に必須）。
- 契約 `:151` `ControlResourceSpec = {ee_left, ee_right, gripper_left, gripper_right: bool}`。
- 契約 `:380` invocation 時に **`required ⊆ offered`** の bool 包含を検査（validate_invocation_start）。

## 2. gap（実測・p4 主張を確認）
- `step_table.py`: `required_control_resources` / 明示 arm-gripper bool = **0 件**。持つのは**暗黙信号** `target_left`/`target_right`/`l_finger`/`r_finger`（`:68-71`）のみ。
- `thread_isaac_lab/wmso/d1/skill_contracts_manifest.json`: 各 skill は `obs_action_schema`（`:58` 等）を持つが **`required_control_resources` フィールド無し**。CLAMP は `:67` 「**CLAMP{side} resolution deferred**」で既に side 未解決と記録。

## 3. ⛔ 暗黙信号から自動導出できない（設計上の核心）
`target_left=None` は「keep current（現状維持）」の意味（`step_table.py:70`）で、**「左腕で保持中＝ee_left を使う」と「左腕は不関与＝使わない」を潰す**（私が 2026-07-21 に DUAL-ARM 機械検証性で指摘した同じ曖昧性）。
⇒ 4-bool を `target_left`/`r_finger` の None から**推論すると誤る**。**明示 authored 宣言が要る**。実際 `required ⊆ offered` 検査（`:380`）は保持腕を offered に含めないと invocation を弾くので、hold を「不関与」と誤宣言すると**保持している skill が実行不能になる**。

## 4. ⭐ 設計の要：基底が coordinate-parametric ゆえ resource は side の関数
pX の基底 7 は side を**パラメータ**に取る（set_finger(side,target) 等・pX が確定）。ゆえに required_control_resources は**静的 4-bool でなく side 束縛の関数**:
- `set_finger(side='left')` → `gripper_left=T`・他 F。`set_finger(side='right')` → `gripper_right=T`・他 F。
- 契約の field は **SkillDefinition ごとの静的 4-bool**。⇒ 整合させる形（契約 + manifest の "CLAMP{side} deferred" と一致）:
  - **基底 entry = 射影規則**（parameter 束縛 → 4-bool）を宣言。
  - **凍結 SkillDefinition = side 解決済みインスタンス**（例 `set_finger_left` / `CLAMP_left`）が、射影で計算した**静的 4-bool** を持つ。
  - これは pX の見立て「side は合成グラフ側の座標」と一致 — グラフが side を束縛し、解決済みインスタンスを生む。

## 5. 提案する宣言形
- **格納場所**: skill-detail 層（私の court）に **per-skill の required_control_resources 宣言（authored・非導出）** を置き、manifest/契約はこれを参照/import する。⚠ 凍結契約と manifest は私は編集しない（pQ/pS の court）— **content と form を提案し、格納先と着地は pQ/pS+pX が決める**。
- **shape**: 基底 entry ごとに `params → {ee_left, ee_right, gripper_left, gripper_right}` の射影規則。side-parametric な entry は side 束縛を読む。side 解決で静的 4-bool に materialize（契約が検査するのはこの静的値）。
- **hold の明示**: 「動かさないが保持している腕」は当該 resource を **True**（`required ⊆ offered` を通すため）。動作の有無でなく**参加の有無**で立てる。

## 6. 実装から確定できる populate（実測済のみ・残りは §7）
| 基底 entry | realization（実測） | ee_L | ee_R | grip_L | grip_R | 根拠 |
|---|---|---|---|---|---|---|
| **acquire-grasp（CLAMP dual）** | `newton_grip_env` dual_arm=True・14D=12D EE+2D finger（`:259`）・両 finger auto-close（`:27`） | T | T | T | T | 両腕 EE + 両 finger |
| （同 per-arm `CLAMP_{side}`） | SkillType `CLAMP_L`/`CLAMP_R`（`skill_adapter.py:10-11`） | side=L→T | side=R→T | side に一致 | side に一致 | 片腕版は side のみ |
| **re-tighten / set_finger(side,target)** | scripted `interpolate_fingers`（`newton_routing_utils.py:1275`）・side finger のみ・EE 動作なし | F | F | side=L→T | side=R→T | finger のみ・EE 不使用 |

## 7. 未確定（自分で導出せず・granularity は pX・実装読了後に populate）
- 残る基底（approach_cable / insert_into_clip / aerial_regrasp / transport / clip_confirm 等 — pX の 7 の内訳しだい）は各 realization を読んで populate する。⚠ 特に **aerial_regrasp は step_table で target None**（`:191`）ゆえ §3 の曖昧性がそのまま当たる — 右接近は ee_right、左保持は「保持ゆえ ee_left=T」を **authored で立てる**必要がある（learned policy の実体を読んで確定）。
- **granularity は pX の分解に従う**（entry がどれだけあるか・side をどこで束縛するか）。pX の 7 が固まっているので、指示あれば全 7 の射影規則 + side 解決 4-bool を私が起草する。

## 8. 境界（自己申告）
- **これは提案**。着地・凍結契約編集・manifest 編集はしない（pQ/pS court）。
- **「どの腕/gripper を使うか」= skill 詳細 = 私の court。「その resource をどう駆動するか」= control-method = p4 court**（本提案は参加の宣言であって駆動方式でない）。
- 07-Design/04-Specs read-only・設計=Rs 専権は不変。
