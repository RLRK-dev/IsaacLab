# p11 — L3 五体検証 verdict: UR15-B controller 設計 v1（cycle 1 = FAIL）＋ pre-check（BLOCK）

**Author** w2:p11 · **Written** 2026-09-13 08:44:02 JST · 対象 = `P11_UR15B_CONTROLLER_DESIGN_20260913.md` **v1**（本 commit で FAIL 印つきで bank・v2 は別 commit）。Naming: Rs1 = 人間 / Rs2 = p4。
panel = pre-check 検証者 1 ＋ lens 4（CC2 premise/provenance・CC3 rule/SSOT・CC4 numerical/physics・CC5 side-effects/regression）＋ CC6 帰無仮説。全員 read-only・driver 不実行・run 0。CC1（当卓）は 6 体完了後に読み、各 finding の事実面を **pin 済 object で自分で開いて**確認してから disposition を書いた。
集計 = pre-check **BLOCK**（CRITICAL 1・HIGH 3・MEDIUM 3）／CC2 12（HIGH 5）／CC3 15（HIGH 4）／CC4 7（MEDIUM 3）／CC5 8（HIGH 1）／CC6 7 null 中 6 生存（HIGH 1）。**union = CRITICAL 1・HIGH 10（重複統合後）・MEDIUM 19・LOW 16**。⭐ **CRITICAL/HIGH は全て panel 発**。当卓の自己検査で捕まえたものは 0（08-09 と同型）。

## 1. DECIDE = **FAIL**（cycle 1）／pre-check = **BLOCK**
- 受入 = CRITICAL 1・HIGH 10 の全部・MEDIUM/LOW の全部（下表）。反駁 = 語法 3 件のみ（表末尾）。
- 中心決定（D1 identity／D2 側別測定／D3 不変／D5・D6 不変／code 変更 = 計器 1 件）は **どの body も偽と示していない**（CC6 総括・CC4 CONFIRMED）。偽だったのは **引用した証拠の射程**（07-29 の測定 = 0.22/45・鏡像化前 hand・生 entry 入力）と **唯一の deliverable の効果**（cap は今日 gate に入らない）と **検証 leg の実行経路**（driver は import 即実行）。
- ⇒ v2 = 射程・経路・census・D4 仕様・created-object 記録を直した書き直し。cycle 2 で pre-check ＋ 5 体を再走。

