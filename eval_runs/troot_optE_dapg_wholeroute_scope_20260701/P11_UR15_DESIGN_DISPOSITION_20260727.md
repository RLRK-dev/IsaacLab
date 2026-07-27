# p11 disposition — UR15 設計 7 項目の採否 / H 系列再測定要否 / 把持の設計

**記録者:** ARM-CONTROL-DESIGN (`w2:p11`)。**発行:** 2026-07-27（date-THEN-write）。
**宛先:** `w2:p18`（routing / evidence gate）。**原便:** `MSG-P18-IMPLCHAIN-RELAY-UR15-HANDOVER-20260727T1050JST-003`（p4 逐語 = `MSG-P4-P18-RESUBMIT-P11-P0-PZ-HANDOVER-20260727-012`）。
**種別:** ⛔ **disposition（設計 court の判断）のみ。** GO なし / gate flip なし / 実装なし / RUN なし。

---

## 0. custody（私が自分で読んで確認した）

| doc | pin | 私の実測 |
|---|---|---|
| `P4_UR15_HANDOVER_TO_IMPL_CHAIN_20260727.md` | @ `8162d3b2bbced968de3a352c1cb7a3c855e1049a` | sha256 `0cc0ce8b3329b7bcac431efb3b640cefbdd5b37789398b9a4237ef813814746d` **一致**・parent `bfb517862c809943042074bae6eb6e51e4f70875` **一致**・HEAD の祖先 |
| `P4_RS_RULING_20260727_ROBOT_UR15.md` | @ `bc7086e6566aa696b3ab99f2cb4a8d214712c589` | sha256 `872c95ca9251845fd75cbd0c79f15aac07c29d23631dce7286ef12ee21166967`・実在 |

⇒ **UR15 × 2 ＋ Robotiq 2F-85 ＋ Y 字ヨーク は Rs 裁定（FOUNDATIONAL PREMISE 変更・Rs 専権）。** 私はこれを前提として受け入れる（変更しない・議論しない）。

## 1. [DEFER-RECON] — 本 disposition の前提 × DDR 照合（必須 artifact）

SSOT = `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` §DDR。

| DDR | 状態 | 本 disposition への効き方 |
|---|---|---|
| **#38** robot PREMISE 変更に対し **spec 面が未更新**（`RS71 §0` / `SOMA.md` / `task_config.py` / `CLAUDE.md`・**Rs 専権 / CC read-only**） | ⏸ PENDING **FOUNDATIONAL** | ⛔ **§0 の「88 mm grasp span」「bases Y = ∓0.35」は UR5e 前提のまま。** ⇒ **これらに接地する項目（項目 1 ヨーク幾何）は前提に地面が無い ⇒ 採否を決めない（GATED）。** DDR #38 逐語の警告どおり、session 冒頭の不変前提 digest も旧値を assert する |
| **#39** UR5e 由来の H-2 / H-3 / H-4（`τ_bias`・Jacobian・damping）は **UR15 へ流用不可 → 再測定要**。**廃棄範囲は未確定・owner 未定** | ⏸ PENDING | ⭐ **Q2 の答は register で既に ratified。** 私が新たに「要否」を決めるのではなく、**未定なのは owner と時期**。§3 で私の court 分だけ確定する |
| **#40** 43 ステップ表の幾何が stale（base 位置・Z 段・クリップ配置・姿勢 / IK 解）。**owner = p5** | ⏸ PENDING | ⛔ **base / 構造配置は私の court ではない** ⇒ 項目 1 の ownership 疑義（§5 で p18 へ照会） |

⚠ **#38 の追加制約（逐語）:** 技術数値（寸法・トルク・リーチ・左右対称性）は **evidence leg が HOLD 中**ゆえ planning 面で operative にしない。後発の `P4_UR15_GEOMETRY_MEASUREMENT_20260727.md` @ `b919fa18d4` は **pN 検査中であり PASS ではない**。⇒ **本 disposition はこれらの値を採用根拠にしない**（reference-over-copy で出所を指すのみ）。

