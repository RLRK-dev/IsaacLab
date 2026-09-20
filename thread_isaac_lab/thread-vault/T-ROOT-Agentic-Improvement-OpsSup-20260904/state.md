---
node_id: T-ROOT-Agentic-Improvement-OpsSup-20260904
node_name: エージェント型 AI 化の改善 — OPS-SUPERVISOR 卓の task（適用第 1 号）: hub 送信計器 D1 の build
goal: "hub 送信計器 D1（script 1・bodies dir・JSONL 1〔＋任意の話題別一覧 file 1〕）を `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p18_desk_tools_20260905/` に着地させ、Claude pane への配達述語 P1（宛先 transcript の `type=user` record に head token）を実測し、否定制御 4 件（v3 §3-D1 #9 a-d）を custody つきで bank する。〔= 提案 v3 §5 #1 の推奨 A・Rs1（人間）逐語「Rs1 待ち（前回 4 件 + 新 1 件）はすべて推奨で良い」2026-09-05 08:42:57〕"
goal_verification: |
  ① 上記 dir に script・bodies dir・JSONL が存在（`ls` で実測・path は goal 逐語）
  ② P1（配達）= 宛先 Claude pane の transcript jsonl に **`type=user`・文字列 content（list でない）・`toolUseResult` 無し・`promptSource ∈ {typed, queued}`・送信 byte（head 行 `MSG m-p18-N / …` を含む本文）を含む record** が現れる — 1 件以上、record の file:行 を引いて bank。⛔ `ABSORBED(unacked)`（宛先に queued_command record のみ・head_found=False・後続 assistant record に id 痕跡なし）は ② を満たさない〔定義 = `p18_desk_tools_20260905/CONTROLS_20260906.md:14-31`・台帳 §1439〕
     ✅ **初の実配達 = m-p18-323 → 本 node の起票卓 p6（09-06 17:11:41 JST）**: **宛先卓 p6 が自分の transcript で実測** `2dbed74a-e29c-45a7-ad8a-5c5af235885b.jsonl:25733` = `type=user`・`promptSource=typed`・content=str・toolUseResult 無し・ts `2026-09-06T08:11:41.053Z`（§1445 の delivered_at と ms まで一致）。✅ **射程注記 閉（09-06 17:50）: tool 単独の配達 = m-p18-324** — tool が置き・tool が Enter・tool が読む。hub 側 `sent_records.jsonl` row 5 = `state: DELIVERED`・**`via: Enter`**・`delivered_at 2026-09-06T08:50:07.357Z`・evidence `user@91189780+0`・HELD/verify row なし。**宛先卓 p6 が自分の transcript で実測** `2dbed74a-e29c-45a7-ad8a-5c5af235885b.jsonl:25783` = `type=user`・`promptSource=typed`・content=str・toolUseResult 無し・ts `2026-09-06T08:50:07.357Z` = **hub の delivered_at と ms 一致**（両側一致 2 件目）。〔旧射程注記（記録として保持）: m-p18-323 は送信後 gate が paste-marker の折りたたみを誤分類して HELD → p18 が composer を読んで Enter 1 回（§1445）= tool の send ＋ 人間 keypress 1 回の配達。gate 修正 = `ee24742ec6` U1〕
  ③ 否定制御 4 件〔**09-13 更新: bank 済 = (a)(b)(c)(g)・(d) = OPEN**（(c) は §1455 で閉・下記）／09-06 22:4x 時点 = (a)(b)(g)・(c) dry-run 待ち — 旧見出し「4 件が bank 済」は本文と矛盾していた〕: (a) composer に置いただけ（Enter 無し）→ NOT delivered ／ (b) queued → **配達ではない** — **bank の形 = 分類器 replay**（`scan()` を宛先 transcript 上で read-only に再生・by-hand の Tab 送信 15 件）= **ABSORBED(unacked) 9・DELIVERED 4・DELIVERED(fused) 1・DELIVERED(turn_end) 1** ⇒ queue した時点では配達でなく、宛先の turn 終端で `promptSource=queued` の user record が生じた時（turn_end）か既存 user record に融合した時（fused・**head 形 token `MSG m-p18-N /` を record 内の任意位置で数える**〔09-06 22:38 訂正・§1450: 旧「head 行のみで数える」〕）に初めて配達。⛔ **tool 自身の Tab 経路（send-keys Tab → 0.5 s viewport read）の実行 = 0 件** — (b) は分類器を検証したのであって tool の Tab を実行していない。**label 対応（同一事実の 2 つの label 体系）**: 事前登録「4 DELIVERED(fused)・1 DELIVERED」= 測定「4 DELIVERED ＋ 1 DELIVERED(fused)」（tool は record の位置 0 を、他 message を含む record でも DELIVERED と label する）= record 単位では multi-message record 4 ＋ standalone 1（m-p18-300 → w2:p4）— 受入文の「exact match」は label 体系を跨いだ一致〔`CONTROLS_20260906.md:14`・§1443・§1447〕／ (c) working 宛 → HELD〔⚠ **bank 済とは書かない**: 通したのは **自卓（hub 自身）working の枝のみ = 結果は変わり得ない**（変わり得ない検査は検査でない）・**他卓 working 時の dry-run 待ち** — §1450 V8・22:11/22:13 とも他卓は全 idle〕→ ✅ **閉（09-13・§1455 `4507749ff1`・CONTROLS Task A）**: **他卓 w2:p11 が working の時**に `send --to ARM-CONTROL-DESIGN … --dry_run` → `HELD(working) status=working composer=empty`（08:45:21 事前 blob・11:39:31 最終 blob）— **結果が変わり得る条件で通した**ので判別器として成立（`--queue` 同卓も dry-run で拒否側）／ (d) HELD→retry→DELIVERED の遷移
  ④ 事前 5 体 debate の DECIDE と事後 debate の記録（台帳 §1431 の gate 列）— ✅ **閉（09-06 22:38）**: 事後 cycle 1（§1447・FAIL → 修正 `ee24742ec6`）＋ **cycle 2 of 2（§1450・8 体・DECIDE PASS・HIGH 0・受理は MEDIUM/LOW のみ）→ 閉め commit `5b60b1556d`・code は本 blob で凍結**〔解凍 = 実 traffic で fail-closed でない失敗（他人の文字への keypress・宛先 record の無い DELIVERED 行・id の重複）のみ〕。bank 面 = 台帳 `<details>`（union 逐語・record file 形は Rs1 提案中）・CONTROLS `207230a844`〔09-20 10:20:40 p6: 凍結 → 更新 `5b3c93002d`（hub_send.py sha256 `c98064e3…`・契機・検証・凍結 pin 更新 = 下 ① の追加 step 2・台帳 §1538/§1542）— 解凍条件への該当判定は p18/p19 の記述（§1540/§1541・`DELIVERY_RELIABILITY_20260920.md` §Failure evidence）が正・p6 は記録のみ〕
  ⛔ 本 node の閉じ条件に含めないもの（隠さない）: codex pane の配達判別表 — w2 に codex pane が 0 で母集団が無い（v3 §1.1 実測）⇒ 状態 `UNKNOWN(table-not-banked)`。解消条件 = w2 に codex pane が生じた時に測る、または別 workspace で測った表を bank する。⛔「未測」であって「不成立」ではない（DDR #70 から本 node へ移管）
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  # ⚠ 依存の実体は本文 §3（p18 台帳 §1431 の gate 列）。blocker = 0。
  # precedent 欄は §3.1 #2 で起動条件として消費される欄ゆえ、走行中の gate（debate）は載せない。
  precedent: []
  blocker: []
