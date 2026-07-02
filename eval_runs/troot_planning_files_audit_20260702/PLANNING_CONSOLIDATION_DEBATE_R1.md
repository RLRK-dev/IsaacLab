# PLANNING_CONSOLIDATION_DESIGN 5体 pre-debate R1 — adjudication (2026-07-02)

**CC1 (lead %12) REBUT_OR_ACCEPT。** 対象 = design v1。挑戦 33 件 (CC2: 8 / CC3: 9 / CC4: 8 / CC5: 8) + CC6 NHA (CHANGE_JUSTIFIED_WITH_REDUCTIONS, R1-R5)。**全 33 件 ACCEPT または PARTIAL (REBUT 0)** — v1 の 4 コア + 3 層アーキテクチャ自体への反証は無く、全 CRIT/HIGH は契約・権限・計装の欠陥であり v2 で修正可能。

## 判定表 (theme 集約; 個票は各 agent 出力参照)

| # | theme (集約元) | worst SEV | 判定 | v2 反映先 |
|---|---|---|---|---|
| 1 | LTM-1 manifest direct-write 永久禁止と層A の正面衝突 + P2-10 LTM-1-note 無宣言 drop + §5.3 tempfile+mv 欠落 + _edit_requests 処遇未定義 (CC2-1/-4/-5) | **CRIT** | **ACCEPT** | §3.5 LTM-1 v1.2 note を scope-in (Rs-gated)。state.md 変更=deposit / 再生成=drain / tempfile+mv + flock / UPDATE block 禁止を注記化。N1 修正。manifest §1/§4 = 温存宣言 |
| 2 | T4 freeze banner = Rs 専権 07-Design への CC 書込 (CC4-1 CRIT + CC2-2 HIGH、2体) | **CRIT** | **ACCEPT** | T4 = Rs-gated 編集に変更 (§9 決裁項目 D4)。banner 文言は CC 起案、書込は Rs 承認後 (or Rs 実施) |
| 3 | 生成器 adapter が lossy (実測 76/233 fallback、status 6 件強制変換、135/238 IN_PROGRESS) → §2 に誤 status を SSOT として書込み、C3 は生成器-vs-生成器で検出不能 (CC3-1) | **CRIT** | **ACCEPT** | M2 契約: strict mode (status verbatim passthrough / fallback・skip・重複で nonzero exit + MANUAL-REVIEW list) + 忠実性 acceptance test (§2 status 列 == 各 state.md `grep '^status:'`) + 非正準 status は raw 表示 + legend |
| 4 | M1/M2 書換の並行 append 消失 (baseline commit 14 分後に実例) + quiet window 無定義 + flock は Edit-tool 書込に無効 (CC5-1 CRIT/-2/-5 + CC6-R3、実質 3 体) | **CRIT** | **ACCEPT** | M-entry protocol: porcelain-clean 前提 + hold-notice dispatch→ACK (Tier 2) + 書込直前 re-read collision gate (porcelain empty-or-own + tail sha256) + salvage-patch→checkout rollback + quiet window を地図含む全共有 surface に拡大。flock は script 書込内のみに限定表記 |
| 5 | C2 day-1 不成立: sha 判定は日付 8-hex で誤爆 (実測 35+ FP)、T-ROOT/umbrella は state.md 無しで FAIL、真性 dangling 3 件 (optE 系) (CC3-2/-3 + CC5-4、2体×2票) | HIGH | **ACCEPT** | C2 = **WARN 出発**、抽出契約 (≥1 [a-f] or `commit` 隣接 anchor / node-id は backtick 引用構文 anchor)、membership は nest-snapshot node set (stub 含む) 照合、committed allowlist、**dry-run 0-FP 実測後に FAIL 昇格**。真性 dangling 3 件の処遇 = Rs 決裁 (§9 D6) |
| 6 | UPDATE-block 禁止が pane の読む場所に無い + C5 不在 (CC5-3) | HIGH | **ACCEPT** | hunk-1 に禁止文明記 + manifest header banner + **C5 新設** (非 GEN 領域の `^## UPDATE` 数凍結照合 FAIL)。LTM-1 note (theme 1) にも同旨 |
| 7 | T7 nest-tracker が M-step 未割当のまま M2 テストが untracked artifact を書換 (CC5-6; CC3 検証中に実際に再生成発生、backup 保全済) | HIGH | **ACCEPT** | **M1.5 新設**: M2 前に `git add docs/nest-tracker/` + commit。CC3 の副作用 (nest-snapshot.json 更新、backup = scratchpad/nest-snapshot.json.bak) を記録 |
| 8 | GOALS.md 5 行化が live consumer を破壊 (verify_goal_contract.sh:55-57 / orchestrator interrupt / RUN_METRICS goal_context) (CC4-2) | HIGH | **ACCEPT** | T3 改: 新 GOALS = pointer + **goal_evidence 契約 2 行を verbatim 温存** (最小 blast radius; harness 無改修)。M4 検証 = consumer sweep + `verify_goal_contract.sh` 実走 PASS。INIT_CODE_A/B の GOALS 依存節の処遇は §9 D7 (Rs 認知) |
| 9 | 承認範囲: ①=起案 GO / ②=CLAUDE.md 類型承認のみ、M1-M4 実装 GO は未取得 (CC4-3 HIGH + CC2-7 LOW + CC6-R4、3体) | HIGH | **PARTIAL** | ② type-level 承認は Rs verbatim「①②承認」(② を CC 側 message で定義済) で real — CC4 VERIFIED-OK 同旨。ただし**実装 GO gate を M-table に明記** + M5 は最終 hunk 4 line-site verbatim の Rs GO 後 (commit 前) に限定 |
| 10 | validate.sh harness fail-open (crash → PASS) (CC3-5) | MED | **ACCEPT** | layer 7 は trap EXIT で contract 行を無条件 emit。run_layer の absent-line=failure 化は optional 提案として §9 D8 (layers 1-6 に波及するため別決裁) |
| 11 | C1 content-date 計装が方向曖昧 (Gantt 未来日付で永久 mask) (CC3-6) | MED | **ACCEPT** | C1 = per-surface `last_updated` stamp (manifest frontmatter 既存 / 地図 live header に `<!-- last_updated -->` 追加 / LEDGER header 行) vs log.md newest heading の片側比較。content scrape は fallback |
| 12 | 地図 §1 tree/Gantt の生成 pipeline が eval_runs 常駐 + TASKS/NOW 手書き = 隠れ計画 surface;「SSOT 連動」footer は現状虚偽; GEN marker は srcdoc 内で不成立 (CC3-7) | MED | **ACCEPT** | GEN 領域 = plain HTML 限定を明記。gen_simplified_tree.py / gen_gantt.py を scripts/ へ常設昇格 + refresh 契約文書化、Gantt TASKS は「手保守 curated view」と正直に再分類し footer 文言修正 (M1) |
| 13 | 00-PM が権限 matrix 不在 (default-deny) + hunk-1 が matrix と未整合のまま恒久 rule 化 (CC2-3 + CC4-4、2体) | MED | **ACCEPT** | §9 D5: Vault Write Permissions.md への行追加 (00-PM / docs 地図 / node dirs) を Rs 依頼 (CC が文面起案、02-Workflow は Rs landing)。hunk-1 に権限根拠句 |
| 14 | hunk-2 :72 の「現 eval_runs dir」= 自己腐敗ポインタ新設 (CC4-5) | MED | **ACCEPT** | :72 差替先 = 安定 surface のみ (LEDGER + 地図)、現 run へは LEDGER 行経由の間接参照 |
| 15 | freeze/pointer 化後も「live/SSOT」を主張し続ける 6 参照 (index.md:127 / LL-ApproachCable:14 / LEDGER:42 tail / Knowledge Index:81 / skills 2 表) (CC4-6) | MED | **ACCEPT** | M4 に **stale-say sweep** 追加 (全て CC-writable、同 commit) |
| 16 | C4 の mtime proxy は層A regen で常時 reset + RS71 Rs-pending diff で恒常 WARN (CC5-7 + CC3-9) | MED | **ACCEPT** | C4 = 「git diff 有 AND last-commit-age >24h」(commit-age 語義) + 対象 file 列挙 + Rs-pending suppression 注記 file (成長時のみ WARN) |
| 17 | node state.md の §2.3 非準拠 (session id `#s1` 無し等) (CC2-6) | LOW | **ACCEPT** | 本 turn で state.md 修正 (実施済み印は v2 §0) |
| 18 | M1 検証強度 (byte 数は同長破損を素通し / render 確認に基準無し) (CC3-8 + CC5-8) | LOW | **ACCEPT** | sha256 領域照合 + 再結合等値 + `google-chrome --headless --dump-dom` exit-0 + html.parser 整形式 (両 file) |
| 19 | .gitignore 反転が先行判断 (repo_root_cleanup_inventory_2026-05-26) を無引用 (CC4-7) | LOW | **ACCEPT** | T3 に supersession 1 行 |
| 20 | handoff.md redirect = vault-root 新 file (CC2-8 + CC6-R2、2体) | LOW | **ACCEPT** | T8 から**分離・deferred** — §9 D9 で Rs 選択 (redirect or VaultProtocol :228 実パス化 1 行 [Rs 専権、そちらが清潔]) |
| 21 | 層B の発火 cadence 未配線 (preflight は validate.sh を呼ばない / V9 gate は --layer 4 固定 / --no-verify 慣行が pre-commit を bypass) — 「存在≠防止」は layer 5 D1 で実証済 (CC6-R1) | (NHA) | **ACCEPT** | layer 7 呼出を `audit_thread_vault_current_state.sh` (V9 wrapper、編集前後に必須実行) に追加 = 編集時点で必ず発火。§5 の cadence 記述を正直化。--staged-only 時は layer 5 同様 SKIP 明記 |
| 22 | C2 は「参照先不在」型のみで「あるべき node の不在」(off-map 型) は捕捉不能 — over-credit 禁止 (CC6-R5) | (NHA) | **ACCEPT** | §3 に honest-scope 注記 (off-map guard = 層C prose + 層A regen 補助) |