## 2. union（severity 降順・出所・当卓の disposition・v2 での fix）
| # | sev | 出所 | 指摘（要旨） | 当卓の確認（object） | disposition → v2 |
|---|---|---|---|---|---|
| C1 | CRITICAL | PC-1 | R1-R3「static・built C-2 cell」に driver を走らせない計器経路が無い。wired は import 即実行（`:442 m = cell.compile()`・`:3143` STEPS loop 全て module-level・`__main__` guard 0）・kinonly は stock URDF＋stock hand（`:123-126/:299-302`）で UR15-B 不在。R3「cap 前後」は wired import 2 回。#69 と循環。「run を含意しない」は R3 について偽 | `__main__` grep = comment 1 のみ／`:442 :447 :3143` module-level 実測／kinonly `:123 :299 :301` 実読／`_gen/dod_c2_20260810/` = run.log＋mp4 のみ | **ACCEPT**。経路 = `ur15_gripper_mirror_acceptance.py::build_side()` @ `b7a5e39ecf`（hand-on-arm・両側・mount は cell_spec から live import ⇒ 既定で C-2・**wrist→hand frame `acc.R_TOOL` = wired `:420` と同一式**〔`ur15_mirror_acceptance.py:56-57` 実読〕・mj_step 0・driver 不要・pZ が 08-10 に隔離 copy で走らせた class）／腕のみ = `ur15_mirror_acceptance.py::build()`／field = 単体 compile。R0（solve_ik on B）は solver 抽出 harness = class 判定を p4/pZ へ。行ごとに計器・object・認可状態を書く |
| H1 | HIGH | PC-3・CC2-1 | 側固定 census が名前 8 個の query の産物。`release_ctrl` `:2827` が `mouth_clear(t="L")` `:2814`・`CLAWG["L"]` `:2847` から RELEASE を導き `:3137`→`:3141` で**両手**へ／`slot_centre("L")` `:1276`／`[rel]` 診断 `:3021-3029`。陽性対照の数が blob と違う | P1（容器 19 名）11 hit・P2 call-form 14・P3 default 3 を blob で実測・`:2847 :3137 :3141 :2890` 実読 | **ACCEPT**。v2 §4 に census 全 hit の分類表＋ D5′（release_ctrl は共有のまま・正当化 = hand 192/192 鏡像 ＋ pZ static row `mouth_clear(L)==mouth_clear(R)`）。数は「行/出現」と rev つき |
| H2 | HIGH | PC-2 | 08-10 の C-2 DoD record が既存 class の B 駆動を測っている（`run.log` sha `04599b84e34be51e` `:55` R 16 solved/4 collision-free・`:99` STEP1 R 2.2 mm・`:355` STEP2 R 100%・`:366`／L は `:51` 0/13・`:94` 658.5 mm・`:84` spread 0.280 tilt 20.0）。ただし hand は回転コピー（run 02:11 ＜ 鏡像 hand 09:09） | 全行 実読・sha 実測 | **ACCEPT**。v2 §3 に「B は C-2 で測られている（旧 hand）— 鏡像 hand 後は再測」。§8-2 の STOP は「初測」でなく「再測で落ちたら」 |
| H3 | HIGH | PC-4・CC6 H0-3・CC4-5・CC5-3 | cap は print `:2987-2988` にしか入らない（`vertical_tol_deg(` 呼び出し 0・cell_spec `:829` は cap 無しの interim 5.73）。gate `:3517` は既に側別（`:3446`）。記録の cap 5.73 = 0.10 rad 厳密 ⇒ v_c ≈ 0 が既に測られており R3 は落ちようがない。将来 r_max 着地で `vertical_tol_deg(r_max, cap)` に入る（第 3 分岐 raise）— min は cap を下げる向き | `:2987-2988 :3517 :829 :768` 実読・record `:104` 実読 | **ACCEPT**。v2: D4 = 「gate-inert・数値効果 0 iff v_c=0」と明記／消費 = 今日 print・将来 `vertical_tol_deg`（p5 §6.4j の court・配線は scope 外＋/reward-design）／controller を判別する述語 = **R0**（solve_ik が B で収束）／R3 は p0 受入項目へ |
| H4 | HIGH | CC2-3・CC6 H0-1・CC4-2・CC4-4 | HOME_POSE_SYMMETRY は `_as_built_t42.xml`（07-29 00:55）= **鏡像化前の回転コピー hand**（`GRIP_XML_MIRRORED` 初出 `b7a5e39ecf` 08-10 09:09）。§1-§3・§5 の数値は 0.22/45（t42 時の cell_spec）。§5 は生 (yaw,roll) を両側へ入れ full-matrix Mx 共役を検査（0.5910 = 2 sin 0.3）— 現行 sgn 規約の pair ではない。「pad が入れ替わる → v_c 反転」は回転コピーの徴で、鏡像 asset では同名 pad = 鏡像 ⇒ v_c^B = +v_c^L | source 行 `:2`・probe `:42`・commit 時刻 実測 | **ACCEPT**。v2: 07-29 由来の全数値に「@0.22/45・t42・pre-mirror hand」札／D2 の根拠 = 「側別に測る構造」のみ／tilt 一致の期待は撤回 → pZ R3 の**開いた測定**（前提 3 つ列挙・両結果の帰結）／pZ への selector = **roll**（yaw でない） |
| H5 | HIGH | CC2-2・CC5-1・PC-5 | D4 仕様が docstring を写し body と矛盾（cap は **入力** roll ≥1e-9 で選ぶ `:1306`・`:1314-1322` が出力選択の bug を記録）。「sgn を 1 箇所に共有」は pose_menu/solve_ik を触る（AST 同一と矛盾）— 正は既存の `SIDES` cell_spec `:485`（kinonly `:661/:666` が既にそう使う）。file 数 1 vs 2 の不一致 | `:1301-1326` 実読・`:485`・kinonly 実読 | **ACCEPT**。v2 §5: `cap_t = min(tilted_t)`（入力選択）・受け取る姿勢 `(SIDES[t]·yaw, SIDES[t]·roll)`・両 calibration raise を側別・pose_menu/solve_ik 不触・file = wired 1 本 |
| H6 | HIGH | CC2-5・CC6 H0-1 | R1（同 q で world 鏡像）は pZ PREREG `:28` の dead query (b)（wrist-3 1.75 m）と衝突 | PREREG 実読・dead query は **kinonly cell（stock arm 両側）**での測定・HOME_POSE_SYMMETRY §1 は鏡像 arm の t42 cell で 0.0000 mm | **ACCEPT**。v2 R1 に builder（鏡像 asset cell）と、dead query が当たらない理由（別 cell・別 asset）を書く |
| H7 | HIGH | CC2-4・CC2-9・CC6 H0-4 | 「Rs 逐語 `:904`」は p4 の 07-27 英語 docstring 言い換え（Rs1/Rs2 未分離）／「p5 −167」は code comment のみで p5 artifact が無い | `git log -S` で `66d8b8747d` 07-27・ledger `:13237` は下流 | **ACCEPT**。v2: 両者を「code 内参照・custody 不在」と札付け。D3 は**測定された code の規約**に立ち、裁定 custody は p4/p5 への非 blocking 質問 |
| H8 | HIGH | CC3-1 | §10 の「＝」式が #69 充足（p4/Rs1）と R4 の等級（pZ）を先決 | DDR #69 `:173`「充足判定 = p4」実読 | **ACCEPT**。v2: 式を削除・rows は等級なしで提供・「動的 controller leg は #69 run の中でしか測れない」を p4→Rs1 への問いに |
| H9 | HIGH | CC3-3 | /pre-check が「列挙」だけで未実行・DoD に無い・07-21 の 3 連続 BLOCK 未開示 | `logs/pre-check-log.jsonl` tail 実読 | **ACCEPT**。本 turn で実行済 = **BLOCK**（本 doc §3）・log 行追記・v2 DoD に「pre-check ≠ BLOCK」・07-21 3× BLOCK を開示 |
| H10 | HIGH | CC3-4・CC6 H0-5 | 「既に在る」が Rs1「作成」を狭める推論。UR15-B は名前＋provenance header を持つ created object だが controller にその類比が無い。task 空間 leg の枠組みを退けるのは p4 の court | kickoff 09:51 §1 実読 | **ACCEPT**。v2: §1 を「導出結果 = identity ＋ D4」に書換・**Rs1 への問い**（identity＋D4 で『作成』を満たすか／B 側 artifact を期待するか）を p4 経由で明記・**created-object 類比 = §「UR15-B controller の識別記録」**（側別 instance と測定箇所の表）＋ p0 による identity print 1 行の**提案**（採否 p4） |
| M1 | MED | CC3-5 | brief `:69`「Rs 承認後 p4 が p0 へ渡す」の読み未記載 | brief 実読 | ACCEPT: 「Rs1 ① 08-10 = 本導出への :69 承認」を **inference 札**で明記 |
| M2 | MED | CC3-6・CC5-3 | `vertical_tol_deg` = p5 §6.4j の court・cap 配線は /reward-design | cell_spec `:768-787` 実読 | ACCEPT: v2 §5 に 1 行 |
| M3 | MED | CC3-7 | 「menu が鏡像であるべきか」を p11 court と自称 | `:78` 実読（court 名なし） | ACCEPT: 「p5 と共有・本書は D3 不変で触れない」 |
| M4 | MED | CC3-8・CC2-6・CC4-7 | cell_spec 1,395 行は dirty tree・pin は 1,250 行・dirty 未開示 | `wc -l` 両方 実測（1250/1395・+391/−246） | ACCEPT（**自分の規約違反**）: 1,250 @ `0f6b4a733e`・dirty を §9 へ |
| M5 | MED | CC3-9 | rule-check stage1 YAML／Tier 0-4 checklist 不在 | skill `:156-215` 実読 | ACCEPT: v2 §11-a に添付 |
| M6 | MED | CC2-7 | pZ B2 自身の FK worst = 0.0079/0.0074 mm・0.0013–0.0076 は record 再 parse | pZ `:22-23` | ACCEPT: 帰属訂正 |
| M7 | MED | CC2-8・CC4-2 | 姿勢の完全な関係 = 接近列は y 鏡像・閉じ列は y 鏡像＋反転（`RD_L = My·RD_R·My·Rz(π)`／`RD_R = My·RD_L·Mx` True）・−0.1668→−0.1669 | CC4 数値と一致 | ACCEPT: 文言＋数値訂正・「導出」札 |
| M8 | MED | CC5-2 | D4 は起動時 abort 面（`:1301/:1307` の 2 raise）を両側に広げる。08-02 に実際に発火（`order_test_logs/*:96` 「zero roll comes out … off vertical」） | log 3 本 実読 | ACCEPT: 先例を §5 に・「cap 計器の abort は controller verdict でない」・pZ R3 に両側極値の static 事前測定 |
| M9 | MED | CC5-4・CC6 H0-6 | dirty WIP が D4 の対象行と重なる（hunk `@@ -1302 @@ def vertical_cap_deg` 等）。WIP は formatter＋未使用 import 6 個削除 | hunk 実読 | ACCEPT: 着地前提 = clean worktree @ `22feba17a6` から編集・WIP の処遇を p18 へ照会（着地条件） |
| M10 | MED | CC5-5 | 「13 def AST 同一」は module-level 制御（STEPS loop `:3143-3978`・START solve・ramp）と rejection helper を見ない | 実読 | ACCEPT: v2 DoD (b) = **module 全体**の正規化 AST 等式（2 def ＋ print Expr 1 のみ差を許容・陽性対照つき） |
| M11 | MED | PC-6・CC4-3 | 「現行 = B の姿勢」は偽（現行 = 「pad が入れ替わらなかった場合の B」= どちらの腕でもない）・det(AXFIX)=+1 は s=a×c ゆえ構成的に真（証拠にならない）・calibration 0.5° ⇒ |v_c| ≤ 0.0087・cap ∈ [5.24°, 6.23°] | CC4 数値 | ACCEPT: 文言削除・det を証拠から外す・bound を記す |
| M12 | MED | PC-7 | bar 不在（R1「asset 級」・M 未指定・R2「等しい」の float・STOP §8-1 に数が無い） | — | ACCEPT: R1 ≤ 1e-3 mm・M ≥ 24 draw／R2 int/range は厳密・共役 float ≤ 1e-12 相対（pZ B3 = 6.7e-16）／STOP は pZ の bar を参照 |
| M13 | MED | CC4-1 | D6 の standing 条件（非対称 range → 側別 LIM）が**逆**。identity-q 鏡像（`A·Rot(n,q)·A = Rot(−An,q)`）では range は **byte 同一**のまま（hand generator `:16-19` が明記・hand は非対称 range を byte 同一で持つ）。acceptance `:214` の `[lo,hi]→[−hi,−lo]` 期待は逆（対称ゆえ今日は落ちない） | `make_ko_mirror.py:16-19`・hand range 実読 | ACCEPT: v2 D6 = 「LIM 共有は D1 の帰結・B の range は A と byte 同一が要件」・acceptance `:214` の訂正は別 task へ回付（本 chunk 外） |
| M14 | MED | CC6 H0-4 | pZ に渡す selector は roll（yaw でない） | CC4/CC6 数値一致 | ACCEPT |
| L* | LOW | 各 body | counts（`\bpinch\(` 21 行/23 出現・`[t` 87 行/92 出現・`\[t\]` 81/86）／`_measure_axfix :594-613`／print `:2987-2988`／LEDGER ①② 番号／`SIDES.items()`／m-p18-282 → ledger §1401/§1403／P4_ROLL_CAP との区別／層5 = post-change／34 日は self-report 札／node = p4 node 下の sub-court／RUN_METRICS leg 実在／LEDGER cite に rev／AXFIX 直交化 assert 提案（D4 外）／CC4-4 前提 3 つ | 実測 | ACCEPT 全部 |

