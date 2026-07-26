# Rs 裁定 2 件 — custody（逐語・受領文脈・帰結）

**記録者:** RS-TECH-LEAD (`w2:p4`)。**私は直接の witness**（relay ではない — Rs から p4 への直接 turn）。
**発行:** 2026-07-26 16:33:07 JST（date-THEN-write）。
**対象:** 私が 2026-07-26 16:04 に Rs へ上げた 3 件のうち **1 と 2**（3 = 私の handoff 追記の可否・下記 §3）。

---

## 1. pin（私の item 1）

**Rs 逐語:**
> 1 クリップのケーブル固定ではkinematicを残す。それ以外ではkinematic禁止

**受領文脈:** 私が「**1. pin** — (i) 残す（§0#5 のまま）/ (ii) 消す（＋ cable モデル or task 表現の変更）」と番号付きで列挙した直後の Rs 直接応答。冒頭の「1」= **私の列挙番号 1（＝ pin）**と読む。

**disposition = (i) 残す。**

- ⭐ **これは既存 §0#5 の再確認であり、新規 rule ではない。** 現行文が既に同内容: `04-Specs/RS71-System-Spec-SSOT.md:27`（§0#5）「physics-faithful only; **the ONLY authorized exception is the clip-retention pin**」／`CLAUDE.md:72`「**kinematic の認可例外は clip-retention pin の 1 件のみ**」＋不許可列挙／`.claude/rules/prohibited.md` 同旨。⇒ ⛔ **規則ファイルの編集は不要**（文言追加もしない）。
- ⛔ **本裁定は realize 形（機構）を定めていない。** 逐語が述べたのは **可否のみ**（残す／それ以外は禁止）。⇒ equality 等の具体機構を本裁定から導出しない。**2026-07-21 の over-elaboration（casual な発話を機構規則へ昇格させ、後に Rs が disavow して revert した件）の再発防止として明記する。**
- ⚠ **語の範囲:** 「クリップのケーブル固定」= **clip 側がケーブルを保持する機構**。⛔ **gripper の把持ではない**（`CLAUDE.md:72` の既存注記どおり。工程表の「クランプ」は gripper 動作を指す語なので流用しない）。
- **帰結:** 07-19 の「完全削除（pin 含む）」読みは決着（07-21 裁定 B に続き、**Rs 直接で再確認**）。⇒ **腕側の kinematic は禁止のまま** = 毎 substep の関節角直接書込（`test_newton_clip_routing.py:1815-1838`）・`update_kinematic_bodies`（`:1752`）は削除対象。**controller-driven 設計（p11 v1.0 の方向）を継続**。
- ⛔ 実装・RUN は本書では行わない（pN operative state で CLOSED）。

## 2. fingertip 定数（私の item 2）

**Rs 逐語:**
> 2　は私が判断することではない

**受領文脈:** 同じ列挙の 2（`EE_TO_FINGERTIP=0.220` = Franka legacy vs 実測コ字 `0.2757`・`GRASP_Z` が 0.220 を使用）への応答。

**disposition = Rs は判断しない ⇒ 設計 lane の court。**

- ⛔ **私（p4）の原因部分 — own して撤回する:** 私はこれを「**Rs の判断待ち 3 件**」の 1 つとして Rs の plate に載せた（16:04 報告、およびそれ以前の relay）。**その framing を撤回する。** 設計判断を human へ上げる前に、court が本当に Rs か（＝不変前提の *変更* か、単に前提下の数値是正か）を私が判別すべきだった。
- ⚠ **p5 の disposition は前提が falsify された:** `P5_ESCALATION_fingertip_offset_franka_legacy_20260721.md` @ `454db0f866`（sha256 `0aa784c9a7b6b948`）は「(i) §0#4 コ geometry LOCKED に属す (ii) `GRASP_Z` が load-bearing ⇒ **Rs 専権 + /reward-design gate**」を理由に Rs escalate としたが、**Rs 逐語がこれを否定**。⇒ **p5 へ RETURN**（cause-side 規則: 発見側は相手の record を代理編集しない）。p5 が自分の disposition を訂正し、設計 lane 内で決める（該当する設計ゲート経由）。
- ⛔ **私は内容を決めない**（設計 = 設計 lane の court）。私が言えるのは routing のみ。
- **非 blocking:** p11 は H-4 を **3 参照点**（`0.220` / pad / `0.2757`）で出力する設計にしており、**どちらに決まっても再測定は不要**。⇒ 誰も待たない。

## 3. handoff 追記（私の item 3）— 記録のみ

**Rs 逐語:** 「3　削る」 ⇒ **執行済**。`handoff_cc_p4_rstechlead_control_method_20260719.md` の :11-16（6 行・通信経路ブロック）を削除。513→507 行、sha256 `eec4eeaf3b9f58e0…` → **`b0838e2ad6d079ec132c3eb765e4526fdcc69c611dd37b3684cd79379fa4a934`**、削除前 backup を同ディレクトリに保持。⚠ 当該 file は git 管理外（IsaacLab repo 非該当）。pN の凍結条件「ユーザー判断まで」が判断到達で解除されたため執行した。

## 非主張

- ⛔ status flip / LEDGER 更新は本書で行わない（p6 court・pN 経由）。
- ⛔ 実装・RUN・verify relay は行わない・指示しない（pN operative state）。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**custody = 2026-07-26 16:33:07 JST / RS-TECH-LEAD (`w2:p4`)**