session_history:
  - id: T-ROOT-Agentic-Improvement-OpsSup-20260904#s1
    status: active
    started_at: 2026-09-04T16:08:00+09:00
    note: "遡及 bind — 根拠 = Rs1（人間）が p18 推奨 A′ を採択（提示 :39597 → 受諾 :39600・promptSource=suggestion_accepted）= DDR 71〔09-06 訂正: 起票時の表現「NEST §6.2 既存 active task 段階適用」は類推であって §6.2 手順 1-3 を踏んだ記録ではない — 語だけ残し根拠から外す〕。実体 = w2:p18 T-ROOT-OPS-SUPERVISOR の claude session 1c3d805c-2a9a-4b6d-bba2-ae7d479862e7（herdr agent list 2026-09-05 11:12 実測・custody transcript と同一 file）。started_at = Rs1 直接指示の時刻（09-04 16:08・v3 doc 冒頭）。⚠ 手順 4（本 state.md の preflight）と手順 5（status → IN_PROGRESS）は bind された session = p18 が行う。p6 は起票のみ・flip しない。"
define_artifact: "eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P18_AGENTIC_SYSTEM_IMPROVEMENT_20260904.md @ f5c681edb3（sha256 4d1e7ac099f8825924367bcd57b0a8ba099d6ab38bfe2d4488e9ada3ed77b86f・p6 が worktree と blob の両方で自算一致）"
created: 2026-09-05T11:12:20+09:00
last_updated: 2026-09-20T10:20:40+09:00
spec_version: LTM-1 v1.2
---

