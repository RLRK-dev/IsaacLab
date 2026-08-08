# P11 設計 spec — C-2 mounting の実装設計（cell 幾何・設計のみ）

desk: p11 ARM-CONTROL-DESIGN (w2:p11) / 起草 **2026-08-08 21:22:01 JST**・**v2 改訂 21:50:11 JST**（5 体 debate 反映・`date` 実測）/ session `aeef3995`
commission: **m-p18-91**（p18 経由・出所 = Rs 逐語「中間目標を達成せよ」→ p4 kickoff `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` §4 回付）
⛔ 本 file は**設計**。code / env / spec / asset の編集を含まない。実装 = p0（pathspec 限定）→ 検証 = pZ → まとめ = p4。**本 spec の bank は canonical 採用ではない**（07-Design / 04-Specs は Rs 専権・p11 は提案として bank する）。

---

## 0. コミッションの範囲と、この設計が動かさないもの

- **決定済みの入力（本 spec は再決定しない）**: mounting = **C-2**（spread 0.280 / tilt 20°・crown 0.110 不変）。決定 = p4・Rs 委任下（Rs 逐語「君が判断していい」）・custody = `P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` §2。本 spec の仕事は **C-2 を実装可能な形に落とすこと**であり、mounting の選び直しではない。
- **動かさないもの**: §0 不変前提のすべて（DUAL-ARM / 指令 88 mm / DiffIK-only / コ字 gripper LOCK / no-kinematic-trick）・task 幾何（clip 位置 C1/C2・REST 列・cable 諸元）・`task_config.py` 全行・04-Specs / 07-Design・制御方式。
- **実行しないもの**: 訓練・two-key・probe launch。chain の DoD（43-step scripted route 動画・裁定 A = `00-DESIGN-STATUS-LEDGER.md:39`）は p0 実装と pZ 検証の先にある。

## 1. 変更点（p0 が実装する 4 点・2 file）

