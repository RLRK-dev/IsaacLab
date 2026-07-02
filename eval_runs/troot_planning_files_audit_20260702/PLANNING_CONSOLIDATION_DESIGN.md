# 計画 surface 少数化 + 整合機構 — 設計 v2 (2026-07-02, 5体 pre-debate 反映済)

**Node:** `T-ROOT-Planning-Surfaces-Consolidation-20260702` / **Author:** %12 RS-TECH-LEAD / **Rs 承認:** 2026-07-02 13:58「①②承認 少数化+整合機構の設計起案を進めて」(① = 設計起案 GO、② = CLAUDE.md 2 類型の変更承認 [type-level; 最終文言 GO は §9 D2])
**L-TRIAGE:** final_L = **L3** (CLAUDE.md path match + validate.sh logic + LTM-1 v1.2 note + >5 files)。
**Debate:** 5体 pre-debate R1 完了 (CC2-5 + CC6 NHA) — 33 challenges 全 ACCEPT/PARTIAL (REBUT 0)、NHA = CHANGE_JUSTIFIED_WITH_REDUCTIONS、DECIDE = **PASS-with-revisions** → 本 v2。判定表 = `PLANNING_CONSOLIDATION_DEBATE_R1.md`。
**上流:** `PLANNING_AUDIT_REPORT.md` P1-6 / P1-7 / P2-8 / P2-9 / P2-10 (**LTM-1 v1.2 note 含む — v1 で無宣言 drop、v2 で scope-in**) / P2-11 + 運用ルール提案。P1-4 (SOMA tail) / P1-5 (LEDGER row54 衛生) は scope 外 (別タスク、前者 Rs 専権)。
**v1→v2 主変更:** LTM-1 v1.2 note scope-in (§3.5) / T4 = Rs-gated / M2 strict-mode 忠実性契約 / C2 = WARN 出発 + 抽出契約 / C5 新設 / M1.5 (nest-tracker 先行 track) / 並行書込 collision gate / GOALS consumer 温存 / stale-say sweep / C1 = last_updated stamp / C4 = commit-age 語義 / 層B 発火配線 = V9 wrapper / 実装 GO gate 明記 (§4/§9)。node state.md の §2.3 非準拠 (CC2-6) は本 turn で修正済。

## §0. prior-art gate 記録 (V7/V10)

`check_thread_vault_prior_art.sh --fail-on-blocker manifest GOALS.md RL-Routing-Progress validate.sh planning` → BLOCKER_CONTEXT_FOUND。**判定 = false positive**: hit は全て `RL-Routing-Progress.md:1654-1667` の旧 C9 系「guard-manifest / command-safety manifest」= RL harness 起動 pipeline の JSON artifact (CC4 が実 file で同語異義を確認)。計画 surface 統合の失敗 prior-art は存在しない。delta = 対象 domain が異なる。

## §1. Goal / Non-goals

**Goal:**
- G1 読む入口を**地図 1 本** (`docs/logical_decomposition.html` live 部) に集約 — SOMA / LEDGER / node state.md へ 1 hop。
- G2 更新 fanout 5 → 3 (地図 + LEDGER + log.md)。view (manifest §2 / 地図 node 索引) は生成に切替。⚠ honest 注記: Gantt の TASKS/NOW は手保守 curated view として残る (§2 T1) — fanout 算入対象外だが「生成」とは主張しない (CC3-7)。
- G3 整合 3 層: 層A 生成 / 層B 機械 checker / 層C 書込 rule。**GEN 領域内は定義上 drift しない**が、それは生成器が忠実な場合に限る → M2 忠実性契約 (§3 層A) が前提 (CC3-1)。
- G4 「黙って腐る」→「検出されて直る」。**honest scope**: 機械で保証するのは日付・参照・status token・GEN 領域まで。**C2 は「参照先不在」型のみで「あるべき node の不在」(off-map 型) は捕捉できない** — off-map guard は層C prose rule + 層A regen 補助のまま (CC6-R5)。

**Non-goals (境界):**
- N1 (v2 改) **LTM-1 v1.2 は「§5.2/§7.2 への minimal 注記 1 件」のみ scope-in** (§3.5、Rs-gated)。それ以外の LTM-1 本文・node DB (per-node state.md) 構造は不変。manifest の §1 tree text / §3 active session list / §4 dependency graph / §5 archive list は **heading・役割・内容とも温存** (§2 のみ生成化) (CC2-1/-5)。
  **N1 v2.1 読替 (%12 決裁 2026-07-02 18:5x — M1 byte 実測で §運用10 顕在化: T2 ≤50KB と N1 温存が両立不能 [§1+§3+§4+§5 = 実測 346KB、§1 単独 234KB; さらに §6/§7 = 203KB が v2 で disposition 未定義]。%10 提示 P1/P2/P3 から **P2 採択**):**
  - §3 (3KB) / §5 (2.5KB) = **verbatim 温存** (従来どおり)。
  - **§1 / §4 = heading + 役割 + 現況 summary/pointer を live 温存、body は archive へ byte 保全移設** — LTM-1 :98 (親子関係 manifest) / §3.4 step5 (cross-tree scan) の参照は pointer 経由で充足 (運用不変; D3 承認済 v1.2 注記の「§1/§3/§4/§5 の運用は従前どおり」とも整合 — 移るのは body text であって運用でない)。§1 tree-text の冗長性根拠: 正規詳細 = jsx tracker + §2 GEN + nest-snapshot.json (view の自己宣言どおり)。
  - **§6 / §7 = heading + pointer 化して body は archive** (disposition 追加)。
  - live 構成 = head + §1 head/summary/ptr + §2 GEN + §3 verbatim + §4 head/ptr + §5 verbatim + §6/§7 head/ptr + banner ≈ **≤50KB (見積 45KB)**。N4 (byte 保全) 全維持。本読替は **層2 post-debate の明示 review 対象**として記録。
