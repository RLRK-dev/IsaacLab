# エージェント型 AI 化の改善提案 v3 — herdr 上の CC pane 群を「自ら考え・行動し・環境から feedback を得て改善する系」にする

**版** v3（v2 = commit `ce50abc3d9` を supersede。v1 = `acb4ff2c2a`）。5 体検証: cycle 1 = **FAIL**（記録 `P18_AGENTIC_VERIFY_CYCLE1_20260905.md` @ `dc10ba462d`・訂正注記 @ `16a8bdc1d0`）／cycle 2 = **REVIEW**（記録 `P18_AGENTIC_VERIFY_CYCLE2_20260905.md` @ `e4842380b3`・cycle 上限 2 に達し、受入した HIGH は全て本 v3 の文書訂正で反映。規則上は Rs1 へ escalate）。**何も build していない**。
**作成** p18（T-ROOT-OPS-SUPERVISOR = role label）— 2026-09-05 07:2x JST（date 実測は各節）。⚠ **本 task の NEST node は未起票**（`CLAUDE.md:126-128`「全 task は node」と不整合。DDR #34 は role label について「node 化するな」と裁定したのみで task には沈黙 ⇒ §5 #4 で Rs1 に問う）。
**契機（custody）** Rs1 (the human) の直接発話・当卓 pane・transcript `~/.claude/projects/-home-rlrk-IsaacLab/1c3d805c-2a9a-4b6d-bba2-ae7d479862e7.jsonl` **行 37937**（`type=user`・`userType=external`・`origin.kind=human`・`promptSource=typed`・2026-09-04T07:08:50.946Z = **16:08:50 JST**・原文は端末折返しで 6 行＋先頭 U+00A0。以下は空白正規化）:「エージェント型AI（Agentic AI）とは、単に指示に応答するだけでなく、自ら考え、行動し、環境からフィードバックを得て改善を行うシステムのことを指すが、IssacLabにおいても 高度なエージェント型AIを構築して目標を実現したい。現在のherdr上の各paneにおけるエージェントの集まりを用いてエージェント型AIとしたい。エージェントの役割分担、エージェントの数　、NEST Tree等　改善点をあげて、次にそれらの点で改善を実行して。」（⚠ v2 は行 38094 = compaction summary（CC が書いた要約）を出典にしていた。cycle 2 で 5 体全員が捕捉）
**読み** 「改善点をあげて、次に…実行して」= 一覧が先・実行が後。一覧 = 本 file。実行のうち (i) **新規 file を作る項は CLAUDE.md:46 により Rs1 の一語の後**（§5 #1）(ii) **file を作らず権限も動かさない項は本 session で実行**（§4-3: p6/p4/p0 への message 3 通・当卓 handoff への行動則）。v2 が (ii) まで Rs1 待ちにしていたのは「未検証の数を流さない」ための当卓の判断であって規則ではない（cycle 2 で分離）。
**L-triage** L3（`operational-rule-LTM-1.md` §9 に触れる項を含む）。`~/.claude/l-gate.md:33` の既定は「複数 L 該当なら最高 L で一律」（分割条項は L1↔L3 のみ）⇒ 本 task は L3 一律。D1 の build は別 turn の別 [TASK] としてそこで再 triage（新規 file = L2）。
**動かさないもの** ⛔ §0 不変前提（DUAL-ARM / 88 mm span / IK のみ・kinematic trick 禁止 / gripper 幾何 LOCK）・run 認可（Rs1 のみ）・動画の物理妥当性判定（Rs1 の目）・04-Specs/07-Design の read-only・役名 = Rs1 割当・pane 間 routing 規則（送信元は p18 へ提出し宛先へ直送しない）。
**語** 本 file で定義して使う語: **hub mode** = p18 だけが複数宛先へ送る運用／**head token** = 本文 1 行目の自己識別（`MSG m-p18-N / 送信 pane / 役名`）／**話題別一覧** = 宛先を役名で持つ一覧（arm-control chain／SKILL／NEST／evidence）／**返し脚** = 受領・disposition を送信元へ返す p18 の行為。台帳で既に使われている語（初出ではない）: announce-first = 実装前に着地先を message で告げる運用／parent-relative leg = 対象 commit をその親との差分で検査する脚／content-sha 等号受入 = 4 者の content sha256 一致で受入とする形。

---

