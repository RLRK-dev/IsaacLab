# Canonical 動作工程表 v1 — 43-step 基準 restate + 現行 route mapping

**Status: v1.0a-r2 — ✅ Rs-APPROVED(2026-07-11 00:15 verbatim「1 承認」、%12 bank `2b818b6f2f`; 承認世代 sha256 = `eb126d42…` @`764431035c`)+ 追補 r1(D-1 裁定執行)+ 追補 r2(§6 VN-1 reframe intake 登録、§5.6 flow、値不変)— 設計基盤 surface 発効。**
chain 完走: %10 author-review CONCUR(fold 済)→ %12 verify PASS(6 leg)→ Rs 承認。世代 chain: `bd1d9979f6`(v1.0 review 世代)→ `7f5d2716a9`(v1.0a fold)→ 本 status 反映 commit。**確定版 sha256 = 承認反映 commit の commit message に記録**(doc 内への自己 sha 埋込は self-reference で原理的に不成立のため、version⇄sha 束縛(P-3)の記録先は commit message / 台帳側とする)。
**未決の現況:** D-1 = ✅ **裁定済**(Rs 承認 00:29、§2 参照)/ P-1・P-3 charter 化 = **未決**(組込保留、継続)。
**Role note(Rs 2026-07-10 23:5x、%12 経由):** VT-DESIGN = **設計基盤(design-foundation)pane に昇格**。本 doc = 昇格第 1 成果物 = 設計 canonical surface(§5.6 governance 参照)。
**Gate(%12 裁定 2026-07-10 23:27):** L2。**v1 = 5体 waive(loud 記録)** — 理由: v1 は banked 済み内容(43-step 表 = Rs 確定 2026-03-28 + MOTION STANDARD)の restate+mapping で新規設計判断を含まず、最終 gate = Rs 承認 flow 自体。代償 = %10 author-review を %12 verify 前に挿入。**⚠ v2(工程の実変更 = slot/z_grasp/摩擦の fold)= L3 相当 + 5体必須**(本 doc §6 参照)。
Author: VT-DESIGN(w2:p5)。Drafted: 2026-07-10 23:32 JST。Node: T-ROOT-Verbal-Teaching-20260705。

---

## §0 目的・基準宣言(Rs directive + 訂正)

- **Rs 指示(2026-07-10 23:1x-23:2x、%12 経由 / banked `52cc4816fe` state.md:30):**「動作工程が毎回ぶれないように確定させる」— scripted route の動作工程を、実行のたびに再導出・変動しない確定版工程表(SSOT)として固定する。
- **Rs 訂正(23:5x、banked `c0f5aa67bc` state.md:30):**「vault の Design のステップ表が基準」— **新しい表構造を発明しない**。canonical =
  - **人間可読 SSOT:** `thread-vault/07-Design/RL-Routing-Design.md` **§2 工程設計(43ステップ)** `:1226`〜(確定 2026-03-28)
  - **機械 SSOT:** `thread_isaac_lab/data/waypoints/full_43step.json`(`RL-Routing-Design.md:2698`「full_43step.json が現行SSOT」; json 実物 = version 2、43 steps、`full_43step.json:2,4`)
- **本 doc の役割(v1):** ①43-step 表の restate(§1、vault 表 + json 実値の統一 view — canonical は上記 2 ソースのまま)②doc↔json 逸脱台帳(§2)③現行 production route の 43-step frame への mapping(§3)④ぶれ防止 = 表駆動構造の確認 + 逸脱検出提案(§4)⑤版管理規約(§5)⑥Rs 本日 3 指示の v-next 登録(§6)。
- **scope 注意:** 現行 production route(W0-e、mujoco-コ / env7、official SR 0.716)は **C1→C2 = 43-step frame の STEP 1-17 相当**(STEP 18「C2から上昇」は scope 終端につき未実行、§3 M-4)。STEP 19-43(C3-C5 + 復帰)は現行 scripted route 未実装領域。

## §1 Canonical frame restate(43-step 表 + json 実値の統一 view)

### §1.1 用語・状態定義(`RL-Routing-Design.md:1231-1239`)

| 用語 | 意味 | 値 |
|------|------|-----|
| Home高度 | ホーム位置・復帰高度 | z=1.12 |
| 上昇点(routing) | ルーティングクリップ上空 | z=1.07 |
| 上昇点(rest) | 置き台上空(Phase A approach/lift) | z=1.05 |
| 下降点(X) | X位置のテーブル面(GRASP_Z/PUSH_Z 相当) | z=1.02(json 実値 1.025 → §2 D-3) |
| **クランプ = full-clamp(摩擦固定)** | フィンガ閉(cable 把持)。**軸方向保持は form-closure + 摩擦**(→ §6 VN-3) | **0.002** |
| **半アンクランプ = half-clamp(滑り誘導)** | フィンガ半開き(cable 軽保持・誘導・しごき保持 `(h)` `:1408`) | **0.006** |
| アンクランプ | フィンガ全開(解放) | 0.04(json STEP 1 のみ 0.041) |