- N2 SOMA.md / RS71 の内容改訂なし (04-Specs = Rs 専権)。
- N3 log.md 不変。
- N4 履歴削除なし — archive は移設 (sha256 領域照合 + 再結合等値で検証、CC3-8)。
- N5 LEDGER row54 分割 (P1-5) は含めない。

## §2. Target shape — surface 別処遇

| # | surface | 処遇 | v2 詳細 |
|---|---------|------|------|
| T1 | `docs/logical_decomposition.html` (460KB) | **地図 = 唯一の読む入口** | live 部 ≤~60KB + 過去 frame → `docs/logical_decomposition_archive_2026H1.html`。**GEN 領域は plain HTML のみ** (srcdoc 属性内は不可 — CC3-7 実証; plain 領域は ~line 190 以降に実在確認済)。live header に `<!-- last_updated: YYYY-MM-DD -->` stamp 追加 (C1 計装)。`gen_simplified_tree.py` / `gen_gantt.py` を eval_runs から `scripts/` へ常設昇格 + refresh 契約を file 冒頭に文書化。Gantt TASKS/NOW は**手保守 curated view と正直に再分類**し「SSOT 連動」footer を修正 (M1) |
| T2 | `00-PM/project-tree-manifest.md` (678KB) | **薄い生成 view ≤50KB** | §2 node 表 = GEN marker 領域として再生成 (層A)。§1/§3/§4/§5 = 温存 (N1)。narrative → `project-tree-manifest-archive-2026H1.md`。**header banner 追加**:「UPDATE block 追記禁止 — node 追記は state.md のみ (LTM-1 v1.2 注記)」(CC5-3)。`_edit_requests/` queue = §3/§5 等 非生成部向けに存置 (処遇を LTM-1 note に明記) |
| T3 | `GOALS.md` (gitignored) | **pointer 化 + track 化** | 有害 3 記述 (PhysX production / CUDA_VISIBLE_DEVICES 不使用 / Franka) を全廃。ただし **goal_evidence 契約 2 行 (`goal_evidence不足の場合、Goal PASS不可（FAIL_PROTOCOL扱い）` / `goal_evidence 4点`) は verbatim 温存** — `verify_goal_contract.sh:55-57` + orchestrator (`GOAL_CONTRACT_VERIFY_ENABLE=1` default) の live consumer を壊さない最小 blast radius (CC4-2)。`## Current Sprint` heading は残し pointer 行のみに。`.gitignore:108` 削除 + supersession 1 行 (「:100-103 rationale は tracked pointer 化で失効、repo_root_cleanup_inventory_2026-05-26 分類を supersede」CC4-7) |
| T4 | `07-Design/RL-Routing-Progress.md` (361KB) | **freeze banner — ⛔ Rs-gated** | 07-Design = CC read-only (権限 matrix; log.md:1195 に同 file での実効 precedent)。**banner 文言は CC 起案、書込は Rs 明示承認後** (§9 D4; 選択肢: Rs 実施 / 承認付き %10 実施)。本文不変 |
| T5 | SOMA / RS71 / LEDGER | **KEEP (3 コア)** | 内容変更なし |
| T6 | node state.md 群 | **KEEP (node DB)** | 不変。層A の source of truth |
| T7 | `docs/nest-tracker/` (untracked) | **git 管理化 — M1.5 で M2 より先に** | nest-tracker.jsx は手書き単一 copy で rollback 経路ゼロ (CC5-6)。M2 の生成器テストが nest-snapshot.json を書換えるため**先行 track 必須** (CC3 検証中に実再生成が発生済; backup = session scratchpad/nest-snapshot.json.bak) |
| T8 | `index.md` | **修正** | 00-PM section 追加 + 件数修正 + **:127「live Current NEST tree (current: S1B…)」の stale 記述修正** (CC4-6)。~~handoff.md redirect~~ → **分離・deferred** (§9 D9; vault-root 新 file = Rs 判断、代替 = VaultProtocol:228 の Rs 1 行修正が清潔) |
| T9 | stale-say sweep (新設) | **M4 で同 commit** | freeze/pointer 化後に「live/アクティブ/SSOT」を主張し続ける CC-writable 参照を一掃: `index.md:127` / `06-Knowledge/LL-ApproachCable-BugHistory.md:14` / LEDGER:42 tail (per-skill status →) / `06-Knowledge/Knowledge Index.md:81` / `.claude/skills/implementation-rules/SKILL.md:15` + `.claude/skills/vault-references/SKILL.md:53` (GOALS=SSOT 行) (CC4-6) |

## §3. 整合機構 (3 層)