## §0 v2 → v3 の変更（cycle 2 の捕捉・すべて disk で再確認済）
| v2 の記述 | 実際（出典） | v3 |
|---|---|---|
| custody = transcript 行 38094（07:24:04Z） | 38094 は compaction summary。人間の発話 = 行 37937（07:08:50.946Z）| 上記 header |
| D1 の配達判別子 = 行頭 `›`/`»` | codex pane での 1 回計測（memory 07-26）。w2 の 16 pane は全部 Claude で、送信済行も composer も `❯`（`›`/`»` は出ない）。⇒ **09-05 07:19 に Claude pane で実測**（§1.4）| D1 point 4 を計測値で書き直し |
| C1 = p4 の 1 session を bind | p4 は既に `T-ROOT-Kinematic-Pin-Complete-Removal-20260719#s1 active`（state.md:13/:23-24）⇒ 1:1（CLAUDE.md:136）に反する | C1 = **新規 session** を bind（§5 #2）|
| 「1 つの範囲」= §1344–§1406 | §1344 の bank commit `3d6d35225d` 17:25:23 は commit 窓（17:30〜）の外 | §1345–§1406（62 節）に揃え再計数 |
| shakedown 10 本（§1379） | §1379 に shakedown の語なし。番号つき shakedown の記録は 1 と 3（§1356/§1359）・`shakedown10.log` は §1368 の file 名 | file 名として引用・run 数は未再計数 |
| 「§1401→§1403 の 21 分」 | 両節の時刻差は 6 分・court word の到着は台帳の窓内に未記録 | 数を削除 |
| C2 = p6 の機械更新・Rs1 不要 | item-9 :65 が p6 に許した伝播先は T-ROOT state.md goal／manifest §1／地図で frontmatter は無い。manifest:47「root_node_id 対 §2 parent 列は不変・Rs 項 9」。THREAD-scope の manifest では `T-ROOT` が正しい可能性 | C2 = p6 への **問い**（field の意味）|
| HELD = working なら全部保留・解除規則なし・STOP も保留 | Rs 06-20 の hold 指示は「別件に専念中の pane」限定。hub が working の間、全卓の送信が止まる | D1 point 3 を書き直し |
| record に本文なし | 「本文が disk に残らない」を埋めるのは D1 なのに schema に body が無い | `body_path` ＋ bodies dir |
| `verification_log_append.py` の core を再利用 | `append_record` は module global `LOG_PATH` に固定（:41/:247）・import 前例は test のみ | ~30 行を出典つきで複写 |
| 「role-bound で NEST 外を走る〔DDR #34〕」 | #34 は role label の裁定。CLAUDE.md:128 は全 task が node | 「node 未起票・不整合を §5 #4 で問う」|
| record commit 2／manifest 5 commit／LTM-1:407／台帳 :15／§1401:27／CLAUDE.md:348 で p16／130 か所 print／鏡像 33.5–42.5 分 | 4（09-05 01:32 時点）／4／:408／:14／§1402（行 46800）／p16 は DDR #31＋memory／148 行／32.6–42.6 分 | 各所訂正 |
| A2 = ITEM4 形（`origin.kind=human` が最強の attestation） | **herdr で送った message も `origin.kind=human`・`promptSource=typed` を持つ**（09-05 07:19 実測・§1.4）⇒ transcript の field は人間を判別しない | A2 の述語を内容・文脈へ |

---

## §1 現状の実測（2026-09-05・command 併記）

### 1.1 pane topology（`herdr agent list` → 20 entries・workspace **w2 = 16**・全部 `"agent":"claude"`）
| 区分 | pane（w2:）| 前窓（08-09 17:30 → 08-10 10:07）の稼働 |
|---|---|---|
| hub | p18 OPS-SUPERVISOR | 稼働（当卓） |
| 核 6 | p4 RS-TECH-LEAD（= Rs2 代理）／p0 IMPL-BUILDER／pZ IMPL-VERIFIER／p5 SKILL-DETAIL-DESIGN／p6 PLAN-KEEPER／p11 ARM-CONTROL-DESIGN | 稼働 |
| 分析 2 | pB LOG-ANALYST／pC VIDEO-ANALYST | 不使用（DoD 動画は Rs1 が直接判定・run.log の行引用は p0 手作業 §1383/§1395） |
| WMSO 5 | p12 RS-TECH-LEAD2／p14 IMPL-BUILDER2／p15 IMPL-VERIFIER2／p16 WMSO-DESIGN／p17 SKILL-DESIGN | dormant（設計どおり。⚠ SKILL の決定卓 = p17〔CLAUDE.md:348〕＋ p16〔DDR #31・memory 08-2x Rs 確定〕。p12 の SKILL 一覧への所属は DDR #33 で未裁定 ⇒ 一覧は広い側に倒す） |
| 退役役名 2 | pV T-ROOT-COORD／pW T-ROOT-COORD2 | pane 生存・役は 07-20 ARCHIVED |
| pane 無し | p9 PAPER-AUTHOR（役名登録のみ）・OPS-SUPERVISOR-CODEX・VT-DESIGN（退役名） | — |
役名登録 `scripts/validations/nest_role_labels.txt` = 43 行・19 役名。live 16 ⊂ 登録 19・pane 無し 3。⚠ 短 id は workspace を跨いで衝突（w1:pV と w2:pV）⇒ 宛先は常に `w2:pN`。
commit: **0**（08-10 10:07 → 09-04 16:14:37）。以後 = 当卓の record commit のみ（`git log --since='2026-08-10 10:07' --format=%h`・本 commit 直前で 6: 043e10901b acb4ff2c2a dc10ba462d ce50abc3d9 16a8bdc1d0 e4842380b3）。

