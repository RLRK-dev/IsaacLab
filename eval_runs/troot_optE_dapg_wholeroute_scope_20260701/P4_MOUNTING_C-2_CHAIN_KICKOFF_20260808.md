# P4 chunk kickoff — Rs 指示「中間目標を達成せよ」→ C-2 実装 chain 設計起動

desk: p4 RS-TECH-LEAD (w2:p4) / 記録 **2026-08-08 21:01:06 JST**（`date` 実測）/ 本 session = `ae175dcf`
⛔ 本 file は **選定と回付の記録**。code / env / spec / asset の編集は含まない（実装は chain と gate 経由）。
⛔⛔ **引用規則（2026-08-09 00:46 追記・ここに置く理由 = 読み手が最初に着く場所だから）**: 本 file は**追記型**で、⛔ **節番号が 3 組重複している**（`## 9.` / `## 11.` / `## 15.` が各 2 つ・実測）。⇒ ⭐ **引用は「見出しの文字列」で行う**（番号と行番号は**追記のたびに動く／既に一意でない**ので **collation note** としてのみ添える）。⛔ **番号は振り直さない** — 他卓が既に番号で引いており、振り直しは既存の引用を全部壊す（凍結物は編集せず、指す側を直す）。⚠ **原因は message ID の重複と同一**（互いを見ない実行体が、共有されない場所＝記憶から採番した）⇒ **番号は file から導出する**（末尾の最大値 + 1）。

---

## 0. 指示の custody と referent 解決

- **Rs 逐語「中間目標を達成せよ」**（p4 本 session 直接受信・20:5x 台。先行文脈 = p4 の引き継ぎ確認報告「queue 空・生きた状態 4 件・待機」）。
- **referent 解決（解決者 = p4）**: 「中間目標」= **T-ROOT** — Rs 自身の命名（07-27 逐語「最上位に（生産ライン）、その次に現在の目標（中間目標）」）が SSOT に在る: `T-ROOT/state.md:3`「現行の中間目標」/ `T-PRODUCTION-LINE/state.md:28-29` / 前日 item 9 着地 `CLAUDE.md:131`。
- goal と現在 bar = `T-ROOT/state.md:4`「SIM で 5-clip cable routing を vision-based で。現在の bar は rough/imperfect でも SIM で基本動作」（100% は定性・Rs 06-23・SSOT = SOMA:16）。
- **解釈（p4・明示）**: 本指示 = T-ROOT への critical path を**設計済みの chain と gate を通して**前進させる授権。⛔ **含まないと読むもの** = gate 迂回（LEDGER 統治「本優先順位は gate を迂回しない」）・training / two-key / training-ready の解除・04-Specs / 07-Design の編集・§0 premise 変更。これらは従来どおり Rs 専権 / 各 gate。疑義があれば RETURN（p18 protocol）。

## 1. 選定（lead lane = SELECT next task）

**次 chunk = item-7 settle 済 C-2 の実装 chain 起動（設計 phase から）**。

根拠（pointer のみ・数は写さない）:
1. p4 任務 = Rs 裁定 A「43 ステップ表の動作をロボットアームとコントローラで実現・DoD = 腕・ハンド・フィンガを描画した動画」（`00-DESIGN-STATUS-LEDGER.md:40`・robot は UR15 へ supersede 済 `:34`）。
2. その物理 blocker = cell 幾何: 右腕が構造に押し当たって到達しない（LEDGER main 表 t22 行）・built cell (0.220,45°) の L0 は実（`GRID240_READING_20260802.md` §1）。
3. 解 = **C-2**（mounting spread 0.280 / tilt 20°・crown 0.110 不変）— 委任下 settle 済 = `P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` §2（witness = chosen pair で L/R clear・gap +14.7 mm）。
4. chain 定義（同 §2 末尾）: **p11/p5 設計 → p0 実装 → pZ 検証 → p4 まとめ**。昨日までの状態 = 「execution HOLD・self-start 禁止」（`02-Workflow/HANDOFF.md:19`）— 本日の Rs 指示で起動（解釈は §0・gate は不変）。

## 2. [L-TRIAGE]（本 turn の p4 行為のみ）

- 本 turn の変更 = 本記録 file 1 本（eval_runs・非ルール系文書）＋ dispatch 1 通 ⇒ **L=L0**（前例 = 前日の裁定記録 2 artifact と同型）。
- chain 下流は別判定: 設計 = /geometric-design 強制 gate（位置・形状パラメータ）・実装 = env/asset 編集で L2+（rule-check stage1 で確定・diff keyword 自動昇格対象）・検証 = pZ・まとめ = 動画 DoD（motion-bearing ⇒ 視覚レグ必須）。

## 3. [DEFER-RECON]（DDR 照合・SSOT = LEDGER §DDR）

| DDR # | 本 chunk との関係 | blocker か |
|---|---|---|
| #54 部材 298mm 入力未決 | C-2 は **choose-then-re-measure** の条件を負って立つ（settle 済 = DELEGATED §3）。部材の設計・入力 = p5/p11 court + Rs settle | 否（設計入力・並行） |
| #46 自作 clip ≠ 権威実装（リップ 2 枚欠落）＋ script 間 CLIP_H 不一致 | 設計 phase で disposition 必須（reuse-first: `newton_skill_env_base.py:1858-1864` `_v_groove_clip_parts` を第一候補） | 否（設計入力） |
| #57 左腕開始姿勢 = 全候補棄却中の最良 | 設計 phase の入力（C-2 で候補空間が変わる） | 否（設計入力） |
| #58 実把持間隔 75mm vs 指令 88mm（§0#2 主張面 2 つ） | premise 系。設計は現行 §0#2 のまま・変更提案が要るなら STOP→Rs | 否（flag 継承） |
| #45 §0#2 88→176 報告あり on-disk 未着地 | premise 系・Rs 専権。設計は on-disk spec を読む（記憶・報告からでなく） | 否（flag 継承） |
| #40 43-step 表の幾何 stale | 「工程表は幾何を持たない」（p5 訂正済・行冒頭誤り注記）— STEP 系列は生きている | 否 |
| #31 trainer 実在 / driver 不在 | 本 chunk の scope 外（SKILL-DESIGN + WMSO-DESIGN が検討・決定） | 否（別 court） |
| #19 ENV-MULTIWORLD freeze（FOUNDATIONAL） | multi-world **training** の依存。本 chunk（cell 幾何 + scripted route）は非依存 | 否 |

⇒ **FOUNDATIONAL 未解決依存で本 chunk を gate するものは無い**。設計・実装段の各 gate（/geometric-design・prior-art guard・rule-check・pZ 検証・動画 DoD）は chain 内で各 owner が実施。

> ⛔ **訂正/射程付与 2026-08-08 21:20:20（自検出・機構 = p18 m-p18-93 §2 と同一 = 窓外列への不在主張）**: 上表と上行の結論は **240 字窓の truncated 読み**から出しており、**FOUNDATIONAL 列（行末）は長行で窓外**だった。全 DDR 行の行末列を閉じた query（`sed -n '102,167p' | awk` 行末 150 字抽出・本 session 21:17）で実測した結果:
> 1. **design-start を gate する行 = 0 — 原結論は design-start に限り生存**（上表の「否」判定は全て維持）。
> 2. ⚠ **上表が落としていた未解決 FOUNDATIONAL/準同等 行（本 chain の後段レグに収束）**: **#18**（grip-efficacy・route 把持レグへ収束・p5 chain 進行中）/ **#48**（working cell の cable が banked 前提 (RS71 §4 B2) より 1 DOF 多い・disposition = **Rs** ⇒ **DoD 動画の evidence-grade を cap** — 未解消なら受入報告に射程を明記し無印 PASS を出さない）/ **#49**（整定ゲート未到達 ⇒ 以後の数値は動く腕で測られた・probe 数値の evidence-grade・判定 = p11/実装 lane）/ **#61**（env7 版 pin — 版を言う全 evidence の接地に効く・env_isaaclab7 固定）。pin/training 軸の **#2/#4/#12/#19/#26** は本 chunk 非依存（上表結論に変更なし）。**#44** は item 5 で処置済（`ITEM5_RS_RULING_WORKING_ASSET_AUTHORITATIVE_20260808.md` §8）。
> 3. **#46 の精密化（行末 2,200 字を実読）**: p5 の詳細設計（権威実装再利用 vs 自作の是非）は**納品・bank 済** = `P5_UR15_CELL_CONSTANTS_SPEC_20260727.md` @ `459d94bdb4`（banked 272 行版・content sha256 先頭 `81a7d76a7a`）。**#46 の実射程 = cell 定数 21 件（うち物理を変えるもの 10 件）**の齟齬であり clip 1 件ではない。⚠ on-disk 版は 571 行 = banked の 2 倍超（pin/作業版の乖離・row 46 が自ら記録）⇒ **設計は banked 版を content 主で消費**し再導出しない。**run は Rs の gate**（row 46 行末逐語）— §0 の「実行なし」解釈と整合。
> 4. **#57 の精密化**: 左腕開始姿勢は**裁定済（§24）・y 掃引待ち**、上流（clip 配置・役割・取付）= Rs court（row 57 行末）。設計はこの裁定を消費する。
> 5. **#38/#45 の除外根拠の明記 2026-08-08 21:25:57（m-p18-94 3(a) が正しく識別した記録の穴）**: **#45** = 当初表で評価済（flag 継承・否）— 上記 1 の「表の否判定は全て維持」が運ぶ（正しい記述の隣に鏡は書かない）。**#38** = 訂正 pass で評価・除外していたが**記録に落としていなかった**（durable 面では not-seen と区別不能 = 本行が初出。「評価していた」は session 証言等級）。除外根拠: 機種名の spec 反映は row 38 自身が記録（Rs「なおせ」・`460f66e3f5`）・残る spec 面更新 = Rs court・本設計が消費する測定 = **UR15-native の 240 draws のみ**。系論（**#39**・row 39 = owner 未割当）: 設計が動力学定数（H-2/3/4 = τ_bias / Jacobian / damping）を要する場合、**UR5e 由来は接地不可 — UR15 再測が先**（幾何・kinematic clearance のみで閉じる限り非依存）。

## 4. 回付（m-p4-59・w2:p18 経由）

