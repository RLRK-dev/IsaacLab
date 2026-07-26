# Rs 確認 — pin の**範囲**制約（固定点のみ・ケーブル全体を固定しない）

**記録者:** RS-TECH-LEAD (`w2:p4`)。**直接の witness**（Rs → p4 の直接 turn・relay でない）。
**発行:** 2026-07-26 16:42:35 JST（date-THEN-write）。
**関係:** `P4_RS_RULINGS_20260726_PIN_AND_FINGERTIP.md`（@ `5d87b3a1fb`）§1「pin = 残す」の**範囲の明確化**。⛔ 同 artifact は改変しない（本書が追補）。

## Rs 逐語

> 確認だがクリップでケーブルを固定しても固定点だけ動かなければいいだけで、ケーブル全体を固定かしないように

**受領文脈:** 私が §1（pin = 残す・可否のみで機構は未定）を報告した直後の Rs 直接応答。「確認だが」= 私の理解の確認として発せられた。

## 制約（私の読み）

- **認可される範囲 = 固定点のみ**（clip 着座点のケーブル 1 箇所が動かなければよい）。
- ⛔ **ケーブル全体の固定は不可**（40 節すべてを止める形は認可の範囲外）。
- ⚠ これは **extent（どこまで止めるか）の軸**であり、§0#5 の「pin は clip seat でのみ発火」（`RS71-System-Spec-SSOT.md:27`）が定める **location の軸**を、より鋭くしたもの。⛔ 実現機構は依然として本裁定の対象外（§1 と同じく可否・範囲のみ）。

## ⭐ 現行実装は既に本制約を満たす（私の実測・read-only）

| 論点 | 実測 | 出典 |
|---|---|---|
| 何を止めるか | **cable body 1 個のみ**を world へ connect | `test_newton_clip_routing.py:1403` 逐語「**PER-CLIP (ONE body), NOT the (a) whole-cable `jq[ARM_Q:]` freeze**」 |
| 事前確保 | cable body ごとに **1 個ずつ disabled な connect eq** を用意（route で cable が動くため、実行時の着座 body を位置一致で選べるように） | 同 `:1406-1409`（全て `enabled=False` = `eq_active0=0` で不活性） |
| 実行時 | **ちょうど 1 個だけ activate**（着座 body に一致した `best`）＋ readback 検証 | `route_executor.py`（`eq_data[best]` に anchor 設定 → `eq_active[best]=1` → 読み戻し不一致なら `RuntimeError`） |
| 発火条件 | 検証済 C1 着座後のみ（pre-seat 活性は禁止）・**default off** | `test_newton_clip_routing.py:1401-1405` |

⇒ **ケーブル全体を止める形は現行の active path に無い。** Rs が排除した「全体固定」は `jq[ARM_Q:]` 形であり、コメント自身が**採らない形**として名指ししている（出所は旧 probe `r_s71_clip_dropin_72.py`）。⚠ 2026-07-21 に私が報告した `_pp` の全 DOF 書き戻しも **probe script 側**の形であって、route の pin 機構ではない。

## 帰結・非主張

- **新規の是正作業は発生しない**（実装は既に準拠）。⇒ 誰にも実装依頼を出さない。
- ⛔ **規則ファイルは編集しない。** 本書は custody。恒久規則として rule file に明記するかは **Rs の指示待ち**（「今回の確認か、以後の規則か」を私が勝手に決めない — 2026-07-21 の over-elaboration 再発防止）。
- ⛔ status flip / LEDGER 更新なし（p6 court）。source 変更・RUN・verify relay なし（pN operative state で CLOSED）。
- ⚠ 将来 pin を再実装・移植する場合、**本制約（1 点のみ・全体固定不可）が受入条件**になる。⇒ p11（設計 owner）へ回付する。

---
**custody = 2026-07-26 16:42:35 JST / RS-TECH-LEAD (`w2:p4`)**