### 1.2 前窓の稼働（commit 窓 = 08-09 17:30 → 08-10 10:07〔最初 `93adb43eb7` 17:32:06・最後 `cf0a14cea3` 10:06:53 = 16.6 h〕／台帳 = **§1345–§1406**〔`P18_CLAMP_COURT_EVIDENCE_LEDGER_20260727.md:46181-46838`・§1345 の初出時刻 17:31:22・§1344 は bank 17:25:23 で窓外ゆえ除外〕）
| 量 | 値 | query（逐語） |
|---|---|---|
| commit | 134 | `git rev-list --count --since='2026-08-09 17:30' --until='2026-08-10 10:07' HEAD` → 7.4 min/commit |
| 台帳の節 | 62 | `grep -c '^## §'` |
| hub の dispatch id | 28 | `grep -oE 'm-p18-[0-9]+' \| sort -u \| wc -l` → 35.5 min に 1 通 |
| 見出しに Rs1 を含む節 | 28 | `grep '^## §' \| grep -c 'Rs1'`（人間の一言を見出しに持つ節の代理量） |
| 見出しに 訂正\|撤回 を含む節 | 17（27.4 %） | `grep '^## §' \| grep -cE '訂正\|撤回'` |
| custodian bank | 10 commit | 窓内の commit のうち `git log --name-only` に `PZ_*` を含むもの（author は単一ゆえ file 名で識別） |
| stale\|交差\|追い越 の行 | 17 | `grep -cE 'stale\|交差\|追い越'` |
| 部分読み\|分母 の行 | 11 | `grep -cE '部分読み\|分母'` |
| 折返し\|regex\|delimiter の行 | 5 | `grep -cE '折返し\|折り返し\|regex\|delimiter'` |
| correlated assent の行 | 5 | `grep -cE 'correlated assent\|相関した同意'` |
| NO-HIT の行 | 3 | `grep -c 'NO-HIT'` |
| 記憶の時刻\|記憶から の行 | 3 | `grep -cE '記憶の時刻\|記憶から'` |
| 配達 N/N の行 | 5 | `grep -cE '配達 [0-9]+/[0-9]+'`（「毎 dispatch 1–3 回 probe」は台帳に記録が無い） |
| pZ の leg 節 | 13 | `grep '^## §' \| grep 'pZ' \| grep -c 'leg'`（独立検証脚は 5 本: §1369/§1372/§1378/§1391/§1406） |
chain の所要（開始事象 → 終了事象・台帳節）: dep-1 unlock→受入 **16.7 分**（`m-p4-246` 01:01:40 → `m-p4-247` 01:18:21・§1373/§1379）／fork 決着 **7.3 分**（`m-p0-259R` 23:02:24 → `m-p4-245` 23:09:42・§1365/§1366）／鏡像 Rs1 所見→受入 **32.6–42.6 分**（08:4x → `26f3e3c2e9` 09:22:33・§1393）／(c) 解散 7 分（§1349 見出しのまま・事象未測）。kinonly bundle 認可 1 回で shakedown が反復（番号つき記録 1・3 = §1356/§1359・pZ へ渡した log 名 `shakedown10.log` = §1368・run 数は未再計数）。DoD run 2 本 = **2 本とも STEP 2 で stall**（§1383/§1395・2 本目は計器が事前予測: witness L 0/240）。
⚠ 本表は「起きた事の数」であって重大度ではない。人数 vs 調整の判定は本表からは出ない（§3-B）。

### 1.3 NEST
- state.md = 254（`find thread_isaac_lab/thread-vault -name state.md | wc -l`・253 live + 1 `_archive/discarded/`）／manifest §2 GEN 行 = 253（`582dbb74ea`）／snapshot json = 256。母集団が違う数を並べない。
- 活動 chain の node `T-ROOT-C3C5-Port-To-Current-Substrate-20260809`: `status: PENDING`・`session_history: []`・`last_updated: 2026-08-10T01:29:56`（state.md:15/:29/:32）。実作業は kickoff（p4・2,235 行）＋当卓台帳＋p6 register で回った ⇒ preflight D2 WARN（25 日）は「作業が node 化されていない」を正しく検出（`check_nest_freshness.sh:8-9`）。⚠ **p4 の session は既に `T-ROOT-Kinematic-Pin-Complete-Removal-20260719#s1 active`**（同 state.md:13/:23-24）⇒ C3C5 に bind するなら**新規 session**（LTM-1:157 の手順どおり `{node_id}#s1` を起動）か、p4 が現 node を §4 で handoff してから。
- manifest §3「Active session list」の `last_heartbeat` は既存の heartbeat 機構（LTM-1:529・Tier 2・§5.3 #2 が preflight で参照）で、2026-04-28 の 2 行を最後に停止（manifest:317-322）。**復活 = 既存 template どおり binding session が行を書く（裁定不要）／退役 = LTM-1 §5.3/§7.2 の改訂（L3）**。
- 依存語彙: precedent/blocker の 2 語（v1.1 で 4→2 に YAGNI 縮小・LTM-1:89）。grade cap／constraint は comment（C3C5 state.md:19-25）。それを読む validator は無い（`build_nest_snapshot.py` は precedent/blocker のみ平坦化・regex fallback 76/254 node は list-of-dict を落とす・全桁数字の sha は YAML で int 化）。