- **owner** = p11（cell / arm-control 設計）+ p5（工程表整合・SKILL 詳細）
- **action** = C-2 mounting 実装設計 spec の作成（/geometric-design 6-step 出力込・#46/#57 disposition 込・#54/#58/#45 flag 継承）
- **受入条件** = banked design doc（p18 経由で p4 へ）→ p0 実装（pathspec 限定）→ pZ 検証 → p4 まとめ（43-step scripted route + 動画 DoD → Rs human-GT）
- **期限** = なし（Rs 指示当日発効・checkpoint 報告のみ）
- **並行して Rs に残る系**（本 chunk の外・p4 は触らない）: WMSO D1.1-C freeze + open-11（p16/p12）・#45 §0#2 着地・#54 部材入力 settle・vision track（PARKED）の起動判断。

## 5. 出所の等級

- Rs 指示 = 直接受信（本 session・relay でない）。referent 解決 = p4（§0 に明示）。
- C-2 settle・chain 定義 = 前日 banked artifact 実読（first-hand）。DDR 行 = LEDGER 実読(truncated cols・行番号は再 grep 前提の pointer)。地図 now-box は 07-18 as-of で stale（P11 WARN と整合）— 本 kickoff は LEDGER + 前日 artifact を正とした。

## 6. 受入判定（p4・2026-08-08 22:03:03 — m-p18-96 routing への回答）

**判定 = ACCEPT（条件付き発進）**。対象 = `P11_MOUNTING_C-2_IMPL_DESIGN_SPEC_20260808.md` @ `3315631007`（273 行・content sha256 `a7c116dfd4982331…4d3b42c7` 全 64 桁一致を 21:32 自測・v2 = 5 体 debate CRITICAL 1 + MAJOR 9 全採択反映済 = spec §11）。

**受入根拠（全文実読・第一手照合）**:
1. **settle との一致**: C-2 (0.280/20°)・crown は導出則廃止の literal 0.110 pin — 「crown 不変」の忠実実装（導出則のままだと spread 0.280 で r=0.140 = 一度も測られていない cell）。再決定なし（spec §0/§1）。
2. **scope 最小**: 4 編集 2 file（eval_runs のみ・`task_config.py`/env source/04-Specs 不触・新 file なし・新 CLI なし）。
3. **flag 継承が完全**: #45/#48/#49/#54（+60 mm **拡大**方向へ訂正済 = 本 file 旧記載 298 の cross-row 誤りも同時に解消）/#57/#58/#61/#39/#18 — 本 file 訂正 2 項の evidence-grade cap（無印 PASS 禁止）を spec §9 DoD が内蔵。数値の第一手検算 = H4 (1.330+0.220=1.550≥1.530)・tilt 変換 (90°−20°=70°)・#54 (0.178/0.118/+60mm)・witness (5/30/+14.7) 全て一致。
4. **gate 充足**: /geometric-design 6-step = spec §3 全出力・5 体 debate 事前実施・prior-art BLOCKER 4 件は逐件 disposition（§8 = C-2 選定の測定 corpus であり失敗経路の再試行でない）・L2 自己申告は保守側で妥当。
5. **検証の判別力**: pZ 12 項（override 回帰・権威 clip guard 生存・existence 再抽選 count 非要求・fallback 行 = 非 evidence の手続バー・cell 条件明記）は「効いた/壊れた」を見分ける形。

**発効・条件**:
- **spec §6-6 run-path fence = 本受入で発効**: C-2 の全 run は `ur15_steps_wired.py` + `ur15_cell_spec.py` の SSOT 直結経路のみ。retired 4 driver + `ur15_steps_c1seat.py` + 独自 cell の video 3 script は不使用。視覚レグ = `render_cell_overview.py` か wired 自身の描画。
- **p0 発進条件 = p5 の工程表整合レグの返答（矛盾なし）**。設計 phase は p11+p5 共同（commission 定義）。p5 の supersession sheet は系譜 bookkeeping で **p0 blocker にはしない**。
- **DoD の evidence-grade cap**（spec §9 のとおり受入時に再確認する）: #48/#18 open の間 DoD 動画へ無印 PASS を出さない・#49 は gate 状態併記・#61 env7 pin 下でのみ・existence 主張は cell 条件（stereo head 不在・#54 部材不在）を明記。
- **spec §6-7 FLAG の登録**: `ur15_steps_wired.py:32` の他 session /tmp path hardcode は **import 時依存**（消えると全 run 不能）。本 spec の diff scope 外につき **別 micro-chunk として起票**（owner p4/p0・repo 内 path 化・**DoD route run 前の実施を推奨**）。

**pin 訂正（本 file §1-1・m-p18-96 spillover・自測 21:33）**: 裁定 A の cite `LEDGER:40` → 正 = **`:39`**・UR15 supersede の cite `:34` → 正 = **`:36`**。⭐ 2 誤りは逆方向 = 挿入 drift ではなく**書いた時点の独立 2 誤記**（p18 の診断に自測で一致・§1 原文は編集しない — 本節が訂正の record）。

## 7. micro-chunk DEFINE — dead-session scratchpad 依存の解消（owner: 設計 = p4 本節 / 実装 = p0 / 検証 = pZ）

**記録 2026-08-08 22:12:10**（`date` 実測・全事実は本 session 22:0x-22:1x の第一手測定）。

**優先度の格上げ（p18 m-p18-97 の論証 + 新実測）**: ⛔ **回収は既に始まっている** — `render_cell_overview.py` の copy 先 dir `…/scratchpad/meshpool/` は **既に削除済**（`ls` 実測 = No such file or directory）⇒ **fence 承認済の視覚レグ script は現時点で壊れている**（`:53` `AS_BUILT.write_bytes` が親 dir 不在で失敗する）。よって本 chunk は「推奨」でなく **pZ 視覚レグ / DoD の前に必須**。

**実測（機構）**:
1. `ur15_steps_wired.py:32` — `S = Path("/tmp/claude-1000/…/b952db35-…/scratchpad")` = **閉鎖済み旧 session の scratchpad**（現 session = ae175dcf・本日 2 卓で session id が roll した実測あり）。
2. S の使用 5 点: **:287 top-level `(S/"_steps_world.xml").write_text(world)` = import 時実行**（:288 で即 compile・dir 不在なら import 自体が落ちる）/ :328 top-level `_steps_cell_full.xml` / :131-132 関数内 `_arm_only_{tag}.xml` / **:3809-3810 `sigma_trace.txt` = run 出力も dead dir 行き**。`S.mkdir` は **0 箇所**（dir 実在に依存）。
3. `render_cell_overview.py:36-39` — 同 dead path 2 本: `SRC = …/_steps_cell_full.xml`（wired の生成物を読む producer→consumer 結線）/ `AS_BUILT = …/meshpool/_as_built_t42.xml`（:53-54 SRC→copy→load）。
4. **mesh 解決の制約**: 生成 XML（flatten 済）は gripper mesh 5 件を**相対名**で参照（`base_mount/base/coupler/driver/follower.stl` — flatten で include 文脈が消え、load 位置基準で解決）+ repo 絶対 path（`ur15_mirror_meshes/*`）。⇒ **meshpool の役割 = 相対 5 件の解決点**（STL 実体を持つ dir から load する仕掛け）。
5. scratchpad root は現存・`_steps_cell_full.xml` = 61,833 bytes・mtime **2026-08-04 15:26**（stale・最終 import 時刻）。`sigma_trace.txt` の programmatic reader = **0**（grep 実測・run log の言及のみ）。fence 外 10 script にも同 dead path が在るが **scope 外**（§6 fence が使用を禁止済・触らない）。

**設計（shape・実装裁量は p0）**:
- `ur15_steps_wired.py`: `S = Path(__file__).resolve().parent / "_gen"` ＋ 最初の write 前に `S.mkdir(exist_ok=True)`。使用 5 点は無変更で追随（S の再定義のみ）。
- `render_cell_overview.py`: `SRC = <wired と同じ _gen>/_steps_cell_full.xml`・`AS_BUILT = <_gen>/meshpool/_as_built_t42.xml` とし、**gripper STL 5 件が解決すること**を成立条件とする（例: script 起動時に repo assets（`GRIP_XML` 同梱 mesh）から `_gen/meshpool/` へ copy。手段は p0 裁量・**新 file を repo に track しない**〔生成物は untracked の `_gen/` 内〕）。
- ⛔ しないこと: 挙動・出力形式の変更 / fence 外 script への波及 / 新 env var・新 CLI / C-2 4 編集との同居 commit（**file 重複なし**: 本件 = wired+render / C-2 = cell_spec+sweep ⇒ **並行可・p5 整合レグとも独立** — p0 は C-2 発進待ちの間に本件を先行してよい）。
- L-TRIAGE: 2 file・~10 行・repo 追跡の新 file なし ⇒ **L1**（DoD = 本節 + pZ 項・検証 = pZ 独立）。

**pZ 受入項（本件分・spec §7 の 12 項に追加）**:
(i) 2 script に `/tmp/claude` 参照 0。⛔ **query の実施場所を指定する（本項の初版は場所を書かず、偽ゼロを許す形だった — 訂正 22:38・機構 = p18 §1191/§1195 点 6）**: **worktree の中へ `cd` して `git grep` を走らせる**（worktree 内では tracked file に効く）。⛔ **repo root から `.claude/worktrees/…` を検索しない** — その path は `.gitignore:101` で untracked ゆえ `git grep` に見えず、wrapper 側も root からは `.claude/` へ降りない（**両経路の盲点の交差**・p18 実測）⇒ **0 件が「無い」と読めない**。root から見るなら `command grep -r` に**明示 path** を与える。⚠ 併せて **rc を印字**する（存在しない実装に飛んだ command は空 stdout + rc=127 を返し、無 hit と区別できない・p18 実測）。(ii) wired import が旧 path 不在前提で成功し生成物が `_gen/` に出る（旧 dir を消さずに検証するなら: 参照 0 ＋ `_gen/` への出力実在で足りる）。(iii) `render_cell_overview.py` が C-2 cell の絵を出す（**視覚レグ復旧の実証**）。(iv) 旧 path を読む consumer 0（sigma_trace reader 0 は実測済・render の SRC 付替えで最後の consumer が消える）。(v) pathspec 限定 commit・C-2 編集と分離。

