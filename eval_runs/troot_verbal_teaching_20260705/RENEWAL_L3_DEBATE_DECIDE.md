# RENEWAL_PLAN 5体 L3 debate — REBUT_OR_ACCEPT + DECIDE

**対象:** `RENEWAL_PLAN_07DESIGN.md` v0.1(commit `a887ed921f`)。CC1 = p5。CC2-5 Challenger + CC6 NHA、独立 context 並列(2026-07-11 00:4x-01:0x)。
**Node:** T-ROOT-DesignDoc-Renewal-20260711。full 挑戦文 = 本 session transcript(agent 出力)— 本 doc は disposition 記録(要旨 + 判定 + fix group)。CC1 spot-check(§運用28): (Rs-confirm) LEDGER:42/:121 / LEDGER:60 行 cite 2 本 / U+2212 :1368-1380 / v3.2 patch-stack frontmatter = **4/4 CONFIRMED**。

## DECIDE: **FAIL → v0.2 改訂必須**

方向性(Rs directive 準拠の刷新 / batch 構造 / rename ゼロ / immutability 原則 / step-0 順序 / inventory 完全性・数値正確性)は複数 challenger が VALIDATED。しかし **CRITICAL 3(CC2)+ HIGH 12+ が ACCEPT** — 全て packet 改訂段階で修正可能、方向棄却なし。

## 収束点(3+ 体が独立指摘 = 最優先 fix)

1. **LEDGER「触らない」vs「cite 同 batch 更新」の矛盾**(CC3-C3 / CC5-C8; LEDGER:60 に実 cite)→ §3.4 = 「構造刷新から除外、cite-currentization + status write-back は governance flow(p6/%12)で実施」。
2. **VGroove ' M' の absorb process**(CC4-C4 / CC5-C7 / CC2-C10)→ §9 分割(4a tracked化 / 4b ' M')+ **verbatim hunk を packet に掲載** + pane 宛 claim broadcast 先行 + **推奨 = revert + anomaly 記録 + banner pointer 化**(commit-as-currentization は代替 B; origin = Rs 本人の可能性も注記)。
3. **banner = 「mirror」は二重管理**(CC4-C2 / CC4-C6 / CC2-C5; LEDGER:119 pointer-only 設計)→ banner = status-class + as-of snapshot 日付 + LEDGER row pointer(維持される mirror ではない)+ allowed-additions 事前登録。

## Disposition(全 findings)

### CC2(invariance)— C1/C2/C3 CRITICAL, C4-C7 HIGH, C8/C9 MED, C10 LOW: **全 ACCEPT**
- C1 swap-blind + Mechanical-Specs 行検査ゼロ → **fix 本命: 宣言 canonical 領域(§2 :1226-1459 + D-1 注記 + Mech-Specs canonical 表列挙)は verbatim block-hash、残部は partition-aware multiset**。
- C2 active→HISTORICAL 移動が素通り + **D-1「上記」= 位置参照**(並べ替えで剥離)→ partition-aware manifest(canonical 値は ACTIVE 区画に存在必須)+ D-1 anchor 明示化(batch C 内、Rs-approved manifest 下)。
- C3 sha anchor / 決定 verbatim 未検査(node の canonical 定義 3 種中 1 種のみ)→ hex-token class `[0-9a-f]{8,64}` 全文字列比較 + 決定 block verbatim hash。
- C4 表 parse 仕様が実表と不一致(z 列なし・6 分割表・§2.2 の `**`/`(h)`/`→` marker 意味論)→ block-hash に包摂。
- C5 **義務 banner 追加が multiset FAIL を内蔵**(92.2 等)→ pre-registered **ALLOWED-ADDITIONS list**(除外 list と同時に事前 commit)。
- C6 「pre-registered」の enforcement 点なし(起草者=執行者=gate 運転者が同一 pane)→ **除外/許可 list + script を刷新起草前に commit + %12/Rs review + script sha pin**。
- C7 U+2212(:1368-1380 実在確認)→ sign class `[-+−]` + 正規化表を事前登録 spec に。
- C8 除外 regex 衝突(ISO 時刻断片 / sha 内数字 / canonical 注記内 cite)→ context-anchored 除外のみ。
- C9 **P-full は multiset 恒真 FAIL = gate 実行不能** → §3.2 に明記(P-light を実質強化; P-full 選択時は presence-based 別検査の別途設計 + 別 debate)。
- C10 batch 0 の ' M' = 値変更で「全 batch 値変更ゼロ」が偽 → 収束点 2 の解決に従属(revert 採用なら消滅 / commit 採用なら明示 carve-out)。