### 1.4 通信基盤 — **Claude pane での配達の見え方（2026-09-05 07:19:40 JST・計測 message `m-p18-283` → idle の w2:pB・snapshot は cycle-2 記録 Part 4）**
- 送信 = `herdr agent send w2:pB "$(cat body)"` → `herdr pane send-keys w2:pB Enter`（07:19:40.576）。
- **直後の viewport（67 行）: token 無し**（render 前・composer = 最後の `❯` 行・空）。
- **`wait agent-status w2:pB --status working` = 07:19:40.862（Enter の 286 ms 後）**: idle→working の遷移を観測。
- **遷移後の viewport: token は composer より上の `❯ ` 行**（`❯ MSG m-p18-283 / w2:p18 …`）。composer は最後の `❯` 行で空。spinner 行あり。
- **宛先の transcript jsonl（`herdr agent list` の `agent_session.value` = session id → `~/.claude/projects/-home-rlrk-IsaacLab/<id>.jsonl`）に `type=user` record が token 付きで追加**（07:19:40.599 JST・`origin.kind=human`・`promptSource=typed`）。⇒ **配達述語は transcript record で決定的・viewport の窓（67 行・作業中は数秒で流れる）に依らない**。
- ⚠ 帰結 1: **herdr 経由の message は人間の入力と同じ field**（`origin.kind=human`・`promptSource=typed`）を持つ ⇒ 人間の裁定の custody は field でなく **内容・文脈**（pane message は head token `MSG m-pN-…` で始まる・人間の一言は始まらない）で判別する（A2）。
- ⚠ 帰結 2: `›`/`»` の表（memory 07-26・codex pane・1 回）は w2 には適用対象が無い（codex 0）。codex pane の表は未計測のまま（w2 に codex が現れたら計測してから送る）。
- 既知の限界（memory と一致）: busy な相手は Enter が効かず Tab で queue（`feedback-verify-message-delivery…:62-69`）・複数卓が同時に送ると入力欄で融合（`reference-codex-pane-long-dispatch-paste-mode…:55`）・別件に専念中の pane へは送らない（Rs 2026-06-20）・`agent read --source recent` = 可視 viewport（67 行）で scrollback ではない。
- herdr 自身は send の成功記録を持たない（herdr-server.log の `agent.send` 2 行はいずれも error）。dispatch 本文は disk に残っていない（30 session dir で 0）。

### 1.5 当卓の自己捕獲（5 回・証拠として載せる）
①`head -25` で役名 file → 「8 役名未登録」（全文で 19 全登録）②manifest frontmatter の注記だけ読み「食い違い 2 件」（本文 :47 は訂正済）③custody に compaction summary の行を引用（人間の発話は 37937）④「shakedown 10 本（§1379）」= 節に無い数 ⑤「21 分」= 未測の数。**同じ class（部分読み・引用先不在・未測の数）が提案書を書く手の中で 5 回発火** ⇒ 法は散文では効かない（memory `feedback-verify-message-delivery…:58`）。5 体検証は 5 回とも捕らえた（cycle 1: ①②／cycle 2: ③④⑤）。

### 1.6 先行実装・既存機構の棚卸し（§運用4・CLAUDE.md:182）＋ prior-art guard
- `scripts/check_thread_vault_prior_art.sh --fail-on-blocker herdr dispatch delivery readback` → rc=2・findings=30 blockers=30（09-05 01:01）。30 件の実体は役割 standing 行の一致が大半・設計上重要 = `eval_runs/phase5_v7_a6_behavioral_2026-05-13/docs/post_v7_disposition_scenarios.md:123`（Known dispatch race: ack=NO でも配達成功あり）の 1 件（2 hit）。**`scripts/dispatch_to_pane.sh`（tmux 時代の送信＋ack 検出 script・07-04 に退役）は guard でなく cycle-1 panel（U3）が挙げた prior art**（header :7-11「ack=UNKNOWN on some Claude states — ALWAYS verify delivery by capture-pane; no blind re-send」・:31「Draft state (› prefix on payload)」）。
- **同じ失敗路でない理由**: 旧 script は 1 つの面（spinner/ack marker）の heuristic を配達と読んだ。D1 v3 は (1) head token を本文先頭に置き (2) **宛先の transcript record**（面でなく記録）を主述語にし (3) 状態遷移と viewport 行位置を従述語にし (4) busy/dialog/composer 非空なら送らず HELD にし (5) 否定制御（composer に置いただけ／queued／working）で NOT delivered が出ることを bank してから信頼する。旧 script から残すもの = 有界待ち・blind 再送禁止・draft 状態の回復。
- 既存機構: `scripts/verification_log_append.py:235-263`（O_APPEND+flock+fsync の追記 core — `append_record` は module global に固定ゆえ **複写**して出典を書く）／`ITEM4_RS_RULING_CUSTODY_RAW_RECORDS_20260808.md/.jsonl`（当卓 08-08 の裁定 custody 面。⚠ その「`origin.kind=human` = 最強の attestation」は本日の計測で降格）／**RUN_METRICS.json の既存契約**（CLAUDE.md Key Files・`.claude/skills/log-analyzer/SKILL.md:14`「存在すれば一次情報」。driver `ur15_steps_wired.py` は書かない: `json.dump|RUN_METRICS` 0・`_gen/*/RUN_METRICS.json` 0・prose の summary 行のみ :1504・`[steps]` print 148 行）／manifest §3 heartbeat（§1.3）／`herdr agent list` の `name` = live な役名地図（保存した id→役 表を信用しない・MEMORY.md:12）／memory 07-04（`herdr agent wait` は既知）・07-26（`›`/`»` は codex 1 回）。