**反駁（語法のみ・受入に変更なし）**: (i) CC2-12(c)「#66 は wired run 規則の行でない」— #66 の閉鎖文「wired/DoD 閉扉は fix 着地まで継続」を DDR #69 が「行 66 の閉鎖文どおり wired/DoD は常設規則 = Rs1 認可」と引く ⇒ 引用は閉鎖文を名指す形に直す（行の見出しではない）。(ii) CC6 H0-5「m-p18-282 は object でない」— pane message の custody = 当卓 transcript・durable = ledger §1403（`:46800-46810`）⇒ 引用を ledger へ。(iii) CC3-1「R4 gate でない は提供と矛盾」— R4 は認可 run の中でしか測れない事実の記述で等級付けは pZ ⇒ 文言修正で解消。

## 3. pre-check（`/pre-check` sub-agent・本 turn）= BLOCK
- 7 issues（CRITICAL 1 = C1／HIGH 3 = H2・H1・H3／MEDIUM 3 = H5・M11・M12）。§0 不変前提の変更 = 0。run 要求 = 明示 0・**含意 1**（R3 as written）。
- 07-21 の p11 pre-check 3 件（forward design v0.2/v0.3/v0.4）は連続 BLOCK（`logs/pre-check-log.jsonl`）— 本件は別 design だが、当卓の pre-check 履歴として開示する。
- log 行 = 本 commit と同 turn で `logs/pre-check-log.jsonl` に追記（untracked file・schema は既存 entry と同じ）。

## 4. 手続記録
- [VERIFY] 事前 debate cycle 1 = **FAIL**。cycle 2 = v2 に対して pre-check ＋ 5 体を再走（上限 2）。
- court word の custody: `m-p11 -> p18` 08:25:24 JST・p18 transcript `1c3d805c-…jsonl:41542`（`type=user`・`2026-09-12T23:25:24.447Z`）。p4 は memory 行を「09-13 節: p11 court word ACCEPT」に更新済（当卓が MEMORY.md 差分で観測・09:0x）。
- v1 は本 commit で **FAIL 印つき**のまま bank（書き換えない）。v2 = 同 file の次 commit（履歴が v1 を保つ）。
