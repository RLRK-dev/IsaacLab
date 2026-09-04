# エージェント型 AI 化の改善提案 — herdr 上の CC pane 群を「自ら考え・行動し・環境から feedback を得て改善する系」にする

**作成** p18 (T-ROOT-OPS-SUPERVISOR) — 2026-09-04 16:1x JST（date 実測）
**契機** Rs1 (the human) 直接指示（当卓 session）「エージェントの役割分担、エージェントの数、NEST Tree 等 改善点をあげて、次にそれらの点で改善を実行して」
**L-triage（自己申告）** = **L3**（NEST 仕様 `operational-rule-LTM-1.md` §9 の改訂提案・validation logic・役割 topology に触れる）⇒ §運用2 [VERIFY] 5 体検証を実装前に実施（結果は §7 に追記）。
**動かさないもの（先に明記）** ⛔ §0 不変前提（DUAL-ARM / 88 mm span / IK のみ・kinematic trick 禁止 / gripper 幾何 LOCK）・run 認可の所在（Rs1 のみ）・動画の物理妥当性判定（Rs1 の目）・04-Specs/07-Design の read-only・役名は Rs1 割当。本提案は **調整機構と feedback loop** の改善であって、設計権限の移動ではない。
**造語なし**: 新機構は一般語で記述する（名を作らない）。

---

## §1 現状の実測（2026-09-04 16:12–16:17 JST・全て再測可能な command つき）

### 1.1 pane topology（`herdr agent list`）
| 区分 | pane | 前 session（08-09 17:3x → 08-10 10:07）の稼働 |
|---|---|---|
| hub | p18 OPS-SUPERVISOR | 稼働（当卓） |
| 核 6 | p4 RS-TECH-LEAD（= Rs2 代理）／p0 IMPL-BUILDER／pZ IMPL-VERIFIER／p5 SKILL-DETAIL-DESIGN／p6 PLAN-KEEPER／p11 ARM-CONTROL-DESIGN | 稼働 |
| 分析 2 | pB LOG-ANALYST／pC VIDEO-ANALYST | **不使用**（DoD 動画は Rs1 が phone で直接判定・run.log の行引用は p0 が手作業） |
| WMSO 5 | p12 RS-TECH-LEAD2／p14 IMPL-BUILDER2／p15 IMPL-VERIFIER2／p16 WMSO-DESIGN／p17 SKILL-DESIGN | dormant（設計どおり: WMSO D1.1 FROZEN・self-start CLOSED） |
| 退役役名 2 | pV T-ROOT-COORD／pW T-ROOT-COORD2 | pane は生存・役は 07-20 に ARCHIVED（memory pass14） |
合計 **16 pane・全 idle**（当卓以外）。**25 日間 commit 0**（`git rev-list --count --since='2026-08-10 10:07' HEAD` = 0）。

### 1.2 前 session の稼働実績（当卓台帳 §1254–§1406 = 151 節・`grep` 計数）
| 量 | 値 | 読み |
|---|---|---|
| 全 commit（08-09 17:30 → 08-10 10:07） | 134 | 16.5 時間で 134 = 7.4 min/commit |
| hub の dispatch（m-p18-* 一意 id） | 47 | 21 分に 1 通 |
| Rs1 裁定/一言を記録した節 | 34 | 人間の介入点 = 約 30 分に 1 回 |
| custodian bank commit（他卓の artifact を当卓が commit） | 12 | pZ に commit 権限が無いため |
| **自己訂正を見出しに持つ節** | **26（17.2%）** | 6 節に 1 節は誰かの訂正 |
| stale / 交差 / 追い越し の言及 | 38 | relay が object に追い越された事例 3・stale-ask 3 |
| 部分読み・分母 の言及 | 13 | 当卓 2 回＋伝播 1（asset header）＋**本日 3 回目（§1.5）** |
| 折返し・regex・delimiter 族の言及 | 19 | 4 卓 6+ 事例（同じ class） |
| correlated assent の言及 | 5 | 2 卓が同じ誤数を「自測」として保持した実例 1 |
| readback の NO-HIT 判定（記録分） | 3（実際は毎 dispatch 1–3 回 probe） | viewport scrape の限界 |
chain の所要: dep-1 の unlock→受入 **17 分**／鏡像 Rs1 所見→受入 **38 分**／fork 決着 **10 分**／(c) 解散 **7 分**／kinonly bundle 認可 1 回で **shakedown 10 本**（1 晩）／DoD run 2 本 = **2 本とも STEP 2 で stall**（2 本目は計器が事前に予測: witness L 0/240）。

