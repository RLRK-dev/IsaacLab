# 07-Design 構造刷新 RENEWAL_PLAN(step 0-1 packet)

**Status: v0.3 — ✅ Rs DESIGN-APPROVED + batch 0 build-authorized**(2026-07-11 01:1x、%12 relay; DESIGN 承認 anchor = packet sha `55554b68…` @`f19a80d34f`)。§9 の 7 決定 = **CC1 総合推奨どおり全確定**(§11 反映)。**執行 layer = §11**(§1-§10 = v0.2 分析基盤、不変)。chain 済: v0.1 → 5体 debate FAIL → v0.2 fold(group A-E)→ %12 verify PASS → Rs 承認。
- **v0.2 chain(履歴):** 本 packet → ~~5体 debate~~(`RENEWAL_L3_DEBATE_DECIDE.md`)→ %12 verify → Rs 承認(§9)→ batch 執行。
**Charter:** Rs 裁定 2026-07-11 00:30(%12 relay 00:35、bank = routeexec node): 対象 = 07-Design 主要 doc 群 / 深さ = **構造から刷新 — canonical 値(43-step 表・全数値・決定記録・sha anchor)不変保証付き** / executor = p5(設計基盤 surface)。**L-TRIAGE = L3**(RL-Routing-*.md path match + 複数 file)。
**Guardrails(charter + %12 00:38 + debate fold):** ①刷新 = 構造/編集のみ — 工程・設計値の変更は v-next governance へ(不混合。**例外 = batch 0 の VGroove ' M' adjudicate のみ、§2-2 で個別 Rs 承認**)②RL-Routing-Progress = FROZEN 原文 verbatim 保存(banner 以外の内容 edit 禁止)③PoseEstimation consolidate は **non-FAILED/non-DISCARDED(ACTIVE または PARKED)系譜のみ**(CC4-C7 修正; 復活禁止 gate)④FAILED/DISCARDED doc の内容復活禁止は **substrate/scope-limited**(blanket でなく LEDGER の scoped list verbatim、CC4-C8 修正)。
Author: p5 VT-DESIGN。v0.1 Drafted 2026-07-11 00:4x、**v0.2 folded 00:55 JST**。**Node: T-ROOT-DesignDoc-Renewal-20260711**(登録 `eac3d11b73`、IN_PROGRESS、assignee = p5)。

> **v0.2 の位置づけ:** 5体 debate(CC2-5 Challenger + CC6 NHA)で CRITICAL 3 + HIGH 12+ を ACCEPT。方向(Rs directive 準拠の刷新 / batch 構造 / rename ゼロ / immutability / step-0 順序 / inventory 完全性)は VALIDATED、棄却なし。本 v0.2 は全 findings を fold。**CC1 推奨(NHA + %12 と一致): batch 0 + A 即時 / B-minimal / C-defer(工程表 v2 fold と単一 pass 統合)。決定 = Rs(§9)。**

---

## §0 接地(§運用4)

| SSOT | 用途 |
|---|---|
| `00-DESIGN-STATUS-LEDGER.md`(:41,:42,:50-57,:65-74,:119,:121-122)| 各 doc 成否 status + (Rs-confirm) 定義 + pointer-only 設計 |
| `CANONICAL_MOTION_TABLE_V1.md`(v1.0a-r1、Rs-approved)| §5 版管理 + sub-revision 規約(準拠先)+ **§6 cite consumer(当事者、§1.2/§7 が RL-Routing-Design 行番号に line-bound)** |
| `RENEWAL_L3_DEBATE_DECIDE.md`(commit `b25c350e95`)| 5体 DECIDE + fold group A-E |
| `Vault Write Permissions.md:27`(07-Design = Rs Write / CC Read-only)| §2-2 / 2 段授権の根拠 |
| charter(%12 00:35)+ 確認 5 点(00:38)+ verify(00:54)| scope・process・guardrail |
| inventory 実測(git status + wc + sha256 + grep、時刻付)| §1/§2/§6 数値 |

## §1 Doc inventory(11 file、実測 2026-07-11 00:3x;数値は §6 の expanded grep で batch C 直前に再取得)