# T-ROOT-Agentic-Improvement-OpsSup-20260904 — 卓単位 task の node 化・適用第 1 号

## 0. 本 node の status が起票時 PENDING だった理由（→ **09-05 11:18:57 に IN_PROGRESS**・§6）〔見出しも主張を配るので 09-06 に併記で訂正〕

- **作成承認 = Rs1（人間）逐語「3項すべて推奨で良い、pV/pW は B」（2026-09-05 11:07:48 JST）**。custody = p18 transcript `1c3d805c-2a9a-4b6d-bba2-ae7d479862e7.jsonl:39600`（`type=user`・`origin.kind=human`・`isCompactSummary` 無し・head token 無し・**`promptSource=suggestion_accepted`** = UI が提示した文を人間が受け入れて送信した record〔対照: 08:42:57 の file 認可 `:39366` は `typed`〕・**p6 が両 record を実読 09-05/09-06**・台帳 §1439 @ `2524504b9c`。⇒ **決定は人間の行為・文言の著者は UI 提案** — 本 file の「逐語」は *送信文* の逐語であって *人間が打った文* ではない）・台帳 §1432 @ `33766d3a32`。
- **等級 = labelled inference（検査可能）**: Rs1 が答えた labelled set = 同 transcript `:39597`（p18 の 11:07 提示・p6 実読）の「1. #4 卓単位 task の node 化 — 推奨 **A'（折衷）**: file を作る・共有面を変える卓 task だけ node 化（**本 D1 build が該当・親 T-ROOT・p6 が起票**）」。⇒ **「p6 が起票・親 T-ROOT」は提示文の中に在り**、Rs1 はそれに「推奨で良い」と答えた。⚠「= NEST §3.1 の子 node 作成承認」という語は p18 の読み（§1432）で、提示文には無い — p6 はこの読みを提示文と矛盾しないものとして採る。
- **status = PENDING の理由**: 本 node は **走行中の仕事に後から起票**したもの（根拠 = Rs1 が推奨 A′ を採択 = DDR 71。〔09-06 訂正〕「§6.2 段階適用」は起票時の類推であって手順 1-3 の記録ではない）。session は既に在り（`session_history` の #s1・遡及 bind）、仕事も走行中（台帳 §1431 の debate）。ただし **§3.1 手順 4（本 state.md の preflight）と手順 5（status を IN_PROGRESS に更新）は bind された session の行為** — p6 は 10:59 に C3C5 node で同じ読みを返しており、自分の起票にも同じ規律を適用する。⇒ **p18 が本 file を読み（手順 4）、status を IN_PROGRESS に更新（手順 5）した時点で flip**。
- ⛔ 本 node は **run 認可・§0 不変前提・設計面・NEST spec・CLAUDE.md・skills・hooks を動かさない**（台帳 §1431「触らないもの」逐語）。