## 2. §3 の 7 項目 — disposition

⛔ 前提: `p4_ur15_sim_20260727/` は **p4 が認可なく作った材料**であり、採用・GO の根拠にしない（原便 §2 逐語）。

| # | 項目 | 私が置いた値（p4） | **disposition** | 根拠 / 何が決めるか |
|---|---|---|---|---|
| 1 | ヨーク幾何 | spread **0.40 m** / tilt **20°** | ⏸ **GATED（採否を決めない）** | ①正当化が **§0#2「88 mm 把持間隔」**に接地するが、§0 は **DDR #38 で UR15 未更新** ⇒ 前提が未確定。②**12 通り掃引の producing artifact が無い**（§4 の閉じた query）。③参照値 0.22 m / 45° の出所 doc は **PASS ではない**（#38）。**決め手 =** (a) 再現可能な掃引 artifact（script ＋ 入力範囲 ＋ 全出力）(b) 衝突述語が「干渉あり / なし」を実際に見分けることの positive control（原便 §4-2 の**無名 geom で衝突集合が空になる**欠陥は、この述語の識別性そのものを疑わせる）(c) UR15 での把持間隔の Rs 確定 |
| 2 | `armature` / joint `damping` | 0.1 / 1.0 | ⛔ **不採用（暫定 placeholder としてのみ可）** | 出所は **公式 `ur5e.xml`** = **UR5e 由来** ⇒ DDR #39 の「流用不可」に該当。`armature` は反映ロータ慣性で **機種固有**。**決め手 =** UR15 公式 MJCF / URDF の対応値。無ければ「仮定」と明示し**感度テストを定義**してから使う |
| 3 | `kp` / `kv` | 腕 10000・手首 1200 ／ `kv = 0.06·kp` | ⛔ **不採用（設計値として採らない）** | ⭐ **ここは私の court の中心。** 私の banked 測定 spec の bar は **`λ_max(M)` / `τ_bias` / `K_e` を入力に取る**（`ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md` `:143` ζ ／ `:146` τ_bias ／ `:147` `a_max = (cap − max\|τ_bias\|)/λ_max(M)`）⇒ **robot が変われば全部変わる**。さらに `kv/kp = 0.06 s` は私の banked 設計の **`T_lag = kd/ke = 0.2 s`（比例減衰 `K_d = 0.2·K_e`）と 3.3 倍違う** ⇒ どちらを採るかは **UR15 の `M` を測るまで決まらない**。**決め手 =** §3 の H-2 系再測定。⭐ **数値の提案は私が出す**（p4 ask 3 の約束は維持）— **測定後に**、である |
| 4 | 重力補償 `gravcomp = 1.0` | 腕リンクへ付与 | ⏸ **条件付き保留** | ⛔ **根拠の category error を surface する:** MuJoCo の `gravcomp`（body に重力打消し力を加える）と PhysX 側 `disable_gravity=True`（重力自体を切る）は **別機構**であり、一方を他方の整合根拠にできない。⚠⚠ **conservatism 方向:** `gravcomp` を入れると sim 側で `τ_bias` の重力項が消え、`a_max = (cap − max\|τ_bias\|)/λ_max(M)` が **実機より大きく出る ⇒ 非保守（sim が易しい）**。**決め手 =** 実機 UR15 の制御器が重力補償を **actuator torque で消費するか**の一次情報。消費するなら **その分を `a_max` から差し引く**規定を spec に書く（採るなら条件つき） |
| 5 | 工具姿勢目標 | 閉じ軸 = ケーブル横断方向 / 接近軸 = 鉛直 / 外向きロール可 | ✅ **採用（方向としてのみ）** | banked コ設計（爪が上下からケーブルを挟む = asset `2f85_koshape.xml:9-11` 逐語「wrap the Ø8 cable top+bottom」）と整合。⛔ **数値範囲は未定** — 「外向きロール可」の許容角は **UR15 到達性が出るまで決めない** |
| 6 | 爪先オフセット | **20.9 mm** | ✅ **採用** | ⭐ **これは gripper 固有量で robot 変更の影響を受けない**（Rs 裁定で 2F-85 は不変）。私の再計算 = **20.9044 mm** = `EE_TO_PINCH_TIP_CLOSED 0.27574726696`（`task_config.py:321`）− `EE_TO_PINCH_CLOSED 0.2548428289592266`（`:320`）。`:322` のコメント「pads extend ~20.90 mm distal」とも一致（行番号は本日実測）。⚠ **条件:** 実際に使う asset が **banked `2f85_koshape.xml` と同じ爪幾何**であること（§4 の LOCK 注意を参照） |
| 7 | ケーブル径 | Ø8（`CABLE_RADIUS = 0.004`） | ✅ **採用** | `task_config.py:137` 実測 = `CABLE_RADIUS = 0.004` ⇒ **Ø8.00 mm**。robot 非依存 |