---

## §2 「エージェント型」を本系に当てはめる（perceive → decide → act → feedback → improve）
| 段 | 今できていること | 測れた欠落 |
|---|---|---|
| perceive | 計器（kinonly 表・run.log・live stream・stills）・事前登録 acceptance | 動画を読むのは Rs1 だけ（CLAUDE.md:274 の視覚レグ必須が守られなかった = 規則の欠如でなく不遵守）・run.log 要約は手作業（RUN_METRICS.json 契約が未履行） |
| decide | 設計 court（p11/p5）・Rs2 代理裁定・5 体検証（p11 草案／本 v1／本 v2 を捕らえた） | prior-art guard の未実行（v1 自身も同じ・§1.6 で是正） |
| act | announce-first・parent-relative leg・content-sha 等号受入（chain 3 本が同型で閉じた） | relay の ingestion lag（§1366）・当卓の bank-without-send（§1296） |
| feedback | run が自ら止まる gate・live stream 保全・計器の事前予測（L 0/240） | 予測は手で添えられ、run は予告どおり stall した（§1395）= 規則でなく判断の問題 |
| improve | 誤りが数分で自己訂正され台帳に法として残る | 法が散文のまま機械化されず同じ class が再発（§1.5 の 5 回） |

---

## §3 改善点 v3（状態: **BUILD-after-word** ／ **執行済（本 session）** ／ **PROPOSAL** ／ **DECISION(Rs1)** ／ **報告のみ** ／ **DROPPED**）

### A. 役割分担
- **A1 hub の 2 機能を分ける（relay = script・custody = p18）** — **BUILD-after-word**（§5 #1）。中身 = D1（下）。p18 の自卓 tooling（**hub mode のみ**・`$HERDR_PANE_ID == w2:p18` に束縛）。他卓の採用は後日・各卓の court（採用しても routing 規則は不変・desk 側は SUBMITTED の行だけを書き、配達の readback は p18 が閉じる〔MEMORY.md 提出形式〕）。
- **A2 Rs1 の言葉の受け口** — **報告のみ（行動則）**。custody の述語 = `type=user` ∧ `isCompactSummary≠true` ∧ content が文字列 ∧ **内容が pane message でない**（head token で始まらない）。field（`origin.kind=human`）は判別しない（§1.4 帰結 1）。受けた pane が受領時に同形で bank し p6 の register 行がそこを指す。file は作らない。
- **A3 設計 court の standing 化** — **DROPPED**（前提不成立: §1402 は controller 側が p11 の court word を待った記録・p11 は発行側・待ち時間は台帳の窓内で未記録）。
- **A4 分析 2 卓を DoD chain の既定段に** — **執行済（本 session・p4 へ遵守所見 1 通）**。新規則でなく既存規則の適用: CLAUDE.md:274「motion-bearing sim RESULT は視覚レグ必須（mandatory-or-justified）」・:275「動画 → ログ → 照合」。08-10 の 2 run は省略理由の記録なく Rs1 の目だけで判定された ⇒ 省略時は loud に理由を記録。pB は `/log-analyzer`（RUN_METRICS.json 一次）で読む（E1）。
- **A5 退役役名 pane pV/pW** — **DECISION(Rs1)**（§5 #3・close は不可逆）。
- **A6 cc 既定一覧** — D1 の一部（**BUILD-after-word**）。役名の**話題別一覧**（arm-control chain／SKILL〔p17＋p16、p12 は広い側に含める〕／NEST／evidence）を live `herdr agent list` の `name` へ解決: `w2:pN ` と任意の `T-ROOT-` を剥いだ**完全一致**・役名ごとに live 1 件のみ（0 件・2 件以上なら fan-out 全体を `refused(unresolved)` で中止）・一覧の役名集合 ⊂ `nest_role_labels.txt`・一覧名の無い送信は拒否。