## 1. 目的（goal 欄逐語）と閉じ条件（goal_verification 欄）

front matter が正。要点: **D1 = 唯一の build 候補**（v3 §3-D）。file 4（script・bodies dir・JSONL・任意の一覧）・hub-only binding・配達述語 P1（宛先 transcript record）＋従述語（agent_status 遷移）＋第 3 述語（viewport）・`STUCK_IN_COMPOSER`・HELD/`--stop`・fan-out・記録 schema・lint は後日。

## 2. 手段（means）= p18 台帳 §1431 の gate 列（逐語要約・p6 実読）

[TASK] L=L3（定量: script >200 行）→ [L-TRIAGE] 済 → [DEFER-RECON] = v3 §6（DDR 69 行 @ `77f8d472a3`）＋ DDR #70（`2773ba6e21`）非依存 → [CHECK] = PROPOSE v1（scratchpad `d1_build/D1_BUILD_PROPOSE_v1.md`・bundle `d1_build/BUNDLE_D1.md` 168 行）→ [VERIFY] **事前 5 体 debate 起動 2026-09-05 11:05**（CC2 premise/provenance・CC3 rule/SSOT・CC4 numerical・CC5 side-effects/history・CC6 NHA・全員 read-only）→ REBUT_OR_ACCEPT → DECIDE（FAIL なら v2・cycle max 2）→ build → 否定制御 4 → 事後 debate → bank。prior-art guard = BLOCKER_CONTEXT_FOUND（内容 = pane ID drift・routing directive・self-start 禁止 — 本 build の失敗路ではない）・**delta 明記**（旧 `dispatch_to_pane.sh` は spinner/ack の 1 面を配達と読んだ／D1 は宛先 transcript の record ＋ head token ＋ live 完全一致解決）。

## 3. 本 node が authorize しないもの（明記）

⛔ run・GPU・training ／ ⛔ §0 不変前提 ／ ⛔ 設計面（04-Specs・07-Design）／ ⛔ NEST spec・CLAUDE.md・skills・hooks の編集（本 task 中の提案は「報告のみ」= v3 §3 の C3/C4/C5・§5 報告欄）／ ⛔ 他卓の task の node 化（**適用第 1 号は本 node のみ** — 以後の卓 task は「file を作る・共有面を変える」もののみ、都度 Rs1 の作成承認）。

## 4. 前提と DDR（[DEFER-RECON]・p6 実施）

| 前提 | DDR | 判定 |
|---|---|---|
| 卓単位 task の node 化 | **#71**（本ルーリングの例外行 = custody/relay の日常は role-bound のまま） | 本 node はその「例外でない側」= file を作る task |
| 旧 #70 の残課題 | **#70**（09-05 11:1x CLOSED・残課題は本 node の goal_verification ⛔ 行へ移管） | codex 表 = 母集団 0 |
| commit trailer | Rs1 裁定 A（harness trailer を認める・§1432） | 本 node の commit も同じ |
| pre-commit の路 | v3 §3-D1 #10 の副問（detached worktree で file 限定 (A) か全体 (B)） | 裁定は build の DECIDE 内で p18 が選び bank（Rs1 は §5 #1 A で「作ってよい」まで） |

## 5. 記録の作法

- 本 file の作成 = p6 PLAN-KEEPER の執行 lane（Rs1 承認の下・§1432）。**内容の決定は p18（本 task の court）と各 gate**、p6 は記録のみ。
- 進捗の反映は **verdict / 最終行為のみ**（DECIDE・着地 sha・否定制御 bank・事後 debate）。途中経過は台帳 §13xx 系が正で、本 file はそれを指す。
- 閉じる時: goal_verification ①-④ を file:行 で引き、⛔ 行（codex 表）は「未測・母集団 0」のまま閉じてよいか **Rs1 の一語**で確定（本 node の閉じ条件から外すと宣言したのは p6 の起票時の読み — Rs1 が含めると言えば戻す）。