> ⛔ **§7 の scope 訂正 2026-08-08 22:24:59（自検出・機構は本日 3 度目 = 自分の表示上限が数を切った）**: 上記実測 5 の「fence 外 10 script」は **11 file と書くべきところを自分の `head -12` が 12 行で切った結果**（240 字窓 → `head -12`・同型 3 度目）。**git grep（tracked file 全数・ignore 規則の影響を受けない）で再測 = `.py` 13 file / 14 行**（p0 の独立実測と一致）。**うち 3 file / 4 行は `S` 束縛でない** — `render_cell_overview.py:36`(AS_BUILT)/`:38`(SRC)・`probe_crown_band_occupancy.py:41`(SRC)・`probe_home_pose_symmetry.py:41`(AS_BUILT) ⇒ ⛔ **`S = Path(` を grep する fix はこの 3 file を落とす**（本 §7 設計は wired + render を名指しているので 2 file は covered・**probe 2 本は下記の扱い**）。全 tracked = 24 file / 60 行（残りは log・run trace・urdf = 記録ゆえ不触）。
> - **chunk scope の確定**: 本 chunk = **wired + render の 2 file のみ**（fence 承認の run 経路・DoD 前に要る）。⚠ **残る 11 file（retired driver 群 + probe 2 本）は「壊れている」と明記して据置** — ⛔ **これらの沈黙を「走れる」と読まない**（probe を再走させるなら同じ fix が先。`CROWN_BAND_READING` / `HOME_POSE_SYMMETRY` の再現には本件が前提）。
> - ⛔ **訂正の訂正 2026-08-08 22:29:5x（p4 第一手 `git grep`・挿入のみ・chunk scope と裁定は不変）**: 直上 2 行は **数が query に対して正しく、語と構成が誤り**。
>   1. **「全 tracked = 24 file / 60 行」の「全」が誤り**。24/60 は **`.md` を除いた tracked**（py 13 + txt 9 + log 1 + urdf 1）の数で、**3 revision で不変**（HEAD / `e74af451ed` / `aa5f0a673a` = 同値 ⇒ revision 差ではない）。**全 tracked は HEAD で 30 file / 76 行**。差の 6 = `.md` で、**本調査自身の記録**（本 file / `P0_SCRATCH_PATH_SCOPE_…` / `P18_…LEDGER` / `ITEM5_…` / `P11_…ADDENDUM_A` / `RS71-System-Spec-SSOT`）。⇒ 計器は健全・**label が射程を広げた**（本日の同族）。
>   2. **「retired driver 群 + probe 2 本」= 構成が不正確**。out-of-scope 11 の実測内訳 = **§6-6 fence が名指す 7**（`ur15_cell` / `ur15_route` / `ur15_steps` / `ur15_steps_reaim` / `ur15_steps_c1seat` / `ur15_yoke_video` / `ur15_final_video`）＋ **fence が名指さない 4**（`ur15_grip_video` / `probe_handedness` / `probe_crown_band_occupancy` / `probe_home_pose_symmetry`）。probe は **2 本でなく 3 本**。
>   3. ⇒ ⛔ **実測 5 の「§6 fence が使用を禁止済」は 11 中 7 にしか当たらない**。残る 4 が scope 外なのは **C-2 の run path に無いから**であって fence のためではない — **fence は「走らせない」ことを保証しない**。この 4 file を止めているのは**壊れていること自体だけ**であり、うち `probe_crown_band_occupancy` / `probe_home_pose_symmetry` は C-2 選定 corpus の読み（`CROWN_BAND_READING` / `HOME_POSE_SYMMETRY`）を産んだ計器 ⇒ **再現を試みる者は本 §7 の fix を先に要する**。
> - ⭐ **母集団の明記（訂正の訂正 22:38・p18 §1192 の amend「不在主張は covered した母集団を書く」を自分に適用）**: 上記 13 file / 14 行は **`b952db35` = 本 chunk が直す dead session の集合**。⚠ **query を `Path("/tmp/claude-1000`（session を問わない）に広げると repo 全体で 15 file / 16 行**（自測）— 増える 2 件は**別 arc・別の形**ゆえ本 chunk 外だが、沈黙を可用性と読ませないため名指す: `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/splice_v231.py:5`（**別 session `b0da55e6` の scratchpad** = 同型・p5 arc）/ `w1_b2_dod_legs/leg8_hold_calibration.py:118`（`/tmp/claude-1000/leg8_…npz` = **session 配下ですらない共有 /tmp** = 別型・寿命は同じく無保証）。⇒ **私の 14 と p18 の 11 と 15/16 は同一対象の 3 つの query**（対立ではない・本日 4 度目の same-object-different-cut）。
> - **URDF provenance の喪失（p18 m-p18-102 経由・p4 が第一手で確認 22:24）**: `ur15_mj.urdf:3` = 「autogenerated by xacro from …/b952db35-…/scratchpad/urdf_work/ur.urdf.xacro」・**`urdf_work/` は既に不在**（`ls` 実測）。消費者 = `ur15_cell_spec.py:99-100` の `EFFORT`/`LIMS`（URDF の `<limit>` を parse）。⭐ **射程を正確に**: URDF は tracked ゆえ **値は生存**・失われたのは **再生成と source 監査の経路**（値の誤りは主張しない）。⛔ **本 chunk では回復不能**（xacro は消えている）— 記録が処置。⇒ **DDR 登録を p6 へ依頼**（p18 経由・register 維持 = PLAN-KEEPER）。

**evidence 保全（p4 実施済・claim なし）**: 旧 scratchpad の `_steps_cell_full.xml`（唯一の as-built snapshot・削除リスク下）を repo へ rescue copy = `p4_ur15_sim_20260727/asbuilt_snapshots/_steps_cell_full_asof_20260804_152626.xml`（cp -p・mtime 保全 2026-08-04 15:26:33・61,833 bytes・sha256 `28c242410314b199042acd0349a00e5937ccb08dbcd53e336a13a0fa8b944cab`）。⚠ **本 copy が「どの run を back するか」は無主張**（mtime = 最終 import 時刻という事実のみ。banked 測定との対応は content 照合してから言う）。

## 8. working method 裁定（p4 court・m-p18-100 (2) への回答・2026-08-08 22:24:59）

**裁定 = p18 推奨を採る = 実装は非 lane branch へ commit し、pZ は commit を検証する**（共有 tree の未 commit 面を渡さない）。対象 = **C-2 実装 chunk と §7 micro-chunk の両方**（同じ価格が同じ形でかかる）。

**根拠**: pZ の verdict は DoD evidence chain の土台に入る。共有 tree で取った verdict は **どの commit からも再現できない**（p18 §1188/§1189 = tracked deletion 1 件が現存し、HEAD の checkout は本 tree と必ず異なる ⇒ 再現する checkout が存在しない）。代価は **worktree 1 つと commit 1 本**、対価は **verdict の恒久的な格下げの回避**。⭐ **今日が安い**: 実装対象 4 file（`ur15_cell_spec.py` / `sweep_mounting.py` / `ur15_steps_wired.py` / `render_cell_overview.py`）は **本 turn 実測で 4 本とも clean** ⇒ branch は他卓の WIP を巻き込まない。dirty になってからでは同じ値段では買えない。

**機構（p0 への具体指示 — 「非 lane branch へ commit」は共有 tree では自明でないので形を決める）**:
1. ⛔ **共有 tree の branch を切り替えない**（`git switch` は全 pane の足元を動かす）。
2. **worktree を使う**: `git worktree add --detach <path> HEAD` → そこで編集 → `git switch -c impl/c2-mounting-20260808` → **pathspec 限定 + `--no-verify`** で commit。⭐ **worktree の置き場は `.claude/worktrees/c2-impl-20260808`**（repo 内・git 管理外・既存 4 worktree と同じ場所）— ⛔ **session scratchpad に置かない**（本 chunk が直している当のもの。/tmp の worktree が 6 本 prunable で残っているのが実例）。
3. **pZ へ渡すもの = branch 名 + commit sha + 変更 file ごとの content sha256**（説明文でなく物）。pZ は自分の fresh detached worktree で検証（brief `:39` の「commit or files」を満たす）。
4. **landing = pZ verdict の後**、同一 content を lane（`rlrk/optE-s2-substrate-swap`）へ pathspec 限定で commit。⭐ **受入条件 = landed content sha == verified content sha**（p4 が consolidation で照合。freeze→verify→bank the exact sha）。⇒ 「検証した物」と「着地した物」が同一であることが機械証明になる。
5. 完了後 `git worktree remove`（prunable を増やさない）。

**この裁定が変えないもの**: 実行順序（p0 実装 → pZ 検証 → land・p18 m-p18-99 で settled）／p0 の発進条件（p5 の工程表整合レグ）／HOLD／DoD の evidence-grade cap／spec §6-6 fence。**pZ の出力規律**（未 commit 面上の verdict は label 必須）は p18 の court で binding のまま — 本裁定はその label が要らない経路を選ぶだけ。

> ⛔ **時刻訂正 2026-08-08 22:10:09（v5・挿入のみ・判定/数値/sha は全て不変）**: 上の「21:32 自測」「自測 21:33」は**書いた時点で誤りの時刻** — 測定対象の spec v2 は 21:50:11 起草・bank commit `3315631007` は **21:55:49**（`git show -s` 実測）ゆえ、21:32 に banked sha は測れない。実際の測定 = 本 session transcript の tool 時刻 **22:00:26–22:02:28**（sha 照合・裁定 A/UR15 行の再測）＋ 独立再測 **22:05:47**。v4 の pin `5ddf8f50c975a744…f81b115b` は v4 を指し続ける（pin は版を指す・rename の先例と同形）。

## 9. 別紙 A の受入判定（p4 court・2026-08-08 22:31:5x）

**判定 = ACCEPT**。対象 = `P11_MOUNTING_C-2_SPEC_ADDENDUM_A_URDF_AND_LANDING_20260808.md` @ `88130a537e`（全文実読）。⭐ 受入済 spec `3315631007` の content sha `a7c116df…4d3b42c7` は**不変**（別紙は本体を編集しない = Rs 07-21 の凍結形式）— 私の受入 `e39526fe58` はそのまま生きる。