対象 file = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/` の `ur15_cell_spec.py`（live 定数面。live driver `ur15_steps_wired.py` はここから import — `:43-52`）と `sweep_mounting.py`（計器 label のみ）。

| # | 定数/対象 | 現行（built） | C-2 | 編集行 |
|---|------|------|------|------|
| 1 | `YOKE_SPREAD` 既定 | `0.22` | **`0.28`** | `ur15_cell_spec.py:358` の最終 else |
| 2 | tilt 既定 | `45.0` | **`20.0`** | 同 `:374-375` の最終 else（数値 token のみ置換 — 併記 comment は `_YOKE_SPREAD_SUPERSEDED` 系の履歴文で不触） |
| 3 | `CROWN_R` 既定則 | `YOKE_SPREAD / 2`（=0.110） | **literal `0.110`**（導出則を廃し pin） | 同 `:432` の最終 else（`:426` の注記も更新） |
| 4 | 計器 label（sheet (a)/(z) の fallback 表示文字列） | `"0.220 (built default)"` / `"45 (built default)"` | **`"0.280 (C-2 default)"` / `"20 (C-2 default)"`** | `sweep_mounting.py:169-170`（**label のみ・挙動不変**） |

- 変更 3 は値の変更ではなく**規則の変更**: built では `YOKE_SPREAD/2 = 0.110` と literal `0.110` が偶然一致するが、spread 0.280 では導出則が **0.140 = 一度も測られていない cell** を作る（grid は crown ∈ {none, 0.110} のみ測定）。witness は `CROWN_R_OVERRIDE=0.110` で測られた（`sweep_mounting.py:294-295`・literal `float("0.110")` と bit 同一）。**測られた cell を既定にする = radius を literal に pin する**。
- **override 優先順位は不変**（`CROWN_R_OVERRIDE` > `CROWN_Z0_OVERRIDE` 導出 > 既定。`ur15_cell_spec.py:429-432` の 4 分岐構造保持 — 最終 else のみ置換）。過去 sweep は環境変数で従来どおり再現可能。⚠ built 再現が「0.110 = 0.22/2 の偶然一致」で成立している点は §7-3 に明記。
- 変更 4 の理由: 既定変更後、override なしの sheet (a)/(z) 実行は **C-2 cell を測りながら行 label に built を印字する**（`sweep_mounting.py:169-170` の fallback 文字列・header/各行/ログ file 名に伝播）。計器自身が「どこで測ったかは表の一部」と書いている（同 `:164-168`）ため、label を既定に一致させる。⚠ 一般欠陥として残る: **この label は既定を変えるたび手で追随が要る**（comment にその旨を書く）。同種の stale 文（`sweep_mounting.py:258/:288`・`compare_24_vs_24.py` 系の歴史記述）は挙動に効かない歴史文 — 変更 4 と同 commit での注記更新は任意。
- crown の**長さ**は `fromto ±YOKE_SPREAD`（`ur15_steps_wired.py:183-184`）で spread に自動追随 — 編集不要・witness と同一構造。
- **コード上の導出は `:432` の 1 箇所のみ**（`ur15_steps_wired.py` に再導出 0 件 = grep 実測）。文言参照は `:426`（注記・更新対象）・`:418`（p5 floor の履歴文・不触）・`sweep_mounting.py:258/:288`・`compare_24_vs_240.py:78`（print 文言・歴史）。
- 提案 comment（p0 が付ける根拠行）: 「C-2 settle = `P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` §2（Rs 委任）・witness = `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt:54`・crown 0.110 は写真由来のまま pin（#60）・条件 = #54 部材入力確定後に部材込み再測」。既存の built 由来注記（Rs 供給 cell `ur15-dual-arm-cell.md` 0.22/45 = `:359-362`）は**履歴として保持**（消さない）。
- **p0 の編集順序**: comment 挿入で行番号がずれるため、**内容で行を特定し file 末尾側から編集**（:432 → :374-375 → :358 → sweep_mounting）。

## 2. 前提の整理（§0#2 の 2 主張面 と flag の継承）

- **指令スパン 88 mm は不変**: `task_config.py:235` 逐語 `GRIP_HALF_SPAN = 0.044 …(commanded arm-to-arm span = 88mm)`。cell spec は同行を import（`ur15_cell_spec.py:60`）。witness は「**指令 88 mm で分離した pose pair**」として測定されている（`GRID240_READING_20260802.md` §4）。
- **#58 継承（語の規律）**: 実際に握られる最近傍 link 間隔は **75 mm**（link pitch 15 mm の量子化床・`00-DESIGN-STATUS-LEDGER.md:162`）。本 spec で「88」は常に**指令**を指す。mounting 変更は link pitch に触れないので、この量子化は C-2 でも同一に残る。
- **#45 継承（条件）**: §0#2 88→176 の報告は **on-disk 未着地**（`:153`）。本 spec は on-disk 88 で設計する。⛔ **もし Rs が 176 を着地させたら、C-2 witness は無効化される**（指令 88 の pair で測った existence ゆえ）— その時は C-2 列を新スパンで再測（KINONLY driver ~100 s/point 級・grid 1 列で安価）。
- **§0#2 の「bases fixed at Y=∓0.35」**（`RS71-System-Spec-SSOT.md:24`・根拠 = `task_config.py:21-22`）は **PhysX 面の座標**。UR15 mujoco cell の取付は **Tier B**（`ur15_cell_spec.py:346`「no authoritative source; the spec carries these」）で、ground = Rs 供給 cell 定義（`ur15-dual-arm-cell.md` 0.22/45・`:359-362`）— その supersede が今回の C-2 settle（Rs 委任下）。⚠ standing rule は不変: **本 mounting 変更を §0 premise 変更と読む読みが出たら、その場で STOP → p4 経由 Rs**。本 spec は §0 の premise をどれも変えない（判定 = role brief `ARM_CONTROL_DESIGN_ROLE_BRIEF_p11_20260721.md:52` の基準で自問済み・debate CC4 Q1 も独立に同判定）。
- **#54 継承（条件・⚠ v2 で数値訂正）**: 柱と腕取付の間に部材が無い。**built (0.22) では 0.220−0.102 = 0.118 m・C-2 では 0.280−0.102 = 0.178 m ⇒ C-2 は無支持 span を +60 mm 拡げる**（片持ち量 = spread − COLUMN_R・§3.2 S3 と同方向に厳しくなる）。⛔ 旧記載「built で 0.298 m」は誤り — 0.298 は **退役 0.40-spread cell の数**（LEDGER `:158` が as-read `YOKE_SPREAD=0.40` で導出・現 `_YOKE_SPREAD_SUPERSEDED = 0.40` = `ur15_cell_spec.py:373`）。部材入力は未決（Rs/p4 court）。**C-2 は「部材入力確定後に C-2 列を部材込みで再測する」条件を負って立つ**（settle §3 逐語）。⚠ #54 帰結 3（計器が新部材を黙って除外する）は部材 task 側に carry — pZ 項目 7 に計器 scope の確認を置く。
- **stereo head 不在条件（v2 追加・debate CC2 発見）**: 参照 cell は yoke 中央に stereo head 障害物（0.24×0.085×0.075 m @ (0, −0.175, 1.485)・roll 135°）を宣言するが、model は**既定 OFF**（`STEREO_HEAD` env 未設定時・`ur15_steps_wired.py:187-206`・`:1232` `_EXCUSED`）。**driver 自身が「欠けた障害物は成功を現実より易しくする = non-conservative」と明記**。⇒ **本 witness と全 clear 数は「stereo head 不在 cell」の主張** — #54 部材と同型の条件として carry（§3.5a・§7-12）。
- **#48 継承（DoD grade cap・disposition = Rs）**: 本 chain が走らせる **MuJoCo cell**（`ur15_steps_wired.py`）の cable は 1 link あたり蝶番 2 本（`cab{i}_y`+`cab{i}_z` = `ur15_steps_wired.py:233-234`・LEDGER `:146`）— **banked 前提（RS71 §4 B2・現 on-disk `:69`（row #48 は `:67` と pin・行がずれている）・Newton cell の 1-DOF planar bender・B1「world-Z DOF 追加」は declined）が名指しで却下した第 2 DOF**。⛔ 前提側の対象は Newton cell・偽なのは MuJoCo cell — **引用時は必ずどちらの cell かを添える**（`:146` 訂正 A の実務帰結）。⇒ **cable 由来の主張は #48 併記なしに引用しない・#48 open の間、DoD 動画に無印 PASS を出さない**（受入報告に射程明記・kickoff 訂正 `405bf8ce81` 逐語）。本 spec の変更は cable 構造に触れない（DOF 追加も除去もしない）。
- **#49 継承（整定ゲート・判定 = p11/実装 lane）**: wired 系 driver は相の整定ゲート未到達を自己申告した実績がある（`r6_positive_pair_result.txt:37`「numbers below are from moving arms」・原因 = 07-28 12:4x 時点で未確定・LEDGER `:147`）。**gate 後の量に接地する verdict は未整定を継承する**。⇒ 本 spec の disposition は §5b。先行 1-packet 裁定 = `P11_UR15_DESIGN_DISPOSITION_20260727.md` §27.2.108（@ `de0d29f2b6` 時点）。
- **#61 継承（版 pin）**: 版を言う全 evidence の接地点（LEDGER `:165`・RESOLVED・freeze sha256 `f700f94f8b56…`）。witness 数値は **mujoco 3.10.0 系 env7** で測られた。⚠ 同行の実測: mujoco 版更新で `mj_geomDistance` が cell 上 non-conservative 方向（接触棄却→空き受理）に動いた ⇒ **clearance 系の再測・pZ 検証は同一 env7 pin（newton 1.4.0 / mujoco 3.10.0 / mujoco-warp 3.10.0.3 / warp 1.15.0）下で行う**こと自体が条件。
- **#39 STOP tripwire（動力学定数の境界）**: 本 spec は**幾何・運動学 clearance で閉じる**。UR5e 由来の動力学測定（H-2/H-3/H-4 = τ_bias・Jacobian・damping）は UR15 へ流用不可・**廃棄範囲は未確定**（LEDGER `:143`・p6 は範囲推定を拒否）。⇒ **設計が動力学定数に手を伸ばした瞬間 STOP → p4 経由 Rs**（注記して通過する類ではない・m-p18-95 §5）。本 spec は PD gain・damping・質量等に一切触れない。
- **#18 注記**: grip-efficacy は本 chain の route 把持レグへ収束する未解決 FOUNDATIONAL（p5 chain 進行中・kickoff 訂正 2 項）— 受入報告の射程注記に含める。

## 3. /geometric-design 出力（強制ゲート）

### 3.0 Step 0 — 機構問い直し（ONE pass・bounded）

1. **そもそも mounting 変更は必要か** → 必要。built (0.220, 45°) の左腕 clear = **0/240**（solved 58 → clear 0・`GRID240_READING_20260802.md` §1）。sample を 10 倍にして solved は 8 倍伸び clear は動かない = **cell の性質**であり draw 数の問題ではない。
2. **安価な代替（salvage）はあるか** →
   - 開始姿勢の選び直し（cell 不変）: 上記により**不成立**（clear が存在しない）。
   - task 幾何を動かす（family A）: settle が却下（把持中心/作業列を汚し DDR #40 の p5 再導出と絡む・`P4_DELEGATED` §2-5）。
   - crown を縮める/消す（family B）: crown 0.110 は写真由来の最弱接地数（#60）— 「頭を縮めて built に合わせる」は測定への忠実性を消費する。settle が「頭に耐える取付を選ぶ」側を採用（§2-3）。crown 無しは Rs が 3 度 directed した参照形状（Y 字 + 頭）に反する。
3. **下流ステージが実リスクではないか** → 下流（route 段の経路衝突）は実リスクだが、**開始 clear が存在しない cell では route 段に到達すらしない**。witness は必要条件の確立であり、route 段は DoD 動画 + pZ が受け持つ（§3.5c・§7）。
⇒ build は正当・scope は最小（定数既定 3 値 + 計器 label 2 行）。sim を要する分岐は launch せず §7 に FLAG。

### 3.1 Step 1 — 実測（全て banked 実測・本 session 直読・debate CC2/CC3 が独立再検証）

| 量 | 値 | 出所 |
|---|---|---|
| built (0.220, 45, crown 0.110): L solved / L clear | 58 / **0**（240 draws） | `GRID240_READING_20260802.md` §1 |
| C-2 (0.280, 20, crown 0.110): L solved / **L clear** | 106 / **5** | `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt:54` |
| C-2: R solved / R clear | 122 / 30 | 同 `:54` |
| C-2: 両腕最近接 gap（選択 pair） | **+14.7 mm** | 同 `:54` |
| 表の `(7 <-> 46)` の意味 | **interleave を測った最近接 geom 対の表示**（`arm_pair_min(want_who=True)` = `ur15_steps_wired.py:2346-2360`）。⛔ **pose pair の識別子ではない**（同表示が (0.340,20) 行にも現れる・pose の joint 値は /tmp ログ消失で**再現不能**） | 同 `:54`/`:57`・`sweep_mounting.py:124-128` |
| 取付点 | `pos=[±YOKE_SPREAD, 0, 1.53]`・`quat=Ry(sign×TILT)` | `ur15_steps_wired.py:297-298` |
| tilt 変換式 | `TILT = π/2 − radians(tilt_deg)` ⇒ built 45°→Ry(±45°)・C-2 20°→**Ry(±70°)**（外向き） | `ur15_cell_spec.py:374-375`・供給 cell 左基部 = Ry(−45°)（`ur15_steps_wired.py:291`） |
| crown 実装 | capsule `size=CROWN_R, fromto=(−YOKE_SPREAD,0,CROWN_ZC)→(+YOKE_SPREAD,0,CROWN_ZC)` | `ur15_steps_wired.py:183-184` |
| CROWN_Z0（下面）/ CROWN_ZC（軸） | 1.330 / CROWN_Z0+CROWN_R | `ur15_cell_spec.py:428` / `:434` |
| SHOULDER_HEIGHT / COLUMN_R | 1.53 / 0.102 | `ur15_cell_spec.py:349` / `:401` |
| 指令スパン | 0.044×2 = 88 mm（commanded） | `task_config.py:235`（本 session 直読） |
| cable 半径 | 0.004（live 面は SSOT import） | `task_config.py:137`・`ur15_cell_spec.py:52` |
| **測定の cell 条件** | **stereo head 不在（既定 OFF・non-conservative と driver 明記）・#54 部材不在** | `ur15_steps_wired.py:187-206`/`:1232` |

### 3.2 Step 2 — 制約

**ハード制約（違反不可）:**
- **H1 左腕 clear 開始姿勢の存在**（witness 必須）— built ❌ / C-2 ✅（5 witness）
- **H2 右腕 clear 開始姿勢の存在** — 全 cell ✅（grid 最小 5・`GRID240` §6）
- **H3 選択 pair で両腕非干渉**（gap > 0・指令 88 mm で分離した pair）— C-2 ✅ +14.7 mm
- **H4 crown が mount を担ぐ**（head top = CROWN_Z0 + 2·CROWN_R ≥ SHOULDER_HEIGHT）— pinned 0.110: 1.330+0.220=**1.550 ≥ 1.530** ✅（margin +20 mm）。p5 §26-3（届かない頭は何も担がない・`ur15_cell_spec.py:420-424`）を満たす
- **H5 task 幾何不変**（clip C1/C2・REST 列・cable 諸元・指令スパン）— C-2 は cell 側で閉じる ✅
- **H6 形状は Rs 参照形**（Y 字 + 頭。crown 除去 cell は計器であって建てる形ではない・`ur15_cell_spec.py:352-354`）

**ソフト目標:** S1 gap margin 最大化 / S2 witness 数（頑健性）最大化 / S3 built からの逸脱最小（**片持ち量 = spread − COLUMN_R は spread に単調に厳しくなる**: built 0.118 m → C-2 0.178 m） / S4 crown 半径不確かさ（#60 写真由来）への頑健性。

**有効設計空間**: grid 24 点中 H1∩H2∩H3 を満たすのは 4 点、H6（crown あり）を課すと **2 点**（C-2 と (0.340, 20)）。設計空間は離散 2 点 — 「狭い」が、これは**測定済み existence の集合**であり連続幅の脆弱性とは意味が異なる（240 draw の existence・`GRID240` §7-3）。⚠ grid の外は無主張。

### 3.3 Step 3 — 断面図（x–z 面・y=0・単位 m・目盛りは主要 z のみ）

```
z[m]        built (±0.220, Ry±45°)                C-2 (±0.280, Ry±70°)
1.550 ─      ┌── crown top ──┐                 ┌──── crown top ────┐
1.530 ─   ●══╪═══════════════╪══●           ●══╪═══════════════════╪══●   ← mount ±YOKE_SPREAD
1.440 ─   ───┼─ crown 軸 ────┼───           ───┼─ crown 軸(=1.440) ─┼───   ← capsule fromto ±spread
1.330 ─      └── crown 下面 ─┘                 └──── crown 下面 ────┘     ← CROWN_Z0
            │ column r=0.102 │                  │ column r=0.102 │
            │ (stem 0.37→1.53)│                 │  柱端→mount の空き │
            │                 │                  │ 0.280−0.102=0.178  │    ← #54 部材 zone（未決・built は 0.118）