## 6. 起動手順 4/5 の記録（bind された session = w2:p18 の行為・NEST §3.1）

- **手順 4（preflight）** 2026-09-05T11:18:57+09:00: 本 file を disk で読み、起票 blob と一致（`git show f25a237fb9:state.md` sha256 先頭 `0501410b` == disk）。status = PENDING（HANDED_OFF でない）。本 node は新規起票で handoff artifact・pins sidecar を持たない ⇒ §4.4 の二段階 sidecar 検証は対象外（対象 file が無い）。session 冒頭の `preflight_check.sh` = 7/11 PASS・0 FAIL・4 WARN（既知: P5 共有 tree 残留・P7 stale lock・P9 env_isaaclab6 不在・P11 snapshot 鮮度 = 本更新で再発するので p6 の再生成待ち）。
- **手順 5** 2026-09-05T11:18:57+09:00: `status: PENDING` → `IN_PROGRESS`（frontmatter :11）・`last_updated` 更新。flip の主体 = 本 session（p6 は flip しない・m-p6-150）。
- 走行中の gate: 事前 5 体 debate（台帳 §1431・11:05 起動）。DECIDE 後に build。

## 7. DoD 進捗（p6 反映・verdict のみ・2026-09-06 17:14:58 JST）

- **①** ✅ 着地: `hub_send.py`・`bodies/`・`sent_records.jsonl`（＋`by_hand_20260905/`・`CONTROLS_20260906.md`）が goal の dir に存在 — p6 `ls` 実測 09-06 17:1x・landing `2f154e9e21`（09:24）→ 記録 `89ae2e53c8`（09:25）→ 修正 `f422f92ad0`（17:09・floor query の hook 通過）→ **事後 cycle 1 の修正 `ee24742ec6`**（17:48・+359/−140・script sha256 `c19dd27c264d2b44…`・**903 行 = spec 目標 ≤250 の declared deviation**〔分割は新 file ⇒ Rs1 の語〕・CONTROLS 追記 `2cd75bf2d7` 17:49）→ **閉め `5b60b1556d`**（22:35・sha256 `a0a099145bf2e97cd08188180d138d0897c468ae643389859c9e0c4274d89c4d`・**1016 行**〔deviation は 903 → 1016 へ拡大・宣言は同じ〕・**凍結**）→ ⭐**追加 step = task A「herdr 0.9.0 適応」`44e0f9a2d1`**（09-13 11:44:40・`hub_send.py` +33/−15・CONTROLS +229〔Task A 節・宣言済 limits (a)–(f)〕・**新凍結 sha256 `b4944c191dcc20f11d3eb3135197d55be5ceac95d0fa8f12968609d0810b00b5` = worktree・1034 行**・新 CLI 引数なし。契機 = herdr 0.9.0（09-10 00:38 導入）が `agent send` を廃止し tool が refuse で停止（§1453）→ Rs1 の語「Aで進めて、p11の件は手送りで届けて」`:41666`（promptSource=suggestion_accepted・08:31:34）→ 事前 5 体 debate **cycle 1 of 1 = PASS**（HIGH 2／MEDIUM 12／LOW 19・NHA CHANGE_JUSTIFIED・§1455）・unit 20・live pane への read-only dry-run 17・code gate A。**解凍の形 = 新 task＋自前 gate＋人間の語**（CONTROLS の解凍規則どおり）。**D7 = 再建 tool の初実送信 = m-p18-327 → p6**（下 ②）。→ ⭐**追加 step 2 = 配達修理「Make hub delivery observable and retry-aware」`5b3c93002d`**（author 09-20 10:05:44・commit 10:11:21・作者卓 = p19 = `w2:p19` codex〔label 空・台帳 `:48095`〕・3 file のみ = `hub_send.py` +137/−85・`test_hub_send.py` +243（新規）・`DELIVERY_RELIABILITY_20260920.md` +128（新規・sha256 `97e27623767feedf9db5c33e25add57e1f081b2ae6ef1ad4d76295ad9a51dce6`）・**新凍結 sha256 `c98064e34cfcb3b20e13b798f4606bece809a8fb269cc5c6434ad2fa8eae0287` = HEAD blob・1086 行**・隔離候補 `f9b019a33e` と blob 同一・sent_records/bodies 不変・以後 hub_send.py の commit 0 — 全て p6 が git で自算）。契機 = 本日の HELD 12 件・死んだ leg・composer 滞留（台帳 §1518/§1540/§1541）→ **Rs1（人間）の語「ok 改善して」= p19 rollout `~/.codex/sessions/2026/09/13/rollout-2026-09-13T23-19-12-01a09b22-….jsonl:1337`**（`2026-09-20T00:44:34.981Z` = 09:44:34 JST・`payload.type=message`・`role=user`・直前 `:1323` 09:43:40 = 利用者の問い・p6 実読）→ p18 の独立検証 **§1538 @ `9c463d9f4d`**（隔離 worktree・live send 0・14 test OK・凍結版 baseline = 同 suite で 7 failures + 4 errors・E1–E7 = test と code 行で照合）→ 着地検証＋**凍結 pin 更新 `44e0f9a2d1` → `5b3c93002d` = §1542 @ `a4f07343ff`**。p6 が読んだ範囲（§1538/§1542・設計 doc）に 5 体 debate の記録なし（事前 gate = 隔離 test＋p18 独立検証・設計 doc §Independent-check expectations）。**E8 = 新 tool の初 live 便 = m-p18-416 → p6**（下 ②）。〔p6 09-20 10:20:40 反映・verdict-only〕
- **②** ✅ 上記（宛先卓の実測つき）— **射程注記は 09-06 17:50 に閉**: tool 単独の配達 = m-p18-324（宛先 `:25783`・hub row 5 `via: Enter`・ms 一致）。**09-13: herdr 0.9.0 上の初実送信 = m-p18-327（task A の D7）**も両側一致 — 宛先 p6 `:25908` = `type=user`・`promptSource=typed`・ts `2026-09-13T02:46:54.555Z` = hub row 7 `delivered_at`・`via: Enter`・`herdr_version: herdr 0.9.0`（両側一致 4 件目・`pane send-text` 経路の初）。 **09-20: E8 = 修理版 tool（`5b3c93002d`）の初 live 送信 = m-p18-416 → p6** も両側一致 — 宛先 p6 `2dbed74a-e29c-45a7-ad8a-5c5af235885b.jsonl:28227` = `type=user`・`promptSource=typed`・content=str・toolUseResult 無し・ts `2026-09-20T01:15:01.120Z`（10:15:01 JST）= hub row `delivered_at`（ms 一致）・`via: agent_prompt`（新経路・旧 `send-text`+Enter ではない）・head「MSG m-p18-416」= content offset 29（固定 29 byte 貼付 prefix・id 84b2 = §1541 のとおり 08:07 以前から全配達に前置）・hub 側 = 意図行 `UNKNOWN(submission_in_progress)`（10:15:00.774）→ 完了 row `DELIVERED(fused_with_unknown_prefix)`・`head_found=true`（`sent_records.jsonl` 末尾 2 行 @ `a4f07343ff`・p6 実読）。E8 の p6 側処置（設計 doc `:120`「p6 records artifact pointers and returns that pointer」）= 本 file の本行・①・末尾 09-20 行＋本 commit の path を p18 へ返す。**受領 ≠ engineering 受入・run 解錠なし**。
- **③** **(a)(b)(c)(g) = 閉**〔(c) は 09-13 §1455 で閉 = w2:p11 working 時の dry-run → HELD(working)・09-06 時点は「自卓 working の枝のみ = 検証でない・他卓 working 待ち」（§1450 V8）〕／(b) の bank の形 = 分類器 replay・tool の Tab 経路 実行 0 件・数え方 = head 形 token を record 内の任意位置で／**(d) OPEN**（実 traffic の HELD → resend まで）／**(d) HELD→resend→DELIVERED = OPEN**（実 traffic が working 卓に当たった時に `resend --id` で測る）／(h) = Rs1 の 2 文字待ち（下書き半分の制御）。
- **④** ✅ **閉（09-06 22:38・§1450 `36db0ce285`）**: 事後 cycle 1（17:12–17:40・U1–U28・FAIL → `ee24742ec6`）→ **cycle 2 of 2（8 体・17:52 起動・6 体が 22:00 上限で落ち再起動・22:29 全完了）= PASS・HIGH 0** → 閉め `5b60b1556d`・凍結。〔経緯: 09:26 の初回 8 体は 7 体が session 上限で落ち view 1 のみ完了〕。〔09-20: 凍結 → 更新 `5b3c93002d`（① 追加 step 2・E8 = ②）・本更新の事前 gate = p18 独立検証 §1538（隔離 test 14 OK・baseline 識別性あり）・5 体 debate の記録は p6 が読んだ範囲に無し（p6 は可否を判断しない）〕
- ⇒ **status = IN_PROGRESS 継続**（〔09-06 17:14 時点: ③(d)・④ が open〕→ ④ は 09-06 22:38 に閉・③(c) は 09-13 に閉 ⇒ **残 = ③(d) のみ**〔09-13 併記訂正: 本行は 22:40 に追記線で越されて「④ open」のまま残っていた〕）。閉じる時は §5 のとおり。
- ⇒ **status = IN_PROGRESS 継続**（残 = **③(d) OPEN のみ** — 09-13 に (c) 閉）。**COMPLETE は Rs1（人間）の語**（codex 表の除外・未追認 2 file の後）— p6 は flip しない。〔2026-09-06 22:40:43 JST・verdict-only〕
- 〔2026-09-13 11:49:46 JST・m-p18-327 反映・verdict-only〕 **DoD 現況: ① ✅（task A 含む）／② ✅／③ (a)(b)(c)(g) 閉・(d) OPEN／④ ✅**。他卓の sender は各卓の事項（p4 は自卓 sender を未検証と記帳 `9e9f6199b3`）— 本 node は hub の tool のみを対象とする。
- 〔2026-09-20 10:20:40 JST・m-p18-416 反映・verdict-only〕 **送信 tool の凍結 pin 更新: `44e0f9a2d1`（hub_send.py sha256 `b4944c19…`・1034 行）→ `5b3c93002d`（hub_send.py sha256 `c98064e34cfcb3b20e13b798f4606bece809a8fb269cc5c6434ad2fa8eae0287`・1086 行・`DELIVERY_RELIABILITY_20260920.md` sha256 `97e27623767feedf9db5c33e25add57e1f081b2ae6ef1ad4d76295ad9a51dce6`・`test_hub_send.py` 243 行）= p6 が HEAD blob と `5b3c93002d` blob の両方で自算一致**（relay m-p18-416 = E8 便そのもの・Rs1 custody = p19 rollout `:1337`「ok 改善して」09:44:34 JST・p6 実読）。**DoD 現況: ① ✅（step 2 含む）／② ✅（E8 両側一致）／③ (a)(b)(c)(g) 閉・(d) OPEN**〔本日の HELD 12 件 = 「再送しない・内容は bodies/ で到達済・operator review」= p18 の語 §1542/§1543・never_submitted 112 件の完了送信は E8 後に p18 が再開（§1543）・(d) の閉否は p18 の court〕／**④ ✅**。条件（relay 逐語）: 受領は engineering 受入や run 解錠を意味しない・旧 HELD 12 件は再送しない・本便は idle 宛先のみ・`--queue` 未使用。COMPLETE は Rs1（人間）の語 — p6 は flip しない。