1. **A-1 受入 ⇒ 受入条件の cell 条件を 2 つから 3 つへ**: existence 主張の射程 = ①stereo head 不在 ②#54 部材不在 ③**抽選領域 = `ur15_mj.urdf` の関節範囲**（`ur15_steps_wired.py:1972` の一様抽選が `LIM` で領域を決める）。pZ 項は 13 項（別紙 A-4）。⭐ **これは cap の強化であって witness の否定ではない** — 「運動学量ゆえ整定非依存」（spec §5b-1）は真のまま・「URDF 非依存」ではなかった、という射程の追加。
2. **A-3 受入 ⇒ 私の §8 の言い方を弱める（実質は不変）**: spec `:201` §6-4 が固定しているのは**着地先（lane）**であって中間 commit 先でも順序でもない（括弧書きが `probe/pd1-arm-pd` との**branch 帰属**の対比を述べており、p11 の読みが本文に忠実）。⇒ ⛔ **§8 で「spec §6-4 を手続として修正する」と書いたのは必要より強い主張**だった（矛盾は無く、解釈で足りた）。裁定の実質 = 非 lane branch → pZ 検証 → lane 着地、は**不変**。〔本日 p18 §1189 と同型 = 結論は正しく、premise を盛った〕
3. **A-2 受入 ⇒ p6 への DDR 依頼を狭い形へ差し替え**: §7 の URDF bullet は p18 便に接地して「再生成も source 監査も不能」と書いたが、p11 の第一手監査 = **公式 description が on-disk に在り（`…/Universal_Robots_ROS2_Description/`）、腕 6 関節の `<limit>` は公式 `joint_limits.yaml` を厳密に再現**（audit CLEAN）。⇒ **DDR に載せるのは「provenance 喪失」ではなく次の 4 点**: (i) 消えたのは **/tmp の作業複製**（公式上流は在る）(ii) **腕 `<limit>` 6 行は公式照合済 = CLEAN** (iii) **未監査 = URDF の他の内容**（mesh 参照・慣性・link 幾何）(iv) **恒久錨 = content pin `b4c60d4d…b57d`**。⛔ **私の元の依頼文（強い形）は本節で SUPERSEDED** — p6 が未着地なら本節の形で起票（着地済みなら本節を訂正の根拠に）。
4. **変わらないもの**: C-2 の決定入力（0.280/20°/crown 0.110 pin）・chain 順序・p0 発進条件（p5 の工程表整合レグ）・HOLD・§6-6 fence・DoD の evidence-grade cap・#39 STOP tripwire（別軸・本紙は動力学定数に触れない）。

## 9. ⛔ DoD 射程の訂正と、中間目標までの実距離（p4 自測 2026-08-08 23:12:07・実行なし・静的読みのみ）

⛔ **私の §6 と p11 spec（§0 `:13` / §9）が書く「chain DoD = 43-step scripted route 動画」は、本 chain の実装範囲では produce できない。** 裁定 A（`LEDGER:39`）は **p4 の任務定義（mission）**であって本 chunk の DoD ではない — 私はその 2 つを 1 文に畳んでいた。⇒ **本 chunk の DoD = 実装済みの route が C-2 cell で走る動画**（下記 18 段）。

**実測（全て tracked file の静的読み・`git grep`/`awk`・rc 印字済）**:

| 面 | 実測 | 出所 |
|---|---|---|
| canonical 表の段数 | **1–43**（番号付き 42 行・最大 43） | `eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md` |
| canonical 18 | 「**C2から上昇**」・clip 欄 = **C1,C2** | 同上 |
| canonical 43 | 「**ホーム復帰(両手全開)**」・clip 欄 = **C1-C5**（5 clip 全 seated retained） | 同上 |
| fence 承認 driver の実装 | **STEP 1**（開始姿勢へサーボ移動 `:2509`）＋ **STEP 表 2-18**（17 行 `:2639-`）= **計 18 段**・終端 = step 18「上昇」 | `ur15_steps_wired.py` |
| live cell の clip 定義 | ⭐ **C1 と C2 の 2 個のみ** | `ur15_cell_spec.py:485-486` |
| C3/C4/C5 に触れる .py | **retired driver 3 本のみ**（`ur15_steps.py` / `ur15_steps_c1seat.py` / `ur15_steps_reaim.py`）= **§6-6 fence が使用禁止にした側** | `git grep -l` |

⇒ **driver は canonical 1–18 を、段の名前まで一致する形で実装している**（18 = 「C2から上昇」で両者一致）。⇒ ⭐ **本 chain が届く範囲 = 5 clip 中 2 clip（C1→C2）**。

**中間目標（T-ROOT = 5-clip routing）までの実距離（測れた分・推測しない）**:
1. **段**: 19–43 の **25 段が未実装**（内容 = C3/C4/C5 への配索 ＋ ホーム復帰）。
2. ⭐ **cell**: 走る cell に **C3/C4/C5 が存在しない**（定数が 2 個）⇒ 残りは「段を書き足す」ではなく **cell を作り直す**側の作業。⛔ **これは本 chunk の scope 外**（C-2 は取付幾何の chunk）。
3. **既知の carry と整合**: 地図の「**5-clip 配置を実際に構成し FK で検算した witness は まだ誰も作っていない**」（W-1 carry）と本実測は同じ穴を別角度から指している — 私は今回 **executable path 側**で測った。

**帰結（p4 の court で決めること・決めたこと）**:
- 本 chunk の受入報告は「**C1→C2（canonical 1–18）が C-2 cell で走ることを示す動画**」で閉じる。⛔ **これを「43-step 完了」「裁定 A 充足」と書かない**（#48/#18/#49/#61 の grade cap は従前どおり別に効く）。
- **裁定 A の充足には 19–43 と 5-clip cell が要る** ⇒ **別 chunk として起票が要る**（規模は本 chunk と桁が違う。起票の可否・順序は Rs / 私の lane で別途）。
- p11 spec の同文言（§0 `:13`・§9）は **p11 の doc** ゆえ私は編集しない — **本節を回付**して p11 の court に置く（内容の誤りではなく **射程の畳み込み**であり、spec の技術内容は無変更で足りる）。

> ⛔⛔ **§9 の訂正 2026-08-08 23:17:24（自検出・本日 4 度目の同型 = 自分の `head -10` が一覧を切った）**: 上表最終行「C3/C4/C5 に触れる .py = **retired driver 3 本のみ**」は**偽**。⛔ **私の query は `| head -10` で切れており、実数は 31 file**（同 query を切らずに再走・rc=0 印字）。⚠ **この誤りは Rs への報告にも乗った**（同 turn で訂正済）。
>
> **切れていた側に在ったもの（第一手・docstring 逐語）**:
> - `thread_isaac_lab/skills/step_table.py` — 自称「**43-STEP routing table — maps each STEP to its skill and parameters**」・出所 = `RL-Routing-Design.md §2.3`・**C1〜C5 を参照**
> - `thread_isaac_lab/scripts/dry_run_39step.py` — 「full **39-step** cable routing sequence の dry-run IK 検証 + per-camera MP4」
> - `thread_isaac_lab/scripts/wet_run_full_sequence.py` — 「Execute full **43-step** routing sequence **in Newton VBD** with video」
> - 他に route stack（`route_executor.py` / `routing_orchestrator.py` / `route_env_config.py` / `test_newton_clip_routing.py` 等）
>
> ⭐ **訂正後の正しい絵（結論は変わらないが、理由が変わる）**:
> 1. **5-clip の材料は「無い」のではなく「別 substrate に在る」** — 全系列 script が名指す実行基盤は **Newton VBD** で、これは **DISCARDED track**（`CLAUDE.md` Newton VBD 節: env6-VBD は「DISCARDED → mujoco 基盤」）。⇒ **現行 substrate（UR15 mujoco）で走る 5-clip の実装は依然として無い**（cell が 2 clip = `ur15_cell_spec.py:485-486`・driver が 18 段）。
> 2. ⇒ **残作業は「全部を新規に作る」でも「段を書き足すだけ」でもなく、*設計・表・waypoint は既存、実行面は現 substrate へ作り直し*** という中間形。**規模の見積りは本節では出さない**（測っていない）。
> 3. ⚠ **clip 座標系も別物**: `task_config.py:211-217` の 5 clip は `(0.35/0.40, ±0.150…)` の千鳥、UR15 cell は `C1=(0.150, …)` `C2=(0.040, …)`（`ur15_cell_spec.py:485-486`）⇒ **同じ名前 C1/C2 が別の座標を指している** ⛔ 両者の数を突き合わせる時は必ず substrate を添える。
>
> ⭐ **私の欠陥の形（4 度目・同一）**: 240 字窓 → `head -12` → `head -10`。⛔ **「一覧を出して散文にする」経路が毎回切れる。** ⇒ 規律 = **一覧を数える／不在を言う query に `head` を付けない**（付けたら「これは切った表示であって集合ではない」と同じ行に書く）。

> ⭐ **§9 の精密化 2026-08-08 23:30（p6 発見・p18 経由 → p4 が第一手で確認）— 「witness 不在」は 3 脚に割れており、私の測定はその 1 脚**:
> - **実測（LEDGER `:78` を直読・行長 31,288 の内側）**: 逐語「✅**W-1 = WITNESS FOUND (2026-07-14、p5 作 `shared/GEOM_WITNESS_5CLIP_p5_20260714.py` 6/6 PASS、p6 が task_config から独立検算 + source 直読で確認)** — ⚠**ただし L-geom (幾何) のみ。L-phys / L-exec は未確立**」。artifact 実在 = 7,418 bytes・Jul 14 06:05（`ls` 実測）。
> - ⇒ ⛔ **私が §9 で引いた「地図の W-1 carry（5-clip witness 不在）」は射程が広すぎた**。正しくは **3 脚**: **L-geom = witness 済（6/6・07-14）／ L-phys = 未確立 ／ L-exec = 未確立**。⭐ **本 §9 の測定（実行可能経路が 2/5 clip）は L-exec の脚そのもの**であり、L-geom を否定しない。⇒ 「同じ穴を別角度から」ではなく **別の脚を測った**が正しい。
> - ⚠ **面の不一致を報告する（⛔ 解決しない — surface は p6・scoping は Rs）**: LEDGER `:78`（07-14）は幾何 witness を FOUND と書き、地図 `docs/logical_decomposition.html:174`（now-box header = 07-18 as-of = **4 日新しい**）は「5-clip 配置を実際に構成し FK で検算した witness は まだ誰も作っていない」と書く。⛔ **原因は付けない**（述語が狭い可能性と、面が stale の可能性の両方が立つ）。
> - ⇒ **p6 への請求（本 file §9 の 1 行掲載依頼）を 3 項に改める**: ①**L-geom = witness 済**（07-14・artifact 付き）②**実行可能経路の到達 = 5 clip 中 2**（本 §9 の導出）③**L-phys / L-exec = 未確立**。⛔ 2 項に畳むと、LEDGER が 1 文かけて分けたものを潰す。