### 層A — 生成契約 (view は手で書かない)
- source of truth: per-node state.md frontmatter。生成器 = `scripts/build_nest_snapshot.py` 拡張 (`--emit-manifest-section` / `--emit-map-index`)。
- **忠実性契約 (CC3-1 CRIT 対応、M2 acceptance):**
  - (a) **strict mode**: SSOT emission 時は status を **verbatim passthrough** (viewer 向け coercion [PENDING→IN_PROGRESS 等] は viewer 出力にのみ適用)。fallback-parse / skip / node_id 重複が 1 件でもあれば **nonzero exit + MANUAL-REVIEW list 出力** (現状実測: 76/233 が regex fallback、6 status が強制変換されていた)。
  - (b) 非正準 status (`COMPLETE_WITH_LIMITATION` 等) は **raw 表示 + 表頭 legend**。一括正準化は行わない (state.md 大量編集は scope 外)。
  - (c) **忠実性 acceptance test**: 生成 §2 の status 列 == 各 state.md の `grep -m1 '^status:'` 値 (全行一致で PASS)。
  - (d) 走査は `*/state.md` + **`_archive/**/state.md`** (archived flag 付き、§2 の ARCHIVED provenance 行を保持; viewer 出力からは既存挙動どおり除外可) (CC3-4)。
  - (e) §2 列 schema と source field の対応表を M2 実装前に確定 (node_id/name/parent/status/session/created/path ← frontmatter どの key か明記)。snapshot JSON への変更は additive keys のみ + viewer 許容を検証 (後方互換の定義を「diff 構造不変」から置換)。
- **書込規約:** tempfile + `mv` (LTM-1 §5.3) + **Tier 3 flock を read-compute-write 全体に** (migration 期だけでなく恒常) (CC2-4)。
- idempotency: 2 回実行 0-diff (既存出力で成立確認済 — CC3 VERIFIED-OK)。時刻は埋め込まない。
- GEN marker: `<!-- GEN:NEST:BEGIN (build_nest_snapshot.py; 手書き禁止) -->` … `<!-- GEN:NEST:END -->`。**plain HTML/markdown 領域のみ** (srcdoc 内不可)。
- **M2 実測 delta (%12 裁定 2026-07-02 19:5x、層2 review 対象):** (i) **`--emit-map-index` は DROP** — M1 後の live 地図に GEN 可能な plain 領域はあるが、§2 TERSE (18KB) の複製を地図に持つのは重複 GEN surface + 18KB で少数化に逆行。地図は manifest §2 + nest-tracker への static pointer を保持 (**G1 修正: node state.md へは地図→manifest §2 経由の 2 hop、SOMA/LEDGER は 1 hop のまま**)。generator の flag は reserved/documented のまま存置。(ii) **非 node の `*/state.md` 恒久 skiplist**: `10-SSOT-Integrity-43STEP/state.md` は pre-NEST (04-19) の `type: task-state` file で node でない — 除外は正しい。committed skiplist file (`path + 理由`) を generator が消費し、**skiplist 登録済み = INFO (exit 汚染なし) / 未登録 skip = HARD 維持** (恒常 exit=1 による alert fatigue 回避、C4 suppression と同型)。(iii) §2 schema = **TERSE (id|status|parent)** 採択 + L28 adoption_phase value archive 化 (X 裁定、audit P2-8 消化) — annex 参照。

### 層B — 機械 checker (`scripts/validations/check_planning_consistency.sh`、validate.sh 新 layer 7)
- **C1 staleness (WARN):** per-surface `last_updated` stamp (manifest frontmatter 既存 / 地図 live header に新設 / LEDGER header 行) vs `log.md` newest `^## 2026-…` heading の**片側比較** >48h。本文 content-date scrape は fallback のみ (Gantt 未来日付での永久 mask を回避、CC3-6)。
- **C2 dangling refs (⚠ WARN 出発 → 実測 0-FP 後に FAIL 昇格):**
  - node-id leg: **backtick 引用構文 anchor** (`` `T-…` ``) で抽出 → **nest-snapshot node set (synthesized stub 含む) に membership 照合** (state.md 直接照合だと T-ROOT/umbrella 4 件で偽 FAIL — CC3-3)。
  - sha leg: 候補 = 7-10 hex **かつ ≥1 [a-f] を含む** (8 桁日付を排除) **かつ** `commit`/sha 語 or backtick 文脈に隣接 → `git cat-file -t`。実測 FP 35+ の教訓 (CC3-2/CC5-4) により**day-1 は WARN + FP report 出力**。
  - committed allowlist file (spare token / role 名 / 歴史 ref)。**C2 dry-run 結果 = M3 の design deliverable** (昇格判断は実測で)。
  - SOMA 内 cross-ref は恒久 WARN 止まり (04-Specs 修正 = Rs 専権)。