0.800 ─  ▓▓▓ table top ▓▓▓（y=REST_Y=0.28 側・task 面・不変）▓▓▓
0.000 ─  floor
   mount 軸回転: built Ry(sign×45°) → C-2 Ry(sign×70°)（=90°−tilt_deg・外向き）
   ⚠ 紙面の横方向は x。REST_Y の「0.28」は y 座標であり spread 0.280 とは無関係（偶然の同値・混同注意）
   ⚠ stereo head 障害物（(0,−0.175,1.485)・既定 OFF）は本図に無い = witness cell にも無い（§2）
```

crown: 半径 0.110 pin・長さは ±spread 追随 ⇒ C-2 では「同じ太さでより長い頭」= witness が測った形そのもの。導出則のままだと C-2 で r=0.140（頭が太る）= **未測 cell** ❌。

### 3.4 Step 4 — トレード表（H を満たす候補のみ。H❌ は除外し注釈で残さない）

| 案 | crown | spread | tilt | L clear | R clear | gap | H1-H6 | 評価 |
|---|---|---|---|---|---|---|---|---|
| **C-2 ★settle 済** | 0.110 | 0.280 | 20 | **5** | 30 | +14.7 mm | 全✅ | S2 優位（witness 5 vs 2・⚠ 数は pair/sample 依存 — `GRID240` §4/§7-3・順位の根拠は settle が別途持つ）・S3 最良（built に最近接 = 片持ち 0.178 m）・S4 実証あり（r=0.075 でも witness・`CROWN_SWEEPS_240_READING_20260802.md` §crown×tilt） |
| 対抗 | 0.110 | 0.340 | 20 | 2 | 34 | +15.3 mm | 全✅ | gap +0.6 mm 優位のみ。S3 劣後（片持ち 0.238 m・crown さらに長い） |

除外（H 違反・sheet 別）: **built crown-0.110 sheet (0.220,45) = H1❌**（L clear 0/240）・**built crown-none sheet (0.220,45) = H3❌**（L clear 3 だが interleave・KINONLY 表 `:37`。H6❌ でもある）。crown-none の 2 PASS 点 = H6❌（計器 cell・Rs 参照形でない）。残る 18 点 = H1 または H3 ❌（`SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt` 全行）。
⇒ **C-2 は crown あり 2 候補中 S3/S4 で優位 — settle 済決定と測定が同じ側を指す**（本 spec は追認であって再決定ではない）。

### 3.5 Step 5 — 物理妥当性・感度・連動・因果連鎖

**5(実機成立性)**: 取付 3 値はどれも物理的に構築可能な剛体幾何（回避策・contact 無効化・貫通に依存しない）。⚠ 強度は未設計のまま carry: p5 は片持ち枝の margin「at or below zero」と明言（`ur15_cell_spec.py:410-411`・crown 形でも spread 拡大は同方向に厳しい — **C-2 は無支持 span を built 比 +60 mm 拡げる**）。部材（#54）settle 時に強度と一緒に入る。sim 内の本 spec 範囲では構造は静的 geom（質量なし scenery・`material="col"`）ゆえ動力学に入らない — **「強度 OK」を本 spec は主張しない**。

**5a 感度分析:**

| 変動要因 | 幅 | C-2 での帰結 | 判定 |
|---|---|---|---|
| crown 半径（#60 写真由来） | −0.035（r=0.075） | witness 存続（`CROWN_SWEEPS_240` §crown×tilt 実測） | ✅ |
| 同上・増側 | r>0.110 | **未測**。導出則なら 0.140 だが C-2 は pin ゆえ晒されない | FLAG（測るなら KINONLY 1 点） |
| draw 数 | 240→それ以上 | existence は単調（増えて消えない）。count は無主張（`GRID240` §7-3） | ✅ |
| #54 部材の挿入 | 未決入力 | 計器は現状部材を持たない ⇒ **witness は「部材なし cell」の主張**（無支持 span は C-2 で +60 mm 広い）。再測条件で carry（§2） | ⏸ 条件 |
| **stereo head の装着** | 既定 OFF → ON | **未測（non-conservative 方向の欠落と driver 明記）**。witness は不在 cell の主張。装着時は C-2 点の再測が要る（KINONLY 1 点・`STEREO_HEAD` env で装着可） | ⏸ 条件 |
| §0#2 指令スパン | 88→176 未着地 | pair 分離条件が変わり witness 無効化 ⇒ 再測条件で carry（§2） | ⏸ 条件 |
| 開始姿勢 sample の別 draw | pair 依存 | fail 行は refutation でない一方、**PASS は 1 pair の witness**（`GRID240` §4）。gap 値は pair の性質 | ✅（読み方の規律） |

**5b 連動パラメータ:**
```
YOKE_SPREAD 0.22→0.28 ──→ crown 長さ（fromto ±spread・自動追随・編集不要）
                      ├─→ mount x（±spread・自動）
                      ├─→ _SHOULDER → ARM_REACH → TRACK_TOL（`ur15_steps_wired.py:436-441`・自動追随・witness は同経路で測定済）
                      ├─→ #54 部材 zone 幅 0.118→0.178 m（記録のみ・部材未決）
                      └─→ CROWN_R 導出則（× 追随させない = 変更 3 で pin。これが唯一の手動連動）