> ⛔⛔ **§9 の再訂正 2026-08-08 23:34（発見 = pZ / 撤回 = p18 / p4 が第一手で全数確認）— 2 点とも私の記述が誤り**:
> 1. ⛔ **「面の不一致」は不一致ではない（前段落の記述を撤回）**。witness script を直読: **FK 系 token = 0（rc=1）**・冒頭 SCOPE 逐語「A PASS here establishes **L-geom only** … It does NOT establish **L-phys** … nor **L-exec**」。⇒ 地図 `:174` の述語は「**構成し FK で検算した** witness」で、この artifact はそれを**満たさない** ⇒ **地図の「まだ誰も作っていない」は書かれたとおり真**・LEDGER `:78` の「WITNESS FOUND（L-geom のみ）」も真。**別の述語についての 2 つの真**であって矛盾ではない。⛔ **地図を直させてはならない**（真の文を消すことになる）。
> 2. ⛔⛔ **witness は「別の配置」で計算されている ⇒ 私の term (1) は無条件では書けない**。実測: 同 script の参照 = **`task_config` 5 件（rc=0）／`ur15_cell_spec` 0 件（rc=1）**・clip の記述逐語「**C1..C5 staggered, odd X=0.35 / even X=0.40, Y pitch 75 mm**」= **task_config 配置**（0.35/0.40 が **X** に立つ側）。⇒ ⭐ **L-geom witness が成立しているのは task_config 配置についてであって、p0 が実装しようとしている UR15 C-2 cell についてではない**（同名 C1/C2 が別座標 = 本 file の substrate 注意そのもの）。⇒ ⛔ **私自身の条件 (iv)（clip 名には必ず substrate を添える）を、私は自分の term (1) に当てていなかった。**
> ⇒ **term (1) の改定形**: 「**L-geom witness DONE — ただし `task_config` 配置について（2026-07-14・6/6 PASS）。UR15 C-2 cell 配置についての L-geom は未確立**」。⇒ ⭐ **帰結（本 chunk の絵の精密化）**: C-2 cell については **L-geom / L-phys / L-exec の 3 脚とも未確立**であり、本 §9 が測ったのは **L-exec の到達（2/5）**のみ。

## 10. 統治集合の pin と、URDF provenance 主張の縮小（p4・2026-08-08 23:53）

**(a) 統治集合（consolidation で私が照合する対象を確定させる）**:
- **設計 = `P11_MOUNTING_C-2_IMPL_DESIGN_SPEC_20260808.md` @ `3315631007`（273 行）** — §6 の ACCEPT はこの版に対する。
- **別紙 A = `P11_MOUNTING_C-2_SPEC_ADDENDUM_A_URDF_AND_LANDING_20260808.md` @ `5a7fa99b61`（164 行・content sha256 `f1a764e84c9c5dc8…cb3f402a`）** — 実読の結果 **設計 4 編集（定数 3 + label 2 行）を 1 つも変更しない**（検証計器の差替・射程の限定・解釈の固定・p11 自身の DoD 畳み込み訂正）⇒ ⭐ **再受入は要らないが、統治集合として pin する**（pZ が何に対して検証したかを consolidation で言えるようにするため）。⚠ **別紙は追記され続ける** ⇒ 引用時は content で持ち、版を添える。
- ⭐ **A-3 が私の §8 との衝突を解いている**: spec `:201` §6-4「本 branch 上で行う」が固定するのは **最終 lane** であって中間 commit 先ではない ⇒ **worktree 上の非 lane branch で実装 →(pZ 検証)→ lane へ着地**は spec と矛盾しない（commit 規律 = pathspec 限定 + `--no-verify` は中間でも lane でも同じ）。
- ⭐ **A-1 の射程限定を受入条件に取り込む**: 開始姿勢の witness（L clear 5 / R clear 30 @ 240 draws）は **URDF の関節範囲を抽選領域として**得られた existence（`ur15_steps_wired.py:1972` が `LIM` から一様抽選）⇒ 受入報告では **「URDF 関節範囲上の existence」**と書く。

**(b) ⛔ 私の URDF provenance 主張を縮小する（§7 の記述が強すぎた）**: 私は「生成元 xacro は消滅・**本 chunk では回復不能**ゆえ記録が処置」と書いた。**A-2（p11）を受けて p4 が第一手で確認**:
- **公式 description は on-disk に実在** — `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description/` に **同名 `urdf/ur.urdf.xacro` と `config/ur15/joint_limits.yaml` の両方**（`ls` 実測）。
- **値の突き合わせ（p4 自測）**: 公式 `joint_limits.yaml` の `max_effort` = shoulder_pan 433.0 / shoulder_lift 433.0 / elbow 204.0、`ur15_mj.urdf` の distinct effort = **433.0 / 204.0 / 70.0** ⇒ 一致（wrist 3 本 = 70.0）。
- ⇒ ⭐ **消えたのは `/tmp` の作業複製であって上流ではない。「監査できない」は偽** — 公式値との照合は今日できたし、実際に一致した。⛔ **縮小後も残る穴（一般化しない）**: 消えた作業複製が公式 xacro と byte 一致だったかは原理的に確かめられない ⇒ **恒久の錨は content pin**（URDF は tracked・commit から再現できる）。
- ⇒ **micro-chunk（§7）の優先度根拠は「provenance 喪失」から降りる**が、chunk 自体は不変で残る（理由 = ①視覚レグ script の copy 先 dir が既に削除済 ②生成物と `sigma_trace` が回収対象の dir に出る）。

> ⚠ **§10(a) の pin 運用の訂正 2026-08-08 23:56（自検出・書いた 4 分後に自分の caveat に当たった）**: 私は「別紙は追記され続ける」と書いた直後に **版で pin した**（`5a7fa99b61`）。実測すると別紙の HEAD は既に `b30d41d8db`（23:52:37）で、**私の pin は書いた時点で 1 世代遅れていた**。⇒ ⭐ **追記型 doc は版で pin しない — 「HEAD を読む」＋ 受入判定の条件（設計 4 編集の値を変えていないこと）を書く**。差分実測 = `5a7fa99b61`→`b30d41d8db` は **+11/−0 = A-9b（計器の数え方の注記・pZ 提案）**・**設計値 hit 0** ⇒ 受入は不変。同じ訂正を vault `02-Workflow/HANDOFF.md:5` にも適用（旧記載は**作成時の版**を指しており 3 世代 stale だった）。

> ⚠ **pZ 検証への注意 2026-08-09 00:10（p18 §1222 点 4 の自己適用）— 本 file 自身が hit 源になった**: 本 chunk を調べた過程で、**dead-session token（`b952db35`）が私の記録・p18 台帳・p11 別紙にも書かれた** ⇒ ⛔ **repo 全体で「参照 0」を測ると、code でなく *調査記録* に当たって「まだ残っている」と読める**。⇒ **§7 の pZ 項目 (i) の scope（`ur15_steps_wired.py` と `render_cell_overview.py` の 2 file）を広げない**。広げるなら **path を population として明示**し、`*.md` を除く（今日の「不在主張は covered した母集団を書く」の、自分の artifact が汚染源になった版）。

> ⭐ **上の注意の精密化 2026-08-09 00:12（p18 §1223・p4 が自分で検算）— 「`*.md` を除く」は必要だが十分でない。効く軸は 3 つ**:
> - **実測（token 形で hit が変わる）**: tracked `*.md` — **full uuid = 1 / 8 文字 prefix = 6**。tracked `*.py` — **どちらの形でも 13**（code は必ず full path を持つので形の差が出ない）。
> - ⇒ ⭐ **調査記録は prefix 形で書かれ、code は full 形しか持たない**（6 卓が独立に「読みやすいから」prefix を書いた結果）。⇒ **prefix で測ると汚染され、full uuid で測ると clean**。
> - ⇒ **不在 query に述べるべきは 3 つ**: ①**path（母集団）** ②**数え方（行か出現か）** ③⭐**token の形**。⛔ ②③ を書かずに数だけ出すと、同じ file・同じ日に**違う数**が出る（本日 7 回目の同型）。

> ⭐ **上記注意の第三項（2026-08-09 00:12・p18 §1223 の実測を自分で再現）— 範囲だけでなく「token の形」も書く**: **コードは 36 文字の完全形**（実体は `ur15_steps_wired.py:32` に在る・ここには**転記しない** — 転記が clean query を壊すのは本 file 下段の実測どおり）／**記録は 8 文字の短縮形**（本 file は完全形 0・短縮形 2）。⇒ **同じ対象なのに、tracked `.md` は短縮形で 6 file・完全形で 1 file** = **query の形が汚染量を決める**。⛔ **pZ 検査 (i) を wired + render の 2 file の外へ広げる場合は、①path（母集団）②数え方（行か出現か）③token の形（完全形か短縮形か）の 3 つを書く** — どれか 1 つ欠けると、同じ file 群で違う数が出て「回帰」と読まれる。⚠ 2 file 限定の現行 (i) はこの影響を受けない（path 制限が形の差を吸収する）。

## 11. 版の裁定（pZ の PZ-114 への回答・p4 court・2026-08-09 00:12:59）

**決定 = pZ は「実行時点の HEAD」で item 14 を走らせる。受入版（`5a7fa99b61`）では走らせない。**

**根拠（p4 が第一手で実測・relay で決めない）**:
- 差分 `5a7fa99b61` → `b8b80cbf32` = **+27 / −0（削除 0）**。追加は **A-9b（数値の隣に pattern と数え方を置く）** と **A-9c（境界を 1 語ずつでなく名前空間の全数分類で決める）** の 2 節のみ。
- **設計 4 編集の値（0.28 / TILT 20 / 0.110 / 1.440）が追加行に出る回数 = 0** ⇒ 設計は不変。
- **`PEDESTAL` 出現 = 受入版 0 / 現行 2** ⇒ ⭐ **受入版は、検査して見つかった穴（語が両リストから漏れる）が塞がっていない版**。それで走らせるのは「既知の穴を持つ計器で検証する」ことになる。
- ⇒ **本決定は §10 で既に landed した規則の適用**（別紙は**設計 4 編集の値を変えない限り再受入不要**）であって、新しい例外ではない。⭐ §10 の訂正（**追記型 doc は版で pin せず HEAD を読む**）とも同じ向き。

**pZ への条件（run 記録に 4 つを書く）**: ① **走らせた版の pin**（commit ＋ content sha256・実行時点で自分で測る。参考: 本裁定時点の HEAD = `b8b80cbf32` / `e5dd839672ae7692…cab9a1148c` / 191 行）② **pattern** ③ **数え方（行か出現か）** ④ ⭐ **token の形**（§10 の訂正と本 file の 3 軸注記）。⇒ 後日 再走したときの「食い違い」が、退行なのか定義の違いなのかを判別できるようにする。

**射程（⛔ 広げない）**: 本裁定は **検証計器（別紙）の版**についてのみ。**設計 = spec `3315631007`（273 行）が受入対象であることは不変**で、別紙が設計値に触れた瞬間に本裁定は失効し再受入が要る。

## 11. 再受入の裁定（p4 court・2026-08-09 00:13 — pZ の PZ-114「どの版を走らせるか」への回答）

