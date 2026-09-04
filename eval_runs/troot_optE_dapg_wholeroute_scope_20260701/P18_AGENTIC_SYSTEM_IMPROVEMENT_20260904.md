# エージェント型 AI 化の改善提案 v2 — herdr 上の CC pane 群を「自ら考え・行動し・環境から feedback を得て改善する系」にする

**版** v2（v1 = commit `acb4ff2c2a`・sha256 `29916eb76dce7fcf…f1548` を supersede。v1 は 5 体検証 cycle 1 で **FAIL**（記録 = `P18_AGENTIC_VERIFY_CYCLE1_20260905.md` @ commit `dc10ba462d`）。本 v2 は受入 40 項目を反映した改訂で、**何も build していない**）
**作成** p18 (T-ROOT-OPS-SUPERVISOR = role label・⚠ NEST node ではない〔DDR #34・`00-DESIGN-STATUS-LEDGER.md:138`〕ゆえ本 task は role-bound で NEST 外を走る) — 2026-09-05（date 実測は各節）
**契機（custody）** Rs1 (the human) 直接指示・当卓 pane・transcript `~/.claude/projects/-home-rlrk-IsaacLab/1c3d805c-2a9a-4b6d-bba2-ae7d479862e7.jsonl:38094`（type=user・2026-09-04T07:24:04Z = 16:24:04 JST）逐語:「エージェント型AI（Agentic AI）とは、単に指示に応答するだけでなく、自ら考え、行動し、環境からフィードバックを得て改善を行うシステムのことを指すが、IssacLabにおいても 高度なエージェント型AIを構築して目標を実現したい。現在のherdr上の各paneにおけるエージェントの集まりを用いてエージェント型AIとしたい。エージェントの役割分担、エージェントの数　、NEST Tree等　改善点をあげて、次にそれらの点で改善を実行して。」
**読み** 「改善点をあげて、次に…実行して」= **一覧が先・実行が後**。一覧 = 本 file。実行のうち **新規 file を作る項は CLAUDE.md:46（ハードストップ: タスク指示に無い新 file 作成）に従い Rs1 の一語の後**（§5 #1）。
**L-triage** L3（NEST 仕様 `operational-rule-LTM-1.md` §9 に触れる項を含む）。⚠ l-gate 混合則（`~/.claude/l-gate.md:33`）により **task 分割を提案**（§5 #7）: (a) 卓 tooling = L2 / (b) NEST §9 改訂 = L3。
**動かさないもの** ⛔ §0 不変前提（DUAL-ARM / 88 mm span / IK のみ・kinematic trick 禁止 / gripper 幾何 LOCK）・run 認可（Rs1 のみ）・動画の物理妥当性判定（Rs1 の目）・04-Specs/07-Design の read-only・役名 = Rs1 割当・pane 間 routing 規則（送信元は p18 へ提出し宛先へ直送しない）。
**語** 造語なし。初出の語: 「announce-first」= 実装前に「何をどこへ着地させるか」を先に message で告げる運用／「parent-relative leg」= 検証者が対象 commit を **その親 commit との差分**で検査する脚／「content-sha 等号受入」= 着地 blob・worktree・当卓・検証者の 4 者の content sha256 が等しいことをもって受入とする形。

---

## §0 v1 → v2 の変更（cycle 1 で捕らえられた誤り・すべて disk で再確認済）
| v1 の記述 | 実際 | 出典 |
|---|---|---|
| manifest の食い違い 2 件・実体更新 07-27 | 234→252 は 08-06 `c45c319f0b` で訂正済（frontmatter :4 の注記だけが古い）。root は 08-08 item-9 裁定 (i) で **既に裁定済**（`P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md:59,:70`・`CLAUDE.md:131`）⇒ 残るのは p6 の frontmatter `root_node_id` 機械更新のみ。manifest は 08-08/08-09 に 5 commit 更新 | 当卓の frontmatter 部分読み（§1.5 の 4 例目） |
| pin の法 = pZ §1391 | §1319（hub 標準）:「hash は関数名を連れて初めて pin になる」（`P18_CLAMP_COURT_EVIDENCE_LEDGER_20260727.md:45922-45923`）。同行 commit 要件は当卓の拡張 | 節番号の取り違え |
| A3: p11 が court word 受諾待ちで idle | §1401:27 = **controller 側**が p11 の court word を待った（p11 は発行側）| 前提不成立 → A3 撤回 |
| cc 不達 2 件（p4 / p6 §1380） | §1366 = ingestion lag（「relay lag・矛盾なし」）／§1380 に p6 不達の記述なし／**真の不達 1 件 = 当卓の bank-without-send（§1296）** | 引用先不在 |
| §1.2 の数（47/34/12/26…） | 少なくとも 3 つの (範囲, query) 対が混在・query 未保存 | §1.2 を全面再計数 |
| 25 日 commit 0 | 0 は 08-10 10:07 → 09-04 16:14:37 の区間。以後 record commit 2（`043e10901b` `acb4ff2c2a`） | 自 commit 後の古い数 |
| 16 pane | `herdr agent list` は 20（w1 4 = 別 project）・**w2 = 16**。p9 PAPER-AUTHOR 行の欠落 | 母集団の明示不足 |
| D1 の配達述語 = 決定的 | `wait output --match` は入力欄・過去 scrollback にも一致（5 ms 実測）／`wait agent-status working` は既に working なら即 true（22 ms 実測）／判別子は行頭 `›`(transcript) vs `»`(入力欄)（memory 07-26） | 述語が判別しない |
| pZ に commit 権限が無い | pZ 自身の「grant 不在」申告（memory `feedback-authority-to-act-must-be-pinned…:15`）| 出典の置換 |
| chain 所要 fork 10 分 | 7.3 分（p0 `m-p0-259R` 23:02:24 → p4 `m-p4-245` 23:09:42）／鏡像 38 分は §1393 見出しの「08:4x」起点 = 33.5–42.5 分 | 未測の数 |

---

## §1 現状の実測（2026-09-05 00:3x–01:0x JST・command 併記・再測可能）

### 1.1 pane topology（`herdr agent list` → 20 entries・workspace w2 = 16）
| 区分 | pane（w2:）| 前窓（08-09 17:30 → 08-10 10:07）の稼働 |
|---|---|---|
| hub | p18 OPS-SUPERVISOR | 稼働（当卓） |
| 核 6 | p4 RS-TECH-LEAD（= Rs2 代理）／p0 IMPL-BUILDER／pZ IMPL-VERIFIER／p5 SKILL-DETAIL-DESIGN／p6 PLAN-KEEPER／p11 ARM-CONTROL-DESIGN | 稼働 |
| 分析 2 | pB LOG-ANALYST／pC VIDEO-ANALYST | 不使用（DoD 動画は Rs1 が直接判定・run.log の行引用は p0 手作業 §1383/§1395） |
| WMSO 5 | p12 RS-TECH-LEAD2／p14 IMPL-BUILDER2／p15 IMPL-VERIFIER2／p16 WMSO-DESIGN／p17 SKILL-DESIGN | dormant（設計どおり。⚠ p16/p17 は SKILL 分解・単位の**決定卓**〔`CLAUDE.md:348`〕ゆえ cc から外してはならない） |
| 退役役名 2 | pV T-ROOT-COORD／pW T-ROOT-COORD2 | pane 生存・役は 07-20 ARCHIVED |
| pane 無し | p9 PAPER-AUTHOR（役名登録のみ）・OPS-SUPERVISOR-CODEX・VT-DESIGN（退役名） | — |
役名登録 `scripts/validations/nest_role_labels.txt` = 43 行・19 役名（全文読み）。**live 16 ⊂ 登録 19・pane 無し 3**。⚠ 短 id は workspace を跨いで衝突（w1:pV と w2:pV）⇒ 宛先は常に `w2:pN` 完全修飾。
commit: **0**（08-10 10:07 → 09-04 16:14:37）。以後 p18 の record commit 2。

### 1.2 前窓の稼働（**1 つの範囲に統一**: commit 窓 = 08-09 17:30 → 08-10 10:07〔最初 `93adb43eb7` 17:32:06・最後 `cf0a14cea3` 10:06:53 = 16.6 h〕／台帳 = §1344–§1406〔`P18_CLAMP_COURT_EVIDENCE_LEDGER_20260727.md:46171-46838`・§1344 の初出時刻 17:24:48〕）
| 量 | 値 | query（逐語・範囲 = 上） |
|---|---|---|
| commit | 134 | `git rev-list --count --since='2026-08-09 17:30' --until='2026-08-10 10:07' HEAD` → 7.4 min/commit |
| 台帳の節 | 63 | `grep -c '^## §'` |
| hub の dispatch id | 28 | `grep -oE 'm-p18-[0-9]+' \| sort -u \| wc -l` → 35.5 min に 1 通 |
| 見出しに Rs1 を含む節 | 28 | `grep '^## §' \| grep -c 'Rs1'`（人間の一言を見出しに持つ節の代理量）|
| 見出しに 訂正\|撤回 を含む節 | 18（28.6 %） | `grep '^## §' \| grep -cE '訂正\|撤回'`（当卓限定 `当卓.*(誤\|訂正\|撤回)` = 17）|
| custodian bank（他卓 artifact を当卓が commit） | 10 commit | `git log --since=… --until=… --name-only` で `PZ_*` file を含む commit 数（git は author 単一ゆえ卓を識別せず・file 名で識別）|
| stale\|交差\|追い越 の行 | 17 | `grep -cE 'stale\|交差\|追い越'` |
| 部分読み\|分母 の行 | 11 | `grep -cE '部分読み\|分母'` |
| 折返し\|regex\|delimiter の行 | 5 | `grep -cE '折返し\|折り返し\|regex\|delimiter'` |
| correlated assent の行 | 5 | `grep -cE 'correlated assent\|相関した同意'` |
| NO-HIT の行 | 3 | `grep -c 'NO-HIT'` |
| 記憶の時刻\|記憶から の行 | 3 | `grep -cE '記憶の時刻\|記憶から'` |
| 配達 N/N の行 | 5 | `grep -cE '配達 [0-9]+/[0-9]+'`（⇒「毎 dispatch 1–3 回 probe」は台帳に記録が無い。v1 の当該行は削除）|
| pZ の leg 節 | 13 | `grep '^## §' \| grep 'pZ' \| grep -c 'leg'`（pZ の独立検証脚は 5 本: §1369/§1372/§1378/§1391/§1406）|
chain の所要（各 = 開始事象 → 終了事象・台帳節）: dep-1 unlock→受入 **16.7 分**（`m-p4-246` 01:01:40 → `m-p4-247` 01:18:21・§1373/§1379）／fork 決着 **7.3 分**（`m-p0-259R` 23:02:24 → `m-p4-245` 23:09:42・§1365/§1366）／鏡像 Rs1 所見→受入 **33.5–42.5 分**（08:4x → `26f3e3c2e9` 09:22:33・§1393）／(c) 解散 7 分（§1349 見出しのまま・事象未測）。kinonly bundle 認可 1 回で shakedown 10 本（§1379）。DoD run 2 本 = **2 本とも STEP 2 で stall**（§1383/§1395・2 本目は計器が事前予測: witness L 0/240）。
⚠ 上の表は「起きた事の数」であって重大度ではない。⚠ **人数 vs 調整** の判定は本表からは出ない（§3-B）。

### 1.3 NEST
- state.md = 254（`find thread_isaac_lab/thread-vault -name state.md | wc -l`・253 live + 1 `_archive/discarded/`）／manifest §2 GEN 行 = 253（`582dbb74ea` 08-09）／snapshot json = 256。**母集団が違う数を並べない**。
- 活動 chain（C-2 取付→UR15-B→controller）の node `T-ROOT-C3C5-Port-To-Current-Substrate-20260809`: `status: PENDING`・`session_history: []`・`last_updated: 2026-08-10T01:29:56`（state.md:15/:29/:32）。実作業は kickoff（p4・2,235 行）＋当卓台帳＋p6 register で回った ⇒ **preflight D2 WARN（25 日）は「作業が node 化されていない」を正しく検出**（`check_nest_freshness.sh:8-9`）。
- manifest §3「Active session list」の `last_heartbeat` は **既存の heartbeat 機構**（LTM-1:529・Tier 2）で、2026-04-28 の 2 行を最後に停止（manifest:317-322・1 行は dead）。
- 依存語彙: NEST は precedent/blocker の 2 語（v1.1 で 4→2 に YAGNI 縮小・LTM-1:89）。p4 の DEFINE は grade cap／constraint を comment に置いた（C3C5 state.md:19-25）。**現在それを読む validator は無い**（`build_nest_snapshot.py` は precedent/blocker のみ平坦化）。

### 1.4 通信基盤（実測・memory 07-04/07-26 と照合）
- 現状 = `herdr agent send` ＋ `pane send-keys Enter` ＋ viewport 読み戻し。既知の限界: 折返しで probe が割れる（§1355）・送信直後は render 前（§1366）・**配達の判別子は行頭 `›`（transcript 登録）vs `»`＋「tab to queue message」（入力欄 = 未送達）**（memory `reference-herdr-dispatch-2step…:30-34`「自分の文字が見える≠届いた」）・busy な相手は Enter が効かず **Tab** で queue（memory `feedback-verify-message-delivery…:62-69`）・複数卓が同時に送ると **入力欄で融合**（memory `reference-codex-pane-long-dispatch-paste-mode…:55`）・busy な pane へは送らない（Rs 2026-06-20 `feedback-hold-dispatch-to-busy-panes`）。
- herdr の primitive（`herdr wait --help`・`herdr agent --help`）: `wait output <pane> --match <text> --source recent-unwrapped --timeout MS [--regex]`／`wait agent-status <pane> --status idle|working|blocked|done|unknown`／`agent read --source recent-unwrapped`／`agent start`／`pane run`。**実測した意味**: 状態が既に一致していれば **即 true**（22 ms・遷移を待たない）／`wait output` は既存 scrollback・入力欄の文字にも一致（5 ms）／timeout: `wait output` = JSON `error.code=timeout`・`wait agent-status` = 平文 rc=1／`agent read` の text には `❯` 入力行と status bar が含まれる。⇒ **配達証拠は「送信前スナップショットに無く・送信後に `›` 付きで現れる自分の先頭 token」でしか取れない**。
- herdr 自身は send の成功記録を持たない（herdr-server.log の `agent.send` 2 行はいずれも error・CC6 実測）。dispatch 本文は disk に残っていない（30 session dir で 0・CC6 実測）。

### 1.5 当卓の自己捕獲（証拠として載せる）
v1 執筆中に `head -25` で役名 file を読み「8 役名が未登録」と書きかけ（全文 43 行で 19 全登録）。cycle 1 でさらに **manifest frontmatter の注記だけを読んで「食い違い 2 件」と書いた**（本文 :47 は訂正済）。前窓で 2 度 bank した「部分読みの分母」class が、提案書を書く手の中で 3 度・4 度目に発火 ⇒ 法は散文では効かない（memory `feedback-verify-message-delivery…:58`「心がけでは守られない — allocator が拒否する形にして初めて守られる」）。

### 1.6 先行実装・既存機構の棚卸し（§運用4・CLAUDE.md:182）＋ prior-art guard
`scripts/check_thread_vault_prior_art.sh --fail-on-blocker herdr dispatch delivery readback` → rc=2・findings=30 blockers=30（09-05 01:01）。blocker の実体 = 役割 standing 行の一致が大半・**設計上重要な 2 件**: `scripts/dispatch_to_pane.sh`（tmux 時代の送信＋ack 検出＋回復 script・07-04 に herdr 2 段へ退役。header :7-11「ack=UNKNOWN on some Claude states — ALWAYS verify delivery by capture-pane; no blind re-send」）／`eval_runs/phase5_v7_a6_behavioral_2026-05-13/docs/post_v7_disposition_scenarios.md:123`（Known dispatch race: ack=NO でも配達成功あり）。
**同じ失敗路でない理由（明示）**: 旧 script の失敗 = **1 つの面（spinner/ack marker）の heuristic を配達と読んだ**こと。D1 v2 は (1) 本文先頭に一意 id token を置き (2) 送信前の読み戻しに **無く** 送信後に **`›` 付きで在る** ことを述語にし (3) busy/dialog/入力欄非空なら **送らず HELD** を記録し (4) 否定制御（queued/未送信の pane で NOT delivered が出ること）を bank してから信頼する。旧 script から**残す**もの = 有界待ち・blind 再送禁止・draft 状態の回復。
既存機構（v1 未引用）: `scripts/verification_log_append.py:20-22`（O_APPEND+flock+fsync の追記 core・再利用）／`ITEM4_RS_RULING_CUSTODY_RAW_RECORDS_20260808.md/.jsonl`（当卓が 08-08 に作った裁定 custody 面・transcript の `origin.kind=human` を機械抽出 = A2 の既存形）／manifest §3 `last_heartbeat`（C3 の既存形）／`.claude/skills/log-analyzer`（pB の既存 skill・RUN_METRICS 一次）／`ur15_steps_wired.py:1504` 等の driver 自身の summary 行（E1 の入力）／`herdr agent list` の `name` = live な役名地図（A6 の入力・保存した id→役 表は信用しない memory MEMORY.md:12）／memory 07-04 `herdr agent wait`（有界待ちは既知）。

---

## §2 「エージェント型」を本系に当てはめる（perceive → decide → act → feedback → improve）
| 段 | 今できていること | 測れた欠落 |
|---|---|---|
| perceive | 計器（kinonly 表・run.log・live stream・stills）・事前登録 acceptance | 動画を読むのは Rs1 だけ（**CLAUDE.md:274 の視覚レグ必須が守られなかった** = 規則の欠如でなく不遵守）・run.log 要約は手作業 |
| decide | 設計 court（p11/p5）・Rs2 代理裁定・5 体検証（p11 草案を FAIL に・本 v1 を FAIL に） | prior-art guard の未実行が panel まで漏れた（v1 自身も同じ・§1.6 で是正）|
| act | announce-first・parent-relative leg・content-sha 等号受入（chain 3 本が同型で閉じた） | relay の ingestion lag（§1366）・当卓の bank-without-send（§1296）|
| feedback | run が自ら止まる gate・live stream 保全・計器の事前予測（L 0/240） | 予測を run 認可要求に添える規則が無い（p5 が手で添えた）— ただし **`/pre-check`（CLAUDE.md:269）と [HIGH-COST-GATE] が既に同旨** |
| improve | 誤りが数分で自己訂正され台帳に法として残る | **法が散文のまま機械化されず同じ class が卓を跨いで再発**（部分読み 4・記憶の数/時刻 3+・stale pin・regex）|

---

## §3 改善点 v2（各項 = 証拠 → 提案 → court → **状態**: BUILD-after-word ／ PROPOSAL ／ DECISION(Rs1) ／ 執行(他卓) ／ DROPPED ／ HOLD）

### A. 役割分担
- **A1 hub の 2 機能を分ける（relay = script・custody = p18）** — 状態 **BUILD-after-word**（§5 #1）。中身 = D1 core（下）。p18 の自卓 tooling として。**他卓の採用は各卓の court**（採用しても routing 規則は不変: desk mode は宛先 `w2:p18` 固定）。
- **A2 Rs1 の言葉の受け口** — 状態 **PROPOSAL**（p6・各卓）。既存形 = `ITEM4_RS_RULING_CUSTODY_RAW_RECORDS_20260808`（transcript record の機械抽出・`origin.kind=human`）。提案 = その形を「受けた pane が受領時に同形で bank し、p6 register 行がそこを指す」へ一般化。**雛形 file は作らない**（採用後に各卓が同形で書く）。
- **A3 設計 court の standing 化** — 状態 **DROPPED**（前提不成立・§0）。記録として残す観測 = 「court word の発行待ち時間」（§1401→§1403 の 21 分）。変えるなら CLAUDE.md の Routing Protocol（L3・Rs1）。
- **A4 分析 2 卓を DoD chain の既定段に** — 状態 **PROPOSAL（compliance）**（p4）。**新規則でなく既存規則の適用**: CLAUDE.md:274「motion-bearing sim RESULT は視覚レグ必須（mandatory-or-justified）」・:275「動画 → ログ → 照合」。08-10 の 2 run は省略理由の記録なく Rs1 の目だけで判定された ⇒ 「省略時は loud に理由を記録」の遵守を p4 の chain 定義に明記。pB は `/log-analyzer` で run.log/RUN_METRICS を読む（E1）。
- **A5 退役役名 pane pV/pW** — 状態 **DECISION(Rs1)**（§5 #3・close は不可逆）。
- **A6 cc 既定一覧** — 状態 **BUILD-after-word（D1 の一部）**。形 = **話題別の一覧**（arm-control chain／SKILL／NEST／evidence）を **役名**で持ち、送信時に `herdr agent list` の live な `name` へ解決（保存した pane id を使わない）・`w2:` 完全修飾・**SKILL 一覧には p16/p17 必須**（CLAUDE.md:348）・一覧名を指定しない送信は拒否。

### B. エージェントの数
証拠: chain の閉止 7.3–42.5 分・pZ の独立脚 5 本を逐次で処理・p15 の並列検証が要った事例 0。**ただし人数を変えた対照実験は無い ⇒ 「人数が律速でない」は NOT_EVALUATED**。測れた支配項 = **人間の一語の待ち**（25 日の空白は Rs1 の条件付き認可 ②「今は発火しない」§1400 と物理 stall §1383/§1395 に gate されている）。結論: **増減の根拠なし → 現行維持**（稼働 7＋分析 2 を稼働に戻す = 9／WMSO 5 dormant／退役 2 は Rs1）。A4 により稼働数は 7→9 になる（Rs1 が問うた「数」への答え）。

### C. NEST Tree
- **C1 活動 chain と node の結合** — 状態 **DECISION(Rs1)**（§5 #2）。**v1 の「7 session を bind」は NEST §5.1 違反**（LTM-1:407 同一 node の並行 session 禁止）。v2 = C3C5 node を起動（§3.1 #4 = Rs1 承認）し **1 session（chain lead = p4）を bind**・他卓は §3.2 の子 node（各卓 1:1）か provenance 記録。これが **D2 WARN の正しい解**。
- **C2 manifest** — 状態 **執行(p6)**・Rs1 の一語は不要（root 裁定は 08-08 に済）。p6: frontmatter `root_node_id` を item-9 (i) に合わせ・:4 の「234 vs 252」注記を削除。
- **C3 心拍** — 状態 **DROPPED**（D2 は正しかった・C1 が解）。代わりに **DECISION**（§5 #6）: manifest §3 `last_heartbeat`（04-28 以来停止）を **復活させるか退役させるか**（p6 court・Rs1）。
- **C4/C5 依存語彙・chain 属性** — 状態 **HOLD**。読む consumer が無い（validator 0・`build_nest_snapshot.py` は未知 key を無視・regex fallback 76/254 node は list-of-dict を落とす・全桁数字の sha は YAML で int 化）⇒ comment 形で足りる。将来採用するなら flat な quoted 文字列＋両 parser の往復 test＋consumer 同梱（L3・§9）。

### D. 通信基盤 — **D1 core（唯一の build 候補・BUILD-after-word）**
仕様（cycle 1 の受入をすべて織り込み）:
1. **id** = O_EXCL で採番した `m-p18-N`（memory :52-58 の allocator）＋ `body_sha256`（date 印を付けた後に計算）。本文 **先頭行** = `MSG m-p18-N / w2:p18 / OPS-SUPERVISOR`（自己識別 head token）。
2. **mode** = hub（p18 のみ fan-out 可）／desk（宛先 `w2:p18` 固定・他宛先は `--rs-directive <id>` 無しに拒否）。宛先は **話題別一覧名**で指定（A6）・live `agent list` の name へ解決・`w2:` 完全修飾。
3. **送信前**: 宛先を read（`agent read --source recent-unwrapped`）。`agent_status==working`／入力欄非空／dialog 表示 → **HELD** を記録して送らない（Rs 06-20 hold 指示）。送信前 snapshot に head token が **無い**ことを確認。
4. **送信**: `agent send` → `pane send-keys Enter` → 再 read → head token が **`›` 付き**（transcript）= DELIVERED／「queued / Press up to edit queued messages」= QUEUED／`»` のまま → `send-keys Tab` → 再 read → QUEUED or UNKNOWN。⛔ Escape 不使用・blind 再送禁止。`delivered_at` は **`›` 述語でのみ**刻む。⚠ 判別子は agent 種で異なり得る（Claude pane の `›` = draft の可能性・`dispatch_to_pane.sh:31`）⇒ **コード化前に両種で prefix 表を実測して header doc に置く**。
5. **fan-out**: 全宛先へ送信して `pending` 行を書き、検証は **background job** が行を書く（foreground 2 分の制限）。
6. **記録**: 送信者ごとの JSONL（単一 writer・file 名に `.log` を含めない〔`.gitignore:5` `**/*.log*`〕）・`verification_log_append.py` の O_APPEND+flock core を再利用・`evidence` は「一致行の prefix＋head token」に限定。field = `{id, body_sha256, mode, list, to, sent_at, state, delivered_at, evidence, supersedes, part, in_reply_to, owner, next_action, accept_cond}`（空許容・存在必須）。**時刻は script が `date` で刻む**。
7. **返し脚**: 受領/disposition/ACK は p18 の行為（row type `disposition`）— 「file を tail すれば cc 確実」とは**言わない**（idle な pane は何も読まない）。JSONL は custody・重複判定・起床時の照合用。
8. **lint** = WARN のみ。述語 = §1319（hex token は関数語 `sha256|blob|commit|content|@|cNN|着地|custody|tip|HEAD` のいずれかを同行に持つ）・id field は除外・`--stop` で bypass し行に `lint: bypassed(STOP)` を刻む（§運用27 の STOP 例外）。数値の `:行番号` 警告（v1 F3）は **採用しない**（全行で鳴る）。
9. **受入前の否定制御**: queued/未送信状態の pane で NOT delivered が出ること、既に working の pane で HELD になることを bank してから A1 が依存する。
10. **code の commit**: 07-26 裁定は code を除外（`P4_RS_RULING_20260726_RECORDS_COMMIT_GATE.md:46`）⇒ 新 code は detached worktree で file 限定の pre-commit を通す（memory `feedback_ruff_format…:37`）・SPDX 2026 header・pathspec commit。
- **D2/D3** は上に内包。**F1/F2/F4** も上に内包。**F5 measured_by** = DROPPED（自己申告 field は判別しない）。

### E. 環境からの feedback
- **E1 run 記録の要約** — 状態 **PROPOSAL**（p0＝producer・pB＝consumer）。p18 が prose を regex で読む要約器は **作らない**（130 か所の ad-hoc print・p0 の編集窓で壊れる・run.log は git-ignored）。提案 = p0 が exit 時に **`[steps] SUMMARY {json}` 1 行**（構成 echo・STEP 別 tool err・COMMAND 到達率・mast/ARM-TO-ARM・gate 文・exit）を出し、入力 run.log の sha256＋byte 数を同行に含める。pB は `/log-analyzer` で消費。
- **E2 認可要求に予測を添える** — 状態 **PROPOSAL（compliance）**。既存 = `/pre-check`（CLAUDE.md:269・train/GPU 消費前の強制 gate）＋ [HIGH-COST-GATE]（:170）。新規則でなく「wired run の認可要求には計器の予測行（witness 等）を同行に置く」を p4/p5 の chain 定義に明記。
- **E3 動画の判読性 pre-gate** — 状態 **PROPOSAL（compliance）** = A4 と同じ規則（CLAUDE.md:274-276）。stills 生成は p0 の court（§1397 で受諾済）。
- **E4 bundle 認可の一般化** — 状態 **DECISION(Rs1)**（§5 #5）。

### F/G. 自己改善の機械化・知識
- **F1/F2/F4** = D1 内。**F3** = 行動則のみ（「数は file 自身の summary 行から引く」を当卓 handoff と brief に置く・lint 化しない）。**F5** = DROPPED。
- **G1 台帳索引** — 状態 **DROPPED as artifact**。索引は `grep -n '^## §' <ledger>` で常に新鮮（生成 file は 30 分で古びる・台帳 :15「commit sha は照合 note であって pin でない」）。
- **G2 MEMORY.md** 22,015 chars = 88.1 %（trigger 22,487 未達）→ 行動なし。**G3** 当卓 handoff = 本 task の終わりに更新。

---

## §4 実行計画 v2（当卓・本 session）
1. ✅ [L-TRIAGE] L3・[VERIFY] cycle 1 = FAIL（記録 `dc10ba462d`）→ 本 v2。
2. [VERIFY] **cycle 2**（本 v2 を PROPOSE に・5 体・同 bundle 形式）→ PASS なら 3 へ。FAIL なら Rs1 へ両方（v2＋残課題）を提示して停止（cycle は最大 2）。
3. **Rs1 へ提示（§5）** — 本 file の path＋sha＋3 行で。⛔ **Rs1 の一語まで tooling file を作らない・他卓へ配付しない**（未検証の数を流さない・CLAUDE.md:46）。
4. Rs1 の一語の後（別 turn）: [DEFER-RECON]（§6）→ [RULE-CHECK] stage2 → D1 core の build（pre-mortem 1 頁・prefix 表の実測・否定制御 → 層2 事後 debate・層5）。
5. 当卓 handoff 更新（G3）。

## §5 Rs1 (the human) の決定が要る項（当卓は実行しない）
| # | 項 | 選択肢 | 当卓推奨 |
|---|---|---|---|
| 1 | **tooling file の作成可否**: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p18_desk_tools_20260905/` に D1 core（script 1・header doc 1・送信者別 JSONL 1・話題別一覧 1） | A) 作ってよい ／ B) 作らない（手作業継続） | A（唯一、既存機構が無い項） |
| 2 | **C3C5 node の起動＋session binding**（NEST §3.1 #4）| A) 起動し **p4 の 1 session を bind**（他卓は子 node/provenance）／ B) 現行どおり kickoff 運用 | A（D2 WARN の正しい解） |
| 3 | 退役役名 pane pV/pW | A) 閉じる ／ B) 役を再付与 ／ C) 放置 | A |
| 4 | NEST §9 改訂（C4/C5 の read-optional field） | A) 保留（consumer が出来るまで comment 形）／ B) 別 task（L3）で着地 | A |
| 5 | 静的計器の bundle 認可の一般化（E4） | A) 既定化 ／ B) 都度 | Rs1 の方針 |
| 6 | manifest §3 active-session heartbeat（04-28 以来停止） | A) 退役（D2 を心拍とする）／ B) 復活（binding session が更新） | A |
| 7 | l-gate 混合則による **task 分割**: (a) 卓 tooling = L2 ／ (b) NEST §9 = L3 | A) 分割承認 ／ B) 1 task のまま L3 一律 | A |
| 8 | 卓単位の改善 task（本件のような role-bound の仕事）に NEST node を持たせるか | A) 持たせる（Rs1 が起動承認）／ B) role-bound のまま（DDR #34 どおり） | B（現行裁定と整合） |

## §6 [DEFER-RECON] 照合記録（DDR = `00-DESIGN-STATUS-LEDGER.md` §DDR）
| 前提 | DDR 項 | 依存判定 |
|---|---|---|
| 本 task は role-bound（node 化しない） | **#34**（:138）role label ≠ node・node 化するな（pN 裁定 07-20） | 整合。§5 #8 は #34 を変えるか否かの Rs1 判断 |
| 全 commit `--no-verify`＋pathspec | **#35**（:139）validate.sh の guard 述語が世界と合わない | 整合（必要性）。ただし **code には 07-26 裁定の除外**が効く ⇒ D1 §10 のとおり worktree で file 限定 check |
| C1 の node 起動 | C3C5 state.md :86-97 が引く **#66**（§0 疑義 → Rs1 裁定 → fix → 閉鎖・dep-1 CLOSED 08-10 01:18・`:170`）／**#68**（Rs1 premise 裁定 08-10: 右腕 = UR15-B・⛔04-Specs 未反映・`:172`）／**#69**（条件つき run 認可 08-10 09:51・⛔未発火・`:173`） | #66 は閉鎖済（非依存）。#68/#69 は node の **DoD と run** を gate する項であって起動を gate しない ⇒ 本 task は起動を**依頼**するのみ（解消は Rs1・04-Specs は CC read-only） |
| A6 の SKILL 一覧 | DDR #31（trainer/実行 driver・p16/p17 が決定） | 非依存（一覧に p16/p17 を含める理由） |

## §7 検証記録
- cycle 1（v1 @ `acb4ff2c2a`）: 5 体（premise/provenance 18・rule/SSOT 17・numerical 22・side-effects/history 19・NHA HOLD）→ union 40 項目・CRITICAL/HIGH 全受入 → **FAIL** → 本 v2。全文 = `P18_AGENTIC_VERIFY_CYCLE1_20260905.md` @ `dc10ba462d`。verification-log 登録済（2026-09-05 01:12 JST・`harness-vault/verification-log/verification-log.jsonl`・parser の overall 欄 = REVIEW・CC1 verdict = FAIL→revise）。
- cycle 2（本 v2）: 実施後に追記。
