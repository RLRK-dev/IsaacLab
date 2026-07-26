# class B（episode 開始時 1 回の reset joint seed）— p4 裁定（records-backed）

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 16:53:10 JST（date-THEN-write）。
**照会:** `MSG-P11-P4-CLASSB-RESET-20260726-001`（p11・pN 経由）。**対象 code:** `thread_isaac_lab/envs/newton_route_env.py:1088-1097`。
**scope:** records/adjudication のみ。⛔ source 変更・実装・RUN・verify relay・status flip は行わない。

## ⭐ 結論

1. **class B は存続する**（=(1) への回答: `CLAUDE.md:67` の reset 例外は `:72` の下でも arm joint seed に生きている）。**working reading として p11 は設計を進めてよい。**
2. **境界は §2**（joint 状態のみ・1 回・first step 前・制御ループへ持ち越さない・⭐**M-4 target-sync 必須**）。
3. ⚠ ただし **rule text 自体に文言上の緊張**があり、その解消は Rs 専権 ⇒ §4 で上程（**blocking にしない**）。
4. ⛔ **p11 の照会枠より対象が広い** — 同 block は腕だけでなく**グリッパ**を含み、隣接行に **body 書込**もある ⇒ §3 に別 disposition として surface。

## 1. 存続の根拠（私が実読したもの）

| # | 根拠 | 出典 |
|---|---|---|
| G1 | 「`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。例外: …**reset直後の初期化（episode開始時1回）も許可**」= **現行文**。07-21 / 07-26 の pin 裁定でも改訂されていない | `CLAUDE.md:67` ＋ **同一文が** `.claude/rules/prohibited.md:23` |
| G2 | **banked 設計記録**（本 branch 上）: 「**分類 A = per-step control-loop（migrate 必須 = 違反本体）／分類 B = reset/init/restore（許可・現状維持 + M-4 target-sync 追加）**」 | `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md:144` |
| G3 | 禁止の**理由**は「物理破壊防止」＝制御ループ中に solver の出した状態を壊すこと。**reset（first step 前）には壊すべき物理が存在しない** | `CLAUDE.md:67` 逐語 |
| G4 | §0#3 は「**どう駆動するか**」の不変前提。**初期条件の設定は駆動ではない** | `RS71-System-Spec-SSOT.md:27` 近傍 §0#3 / `CLAUDE.md:72` |

⛔ **私が使わなかったもの（訂正）:** 私は当初 `RESET_SEED_MANIFEST` による banked 境界を想起したが、**本 branch には存在しない**（`scripts/` 全体で grep 0 件）。⇒ 引用しない。（存在するとすれば `probe/pd1-arm-pd` 側。）

## 2. 境界（=(2) への回答・working reading）

| 軸 | 可否 | 根拠 |
|---|---|---|
| 回数・時点 | **1 回・reset 直後・first solver step より前** | `CLAUDE.md:67` 逐語「episode開始時1回」 |
| 対象 | **joint 状態のみ**（`joint_q` / `joint_qd`） | :67 は joint-state API の例外。⛔ **body 状態の直接 assign は射程外**（`:72` が FK→physics の body 複写を名指しで不許可） |
| 持ち越し | ⛔ **不可**。1 step 目以降の同種書込は**分類 A ＝ 違反本体** | charter `:144` |
| ⭐ 付帯義務 | **M-4 target-sync 必須** = 許可される reset/restore では**同一 turn で arm ctrl に同じ pose を設定**する。さもないと PD が stale target へ引き戻す（gripper が comp3 R1a で踏んだ罠） | charter `:92`（`newton_route_env.py:1098-1100` 系を precedent として明示） |
| `mj_forward` 等 | **許可された joint seed から body を「導出」する再計算は射程内**／body を**独立に assign** するのは射程外 | ⚠ **私の解釈**（逐語根拠なし）。異論があれば設計側で上書き可 |

## 3. p11 の照会枠を超える所見（silent に承認しない）

1. ⚠ **対象は 28-wide = 腕 ＋ グリッパ。** `_N_ARM_JOINTS = 2 * JOINTS_PER_ARM` = **28**（`:152`）＝ 1 腕 14 = 腕 6 + gripper 8。code 自身のコメント逐語「the **28-wide reset-init** above re-poses the **gripper joint_q**（patched OPEN branch）+ zeroes qd」（`:1099`）。⇒ **指の joint 書込**が含まれる。`:72` は「**指の kinematic close**」を不許可とするため、**「episode 開始時の初期 OPEN 姿勢」と「kinematic close」の区別**が要る。**別 disposition（未裁定・p11/p5 court）**。
2. ⚠ **隣接行に body 書込**: `:1086` `assign_world_states_to_sim(self._state_0, self._solver, bq, bqd, prev)` = reset 時の **body 状態書込**。⇒ §2 のとおり **:67 の joint 例外の射程外**。**別 disposition（未裁定）**。
3. ⚠ **cable joint の seed**: `:1104-1108`（`seed_cable_joint_state`・settled tangents から導出）＝ ケーブルの**初期条件**。⚠ Rs の 2026-07-26「ケーブル全体を固定しないように」は **episode 中の保持（extent）** の話であり軸が違う ⇒ 混同しない。**別 disposition（未裁定）**。
4. ⚠ **guard は本件の証拠にならない**: `scripts/validations/check_control_method.sh` CHECK 10 は `(phys_jq|joint_q|qpos)[...] =` の regex のみで（`:43`/`:48`）、**reset と制御ループを区別しない**。⇒ guard が赤いことは class B 不許可の証拠ではない（DDR #34/#35「guard の述語が世界と合っていない」と同型）。本 branch で `--no-verify` が常態なのはこのため（DDR #35）。

## 4. Rs へ上程する 1 点（§運用10・rule text は Rs 専権）— ⛔ blocking にしない

**文言上の緊張:** `:67` は reset 初期化を**明示的に許可**する一方、`:72` の「⛔**不許可（不変）**」列挙は「腕関節角の直接書込」を**除外条件なしで**挙げている。逐語だけを読むと同一ファイル内で衝突し得る。⇒ **§運用10（CLAUDE.md 内の不整合は実行を止めて Rs へ報告）**に従い上程する。
**私の提案（Rs が採るなら）:** `:72` の不許可列挙に「（⚠ `:67` の reset 直後 1 回の初期化を除く）」に相当する一句を足す。⛔ **私は rule file を編集しない。**
⇒ それまでは **§1-§2 の working reading** で運用する（p11 は待たない）。

## 5. 非主張

- ⛔ §3 の 4 項目は**未裁定**（本書は class B の joint-seed のみを裁定）。
- ⛔ 実装・RUN・verify relay・status flip は行わない・指示しない。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 裁定 = 2026-07-26 16:53:10 JST / RS-TECH-LEAD (`w2:p4`)**