- **C3 GEN-region drift (FAIL):** GEN marker 内容 ≠ 生成器再計算出力 → FAIL。⚠ scope 注記: C3 は「file が生成器出力と一致するか」のみを保証 — **生成器自体の忠実性は M2 acceptance (層A) が担保** (生成器-vs-生成器の盲点、CC3-1)。
- **C4 uncommitted-age (WARN):** 対象 file 列挙 = [地図, manifest, LEDGER, GOALS.md, index.md] (SOMA/RS71 は **対象外** — Rs-pending diff で恒常 WARN 化するため; 代わりに suppression 注記 file `planning_pending_rs.txt` [path+理由+日付] に列挙し、**エントリ成長時のみ WARN**)。判定 = 「`git diff --name-only` に有 AND `git log -1 --format=%ct` >24h」(**commit-age 語義** — mtime は層A regen で常時 reset されるため使わない、CC5-7/CC3-9)。WARN には age + file 明記。
- **C5 non-GEN 凍結照合 (FAIL、新設):** manifest の非 GEN 領域で `^## UPDATE` 行数 > archive 時凍結値 → FAIL (UPDATE-block 禁止の機械検出、CC5-3)。
- **実装規約:** `set -uo pipefail` + **`trap 'echo "LAYER7_FAIL=${FAIL_COUNT:-1}"; echo "LAYER7_WARN=${WARN_COUNT:-0}"' EXIT`** (validate.sh は exit code を捨て contract 行のみ読むため、crash=PASS の fail-open を trap で閉じる — CC3-5)。`--staged-only` 時は repo-state check につき SKIP (layer 5 と同型)。giant-line は `grep -o/-c`。
- **発火配線 (CC6-R1 — 「存在≠防止」は layer 5 D1 で実証済):**
  - `scripts/audit_thread_vault_current_state.sh` (V9 wrapper — 状態 surface 編集の前後に実行が既に必須) の末尾に `validate.sh --layer 7` 呼出を追加 = **編集時点で必ず発火**。
  - pre-commit 経由 (--no-verify で bypass されうる) と on-demand は補助経路。
  - §5 の cadence 記述はこの実配線のみを主張する (「session 開始で全 layer」は preflight が validate.sh を呼ばない現状では**未配線につき主張しない**)。preflight への追加は optional 提案 (§9 D8)。

### 層C — 書込 rule (CLAUDE.md、**4 line-site を §9 D2 で verbatim 提示 → Rs GO 後に landing**)
- **hunk-1 (:233 §運用4 追記、最終文言案):**
  > (3) 計画 surface への同一ターン反映: 地図 (`docs/logical_decomposition.html` 現在 frame) + 該当 node state.md を更新し、view (manifest §2 / node 索引) は `build_nest_snapshot.py` で再生成する (再生成は LTM-1 §5.2 Tier 3 flock 下、tempfile+mv; contention 時は次ターン繰延を loud 記録)。**manifest への UPDATE block 追記は禁止 — node 追記は state.md のみ** (LTM-1 v1.2 注記準拠)。反映 commit は explicit-path の atomic commit とする。
- **hunk-2 (:72):**「RL進捗」→ `00-DESIGN-STATUS-LEDGER.md` + 地図 (**安定 surface のみ**; 現 run は LEDGER 該当行 → eval_runs の間接参照 — eval_runs 直指しは自己腐敗ポインタになるため不採用、CC4-5)。
- **hunk-3 (:226):** 参照ガイドから RL-Routing-Progress.md を除去 (RL-Routing-Design.md は残す)。
- **hunk-4 (:421):** GOALS.md 行を「pointer + goal_evidence 契約 stub (実体 = SOMA/地図)」へ更新。
- 適用 = M5 (最後)。**Rs の最終文言 GO (commit 前) を必須とする** (CC4-3/CC6-R4)。

### §3.5 — LTM-1 v1.2 minimal 注記 (新規 scope-in、**Rs-gated**; 監査 P2-10 の LTM-1-note component)
LTM-1 は manifest への CC direct write を永久禁止し (:530/:607)、書込を Tier 2 deposit/drain (:426-427) に限定する — 層A の同一ターン再生成はこのままでは違反 (CC2-1 CRIT)。**§5.2/§7.2 配下に注記 1 件を追加する v1.2 改訂を提案** (文言案、Rs 承認 + L3 cascade [本 debate がその 5-CC pre-debate を構成]):
> 【v1.2 注記 — manifest §2 GEN 領域】manifest §2 は `build_nest_snapshot.py` の生成領域 (GEN marker) とする。node state.md の更新 = 本条の deposit、同一ターンの再生成 = drain とみなす (executor = state.md を更新した session; tempfile+mv [§5.3] + Tier 3 flock 必須)。§2 GEN 領域への手書きおよび manifest への UPDATE block 追記は禁止 (追記型 node 記録は state.md へ)。§1/§3/§4/§5 および `_edit_requests/` queue の運用は従前どおり (Tier 2 は非生成部向けに存続)。本注記は P17「direct write 永久禁止」の部分改定である。
改訂の landing 自体は Rs 実施 or Rs 明示承認付き CC 実施 (00-PM 内 file だが仕様書; §9 D3)。

## §4. Migration plan (v2)

