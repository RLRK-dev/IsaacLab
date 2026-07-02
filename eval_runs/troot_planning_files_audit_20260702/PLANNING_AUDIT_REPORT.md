# 計画ファイル群 監査報告 + 改善提案 (2026-07-02)

**Auditor:** RS-TECH-LEAD (%12) + 3 並列監査 agent (Visual Tree / NEST / SOMA-RS71-LEDGER)。read-only 監査、編集ゼロ。
**Ground truth 基準:** 2026-06-30 以降の Rs 確定事項 F1-F7 (re-grasp COMMIT `bcb7393ec8` / P1 PASS / P2 BLOCK / Q3-first reframe / Q1 UNIT pending / node T-ROOT-optE-route-dapg-C1C2 / pin(b) slot① / env6-VBD DISCARD)。
**機械 gate:** V9 freshness audit + validate.sh --layer 4 = PASS (0 err) — ただし本監査で semantic staleness は 2 日分検出 → V9 の盲点 (提案 #11)。

---

## §1. 全体判定

1. **計画ファイル群は「06-30 09:44 で凍結した過去」を現在として提示している。** 07-01/07-02 の確定事項 (F1-F5) を反映するのは LEDGER row43 (07-01 21:46) と log.md のみ。Visual Tree / manifest / SOMA / NEST state.md 群 / nest-tracker はすべて 06-30 以前。
2. **off-map 実行が発生済:** 現 active node `T-ROOT-optE-route-dapg-C1C2` (Rs 承認 07-01) が**全計画 surface に不在**のまま P1 実行済 = LTM-1 §3.1 起動条件 + 「record BEFORE execute」invariant の破れ。
3. **成否 SSOT 群に git 保全がない:** SOMA / LEDGER / RL-Routing-Progress / manifest = **UNTRACKED** (履歴ゼロ)、GOALS.md = gitignored (.gitignore:108)。tracked は RS71 と Visual Tree のみで、**両方に未コミット diff** (RS71 = Rs 決定 3 hunks が ~8 日未コミット / Visual Tree = 地図履歴 ~5 日分)。checkout/reset 一発で Rs 決定・地図履歴が silent 消失する状態。
4. **構造劣化が進行:** LEDGER row54 = 単一 table 行 31,429 chars (ファイルの ~60%、13 増分の追記ログ化、ugrep が complexity error)。manifest 677KB の 80% が narrative の inline 重複 (「view」の自己宣言に反する)。行番号 cross-ref は既に drift (SOMA:82 →「LEDGER row 53」= 現在は空行)。

## §2. 構成マップ (SET の実態)

| surface | 役割 (宣言) | 実態 / 健全性 |
|---|---|---|
| `docs/logical_decomposition.html` (460KB, tracked+dirty) | THE MAP (§1 Visual Tree + Gantt) | 3-in-1 複合 (簡易tree iframe + Gantt iframe + 旧詳細 archive 2.3K 行)。live 部は snapshot 生成宣言 vs hand-edit 先行の**生成契約 drift**。同一 node が file 内で 3 状態に分岐。newest frame 06-30 09:16、5 日分未コミット |
| `00-PM/project-tree-manifest.md` (677KB, untracked) | NEST tree view (遅延整合可) | 80% narrative 重複。§2 node 表は 06-23 re-seed 世代 13+ node を**ゼロ収録**。§3 session 表は 04-28 の死表。UPDATE 群が逆順追記 |
| `00-PM/operational-rule-LTM-1.md` (34KB) | NEST 仕様 (SSOT) | 仕様自体は安定。ただし実践は「minimal-schema node」(session_history 欠落) で**仕様と乖離** (v1.1 のまま未改訂) |
| NEST node state.md ×~230 + nest-tracker | node 実体 + 正規ビュー | newest 06-24。現 active node 不在。`.sha256` sidecar handoff は 05-03 で停止 (memory 系に事実上移行)。nest-tracker dir は untracked |
| `04-Specs/SOMA.md` (350KB, untracked) | 目標/Phase/Pipeline SSOT | F4 (pos/pose-random) は明記 ✓。:82 tail が 06-30「exploration IN-PROGRESS」のまま = re-grasp 成功が読めない。更新履歴 section は 05-24 で死亡。env6-VBD DISCARD 未記載 |
| `04-Specs/RS71-System-Spec-SSOT.md` (42KB, tracked+dirty) | INVARIANTS SSOT (session 毎 auto-echo) | 内容は正確・最新 (06-25)。**Rs 決定 3 hunks (B2 fidelity boundary / deploy-req supersession / LIFT DATUM) が ~8 日未コミット** = 最重要 loss-vector |
| `07-Design/00-DESIGN-STATUS-LEDGER.md` (52KB, untracked) | 設計成否 SSOT | row43 (re-grasp WORKING 07-01) ✓ 最新。**row54 mega-row 31.4KB** / header「as of 06-21」stale / row54 の OPEN が row43 と矛盾 / slot①=pin(b) 07-01 確定が未 bank |
| `07-Design/RL-Routing-Progress.md` (361KB, untracked) | RL 進捗 (CLAUDE.md ポインタ先) | **死亡** (05-28 停止)。「現在地」= DISCARDED env6-VBD 系譜。後継 surface 未指定 — 現 RL track (DAPG whole-route) の進捗は eval_runs + log.md + memory にのみ存在 |
| `GOALS.md` (4.7KB, gitignored) | SOMA への純ポインタ (CLAUDE.md 宣言) | 実態は 03-20 凍結 dashboard。**有害な誤記述**: 「Track A: PhysX (current production)」「CUDA_VISIBLE_DEVICES 不使用」(CLAUDE.md GPU 規則と直接矛盾)、Franka 前提 (現 UR5e) |
| `index.md` (8.5KB) | vault 入口 | 00-Project-Management section 自体が欠落 (manifest/LTM-1 へ到達不能)。07-Design 件数 5 (実 11)。`VaultProtocol.md:228` が読めと指示する `thread-vault/handoff.md` は**不存在** (パス矛盾) |

## §3. 整合マトリクス (確定事実 × surface)

| 事実 (Rs 確定) | Visual Tree | manifest/NEST | SOMA | RS71 | LEDGER |
|---|---|---|---|---|---|
| F1 re-grasp WORKING + commit (07-01) | ✗ absent | ✗ absent | ✗ stale (06-30 IN-PROGRESS のまま) | — (scope外) | ✅ row43 |
| F2 P1 whole-route PASS (07-02) | ✗ | ✗ | ✗ | — | ✗ |
| F3 P2 BLOCK / Q3-first / Q1 pending (07-02) | ✗ (+Q1-3 token 衝突 4 重) | ✗ | ✗ | — | ✗ |
| F4 pos/pose-random deploy req (06-24) | — | — | ✅ :28 | ✅ (未コミット) | — |
| F5 pin(b) slot① 確定 (07-01) | ✗ (06-30 で停止) | △ 06-30 迄 | ✗ (06-30 option 列挙のまま) | ✗ (:43 は 06-21 の「DOWNGRADED」) | △ row54 は 06-30 迄 / row43(c) に C2-DEFER のみ |
| F6 env6-VBD DISCARD (06-26) | △ 一部 bar 未反映 + legacy chip が n-active のまま | ✅ (06-23 note) | ✗ | ✅ | ✅ FAILED item2/3 |
| F7 retention thread 帰結 | △ 06-30 朝迄 | △ | △ | ✗ | △ |

**結論:** 「現在何が真か」を 1 surface で読める場所が存在しない (最も近いのは LEDGER row43 + log.md tail)。

## §4. 改善提案 (優先度付き / 実行権限つき)

### P0 — 損失防止 (即日)
| # | 提案 | 対象 | 権限 |
|---|---|---|---|
| 1 | **RS71 の未コミット 3 hunks + Visual Tree の 5 日分を commit** (Rs 決定の git 保全) | RS71 / logical_decomposition.html | CC 実行可 (Rs 一言承認; --no-verify THREAD practice) |
| 2 | **SOMA / LEDGER / manifest / RL-Progress を `git add` で管理下に** (.gitignore は /GOALS.md のみ→追加可能) | 4 files | CC 実行可 (Rs 承認) |
| 3 | **off-map node の即時記録**: T-ROOT-optE-route-dapg-C1C2 の state.md + 簡易tree node + 学習 lane bar + 07-02 frame (F1-F5 反映)。Q token 衝突回避に新 namespace (例 `DQ1/DQ2/DQ3`) | manifest / state.md / Visual Tree | CC 実行可 (Rs 承認; 00-PM・docs は CC 書込域) |

### P1 — 現在状態の正しさ
| # | 提案 | 対象 | 権限 |
|---|---|---|---|
| 4 | SOMA :82 tail 更新 (re-grasp COMMITTED / pin(b) / C2-DEFER / env6-VBD DISCARD 追記) + 「LEDGER row 53」dangling 修正 + 更新履歴 section の再開 or 閉鎖注記 | SOMA.md | **Rs専権** (04-Specs) — 案文は CC が用意 |
| 5 | LEDGER 衛生: row54 の 13 増分を per-node log file へ分離し 1 行 status 化 / header「as of」更新 / row54 の OPEN を row43 pointer で閉鎖 / **slot①=pin(b) 07-01 確定を bank** / 引用は行番号でなく doc-name キー | LEDGER | CC 保守可 (mechanism owner 系; status は Rs-confirmable) |
| 6 | GOALS.md を宣言通りの**純ポインタに縮約** (or 削除+CLAUDE.md 行修正)。少なくとも PhysX-production /「CUDA_VISIBLE_DEVICES 不使用」の有害 2 記述を除去 | GOALS.md | CC 実行可 (Rs 承認) |
| 7 | RL-Routing-Progress に **freeze banner** (「≤05-28 歴史・env6-VBD 系譜」) + CLAUDE.md「RL進捗」ポインタを後継 (eval_runs 現 dir + LEDGER) へ差替 | RL-Progress / CLAUDE.md | CLAUDE.md 変更 = **Rs 指示必須** |

### P2 — 構造的持続性
| # | 提案 | 対象 | 権限 |
|---|---|---|---|
| 8 | manifest rotation: Apr-May 本体を archive file へ / live manifest ≤50KB / §2 は state.md から**再生成** (`build_nest_snapshot.py` 既存) / narrative は log.md pointer のみ (YAML 内 24KB 一行 append-log 禁止) | manifest | CC 実行可 (Rs 承認) |
| 9 | Visual Tree の live/archive 分離 (~30KB live + archive) + **生成契約修復** (snapshot 更新→再生成 or「SSOT 連動」footer 削除 / nest-tracker を git 管理 / gen_*.py を eval_runs から常設場所へ) + frame 追記ごと atomic commit 運用 | logical_decomposition.html ほか | CC 実行可 (Rs 承認) |
| 10 | index.md 更新 (00-PM section 追加・件数修正) + **handoff.md パス矛盾解消** (thin redirect 設置 or VaultProtocol :100/:228 の実パス化) + LTM-1 v1.2 note (minimal-schema node の合法化 or session_history 復活) | index / VaultProtocol / LTM-1 | CC 実行可 (Rs 承認); LTM-1 改訂 = **L3 cascade** |
| 11 | **鮮度 gate の盲点封鎖**: V9 は無時刻 RUNNING 検出のみ → validate.sh に「planning surface の newest 日付 vs log.md newest の乖離 >48h で WARN」を機械追加 | scripts/validate.sh | CC 実行可 (Rs 承認); validate logic = L3 |

### 運用ルール提案 (files でなく習慣)
- **確定事項の即反映 gate (§運用4 書込側) の対象に「計画 surface」(Visual Tree frame + manifest/state.md) を明示追加** — 現行 gate は LEDGER+spec を対象にし、地図/NEST が漏れる (今回の off-map 実行の根本)。CLAUDE.md 変更 = Rs 指示必須。

## §5. 明示 caveat
- 本報告は read-only 監査。**どの提案も未実行** (07-Design/04-Specs/CLAUDE.md は Rs専権のため特に)。
- F2/F3 は log.md (07-02 05:38 エントリ) には bank 済 — 「どこにも記録がない」のではなく「**計画 surface 群に**ない」が正確。
- 監査 agent 3体の主要主張は %12 が on-disk spot-verify 済 (untracked 状態 / gitignore:108 / row54=31,429 chars / dispatch map)。