### B. エージェントの数
chain の閉止 7.3–42.6 分・pZ の独立脚 5 本を逐次処理・p15 の並列検証が要った事例 0。**人数を変えた対照実験は無く「人数が律速でない」は NOT_EVALUATED**。測れた支配項 = 人間の一語の待ち（25 日の空白は Rs1 の条件付き認可「今は発火しない」§1400 と物理 stall §1383/§1395 に gate）。結論: **増減の根拠なし → 現行維持**（核 7＋分析 2 を稼働に戻す = 9／WMSO 5 dormant／退役 2 は Rs1）。A4 により稼働数は 7→9。

### C. NEST Tree
- **C1 活動 chain と node の結合** — **DECISION(Rs1)**（§5 #2）。C3C5 node を起動（§3.1 #4）し **新規 session 1 つ**（`{node_id}#s1`・LTM-1:157）を bind。p4 の現 session は別 node に bind 済（§1.3）ゆえ p4 を bind するなら先に §4 handoff。他卓は provenance 記録（子 node にすると各 node に §3.1 #4 の承認が要る — Rs1 が望む場合のみ）。効果 = 作業が node 化される（D2 WARN は 14 日静かなら再発するので「解」ではなく「node 化」）。
- **C2 manifest frontmatter** — **執行済（本 session・p6 へ問い 1 通）**。root の裁定は 08-08 item-9 (i) で済（tree root = T-PRODUCTION-LINE・T-ROOT = THREAD subtree の root・CLAUDE.md:131 に反映済）。frontmatter `root_node_id` の**意味**（tree root か THREAD-subtree root か）は未定義で、item-9 :65 の伝播先にも無い ⇒ p6 に問う。:4 の「234 vs 252」注記（08-06 `c45c319f0b` で本文は訂正済）の削除は p6 の court。
- **C3 心拍** — **DROPPED**（D2 は正しかった・C1 が node 化の解）。manifest §3 heartbeat の扱い = **報告のみ**（復活 = 既存 template・退役 = L3）。
- **C4/C5 依存語彙・chain 属性** — **報告のみ（HOLD）**。consumer 0・YAGNI（LTM-1:89）・comment 形で足りる。採用するなら flat な quoted 文字列＋両 parser の往復 test＋consumer 同梱（L3・§9）。

### D. 通信基盤 — **D1（唯一の build 候補・BUILD-after-word）** 仕様 v3
1. **id** = O_EXCL で採番 `m-p18-N`（memory :52-58）＋ `body_sha256`（date 印を付けた後に計算）。本文 1 行目 = head token `MSG m-p18-N / w2:p18 / OPS-SUPERVISOR`。**本文は bodies dir に 1 id 1 file で保存**（`body_path` field）— 「本文が disk に残らない」を埋めるのは本項。
2. **mode** = hub のみ（`$HERDR_PANE_ID == w2:p18` を実測して束縛）。宛先 = 話題別一覧名（A6 の解決規則）。desk mode・bypass flag は無し（採用は各卓の後日判断）。
3. **送信前**: 宛先の `agent_status` と viewport を read。**hub 宛は保留しない**（Tab-queue が既定路）。宛先が `working`／composer 非空／dialog 表示 → **HELD**（Rs 06-20「別件に専念中は送らない」）。`--stop` は HELD を**上書き**して送り Tab で queue（行に `stop: true`）。HELD は background job が `wait agent-status <to> --status idle --timeout T` の後に **1 回だけ再送**（同 id・row type `retry`）・timeout で `HELD_EXPIRED`（次の checkpoint message に列挙）。
4. **送信と配達述語（Claude pane・§1.4 の実測）**: `agent send` → `send-keys Enter` → **宛先の transcript jsonl に head token を含む `type=user` record が現れる = DELIVERED**（主述語・viewport 非依存）／`wait agent-status idle→working` の遷移 = 従述語／viewport で token が composer（最後の `❯` 行）より上の `❯ ` 行に在る = 第 3 述語。Enter 後も composer に token が残る → **`STUCK_IN_COMPOSER`**（宛先が既知 busy かつ本文がその話題なら Tab で QUEUED・そうでなければ操作者へ表示・⛔ Escape 不使用・blind 再送禁止）。`delivered_at` は主述語でのみ刻む。**codex pane** は表が未計測 ⇒ 状態 `UNKNOWN(table-not-banked)`。
5. **fan-out**: foreground で各宛先に送信し**直後に**主述語を読む（transcript は render 遅延の影響を受けない）。`pending`（`verify_by` つき）は QUEUED→消費の遷移待ちにのみ使い、background job が同じ file に flock で追記（「1 file・協調する 2 writer」）。script 起動時に期限切れ `pending` を `UNKNOWN(verifier-lost)` に畳む。
6. **記録**: 送信者ごとの JSONL（file 名に `.log` を含めない〔`.gitignore:5`〕・`verification_log_append.py:235-263` の core を複写）。field = `{id, body_sha256, body_path, mode, list, to, sent_at, state, delivered_at, evidence, stop, supersedes, part, in_reply_to, owner, next_action, accept_cond}`（後 6 つは任意）。時刻は script が `date` で刻む。**commit 周期** = checkpoint ごとに records-only の pathspec commit（shared tree で dirty のままにしない）。
7. **返し脚**: 受領/disposition/ACK は p18 の行為（row type `disposition`）。JSONL は custody・重複判定・起床時の照合用（idle な pane は file を読まない）。
8. **lint** = 後日（実 body が 20 通以上溜まって誤検知率を印字してから）。述語 = §1319（hex token は関数語 `sha256|blob|commit|content|@|cNN|着地|custody|tip|HEAD` を同行に持つ）・WARN のみ・id field 除外。
9. **受入前の否定制御**: (a) composer に置いただけ（Enter 無し）→ NOT delivered (b) queued → QUEUED であって DELIVERED でない (c) working 宛 → HELD (d) HELD→retry→DELIVERED の遷移。bank してから A1 が依存する。
10. **code の commit**: 07-26 裁定は code に沈黙（records の免除から除外しただけ）。AGENTS.md の全 file check 要件と shared tree での `--all-files` 禁止（:47）が衝突 ⇒ §5 #1 の副問（A: detached worktree で file 限定 pre-commit／B: detached worktree で `./isaaclab.sh -f` 全体を走らせ新 file の差分だけ読む）。SPDX 2026 header・pathspec commit。
- **file 数**（§5 #1）: script 1（docstring = 手順＋述語表）＋ bodies dir ＋ JSONL 1（＋任意の話題別一覧 file 1）。