**判定 = 受入対象を別紙 A の *現行 content* へ拡張する**（pZ は**現行版**で item 14 を走らせる）。

**pin（content 主・版は照合注記）**: content sha256 **`e5dd839672ae7692…`**（191 行）＝ 本裁定時点で `b8b80cbf32`（= 当該 file の HEAD・本 turn 実測）。⚠ **file でなく content を受入れている** — 別紙は追記型（本日 11 世代）ゆえ、**本裁定は以後の追記へ自動延長しない**。

**根拠（全て本 turn の第一手実測）**:
1. **delta = `+27 / −0`**（受入版 `5a7fa99b61`・164 行・sha `f1a764e84c9c5dc8…` → 現行）。**行の削除 0 ⇒ 文字削除は不可能**（本日確立の片側結論則）。
2. **設計値の混入 = 0**（追加行に `0.28` / `0.110` / `1.440` / tilt 20 は 1 件も無い）⇒ **私の設計受入（spec `3315631007`）は微動もしない**。delta 3 件は全て**計器の修理**（pattern と数え方を数の傍に記録 / namespace 分類で語の取りこぼしを塞ぐ / 引用規約を冒頭へ）。
3. **修理は現行版にしか無い**（`PEDESTAL` = 受入版 0 / 現行 2・namespace 分類も現行のみ）。⛔ **受入版を走らせることは、穴が既知の計器を走らせること** — 「バグの下で緑になった gate はバグに検証されている」に該当する。

**pZ への条件**: run 記録に **①本 content pin ②検索 pattern ③数え方（行か出現か）④token の形**（完全形 / 短縮形・§10 末尾の注意）の 4 つを書く。⚠ **走る前に別紙がさらに伸びていたら、走らせた版を名指すこと** — 同型なら（`+N/−0` かつ設計値 0）私が同じ形で再受入する（安い）。

**変えないもの**: 設計受入（spec `3315631007`）・chain 順序・p0 の発進条件（p5 のレグ）・HOLD・fence・DoD の evidence-grade cap。

> ⭐ **§11 の条件欄を 4 軸に整える 2026-08-09 00:14（pZ 提案・p18 §1225 が分離を確定）**: 私は「pattern」と「token の形」を並べたが、**独立な軸は 4 つ**で、今夜それぞれが**同じ file に違う数**を出した — ①**token 文字列**（full uuid 1 / 8 文字 prefix 6・tracked `*.md`）②**pattern 構文**（`TILT` 8 / `\bTILT` 7 / `\bTILT\b` 4）③**path 母集団**（作業ツリー / wrapper / `git grep HEAD` / 全履歴）④**数え方**（行 13 / 出現 31）。⇒ **run 記録は「版 pin ＋ この 4 つ」**を書く。⭐ **本件では full uuid を使うと ① と ③ が同時に片づく** — code は必ず full path を持つ（`*.py` は full/prefix とも 13）一方、調査記録は prefix 形なので、**path 制限なしで記録だけ落ちる**（「`*.md` を除く」より強い）。⚠ 不在主張には **rc** と **その道具の出力形に対する positive control** も併記する。

> ⛔⛔ **§11 の訂正 2026-08-09 00:15（自検出・私の卓から相反する 2 裁定が出ていた）**: 上の「**以後の追記へ自動延長しない**」は、**私が §10 で先に着地させた規則と矛盾する** — §10 = 「別紙は**追記型ゆえ版で pin せず HEAD を読む**／**設計 4 編集の値を変えない限り再受入不要**」。⇒ ⭐ **先に着地した §10 が governs**（§11 は気付かぬまま例外を作っていた）。**同旨の裁定 `m-p4-93` が正**・本 §11 の pin は**参考値**（裁定時点の実測）として残す。
> **確定形（機械判定できる述語）**: pZ は **実行時点の HEAD** で item 14 を走らせ、**走らせた版の pin を記録する**。その版が受入済 content と異なる場合、**①`+N / −0`（行削除 0）かつ ②追加行に設計 4 値（`0.28` / TILT 20 / `0.110` / `1.440`）が 0 件** なら **本受入が自動的に及ぶ**（再受入不要）。⛔ どちらかが崩れたら **verdict を「p4 受入待ち」と label して私へ回す**（走行自体は妨げない）。⇒ **pZ は私を待たずに走れ、かつ未読のテキストが黙って受入を継承しない。**

> ⛔ **上記「HEAD」の語義固定 2026-08-09 00:18（自検出・p18 §1226 と同旨・私の文が repo ref と読めた）**: ここでの「実行時点の HEAD」は ⭐ **その file の現行 content**（`sha256sum <別紙>` で取る値）であって **repo の ref ではない**。⚠ 本 turn の実測がその差そのもの: **repo HEAD = `a392d994e7`**（他 pane の commit で動いた）／**別紙の最終更新 = `b8b80cbf32`・content sha `e5dd839672ae7692…`**（不変）。⇒ **repo ref を pin しても file について何も言わない**。**pin は file の content で取り、commit は照合注記**（本日確立の型）。⇒ ⭐ **「動く参照を、使う瞬間に解決して pin する」= 崩れる anchor の唯一の安全形**（item 14 が literal 行番号で踏んだのと同じ穴を、語のレベルで塞ぐ）。

> ⭐⭐ **軸 0 と、その解き方 2026-08-09 00:20（p18 §1228 = 「dead session は 2 つある」・p4 が自分の記録を実測）**:
> - ⛔ **軸 0 =「どの対象か」が 4 軸の前に在る**。今夜 2 卓が同時に「dead-session token」と散文で書き、**別々の session を指していた**（p4 側 = driver が bind する sim session ／ 他卓 = その卓自身の旧 session）。⇒ **散文は対象の一意性を失う**。⇒ **run 記録は 5 項**: ⓪**どの対象か** ①token 文字列 ②pattern 構文 ③path 母集団 ④数え方。
> - **自測（本 file）**: full identifier **0 回** / prefix 5 回 / **省略記号つき 2 回** ⇒ ⛔ **「完全形で引け」と書いた記録自身が、完全形を 1 度も持っていない**。
> - ⭐⭐ **しかし書き足してはいけない**: 完全形が clean な query になるのは **記録が完全形を写さないから**。⇒ **解き方 = 記録は「対象を名指し、完全形が在る場所を指す」。完全形を転記しない。** 本 chunk の対象 = **`ur15_steps_wired.py:32` の `S = Path(...)` が持つ session id**（＝ driver が実際に bind する側・本 file の §7 が扱うもの）。完全形が要る者はそこから取る。
> - ⚠ **形は 3 通りで、prefix ではない形が在る**: 完全形 / 切り詰め（prefix）/ **省略記号（`…`）入り** — ⭐ **`…` は path に存在しない文字**ゆえ、省略形は**完全形の prefix ですらない別の文字列**。⇒ 「完全形で引く」が効く理由は「記録が短い」ではなく「**記録が別の文字列を書く**」こと。

## 12. chunk scope の再確認（p18 §1229 が渡した object 数への回答・p4 court・2026-08-09 00:22:52）

**実測（p4 が全数で再導出・relay で決めない）**: tracked `*.py` が bind する session object は **1 つでなく 3 つ**。
| object（prefix） | tracked `*.py` | scratch dir | 備考 |
|---|---|---|---|
| `377de041` | **1** | ⛔ **既に消滅** | `eval_runs/troot_optE_srg_probe_20260707/srg_s0_claw_render.py`（SRG probe） |
| `b0da55e6` | 1 | 在る | `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/splice_v231.py`（p5 arc） |
| `b952db35` | **13** | 在る | 本 chunk が扱う側（driver が bind する） |

**決定 = chunk の scope は変えない（`ur15_steps_wired.py` + `render_cell_overview.py` の 2 file のまま）**。
- 根拠 ①**交差 0**: `377de041` は本 chunk の 2 file に**出現しない**（実測 rc=1）⇒ DoD 経路を塞いでいない。②本 chunk の目的は「**DoD の run 経路を通す**」であって「dead-session binding を一掃する」ではない（後者は 3 object・15 file に及び、退役 driver と banked 読みを backing する probe を触る = 別のリスク）。
- ⇒ **p0 への答え = 「S を書き換える」側**（2 file・class 一掃ではない）。

**⛔ ただし記述を訂正する（私の §7 は 1 object しか数えていなかった）**: §7 の「残 11 file は壊れていると明記して据置」は **`b952db35` の集合に限った数**だった。⭐ **全体像 = 3 object / 15 file**、そして **既に回収済みの dir を持つ binding が 1 件実在する**（`377de041`・**予測ではなく実測**）。⇒ **§7 の「沈黙を可用性と読まない」は 3 object 全体へ適用**する。
- ⇒ **別件として起票を依頼**（p6 register・p18 経由）: 「**tracked code が、既に消滅した session scratch に bind している**」= 予測でなく現況。owner・修正形は本 chunk の court 外（当該 arc の owner）。⛔ **私は修正しない**（scope 外）。

> ⭐ **§7 scope の確定（p4 court・2026-08-09 00:23・p18 §1228 を第一手で再測）— 対象は 1 つでなく 3 つ、うち 1 つは既に消滅**: tracked `.py` が束縛する session object は **3 つ**（`git grep -ho` で完全 uuid を抽出・私の実測）: **`b952db35…`= 13 file・dir 存在**（本 chunk が直す側）／**`b0da55e6…`= 1 file・dir 存在**（`P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/splice_v231.py`）／⛔ **`377de041…`= 1 file・dir 既に GONE**（`eval_runs/troot_optE_srg_probe_20260707/srg_s0_claw_render.py`）。⇒ ⭐ **回収は予測でなく既遂**（「いつか消える」ではなく「1 つは既に消えていて、tracked file がまだ指している」）。
> **判定**: 本 chunk の scope は **wired + render の 2 file のまま不変**（C-2 の run path で閉じる・SRG probe 系は別 arc で本 DoD を塞がない）。⛔ **ただし class を黙って落とさない** — 上の 3 object / 15 束縛は本 file の記録として残す。
> **p0 への形の指定（重要）**: 修正を **「session id を書き換える」形で書かない**。⛔ 1 つの uuid への一括置換は ①他の 2 object を残し ②chunk 外の file に触れる。⇒ **「in-scope 2 file の `S` / `SRC` / `AS_BUILT` を repo 内 `_gen/` へ再定義する」= instance fix** として書く（§7 設計のまま）。**class（残り 2 object）は可視のまま未請求** — `377de041` は**既に壊れている** ので、SRG probe 系の owner へ回付が要る（私の court でない・p18 経由で routing 依頼）。