| doc | 行 | git | LEDGER status(:行)| cite 露出(暫定、下記注)| disposition(§3)|
|---|---|---|---|---|---|
| 00-DESIGN-STATUS-LEDGER.md | 122 | tracked | (自身が SSOT)| 生きた参照多数 | **EXCLUDE**(構造刷新対象外; cite write-back は §3.4)|
| RL-Routing-Design.md | 3,760 | tracked(⑥済 file sha `eaf05513…`、commit `59badc4b7a`)| **⚠️ MIXED (Rs-confirm)** = **未批准 draft 判定**(:42 + :121-122; CC4-C1)| 行 cite 74/全拡張子(md/py/sh:69、+html/txt 5)+ bare-§ 19 + `.md §` 56 + memory 13 file | **RENEW**(batch C、最重)|
| RL-Routing-Progress.md | 4,926 | tracked | 📖 REFERENCE、FROZEN(:55、Rs D4 07-02)| 名前 ~325/23(drift) | **ARCHIVE-LABEL**(batch A; verbatim 保存)|
| Mechanical-Specs.md | 2,646 | tracked | 📖 REFERENCE(:56、hardware 未取得)| 行 cite 3/2(低)| **RENEW**(batch C; 深さ = Rs 決定 §9-3)|
| PoseEstimation-Design-v3.2.md | 686 | **untracked** | ⏸ PARKED **head**(:50、unvalidated・L1.A 未着手)| 名前系 ~146/59(5 世代計、drift)| **head banner**(batch B、§3.2)|
| PoseEstimation-Design-v3.1.md | 1,187 | untracked | 🔁 SUPERSEDED(:51)| 同上 | **部分 supersede / head 構成要素**(§3.2、CC4-C3)|
| PoseEstimation-Design-v3.md | 1,417 | untracked | 🔁 SUPERSEDED(:52)| 同上 | **部分 supersede / head 構成要素(parent base)**(§3.2)|
| PoseEstimation-Design-v2.md | 1,062 | untracked | 🔁 SUPERSEDED(:53)| 同上 | ARCHIVE(whole-superseded)|
| PoseEstimation-Design-v1.md | 622 | untracked | 🔁 SUPERSEDED(:54)| 同上 | ARCHIVE(whole-superseded)|
| S1B-Faithful-Finger-Design.md | 144 | **untracked** | ⛔ FAILED/ABANDONED/SUPERSEDED(:41、§FAILED item 1 :65)| 低 | **ARCHIVE-LABEL + scoped 復活禁止**(batch A)|
| Gripper-VGroove-Design.md | 141 | tracked(**' M' 1 行**)| 🔁 SUPERSEDED by コ / ◇ DISCARDED(:57)| 低 | **ARCHIVE-LABEL + staleness pointer**(batch A)+ ' M' adjudicate(§2-2)|