| M | 内容 | owner | 検証 | rollback |
|---|------|-------|------|----------|
| **GATE** | **v2 + 最終 hunk 文言 + §9 決裁項目を Rs 提示 → 実装 GO** | %12 | Rs 応答 | — |
| M0 | entry 前提: 対象 5 surface `git status --porcelain` clean (or 差分 hold 宣言) + entry sha 記録 | %10 | porcelain 出力 | — |
| M1 | archive 分離 (T1 地図 + T2 manifest) + footer/banner/stamp (T1/T2) + gen_* scripts/ 昇格 | %10 | **sha256 領域照合 + 再結合等値** + `google-chrome --headless --dump-dom` exit-0 + python html.parser 整形式 (live/archive 両方) | salvage patch (`git diff >`) → entry sha へ checkout → 外来 delta 再適用 |
| M1.5 | `git add docs/nest-tracker/` + commit (**M2 より先**) | %10 | git ls-files 確認 | revert |
| M2 | 生成器拡張 (strict mode + 忠実性契約 §3 層A (a)-(e) + GEN marker emission) | %10 | idempotency 2 回 0-diff + **忠実性 test (c)** + MANUAL-REVIEW list 空 or 処理済 + viewer 後方互換 | flag 未使用なら既存動作不変 |
| M3 | checker layer 7 + V9 wrapper 配線 | %10 | fail-first (SOMA:82 WARN + 人工 GEN-drift FAIL + 人工 UPDATE block C5 FAIL) → **C2 dry-run FP report** (昇格判断材料) → 全 layer PASS | validate.sh から layer 7 行除去 + wrapper 行 revert |
| M4 | GOALS pointer 化 (consumer 温存 §2 T3) + .gitignore + T8 index.md + **T9 stale-say sweep** + (T4 は Rs-gated 別実施) | %10 | 有害 3 記述 grep 消滅 + **`verify_goal_contract.sh` 実走 PASS** + `generate_run_metrics.sh` goal_context fallback 確認 + sweep 6 箇所 diff | revert |
| M5 | CLAUDE.md 4 hunks (層C) — **Rs 最終文言 GO 後** | %12 | 引用原文 cat + rule-check stage2 | revert |
| M6 | 完了検証: validate.sh 全 layer + 層2 post-debate + 層5 + DoD (a)-(f) 照合 + 完了報告 | %12 | 全 PASS | — |

**並行書込 protocol (全 in-place 書換 step 共通、CC5-1 CRIT 対応):**
1. 書換 step 開始時: %9/%11/%12 へ hold-notice dispatch + ACK (or capture-verify)。quiet window = **%11 B1 報告 landing 後** (地図 frame + LEDGER 行が着地してから)、対象 = 地図・manifest **両方** (CC6-R3)。
2. 書込直前: 対象 file re-read + `git status --porcelain` が empty or 自 delta のみ + tail 領域 sha256 == entry snapshot → 不一致なら **abort + re-merge** (byte 照合は自分の read snapshot 基準なので並行 append 消失を検出できない — 実証: baseline commit 14 分後に %12 自身の uncommitted block が実在した)。
3. 書込 + commit を同一ターンで完結。flock は script 媒介書込 (層A) のみに有効 — Edit-tool 書込には効かないため hold-notice が一次防御。

## §5. 更新トリガー表 (honest cadence)

| イベント | 書く (手) | 再生成 (層A) | 検証 (層B) |
|---|---|---|---|
| Rs 確定・supersede | LEDGER 行 + 地図 frame + state.md (同一ターン、層C hunk-1) | manifest §2 / 索引 (flock+tempfile) | V9 wrapper 経由で layer 7 発火 |
| node 起動/完了 | state.md (record-before-execute) | 同上 | C2/C3 |
| 設計 bank / commit | LEDGER 行 (+ 地図 frame 要旨) | — | C4 (commit-age) |
| 状態 surface 編集の前後 (V9 既存義務) | — | — | **layer 7 自動発火 (M3 配線)** |
| on-demand / pre-commit (--no-verify 非使用時) | — | — | 補助経路 |

## §6. Risks (v2)

- R1 並行 pane 書込: §4 並行書込 protocol (hold-notice + ACK + collision gate)。flock は script 書込のみに有効と明記。
- R2 生成領域衝突: M1 で領域確定 → M2 marker。plain HTML 限定。
- R3 checker FP: C2 WARN 出発 + 抽出契約 + allowlist + dry-run 実測 → 0-FP 後に FAIL 昇格。C1/C4 は WARN 恒久。
- R4 LTM-1 整合: §3.5 v1.2 注記で正面解消 (黙殺しない)。
- R5 archive loss: sha256 照合 + git tracked。
- R6 地図の生成/手書き混在: 生成 = node 索引のみ。narrative frame + Gantt TASKS = 手書き/手保守と正直に分類。
- R7 (新) 生成器忠実性: strict mode + acceptance test (c) が M2 の合格条件 — これ無しに §2 生成へ切替えない。

## §7. Cost

%10 実装 M0-M4 ≈ 3-5h (GPU 0) / %12 GATE+M5+M6 ≈ 1-1.5h。B1 と無干渉 (書換は B1 報告 landing 後)。

## §8. KNOWN_ALTERNATIVES + NHA 判定

- A0 現状維持 (P0 のみ): 喪失 vector は閉鎖済だが、誤誘導ポインタ 2 件・入口分散・drift 検出不在が恒常化。**NHA: A3 との gap は §3「1 surface で読めない」の解消と drift 検出 — Rs directive が少数化を既に採択しており HOLD 不成立。**
- A1 バラ実施: 生成契約が file ごとに分裂、G2/G3 未達 — dominated。
- A2 完全 1 file 化: 権限境界 + サイズで Rs 棄却済。
- A3 本設計 v2: **採用 (NHA = CHANGE_JUSTIFIED_WITH_REDUCTIONS、R1-R5 全反映済)**。

## §9. Rs 決裁項目 (実装前)

