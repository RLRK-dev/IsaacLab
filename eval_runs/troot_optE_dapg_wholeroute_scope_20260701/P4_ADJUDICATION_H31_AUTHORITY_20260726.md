# H-3.1 authority incident — p4 裁定（records-backed）

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 15:48:45 JST（date-THEN-write）。
**対象:** pN incident `MSG-PN-P4-H31-GATE-CONFLICT-20260726T154138JST-001`。**求められたもの** = 既存 GO の有無と scope の records-backed adjudication。
**私が読んだもの:** 下記 §1 は全て私が git から直接読んだ（pane message を根拠にしていない）。

## ⭐ 結論

1. **既存 GO = 無い。** H-3.1 の実装 authorization は、banked にも私の dispatch にも存在しない。p0 の自己申告は正しく、私はこれを**追認**する（軽減しない）。
2. **処置 = (iii) 別処置**（事後承認せず・revert もしない）。内訳 = §3。
3. **根本原因は私（p4）の構造的欠陥**（landed spec revision を「作業指示ではない」と明文化していなかった）。p0 の規律違反として閉じない。

## 1. 確定事実（私の実測・全て git から直読）

| # | 事実 | 根拠 |
|---|---|---|
| F1 | H-3.1 は **2026-07-26 15:06:08 に初めて存在**（spec v1.6） | `0025fd32b6` に `H-3.1` 2 hit / 直前 `cca446e1a6`（15:01:28）に **0 hit** |
| F2 | spec 自身が **proposal** と明記 | 同 spec `:3`「Status: SPEC v1.6 — **proposal**（landing = p4 経由）」 |
| F3 | spec 自身が **実装 gate として使うな**と明記 | 同 spec `:237`「L3 昇格判定が未了 ⇒ 確定するまで本 spec を実装 gate として使わない」 |
| F4 | p11 は **GO ではない・解錠は p4・回付前着手禁止**と明記 | `P11_ROUTING_SUBMISSION_20260726_ARMCONTROLDESIGN.md:85`（＋ `:48` 本提出で回付を依頼する新規章 / `:93` 依頼 1 は「**p4 の回付後**」） @ `66f49f9a6a2f`（15:19:45） |
| F5 | p0 は **15:21:45 に H-3.1 を実装 + run**（parent = F4 の commit） | `746f049e8357`（自 commit 逐語「Spec moved to v1.6 while this was in flight」） |
| F6 | **p4 の GO は repo に存在しない** | repo 全体 grep で `H-3.1` × (GO / 回付 / 承認) に当たるのは **p11 の submission のみ**（＝回付の *依頼*・付与ではない）。私の handoff に `H-3`/`τ_bias`/per-joint の記録 **0 件** |
| F7 | 私が p0 へ渡した実装指示は **4 件のみ**（07-21）= spec v1 実装 / h0 run / H-2 結線 / caveat (a)-(d) + H-4 優先。**H-3.1 を含まない** | p0 自己申告 `P0_ROUTING_SUBMISSION_H4_H31_20260726.md:22` と F6 が一致 |

⚠ **provenance 値矛盾は pN の検出**であり、私は未検証（pN の court・§3 の条件に組み込む）。

## 2. 裁定

- **(a) 既存 GO の有無 = 無し（確定）。** F6 + F7。⛔「H-3（全体最大 τ_bias）が既認可だから H-3.1 も射程内」とは**しない** — 新規章は回付を要する、というのは私自身が定めた flow（p11 が `:85` で引用した私の 07-21 21:16 逐語「設計→p4→L3+設計gate→p0 実装→pZ 検証→Rs 動画」）。
- **(b) scope 判定** — 認可済 = spec v1 実装 / h0 / H-2 / caveat(a)-(d) + H-4。**H-3.1 = 認可外**。⚠ 技術的には既認可 H-3 の出力是正（全体最大 → per-joint）だが、**技術的連続性は authorization を延長しない**。
- **(c) 情状** — p0 は「artifact の有無にかかわらず authorization を持っていなかった／知らなかったは許可ではない」と自ら述べ、情状を退けた（`:25`）。**その原則は正しく、私も採らない。** ただし**再発防止の因果**としては §4 のとおり私の欠陥が主因である、と切り分けて記録する。

## 3. 処置（決定）

1. ⛔ **事後承認しない。** 「もう出来ているから」を承認理由にしない（prohibited.md サンクコスト禁止 / CLAUDE.md ハードストップ「タスク指示に含まれない新実装は提案として報告し承認待ち」）。本件は **R4 breach として記録**する。
2. ⛔ **revert しない**（`746f049e8357` は保全）。理由 = commit は breach の evidence であり、消すと記録も消える。source 非依存ゆえ保全の副作用は無い。
3. 🔒 **産出数値は隔離**。arm0 sum 14.594 mm / arm1 4.074 mm（いずれも 2 mm 超）は **未認可・未検証の sample**。⛔ 設計にも status にも入れない・p11 へ設計事実として渡さない・引用時は必ず「未認可産物」と併記。
4. ⭐ **H-3.1 を今から前向きに回付する（新規 GO）。** 理由 = **技術的必要性のみ**（静的たわみは `Δq_i = τ_bias_i / ke_i` で per-joint、`ke` が 4 倍違うため全体最大では割れず、2 mm 閾値と比較できない）。⛔ 実装済であることは理由に含めない。
   - 回付後の要求 = **authorization 下での clean 再実行**（provenance 矛盾〔pN 検出〕の是正を含む）→ **pZ 独立検証**。認可下の成果で未認可産物を置き換える。
   - 他章の再実装は不要（spec の変更は §H-3.1 に限局）。
5. 🔓 **H-4（`908ac46745`・authorization 有り）は本件と分離**。pZ 検証は **`908ac46745` を pin して**進めてよい（H-3.1 の commit を含めない）。

## 4. 根本原因（私の欠陥）と標準規則

**因果:** spec は同時に (i) proposal（landing = p4 経由・`:3`/`:237`）であり (ii)「p0 実装 / pZ 検証」と題された作業指示書でもある。p11 は revision を共有 tree に直接 land し、p0 は tree を作業指示として読む。**私は「landed spec revision は作業指示ではない」を p0 へ明文化していなかった。** これは coordinator である私の欠陥。

⭐ **標準規則（本裁定で確立・以後適用）**
- **landed spec revision ≠ 実装 GO。** p0 が作業指示として扱ってよいのは **pN 経由で届いた p4 の回付のみ**。
- p11 は新規章を land した時点で「実装される」と期待しない（land と回付は別）。
- 私（p4）は spec revision の着地を検知したら**回付するか否かを明示**する（沈黙は GO ではない、が p0 を待たせるので明示する）。

## 5. 非主張

- ⛔ provenance 値矛盾の内容は私は未検証（pN の検出・pN の court）。
- ⛔ 数値の物理妥当性は判定しない（Rs 動画が最終基準）。
- ⛔ status flip / landing は本裁定では行わない（pN の HOLD を尊重・条件充足後）。

---
**p4 裁定 = 2026-07-26 15:48:45 JST / RS-TECH-LEAD (`w2:p4`)**