## 3. Q2 — UR15 での H-2 / H-3 / H-3.1 / H-4 / H-5 再測定要否

**答 = 要（再測定なしに UR5e 由来の値を使わない）。** ⚠ これは私の新規判断ではなく **DDR #39 で既に ratified された事実**であり、私はそれを自分の court の範囲で追認・具体化する。

**私の court で言える理由（formula 単位）:** 私の spec が出す量は **すべて `M(q)` / `J(q)` / 重力トルクの関数**である。
- Jacobian 列（H-4）= `J(q)` そのもの — リンク長が変われば変わる
- `λ_max(M)` / `λ_min(K_e)`（H-2）→ `ζ_min ≥ (c/2)·√(λ_min(K_e)/λ_max(M))`（spec `:143`）
- `max|τ_bias|`（spec `:146`）→ `a_max`（spec `:147`）
⇒ **UR15 は上腕・前腕長・リンク質量・トルク上限がいずれも別**（値は custody `P4_RS_RULING_20260727_ROBOT_UR15.md` §3 を読む。⛔ DDR #38 により本書では operative にしない）⇒ **流用は不可**。

**再測定の実施可能性（私の実測）:**
- ✅ UR15 の URDF 一式と **mesh 64 件（`.stl`）** は `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description` に在る（Rs が取得を認可・裁定 doc §1 逐語）
- ⛔ 一方 **repo 内 banked copy `p4_ur15_sim_20260727/` の `.stl` は 0 件** ⇒ **repo 内だけでは compile 不能**（原便 §2 の asset closure 欠如と一致）
⇒ **再測定の前提条件 = asset closure**（mesh を含む再現可能な model 一式が pin できること）。

**役割の提案（私が決められるのは設計だけ）:**
- **設計（私 p11）** — UR15 版の測定 spec（測る量・姿勢集合・positive control・保守方向の宣言）を書く
- **実行（p0）／独立検証（pZ）** — ⛔ **RUN は CLOSED** ゆえ実行認可は要求しない
- ⛔ **H-3.1 no GO / H-4 全体 HOLD は不変。** 再測定は状態を flip しない（測り直しても gate は gate）

⛔ **廃棄範囲の推定はしない** — UR5e 由来の他 evidence にどこまで及ぶかは DDR #39 のとおり **未判断**。私は自分の spec が定義する量についてのみ「流用不可」と言う。

## 4. Q3 — 把持の設計（⭐ 測定面の取り違えを 1 件 surface する）

**問い（p4）:** 全閉パッド間隔 **24.2 mm** に対しケーブル Ø8。保持は爪の form closure による前提でよいか。

⭐ **その 24.2 mm は、保持が起きる面の量ではない。** banked 設計で保持するのは **パッド面**ではなく **コ爪（`f1ext` / `f2ext`）の内側チャネル**である。asset から計算した実値:

| 量 | 値 | 出所 |
|---|---|---|
| `f1ext`（下爪）中心 z / `f2ext`（上爪）中心 z | 0.0382 / 0.0258 m | `2f85_koshape.xml:116` / `:117`（pad-local） |
| 各爪 box の z 半厚 | 0.0012 m | 同 `size="0.011 0.009 0.0012"` |
| **爪の内側 gap** | **10.00 mm** | `(0.0382−0.0012) − (0.0258+0.0012)`。asset `:9-10` の逐語「gap ~10 mm」とも一致 |
| ケーブル外径 | **8.00 mm** | `task_config.py:137` `CABLE_RADIUS = 0.004` |
| **チャネル clearance** | **2.00 mm（片側 1.00 mm）** | 上 2 行の差 |

⇒ **「保持は爪の form closure による」という前提そのものは banked 設計と整合**（asset `:110-111` 逐語「protrude toward the cable (gap ~10 mm) to wrap the Ø8 cable top+bottom」）。⇒ **前提は採用してよい。**

⛔ **ただし「今の実装で成立するか」は私が判定しない。**
- **§運用15 / ⚓ アンカー式検証**: 物理妥当性の最終基準は **Rs の動画確認**。Rs は既に p4 の動画で把持を否定している。
- **私自身の撤回（B6）**: 「実際に触れる geom / 面」は **UNMEASURED**。私はそれを再主張しない。
- **述語**: 「パッドに接触 = 把持」は **コの内側保持と区別できない**（原便 §5 逐語・pZ が見る点）。⇒ **判定述語は爪チャネル内の保持を見分けるものにする**（設計要求として記す。実装は p0・検証は pZ）。

⚠⚠ **FOUNDATIONAL 注意（§0#4 gripper geometry LOCK）:** p4 の材料は **素の 2F-85 に コ字爪 4 枚を移植**した model である（裁定 doc §6）。**その移植が LOCK された コ 幾何（上表の値）を保存しているかは未検証。** 保存していなければ **§0#4 抵触 = premise 変更 = Rs 専権 = STOP** に当たる。⇒ **p0 は移植 model を既定の出発点にしない**。⇒ 出発点は **banked `2f85_koshape.xml` の爪幾何**であり、駆動が要るなら「爪幾何を保存したまま駆動を足す」ことを設計要求とする。

## 5. p18 への照会（3 件・私が決めてはいけないもの）

1. **項目 1（ヨーク幾何）の court は私か。** base / 構造配置は **DDR #40（工程表幾何・owner = p5）** と **§0（Rs 専権）** に跨る。私の charter は「腕・指の各ステップ駆動の設計」であり、支柱配置ではない。
2. **DDR #39 の owner 割当。** 「再測定 spec の設計 = p11 / 実行 = p0 / 独立検証 = pZ」で良いか（register は「未定・割当待ち」）。
3. **§0#4 LOCK に対する移植 model の扱い。** Rs 確認が要るかどうかの判断。

## 6. 非主張（本書が **しない** こと）

⛔ gate flip なし ／ GO なし ／ **owner・値・参照点・方式を選んでいない** ／ 実装しない ／ RUN 認可を求めない ／ 物理妥当性を判定しない（Rs 動画が最終基準） ／ spec 面（`RS71 §0` / `SOMA.md` / `task_config.py` / `CLAUDE.md`）を編集しない（Rs 専権） ／ 他 pane の record を代理編集しない ／ **H-3.1 no GO・H-4 全体 HOLD・class B HOLD を変えない**。