| D | 項目 | 推奨 |
|---|------|------|
| D1 | **実装 GO** (M0-M4、%10 charter) | GO 推奨 (本 v2 で全 CRIT/HIGH 措置済) |
| D2 | **CLAUDE.md 4 hunk 最終文言** (§3 層C — :233/:72/:226/:421) | M5 時に verbatim 再提示 → GO で landing |
| D3 | **LTM-1 v1.2 注記** (§3.5 文言) | 承認推奨 (これ無しだと層A が LTM-1 違反のまま = v1 の隠れ欠陥) |
| D4 | **T4 RL-Routing-Progress freeze banner** (07-Design = Rs 専権) | 文言 CC 起案 → Rs 承認付き %10 実施 or Rs 実施 |
| D5 | **Vault Write Permissions.md への行追加** (00-PM / docs 地図 / node dirs — 02-Workflow = Rs landing) | CC が文面起案 → Rs 適用 |
| D6 | **真性 dangling 3 node** (`T-ROOT-optE-rebase-env7` [CLAUDE.md も cite] / `T-ROOT-optE-S3-gpu-smoke-parity` / `T-ROOT-optE-R-S6`) の処遇 | allowlist 登録を推奨 (歴史 ref; state.md stub 逆起票は record 汚染) |
| D7 | INIT_CODE_A/B の GOALS 依存節 (A:479 ダッシュボード同期指示 / B:1599 Current Sprint 出発点) | 当面 = GOALS に契約 stub 温存で無害化 (T3)。恒久整理は別タスク |
| D8 | (optional) validate.sh run_layer の absent-contract-line=failure 化 + preflight への layer 7 追加 | 別 L3 小タスクとして後日 |
| D9 | (deferred) `thread-vault/handoff.md` redirect 新設 or VaultProtocol:228 Rs 1 行修正 | **後者推奨** (file を増やさない = 少数化整合) |

## §10. M2 schema annex (%10, 2026-07-02 — caution b: 実装前に確定)

**X 裁定記録:** residual-1「keep L28」は §2 fill の budget 実測で premise 反証 (keep-L28 の §2 枠 = 12.3KB < TERSE §2 実測 18.2KB) → %12 が **X 採択** (2026-07-02 19:3x): L28 `adoption_phase` VALUE を archive+pointer 化 + §2 = TERSE。audit P2-8「YAML 24KB append-log」残件の実行を兼ねる。

**§2 GEN 列 schema (TERSE) ↔ state.md frontmatter key 対応:**

| §2 列 | source (state.md frontmatter key) | strict-mode 規約 |
|---|---|---|
| node_id | `node_id` | 必須。無ければ skip + MANUAL-REVIEW 記載 |
| status | `status` | **verbatim passthrough** (viewer 向け PENDING→IN_PROGRESS coercion は nest-snapshot.json 出力のみ; §2 SSOT emission は生値)。非正準値 (`COMPLETE_WITH_LIMITATION` 等) は raw 表示 + 表頭 legend |
| parent | `parent_node` | 空/null は `—` |

**TERSE 採択理由:** name = node_id が self-describing + jsx tracker/nest-snapshot.json に有り → drop。session active 列 = §3 (Active session list, 温存) と冗長 → drop。created / state.md path = jsx/nest-snapshot に有り + headroom 優先 → drop。233 node ≈ 18.2KB、live ≈ 31KB (≤50KB, 将来 node 増への headroom 最大)。

**strict mode 契約 (§3 層A (a)-(e) の実装対応):**
- (a) status verbatim (§2 SSOT emission); fallback-parse / no-node_id skip / node_id 重複 が 1 件でも → **nonzero exit + MANUAL-REVIEW list を stderr 出力**。⚠ MANUAL-REVIEW 非空は正常 (実測 ~76 YAML-fallback + 6 status coercion; 対処 = raw 表示 + 表頭 legend、state.md 一括改変は禁止)。
- (b) 非正準 status = raw + legend。一括正準化しない。
- (c) 忠実性 acceptance: 生成 §2 の status 列 == 各 state.md `grep -m1 '^status:'` (全 node 一致で PASS)。
- (d) 走査 = `*/state.md` + `_archive/**/state.md` (archived flag)。
- (e) snapshot JSON 変更 = additive keys のみ + viewer 後方互換。§2 生成は既存 nest-snapshot.json 生成 path を壊さない (別 CLI flag、default 動作不変)。
- 書込 = tempfile + mv + Tier 3 flock (GEN marker 間 in-place)。GEN marker = `<!-- GEN:NEST:BEGIN (build_nest_snapshot.py; 手書き禁止) -->` … `<!-- GEN:NEST:END -->` (plain markdown のみ)。
- idempotency: 2 回実行 0-diff (時刻埋め込みなし)。

**C5 note:** L28 は frontmatter key (`^adoption_phase:`) につき `^## UPDATE` 計数 (C5) に無関係 — archive 後も C5 freeze 値に影響なし。

---

## §11 M6 close-out records (2026-07-02, %12) — as-landed 文面の耐久記録 + 裁定

**本節が D2/D5 の as-landed 正本記録** (CLAUDE.md は意図的 gitignore `.gitignore:2`、log.md は untracked journal のため、tracked な本 doc が git 耐久 copy)。§3 層C の blockquote は修正前 draft のまま — 本節が supersede (M6 CC2-CH1 fix)。Rs verbatim: D2/D5 = 2026-07-02 22:24「1 2 3 承認 進めて」項目 2。

