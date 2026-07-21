# D1.1-B fixture / identity.py の WCJ key-sort 適合性 — OPS-SUP evidence/custody 再測

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 18:34 JST。
**依頼:** `w2:pQ`（事前照会・⛔two-key key 依頼でない）。D1.1-C cycle-3 debate（G-4）で「D1.1-B 凍結 fixture の wcj_bytes + identity.py:80-82 が contracts_v2 §168 の UTF-16 code unit 順に非適合（sort_keys=codepoint 順）」の疑義。
**性質:** evidence（独立再測）+ custody（凍結 chunk 内 *実装* 非適合の手続）。⛔設計判定でない。

## ⭐ VERDICT

1. **§168 spec = UTF-16 code unit 順** を確認（frozen `00192d20ca00b654`:168）。順序反転も empirical に確認。
2. ⚠ **framing 補正（重要）**: **凍結 D1.1-B fixture の wcj_bytes は COMPLIANT**（ASCII-key assert が divergence を empirically foreclose = spec §171 の layer (b)）。**identity.py:82 のみ guard 無し**の別 canonicalizer。⇒ **両 site は「同型」でない・凍結 chunk 内に確認された非適合は無い**。
3. identity.py:82 の §168 非適合は **conditional**（§168 WCJ を名乗らない別 canonicalizer ゆえ）— design question。

## (1) 独立再測（empirical・python3 で encoder を実行）

**§168 spec（frozen `00192d20ca00b654`:168 逐語）:** 「object key sort = UTF-16 code unit 順（`k.encode("utf-16-be")` bytes 昇順）」。**§171:** 「(a) key-sort comparator / raw-WCJ（full-Unicode key・golden vectors の対象）/ (b) typed 入口 `canonicalize()`（**ASCII-key assert**）」= spec 自身が 2 層。

**順序反転（U+FF01 vs U+1F600）= 確認:** utf-16-be `ff01` vs `d83dde00` ⇒ §168 順 = `[U+1F600, U+FF01]`／codepoint(sort_keys) 順 = `[U+FF01, U+1F600]` = **逆**。pQ の technical 主張は正確。

| Site | 実装 | empirical 挙動（非 ASCII key 入力） | 判定 |
|---|---|---|---|
| **1. 凍結 fixture** `wmso_d11b_fixtures/build_goldens.py:194-208`（`c74ca3b36193c638`） | `check()` で **ASCII-key assert**（:198）→ その後 sort_keys | **AssertionError で拒否**（`non-ASCII key at $`）⇒ divergence 到達不能 | ✅ **COMPLIANT**（domain 制限で codepoint==UTF-16・= spec layer (b)） |
| **2.** `identity.py:82` `canonical_json` | **guard 無し** sort_keys=True | **通過し codepoint 順を出力**（`{"！":1,"😀":2}`・key 順 = `[U+FF01, U+1F600]`） | ⚠ **latent divergence**（下記 conditional） |

⇒ **凍結 fixture は「非適合」でない** — ASCII assert が非 ASCII を拒否するので、codepoint/UTF-16 の食い違いは**構造的に起き得ない**。pQ の測定は恐らく guard を外した raw `json.dumps`(:208) 単体か、identity.py 側を測って一般化した（両 site を「同型」とした点が実測と乖離）。

## (2) identity.py:82 の非適合は conditional（design question）

- identity.py の `canonical_json` は **§168 / WCJ / utf-16 を一切参照しない**（grep 0 hit）。docstring = 「canonical UTF-8 JSON (sorted keys…)」の**別 canonicalizer**。用途 = `finetune_cfg_hash`(:111) + handoff-start payload hash(:194) + `harness.py:101` の `payload_canonical_json` 妥当性検査。
- ⇒ **これが §168 WCJ に一致すべきか（→ latent 非適合）／独自 canonical 形として正当か（→ 適合）は design 判定**（pS + pQ）。判断材料 = 「identity.py が hash する artifact が §168 H_WCJ と consistency を要求されるか」。current corpus 全 ASCII ゆえ **どちらでも latent**。

## (3) custody 手続 — 凍結 chunk 内の *実装* 非適合（pQ 質問②）

**本件では前提が成立しない**（凍結 fixture は compliant）。⇒ 「凍結 chunk 内非適合の手続」を発火させる対象は無い。identity.py:82 は source code で「凍結 D1.1-B chunk 内」の framing 外・かつ非適合が conditional。

**一般解（*実装* 非適合が実在した場合・前回 07-21 14:53 の 5 段との差分）:**
- **5 段は適用**（①凍結を編集しない ②別記録 ③軸で route ④Rs 上程 ⑤LEDGER flag）。凍結 pin を壊さない原則は同一。
- ⭐**差分 = 深刻度と route 先**: *理由づけ* 疑義は artifact の**挙動を無傷**にする（justification のみ問う）。*実装* 非適合は**凍結 code が凍結 spec に反する内部矛盾** = certify が spec-code 乖離を見落として凍結した、を意味する ⇒ **より重い**。route = pS（spec と code のどちらが権威か）+ impl owner。
- ⭐**conservatism（latent vs live）**: **latent**（current corpus が触れない・本件の非 ASCII の如く）= 今は正しい出力・domain 拡大時のみ乖離 ⇒ 次 version bump の defect として記録・即時性低。**live**（current corpus が触れる）= 凍結 package が実際に非 canonical 出力 ⇒ 高緊急・即 re-freeze 検討。
- **訂正は Rs 認可の version bump のみ**（凍結 code 直編集は pin=baseline 破壊）。

## 非主張

- ⛔ identity.py の canonical_json が §168 に一致すべきか = design（pS + pQ）。本 leg = 実装の実挙動の evidence + 手続。
- ⛔ fixture が ASCII 限定ゆえ §171 layer (a)（full-Unicode golden vectors）を fixture 単体で供給できない点は **test-coverage の設計論点**（pS）— 「出力が非適合」とは別。
- ⛔ 凍結/source file は本 leg で一切編集していない（read-only + 別環境での encoder 再現のみ）。

---
**evidence/custody = 2026-07-21 18:34 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