## NO_ACTION_EVALUATION + DECIDE

- **NHA 判定 = CHANGE_JUSTIFIED_WITH_REDUCTIONS** (HOLD ではない)。A0 (P0 で停止) は喪失 vector を閉じたが、(i) 毎 session の接地経路に残る 2 つの誤誘導 surface (CLAUDE.md:72 死亡ポインタ / GOALS 有害記述)、(ii) 監査 §3「現在何が真かを 1 surface で読めない」、(iii) Rs standing directive (少数化) を解決しない。A1 (バラ実施) は生成契約の統一性を失い G2/G3 未達で dominated。A2 は Rs 棄却済。
- **DECIDE = PASS-with-revisions**: ACCEPTED CRIT/HIGH は全て v2 に修正として反映 (BLOCK 該当なし — どの CRIT も設計契約の追補で解消し、アーキテクチャ棄却を要求しない)。CC6 reductions R1-R5 全採用。
- **実装は未開始**: v2 + 最終 hunk 文言 + §9 決裁項目を Rs に提示 → **実装 GO 取得後に M1** (theme 9 の是正をここで自己適用)。

## 検証メタ

- 5体は独立 context・全て on-disk 実測 (CC3 は生成器を実走、CC5 は git 実査、CC4 は consumer grep 全 build path)。%12 は各 CRIT の 1 次証拠 (LTM-1 :426-427/:530/:607、権限 matrix 07-Design 行、CC3 の実走ログ、14:02 uncommitted block) を spot 確認済。
- CC3 副作用: docs/nest-tracker/nest-snapshot.json が検証実走で再生成された (untracked、29 diff-line stale だった; pre-run backup = 本 session scratchpad/nest-snapshot.json.bak)。D1 の文書化された修復操作と同一のため無害と判定、M1.5 で track 化する。