### CC3(cite/map)— C1/C3/C4/C5 HIGH, C2/C6/C7 MED/LOW: **全 ACCEPT**
- C1 regex 取り漏れ(bare-§ 19 hits / **task_config.py:357 の L462-581 形式 = 刷新前から stale** / 逆順 / html・txt で全 repo 74 / memory 13 file)→ **pre-registered regex SET** + 全 repo 全拡張子 + memory は report-only sweep。task_config:357 既存 stale cite = 独立の小修正候補として %12 へ報告(刷新と分離)。
- C2 rename-zero は P-light 条件付き → policy 条件明記 + P-full 選択時 contingency(v3.2 へ in-place 統合 = 名前保存)。
- C3 → 収束点 1。
- C4 live/banked 境界判定不能(工程表自身が eval_runs 内で live = path 則破綻、8 file 無所属)→ **3 列 disposition ledger(file × {LIVE/BANKED/OUT-OF-SCOPE} × decided-by)、p5 分類 → %12 verify → Rs 承認**。
- C5 §番号後方互換が ill-defined(§4.2 重複 :2537/:2539 / 冒頭 ~1,000 行無番号 preamble / **preamble 移設 ⊥ 行安定は相互排他**)→ **§ canonicalization table(old heading@line → new §ID)を cite map の一部として事前登録** + 相互排他は Rs/5体判断事項に昇格。
- C6 map の currency 機構なし → map = tracked live file、doc sub-revision と 1:1(header に doc sha⇄map version)、anchor = §ID のみ、banner に map pointer、freshness check。
- C7 count drift + frozen doc cite = MAP-ONLY class → 反映。

### CC4(disposition/権限)— C1/C2/C3 HIGH, C4 MED-HIGH, C5/C6 MED, C7/C8 LOW: **全 ACCEPT(C4 は PARTIAL = 選択肢分割)**
- C1 **「(Rs-confirm)」脱落** — :42 は未批准 draft 判定(:121-122)→ full token 表記 + §9 に「:42 MIXED を今批准するか」optional 追加。
- C2 :42 caveat の cherry-pick(mechanism-QUARANTINED を結果数値に誤帰属 / as-scoped 脱落 等)→ paraphrase 削除、banner = row snapshot(C6 の as-of 形式)。
- C3 **PoseEst = 線形 supersession でなく base+patch-stack**(v3.2 frontmatter「v3 remains parent」「open v3+v3.1+v3.2 together」= CONFIRMED)→ banner 2 class(v1/v2 = whole-SUPERSEDED / v3・v3.1 = 部分 supersede・head 構成要素・normative 継続)+ head に composite 読解契約。**B-minimal を正当化する追加根拠**。
- C4 ' M' commit は Rs-専権 write の無署名 edit absorb(Vault Write Permissions:27)→ PARTIAL: 「violation」とまでは未確定(origin = Rs 可能性)だが process 論点は成立 → 収束点 2 の選択肢分割で Rs 判断。
- C5 VGroove banner に :57 と矛盾する別の stale 主張(swap deferred 記述 vs COMMITTED 85315bbec6)→ batch A で dated staleness pointer 追加。
- C6 → 収束点 3。
- C7 guardrail ③「ACTIVE のみ」vs 適用「FAILED/DISCARDED 混在なし」の不一致(head = PARKED)→ 文言修正「non-FAILED/non-DISCARDED 系譜のみ」。
- C8 S1B 復活禁止は substrate-scoped(:65-74 verbatim; 「cable retention は Newton で infeasible ではない」保存)→ blanket 禁止でなく scoped list verbatim。
- 観察(刷新対象に ACTIVE 設計 doc ゼロ — GD-KoShape は 06-Knowledge)→ §9 に charter 解釈 1 行(Rs 意図確認)。