**clamp 二態の明示(Rs charter 要求):** full-clamp(0.002)= 摩擦固定状態、half-clamp(0.006)= 滑り誘導状態。state 値の SSOT は task_config.py にも同値で存在: `FINGER_CLOSE_POS=0.002 :277` / `FINGER_HALF_OPEN_POS=0.006 :276` / `FINGER_OPEN_POS=0.04 :274`。**現行 mujoco-コ substrate での同状態対応(driver 角):** open `GRIPPER_DRIVER_OPEN_RAD=0.0 :289` / half `GRIPPER_DRIVER_HALF_OPEN_RAD=0.69 :313`(human-CONFIRMED 2026-06-21)/ close `GRIPPER_DRIVER_CLOSE_RAD=0.7407 :291` — 状態意味論は substrate 世代を跨いで 3 態のまま保存。43-step 表の全 finger 遷移は CLOSED→半(HalfUnclamp)方向のみで、**半クランプ(OPEN→0.006)は表に対応 STEP なし(未割当、`:1064-1065`)**。Handover は独立 STEP なし(STEP 10→11 の TransportToClip に腕役割切替 R支配→L支配を内包、`:1062`)。scripted/RL 方式割当は `:1050-1060`(半アンクランプ/半クランプ = scripted 固定値、フルクランプ/フルアンクランプ = 純RL — RL-track の割当であり、本 scripted route では全て scripted)。

### §1.2 統一 43-step 表(vault 表 `:1284-1361` × json 実値;canonical は原本 2 ソース)

列: 表内容 = vault 表の動作、z_L/z_R・fing_L/fing_R = json 実値(target z [m] / finger [m])、クリップ状態 = vault 表。

| STEP | Ph | 動作(vault 表) | z_L | z_R | fing_L | fing_R | クリップ状態 |
|---|---|---|---|---|---|---|---|
| 1 | A | 初期位置(上昇点・原点) | 1.120 | 1.120 | 0.041 | 0.041 | - |
| 2 | A | ケーブル上空へ | 1.050 | 1.050 | 0.040 | 0.040 | - |
| 3 | A | ケーブルへ下降 | 1.025 | 1.025 | 0.040 | 0.040 | - |
| 4 | A | ケーブル把持(両手クランプ) | 1.025 | 1.025 | **0.002** | **0.002** | - |
| 5 | A | 持ち上げ | 1.050 | 1.050 | 0.002 | 0.002 | - |
| 6 | B | C1上空へ搬送 | 1.070 | 1.070 | 0.002 | 0.002 | - |
| 7 | B | C1へ押し込み | 1.025 | 1.025 | 0.002 | 0.002 | - |
| 8 | B | 誘導ハンド半保持(L半アンクランプ・R全開) | 1.025 | 1.025 | *0.006* | 0.040 | - |
| 9 | B | C1がcable固定 | 1.025 | 1.025 | 0.006 | 0.040 | C1 |
| 10 | B | C1から上昇 | 1.070 | 1.070 | 0.006 | 0.040 | C1 |
| 11 | C | C2上空へ | 1.070 | 1.070 | 0.006 | 0.040 | C1 |
| 12 | C | 左クランプ(ケーブル固定) | 1.070 | 1.070 | **0.002** | 0.040 | C1 |
| 13 | C | 右がケーブル再把持へ(R→cable) | 1.070 | 1.070 | 0.002 | 0.040 | C1 |
| 14 | C | 両手クランプ | 1.070 | 1.070 | 0.002 | **0.002** | C1 |
| 15 | D | C2へ押し込み | 1.025 | 1.025 | 0.002 | 0.002 | C1 |
| 16 | D | C2固定 | 1.025 | 1.025 | 0.002 | 0.002 | C1,C2 |
| 17 | D | 解放(L半アンクランプ・R全開) | 1.025 | 1.025 | *0.006* | 0.040 | C1,C2 |
| 18 | D | C2から上昇 | 1.070 | 1.070 | 0.006 | 0.040 | C1,C2 |
| 19-26 | C+D | C3 block(11-18 と同型: 上空→L固定→R再把持→両手→押込→固定→解放→上昇) | 同型 | 同型 | 同型 | 同型 | →C1-C3 |
| 27-34 | C+D | C4 block(同型) | 同型 | 同型 | 同型 | 同型 | →C1-C4 |
| 35-42 | C+D | C5 block(同型) | 同型 | 同型 | 同型 | 同型 | →C1-C5 |
| 43 | E | ホーム復帰(両手全開) | 1.120 | 1.120 | 0.040 | 0.040 | C1-C5 |

(STEP 19-42 の json 個別値は C2 block と数値同一パターン[上空 1.070 / 押込・固定 1.025 / L 0.002⇄0.006 / R 0.040⇄0.002]で 43/43 PASS — json 全行抽出で確認済。個別行は json 原本参照。)

### §1.3 セグメント対応・再クランプ手順(参照)

- STEP↔cable segment 対応表(全 43): `RL-Routing-Design.md:1405-1449`+(把持 seg: C1=26/34、C2=21/29、C3=16/24、C4=11/19、C5=6/14; groove: 30/25/20/15/10)
- 再クランプ 4 手順(C2-C5 共通、L固定 v2 追加): `:1272-1282`(R-hand X = L-hand X、R-hand Y = クリップ間中点[dry-run 固定値])
- クリップレイアウト(8 clips、千鳥): `:1249-1262`(SSOT = task_config.py CLIP_POSITIONS、Y 統一 v4 `:2710-2716`)

## §2 doc↔json 逸脱台帳(v1 で検出、黙って解決しない — %12/Rs 裁定待ち)