### 11.1 as-landed CLAUDE.md 4 hunks (on-disk から live 抽出、下記 = 抽出時点の実文面)

```
--- :72 (hunk-2 RL進捗) ---
- **RL進捗:** `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md`（成否 SSOT）+ 地図 `docs/logical_decomposition.html`（現在 frame。現 run の eval_runs は LEDGER 該当行から辿る）。旧 `RL-Routing-Progress.md` は ≤2026-05-28 の歴史記録（FROZEN）
--- :226 (hunk-3 参照ガイド) ---
   - RL設計・訓練 → `thread-vault/07-Design/RL-Routing-Design.md` + `07-Design/00-DESIGN-STATUS-LEDGER.md`
--- :421 (hunk-4 GOALS row) ---
| `GOALS.md` | pointer + goal_evidence 契約 stub（実体 = SOMA.md / 地図 / LEDGER。tracked 化済み） |
--- §運用4(3) (hunk-1、確定事項の即反映 block 末尾) ---
233:   **確定事項の即反映（書込側 hard gate、2026-06-21 human 承認）:** ある node の設計・状態・値が human により**確定 / supersede** された場合、CC は**同一ターン**で (1) `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` の該当行を更新/追加（governing な 06-Knowledge 決定記録も行として追跡）し、(2) その事実を主張する**全 authoritative doc**（07-Design spec + `RS71-System-Spec-SSOT.md` 等 SSOT-INDEX + `SOMA.md`）に supersession flag を反映する。07-Design/04-Specs は CC read-only（設計=Rs専権）のため、human が spec 編集を明示承認していない場合は §運用26 `BLOCKED_FOR_USER` 様式で「spec 更新待ち」を **loud に surface**（黙って spec を古いまま放置しない）。上の banked design SSOT 接地が**読込側**、本項が**書込側**で対をなす。実績: 2026-06-21 コ-vs-V-groove stale-spec drift（決定の記録が 06-Knowledge working doc のみに行き、authoritative spec が ~24h 古いまま→/clear 後に決定が復活）。仕組み詳細・over-reaction guard: memory `feedback-confirmed-decision-reflect-in-authoritative-spec`。(3) 計画 surface への同一ターン反映（2026-07-02 Rs D2 承認）: 地図（`docs/logical_decomposition.html` 現在 frame）+ 該当 node state.md を更新し、manifest §2 は `build_nest_snapshot.py --emit-manifest-section` で再生成する（tempfile+mv + flock、contention 時は次ターン繰延を loud 記録）。manifest への UPDATE block 追記は禁止 — node 追記は state.md のみ（LTM-1 v1.2 注記準拠）。反映 commit は explicit-path の atomic commit とする。
   **確定事項の即反映（書込側 hard gate、2026-06-21 human 承認）:** ある node の設計・状態・値が human により**確定 / supersede** された場合、CC は**同一ターン**で (1) `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` の該当行を更新/追加（governing な 06-Knowledge 決定記録も行として追跡）し、(2) その事実を主張する**全 authoritative doc**（07-Design spec + `RS71-System-Spec-SSOT.md` 等 SSOT-INDEX + `SOMA.md`）に supersession flag を反映する。07-Design/04-Specs は CC read-only（設計=Rs専権）のため、human が spec 編集を明示承認していない場合は §運用26 `BLOCKED_FOR_USER` 様式で「spec 更新待ち」を **loud に surface**（黙って spec を古いまま放置しない）。上の banked design SSOT 接地が**読込側**、本項が**書込側**で対をなす。実績: 2026-06-21 コ-vs-V-groove stale-spec drift（決定の記録が 06-Knowledge working doc のみに行き、authoritative spec が ~24h 古いまま→/clear 後に決定が復活）。仕組み詳細・over-reaction guard: memory `feedback-confirmed-decision-reflect-in-authoritative-spec`。(3) 計画 surface への同一ターン反映（2026-07-02 Rs D2 承認）: 地図（`docs/logical_decomposition.html` 現在 frame）+ 該当 node state.md を更新し、manifest §2 は `build_nest_snapshot.py --emit-manifest-section` で再生成する（tempfile+mv + flock、contention 時は次ターン繰延を loud 記録）。manifest への UPDATE block 追記は禁止 — node 追記は state.md のみ（LTM-1 v1.2 注記準拠）。反映 commit は explicit-path の atomic commit とする。
```

**hunk-1 の 2 delta (承認 draft との差、Rs retro-ACK 待ち = ACK A2):** (i)「（2026-07-02 Rs D2 承認）」の挿入 (Rs 未提示の provenance 注記; 事実として真)、(ii)「manifest への UPDATE block 追記は禁止」の bold 落ち。semantics 不変。

### 11.2 as-landed D5 権限 rows (Vault Write Permissions.md から live 抽出)

```
| `07-Design/` | ✅ Write | ❌ Read-only | — | 設計はRs専権（例外: `00-DESIGN-STATUS-LEDGER.md` 行更新 = CLAUDE.md §運用4 mandate） |
| `00-Project-Management/` | ✅ Write | ✅ Update | — | NEST 運用 file 群（manifest §2 = GEN 領域につき生成器経由のみ・UPDATE block 追記禁止、LTM-1 v1.2 準拠。2026-07-02 Rs D5 承認で行追加） |
| `docs/` 地図（logical_decomposition*.html、repo 側） | ✅ Write | ✅ Update | — | THE MAP（現在 frame 追記 + atomic commit。同上 D5） |
| node dir（`T-*/state.md` ほか vault 直下 node dirs） | ✅ Write | ✅ Create/Update | — | node DB（層A source of truth。同上 D5） |
```

