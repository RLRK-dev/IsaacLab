# P4 chunk kickoff — Rs 指示「中間目標を達成せよ」→ C-2 実装 chain 設計起動

desk: p4 RS-TECH-LEAD (w2:p4) / 記録 **2026-08-08 21:01:06 JST**（`date` 実測）/ 本 session = `ae175dcf`
⛔ 本 file は **選定と回付の記録**。code / env / spec / asset の編集は含まない（実装は chain と gate 経由）。

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
