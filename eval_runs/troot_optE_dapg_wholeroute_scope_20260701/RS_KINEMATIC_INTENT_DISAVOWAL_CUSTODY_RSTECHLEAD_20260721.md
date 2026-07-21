# Rs kinematic-intent clarification +「すてるなよ」disavowal — custody provenance

**記録者 (witness):** p4 (RS-TECH-LEAD)。**直接 witness** — Rs が p4 に本セッションで直接発話（relay でない）。
**発行:** 2026-07-21 19:07 JST（date-THEN-write）。
**目的:** realize-form 追記の revert + §0.5 supersession の *authority* を記録する。この authority は Rs の発話ゆえ、未記録だと元問題（未確認発話の上に governance を築く）の鏡像になる。pY flag = `CLAUDEMD_REALIZE_FORM_REVERT_CLOSURE_OPSSUP_20260721.md`（sha256 `a80a3da1253fd0da` @ `35165a040d`）gap ①。

## Rs 逐語（受領文脈つき・発話順）

1. **「わからない」** ← p4 の質問「この reword 執行は認可でしたか？」への応答。
2. **「「すてるなよ」ルールなどしらない」** ← p4 の premise-collapse 報告（「すてるなよ」は p11-relay で p4 が Rs 直接確認しておらず、realize 形 rule はこれに依拠。元に戻してよいか）への応答。
3. **「許可されていない箇所にkinematicを使うなということ」** ← p4 の言い直し報告への応答。Rs が意図を明示。

## 帰結（この authority が支えるもの）

- ⇒「すてるなよ」= Rs は rule として **disavow**。Rs の意図 = **既存 invariant「許可されていない箇所に kinematic を使うな」= RS71 §0#5**（新規 rule でない）。
- ⇒ realize-form 追記を revert:
  - CLAUDE.md:72 = `3ef4814f30`（追記前 `f45670929e` と byte 一致・pin 例外 intact）
  - prohibited.md bullet 削除（gitignore・working tree）
  - LEDGER:35 = p6 `a80184b05c`（realize 形 2 層を revert-record 化）
  - MEMORY.md:20（realize 形詳細 revert・residue grep 0）
  - pY 独立確認 = `35165a040d`（byte-identical PASS）

## 射程外（触れていない）

- **clip-retention pin 例外そのもの（§0#5・clip だけ kinematic 可）は不変** — 別経緯（`log.md:6534` 2026-06-16 + 07-15 banked + 07-21 receipts）。Rs の「許可されていない箇所に」は「clip = 許可された箇所」と consistent。
- **P-1（腕・指の物理を捨てない）の *content* は §0#5 に subsume**（物理無視トリック禁止と同義）。「すてるなよ」への *attribution* のみ除去。P-1-as-named-principle が disavowal の射程かは p4/p11 判定事項（p4 判定 = attribution 除去・content は §0#5 経由で保持）。§0.5 doc（`ARM_CONTROL_FORWARD_DESIGN_SCOPE_ARMCONTROLDESIGN_20260721.md:27`）の supersession flag = p11 court（p4 通知済）。

## 元の「すてるなよ」の provenance（p11 訂正・2026-07-21 19:10 反映）

発話は **捏造でなく実在** — Rs の user-turn として p11 のセッションに **直接** 出現（p11 attests: transcript line 535 / role=user / 2026-07-21 13:48:37 JST）。p11 が p4 へ relay（「p4 にわたして」）。⇒「p11 relay」は *伝播経路* として正・ただし「p11 へ relay された（二次受領）」は誤りで、p11 は直接受領した。p11 の transcript は p11 court の attestation（p4 は別 session ゆえ独立検証せず・p11 の記録として引用）。

## discipline（根本）

**p4 の誤りの核心 = 発話の有無でなく、実在するが casual な発話を、*それが governance rule として意図されたか*を Rs に確認しないまま CLAUDE.md rule へ elevate したこと**（§15 records-must-match-fact:「human が X を決定」は伝播前に verbatim + intent 照合 / 三原則#1「CLAUDE.md 変更は Rs 指示時のみ」）。本 doc は disavowal の authority を verbatim で記録し、鏡像（authority 未記録）を回避する。

---
**custody provenance = 2026-07-21 19:07 JST / p4 (RS-TECH-LEAD)**