### 1.3 NEST
- node = 254（`find … -name state.md`）・最新更新 08-10 10:01（C3C5）。**活動中の chain（C-2 取付→UR15-B→controller）の node `T-ROOT-C3C5-…` は status PENDING = 未起動**（§3.1 #4 の Rs 起動承認と session binding が無い）— 実作業は kickoff file（p4・2,200 行超）と当卓台帳（46k 行）と register row で回っていた。
- manifest: frontmatter `last_updated 2026-08-06`、実体更新 07-27 `ec03cf13d5`、**未解消の食い違い 2 件**（root_node_id `T-ROOT` vs §2 の `T-PRODUCTION-LINE` 親／§1 234 vs §2 252）— 木の裁定は Rs 専権と manifest 自身が明記。
- preflight P11 WARN: D2（node 心拍 25 日）・D3（manifest stale）。D2 は **state.md の mtime** を測るが、実作業は kickoff/台帳に住んでいた ⇒ **心拍が測っている面と、仕事が起きた面が違う**。
- 役名登録 `scripts/validations/nest_role_labels.txt` = **19 役名すべて登録済**（COORD/COORD2/VT-DESIGN の退役名も残存）。

### 1.4 通信基盤
- 現状: `herdr agent send` ＋ `pane send-keys Enter` ＋ **viewport scrape**（`agent read --source recent` を tr で正規化して grep）。前 session で判明した限界: 折返しで probe が割れる（§1355）・送信直後は render 前で miss（§1366）・cc は届いたかどうかが誰にも分からない（p4 が p0 の (i) を持っていなかった・p6 も同様 §1380）。
- **未使用だった herdr 機能（本日実測）**: `herdr wait output <pane> --match <text> --source recent-unwrapped --timeout MS`（一致まで block・timeout は JSON `error.code=timeout`）／`herdr wait agent-status <pane> --status working|idle`（受信側が処理を始めた事象）／`agent read --source recent-unwrapped`（折返しなし）／`herdr agent start`（agent の programmatic 起動）。⇒ **配達証拠を決定的に取れる primitive が既に在った**。

### 1.5 本日の自己捕獲（証拠として載せる）
当卓は `head -25` で役名 file を読み「8 役名が未登録」と書きかけた。全文（43 行）では 19 役名すべて登録済。**前 session で 2 度 bank した「部分読みの分母」class が、提案書を書く手の中で 3 度目に発火した**（公表前に捕獲）。⇒ §5-F3 の lint は当卓自身に要る。

---

## §2 「エージェント型」を本系に当てはめる（perceive → decide → act → feedback → improve）
| 段 | 今できていること | 測れた欠落 |
|---|---|---|
| perceive | 計器（kinonly 表・run.log・live stream・stills）・事前登録 acceptance | 動画を読むのは Rs1 だけ（pB/pC 不使用）・run.log の要約は手作業 |
| decide | 設計 court（p11/p5）・Rs2 代理裁定・5 体検証（p11 の草案を FAIL にした） | court 受諾の handshake で待ち（p11「court word 待ち」）・prior-art guard の未実行が panel まで漏れた |
| act | announce-first・parent-relative leg・content-sha 等号受入（chain 3 本が同型で閉じた） | relay が object に追い越される（3 回）・cc 不達 |
| feedback | run が自ら止まる gate・live stream の保全・計器の事前予測（L 0/240） | 予測が run 認可要求に**添付される規則がない**（p5 が手で添えた）・run 後の要約が手作業 |
| improve | 誤りが数分で自己訂正され台帳に法として残る（26 節） | **法が散文のまま機械化されず、同じ class が卓を跨いで再発**（部分読み 3・記憶の数 5・stale pin 4・regex 6+） |