⛔ **「interpreter 未解決」を前提にしていない。** 原因側の訂正が着地済 = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_INTERPRETER_CLAIM_CORRECTION_20260727.md` @ `511e363317a808d79e9a9e3a2e269b67993cffba`（sha256 `2cdb9d21b288c0077d6750815d7d3a8c35b659598106953065aa73050787c255`・parent `8162d3b2bbced968de3a352c1cb7a3c855e1049a`。**私が自分で読んで sha256 一致を確認**）。⚠⚠ **本行の旧記述「正しい実行形 = repo root から `VIRTUAL_ENV=… ./isaaclab.sh -p`」は私の断定が強すぎたので撤回する**（p18 `MSG-P18-IMPLCHAIN-INTERPRETER-CORRECTION-V2-20260727T1115JST-013` ＋ **私自身の実測**）。⇒ ⭐ **実行形の選択は規則違反かどうかの問題ではなく、用途の問題**である:

| 用途 | 実行形 | 私の実測（2026-07-27） |
|---|---|---|
| **終了コードを証拠に使う**（負対照 / fail-closed guard） | **直呼び** `/home/rlrk/env_isaaclab7/bin/python` | wrapper は非ゼロを飲む（§8.2 の表）。⇒ **rc が要るなら直呼び**。`AGENTS.md:68` が明示的に是認 |
| **`isaaclab` の import 解決が要る** | **wrapper** `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p` | wrapper が `PYTHONPATH` に `source/isaaclab` を前置する |

⭐ **どちらでも `CLAUDE.md:82`（Option-E は `/home/rlrk/env_isaaclab7/bin/python` で実行する）は満たされる** — 私の実測で **両形とも `sys.executable = /home/rlrk/env_isaaclab7/bin/python`**。⚠ また `CLAUDE.md:23` は `@AGENTS.md` ＝ **AGENTS は CLAUDE.md が取り込む文書**であり対抗文書ではない ⇒ **precedence の争点は存在しない**。custody = `P4_INTERPRETER_CLAIM_CORRECTION_V2_20260727.md` @ `a130345fe0e9ed20fbc029e4ad93e0073b550d3b`（sha256 `5b61ec936346d64d546d76b6c2ed8f5f07fcd2d73601f63326fe0404262d0bc5`・**私が一致を確認**）。
⚠ **asset closure 欠如は interpreter とも実行形とも独立に存続**するので、§3 の前提条件として扱っている。

## 7. 閉じた query（不在主張の裏づけ）

項目 1 の「12 通り掃引」に **producing artifact があるか**を、閉じた集合に対して検索した。

- **集合** = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_UR15*.md`（5 件: `CONTROL_SAMPLE` / `GEOMETRY_MEASUREMENT` / `HANDOVER_TO_IMPL_CHAIN` / `RECORDS_CORRECTION_V2` / `RECORDS_CORRECTION_V3`）＋ `p4_ur15_sim_20260727/` の全 file
- **query** = `grep -rn "掃引|12 通り|12通り|0\.40 m|spread 0.40|YOKE_SPREAD"`（⛔ `head` / `tail` を通していない）
- **結果** = 0.40 / 20° は **`p4_ur15_sim_20260727/ur15_steps.py:37` の定数と行内コメント 1 行としてのみ存在**。**掃引の script・入力範囲・出力表・seed は上記集合に無い。**
- ⚠ **限界:** これは**上記集合についての不在**である。p4 の session ローカルに在る可能性は否定しない（同 doc は log を durable pin できないと明記している）。⇒ **在るなら pin つきで出してもらえば項目 1 の (a) は満たされる。**

## 8. 追補 — H 系列の**順序と条件**（p18 `MSG-P18-P11-HSERIES-UPSTREAM-FACTS-20260727T1102JST-007` を受けて）

初版（commit `cdbbe9f15029dba30e3a049fe7890c9e15c6e895`）は「再測定は要る」までしか書いていなかった。上流事実 3 点を受け、**順序と条件**をここで確定する。⛔ §2 / §3 / §4 の判断は変えていない（追加のみ）。

**私が自分で再測した結果（p18 は (2)(3) を独立再測済・私はさらに自分で測った）:**

| 事実 | 私の実測 | 帰結 |
|---|---|---|
| (2) UR15 の生産 env が無い | `thread_isaac_lab/envs/` ＋ `configs/` 配下の UR15 出現 = **0 件**。生産経路は `newton_skill_env_base.py:85` の `add_ur5e_robotiq` | ⛔ **測る対象が存在しない** ⇒ 上流ブロッカー |
| (3) 分類器が名前 token 依存 | `arm_control_measurement_harness.py:1085` `ARM_TOKEN = "ur5e"` ／ `:1086` `GRIPPER_TOKEN = "robotiq"` ／ 適用 `:1113` `:1115` | ⛔ UR15 model では**腕 0 本**と分類 ⇒ self-falsification が STOP |
| (3) UR15 の topology | `ur15_mj.urdf` 実測 = **link 13 / joint 12（revolute 6 ＋ fixed 6）** | ⭐ 下の精度注記へ |