**draft 超過分 (Rs ACK A1):** 07-Design row の LEDGER carve-out 明文化 + node-dir row の「ほか vault 直下 node dirs」拡張は Rs 提示 draft (3 rows) に無かった。内容は CLAUDE.md §運用4 mandate の codification で正当、授権が不完全 → ACK or 拡張部 revert。

### 11.3 M6 裁定記録 (mid-flight / deferral rulings)

- **sha-token leg deferral (M6 CC4-CH5 ACCEPT):** M3 dry-run は設計指定の context-anchor 付き extractor ではなく bare-hex 形で測定 (62% FP) — **設計指定 extractor は未評価**。leg は unwired のまま。**owner = %12、condition = B2 window 後に anchor 付き re-dry-run → WARN 配線判断**。checker :93 INFO 行にも明記済。
- **C2 node-id FAIL 昇格の corpus 注記 (CC4-CH10):** 0-FP corpus = 抽出候補 2 件 — FAIL の強さは真だが保護 coverage は狭い (backtick 抽出は HTML/prose からほぼ拾わない)。
- **regen exit-2 = expected (NHA-R2):** `--emit-manifest-section` は legacy state.md ~81 件の SOFT で慢性 exit 2。**運用 = 「exit 2 は既知 baseline、NEW soft item の増分のみ review」**。CLAUDE.md hunk への注記追記は Rs ACK A6。
- **M2-delta(i) の decide→record→implement 順序逆転 (CC4-CH9):** commit ef24f3ab36 (19:48) が裁定 stamp (19:5x) に数分先行 — 同 session・honest stamp・層2 済。以後は ruling-before-commit を厳守。
- **地図 C1 の 24h 化 + 今ここ as-of stamp (NHA-R5):** as-of stamp = M6 で landed。C1 per-surface 24h 化 = 候補のまま (未実装、必要なら次 iteration)。
- **first-tracked files (CC5-CH4/CC4-CH8 開示):** cce2975dc8 = validate.sh + build_nest_snapshot.py / 21c4c92aae = operational-rule-LTM-1.md / 5b2c7dff5c = LL-ApproachCable-BugHistory.md (+LEDGER は既 tracked) / ef24f3ab36 = index.md / 55dae1a15a = Vault Write Permissions.md / f60eebf3ee = .gitignore 既存 uncommitted ~27 行を同時 first-commit (root-cleanup 由来)。**step rollback = 外科的 edit 必須 (plain revert は file 全削除)**。GOALS.md pre-chain = 復元不能 (Rs 承認済の意図的破棄; 断片 = PLANNING_AUDIT_REPORT.md:28)。

### 11.4 M6 checker 堅牢化 (fail-first 証跡付、commit 参照)

1. crash-sentinel fail-closed (CC3-M2/CC4-CH7): COMPLETED sentinel + trap C0 FAIL。証跡 = 旧 code 注入 crash → LAYER7_FAIL=0 (fail-open 実証) / 新 code → C0 FAIL + LAYER7_FAIL=1。
2. `--check-manifest-section` の HARD 検出 (CC3-M1): dup node_id 注入 → rc=1 + C3-DATA (旧 = rc=0 blind、CC3 実測)。clean → rc=0。
3. C2 membership = snapshot ∪ §2 GEN (CC3-M3/NHA-R3): T-VBD-AC = snapshot 0 / §2 1 → union で archived-ref FP 消滅 + emit-lag FP 消滅。FAIL message に fix-hint 追加。
4. C2b 'LEDGER row N' leg 新設 (CC4-CH3 → DoD (c) を実検出化): row-999 注入 → WARN 発火 / SOMA:82 row 53 → resolve = quiet。**規約 = 行番号** (row 53 = L53)。limitation: 無 space 形 (row43) は未検出 — 地図 :165 の 1 件は目視確認済 (L43 = re-grasp row、valid)。
5. C1 LEDGER stamp anchor 化 (CC3-M5): '^## Ledger (as of' 固定 (prose の as-of 誤 pin 防止)。
6. .manifest_gen.lock → .gitignore (CC3-M4)。

### 11.5 M6 検証 verdict 要約 (8 agents)

層2: CC2 spec-fidelity = 2H/4M/2L (records 層; 全 fix or ACK 化) / CC3 mechanism = 0 CRIT/HIGH, 2M+1ML (全 fix) / CC4 (Fable slot 初適用) governance = 4H/4M/2L (records+DoD; 全 fix or ACK 化) / CC5 integrity = 保存性 CLEAN (全 sha 独立再計算一致)、1H (map pointer → fix 済) / CC6 NHA = **IMPROVED (null 棄却)**、R2/R3/R5 fix 済。層5: STRUCT = PASS (F2 tracking → fix 済) / RULE = PASS-conditional (F1/F2 records → fix 済 + omission 記録) / SSOT = sidecar HIGH → 再 pin 済、F3-F12 fix or ACK 化。**rule-check stage1/2 の %10 実行記録は欠落 (RULE-F2) — 遡及せず loud omission として記録: Tier-0 相当は 層5 RULE agent が独立再検証 clean。**