---

## §3 改善点（各項: 証拠 → 提案 → court → L → 今すぐ実行可か）

### A. 役割分担
**A1. hub の 2 機能を分ける — relay は script、custody は p18**
証拠: §1.2 の stale/交差 38・cc 不達・47 dispatch 全部に手作業 readback。提案: 送信・配達証拠・時刻印字を **配達記録付き送信 script** に置き、p18 は検証と bank に専念。court: p18（自卓運用）。L: eval_runs 配下の desk tooling（p0 の計器と同じ置き方・前例あり）。**今すぐ実行可**。
**A2. Rs1 の言葉の受け口を 1 つにする**
証拠: 裁定が p4 pane（「a」「A」「すすめて」）と p5 pane（撮り直し指示）に分かれて着地・custody は各卓の kickoff 節に散在（当卓台帳が横串）。提案: **裁定の追記専用 file**（受けた pane が受領時に逐語＋pane＋date 実測を追記・p6 の register row はそこを指す）。court: p6（register）＋各卓（追記）。L: 新 file（L2）— eval_runs 配下なら desk artifact 相当。**今すぐ雛形を作れる・採用は各卓**。
**A3. 設計 court の handshake を standing 化**
証拠: p11 は「court word 受諾」を待って idle（§1400 → §1403 の間）。提案: role brief に書かれた court は**受諾不要の standing**（依頼は即着手・拒否時のみ返す）。court: p4（brief の管理）・Rs1（役割）。L: brief 文言の変更 = artifact 追記。**提案のみ**。
**A4. 分析 2 卓を DoD chain の既定段に入れる**
証拠: DoD 動画 2 本とも Rs1 が phone で判定し「構成が良く見えない」→ stills を追加（§1396）。run.log の行引用は p0 が手作業（§1383, §1395）。提案: (i) pC = **判読性の事前 gate**（両腕・両手・取付が読める frame が在るか — 物理妥当性は判定しない・Rs1 専権不変）(ii) pB = **run 記録の要約器の消費者**（§5-E1 の JSON を読む）。court: p4（chain 定義）・pB/pC（計器）。L: workflow 規則。**要約器は今すぐ・chain 組込は提案**。
**A5. 退役役名の pane 2 つ（pV/pW）**
証拠: 役は 07-20 ARCHIVED・pane は生存・cc 対象になり得る。提案: 閉じるか役を再付与（Rs1 割当）。**Rs1 決定**（pane close は不可逆）。
**A6. WMSO 5 卓**: 設計どおり dormant を維持・**既定 cc 一覧から外す**（届かない cc を減らす）。court: p18 運用。**今すぐ実行可**（当卓の送信先既定）。

### B. エージェントの数
証拠: chain の律速は**人数でなく調整**（closure 7–38 分・10 shakedown/晩・pZ は 4 leg を逐次でこなし律速にならず・p15 の並列検証が要った事例 0）。**結論: 増やさない**。配置換え: 核 7（hub 含む）＋分析 2 を稼働（= 9）／WMSO 5 は dormant／退役 2 は Rs1 判断。16 → 稼働 9・待機 5・（2 は決定待ち）。