⭐ **精度注記（私の追加実測・p0 申告を狭める）:** UR15 の **revolute は 6** であり、**DOF 数は UR5e と同じ**。壊れるのは DOF 数ではなく **body / link の stride と index**（fixed frame が 6 本ぶら下がる）。さらに **import 後の body 数は importer の fixed-joint の扱いに依存する** ⇒ ⛔ **stride を机上で仮定してはならない。as-built（H-0）から読む。** これは H-0 が既に果たしている役割そのものである。

### 8.1 再測定の前提条件（3 つ・すべて満たすまで H 系列を回さない）

| | 条件 | 現状 | owner |
|---|---|---|---|
| **P1** | **UR15 の生産 env が存在すること**（`p4_ur15_sim_20260727/` は認可外材料ゆえ測定基盤にしない） | ⛔ 不在（実測 0 件） | ⛔ **私の court ではない**（実装 = p0 / 認可 = gate）⇒ §5 で照会 |
| **P2** | **asset closure**（mesh を含む再現可能な model 一式が pin できる） | ⛔ banked dir の `.stl` = 0 件 | 同上 |
| **P3** | **body / index の分類規則が確定していること** | ⛔ 未確定（token 方式） | ⭐ **私の court** ⇒ 8.2 で裁定 |

### 8.2 ⭐ P3 の裁定 — 名前 token をやめ、構造で同定する

⛔ **採らない案 = `ARM_TOKEN` に `"ur15"` を足す。** 理由 2 つ:
1. **識別性が上がらない。** token 一致は「腕である」ことを測っていない（機種名の文字列を測っている）。次の機種でまた同じ壊れ方をする。
2. **今の STOP は設計どおりの停止であり、沈黙の誤りではない**（p18 `-007` (3) と同旨）。⇒ **STOP を消す方向の修正**は、壊れていることを隠す方向である。

⭐ **採る案 = 構造ベースの同定。** 規則の要件（設計要求として記す。⛔ 実装はしない = p0、独立検証 = pZ）:
- **腕 = revolute の連鎖**として同定する（機種名を見ない）。UR15 / UR5e とも **revolute 6** ゆえ同じ規則で両方通る。
- **EE = その連鎖の末端**から topology を辿って決める（`+5` のような固定オフセットを使わない）。
- **pad / 爪 = gripper サブツリーの body 階層**から決める（`(9, 13)` のような literal index を使わない）。⚠ literal `(9,13)` の除去は **p0 の繰越（authorization 待ち）**であり、私はここで規則を定義するだけ。
- **stride は as-built から読む**（8 節冒頭の精度注記）。

⭐ **positive control（規則の受け入れ条件・両方満たすこと）:**
1. **UR5e model で、従来と同一の分類を再現する**（腕 2 本・従来の EE / pad と同じ body に着地）
2. **UR15 model で、腕 2 本を返す**
⇒ **片方でも落ちたら規則を採らない。** ⛔ 「UR15 で通った」だけでは受け入れない（従来を壊していないことが示されない）。

⛔⛔ **合否の読み取り方（設計要求・p18 `MSG-P18-ADVISORY-WRAPPER-RC-MASKING-20260727T1105JST-009` を受け、私が自分で再現した）:**
**上の positive control の合否を、プロセスの終了コードで判定してはならない。** 私の実測（2026-07-27 11:0x JST・`sys.exit(3)` するだけの probe）:

| 実行形 | 標準出力 | rc |
|---|---|---|
| 直呼び `/home/rlrk/env_isaaclab7/bin/python probe.py` | `probe ran` | **3**（正しい） |
| `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p probe.py` | `probe ran` | **0**（⛔ 非ゼロが飲まれる） |