> ⭐⭐ **5 番目の形 2026-08-09 00:24（p18 §1230 が「私の kickoff にまだ在る」と報告・両者の数が食い違った ⇒ 同じ文字列を探したかを先に問うた）**: **両方正しかった**。私の query は**完全 36 字**で hit 0、p18 の query は**頭 13 字**で hit 1。実際に在ったのは ⭐ **頭と尾を残して *中間* を省略した形**〔**役割 = 形の例示**（schematic・実 identifier は転記しない）: `xxxxxxxx-xxxx-…-xxxxxxxxxxxx`〕。⇒ **形の空間は 4 つでなく 5 つ**: 完全／頭だけ（prefix）／末尾省略（unicode `…`）／末尾省略（ASCII `...`）／⭐ **中間省略（頭…尾）**。⚠ **中間省略は最も紛らわしい** — **prefix query には当たり、完全形 query には当たらない**ので、「完全形 0 件」と「まだ在る」が**同時に真**になる。⇒ ⭐ **形を列挙して防ぐのは不可能**（記録側は書くたびに形を増やす）＝ 完全形で引く根拠はここにある。
> ⇒ **私の該当箇所は「引用」でなく「例示のための転記」**（p18 の 2 分岐で言えば *pointer で足りる* 側）⇒ **上の第三項から転記を外し、`ur15_steps_wired.py:32` を指す形へ直した**（本 turn）。⛔ **p18 の台帳側は別分類**: あちらは*証拠としての引用*（特に 8 文字 prefix が一致する 2 uuid の対比は完全形でしか書けない）⇒ **消してはならない**。⭐ **完成形の規律は 2 分岐**: **記録が対象を*指す*だけなら prefix + 在り処** ／ **記録が*証拠を引用*するなら逐語で残し、query 側が 5 欄を書く**。

> ⛔⛔ **同 turn の再発と、その処置 2026-08-09 00:26**: 上の「5 番目の形」の段落で、私は**転記を外した直後に、同じ文字列を「例示」として書き戻していた**（p18 の pattern で hit が 1 のまま残った・私の label 読み違い `rc=0` かつ count 1 = **まだ在る**を「消えた」と書いたのも同じ turn）。⇒ **処置 = 実 identifier を schematic（`xxxxxxxx-xxxx-…-xxxxxxxxxxxx`）へ置換し、⭐ 役割を行内に明記した**（「役割 = 形の例示」）。
> ⭐ **一般形（p11 発・p18 が採択した「役割を書く」の、私の側の実例）**: **2 分岐（指す / 引用する）は行の *役割* で決まるのに、散文は役割を運ばない** ⇒ **行に役割を書く**。⚠ 私の場合、役割は「形の説明」であって「証拠の引用」ではなかった — **形を説明するのに実 identifier は要らない**（schematic で足りる）。⇒ **第 3 の枝**: 指す＝prefix + 在り処／引用＝逐語で残す／**例示＝schematic に置き換える**。

## 13. 2 件の一言回答（p0 と p6・p4 court・2026-08-09 00:29）

**(a) p0 へ — 「`S` を書き換える」は *置き換え対象の呼び名* であって literal な述語ではない。対象は本 chunk 2 file の binding 全部 = 3 本。**
- 実測（p4 第一手・p0 の発見どおり）: `ur15_steps_wired.py:32` = `S = Path(<session>/scratchpad)`（**dir 自体**）／`render_cell_overview.py:36-37` = `AS_BUILT`（**2 行連結**・末尾 `scratchpad/meshpool/_as_built_t42.xml`）／`:38-39` = `SRC`（**2 行連結**・末尾 `scratchpad/_steps_cell_full.xml`）⇒ **3 binding・3 つの深さ・2 本は行境界で分割**。
- ⇒ **3 本すべてが対象**。⛔ **2 つの sub-path を片方に畳まない**（別物として保つ）。⭐ **`S` の 1 変数だけ直す読みは誤り**（3 分の 1 しか届かない）。§7 は当初から render の `SRC`/`AS_BUILT` を名指していたので、本回答は **scope 変更ではなく語の明確化**。
- ⚠ 行境界分割ゆえ **`S = Path(` を grep する修正はこの 2 本を落とす** ⇒ **内容で特定して直す**。

**(b) p6 へ — ① class として起票する（instance は第一の実測メンバーとして添える） ② 起票する（「しない決定の記録」ではない）。**
- ① 理由: 対象は **3 object / 15 file**、**うち 1 つ（`377de041`）は dir が既に消滅**。**instance 1 行にすると「その 1 file を直して close」と読まれる**が、閉じるべきは「**tracked code が session 単位の scratch dir に bind している**」という条件のほう。⇒ **row = class**・本文に測定（3 object / 15 file / 消滅 1）と消滅済み instance の file 名を添える。
- ② 理由: 仮説でなく**現況の実測**であり、**arc をまたぐ**（p4 sim / p5 / SRG probe）。⛔ **owner が居ない** ＝ DDR が拾うべき「誰も進めず gate も鳴らない面」そのもの。**owner・修正形は各 arc の court**（⛔ 私は当該 file を直さない）。⚠ **本 chunk の 2 file は例外**（本 chunk が処置する）と row に明記されたい。
- ⚠ 出所の等級: 本節は **p4 の一次テキスト**。p6 は relay でなく本 §13 と §12 を on-disk で読んで起票してよい。

> ⛔⛔ **§7 設計の穴（自検出 2026-08-09 00:33・p18 §1235 の実測が照らした・p0 が diff を書く前に）**: 私は **wired 側にのみ** `S.mkdir(exist_ok=True)` を要求し、**render 側の親 dir 生成を書いていなかった**。実測（本 turn・rc は grep 自身のもの）= `render_cell_overview.py` に `mkdir` は **0 箇所（rc=1）**／`…/scratchpad` は**在る**が **`…/scratchpad/meshpool` は不在** ⇒ **`:53 `AS_BUILT.write_bytes(SRC.read_bytes())` は今この瞬間 FileNotFoundError で落ちる**（⭐ 落ちる原因は **AS_BUILT の親 dir** であって、書かれる側の `_as_built_t42.xml` の不在ではない — **不在の出力は証拠でなく、不在の入力が証拠**）。
> ⇒ **p0 への追加要求（設計の変更でなく欠落の補充）**: 移設先でも **`AS_BUILT.parent.mkdir(parents=True, exist_ok=True)` を書く**（`_gen/meshpool/` は 2 階層ゆえ `parents=True` 必須・wired 側の `_gen` も同形で安全側に `parents=True`）。⛔ **これを落とすと同じ失敗が新しい path で再現する**。
> ⇒ **本 chunk の性格も更新**: 「将来 dir が消えるかもしれないという durability 上の懸念」ではなく、**DoD の視覚レグ script が現に走らない状態の修理**（p4 が 23:53 に priority を provenance から降ろした後の、より強い実測根拠）。⚠ 代替経路は spec `:203`/`:215` が既に認可（視覚レグは wired 自身の描画でも可）— ⛔ **旧 session の dir を作り直して回避しない**（本 chunk が消しに来ている条件そのもの）。

## 14. HOLD 下で何を実行してよいか（p4 court・2026-08-09 00:37）

⚠ **契機**: 「p0 が 00:34 に write を実行して `FileNotFoundError` を得た」（p18 §1235/§1241）。⛔ **私は p0 を咎めない** — **境界を書いていなかったのは私**で、fence を発効させたのは私だから。⇒ 前例が曖昧なまま積み上がる前に明文化する。⛔ **本節は緩和ではない**（下の C は従来どおり Rs gate）。

**A. 受入済 spec が既に authorize している実行（追加の gate 不要）**
- spec §6-2 の self-check（`python -c` で定数を import して印字）・pZ の受入 12 項＋別紙の項目。⇒ **私が accept した時点で承認済**。⚠ ただし **#61 の env pin**（`env_isaaclab7`）下で行い、版を run 記録に書く。

**B. 診断実行（本節で新たに明文化・条件つきで可）**
- **定義**: 既存 script を走らせて**故障の有無・機構を観測する**こと。⭐ **成果物は「壊れている/直った」の観測のみ**。
- **条件（全て満たすこと）**: ①**task 性能・DoD・verdict の根拠に一切引用しない**（引用したければ C へ上がる）②書き込みは **repo 内の生成物 dir** に限る（⛔ session scratchpad へ新規に作らない = 本 chunk が直している当のもの）③**実行した事実と結果を報告する**（黙って走らせない）④**fence 内の script のみ**（退役 driver・独自 cell の video script は不可）。
- **理由**: 修理が要るかを**測らずに決める**ことこそ今夜ずっと直してきた失敗（p0 の 00:34 の実行は、私の §7 の穴＝render 側 mkdir 欠落を**別の端から**照らした）。⛔ 診断を禁じると、設計判断が推測の上に乗る。

**C. 判定を生む run（不変・Rs gate）**
- sim を走らせて **task の成否・数値・動画**を得る類（DoD run・row 46 の close 条件を満たす run・training 一切）。⇒ **Rs の gate**（row 46 逐語）＋ fence ＋ env pin ＋ 本 file の evidence-grade cap（#48/#18 open の間は無印 PASS なし・#49 は gate 状態併記）。⛔ **本節は C を 1 mm も動かさない**。

**判別の一言**: ⭐ **「その出力を後で引用したくなるか」**。引用したくなるなら C（Rs gate）。「動くか動かないか」を見るだけなら B。定数を読むだけなら A。

## 15. ⛔ 節番号の対照表（本 file は番号が 2 組重複している・2026-08-09 00:39 自検出）

⛔ **本 file を引く時は「番号だけ」で引かない。番号＋見出し（または内容）で引く。** 実測 = 見出し 17 個のうち **`## 9.` と `## 11.` が各 2 回**（追記を並行に重ねた結果・外部引用は本節時点で 0 件 = まだ伝播していない）。
⛔ **番号は振り直さない** — 振り直しは既存の見出しの in-place 書き換えであり、他卓が既に引いた pin を壊す（p11 が同じ理由で節の並べ替えを断ったのと同型）。**代わりに本表で一意にする。**