### C. NEST Tree
**C1. 活動 chain と node の結合**: C3C5 node を **起動**（§3.1 #4 = Rs1 承認）し、session_history に p18/p4/p0/pZ/p5/p6/p11 の session を bind。**Rs1 の一語が要る**。
**C2. manifest の食い違い 2 件**: root = `T-PRODUCTION-LINE`（07-27 `ec03cf13d5` 以降の実体）を frontmatter に反映・§1 の 234 を §2 の 252 に揃える — **木の裁定 = Rs1**（manifest 自身が明記）。p6 が執行。**Rs1 の一語**。
**C3. 心拍の測り方**: D2 が state.md の mtime だけを見る ⇒ chain の checkpoint（announce/landing/leg/受入）で **node の session_history を更新する規則**を入れる（実体の面を心拍にする）。court: p6＋NEST §9。L3（validation logic）。**提案＋差分案**。
**C4. 依存の語彙**: NEST は precedent/blocker の 2 語だが、p4 の DEFINE は grade cap／constraint を要して comment に逃がした（C3C5 state.md 冒頭）。提案: state.md に **read-optional の `grade_caps:`／`constraints:`** を足す（§9 の後方互換規則どおり parser default None）。L3。**差分案を §6 に置く**。
**C5. chain を node の属性にする**: announce→landing→leg→受入 の 4 commit を **`chains:` list（read-optional）**として state.md に持たせる（custody trail から機械生成可）。L3。**差分案**。

### D. 通信基盤（最大の実測痛点）
**D1. 配達記録付き送信 script**（当卓 tooling）: 本文 file → 各宛先へ `agent send`＋`Enter` → `wait agent-status working`（受信側が動いた）→ `wait output --match <末尾 token> --source recent-unwrapped`（配達証拠・折返し無縁・render 競合無縁）→ 追記専用 JSONL に {id=sha256(本文), to, sent_at(script が date), delivered_at, evidence} を記録。**時刻を script が刻む**ので「記憶の時刻」class（p0 1・p4 4）は構造的に消える。**今すぐ実行可**。
**D2. 共有追記ログ**: 上の JSONL を全卓共通の 1 file にすれば cc は「file を tail する」ことで確実になる（viewport に依らない）。採用 = 各卓が同 script で送る。**雛形は今すぐ・採用は各卓**。
**D3. message id**: 各卓の counter（衝突・別系列 m-p4-* を p5 が使用）→ sha id で一意。D1 に内包。

### E. 環境からの feedback（エージェント型の核）
**E1. run 記録の要約器**: run.log → JSON（構成 echo・STEP ごとの tool err・COMMAND 到達率・mast/arm-to-arm・gate 文・exit）。前 session で p0 が 3 回手作業した行引用（§1383/§1395）を機械化。pB が消費。**今すぐ実行可**（format は `_gen/*/run.log` の `[steps]` 行から実測）。
**E2. 認可要求に予測を必ず添える**: p5 が手で添えた「witness L 0/240 → stall 見込み」を規則化 — run 認可を求める message は計器の予測行を同行に持つ。court: p4/p5。**提案**。
**E3. 動画の判読性 pre-gate**（pC）: Rs1 に出す前に「構成が読める frame」検査＋stills 自動生成（p0 は montage への構成 camera を「次の認可編集窓で」と受諾済 §1397）。**提案**。
**E4. bundle 認可の一般化**: 静的 class（mj_step 0）の計器は bundle 認可（1 語で自由反復）が最高効率だった（10 shakedown/晩）。wired run は 1 語 1 run のまま。**認可方針 = Rs1**・提案のみ。

### F. 自己改善の機械化（法 → 検査）
**F1. pin lint**: hex token には function 語（commit/blob/sha256）が同行に要る・content sha には commit が要る（pZ の法 §1391）。送信 script が送信前に検査し、欠けたら送らない。**今すぐ実行可**。
**F2. 時刻**: D1 で構造的に解決。
**F3. 分母**: 記録から数を引く時は **summary 行**を引く（§1.5 の当卓再発が根拠）。要約器（E1）が summary 行を返す・lint は「`:行番号` の無い数」に警告。**今すぐ（警告のみ）**。
**F4. 折返し/regex**: readback を `recent-unwrapped`＋`wait output` に移す（D1）・source の grep は改行平坦化＋空白 squeeze の helper。**今すぐ**。
**F5. correlated assent**: 送信 JSONL に `measured_by`（自測した卓）を持たせ、register の「N 卓一致」は measured_by の集合で言う。**D1 の field**。