### E. 環境からの feedback
- **E1 run 記録の要約** — **執行済（本 session・p0 へ依頼 1 通）**: 新形式でなく **既存契約 RUN_METRICS.json**（CLAUDE.md Key Files・log-analyzer が一次情報として読む）を driver が exit 時に書く（構成 echo・STEP 別 tool err・COMMAND 到達率・mast/ARM-TO-ARM・gate 文・exit・入力 run.log の sha256＋byte 数）。p18 は prose を parse しない。
- **E2 認可要求に予測を添える** — **執行済（A4 と同じ 1 通に同梱・遵守所見）**: 既存 = `/pre-check`（CLAUDE.md:269）＋[HIGH-COST-GATE]（:170）。証拠は規則に反する（予測は手で添えられ run は予告どおり stall した §1395）⇒ 新規則は作らない。
- **E3 動画の判読性 pre-gate** — A4 と同じ（CLAUDE.md:274-276）。stills は p0 の court（§1397 で受諾済）。
- **E4 bundle 認可の一般化** — **報告のみ**（次の静的計器の反復が要求された時に Rs1 へ問う。今は pending の反復が無い）。

### F/G. 自己改善の機械化・知識
- **F1/F2/F4** = D1 内。**F3** = 行動則のみ（「数は file 自身の summary 行から引く」— 当卓 handoff に記載 = **執行済**）。**F5** = DROPPED（自己申告 field）。
- **G1 台帳索引** = DROPPED（`grep -n '^## §'` が索引・台帳 :14「commit sha は照合 note」）。**G2** MEMORY.md 22,015 chars = 88.1 %（trigger 22,487 未達）→ 行動なし。**G3** 当卓 handoff = 本 session で更新（執行済）。

---

## §4 実行計画 v3（順序は CLAUDE.md:169 の連鎖で記す）
1. ✅ [L-TRIAGE] L3（§7 に stage-1 block）→ ✅ [DEFER-RECON]（§6）→ ✅ [CHECK]（§1 の再測）→ ✅ [VERIFY] cycle 1 FAIL（`dc10ba462d`）→ v2 → ✅ [VERIFY] cycle 2 REVIEW（`e4842380b3`）→ 本 v3。
2. ✅ Claude pane の配達述語を実測（§1.4・file を作らずに済む実験）。
3. **本 session で実行（file を作らず権限を動かさない項）**: (a) p6 へ C2 の問い 1 通 (b) p4 へ A4/E2/E3 の遵守所見 1 通 (c) p0 へ E1（RUN_METRICS.json）の依頼 1 通 (d) F3 を当卓 handoff へ。数は本 file の query 付きの値のみ。
4. **Rs1 へ提示（§5）**: 本 file の path＋sha＋3 行。⛔ Rs1 の一語まで tooling file を作らない。
5. Rs1 の一語の後（別 [TASK]・L2 再 triage）: [RULE-CHECK] stage2 → D1 build（pre-mortem 1 頁・否定制御 4 件 → 層2 事後 debate・層5）。