| 番号 | 見出し（一意な識別子はこちら） | 行 |
|---|---|---|
| 0-8 | 重複なし（`## 0.`〜`## 8.`） | :8 / :15 / :25 / :30 / :52 / :60 / :65 / :84 / :117 |
| **9(a)** | **別紙 A の受入判定**（p4 court・22:31:5x） | :134 |
| **9(b)** | **DoD 射程の訂正と、中間目標までの実距離**（p4 自測・23:0x） | :143 |
| 10 | 統治集合の pin と URDF provenance 主張の縮小 | :196 |
| **11(a)** | **版の裁定（PZ-114 への回答）** | :221 |
| **11(b)** | **再受入の裁定**（⚠ **11(a) と同じ問い** — 競合し、`§10` の先行規則が governs と 11(b) 内で訂正済） | :235 |
| 12-14 | chunk scope 再確認 / 2 件の一言回答 / HOLD 下で何を実行してよいか | :263 / :289 / :305 |

⚠ **行番号は本節時点の値**（本 file は追記で伸びる）⇒ **恒久の指し手は「番号＋見出し」**、行と commit は照合注記。⭐ 本表を**末尾に置いた**のは、先頭に入れると既存の全行番号がずれ、他卓が既に持つ `:117` `:289` 等の pin を今この瞬間に腐らせるため（**索引の置き場所自体が anchor 問題**）。

> ⛔ **本表自身の更新 2026-08-09 00:44（表を足した 5 分後に、表が扱う欠陥を表自身が起こした）**: **`## 15.` が 2 つになった** — **15(a) = 本表**（節番号の対照表）／**15(b) = p0 への一言**（micro-chunk 発進可否）。さらに **16 = p0 の 3 行は fence の内か外か**。⚠ **実害が既に出ている**: p18 が `§15 :322 = §7:100 が govern するか` と引用したが、**:322 は本表**で、その内容は **15(b)** に在る（行は本節挿入で下にずれる ⇒ ⭐ **行番号は照合注記・恒久の指し手は「番号＋見出し」**）。⇒ ⛔ **やはり振り直さない**（他卓が既に引いた番号を壊す）。**引く側は必ず見出しを添える**。

## 15. p0 への一言（micro-chunk の発進可否・p4 court・2026-08-09 00:41）

**答え = YES。§7 `:100` は現に govern する ⇒ p0 は p5 のレグを待たずに `wired` + `render` を進めてよい。**

- **根拠（私が自分の §7 を実読して確認）**: `:100` 逐語「**file 重複なし**: 本件 = wired+render / C-2 = cell_spec+sweep ⇒ **並行可・p5 整合レグとも独立** — p0 は C-2 発進待ちの間に本件を先行してよい」。⇒ **p5 のレグが gate するのは C-2 の 4 編集（工程表との整合）**であって、dead-scratchpad の修理ではない。**両者は file が交差しない**（実測済）。
- **同時に効く条件（変更なし・全て私の既存節）**: ① **§8 の working method**（worktree の非 lane branch へ commit → pZ が clean checkout で content pin 検証 → verdict 後に lane へ着地・受入条件 = landed sha == verified sha）② **§7 の ⛔ list**（挙動/出力形式を変えない・fence 外へ波及しない・新 env var/新 CLI なし・**C-2 4 編集と同居 commit にしない**）③ **§7 末尾の mkdir 要求**（`AS_BUILT.parent.mkdir(parents=True, exist_ok=True)`・`_gen/meshpool/` は 2 階層ゆえ `parents=True` 必須）④ **§14 の実行境界**（実装は run ではない。直後に「動くようになったか」を見るのは **B = 診断**で可 — 引用しない・repo 内へ書く・報告する・fence 内 script のみ）。
- ⛔ **本節が動かさないもの**: C-2 の 4 編集（p5 待ち）／判定を生む run（Rs gate）／DoD の evidence-grade cap。⭐ **「HOLD」は run の権限についての語であって、実装を止める語ではない** — 私も §0 でそう書き分けていたが、**両方を 1 語で呼んでいた期間があった**ことは記録しておく。

## 16. p0 の 3 行は fence の内か外か（p4 court・2026-08-09 00:42・§14 の適用）

**答え = 内（違反なし）。ただし §14 の A/B/C のどれでもなく、その下に 1 段在ることが分かったので明文化する。**

- **対象（p0 の自己申告・私は観測していない = 等級 relay）**: import なし／path は literal／`SRC` を読まない／**何も作られていない**／書込先は `/tmp` のみ。⇒ **fence が支配するのは「どの script を走らせるか」**（spec §6-6）だが、**p0 は fence 内外いずれの script も走らせていない** — file system の呼び出しを 1 つ試しただけ。
- ⇒ ⭐ **新設 class A′（§14 の A の下）= 到達性の確認**: 「その path は解決するか」を確かめる最小の呼び出し。**条件** = ①**何も作らない**（作るなら B の条件に上がる）②**出力を task の証拠に引用しない** ③**報告する**（p0 は満たした）。⛔ **C（判定を生む run）とは無関係**。
- **理由**: この 1 呼び出しが**私の設計の穴**（render 側の `mkdir` 欠落）を照らした。⛔ **これを禁じる境界は、修理の要否を推測で決めろと言うに等しい** — 今夜ずっと直してきた失敗そのもの。⭐ ただし **A′ は「何も作らない」で線を引く** — 作った瞬間に、消えた dir を作り直す等の副作用が入り得るから。
- ⚠ **等級の明示**: 上の記述は **p0 の申告に基づく**（p18 も観測していないと訂正済）。⇒ **申告と異なる事実が出たら本裁定は再判定**。⛔ 私は p0 の act を咎めない — 境界を書いていなかったのは私（§14 の契機）。

> ⭐ **§14 追補 — 00:34 の 3 行 snippet の分類（p4 court・2026-08-09 00:42・p18 §1243 (i) への回答）**: **fence の内側（許容）。B より更に狭い「機構 probe」に当たる。**
> **判定の根拠（p0 の報告した性質・私は実行を観測していない = relay 等級）**: ①**project の code を 1 行も実行していない**（import なし・literal payload）②**何も生成・変更していない**（SRC 未読・write は親 dir 不在で失敗）③出力は「その操作が落ちるか・なぜ落ちるか」だけ ④**task 性能・DoD・verdict の根拠に引用されていない**。⇒ **§14 の B が要求する 4 条件を全て満たし、かつ B より侵襲が小さい**（B は「既存 script を走らせる」を含むが、本件は走らせていない）。
> ⛔ **咎めない理由は §14 冒頭のまま**（境界を書いていなかったのは私）。⭐ **加えて、この probe は私の設計の穴を別の端から照らした** — 読解（私）と実行（p0）が同じ欠落に別経路で到達した。
> **次回のための締め（禁止でなく形の指定）**: ⭐ **非破壊の probe を優先する** — 「親 dir が在るか」は `Path(...).parent.exists()` で**書かずに**答えが出る。⚠ **書く probe が要る場合は、書き先を dead session の tree にしない**（成功していたら**回収済み dir を作り直す**ことになり、本 chunk が消しに来ている条件そのものを再生産する）。⇒ 書き先は repo 内の生成物 dir か、その場限りの別 path。

## 17. pZ の item (iii) — render 実行は pZ の職掌内か（p4 court・2026-08-09 00:44）＋ §14 の判別語を直す

**答え = YES、pZ の職掌内。Rs gate に上げない。**

⛔ **ただし先に私の欠陥を直す**: §14 の判別語「**その出力を後で引用したくなるか**」は**粗すぎた**。pZ の (iii) の出力（絵が出たという事実）は確かに引用したくなるが、**何の証拠として**引用するかが決定的で、それを私の語は区別していなかった。⭐ **修正した判別語**:

> ⭐ **その出力は「道具」の証拠か、「世界」の証拠か。**
> - **道具の証拠**（走るか / file が出るか / 定数が効いているか）= **実装の検証** ⇒ **pZ の職掌・追加の gate 不要**。
> - **世界の証拠**（cell は正しいか / route は成功したか / 物理は妥当か）= **判定** ⇒ **Rs gate**（＋ fence・env pin・evidence cap）。

**⇒ (iii) の扱い（条件つき YES）**:
1. **verdict は機械的レグに限る** — 「script が走り、画像を出した」まで。⛔ **絵の物理妥当性は一切述べない**（pZ の brief どおり Rs の court）。pZ が裁定前に自らこの scope を宣言したのは正しい形。
2. ⛔ **この画像を DoD の視覚レグとして提出しない**（DoD の視覚レグは motion を含む run → Rs human-GT）。**修理の実証**であって成果の実証ではない。
3. **#61 の env pin 下**（`env_isaaclab7`）で実行し版を run 記録に印字・**fence 内 script のみ**（`render_cell_overview.py` は spec `:203`/`:215` で authorized）。
4. 生成物は **repo 内の生成先**へ（⛔ session scratchpad を作り直さない = 本 chunk が直している当のもの）。
5. ⛔ **2 つの視覚レグ経路は等価でない（p11 の spec-owner 明確化 2026-08-09 00:45 を受けて明記）**: spec `:203`/`:215` は 「`render_cell_overview.py` **か** wired 自身の描画で」と 2 択に書くが、**後者は route run**（sim を走らせて絵を得る）⇒ **class C = Rs gate**。本 §17 が pZ の職掌内としたのは **前者のみ**（静的 build 時の絵）。⚠ **spec の 2 択を「どちらも同じ費用」と読まない** — 片方は道具の証拠、もう片方は世界の証拠を生む経路で、gate が違う。

**⭐ 私の側の記録**: 本問は **§7 の pZ 項目 (iii) を私自身が書いた時点で既に authorize していた**のに、後から書いた §14 の粗い語がそれと衝突した。⇒ **後から書いた一般則が、先に書いた具体を否定して見えることがある** — その時は**具体が正しく、一般則を直す**（今夜の §10 対 §11 と同じ形・2 度目）。

> ⛔ **§17 の穴を塞ぐ 2026-08-09 00:45（p11 の実務注記が照らした・p4 が構造で確認）**: spec `:203`/`:215` は視覚レグに **2 択**を認める（`render_cell_overview.py` **か** wired 自身の描画）。⛔ **私の §17 の YES は前者だけ**である。⭐ **後者は route run** — `ur15_steps_wired.py` を走らせることは **STEP 1（`:2509`）＋ STEP 表 2-18（`:2639`）を実行すること**そのもの ⇒ **世界の証拠を生む** ⇒ **§17 の新判別語で C 側 = Rs gate**。
> ⇒ **確定**: **pZ の item は `render_cell_overview.py`（静的）で行う**。⛔ **wired 描画へ切り替えてよいと読まない**（読み替えると authorization の無い route run になる）。⚠ **順序**: render は今日の disk では走らない（`meshpool` 不在・`mkdir` 0）⇒ **micro-chunk の着地後**に `_gen` 経路で走る（§7 `:98-99`）。⇒ **2 択は費用が等価でない** — 一方は静的、他方は Rs gate。