### G. 知識・台帳
**G1. 当卓台帳 46k 行**: 見出し索引（§番号・見出し・commit）を生成して新 session の入口にする。**今すぐ**。
**G2. MEMORY.md** 22,015 chars = 88.1%（trigger 22,487 未達）— 行動なし。
**G3. handoff**: 本 task の終わりに当卓 handoff を書く（§運用13）。

---

## §4 実行計画（本 session で当卓が行う順）
1. [L-TRIAGE] rule-check stage1 → L3 確定（§7 に記録）
2. [VERIFY] 5 体検証（verification-subagent）— 本提案を PROPOSE とし、challenger の指摘を §7 に反映
3. 実行（当卓権限内・L1 以下 or desk tooling）: D1/D2/D3/F1/F3/F4/F5 の送信 script ＋ 共有追記ログ雛形 ／ E1 要約器 ／ G1 索引 ／ A6 既定 cc 一覧 ／ A2 裁定追記 file の雛形 ／ 前 session の未 commit 台帳節の回収（済 `043e10901b`）
4. 提案の配付: 生存 9 卓（核 6＋分析 2＋hub）へ本 file を送り、各卓の court に属する項の受諾/反証を求める（agentic = 各卓が自分の面で判断する）
5. Rs1 へ提示（BLOCKED_FOR_USER 相当・§6）: C1 起動承認／C2 木の裁定／A5 pane 2 つ／C3-C5 NEST §9 改訂の差分案／E4 認可方針／A3 standing court
6. 当卓 handoff 更新

## §5 実行結果（当卓・本 session）— 実行後に追記
（§7 の下に「§8 実行記録」として追記する）

## §6 Rs1 (the human) の決定が要る項（当卓は実行しない）
| # | 項 | 選択肢 | 当卓推奨 |
|---|---|---|---|
| 1 | C3C5 node の起動承認＋session binding（NEST §3.1 #4） | A) 承認して bind ／ B) 現行どおり kickoff 運用 | A |
| 2 | manifest root の裁定（`T-ROOT` vs `T-PRODUCTION-LINE`） | A) T-PRODUCTION-LINE を root と確定 ／ B) 保留 | A（07-27 以降の実体） |
| 3 | 退役役名 pane pV/pW | A) 閉じる ／ B) 役を再付与 ／ C) 放置 | A |
| 4 | NEST §9 改訂（C3 心拍・C4 語彙・C5 chain — read-optional field 3 つ） | A) 5 体検証後に着地 ／ B) 提案のまま | A（§6 末尾の差分案） |
| 5 | 静的計器の bundle 認可の一般化（E4） | A) 既定化 ／ B) 都度 | Rs1 の方針 |
| 6 | 設計 court の standing 化（A3） | A) brief に明記 ／ B) 現行 | A |

### §6 末尾 — NEST §2.3 state.md front matter への差分案（read-optional・§9 後方互換）
```
# 追加候補（parser default None・既存 artifact を refuse しない）
grade_caps: []      # 例: "#48 cable premise (spec 未着地)" — 依存でなく等級 cap
constraints: []     # 例: "D6: 04-Specs read-only" — 依存でなく制約
chains: []          # 例: {name, announce, landing, leg, acceptance}  各 = commit sha（custody trail から機械生成）
heartbeat_rule: "chain checkpoint（announce/landing/leg/acceptance）ごとに session_history を更新する"
```

## §7 5 体検証の結果 — 実施後に追記