**注(cite 数値、CC3-C1/CC3-C7):** v0.1 の「69/21」は md/py/sh の `\.md:[0-9]` のみ。実際は取り漏れ複数形式あり(bare-name §、`L462-581` 形式、逆順 §、html/txt、memory）→ §6 の **pre-registered regex SET** で batch C 直前に全 repo 全拡張子 + memory report-only sweep を再取得し、本 §1 数値を supersede。
**LEDGER 照合(guardrail ③、CC4-C3 修正):** PoseEstimation は **線形 supersession でなく base+patch-stack**(v3.2 frontmatter「v3 remains parent」「open v3 + v3.1 + v3.2 together」verbatim CONFIRMED)。v1/v2 = whole-superseded、**v3・v3.1 = head v3.2 の normative 構成要素(部分 supersede)**。FAILED/DISCARDED 混在なし = consolidate 系譜として clean(head = PARKED ≠ DISCARDED)。

## §2 Step-0 提案

### §2-1 tracked 化 6 file(§9-4a、機械執行)
**tracked 化 6 file**(PoseEstimation v1/v2/v3/v3.1/v3.2 + S1B)。順序論理 = consolidation/archive-label 前に tracked 化して原本を git provenance に固定(⑥ RL-Routing-Design と同型)。
- **編集前 sha256(p5 実測 2026-07-11 00:3x; %12 verify 01:0x に full-hash 6/6 再計算 EXACT 確認):** v1 `49c8c52fb0…` / v2 `42aeaf03c1…` / v3 `a7913e9fab…` / v3.1 `623ee87571…` / v3.2 `6719200e7d…` / S1B `93822028d2…`(full 64-hex は batch 0 commit message に記録)。
- **執行時 re-verify 契約(CC5-C3、新規):** 承認〜執行の間に SHARED-LIVE vault で他 pane 編集が起き得る(D-1 flow が同夜 00:31 に RL-Routing-Design を実編集した実績)→ **batch 0 執行の同一ターンに full-sha 再計算 → 上記 pin と照合 → mismatch なら STOP + re-inventory + Rs へ delta 報告**(一括承認は変更後 byte に carry しない)。full 64-hex を commit message に記録(§5 P-3 out-of-doc 束縛)。

### §2-2 VGroove ' M'(1 行 uncommitted)の adjudicate(§9-4b、Rs 個別判断)
- **内容:** HALF_OPEN_RAD「≈0.667 PROPOSED」→「0.69 human-confirmed 06-21 + LANDED(task_config 06-25)」の records-currentization。**task_config.py:313 = `GRIPPER_DRIVER_HALF_OPEN_RAD = 0.69` と検証一致 = 事実正**(LEDGER:58 独立 bank)。
- **verbatim hunk(CC4-C4 掲載要求):**
  ```
  - `GRIPPER_DRIVER_HALF_OPEN_RAD` ≈ 0.667 (half-clamp = ◇ form / GUIDANCE) — **PROPOSED, NOT yet landed**
  + `GRIPPER_DRIVER_HALF_OPEN_RAD` = **0.69** (half-clamp GUIDANCE) — **human-confirmed 2026-06-21 (supersedes the ≈0.667 PROPOSED) + LANDED in task_config.py 2026-06-25** ... ⚠ this doc's ◇ V-groove is DISCARDED — the param value now serves the コ finger.
  ```
- **process 論点(CC4-C4 / CC5-C7):** origin pane = 不明(p5 + %12 とも不明、最終 commit 06-22 以降放置)。07-Design = Rs-専権 write(Vault Write Permissions:27)につき、無署名 edit の commit 化は §運用10 anomaly + §運用4 write-side の慎重域。
- **選択肢(決定 = Rs、§9-4b):**
  - **A(CC4 推奨): revert + anomaly 記録 + banner pointer 化** — `git checkout --` で Rs-governance-committed 状態に戻し、値は batch A の ARCHIVE banner に pointer(「current value = task_config.py `GRIPPER_DRIVER_HALF_OPEN_RAD` 0.69; LEDGER:57/:58」)として反映(reference-over-copy 整合; DISCARDED doc に live 値を copy しない)。
  - **B: 「内容検証済 currentization」として commit**(origin-unknown + 検証根拠を message 明記)。origin = Rs 本人の可能性も残る。
  - いずれも **pane 宛 claim broadcast を先行**(CC5-C7; %12 経由で fold 後に文面回付 = %12 00:54 手順)。

## §3 Per-doc disposition(詳細、debate fold 済)

### 3.1 RENEW(batch C — 構造刷新本体)
- **RL-Routing-Design.md**(3,760 行):
  - **canonical 領域 = verbatim block 維持**: §2 工程設計(43-step 表 :1284-1361 の 6 分割表 + 用語 :1231-1239 + §2.1 layout :1363-1403 + §2.2 segment map :1405-1459 の `**`/`(h)`/`→` marker 含む)+ **D-1 訂正注記**(**注: 実位置 = §6 版数注記 block :2701-2716 内であり §2 内ではない — v0.1 の「§2 内」は位置誤記、CC6/CC2-C2 訂正**)+ 決定記録 block(sha anchor :68-69 等 + Rs 決定 verbatim)。§5 の block-hash で保護。
  - **STATUS banner = LEDGER :42 行の verbatim snapshot**(mirror でなく as-of 日付付 snapshot、§4-1 / CC4-C2 / CC4-C6)。**「(Rs-confirm)」+ full caveat(mechanism = spring-follow+kinematic-hold が QUARANTINED / P0-KILL as-scoped / not clean success-or-fail / Gate G3 PASS / per-skill → SOMA.md)を脱落なく含める**(CC4-C1/C2)。paraphrase 禁止。
  - historical 堆積(冒頭 ~1,000 行の R2-A Track state :27-1027、v5/v8-v12 廃止 Step 表等)は HISTORICAL 節へ **in-repo 移動のみ**(削除・参照化による repo 外化 禁止、§4-4 / CC5-C6)。
- **Mechanical-Specs.md**(2,646 行、深さ = Rs 決定 §9-3): 「intended hardware / 物理未取得」(:56)banner。**canonical 表を列挙して block-hash 対象化**(CC2-C1: 行検査ゼロを閉じる)。cite 露出低(3)。

### 3.2 batch B(PoseEstimation 系譜、CC4-C3 patch-stack 修正)
- **v3.2 = head**(rename なし): head banner =「CURRENT HEAD(PARKED/unvalidated、L1.A 未着手)+ **composite 読解契約(v3 + v3.1 + v3.2 を併読、v3.2 は §1.2 掲載 section のみ supersede)** + 系譜 + 各 LEDGER 行 pointer」。
- **v3・v3.1 = 部分 supersede banner**:「edit-frozen; **v3.1/v3.2 §1.2 未掲載 section では normative 継続**; head v3.2 の構成要素」。← **一律 SUPERSEDED archive banner は誤読誘発(head が base なし 686 行 patch 化)→ 禁止**。
- **v1・v2 = whole-superseded archive banner**(edit-frozen)。
- **Option(§9-1):** **B-minimal(CC1/NHA 推奨)= 上記 banner のみ**(消費者ゼロ = L1.A 未着手、frontmatter label 既存)/ P-light = 同+正規化 / **P-full = 非推奨**(§5 multiset が dedup で恒真 FAIL = gate 実行不能、CC2-C9; 選択時は presence-based 別検査 + 別 debate)。

### 3.3 ARCHIVE-LABEL(batch A — 低 risk)
- **RL-Routing-Progress.md**: FROZEN banner 確認のみ(既設 07-02)。**内容 edit 禁止(verbatim、guardrail ②)。**
- **S1B-Faithful-Finger-Design.md**: FAILED banner。**復活禁止 = scoped**(CC4-C8): LEDGER :65-74 の閉鎖 path(VBD-prismatic retry / Kamino single-solver / dual-solver-external / **本 substrate での faithful finger 再建**)を **verbatim 引用**。「cable retention は Newton で infeasible ではない」(:73-74)+ reward-design 補正の mujoco portable 性(:86-87)は blanket 禁止で潰さない。
- **Gripper-VGroove-Design.md**: DISCARDED banner。**追加 = dated staleness pointer**(CC4-C5): 既存 banner の「committed asset still ◇ / swap deferred L3」記述は :57(COMMITTED `85315bbec6` 06-23、records-vs-code CONSISTENT)に対し stale → 「internal asset-status claims are pre-swap (stale as of `85315bbec6` 2026-06-23); current = LEDGER:57」を追記。' M' は §2-2 決定後に反映。

### 3.4 EXCLUDE(CC3-C3 / CC5-C8 矛盾解消)
- **00-DESIGN-STATUS-LEDGER.md = 構造刷新から除外**。ただし **cite-currentization(:60 の `RL-Routing-Design.md:1410/:1422` 等)+ status write-back(§5 規約 2)は除外対象外** — governance flow(**p6 PLAN-KEEPER charter / %12 or Rs-専権 flow**)で実施。「触らない」は「構造を再編しない」の意で、cite/status の維持は行う。

## §4 新構造 skeleton(RENEW 対象に適用、CC5/CC6 fold)

```
1. STATUS banner = LEDGER 該当行の verbatim snapshot + as-of 日付 + 「SSOT = LEDGER」pointer
   + cite-migration map への pointer(§6)。※維持される mirror ではない(LEDGER:119 pointer-only 整合)
2. SSOT cross-ref 節(canonical 値は保持せず参照: task_config.py / full_43step.json /
   CANONICAL_MOTION_TABLE_V1 §*)。reference-over-copy。※既存重複値の「削除」ではなく add-only
   (新規 cross-ref 追加のみ; 既存 in-doc 値は canonical 領域として block-hash 保護、CC5-C6)
3. 本文(現行有効な設計内容 — 構造再編、値 verbatim)
4. HISTORICAL 節(廃止済経緯・旧 version — in-repo 区画化のみ。「参照化」= repo 外削除は禁止、
   移動先は同 doc 内 HISTORICAL 節 or in-repo archive file + sha pin、CC5-C6)
5. Changelog + 版管理(CANONICAL_MOTION_TABLE_V1 §5 規約 + sub-revision;
   version⇄sha 束縛は commit message / LEDGER = 自己 sha 埋込禁止)
```

## §5 Canonical-invariance 機械検査(全面再設計、CC2 fold; batch C gate)

**設計原則(CC2-C1/C2/C3/C4 収束):** 「全数値 token multiset + 43-row parse」は **値 swap・active→HISTORICAL 移動・sha/決定 corruption に盲目**。→ **3 層構成**に置換。

### §5-1 canonical 領域 = verbatim block-hash(swap/relocation/表構造に堅牢)
- §3.1 が約束する「canonical 領域 verbatim 維持」を **直接機械化**: RENEW doc ごとに **canonical block manifest**(pre-registered)を宣言 — RL-Routing-Design: §2 全域 + D-1 注記 + 決定記録 block; Mechanical-Specs: 列挙した canonical 表。各 block を **正規化後 verbatim hash(SHA256)**で pre/post 比較 → 不一致 = FAIL。※ block の**位置移動は許容・内容変更は不許容**(D-1「上記」位置参照は block 内に referent を含めて凍結、or anchor 明示化を batch C 内 Rs-approved manifest 下で実施)。

### §5-2 partition-aware multiset(残部 + presence 保証)
- canonical block を除く残部を **post-renewal の ACTIVE 区画 / HISTORICAL 区画で別々に**数値抽出。
- **抽出 token class(CC2-C7 / CC2-C3):**
  - 数値: `[-+−]?[0-9０-９]+\.?[0-9０-９]*([eE][-+−]?[0-9]+)?`(**U+2212 minus + 全角数字対応**; :1368-1380 に U+2212 実在)。正規化表 = 先頭 `+` / 末尾ゼロ / ASCII⇄Unicode minus / en-dash range を**事前登録**(後出し禁止)。
  - hex anchor: `[0-9a-f]{8,64}` を **whole-string** 比較(数字だけ corrupt = false-PASS を封じる)。
  - 決定 verbatim: pre-registered 決定 block(D-1 / v2-v4 注記 / Rs 承認行 / `PRODUCT_GO=false` 等)の hash。
- **presence 保証:** pre-registered **canonical value manifest**(用語 z/finger、座標、segment map、D-1 値、sha)の各値が **post の ACTIVE 区画に存在必須**(HISTORICAL への移動で「現行として主張されなくなる」silent 化を捕捉、CC2-C2)。

### §5-3 prose 保存 leg(CC5-C6)
- RENEW doc の **非空行 multiset**(正規化)を pre/post 比較 = **移動 OK / 削除 FAIL**。数値なし historical prose の silent 消失を捕捉(「invariance PASS」と誤表示させない)。

### §5-4 anchor-semantics 検査(CC6)
- 刷新後、canonical anchor が意味を保つか検証: 例 = 旧 `:1284-1361` 相当が **依然 43-step 表として parse できる**(§ canonicalization table 経由で新 anchor に解決)。数値不変でも anchor 剥離を捕捉。

### §5-5 ALLOWED-ADDITIONS + enforcement(CC2-C5/C6)
- 義務 banner(`92.2` 等)・changelog header は multiset で「新規追加=FAIL」に抵触 → **pre-registered ALLOWED-ADDITIONS list**(exact 文字列/block)で許可。
- **enforcement(最重要):** 除外 regex list + ALLOWED-ADDITIONS list + `renewal_invariance_check.py` を **刷新編集の起草前に commit + %12/Rs review + script sha pin**。起草者=執行者=gate 運転者が同一 pane(p5)ゆえ、freeze 点なしでは「自分の diff が通る除外」を後付けできる。後の list 変更 = full gate 再走 + loud。
- 除外は **context-anchored のみ**(CC2-C8): full ISO timestamp / `§[0-9.]+` / `<filename>\.md:[0-9]+(-[0-9]+)?` / sha-class。bare `\d{4}-\d{2}-\d{2}` / bare `:\d+` 禁止。
- **判定:** §5-1〜§5-4 全 PASS でのみ per-doc commit。FAIL = loud diff + STOP(自動修正なし)。log = evidence dir 世代 tag。full_43step.json = sha 不変検査(不触)。
- **P-full 注記(CC2-C9):** 本検査は **same-doc RENEW 専用**。P-full(5→1 dedup)は multiset 恒真 FAIL → 選択時は presence-based 別検査を別途設計 + 別 debate(∴ B-minimal を実質推奨)。

## §6 Cite-breakage 監査 + migration map(CC3 fold)

### §6-1 pre-registered regex SET(CC3-C1、全 repo 全拡張子)
v0.1 の 2 patterns は取り漏れ多数 → **SET を batch C artifact として事前登録**:
```
\.md:[0-9]+(-[0-9]+)?              # 行 cite（範囲含む）
\.md[: ]?L[0-9]+(-[0-9]+)?         # L462-581 形式（task_config.py:357 = 既存 stale）
(RL-Routing-Design|…)( ?\.md)? ?§[0-9]   # bare-name § 19 hits 含む
§[0-9.]+ +(RL-Routing-Design|…)\.md      # 逆順 §（task_config.py:220）
```
- 全 repo・**全拡張子**(md/py/sh/html/txt)+ `--exclude-dir=.git`。memory-dir(`~/.claude/.../memory/` 13 file)は **report-only sweep**(auto-edit 禁止、handoff drift 注意喚起のみ)。
- §8 の batch C 直前 re-grep は本 SET を使う(v0.1 の「§6 数値」patterns でなく)。

### §6-2 3 列 disposition ledger(CC3-C4、境界判定)
citing file を **{LIVE-update / BANKED-immutable / OUT-OF-SCOPE-report-only} × decided-by** で **per-file 分類**(path 則でなく; 工程表自身が eval_runs 内で LIVE = path 則破綻の実例)。分類 = **p5 提案 → %12 verify → Rs 承認**(batch C gate 内)。
- **明示登録すべき当事者(CC6 / CC3-C4):** `CANONICAL_MOTION_TABLE_V1.md`(§1.2/§7 = LIVE; **既に D-1 3 行挿入で :2708 以深 cite が ±3 stale = NHA 論点の実証、r1 未再 anchor**)/ `DESIGN_V1.md:44`(`:1226` cite)/ 06-Knowledge 3 doc / node DEFINE docs / frozen doc(Progress/v3.1)= **MAP-ONLY class**(verbatim 保存ゆえ更新不可、map 依存)。
- **task_config.py:357(`L462-581`)= 刷新前から stale**(成功条件定義 v3 は現 :1588)→ **刷新と分離**、report-only の別途小裁定(task_config = L3 path、%12 00:54 受領)。

### §6-3 § canonicalization table(CC3-C5)
§番号後方互換は現状 ill-defined(§4.2 重複 :2537/:2539 / 冒頭 ~1,000 行無番号 preamble / 深さ不整合 / 無番号 trailing 節)→ **`old heading@old-line → new §ID` table を cite map の一部として事前登録**(§4.2 重複解消 + 無番号節への ID 付与含む)。「§ compat」= 「旧 §ID が table 経由で解決可能」の意に再定義(番号不変ではない)。
- **相互排他の Rs 昇格(§9):** 「§2 前 preamble 移設」⊥「43-step 表 行位置安定化」は両立不能(preamble ~1,000 行を動かせば §2 が ~1,000 行 shift)→ Rs/5体 判断事項(v0.1 の「両方 design 選択」は誤り)。

### §6-4 map currency(CC3-C6)
`RENEWAL_CITE_MAP.md` = **tracked live file**、doc sub-revision と 1:1(header に `doc sha ⇄ map version`)。anchor = **§ID のみ**(new line number 禁止 — 次編集で stale)。RENEW doc の STATUS banner に map pointer(§4-1)。freshness check(PLAN-KEEPER `check_map_freshness.sh` 型 = map 記録 sha vs 現 doc sha)。

## §7 執行 batch + gate(CC5 fold: 層5 / 層2 / CP / 2 段授権)

| batch | 内容 | gate |
|---|---|---|
| **0** | tracked 化 6(§2-1)+ VGroove ' M'(§2-2 Rs 決定)| §2-1 執行時 full-sha 再検証 + mismatch STOP。**層5-lite or loud 免除記録**(内容 diff なしの git-add ゆえ; CC5-C1)|
| **A** | archive-label 3(Progress 確認 / S1B scoped / VGroove staleness)| banner-only diff(banner 以外 diff==0 検査)+ **層5 SSOT lens**(3+file 直交トリガー、CC5-C1)+ %12 verify |
| **B** | PoseEstimation banner(§3.2、Rs option)| B-minimal/P-light = A 同型 + 層5 SSOT lens / P-full = §5-5 別検査 + C 同型 |
| **C** | RL-Routing-Design(+ Mechanical-Specs、Rs 深さ)構造刷新 | **§5 全層 PASS** + cite map(§6)納品 + **CP1/CP2 2 commit**(CP1=純移動 verbatim / CP2=追加のみ、両 CP で §5、CC5-C5)+ **層5 多視点(幾何 n/a・SSOT・prose)** + %12 verify + **post 層2 focused challenger pass**(L3 事後、CC5-C2)+ per-doc commit(sub-revision)|

- **2 段 Rs 授権(CC5-C4、D-1 per-edit 先例 + ST2 design≠build 整合):** 本 packet 承認 = **DESIGN 承認**。各 batch(特に C)着手前に **Rs build-auth 1 行** + per-doc 前後 sha manifest 報告。一括 skeleton 承認で 3,760 行 rewrite を無 gate 執行しない。
- 全 batch: 値変更ゼロ(guardrail ①、例外 = §2-2 ' M' のみ Rs 個別承認)。刷新中の値変更要求 = v-next 台帳へ回送。

## §8 Louds / risks(更新)

- 行 cite の stale 化は**不可避**(map で §ID 解決に緩和、消滅はしない)。**CANONICAL_MOTION_TABLE_V1 は既に D-1 で ±3 stale**(§6-2)= C-defer 論拠。
- §5 除外/許可 list の設計が甘いと false-PASS/FAIL — **起草前 commit + %12/Rs review + script sha pin で freeze**(§5-5)。
- P-full = §5 gate 実行不能(§5-5)。unvalidated 内容再構成 = 検証手段なし。
- RL-Routing-Design は live 参照先(他 pane 並行 cite)→ batch C 直前 re-grep(§6-1 SET)。
- **renewal-first vs v2-first の順序(NHA、§9-C):** 工程表 v2 fold は §2 領域の同時編集を義務化(CANONICAL §5 規約 3)+ probe dispatch 済(days-scale)。renewal-first = §2 二重編集 + cite map 2 回 + 工程表 sub-revision 2 回。**v2-first(C-defer)が無駄最小。**
- 07-Design ACTIVE 設計 doc は本 inventory にゼロ(GD-KoShape = 06-Knowledge、LEDGER:58 🟢)→ charter「主要 doc 群」の意図確認(§9)。
- Fable5 常用: 実行 model 指定は Rs/%12 に従う(p5 は現 session model で起草)。

## §9 Rs decision items(再構築、CC6/CC4 fold)

1. **batch C timing(最重要):**
   - **C-defer(CC1 + NHA + %12 推奨):** batch C を工程表 **v2 fold 着地まで HOLD** → v2 + 構造刷新を単一 pass(cite map 1 回 / invariance 1 回 / 工程表 re-anchor 1 回)。
   - C-light: RL-Routing-Design を **行数保存 in-place 編集のみ**(冒頭 stale :27-40 を同行数 STATUS banner に置換; :1062-2716 を shift しない)。
   - C-now: v0.2 の full batch C を即時。
2. **batch B:** **B-minimal(推奨)** / P-light / **P-full(非推奨、§5 gate 実行不能)**。
3. **Mechanical-Specs 深さ:** full skeleton / banner+区画化のみ(hardware 未取得ゆえ軽量可)。
4. **Step-0 分割:** **4a** tracked 化 6(承認即可)/ **4b** VGroove ' M' = §2-2 の A(revert 推奨)vs B(commit)。
5. **(optional)RL-Routing-Design :42 MIXED を今 Rs 批准するか**(批准で banner が clean に ship、CC4-C1)。
6. **charter scope 確認:** 「07-Design 主要 doc 群」に ACTIVE 設計面(GD-KoShape @06-Knowledge)を含めるか(現 inventory は 07-Design のみ = charter 文言 faithful、CC4 観察)。
7. LEDGER = EXCLUDE(構造刷新のみ、cite/status write-back は §3.4)の確認(%12 同意済)。

**CC1 総合推奨:** 4a + batch A(scoped)即時 / 4b = revert(A)/ B-minimal / **C-defer** / Mech-Specs = 軽量 / :42 批准は Rs 任意 / GD-KoShape は charter 外のまま(別 charter 化を提案可)。

## §11 Rs 決定反映 + 執行 detail(v0.3、承認 path)

### §11.1 Rs 7 決定(2026-07-11 01:1x、%12 relay; verbatim「7項目確定」+「4 承認」)

| § | 項目 | Rs 決定 | 執行 |
|---|---|---|---|
| 9-1 | batch C timing | **C-defer** | 工程表 v2 fold 着地まで HOLD(§11.4)|
| 9-2 | batch B | **B-minimal** | v3.2 head banner + patch-stack 2 class(§11.3)|
| 9-3 | Mech-Specs 深さ | **軽量**(banner + 区画化のみ、full skeleton 不適用)| batch C 内だが C-defer に従属 → HOLD |
| 9-4a | tracked 化 6 | **承認** | ✅ 済(commit `995bdefafc`、full-sha 6/6 EXACT)|
| 9-4b | VGroove ' M' | **A(revert)** | broadcast 先行 → revert(§11.2)。origin-unknown のまま(Rs 心当り言及なし)|
| 9-5 | :42 MIXED 批准 | **行使なし** | 未批准のまま。banner = (Rs-confirm) 未批准 draft と明記 |
| 9-6 | GD-KoShape scope | **charter 外** | 07-Design のみ(別 charter 化は将来提案可)|
| 9-7 | LEDGER EXCLUDE | 確認 | 構造刷新から除外、cite/status write-back のみ(§3.4)|

「4 承認」= **batch 0 の build 授権**(2 段授権 第 2 段 初回)。batch A/B/C の build-auth = 各着手前に Rs へ別途 1 行。

### §11.2 batch 0(build-authorized、執行中)
- **§2-1 tracked 化 6 = ✅ 済**(`995bdefafc`; 執行時 full-sha 再検証 6/6 pin EXACT、%12 verify PASS 01:21 = tracked 11/11)。
- **§2-2 VGroove ' M' = A(revert)**: 全 pane claim broadcast(p1/p2/p3/p6、申告期限 **2026-07-11 02:00 JST**、応答先 p5、hunk pointer = §2-2、p3 sweep 中は急ぎ不要)→ **期限無申告なら anomaly 記録 + `git checkout --` revert** → batch 0 完了報告(%12 が Rs へ batch A 授権 1 行)。値 0.69 は batch A の VGroove ARCHIVE banner に **pointer 化保存**(§11.3、reference-over-copy)。

### §11.3 batch A(archive-label 3、B-minimal 込; **build-auth 待ち = 未着手**)
- **RL-Routing-Progress.md**: FROZEN banner 確認のみ(verbatim、guardrail ②)。
- **S1B-Faithful-Finger-Design.md**: FAILED banner + **scoped 復活禁止**(LEDGER :65-74 の閉鎖 path verbatim 引用; 「cable retention は Newton で infeasible ではない」:73-74 / reward-design mujoco portable :86-87 は潰さない)。
- **Gripper-VGroove-Design.md**: DISCARDED banner + **dated staleness pointer**(既 banner の「swap deferred」は :57 COMMITTED `85315bbec6` 06-23 に対し stale)+ **' M' 値の pointer 化**(「current HALF_OPEN_RAD = task_config.py:313 = 0.69; LEDGER:57/:58」)。
- **batch B(B-minimal、A と同 gate)**: v3.2 head banner(CURRENT HEAD PARKED/unvalidated + composite 読解契約 v3+v3.1+v3.2)/ v3・v3.1 = 部分 supersede banner(未掲載 section normative 継続)/ v1・v2 = whole-superseded archive banner。**内容再合成なし**(消費者ゼロ = L1.A 未着手)。
- gate(A/B 共通): banner-only diff(banner 以外 diff==0)+ **層5 SSOT lens**(3+file 直交)+ %12 verify。

### §11.4 batch C(C-defer、HOLD)
- **HELD until 工程表 CANONICAL_MOTION_TABLE_V1 の v2 fold 着地。** trigger = v2 発効(L3 + 5体 + Rs 承認 + LEDGER 行、CANONICAL §6 統合方針)。
- 着地時: **v2 の §2 領域編集 + 構造刷新を単一 pass** で実施(cite map 1 回 / invariance 1 回 / 工程表 re-anchor 1 回)。§5 全層 + cite map(§6)+ CP1/CP2 + 層5 + %12 verify + post 層2 + per-doc commit + 各着手前 Rs build-auth(§7)。
- Mech-Specs(軽量、§11.1-9-3)も本 defer に同乗(単一 pass 内で banner + 区画化)。
- **監視:** VN-1/VN-2 は FLAT 深さ sweep(COORD 実行中)+ slot reframe の統合検討待ち(CANONICAL v1.0a-r2 §6.2)。sweep→統合→v2 提案→v2 発効 が batch C の解除条件。

## §10 Changelog

- v0.1-DRAFT(00:4x): 初版。inventory・LEDGER 照合・cite 実数・invariance 案・batch 設計。
- **v0.3(01:2x): Rs DESIGN 承認 + batch 0 build 授権 反映。** §11 追加(7 決定表 + batch 0 済/VGroove revert plan + batch A/B-minimal banner spec + batch C-defer trigger)。status → Rs DESIGN-APPROVED。§1-§10 = v0.2 分析基盤で不変。
- **v0.2-DRAFT(00:55): 5体 L3 debate(CRITICAL 3 + HIGH 12+)全 fold。** A=invariance 再設計(block-hash + partition-aware + hex/verbatim class + allowed-additions + 起草前 commit freeze + U+2212 + prose leg + anchor-semantics + P-full 実行不能)/ B=cite(regex SET + 3 列 ledger + § canonicalization + map currency + CANONICAL consumer 明記 + task_config:357 分離)/ C=disposition(Rs-confirm + snapshot banner + patch-stack 2 class + ' M' 分割 + hunk 掲載 + S1B scoped + VGroove staleness + guardrail 文言 + 2 段授権)/ D=process(層5 A/B + post 層2 + sha 再検証 + CP1/CP2 + 参照化削除)/ E=§9 再構築(C-defer/C-light + B-minimal + D-1 位置訂正 + GD-KoShape 質問)。次 = targeted re-verify → %12 verify → Rs packet。