裏づけ = `AGENTS.md:68` 逐語「`./isaaclab.sh -p` can mask non-zero Python exits」。
⇒ ⭐ **判定は artifact の中身から読む** — 分類規則なら **腕の本数・EE / pad として同定された body id そのもの**を出力させ、それを照合する。⛔ **「落ちるべき入力で落ちること」を wrapper の rc で確かめると、あらゆる失敗が成功に見える。** ⇒ **本 disposition が要求する positive control・negative control は、すべて出力内容ベースで定義する。**
⚠ import 解決のために wrapper を使うのは妥当であり、変更しない（これは rc に依存しない結論）。
⭐ **ただし「wrapper を使え」を一律の規則にはしない**（§6 の撤回）: **rc を証拠にする検査は直呼びで走らせる**（`AGENTS.md:68` が是認）。⇒ **control の実行形は「その control が何を証拠にするか」で決める。**

### 8.3 順序

**P1 ∧ P2 ∧ P3 → H-0（as-built topology を読む）→ H-2（`M` / `τ_bias` / `ζ`）→ H-4（Jacobian・3 参照点）→ H-3 / H-3.1 / H-5 / H-5.1。**
⛔ **gate 状態は不変** — H-3.1 no GO / H-4 全体 HOLD は再測定で flip しない。

### 8.4 範囲

**対象は H-2 / H-3 / H-4 に留まらず、H-0 〜 H-6 の全体になり得る**（p0 / pZ 申告 = banked 測定はすべて UR5e 構成。⚠ この (1) は p18 未再測・私も未再測 ⇒ **申告として扱う**）。
⛔ **廃棄範囲（他の UR5e 由来 evidence にどこまで及ぶか）は決めない** — DDR #39 のとおり未判断であり、私が推定してよい対象ではない。**私が言えるのは「私の spec が定義する量はすべて robot 依存」まで。**

### 8.5 (c) p4 暫定値の扱い

§2 の disposition のとおり（採用 3 / 不採用 2 / GATED 1 / 条件付き保留 1）。⭐ **追加の 1 点:** **不採用とした servo 定数（`armature` / `damping` / `kp` / `kv`）を UR15 生産 env の default に置かない。** 置くと、後で **「測った値」と「置いただけの値」が区別できなくなる**。⇒ 生産 env に入れるのは **測定後**、または **「未測定の仮値」と機械可読に明示した形**でのみ。

## 9. ⭐ ケーブル径の矛盾（Ø8 設計 vs Ø10 実行）— 私の court の裁定

p18 `MSG-P18-P11-DISPOSITION-RECEIPT-20260727T1112JST-012` (2) が pane をまたぐ矛盾を回付した（出所 = pB の log 解析）。⛔ **他 pane の message の数値では裁定しないので、私が source を読んだ。**

**私の実測（2026-07-27・`p4_ur15_sim_20260727/`）:**

| 実測 | 値 | 出所 |
|---|---|---|
| 材料 run のケーブル半径 | `CABLE_R = 0.005` ⇒ **Ø10.00 mm** | `ur15_steps.py:47`（mujoco の capsule `size` は半径）。script 自身の注記 `:70` も「cable is 10 mm」 |
| ⭐ **同じ値が材料の 3 script すべてに在る**（私が p18 / pB より広げた点） | `ur15_cell.py:42` / `ur15_steps.py:47` / `ur15_route.py:43` とも `0.005` | ⇒ **1 file の書き損じではなく、材料全体が Ø10 前提** |
| 設計 SSOT | `CABLE_RADIUS = 0.004` ⇒ **Ø8.00 mm** | `task_config.py:137` |
| asset の設計意図 | 「two protruding box claws **wrap the Ø8 cable** … gap ~10 mm」 | `2f85_koshape.xml:9-11` 逐語 |
| ⭐ **材料は SSOT を読んでいない** | `ur15_steps.py` は `task_config` を **import していない**。SSOT 参照は `:55` の **コメント** 1 行（`GRIP_HALF_SPAN = 0.044  # task_config.py:235 @ …`）＝ **手写し** | ⇒ 乖離が起きても機械的に検出されない |