## §5 Rs1 (the human) の決定が要る項（4 件）＋ 不整合の報告（1 件）
| # | 項 | 選択肢 | 当卓推奨 |
|---|---|---|---|
| 1 | **tooling file の作成可否**: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p18_desk_tools_20260905/` に D1（script 1・bodies dir・JSONL 1・任意の一覧 file 1）。副問 = code の check 路: A) worktree で file 限定 pre-commit ／ B) worktree で `./isaaclab.sh -f` 全体 | A) 作ってよい ／ B) 作らない（手作業継続） | A（唯一、既存機構が無い項。述語は実測済・否定制御は build 後） |
| 2 | **C3C5 node の起動＋session binding**（NEST §3.1 #4） | A) 起動し**新規 session** `{node_id}#s1` を bind（p4 は現 node の handoff 後なら可）／ B) 現行どおり kickoff 運用 | A |
| 3 | 退役役名 pane pV/pW | A) 閉じる ／ B) 役を再付与 ／ C) 放置 | A |
| 4 | 卓単位の改善 task（本件のような role-bound の仕事）に NEST node を持たせるか — CLAUDE.md:128「全 task は node」と現行（node 未起票）の不整合 | A) 持たせる（Rs1 が起動承認）／ B) role-bound のまま（#34 は label の裁定で task には沈黙）| 推奨なし（不整合の解消は Rs1 専権・§運用10） |
| 報告 | **commit message の trailer**: 当卓の record commit 6 件は harness の指示で `Co-Authored-By: Claude Fable 5.1` / `Claude-Session:` を末尾に持つ。AGENTS.md「AI attribution / co-authorship 行を書かない」と衝突（§運用10 で報告）。履歴の書換は提案しない | A) harness trailer を認める ／ B) 以後 trailer 無し | Rs1 の裁定 |
**報告のみ（問わない）**: C4/C5 = HOLD（YAGNI・consumer 0）／manifest §3 heartbeat = 復活は template・退役は L3／E4 = 次の反復要求時に問う／l-gate 分割 = 既定は L3 一律（D1 は別 [TASK] で L2）。

## §6 [DEFER-RECON] 照合記録（DDR = `00-DESIGN-STATUS-LEDGER.md` §DDR・**69 行を読了**〔`grep -cE '^\| [0-9]+ \|'` = 69・@ `77f8d472a3`（2026-08-10 10:06:10）〕・下記以外の行は本 task の前提に非依存と判定）
| 前提 | DDR 項 | 依存判定 |
|---|---|---|
| 本 task の node 未起票 | **#34**（:138）role label ≠ node（pN 裁定 07-20） | #34 は label の裁定。task の node 化は CLAUDE.md:128 との不整合として §5 #4 で Rs1 へ |
| 全 commit `--no-verify`＋pathspec | **#35**（:139）validate.sh の guard 述語が世界と合わない | 整合（必要性）。code は 07-26 裁定の免除外 ⇒ D1 §10 の副問 |
| C1 の node 起動 | **#66**（:170・閉鎖済）／**#68**（:172・UR15-B premise・04-Specs 未反映）／**#69**（:173・条件つき run 認可・未発火） | #66 非依存。#68/#69 は node の DoD/run を gate し起動を gate しない ⇒ 起動は依頼のみ |
| C1 の binding 先 session | （DDR 外）`T-ROOT-Kinematic-Pin-Complete-Removal-20260719/state.md:13,:23-24` = p4 `#s1 active` | p4 を bind するなら §4 handoff が先 ⇒ §5 #2 は新規 session を既定に |
| A6 の SKILL 一覧 | **#31**（:135）trainer/実行 driver = p17＋p16 が決定／**#33**（:137）pS・pQ 軸未裁定 | 非依存（一覧は広い側に倒す・p12 の所属は #33 が閉じるまで含める） |
| D1 の配達述語 | （DDR 外）codex pane の表 = 未計測（w2 に codex 0） | build 後の残課題として p6 に register 起票を依頼（本 session の p6 宛 message に同梱） |

## §7 検証記録
- **stage-1（rule-check）**: `final_L: L3`・path 一致 = `operational-rule-LTM-1.md`（提案対象）・`check_nest_freshness.sh`（提案対象）・keyword = `ik`（§0 不変前提の言及・文脈は不変）・定量 = 新規 file ≥5（v1 時点）⇒ L3・status READY_FOR_CHECK（09-04 16:2x）。
- **cycle 1**（v1 @ `acb4ff2c2a`）: 5 体（premise/provenance 18・rule/SSOT 17・numerical 22・side-effects/history 19・NHA HOLD）→ union 40 項目・CRITICAL/HIGH 全受入 → **FAIL** → v2。記録 `P18_AGENTIC_VERIFY_CYCLE1_20260905.md` @ `dc10ba462d`（U30 の訂正注記 @ `16a8bdc1d0`）。verification-log 登録 2026-09-05 01:12 JST。
- **cycle 2**（v2 @ `ce50abc3d9`）: 5 体（14・20・12・17・NHA CHANGE_JUSTIFIED 条件つき）→ HIGH 受入（custody 行・配達判別子・C1 の二重 binding・viewport 窓・HELD/STOP・本文未保存）→ **REVIEW**（cycle 上限）→ 本 v3 ＋ Claude pane の実測。記録 `P18_AGENTIC_VERIFY_CYCLE2_20260905.md` @ `e4842380b3`。verification-log 登録 2026-09-05 07:22 JST。