tilt 45→20 ──→ mount quat Ry(±45°)→Ry(±70°)（自動）
CROWN_R pin 0.110 ──→ CROWN_ZC = 1.440（自動・:434）──→ head top 1.550・H4 ✅
計器 label（変更 4）──→ sheet (a)/(z) の header/行/ログ名（手動・label のみ）
非連動（触らない）: SHOULDER_HEIGHT / COLUMN_R / CROWN_Z0 / REST_Y / REST_X / C1・C2 / TABLE_* / GRIP_HALF_SPAN / CABLE_* / HOME_POSE / TILT_CAL_DEG（姿勢較正公差・mounting TILT と無関係）
```
（camera は `m.stat.center/extent` 追随 = `ur15_steps_wired.py:2736-2737`・hardcode なし — debate CC5 traced clean）

**5c 動的因果連鎖（5 step）:**

| Step | 状態/イベント | 応答 | 問題 |
|---|---|---|---|
| 0 | 既定 build = C-2 cell | witness 測定時と同一幾何（override 経路と同値・literal bit 同一） | — |
| 1 | driver が開始姿勢を draw（240） | L clear ≥1 期待（witness 5 実測）。**0 なら fallback 行が出る — その run は route evidence にならない**（§5-2 手続バー） | — |
| 2 | 43-step route 実行 | 開始 clear ≠ 経路 clear（`GRID240` §7-1）。経路衝突は残リスク → DoD 動画 + pZ + Rs human-GT が受ける | ⚠ carry |
| 3 | clip への配索 | task 幾何・clip（権威 V-groove）不変 ⇒ mounting 変更の影響なし | — |
| 4 | crown/柱との干渉 | 開始時は witness が保証。経路中は step 2 と同じ carry。部材/stereo head 追加時は再測（§3.5a） | ⚠ carry |
| 5 | DoD 動画 → Rs 判定 | 数値で動画を上書きしない（検証順序 動画→ログ→照合） | — |

❌ なし・⚠ 2 件はいずれも本 chain の既設 gate（pZ・動画 DoD・Rs human-GT）が受け皿。訓練報酬系は本 chunk に無い（scripted route）。

**5d 軸分解保持検証**: N/A — 本変更は把持・保持幾何に触れない（gripper LOCK・clip 権威実装不変）。保持系の主張を本 spec は一切しない。

## 4. #46 disposition — 実射程は cell 定数 21 件・解消形は「SSOT 直結経路」で、C-2 実装面はその経路そのもの

- **実射程（kickoff 訂正 3 項・LEDGER `:150` フル読み）**: #46 = clip 1 件ではなく **cell 定数 21 件（物理を変えるもの 10 件）の齟齬** — 実例 4 分裂 = clip 高さ（0.070/0.026）・cable 半径（Ø10/Ø8）・質量（1.78 倍/単位長）・関節剛性（per-joint 6 倍/2 対 3、c1seat は世代差）。一般形 = 「式で結ばれた 2 量の片方だけが定数の所は、式が片側からしか守られていない」（p11 先行縮約・row 採録）。
- **設計の消費規則（v2 訂正）**: p5 詳細設計は納品・bank 済 = `P5_UR15_CELL_CONSTANTS_SPEC_20260727.md` @ `459d94bdb4`（**banked 272 行版・sha256 先頭 `81a7d76a7a`**）。⚠ on-disk は 571 行（作業版・乖離は row 46 自身が記録）⇒ **本設計は banked 版を content 主で消費し再導出しない**。⛔ 旧記載「contract の 2 値+1 規則を supersede」は**誤り**（debate CC6 が banked 版を実読）: banked §4 Tier B は **0.40 / 20°** を採り（0.22/45 は齟齬目録 `:30-31` 側）、**crown はどの版にも無い**（bank #22 が後出）。正しい関係 = **YOKE_SPREAD**: banked 0.40 → Rs 供給 cell 0.22（既に supersede 済・custody は `ur15_cell_spec.py:359-373` のみ）→ **C-2 0.28（settle）** ／ **tilt 20°**: **banked contract と再一致**（supersede ではない）／ **CROWN_R pin**: contract 外（bank #22 系・cell spec 内規則）。⇒ **p5 への依頼（本 spec の deliverable）**: constants-contract 系譜に supersession note を 1 枚追記（banked は凍結のまま・訂正別紙の型 = Rs 07-21 裁定）— 第 3 世代が banked 版を素で読む罠を塞ぐ。
- **解消形は既に実装され実走で権威を再現済**（row `:150` 末尾・p6 直読）: `ur15_steps_wired.py` + `ur15_cell_spec.py` の SSOT import 経路（`CABLE_N/SEG/R/質量/剛性 EI 導出` = `task_config.py:135-139`/`:144` と一致を `r6_positive_pair_result.txt` が印字）。**§1 の実装対象 = まさにこの経路**。⇒ C-2 実装は #46 の分裂を 1 件も持ち込まない。⚠ **#46 の CLOSE 条件 = 判定対象の run がこの経路で走ること** — 本 chain の DoD run（wired 経由）は close 条件へ寄与する（close の宣言は私の court でない・p6/p4）。
- **clip 個別（第一手検証済）**: 権威 = `thread_isaac_lab/envs/newton_skill_env_base.py:1858-1864` `_v_groove_clip_parts` = **5 box（台+下壁×2+リップ×2）**。live cell はこれを AST で直読（`ur15_cell_spec.py:309-321`・消えたら RuntimeError `:321`）→ 溝軸 y→x 90° 回転（`:325-333`）→ spec 照合表（`:337-343`）とクロスチェック。接触は task_config の solref/friction 写像（`:66-67`）。CLIP_H/GROOVE_W/CLIP_RISER は RETIRED 名簿（`:877`）。
- ⚠ **stale 定数は歴史ではなく現況**: retired 4 driver + 前世代 1 本は今も tracked・clean で Ø10 等を保持（row `:150`）。**どの driver を走らせるかは p4 の court** — §6-6 は**提案（p4 acceptance で発効）**として置く。
- DDR #46 行の現況注記の更新提案（「C-2 実装は SSOT 経路・stale 5 driver は不使用」）→ **p6 へ回付**（register 維持 = PLAN-KEEPER・`CLAUDE.md:173`。私は LEDGER を編集しない）。

## 5. #57 消費（開始姿勢 — p5 §24 裁定を消費する・再裁定しない）

- **裁定の現況（LEDGER `:161` フル読み + kickoff 訂正 4 項）**: #57 は**裁定済（p5 §24・bank #30 @ `40676a0d45`）**。裁定 (1) 把持対の**中心**は C1 から切り離された明示の設計変数（driver 実装済 `GRASP_CENTRE_X`・既定 = `C1[0]` = 挙動不変）— 拘束は「対の間隔 88 mm 指令」であって「C1 中心」ではない（⚠ これは p5 の**論**であり §0 適用範囲の確定は Rs — 「§0#2 非接触が確認された」とは書かない）。裁定 (2) 閾値は掃引で測る・計器 = **側ごとの無衝突候補数**。裁定 (3) 中心は段ごとの変数。
- **escalation の系譜**: built cell では全中心で L free = 0（24-draw 掃引）→ p5 が Rs へ 3 択 escalation（①clip 移動 ②役割交換 ③**取付幾何**）。**C-2 settle は Rs 委任下でこの ③ 側を実現した決定**であり、C-2 witness（L free 5・中心 = 既定のまま）は「**中心を動かさずに左の窓が開いた**」ことの実測。⚠ 上流（clip 配置・役割・y 掃引残り）= **Rs court のまま**（kickoff 訂正 4 項「y 掃引待ち」）— 本 spec は上流を動かさない・中心既定も動かさない（§2 H5 と同じ側）。
- **設計入力（p0/pZ へ・裁定の枠内の運用規律）**:
  1. **START_TRIES = 240 以上**（grid と同条件・既存 env var = `ur15_steps_wired.py:2418`・新 CLI 不要。24-draw の 0 は existence を語れない — `GRID240` §2）。
  2. **fallback run の非 evidence 化（手続バー・v2 で形を変更）**: driver は clear 候補 0 のとき **無条件で ⛔ fallback 行を印字して続行する**（`ur15_steps_wired.py:2194-2211`（`_fell_back`・⛔ print `:2207-2211`）・`:2319-2320`・実例 = `T43_RUN_TRACE_20260729.txt:27-28`）。**code に STOP 経路は存在しない**（debate CC5/CC4 実測）— そして本 spec の diff scope では作らない。⇒ **バーは手続に置く**: **route/DoD run のログに fallback 行（`put back`）が現れたら、その run は route 段の evidence として無効** — pZ は log grep で検出し、検出時は **STOP → p4 経由で報告**（棄却済 pose の run を成功系 evidence に数えない）。⚠ 将来 code-level gate（env-gated abort 等・wired 1 箇所）を望む場合は **別途 p4/Rs 承認の scope 拡張**として起票（本 spec は launch しない・FLAG のみ）。
  3. **再現は再抽選で**: witness の pose joint 値は**どこにも残っていない**（sweep の per-point ログは /tmp 揮発・消失を debate CC5 実測。表の `(7↔46)` は geom 対表示 — §3.1）。⇒ 同 predicate・同 draw 数（240）の**再抽選**で existence を再確認する（count 一致は要求しない）。計器は裁定 (2) の「側ごとの無衝突候補数」＋ 選択 pair gap の無条件印字（`ur15_steps_wired.py:2475`）。集計は候補分割でなく**棄却事象の数え上げ**である点を読み違えない（1 候補が複数相手に棄却され得る・row `:161`）。
- ⚠ **述語の版**: 現行候補述語は crown を含む（COLG 拡張・**ngeom 140 は t42/t43 共通・139→140 は aimboth（旧 cell）→t43 の間** — row `:161` の差し戻しで両 doc 訂正済）。**述語版の異なる run と clear 数を比較しない**。

## 5b. #49 disposition（整定ゲート — 本 chunk での扱い・判定 lane = p11/実装）

- **事実**: wired 系 driver は「settle gate: NOT REACHED — numbers below are from moving arms」を自己申告した実績がある（`r6_positive_pair_result.txt:37-39`・公差 2.0 mrad に対し残差 6〜10 倍・原因は 07-28 12:4x 時点で未確定・LEDGER `:147`）。腕の本数それ自体は収束を壊していない（同 run STEP1 で両腕 0.00 mrad）— 相どうしの対比。
- **disposition（本 chunk）**:
  1. **設計段（本 spec）は整定ゲート後の量に接地しない** — witness は運動学量のみ（整定非依存）。
  2. **実装指示**: route 実行の各相で driver の整定ゲート自己申告（到達/未到達・残差・公差）を**必ず印字・保存**する（既存機構の維持・削らない）。
  3. **検証指示（pZ）**: gate 後の量（背板距離・pad-local z・in-band 等）に接地する数値 verdict には**ゲート状態を併記** — 未到達相の数値に無印 PASS を出さない。
  4. **route run で整定ゲートが到達しない相が出たら**: 閾値緩和・公差拡大で通さず **STOP → p4 経由で報告**（Gate FAIL は fix-first・原因確定は本 chunk の scope 外 = 制御方式 (d) 系に隣接するため、勝手に制御へ手を入れない）。
- 先行 1-packet 裁定 = `P11_UR15_DESIGN_DISPOSITION_20260727.md` §27.2.108（@ `de0d29f2b6` 時点の内容に接地・以後加筆あり）— 本 disposition はそれを本 chain の受入条件へ具体化したもの。

## 6. p0 実装指示（diff 形・commit 規律）

1. §1 の 4 編集（提案 comment 付き・**内容特定・末尾側から**）。**他 file 編集なし**（retired 4 driver + 前世代 c1seat 不触・`task_config.py` 不触・env source 不触・`ur15_steps_wired.py` 不触）。
2. 実装前に対象行を cat（§運用16）。編集後 self-check（**実行可能形・v2 訂正**）: (a) `ur15_cell_spec.py` 単体実行の Tier B print（`:1232`）が `YOKE_SPREAD=0.28 TILT=20 deg` を示す。(b) crown 値は print に無いため（debate 実測）`env_isaaclab7/bin/python -c "import ur15_cell_spec as s; print(s.YOKE_SPREAD, s.CROWN_R, s.CROWN_ZC)"` で `0.28 0.110 1.440` を確認（read-only・file 追加なし）。
3. **commit = explicit pathspec 限定**（共有 index の他 pane 分を巻き込まない）+ `--no-verify`（Layer 8 の既存 19 FAIL は本変更と無関係 = DDR #35。commit message に理由 1 行）。
4. 本 branch (`rlrk/optE-s2-substrate-swap`) 上で行う（cell 実装面は本 branch に live。`probe/pd1-arm-pd` は (d) arc 用で本 chunk の対象外）。
5. 新規 file・新 CLI 引数・新 Phase を作らない（scope = §1 の 4 点のみ。START_TRIES/STEREO_HEAD は既存 env var）。
6. **【提案 — p4 acceptance で発効】C-2 の全 run は `ur15_steps_wired.py` + `ur15_cell_spec.py` の SSOT 直結経路に限る**（#46 の分裂を持ち込まない）。走らせない: retired 4 driver（`ur15_cell.py`/`ur15_route.py`/`ur15_steps.py`/`ur15_steps_reaim.py`）・前世代 `ur15_steps_c1seat.py`・**独自 cell を持つ video 系**（`ur15_yoke_video.py` は `:30` に自前 `YOKE_SPREAD=0.22` を hardcode — C-2 の絵にならない／`ur15_final_video.py`・`p4_pd_video.py` は cell spec を経由しない）。視覚レグは `render_cell_overview.py`（CELL+WIRED から読む・安全を debate CC5 確認）か wired 自身の描画で。
7. ⚠ **既存の脆弱点（本 scope 外・p4 へ FLAG）**: `ur15_steps_wired.py:32` が他 session の /tmp scratchpad path を hardcode し import 時にそこへ XML を書く（消えると全 run が import で落ちる・今日時点は存在を確認済）。恒久修正（repo 内 path 化）は p4/p0 の別 chunk。

## 7. pZ 検証項目（受入条件の分解）

1. **diff scope**: 変更が `ur15_cell_spec.py` の 3 箇所+注記と `sweep_mounting.py:169-170` の label のみであること（pathspec 外の混入 0）。
2. **既定 build = witness cell**: override なしで `YOKE_SPREAD=0.28 / tilt 20 / CROWN_R=0.110 / CROWN_ZC=1.440`（確認は §6-2b の `python -c` か wired build の効き値印字 — **crown r と mounting は毎 run 無条件印字される** `ur15_steps_wired.py:2358-2359`）・crown capsule `fromto ±0.28`・mount `pos=[±0.28,0,1.53]`・`quat=Ry(±70°)`。
3. **override 後退なし**: `YOKE_SPREAD_OVERRIDE=0.220 TILT_DEG_OVERRIDE=45` で built cell が値一致で再現（⚠ crown は「0.110 = 0.22/2 の偶然一致」で override 不要のまま一致する — この一致に依存していることを記録）。`CROWN_Z0_OVERRIDE` 経路・`"none"` 経路も生存。
4. **clip = 権威**: build 後の compiled clip geom 群が `_v_groove_clip_parts` の 90° 回転像と一致（リップ 2 枚を含む 5 box×2 clip）・RuntimeError guard（`:321`）生存。
5. **開始姿勢（手続バー）**: 240 draws で L clear ≥ 1 かつ R clear ≥ 1 かつ選択 pair の gap > 0（existence の再現。**count 5/30 の一致は要求しない** — `GRID240` §7-3）。**route/DoD run のログに fallback 行（`put back`）が無いこと** — 在れば当該 run は route evidence 無効・STOP→p4 報告（§5-2）。
6. **task 幾何不変**: C1/C2/REST_Y/REST_X/GRIP_HALF_SPAN/CABLE_R の値が変更前後で同一。
7. **計器 scope 記録**: (a) inner IK loop は運動学のみ読み（`mj_kinematics` 系 `ur15_steps_wired.py:1329-1376`・接触は収束後読み）、route 物理 `mj_step` は不触 — **この性質は全 solve 経路共通**（「sweep 限定」ではない・v2 訂正。"KINONLY" は表の tag であって code flag でない）。(b) #54 部材・stereo head は collision 集合に**不在**であることを cell 条件として記録。
8. **視覚レグ**: `render_cell_overview.py` か wired 描画で C-2 cell の絵を残す（motion を含む RESULT は本 chain の DoD 段で `/verify-run` 経由・数値単独 PASS 禁止）。
9. **env 版 pin（#61）**: pZ の全 run は `env_isaaclab7`（`/home/rlrk/env_isaaclab7/bin/python`）で実行し、4 package（newton 1.4.0 / mujoco 3.10.0 / mujoco-warp 3.10.0.3 / warp 1.15.0）を run 記録に印字（witness と同一計器条件。mujoco 版差は `mj_geomDistance` を non-conservative 方向に動かした実測がある — LEDGER `:165`）。
10. **整定ゲート併記（#49・§5b）**: gate 後の量に接地する数値には到達/未到達と残差を併記。未到達相の数値に無印 PASS を出さない。
11. **cable 主張の co-cite（#48）**: DoD run の cable 挙動に関する主張は「MuJoCo cell」と明示し #48 を併記（#48 open の間、DoD 動画へ無印 PASS を出さない — 受入報告に射程を明記）。
12. **cell 条件の明記**: 受入報告の existence 主張は「**stereo head 不在・#54 部材不在の cell について**」と射程を書く（§2）。sweep label（変更 4）が cell 既定と一致していること。

## 8. prior-art guard disposition（V7・BLOCKER 4 件）

`scripts/check_thread_vault_prior_art.sh --fail-on-blocker mounting yoke spread tilt crown` = **BLOCKER_CONTEXT_FOUND**（本 session 実行・出力保持）。逐件 disposition:

| hit | 内容 | 判定 |
|---|---|---|
| `CROWN_BAND_READING_20260802.md:48` | 「この mounting で生き残らなかった 12」 | **C-2 選定の測定 corpus そのもの**（menu の入力）。再試行対象の失敗経路ではない |
| `CROWN_SWEEPS_240_READING_20260802.md:39` | 不在主張の自己訂正（過程の教訓） | 設計経路ではない（教訓は §5 の述語版注意に反映） |
| 同 `:62` | built cell の crown 掃引 fail 表 | **置換対象（built）の失敗証拠** = 本設計の動機。再試行ではない |
| 同 `:185` | crown×tilt 相互作用（C-2 で r=0.075 も witness） | C-2 の**頑健性の根拠**（§3.5a に採用） |

⇒ **同一失敗経路の再試行に該当しない**: 失敗経路 = built mounting での走行であり、本設計はそれを settle 済みの measured witness 点へ置換する。新 directive = Rs 08-08「中間目標を達成せよ」→ m-p18-91（custody = kickoff §0）。

## 9. ゲート記録

- **[L-TRIAGE]**: 本 turn の変更 = 本 spec 1 file（eval_runs・非ルール系文書）。質的トリガ「新規ファイル作成」を保守側に採り **L=L2** を自己申告（p4 kickoff の L0 前例より重く取る: 本 file は下流実装を駆動する設計 spec）。⇒ L2 ゲート = DoD 事前宣言（本 §）+ pre-mortem（§3.5c + debate の failure-mode lens）+ **5 体 CC Debate 事前**（§11 = 実施済・全採択反映）+ handoff（§25 該当なしと判断・CC1 裁量）。⚠ `/rule-check` stage1/stage2 は**手動形で代替**（skill 本体が手動チェックリスト方式・§0 keyword 照合は実施: 対象 path は L3 一覧に非該当〔eval_runs 文書 + eval_runs 内 sim 定数/計器 label〕・`task_config.py`/CLAUDE.md/skills/hooks/04-Specs/07-Design に触れない・reward/成功条件/制御方式の変更なし。文書テキスト中の keyword 出現は変更対象の性質でなく記述対象 — kickoff L0 前例と同扱い）。代替の妥当性は debate CC4 が checklist 全項を独立検証。
- **[DEFER-RECON]**: p4 kickoff §3 の register 照合を第一手で再読・継承 + kickoff 訂正（`405bf8ce81` +6 行・`50eeaa134d` #38/#45 除外記録）を diff で実読。フル読み = #46/#48/#49/#57/#61。FOUNDATIONAL で design-start を gate する行 = 0（p18 が全行 untruncated で追認・m-p18-94）。flag 継承 = #45/#48/#49/#54/#58/#61/#39/#18（§2）。#45↔#58 の相互参照は p6 が両方向化済（`661c5e0f24`）。
- **[RULE-CHECK] 主要項**: kinematic 不使用（幾何定数と label のみ）✅ / 制御方式不変 ✅ / `task_config.py` 不触 ✅ / 04-Specs・07-Design 不触 ✅ / 新 file は本 spec のみ ✅ / timeouts・reward 無関係 ✅ / PhysX↔Newton 規約混同なし（本件は mujoco cell 面・PhysX API 名を持ち込まない）✅。
- **DoD（本 turn）**: 本 spec bank（pathspec 限定 commit）+ debate 完了 + p18 経由で p4/p5 へ回付。**chain DoD**: 43-step scripted route 動画（裁定 A・`00-DESIGN-STATUS-LEDGER.md:39`）— 視覚レグ必須・数値単独 PASS 禁止・最終は Rs human-GT。⛔ **evidence-grade cap（受入報告に必ず射程明記）**: #48（cable 第 2 DOF・Rs 裁定待ち）と #18（grip-efficacy・p5 chain）が open の間、DoD へ**無印 PASS を出さない**。#49 未整定相の数値はゲート状態併記（§5b）。版を言う主張は #61 の pin に接地。**existence 主張は stereo head 不在・部材不在の cell 条件を明記**（§7-12）。

## 10. 出所の等級

- 第一手（本 session 直読）: kickoff **v3**（`405bf8ce81` +6 行・`50eeaa134d` を diff で実読）/ role brief / LEDGER `:34-40` / **DDR フル読み = #46（:150 全）・#48（:146 全）・#49（:147 頭 5500 字）・#57（:161 頭 7000 字）・#61（:165 全）**・#45/#54/#58 は各 1000 字頭（**不在主張には未使用**）/ `P4_DELEGATED` 全文 / `GRID240_READING` 全文 / KINONLY 表 `:25-70` / `ur15_cell_spec.py` 該当区間 / `ur15_steps_wired.py` grep 区間 / `newton_skill_env_base.py:1850-1874` / `task_config.py:21-22,135-138,233-236` / RS71 §0 頭部 / SOMA `:14-18`。
- debate panel（5 体・本 session 起動・§11）: 各 challenger の on-disk 実測は当方の第一手と独立 — 本 spec の v2 数値はその実測を採択して更新した（採択根拠は §11 の findings 対応表）。
- relay（未検証・flag 付きで扱う）: #45 の Rs 逐語（p18 broadcast 系・on-disk 未着地が要点）/ #57 の p4 推論（柱越え）— いずれも本 spec の決定に不使用。
- 実行記録: prior-art guard 出力（§8）・grep 実測（§1・§3.5b）。

## 11. [VERIFY] 5 体 CC Debate 記録（事前・bank 前実施）

**体制**: CC1 = p11（本 spec 起草者）/ CC2 幾何・物理 / CC3 SSOT 引用整合 / CC4 プロセス・ゲート / CC5 実装可能性（p0/pZ 視点）/ CC6 null 仮説擁護（「今 変えるべきでない」の steelman）。全員が on-disk を独立実測。実施 = 2026-08-08 21:3x-21:4x・並列。

**findings と disposition（v1 → v2）**:

| # | 出所 | 内容（要旨） | 判定 | v2 反映先 |
|---|---|---|---|---|
| 1 | CC5/CC4 | **[CRITICAL]** loud STOP 経路は driver に無く（fallback は印字して続行 `:2194-2211`）、宣言 diff 範囲では作れない — §5-2/§7-5 と §6/§7-1 が同時に満たせない | **採択** | §5-2 を手続バー（fallback 行 = 非 evidence・pZ log 検出・STOP 報告）へ書換。code gate は FLAG のみ |
| 2 | CC2/CC3/CC4 | **[MAJOR]** #54 zone「built 0.298 m」は退役 0.40-cell の数 — built は 0.118 m・**C-2 は +60 mm 拡大**（方向逆転） | **採択** | §2/§3.3/§3.5a/§3.5b/§3.2 S3 訂正（拡大と明記） |
| 3 | CC2 | **[MAJOR]** stereo head 既定 OFF が witness の未記録条件（driver 自身が non-conservative と明記） | **採択** | §2 新 bullet・§3.1・§3.3・§3.5a・§7-12 |
| 4 | CC5 | **[MAJOR]** `(7↔46)` は pose pair でなく最近接 geom 対・pose は /tmp 消失で再現不能 — seed 案は実行不能 | **採択** | §3.1 相貌訂正・§5-3 再抽選のみへ |
| 5 | CC6 | **[MAJOR]** §4 の banked contract 記述が誤り（banked = 0.40/20°・crown 記載なし ⇒ tilt は再一致・crown 規則は contract 外） | **採択** | §4 書換 + p5 への supersession note 依頼を deliverable 化 |
| 6 | CC2/CC5 | **[MAJOR]** 変更後、override なし sheet (a)/(z) 実行が C-2 を測りながら built label を印字（`sweep_mounting.py:169-170`） | **採択** | 変更 4 新設（label 2 行）+ §7-12 |
| 7 | CC2/CC3/CC5 | **[MAJOR]** §6-2 の「crown print」は存在しない（`__main__` に CROWN 印字 0） | **採択** | §6-2 を実行可能形（`python -c`）へ |
| 8 | CC3/CC4 | **[MAJOR]** RS71 引用 `:22`→`:24`・#48 の hinge 行 `:183-184`→`:233-234`・RS71 §4 B2 は現 `:69`（row pin `:67` は行ずれ） | **採択** | §2 の 3 pin 修正 |
| 9 | CC5 | **[MAJOR]** §7-7「sweep 計測経路限定」は偽の述語（IK loop 変更は全 solve 経路共通・"KINONLY" は code に無い） | **採択** | §7-7 を検証可能な形（運動学のみ読み・mj_step 不触・全経路共通）へ |
| 10 | CC5 | **[MAJOR]** video 系 3 script が cell spec を経由せず（`ur15_yoke_video.py:30` 自前 0.22 等）§6-6 の fence 外 | **採択** | §6-6 に video fence 追加・§7-8 手段を限定 |
| 11 | CC2/CC5 | [MINOR] §3.4 除外計上（crown-none built は H3 側）・断面図の「fork」表記・§3.5b の網羅主張（_SHOULDER 連鎖）・「:426/:432 のみ」の語り過ぎ・retired「3」→4+1・行番号ずれ対策・§7-3 の偶然一致依存 | **採択** | 各所訂正 |
| 12 | CC4 | [MINOR] /rule-check skill 経路の非実施・§6-6 の court 表示 | **採択** | §9 に手動代替を loud 記載・§6-6 を【提案】表示 |
| 13 | CC5 | [MINOR] wired:32 の他 session /tmp path hardcode（消えると import 不能） | **採択（FLAG）** | §6-7 で p4 へ FLAG（scope 外） |
| 14 | CC6 | null 仮説 5 系統中 4 系統 KILLED（override-only 運用は 0.140 罠と env-drift 前例で劣後・witness thin は existence-scope 済・#54/#45 待機は settle 自身の条件に反する 等）— SURVIVES 1 = finding 5 | 追認 | 同上（#5 で反映済） |

**rebut（不採択）**: なし（全 findings を採択または FLAG 化）。CC2/CC3/CC5 の「verified clean」集合（witness 数値・tilt 変換・crown 算術・編集行番号・literal bit 同一性・camera/TILT_CAL_DEG 非連動・START_TRIES 既存 env・KINONLY `:54` 行）は v2 の根拠として §10 に登録。

**spillover（本 spec 外・回付対象）**: kickoff の 2 pin ずれ（裁定 A `:40`→実 `:39`・UR15 `:34`→実 `:36`）= p4 の artifact（CC3 発見）— p18 経由で p4 へ 1 行報告。
