# 設計原則の再接地 — 名前付き原則「P-1」を取り下げ、§0#5 へ接地し直す（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** 訂正 — **proposal**（landing = p4）。
**契機:** p4 → p11 接地更新（STOP）2026-07-21 18:56:25 JST — **Rs が当該 rule を disavow**（p4 relay 逐語「そんなルール知らない」）。意図 = 既存不変前提「許可されていない箇所に kinematic を使うな」。
**上流の処置（p11 実測）:** `CLAUDE.md` の realize 形追記は **revert 済** = `3ef4814f30`（2026-07-21 18:55:04・`git show` で確認 = `CLAUDE.md` 1 file / realize 形 (a)(b) を削除 / **pin 例外と不許可列挙は不変**）。

---

## 1. 何を取り下げるか（1 行）

**名前付き原則「P-1」を取り下げる。** 以後、私の設計文書は **「すてるなよ」を authority として引かない**。

## 2. 何が変わらないか — 設計上の帰結は §0#5 が元から要求している

制御ループ内で **solver の出した状態を捨てて保存値を書き戻す形**（`_pp` 式）を採らない、という**設計の向きは不変**。根拠は逐語でなく不変前提:

- `04-Specs/RS71-System-Spec-SSOT.md:27` 逐語: **NO KINEMATIC TRICK — physics-faithful only; the ONLY authorized exception is the clip-retention pin**
- `.claude/rules/prohibited.md:19`「kinematic トリック（物理を無視したテレポート・強制配置＝アーム関節角の直接書き込み等）禁止。唯一の認可例外 = clip-retention pin（§0#5）」
- `CLAUDE.md:72`「⛔不許可（不変）= 腕関節角の直接書込 / 指の kinematic close / `update_kinematic_bodies` / weld・cable-finger attachment」

⇒ **腕の `_pp`（関節角 直接書込）は不許可列挙に名指しで載っている。** ケーブル全 DOF の毎ステップ書き戻しは、認可例外（clip-retention pin = **clip 側がケーブルを保持する機構**）**より広い**ため `physics-faithful only` に反する。**どちらの結論も「すてるなよ」を必要としない。**

⚠ **読み方の 1 点（p4/Rs 判断を要する）**: 本書は §0#5 を **述語**（逐語 `physics-faithful only`）として読み、不許可列挙を**その例示**として扱う。**閉じた列挙**として読む場合、列挙に名前が無い形（例: ケーブル全 DOF の書き戻し）は都度 Rs 確認が要る。⇒ **どちらの読みかは私の court 外。** 現行設計はどちらの読みでも同じ結論になる（腕 `_pp` は列挙に載り、ケーブル全 DOF 書き戻しは pin 例外より広い）。

## 3. 私の誤りの形（記録・再発防止のため形で書く）

| # | 形 | 実体 |
|---|---|---|
| (a) | **receipt を norm に格上げした** | Rs のその場の応答（4 文字）に**名前を与えて standing な原則**にし、設計文書 → p4 → **L3 rule file** まで流した。⚠ 本 project は同じ区別を**同日に裁定済** — `00-DESIGN-STATUS-LEDGER.md:35` 逐語「**receipts は統一の対象外**… 発話の記録であって規範文ではない」。私は**受け手側で**同じ境界を踏み越えた |
| (b) | **造語を作った** | 「P-1」は一般語でも定義済技術語でも正式名でもない（global CLAUDE.md「造語を作らない」）。⚠ さらに同 label を v0.4 の**手続き段**（P-0〜P-4）にも使っており、**同一文書群で 2 義**になっていた |
| (c) | **規則かを確かめずに標準へ流した** | 「これは規則として言われたのか」を Rs に確認しないまま、rule file に到達する経路へ載せた。⭐ **必要だった 1 問 = 「これは今回の指示か、以後の規則か」** |

## 4. provenance の注記（訂正提案・p4 / pY 宛）

revert commit message は当該追記を「propagated from an **unconfirmed p11 relay**」と記す。

- ✅ **伝播経路（p11 → p4 → rule file）は正しい。** ✅ **`unconfirmed`（Rs に規則か確かめていない）も正しい。**
- ⚠ **ただし発話自体は p11 が直接受領した user turn** であり、p11 へ relay されたものではない。実測 = session transcript `ba047d22-6836-4710-8c35-f9a5badf9762.jsonl` **line 535 / role=user / 2026-07-21T04:48:37.800Z（= 13:48:37 JST）**、逐語「毎回捨てて同じ値に戻すので、変化が積み上がらない。」すてるなよ」。

⇒ **記録の正確さのためだけの注記であり、disposition に異議はない**（取り下げる）。
⚠ **発話 receipt 自体は消さない** — `00-DESIGN-STATUS-LEDGER.md:35` の教訓（c73 §5 逐語「実際に人間の発話を消す寸前だった」）。**receipt として保持し、authority としては引かない。**

## 5. 反映（本 commit・p11 所有 doc のみ）

| file | 前 | 後 |
|---|---|---|
| `ARM_CONTROL_FORWARD_DESIGN_SCOPE_…:25-38`（§0.5） | 「設計原則（Rs 直接指示）」+ 原則 P-1 | **§0#5 への接地**へ書き換え。逐語は §0.5 末尾に **receipt（authority でない）**として残置 |
| `ARM_CONTROL_FORWARD_DESIGN_V02_…:5` | 「原則: P-1 =…（Rs 逐語「すてるなよ」）」 | 「§0#5 `physics-faithful only`」 |
| `ARM_CONTROL_PD1_PREREG_V14_…:86` | 「P-1 物理結果を捨てない（Rs「すてるなよ」）」 | 「§0#5 `physics-faithful only`」 |
| `SEC_14_27_CORRECTED_…:126,156,170`（Δ E） | disposition 根拠 = Rs 逐語 | disposition 根拠 = **§0#5 例外 scope 超過**（元から並記していた根拠）。逐語は receipt 表記へ降格 |

⚠ 他の P-1 言及（V02:16-19,136 / V03:4,72 / prereg:30）は**参照語の置換のみ**（技術内容は不変）。
⚠ `ARM_CONTROL_FORWARD_DESIGN_V04_…:52` の `P-1` は**手続き段の番号**であり本件と無関係（改名しない）。
⚠ 現行 live 成果物 `ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_…`（v1.1 `37902fb909`）は **当該原則を引いていない**（`grep` 0 件）⇒ **無変更**。

## 6. 未処置（p11 の court 外・通知のみ）

| 面 | owner | 状態 |
|---|---|---|
| `CLAUDEMD_REALIZE_FORM_L3_CUSTODY_VERIFY_OPSSUP_…` / `…LANDED_RECONFIRM_OPSSUP_…` | pY | 逐語を authority として引用中 ⇒ **通知のみ** |
| `00-DESIGN-STATUS-LEDGER.md:35` の realize 形 (a)(b) 記述 | p6 | 同根 ⇒ **p4 経由で通知** |
| §0#5 の読み（述語 or 閉じた列挙） | p4 / Rs | §2 の ⚠ 参照 |

## 7. 非主張

- 本書は §0 不変前提を**解釈も変更もしない**。設計 owner の読みと、その読みが p4/Rs 判断を要する箇所を明示するのみ。
- Rs の disavow 逐語「そんなルール知らない」は **p4 relay**（p11 直接受領ではない）。