### CC5(process)— C1/C2/C4/C6 HIGH, C3/C5/C7/C8 MED: **全 ACCEPT**
- C1 層5 が batch 0/A/B で欠落(CLAUDE.md 3+file 機械トリガー、CC 判断非依存)→ 層5(最低 SSOT lens)を A/B に拡張、batch 0 は loud 免除記録 or lite pass を packet 内で宣言。
- C2 L3 事後 層2 が chain に不在 → post-batch-C focused challenger pass(ST2 精度先例の変種)を §7 に明記。
- C3 step-0 sha の執行時 re-verify 契約なし → full-sha 再検証 + mismatch = STOP + Rs へ delta 報告 + full 64-hex を commit message に。
- C4 **一括 Rs 承認は per-edit 授権先例(D-1 = 1 行でも個別授権+sha)からの regress** → **2 段化: packet = DESIGN 承認 / batch 毎に Rs build-auth 1 行 + per-doc 前後 sha manifest 報告**(ST2 の design≠build 分離と同型)。
- C5 intra-doc bisectability なし → RENEW doc 毎 **CP1(純移動、verbatim)/ CP2(追加のみ)の 2 commit** + 両 CP で §5 検査(St2 Q2=B 先例)。
- C6 「or 参照化」= prose 削除 channel(§4-4「削除はしない」と矛盾; §5 は数値のみ監視)→ 「or 参照化」削除(in-repo 移動のみと定義)+ §4-2 を add-only 読みに pin + **prose 保存 leg(非空行 multiset: 移動 OK / 削除 FAIL)を §5 に追加**。
- C7 → 収束点 2 に fold(broadcast 先行 + §9 分割)。
- C8 → 収束点 1 に fold(write-back 実施者 = p6/%12 flow を明記)。

### CC6(NHA)— **NULL_HYPOTHESIS: 部分 HOLD** → ACCEPT(§9 再構築)
- batch 0 + A = CHANGE_JUSTIFIED now(tracked 化 = 真の価値 / A = 確認 + 純増 ≈ 1 banner + 1 句)。
- **batch C = motion-table v2 fold 着地まで DEFER 推奨**: 私の工程表(Rs 承認済)が RL-Routing-Design 現行行番号に line-bound(§1.2/§7)+ v2 fold は §5 規約 3 で「json⇄§2 doc 同時更新」を義務化 + probe は dispatch 済 = days-scale → **renewal-first = §2 領域二重編集 + cite map 2 回 + 工程表 sub-revision 2 回。v2-first が厳密に無駄が少ない。** CC1 追認(正直注記): D-1 挿入(+3 行)で工程表の :2708 以深 cite は**既に ±3 stale** — r1 で未再 anchor。NHA 論点を実証する既成事実。
- **B = v3.2 head banner のみ(B-minimal)まで縮小推奨**(消費者ゼロ = L1.A 未着手; CC4-C3 の patch-stack 発見が uniform archive banner の誤りを独立に裏付け)。
- §9 再構築: **C timing(C-now vs C-defer[CC1+NHA 推奨] vs C-light[行数保存 in-place 編集のみ])** + **B(B-minimal[推奨] vs P-light vs P-full[CC2-C9 で gate 実行不能 = 非推奨])** を Rs 決定項目に追加。CANONICAL 工程表を §6 の consumer list に明記 + anchor-semantics 検査(:1284-1361 が刷新後も 43-step 表として parse できること)+ §3.1 の D-1 位置誤記(§2 内 → 実際は §6 版数注記 block :2701-2716)訂正。

## NO_ACTION_EVALUATION

- 完全 No Action = Rs directive 違反 → 棄却。
- **部分 null(NHA)は採用**: v0.2 の §9 に C-defer / C-light / B-minimal を正式 option 化(CC1 推奨 = **batch 0+A 即時 / B-minimal / C-defer(v2 fold と単一 pass 統合)**)。決定 = Rs。

## v0.2 fold 計画(group)

- **A(invariance 再設計)**: CC2 全項 — block-hash canonical 領域 + partition-aware multiset + hex/verbatim class + allowed-additions + 事前 commit review + U+2212 + context-anchored 除外 + P-full 実行不能注記 + prose 保存 leg(CC5-C6)。
- **B(cite/map)**: CC3 全項 — regex set / 3 列 disposition ledger / LEDGER 矛盾解消 / § canonicalization table + 相互排他の Rs 昇格 / map currency / MAP-ONLY class / CANONICAL consumer 明記 + 既 ±3 stale 正直注記。
- **C(disposition/権限)**: CC4 全項 + CC5-C4 — (Rs-confirm) / snapshot banner / patch-stack 2 class / ' M' 分割 + hunk 掲載 + broadcast / VGroove staleness pointer / S1B scoped / guardrail 文言 / GD-KoShape charter 質問 / **2 段 Rs 授権**。
- **D(process/gate)**: CC5 残項 — 層5 拡張 / post 層2 / sha 再検証契約 / CP1/CP2 / 参照化 削除。
- **E(§9 再構築)**: NHA options + D-1 位置訂正 + anchor-semantics 検査。

**次:** %12 DECIDE verify → v0.2 fold → targeted re-verify → %12 verify → Rs packet(§9 再構築版)。