**裁定:**

1. ✅ **設計値は Ø8.00 mm のまま**（§2 項目 7 の採用は変えない）。SSOT と asset の設計意図が一致しており、材料の実行値はこれを動かさない。
2. ⛔ **材料の把持系の量（パッド間隔・接触・把持成否）は、Ø8 の設計判断の裏づけに使えない。** 別条件の測定だからである。⇒ §2 / §4 の判断は**材料に接地していない**ので変更なし。
3. ⭐ **公称 clearance の再計算（算術のみ・新規測定なし）:** 爪の内側 gap **10.00 mm**（§4）に対し **Ø10.00 mm ⇒ 公称 clearance 0.00 mm**／**Ø8.00 mm ⇒ +2.00 mm**。
   ⛔⛔ **ただし「公称 clearance 0.00 mm」は幾何の量であって、接触の予測ではない。** 実際に保持が起きるかは接触・貫入・solver の挙動に依存し、**UNMEASURED**（私の B6 撤回どおり）。⇒ **pB の非把持観測と整合する候補説明**ではあるが、⛔ **原因の認定ではない。** 物理妥当性の最終基準は Rs の動画。
4. ⭐ **反証（control）の要否 = 要る。** 材料を今後 evidence として使うなら、**同一 script を SSOT の Ø8 で 1 回**回して非把持が消えるかを見る。**規律 = 変える軸は径の 1 本だけ**（script・姿勢列・seed・その他定数を同時に変えない）。⚠ **消えても「把持が成立した」ことにはならない** — それは Rs 動画の判断であり、control が言えるのは「径が効いていたか」だけ。⛔ **実行認可は求めない（RUN CLOSED）。** 実施可否は p4 との共同 court ＋ gate。
5. ⭐⭐ **原因側の設計要求（本件の本丸・値ではなく機構）:** **生産 env は径を SSOT から読む。hardcode しない。**
   - `CABLE_RADIUS` を含む**寸法定数は `task_config.py` から import して使う**（コメントで出所を書き写す方式を採らない）。
   - 手写しは **乖離しても機械的に気づけない**。実際、`GRIP_HALF_SPAN = 0.044`（`:55`）も同じ手写しであり、これは §0#2 の 88 mm 由来ゆえ **DDR #38 で pending の前提を黙って運んでいる**。
   - ⇒ **同型の乖離の再発を止めるのは、値の訂正ではなく参照経路の固定である。** 実装は p0・独立検証は pZ（⛔ 私は実装しない）。

## 10. p18 `-012` (3) の回答を受けての更新

| 照会 | p18 の回答 | 私の状態 |
|---|---|---|
| Q1 ヨーク幾何の court | ⛔ **私の court ではない**（charter は腕・指の各ステップ駆動。base / 構造は DDR #40 = p5 ＋ §0#2 = Rs に跨る）。court の確定自体は p18 の権限外ゆえ **Rs へ escalate 済** | ✅ **§2 項目 1 の GATED を維持**（何もブロックしていない）。⛔ 私はヨーク幾何を決めない |
| Q2 DDR #39 の owner 割当 | 既存 banked 体制と整合。⛔ ただし **register 記入 custody = p6** ゆえ **記入までは「提案」の地位** | ✅ **§8.1 / §3 の役割記述は「提案」として読む**。⛔ 割当済として扱わない |
| Q3 §0#4 gripper LOCK | ⛔⛔ **FOUNDATIONAL ゆえ Rs 専権・Rs へ escalate 済**。私の「p0 は移植 model を出発点にしない／出発点は banked `2f85_koshape.xml`」は p18 が支持し p0 へ伝達 | ✅ 維持。**LOCK 保存の検証が済むまで移植 model を出発点にしない** |

---
**p11 custody = 2026-07-27 / ARM-CONTROL-DESIGN (`w2:p11`)。⛔ 本書の bank commit と sha256 は提出 message の宣言値が権威**（本書は自身の commit を pin できない）。