| ID | 内容 | doc 側 | json 側 | 備考 |
|---|---|---|---|---|
| D-1 | Phase A grasp X | v3 注記 `:2702`「X=0.30→0.15(REST_CLIPS 一致)」 | STEP 2-5 x=**0.30**(z は v3 値 1.05 を反映) | ✅ **裁定済(Rs 承認 2026-07-11 00:29、bank `cb4a416067`)**: 現行 = X=0.30 で確定、v3 注記側 = revert 済 stale。**訂正注記を RL-Routing-Design.md v3 注記直後に Rs 授権で追記済**(§5 規約 3 flow; file untracked につき provenance = 前後 sha を VT node bank に記録) |
| D-2 | 初期把持 Y span | §2.1 表 `:1378` C1: L+0.120/R+0.180(±30mm) | STEP 2-5 y=0.09/0.21(±60mm) | **3 世代値**: §2.1=±30mm / json=±60mm / **現行 runtime=±44mm(88mm span = INVARIANT #2、`GRIP_HALF_SPAN=0.044 :235`、`WIDE_LEFT_Y/RIGHT_Y=+0.106/+0.194 :268-269`)**。§6.3 既知 divergence `:2690` と同根。現行実効値は task_config が正 |
| D-3 | 下降点 z | 用語表 `:1236` z=1.02 | 下降/押込 z=**1.025** | 5mm 差。json が現行 SSOT |
| D-4 | §6.3 既知 divergence 残存 | 再把持Y = 中点固定 vs nearest query `:2692` / guide手選択 L固定 vs テスト選択 `:2693` | — | dry↔wet 世代の未解消項目、v1 では記録のみ |

## §3 現行 production route ↔ 43-step frame mapping

**基準実装:** `_run_mujoco_grasp_route`(`test_newton_clip_routing.py:3569`、以下 TNC; dispatch = main `:6893`→`:6954-6955`)。**⚠ legacy 同名関数は cite 禁止**(`_run_mujoco_grasp_episode :3007` / `_run_mujoco_grasp_engage_episode :3201` / `do_p1_grasp :2198` 等 — production docstring `:3579`「NOT a port of the legacy VBD path(先祖返り-fenced)」)。
**as-executed 条件(公式 81-grid):** ROUTE_ENV(`test_routeexec_byte_repro.py:72-87`; CLIP_X=0.35 / CLIP_Y=0.150 / CLIP2_X=0.40 / **CLIP2_Y=0.000**(Rs lever)/ S6_ENGAGE_YC=0.15 / CLIP_FLOAT_Z=0.020 / SEAT_TOPDOWN=1 / C2_DUALSEAT=1 / PERCLIP_PIN=1 / S13_ROUTE_C2=1)+ **FON_V1 pin**(`:88-95` = W0E_F1A=1 / **W0E_F1A_V2=0** / W0E_F1B=1 / **W0E_F1B_SNAPDOWN=1** / W0E_F2=1 / **W0E_F3=0**; shell 版 `w0e_81rerun_snapdown_runner.sh:22`)。⚠ **as-executed = F-1a v1 flat 降下 + F-3 OFF**(code default は両方 "1" — §4.1 gap (b))。W0E_LIFT_M は pin 外 = default 0.08。byte-id anchor = RUN1_REFERENCE_V2(`5f1c3f92…16cf`)。
**引用の鮮度:** TNC = working tree unmodified、commit `6808964dc3` と一致(2026-07-10 23:37 git status 確認)。

### §3.1 mapping 表(現行 phase 実行順 → 43-STEP)

| 現行 phase(TNC:line) | 43-STEP | gripper 状態遷移(as-executed) | 現行 pinned 値(source) | note |
|---|---|---|---|---|
| pre-setup: seeds+settle+座標導出(:3923-3999) | **1**(初期位置) | both OPEN 0.0(:3599) | seeds :3923-3924 / **caveat-a** GRASP_YC=mean(cable Y) :3942-3946 / **F-1b+snap-down** :3957-3974 / **fix-⑤** x_grasp :3985-3988 | **M-7**: 座標補正 = 実測 cable 由来(表は固定値)。coordinate-only = MOTION STANDARD 適合(LEDGER:44「fixes = coordinate-only on existing legs」) |
| GRASP_HOVER(:4011) | **2**(ケーブル上空へ) | both OPEN | z_high=1.1668(:3636) | M-6(z 世代差) |
| GRASP_DESCEND(:4016)8 legs | **3**(ケーブルへ下降) | both OPEN | **z_grasp=1.0668**(:3635 code literal「banked WR cradle」) | M-6: 表 1.025 の意味対応(下記) |
| GRASP_CLOSE(:4026) | **4**(ケーブル把持) | both OPEN→cage 0.66663(CAGE_FRAC 0.9 :4027)→**FULL 0.7407** | CLOSE=0.7407(TC:291) | 2 段 close = full-clamp 状態への sub-procedure(状態遷移は表どおり) |
| LIFT(:4048)12 legs | **5**(持ち上げ) | both FULL | **LIFT_M=0.08**(env W0E_LIFT_M :3642、z_lift=z_grasp+LIFT_M :3643) | LIFT_M = Rs 承認済 1 座標 lever(LEDGER:44) |
| ROUTE_C1(:4082)6 legs | **6**(C1上空へ搬送) | both FULL | N_ROUTE=6(:3647)、z_lift=1.1468 | 表 上昇点(routing)1.07 の意味対応 |
| C1_SEAT(:4213)8 legs | **7**(C1へ押し込み) | both FULL | seat_ee_z=GROOVE_CENTER_Z(0.809 TC:226)+CLIP_FLOAT_Z(0.020)+ee_off(:4214); as-executed = **F-1a v1 flat 降下**(:4306-4310) | F-1a comp = offset-gated(nominal 不変) |
| C1_PIN(:4342) | **9**(C1がcable固定) | 不変 | PERCLIP_PIN eq_active=1(:4379)、40 settle(:4385-4386) | **M-1 順序 swap**: production = 固定(9)→半保持(8)。pin = clip-retention kinematic の唯一許可例外([[feedback-clip-retention-kinematic-trick-authorized]]) |
| L_HALF_UNCLAMP(:4391) | **8**(L 半アンクランプ分) | **L FULL 0.7407→HALF 0.69**(ramp 0.0125 刻み :4396-4409) | HALF=GRIPPER_DRIVER_HALF_OPEN_RAD(TC:313) | half-clamp = 滑り誘導状態へ(cradle 判定 :4402,4414) |
| R_UNCLAMP_RISE(:4423) | **8**(R アンクランプ分)+ **10** の R 分 | **R FULL→OPEN 0.0**(:4427; code cite「43-step step8」:4418-4422) | rise +45mm 8 legs(:4439-4446) | **M-2**: rise は per-arm 逐次(表 = 両手同時) |
| GUIDE_C2(:4450)= setup | (10-11 準備) | 状態不変(R_hold 凍結 :4452-4453) | N_GUIDE=8(:4462); F-2 X-follow gate(:4483-4485) | `_ph` label 行(準備のみ、arm 移動なし)— conformance 期待列に含める |
| GUIDE_PRELIFT(:4489)= L prelift 8 legs + **guide traverse 8 legs(:4507-4521)** | **10** の L 分 + **11**(C2上空へ) | L **HALF 0.69 のまま(しごき = 滑り誘導の実体)**、R OPEN 凍結 | code cite「json steps 10-11」:4470-4476; _trav_z=+45mm(:4491); F-2 rate±8mm/cap 7mm(:4513-4516) | M-2: R は同行しない。**⚠ traverse は `_ph` 上 GUIDE_PRELIFT 配下で走る**(GUIDE_PRELIFT〜C2_REGRASP 間に別 label なし — grep 検証済) |
| pre-regrasp L(:4625-4647)10 legs | **12**(左クランプ) | **L HALF→FULL 0.7407**(:4645) | _z_above_d(:4629)、c2y−GHS lane | 表どおり。**`_ph` label なし(recorder 上 GUIDE_PRELIFT 配下)** — P-1 期待列生成時の注意点 |
| C2_REGRASP(:4675) | **13**(右がケーブル再把持へ)+ **14**(両手クランプ) | R OPEN→cage 0.66663(:4761)→**FULL 0.7407**(:4765) | **square-on C2_TILT_SIGN=0**(:4681、Rs-LOCKED ANTI-REVERT :4678-4681); _at_88 gate ≤20mm(:4750-4755); span-preserving c2y+GHS(:4664-4668) | **M-5**: 表 STEP 13 の R 位置 = クリップ間中点(dry-run 固定 :1282)→ 現行 = 実 cable +Y lane(§6.3 divergence「再把持Y」:2692 の現行解、Rs-LOCKED square-on) |
| C2_TRANSPORT(:4813)10 legs | **14** 内 sub-motion | both FULL | (c2x, c2y+GHS, _z_above_d)(:4817-4823) | **M-3**: 表に独立 STEP なし(表は再把持位置=最終 lane 前提; 現行は実 cable 把持→lane 位置合わせ) |
| C2_DUAL_SEAT(:4836)12 legs | **15**(C2へ押し込み) | both FULL | _seat_z_d(:4630); **F-3 = FON_V1 で OFF**(:4845) | top-down 両手 seat(C2_DUALSEAT=1) |
| C2_SETTLE(:4883)90 steps | **16**(C2固定)+ **17**(解放)相当 | **both FULL→OPEN 0.0**(:4886-4888) | _c2_settled = C2≤0.5mm ∧ groove±3mm(:4897) | **M-4 scope 終端**: 表 STEP 17 = L半保持(C3 継続用)→ 現行 = 両手全開(C1→C2 終端)。**C2 に pin なし = %10 code 反証確認済 CONFIRMED**(eq_active 書込 = 全 runner で :4379 の 1 箇所のみ; `route_c2_pin.json` :5075-5084 = metrics dump のみで eq 不触 = 命名 trap; LEDGER row43 Rs 決定 (c) C2 positive-retention DEFERRED と整合) |
| verdict+exit(:4951-5088) | (**18** = 未実行) | — | c2_seated_honest(:4971)、exit(:5088) | M-4: STEP 18「C2から上昇」= scope 外 |

### §3.2 z 意味対応(M-6)と遷移機構

- **z 世代差 = substrate 定数差、工程意味は保存**: 表 GRASP_Z 1.025 = TABLE+CLIP_BASE+**EE_TO_FINGERTIP 0.220**(TC:93、Franka 世代)⇄ 現行 z_grasp 1.0668 = TABLE+CABLE_RADIUS+**EE_TO_PINCH_CLOSED 0.2548**+0.008(コ-gripper 世代、routeexec node state.md:33)。runner 註 `:3679-3680`「GRASP_Z/PUSH_Z(task_config)は legacy P1-P4 path、route_c1_c2 は不使用 — route 降下 target = GROOVE_CENTER_Z+ee_off(動的)」。
- **遷移機構(全 ik_move_both leg 共通)**: 単発 IK + FK 関節補間、`n_steps = max(dist×100×STEPS_PER_CM×sf, 50)`(TNC:1960-1961、STEPS_PER_CM=50 TC:350、MAX_MOVE_STEPS=3000 TC:352)。**phase 遷移は全て固定 leg/step 数**(収束待ちループなし; converge_mm は ok-flag のみ)= 表の「遷移条件」に相当する暗黙値。
- **M-note 総括**: 順序 swap(M-1)/ per-arm 逐次化(M-2)/ sub-motion 追加(M-3)/ scope 終端差(M-4)/ 再把持位置の実測化(M-5)/ z 世代差(M-6)/ 座標補正層(M-7)。**いずれも MOTION STANDARD(LEDGER:44)適合の coordinate-only / sub-order 差**で、新 leg 発明ではない(発明 leg C1v2-LIFT/SHIFT/TRIM + F-3 は撤去/OFF 済 — LEDGER:44)。ただし M-1〜M-5 は「表 v-next で表側に正式反映するか」の Rs 判断対象(§6 統合方針)。

## §4 ぶれ防止 — 表駆動構造の確認 + 逸脱検出提案

### §4.1 事実確認(loud)

- **現行実行系は 43-step 表 / full_43step.json から直接駆動されていない**: production route = TNC 手書き逐次 phase block(in-code step table なし — grep 0 件; json への言及はコメントのみ `:4418-4422`, `:4470-4476`)。表↔実装の対応はこれまで暗黙 = ぶれの構造的根源。**本 doc §3 がその対応の初の明文化**。
- ただし「毎回ぶれない」は現状 **byte-レベルで達成**(4 装置): ①byte-id anchor = RUN1_REFERENCE_V2 三鍵(npz sha、`RUN1_REFERENCE_V2.md:3,5,15`)②**FON_V1 env pin**(as-executed flag 固定)③**Layer-A byte-repro 81/81**(抽出体 route_executor.py が locked runner を byte 再現、harness `test_routeexec_byte_repro.py`、LEDGER:47)④**MOTION STANDARD leg-diff detector**(`route_leg_diff.py`、invented-leg 検出実績、LEDGER:44)。
- **残存 gap(loud)**: (a) 表→実装 conformance が機械検査されていない(§3 は人手 mapping)(b) **code default ≠ pin**(W0E_F1A_V2 / W0E_F3 default "1" vs FON_V1 "0" — default-flip は Rs batch 済 park item、%12 banked `867625e9e1`)(c) 43-step json は Newton 世代値のまま(M-6 差は本 doc が吸収、json 側未改訂)。

### §4.2 逸脱検出の提案(proposal only、実装なし — §運用24)

| ID | 提案 | 基盤 |
|---|---|---|
| P-1 | **表 conformance check の機械化**: 実行 log の `_ph` 系列 + gripper 状態列を §3.1 mapping の期待列と照合(新 leg / 順序逸脱 / 状態逸脱 → loud FAIL) | 既存 `route_leg_diff.py`(LEDGER:44)の一般化 — 新規発明でなく実績 tool の拡張 |
| P-2 | **駆動一本化 = DESIGN_V1 St1a**(launch-wrapper が表 nominal → env params を export、runner は env 読み) | **既承認 staged plan**(DESIGN_V1:108、evidence-gated)— 新提案ではなく適用点の明記 |
| P-3 | **版管理連動**: 各表 version に byte-id anchor(基準 npz sha)を再宣言し、version⇄sha を 1:1 束縛。**束縛の記録先は doc 外(commit message / LEDGER 行 / 外部台帳)に置く — 自 doc への自己 sha 埋込は構造的に不可能**(埋込前 hash が入る; 実証 2026-07-11、`764431035c` で規約化。他 file の sha 埋込は可 = RUN1_REFERENCE_V2 型) | §5 規約 + RUN1_REFERENCE_V2 供給系 + %12 fold 指示 00:20 |

## §5 版管理規約(Rs charter、前 charter 継承)

1. **工程変更は表の新 version としてのみ**行う(ad-hoc 再導出・hand-edit 禁止)。
2. 各 version = **Rs 承認 + LEDGER 行**が発効条件。
3. 機械 SSOT(full_43step.json)と人間可読表(RL-Routing-Design.md §2)は**同一 version で同時更新**(§2 の D-1〜D-3 のような drift の再発防止)。07-Design 編集は Rs-専権につき、更新執行は Rs 授権 flow で行う。
4. 現行版 = **v2(json header `full_43step.json:2-4`)+ v3/v4 注記**(`:2701-2716`)。⚠ v3 の json 反映が部分的(§2 D-1)— 現行版の正確な同定は %12/Rs 裁定後に確定。
5. **v-next(工程の実変更)= L3 + 5体必須 + Rs 承認**(%12 gate 裁定 2026-07-10 23:27)。
6. **post-approval 追補の sub-revision 規約(採用 2026-07-11 00:2x、%12 提案・p5 判断):** Rs 承認後の editorial 追補(工程内容を変えない fold・注記)には **sub-revision label(v1.0a-r1, -r2, …)を付し、status 行に「Rs 承認世代 sha = どれか」を一意に保つ**。LEDGER 側は二層 sha(承認世代 / 現行)で記録(p6 伝達済)。本規約は次回追補から適用(今回分は changelog + commit message で追跡可能)。

### §5.6 設計基盤 governance(Rs role 昇格 2026-07-10 23:5x)

- **設計 canonical surface = 本 doc(+ その version 系列)を VT-DESIGN が保持**。
- **全設計変更の集約 flow**: COORD の study/probe 結果・%12 の verdict・Rs 指示 = **design 入力**として VT-DESIGN に集約 → §6 v-next 台帳に登録 → 統合された**新 version 提案** → %12 verify → **Rs 承認** → 確定版から実装(COORD)を駆動。
- 07-Design(canonical 原本 = RL-Routing-Design.md §2 + full_43step.json)は **Rs 専権のまま** — 本 doc は draft + Rs 承認 flow の作業面であり、canonical 原本の supersede ではない(承認された v-next は Rs 授権 flow で原本へ反映)。

## §6 v-next 登録 — Rs 設計指示 3 件(2026-07-10、実装なし・登録のみ)

**統合スタディ:** `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/SLOT_REDESIGN_STUDY_COORD_20260710.md`(COORD、paper only、`f8b1ff6b4c`)+ 機械証拠 `comp3_slot_zgrasp_geom_probe.py` / `_result.json`。**fold 規約: スタディ結論 → 単一 v2 提案として fold(z_grasp 変更 ⇒ 再録画必至 ⇒ F-B fork = MOTION STANDARD 再基準化、study `:89,114-115` — slot 変更と同一 fork に載せるのが正)→ L3 + 5体 + Rs 承認 + LEDGER 行。**

| ID | Rs 指示(banked) | 内容・現状 | 表への影響(見込み) |
|---|---|---|---|
| VN-1 | **slot 中央支持**(state.md:34、`f8cb48c2e8`)「ケーブルがたれないようにスロットの中央で支えられるように。空きはフィンガが入る部分だけで良い」 | study 実測: claw Y footprint 22.0mm/gripper、81-cell park-Y span 2.5mm → 必要 slot 幅 ≈28.5mm。提案 = 連続 void 120mm → 2-slot ≈29mm + 中央 SOLID ≈59mm。option S0/S1/S2 = **Rs 未決**。blast radius: base builder L3 + Rs-LOCKED test builder(F-B 授権要)+ void-parity banked 結果の supersession + C1 island overlap 要確認。**⭐REFRAME(intake 2026-07-11 01:10、%12 §5.6 flow):** slot probe = **INCONCLUSIVE 交絡**(COORD `c1a9d66523`)→ footprint 実測(`44aacb92a5`)で **slot-too-narrow root-cause = REFUTED**(full-assembly Y=22mm、2-slot が全軸 clear = 29mm slot は障害でなかった)。新仮説(**未解決**)= 中央支持が cable を unyielding 化 → flat-koshape の **scoop-cage 機構**(close で cable −6mm 押下げ + f1ext が下から hook)を阻害。**設計 tension = sag 除去 benefit vs scoop 阻害 cost** → 両立案の探索(支持高さを cable 静置面より下げ押下げ余地を残す / 把持窓だけ局所 void / scoop 非依存の把持形)が VN-1 の v2 fold 内容を左右。統合検討 = FLAT 深さ sweep 後(下記 統合方針)| scene 幾何変更(STEP 3-4/15 の把持・押込環境)。工程順序は不変見込み |
| VN-2 | **z_grasp +3-5mm(下降位置が低すぎる)**(state.md:33、`888e5e5623`) | 現行 z_grasp = **1.0668**(`route_executor.py:1114` / `test_newton_clip_routing.py:3246`; = TABLE+CABLE_RADIUS+EE_TO_PINCH_CLOSED+0.008)。**改善方向の符号は静力学から確定できず**、事前登録 probe sweep {+0,+3,+4,+5}mm に委譲(study `:51-54,113-114`) | STEP 3(下降点)の z 値変更 ⇒ **再録画必至**(録画 arm_q/ee_pos が z を内包、study `:89`)⇒ F-B fork |
| VN-3 | **摩擦固定**(state.md:31、`222e9a130f`)「クランプ時の cable-フィンガ間摩擦で cable をフィンガに固定する」 | %12 整理: コ型 form-closure は軸方向拘束なし・摩擦のみ → 「form-closure + 摩擦(axial)の複合、摩擦収支は実測が条件」。study 追加 leg = **friction budget 実測**(pad 法線力×μ vs pay-through 軸張力; lever = 法線力↑/μ↑/軸荷重↓=曲げ除去) | **full-clamp(0.002)状態の意味論強化**(§1.1 二態定義の full-clamp 側)。値・工程順序への影響は budget 実測後 |
| (VN-0) | 統一機構仮説 bend→pay-out(state.md:32、`20a94d19fa`)— 表変更でなく VN-1/2/3 の統一因果 | 「低すぎ → クランプ時に曲げ力 → 曲がった cable がすり抜け落ちる」。実測強支持: held-seg 曲率 env L 29.7° vs 録画 2.6°、push-down −6.0 vs −2.8mm(study §1 :25-29)。**falsification probe 事前登録済 → Rs GO 着地(2026-07-11 00:1x、COORD へ実行 dispatch 済)**(study §5 :117-129) | probe 解釈 grid(:125-127)が VN-1/2/3 の fold 内容を決める(いずれか cell 両腕 PASS → 仮説実証 + D-b 窓不要化の芽 / 全 fail → bend 非主因、D-b 窓設計復帰) |
| VN-4 | **trainer 駆動組成**(%12 role-昇格 message 2026-07-10 23:36 で v-next 群に指定) | canonical 事実(`COMP3_DRIVEPATH_DECISION_PACKET_COORD_20260710.md` + Rs 裁定 4 LEDGER:47): **D ρ=0 feedforward = scripted 検証段で採用**(armqdirect 実証機構、`route_executor.py` apply_recorded_arm_ff、cdac6b6972)。cage capture = **分岐点近傍プロセス**(sub-mm/sub-deg 駆動差で outcome flip、packet §2)→ option A 効果は実測でのみ実証可能。**どの slot-option でも D ρ=0(検証段)の価値は残存**(study §6 :138) | **表への直接変更なし(駆動 layer)**。ただし S1 成立時は trainer D-b 窓が不要化し得る(fork-(iv) 契約変更消滅、study :125-127)→ VN-1/2 の採否と相互依存。表 v2 には「駆動 mode 列(ik_chord / feedforward)を追加するか」が設計判断として付随(Rs 判断) |

### §6.2 design-input intake 台帳(§5.6 governance の第 1 回 intake、%12 転送 2026-07-10 23:38)

| 入力 | 内容 | 状態 |
|---|---|---|
| `SLOT_REDESIGN_STUDY_COORD_20260710.md`(`f8b1ff6b4c`) | 3 本柱統合 study(§1 仮説数値 / §3 slot 設計 / §4 z_grasp 変位表 / §5 probe 事前登録 / §6 decision 表 S0-S2 / §7 louds) | **直読済**(agent 抽出と数値照合 = 一致、§運用28)→ VN-0〜VN-2 に fold 済 |
| machine evidence: `comp3_slot_zgrasp_geom_probe.py`+result / `comp3_lane_floor_sweep.py`+result(81-cell)/ `comp3_drivepath_cost_probe.py`+result | built-model 爪実測・lane floor・cost+IK delta | pointer 登録(数値は study/packet 経由で fold 済; 一次 JSON は再実行可能) |
| `COMP3_DRIVEPATH_DECISION_PACKET_COORD_20260710.md` | drive-mode 系 canonical 事実(D ρ=0 採用、分岐点近傍、options 比較) | **§0-§3 直読済** → VN-4 に fold 済 |
| Rs 指示 4 件(state.md:30-34) | slot / z_grasp / 摩擦固定 / 工程表 charter | VN-1〜VN-3 + 本 doc 自体 |
| slot probe 帰結(intake 2026-07-11 01:10、%12 §5.6 flow; COORD `c1a9d66523` INCONCLUSIVE + `44aacb92a5` footprint 実測)| slot-too-narrow REFUTED → 新仮説 = 中央支持 vs scoop-cage 阻害の tension(未解決)| **VN-1 reframe に登録**(v-next 台帳、作業 = Rs 決定後)|

**統合方針:** VN-1/VN-2 は probe(study §5)の解釈 grid で fold 内容が確定 → **表 v2 は probe 結果後に単一提案として統合**(F-B 採用なら slot+z_grasp 同時 = MOTION STANDARD 再基準化 + 再録画; F-A なら scene 変更のみで表の座標行は不変)。S0/S1/S2 の選択 = **Rs 専権**(study §6)。VN-3(摩擦固定)は friction budget 実測 leg の結果待ち。VN-4 は VN-1/2 の採否と相互依存(D-b 窓の要否)。**v2 発効 = L3 + 5体 + Rs 承認 + LEDGER 行**(§5)。
**⭐intake 更新(2026-07-11 01:10):** slot probe が VN-1 root-cause(slot-too-narrow)を REFUTE → **VN-1 は「中央支持 vs scoop-cage 阻害」tension の未解決設計問題に reframe**。**正順(Rs 裁定 01:06)= FLAT scene 深さ sweep 先行**(COORD 実行中、= VN-2 の fold 材料)→ sweep 結果と slot reframe を **併せて統合検討**。∴ VN-1/VN-2 は now 相互結合(深さ軸が両者を跨ぐ)。COORD は表形式整形の協力可(%12 23:38)。

## §7 接地台帳(§運用4)

| ソース | 用途 | cite |
|---|---|---|
| RL-Routing-Design.md §2(:1226〜) | canonical 人間可読表 | 用語 :1231-1239 / STEP 表 :1284-1361 / §2.1 :1363-1403 / §2.2 :1405-1449+ / Handover・半クランプ注記 :1062-1066 / json SSOT 宣言 :2697-2699 / v3・v4 :2701-2716 / §6.3 divergence :2685-2695 |
| full_43step.json | canonical 機械 SSOT | version/changelog :2-4 / clip_positions :5-31 / steps 43 件(全行抽出で z・finger 値確認) |
| SLOT_REDESIGN_STUDY_COORD_20260710.md | v-next 3 指示の統合スタディ | 数値 :25-29,42-47,60-82,106-115 / probe prereg :117-129 / option 表 :131-138 |
| routeexec node state.md :30-34 | Rs 指示 verbatim + banked commits | `f8cb48c2e8` / `888e5e5623` / `20a94d19fa` / `222e9a130f` / `52cc4816fe` / `c0f5aa67bc` |
| 00-DESIGN-STATUS-LEDGER.md | **MOTION STANDARD**(p2r_c11、Rs-DECLARED 2026-07-05「この動作が基準だ」; **step-table-first: fixes = coordinate-only on existing legs、新動作追加 = Rs 専権**)= LEDGER:44。W0-e CLOSED 公式 0.716 / Layer-A byte-repro 81/81 / D ρ=0 採用 = LEDGER:47 | LEDGER:44, :47 |
| RUN1_REFERENCE_V2.md | byte-id anchor 三鍵 = npz sha256 `5f1c3f92…16cf`(:3、対象 = CLIP2_Y=0.000+LIFT_M 0.08 nominal :4、三鍵 %11/%9/%12 :5,:15)。⚠ LEDGER 行は ABSENT(CC tri-key freeze = precedent-with-caveat、DESIGN_V1.md:168) | w0e_offline_validation/RUN1_REFERENCE_V2.md |
| FON_V1 env pin | W0E_F1B_SNAPDOWN=1(公式 grid 実行条件) | BUILD_PLAN_ENVCORE_COORD_20260706.md:5 / p2_envcore_smoke_20260706_211613/PROVENANCE_PIN.md:7 |
| task_config.py | 状態値・幾何 SSOT | FINGER_{OPEN,HALF_OPEN,CLOSE}_POS :274-277 / GRIPPER_DRIVER_*_RAD :289,291,313 / APPROACH_Z=1.120 :92 / GRASP_Z=PUSH_Z=1.025 :93,95 / LIFT_Z=1.120 :94 / GRASP_X=0.30 :231 / GRIP_HALF_SPAN=0.044 :235 / CLIP_POSITIONS :211-217 / GROOVE_CENTER_Z=0.809 :226 |
| test_newton_clip_routing.py(TNC)@`6808964dc3` | §3 mapping の production 実装(working tree = commit 一致、23:37 確認) | `_run_mujoco_grasp_route` :3569 / dispatch :6893,:6954-6955 / phase 行は §3.1 表に個別 cite / W0E_* flags :3642-4845 / legacy fence :3579 |
| test_routeexec_byte_repro.py | as-executed env の機械定義 | ROUTE_ENV :72-87 / FON_V1 :88-95 / RUN1_REF :69 |
| SLOT_REDESIGN_STUDY_COORD_20260710.md | design input(直読 + agent 照合一致) | §1 :21-36 / §2 :38-54 / §3 :56-102 / §4 :104-115 / §5 :117-129 / §6 :131-138 / §7 :140-146 |
| COMP3_DRIVEPATH_DECISION_PACKET_COORD_20260710.md | VN-4 canonical 事実(§0-§3 直読) | fork-(iv) 契約 :12 / evidence grid :20-29 / 分岐点近傍 :31-40 |
| route_executor.py / newton_route_env.py(cdac6b6972) | D ρ=0 機構 | route_drive_mode NRE:458-474 / apply_recorded_arm_ff REX:3337-3388 |

## §8 Changelog

- v1.0-DRAFT(2026-07-10 23:32 JST): §0-§2, §5-§6 起草。§3/§4 = runner 抽出待ち。
- v1.0(2026-07-10 23:4x JST): §3 mapping(17 行 + M-1〜M-7)+ §4 ぶれ防止(4 装置 + gap 3 + 提案 P-1〜P-3)fold。§5.6 設計基盤 governance(Rs role 昇格 23:5x)+ §6 VN-4 + §6.2 intake 台帳追加。§2 D-1/D-2 に task_config 証拠追記。READY FOR %10 AUTHOR-REVIEW。commit `bd1d9979f6`(review 世代 pin、sha256 245fe334…)。
- **v1.0a-r2**(2026-07-11 01:1x JST): **§6 VN-1 reframe intake 登録**(%12 §5.6 design-foundation flow 2026-07-11 01:10)— slot probe(COORD `c1a9d66523` INCONCLUSIVE + `44aacb92a5` footprint 実測)が VN-1 root-cause「slot-too-narrow」を **REFUTE** → VN-1 = 「中央支持 vs scoop-cage 阻害」tension の未解決設計問題に reframe。正順(Rs 裁定 01:06)= FLAT 深さ sweep 先行(COORD 実行中、VN-2 材料)→ slot reframe と併せ統合検討 → VN-1/VN-2 相互結合。§6 VN-1 行 + §6.2 intake 台帳 + 統合方針を更新。**canonical 値・承認済 disposition は不変**(v-next 台帳への intake 登録のみ、作業 = Rs 決定後)。§5 規約 6 sub-revision。
- **v1.0a-r1**(2026-07-11 00:3x JST): **D-1 = Rs 裁定「承認」執行**(00:29、bank `cb4a416067`)— RL-Routing-Design.md v3 注記直後に訂正注記を Rs 授権追記(現行 X=0.30 確定 / Z=1.05 有効 / 裁定記録 = 本 doc §2 D-1)。provenance(file untracked): 編集前 sha `02bbedcfef0b143f…`(%12 独立取得と EXACT)/ 編集後 sha = VT node bank + commit message に記録。§2 D-1 行 = 裁定済化。**sub-revision label 初適用(§5 規約 6)**。
- P-3 規約化 fold(2026-07-11 00:2x JST): %12 執行 verify PASS(00:20)+ directive fold — P-3 に「version⇄sha 束縛は doc 外(commit message / LEDGER 行)に置く」を規約として明文化(self-referential sha 教訓)。FYI 受領: RL-Routing-Design.md = git untracked 判明、tracked 化は %12 が Rs 提起中(§5 版管理規約に関係 — 着地待ち)。
- v1.0a Rs-APPROVED 反映(2026-07-11 00:17 JST): **Rs 承認(00:15「1 承認」、%12 bank `2b818b6f2f`)→ status 確定化 + 設計基盤 surface 発効。** D-1 = 未裁定のまま §2 現状維持(Rs 指示②)/ P-1・P-3 charter = 未決・組込保留(同③)/ VN-0 probe = **Rs GO 着地、COORD 実行中**(結果は §6 解釈 grid 経由で v2 fold 入力)。%12 verify = PASS 6 leg(23:55、非重複独立検証)。
- v1.0a(2026-07-10 23:5x JST): **%10 author-review = CONCUR w/1 MED + 2 LOW(23:48、sha EXACT 照合)fold。** MED: §3.1 の `_ph` label 系列を実系列に一致化 — GUIDE_C2(:4450 setup)行を独立化 + guide traverse は GUIDE_PRELIFT 配下(:4489〜:4675 間に別 label なしを grep 再検証)+ pre-regrasp L に「label なし(GUIDE_PRELIFT 配下)」注記(P-1 conformance 期待列の false-FAIL/PASS 防止)。LOW: seed cite :3600→**:3599** / C2_TILT_SIGN :4683→**:4681**(両方 grep 再検証済、§運用28)。C2-pin なし = %10 反証確認 CONFIRMED を M-4 行に反映(命名 trap 注記 + LEDGER row43 整合)。%12 verify READY。
