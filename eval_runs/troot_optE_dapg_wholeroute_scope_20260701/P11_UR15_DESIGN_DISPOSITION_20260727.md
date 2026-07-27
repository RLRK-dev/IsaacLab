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
**上の positive control の合否を、プロセスの終了コードで判定してはならない。** 私の実測（`sys.exit(3)` するだけの probe。⛔ **旧記載の時刻「2026-07-27 11:0x JST」は撤回** — **私は `date` を実測せずに書いた**＝ `CLAUDE.md` §運用27 の date-THEN-write 違反。⇒ **時刻は書かず、測定を含む版を bank した commit の author time を権威とする**。再現手順は下表そのもの）:

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

## 11. コ字爪 LOCK の差分と、**反証 control の再設計**（p18 `MSG-P18-IMPLCHAIN-KOSHAPE-LOCK-DELTA-20260727T1126JST-017`）

⛔ **他 pane の数値では裁定しないので、私が両 model を読んだ。** custody = 測定 artifact `P4_KOSHAPE_LOCK_DELTA_MEASUREMENT_20260727.md` sha256 `4c2a51d3508f27c0ff9d58c1463807c35be650b9b7c086198282fc453afd3464` @ `03d924b3128e617acecb1ed979d35b91ec38ff45`／banked LOCK asset sha256 `a3bef79ee9b4f4161dd6da20967e65e0da78f5706724fbf61e35fb43ba230ba3` @ `85315bbec6787a9cfcb3cb147c87fb78beb3b5ca`（**両方とも私の実測で一致**）。

### 11.1 私の実測（3 点）⚠ **すべて file の面の測定である**（11.6 の限定を先に読むこと）

| 対象 | banked `2f85_koshape.xml` | p4 移植版 `_ur15_2f85_koshape_actuated.xml` | 判定 |
|---|---|---|---|
| ⭐ **LOCK の対象＝コ字爪 4 geom** | `right/left_pad_f1ext` `f2ext`（`size 0.011 0.009 0.0012` / `pos 0 -0.0026 0.0382` と `0.0258` / `quat` / `friction 0.7` / `solimp` / `solref` / `priority 1`） | **同一** | ✅ **byte 同一 = LOCK 対象の幾何は保たれている** |
| **A tendon** | `<tendon>` **削除済**（`:188-194` は削除理由のコメント。逐語 = 結合 build が `SolverMuJoCo` の `_init_tendons`（`solver_mujoco.py:2165`）で OOB crash ／「**NOT a faithful gripper** — the Robotiq 4-bar grasp is **rebuilt at S5**」） | `<tendon>` node が **`:169-174` に在る** | ⚠ **差分（宣言つきなら許容余地あり・11.3）。⛔ *file に在る* だけで、**それが駆動に効いているかは未測定**（11.6） |
| **B 接触除外** | **7 行**。うち `:176` `<exclude body1="right_pad" body2="left_pad"/>`。直前コメント **`:173-175`** 逐語（⚠ **旧記載 `:174-175` は私の欠陥** — p18 の message から引き写し、しかも **174 から始まる窓**で確認したので食い違いようがなかった。実測 = `:172` が `<contact>` / コメントは `:173-175` / exclude が `:176`）=「Prevent claw-claw self-collision jam at the scripted close（the protruding コ claws f1ext/f2ext can overlap at `GRIPPER_CLOSE_QPOS`）. **Cable contact is UNAFFECTED**（the cable is a separate body）」 | **6 行**。⛔ **`right_pad`×`left_pad` の 1 行が無い**（他 6 行は一致） | ⛔ **file 面では脱落 = 欠陥。** ⚠ **build 後の `mj_model` で当該 exclude 対が生きているかは未測定**（11.6） |

### 11.2 clearance 説の現在地 — ⛔ **本節の旧版（「Ø6 で反証された」）を撤回する**

⚠ **経緯:** 私は本節の旧版で「Ø6〜Ø10 のいずれの径でも爪に入らなかった ⇒ clearance 説は反証された」と書いた（commit `961fd5c5dbabd52381a373dc6e12111522c855a3` 時点）。**その反証は原因側（p18）が撤回した**（`MSG-P18-IMPLCHAIN-WITHDRAW-O6-REFUTATION-20260727T1133JST-019`・発端は p4 の STOP）。理由 = 「入らなかった」の述語が **p4 が既に撤回済の述語（上下 *両方* の板に接触）** だった。撤回済述語を外して同じ probe を読み直すと、**slot 開口 27.0–37.0 mm に対し着座中心は Ø10=32.5 / Ø9=33.0 / Ø8=33.5 / Ø7=34.0 / Ø6=34.3 ⇒ 全径で中心は slot の中**。⇒ **「Ø6 でも入らなかった」は成立しない。**

⭐⭐ **正しい現在地（過剰訂正をしないために明示する）:**
- ⛔ **反証が無効になったことは、clearance 説が正しいことを意味しない。**
- ⇒ clearance 説は **反証前の地位 = 候補仮説・未検証** に戻る。⛔ **確立でも優先でもない。**
- ⚠ **p4 の probe はそもそも「捕捉できるか」を一度も試していない**（ケーブルは slide joint・軸 `0 0 1` で **z のみ拘束**され、slot の x, y には**構成上置かれていた**）⇒ **clearance 説を支持も反証もしない。**
- ⇒ ⭐ **捕捉についての証拠は、どちらの向きにも、まだ 1 つも無い。** 私の §4 の「form closure 前提は banked 設計と整合」は**設計意図の一致**であって、**成立の証拠ではない**（元からそう書いている・変更なし）。

⭐ **影響を受けないもの（同じ検査に通した）:** 除外行 1 行の脱落という **file 面**の事実（banked `:176`）／banked コメントの警告／**パッド間隔 24.2 mm 停止**の観測／**開口 10.00 mm** という量／**Ø10 が SSOT 逸脱**であること（§9 (1)(2)(5) は不変）。⚠ ただし **除外の件は file 面であって model 面は未測定**（11.6）。
⛔ **因果は私も判定しない**（物理妥当性の最終基準は Rs 動画）。

### 11.3 §0#4（gripper geometry LOCK）— 私の技術的読み（⛔ 裁定は Rs）

- ⭐ **LOCK の対象は「コ字フィンガの幾何」**（RS71 §0#4）。**その 4 geom は byte 同一**（11.1）⇒ **私の読みでは A / B は LOCK 対象の幾何を変えていない。**
- ⛔ ただし **§0#4 抵触の可否は FOUNDATIONAL ゆえ Rs 専権**。私は**材料として技術的読みを出すだけ**で、判定しない（escalate 済）。
- ⚠ **別建ての問題として、model 同一性は失われている。** 特に **B は §0#4 と無関係に欠陥**である — banked のコメントが**まさにその症状（全閉で爪同士が噛む）を事前に警告している**。⭐ **かつ同コメントは「ケーブル接触には影響しない」と明言**しており、**除外行を戻してもケーブル側の物理は変わらない** ⇒ **戻すことに副作用が無い**。

### 11.4 ⭐ 設計要求（原因側・§9 (5) と同じ形）

1. **測定・生産に使う model は、banked asset から *宣言された差分* として導出する。** 手で組み直さない。⇒ **B のような脱落が黙って発生しない。**
2. **接触フィルタ（`<exclude>` 集合）は banked のまま持ち越す。** 駆動を足すことと、接触フィルタを削ることは別である。
3. ⛔⛔ **A（tendon 復活）は素の MuJoCo の probe に限る。生産経路（Newton / SolverMuJoCo）では復活させない** — 削除理由は Newton 側の crash（`_init_tendons`）であり、生産は Newton だからである。⇒ **駆動は banked コメントの方針どおり code 側で組む**（「the Robotiq 4-bar grasp is rebuilt at S5」）。

### 11.5 ⭐⭐ 反証 control の再設計（私の court・⛔ 実行認可は求めない）

§9 (4) で私が定義した control は **径 1 軸**だった。⛔ **現在、候補軸は 3 本ある**（`-019` 6 と同じ数え方）:

| 軸 | 中身 | 接地 |
|---|---|---|
| **α 径** | Ø8（SSOT）対 Ø10（材料の実行値） | §9・私の実測 |
| **β 除外行** | `right_pad`×`left_pad` の脱落 | 11.1 B（⚠ **file 面のみ**・11.6） |
| **γ 駆動経路** | **tendon 復活で、爪を閉じる駆動経路そのものが banked と違う** — banked は tendon 結合が不在**かつ**取り残された `actuator general tendon="split"` も parse 時に skip されて不活性（banked file 自身の記述）。移植版は素の MuJoCo で tendon を復活。⇒ **「全閉指令でパッドが 24.2 mm で停止」を単独でも説明し得る**（pZ 発・`-019` 5） | banked file の逐語 ＋ 11.1 A |

⛔⛔ **⇒ 除外行だけを 1 軸で戻しても、γ が未統制のままなので解釈できない**（陰性でも β を免責できず、陽性でも交絡し得る）。⚠ **2 軸を同時に変えれば、なお分離できない。**

### ⭐⭐ 私の裁定 — **実験で交絡を解くより、構成でやり直すほうが安い**

3 本の軸を実験で切り分けるには最低 3 run が要り、しかも **β は現行 harness では「軸が動いた」ことすら確認できない**（11.6）。⇒ **先に構成を直す。**

- **C-0（実験ではなく構成・11.4-1 の再掲）:** **測定 model を banked asset から *宣言された駆動差分* として導出する。** ⇒ **β は構成上消える**（exclude 集合を継承するため）。⇒ **γ は「宣言された 1 つの駆動経路」に定まる**（⛔ 生産経路では tendon を復活させない = 11.4-3）。
- ⇒ **残るのは α だけ**であり、**設計値はもともと Ø8** ゆえ、**設計判断のためには α の control すら要らない**。α が要るのは **旧材料の失敗を帰属させたい場合だけ**である。
- ⭐ **旧材料の帰属は、設計を進めるための必要条件ではない。** ⇒ **私は「3 軸の切り分け run」を設計上の必須にしない。**

⚠ **それでもなお旧材料に帰属させたい場合の規律**（p4 との共同 court）: **1 度に 1 軸**・**各軸の変更が `mj_model` で起きたことを確認**（11.6）・**述語は閉じるか / 保持するかを分ける**（下表）。

| | 変える軸（**1 本だけ**） | 他は固定 | ⭐ 観測する述語 | 何が言えるか |
|---|---|---|---|---|
| **C-1**（先） | **`<exclude right_pad × left_pad>` を戻す** | **径は run の Ø10 のまま**・script・姿勢列・その他定数すべて不変 | ⭐ **全閉指令でのパッド間隔が 24.2 mm を下回るか**（＝ **閉じるか** の述語。⛔ 把持の述語ではない） | 「そもそも閉じていない」かどうか。**閉じないなら径は効きようがない**（爪がケーブルに届かない）。⛔⛔ **前提条件 = 11.6**（`mj_model` の exclude 対を読めること。読めないなら **軸が動いた確証が無く、結果が解釈できない**） |
| **C-2**（C-1 の後だけ） | **径を SSOT の Ø8 にする** | 除外行は戻したまま・他すべて不変 | ⭐ **爪チャネル内の保持**（⛔ **パッド接触ではない** — 2 状態を見分ける述語にする） | 径が保持に効くか |

**規律（両 control 共通）:**
- ⛔ **合否を終了コードで読まない**（§8.2）。**出力内容**（パッド間隔の数値・保持の判定に使った body / geom）から読む。
- ⚠ **C-1 で閉じても、C-2 で保持しても、「把持が成立した」ことにはならない** — 物理妥当性の最終基準は **Rs の動画**。control が言えるのは **どの軸が効いたか**だけ。
- ⚠ **A（tendon）は移植版と banked で異なるため、C-1 の解釈には「駆動機構が banked と別」という限定が付く。** ⇒ 11.4-1 の「宣言された差分として導出」を先に満たせば、この限定は消える。
- ⛔ **実行認可は求めない（RUN CLOSED）。** 実施可否は p4 との共同 court ＋ gate。

### 11.6 ⛔⛔ file の面と model の面は別 — **述語を model 側に置く**（p18 `MSG-P18-IMPLCHAIN-EXCLUDE-CLAIM-SCOPE-20260727T1130JST-018` を受けた、私の court の要求）

**11.1 の A / B は XML text の差であって、build 後の `mj_model` で当該機構が生きているかを測っていない。** ⇒ **私の §11 の読みを、その分だけ弱める。**

⭐ **この asset の中に、file と runtime が一致しない実例が既に在る**（banked のコメント逐語・私が読んだもの）:
- `<equality>` の 4-bar は **`add_mjcf(skip_equality_constraints=True)` により parse 時に落ちる**（file 編集ではない）
- 孤立した `<actuator general tendon="split">` は **tendon 名が解決できないと parse 時に黙って skip される**（`import_mjcf.py ~:2417` の無条件 `continue`）

⇒ ⛔ **「file に在る / 無い」から「model で効いている / いない」を導けない経路が、この asset には実在する。** ⇒ **B の脱落が閉じ切らない症状を説明する、という読みは file 面からの候補仮説であり、機構が runtime で有効かも未確認**（より弱く読む）。**A も同様** — `<tendon>` が file に在ることは、それが駆動していることを意味しない。

**⇒ 設計要求（私の court・実装は p0 / 検証は pZ）:**
1. ⭐ **正しい述語 = `mj_model` の exclude 対の集合**（file の diff ではない）。**C-1 の「戻した」の確認も、これで行う。**
2. ⛔ **現行 harness はこれを記録していない。** ⭐ **私が producing commit で自分で確かめた**（当初は p0 / p18 の申告を写していた・§14）: `746f049e8357aead0f28c48be1588c9ef2fee005:arm_control_measurement_harness.py` の MJCF 由来 field は `nu` / `nq` / `nv` / `nbody` / `neq` / `eq_type` / `actuator_forcerange` / `actuator_trnid` / `jnt_actfrcrange` / `actuator_ctrlrange`（`:401`）である。**閉じた query（当該 commit の当該 file 全 1589 行・⛔ `head` / `tail` を通していない）で `exclude` / `nexclude` / `contact_pair` を検索した結果、接触対を記録する probe は 1 つも無い**（一致した 12 行はすべて「FK model を測定から除外する」という英文の散文であり、接触の除外ではない）。⇒ ⛔ **p0 の既存 banked 出力を「除外行が在る / 無い」の根拠に使わない。**
3. ⇒ ⭐ **H-0 inventory に「build 後の接触フィルタ状態（exclude 対の集合）」を記録項目として加える**ことを、**測定 spec 側の要求**として出す。⚠ **実装は authorization 待ち**（p0 の繰越）。⛔ **これが入るまで C-1 を回しても、軸が動いた確証が取れない。**
4. ⭐ **一般形（本 lane の既存要求と同じ形）:** **「宣言した機構が build 後に生きていること」を記録する項目が無いなら、その機構に依存する control は成立しない。** ⇒ §8.2 の「合否は出力内容から読む」と同根であり、**読む対象を file でなく model にする**、という点が追加分である。

## 12. 視覚レグの着地・出発点の blocker 解消・軸の更新（p18 `MSG-P18-IMPLCHAIN-VISUAL-VERDICT-AND-COMPILE-BLOCKER-20260727T1140JST-020`）

### 12.1 視覚レグ（独立・フレームのみ）が着地した — evidence 状態の更新

⚠⚠ **本節は 2 つの別物を分ける（私の記録点検 → p18 `-041` で原因側が確定した）。** ⭐ **対象の同一性は私も確認**した — 動画の sha256 を自分で計算し `fc4fd4f3c538cd79f30559b3045d7b3d3ae4ff5f8b6614d494c4871cdcc14e83` と一致。

**(A) ✅ 私が採るもの = pC（VIDEO-ANALYST）の banked レグ — 私が自分で読んだ**
custody = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/UR15_KOGRASP_VIDEO_LEG_pC_20260727.md` @ `57433c92f64e333cfc4adfbbe3258617573e67e9`（sha256 `89fc2c59cec8c6c4a8c80cfcd28d8103afab6a9b2109eccc2becafca0c082ddc`・**私の実測で一致**）。
- **観測:** **サンプルした 18 時刻・両アームとも、赤板と青板の間の開口にケーブルを認めない。** ケーブルは爪の外側（上・下・横）を通る。**決定的 = `f600`（2 視点一致）**／`f250` `f350` ではケーブルが爪の上面を斜めに横切る。
- **計器の適格性を先に検定している**（mean luma 75.7 = Rs が判定できた版と同水準・2 視点・3×/5× 拡大）⇒ **judge-fit の検定を経ている。**
- ⭐⭐ **pC は開口 10.00 mm を asset 定義から独立に導いている**（中心間 12.40 mm − 2 × 半厚 1.2 mm）⇒ **私の §4 の値の独立確認**（同じ数に、別の者が別経路で到達した）。
- ⛔ **pC 自身の限界（そのまま carry する）:** ①**悉皆ではない**（1029 frames 中 **18 時刻**）②色による自動判定は**識別力が無いとして根拠に使っていない** ③2 視点は**同一 run の同一レンダリング** ④ **`f600` の接触と屈曲は観測されるが、屈曲が爪に押された結果かは動画単独では分離できない**（分離には爪を止めた対照が要る）。
- ⛔ **pC は verdict を出していない**（物理妥当性は Rs 専権）。⇒ **私も「判定」としては扱わない。**

**(B) ⛔ 私が採らないもの = 旧記載の ①〜⑤（p4 の報告）**
p18 `-041` により、**旧 §12.1 の ①〜⑤ は p4 の報告**であり、**判定者・path・judge-fit は未確認**と確定した（p18 も判定者を確認していない）。⚠ **内容も (A) と同一ではない** — 「顎の閉は 1 回のみ」「持ち上げ無し」「溝は最終フレームまで空」「貫通なし」は **pC のレグには無い**。⇒ **これらは attribution 待ちとし、私は使わない。** ⛔ 両者が同一作業か別 pass かは**誰も判定できていない**ので、私も埋めない。

⇒ ⭐ **本節が支えるのはここまで:** **サンプルされた 18 時刻・両アームで、開口にケーブルは無かった。** ⛔ **「全編で起きなかった」とは言わない**（悉皆でない）。⛔ **設計の否定でもない**（form closure の設計意図は不変）。
⭐ **下流の帰結は視覚レグに依存しない** — 「材料は保持についてどちら向きの主張も支えない」は **§9 と §11 で独立に成立**する（材料は SSOT と別の径で走り、probe は捕捉を一度も試していない）。

📎 **HISTORICAL / 出所未特定（上の (B)）— ⛔ 本行の主張を私は使わない。** 旧 §12.1 は対象（`media/ur15_steps_c1c2_20260727_0850.mp4` sha256 `fc4fd4f3c538cd79f30559b3045d7b3d3ae4ff5f8b6614d494c4871cdcc14e83` / 34.30 s / 1029 frames）に対する **5 項目の観察**を「判定」として載せていた。**そのうち「開口にケーブルが無い」は (A) の pC レグが 18 時刻サンプルで独立に支えるが、残る 4 項目（顎の閉動作の回数・持ち上げの有無・溝が最終フレームまで空・貫通の有無）は pC のレグに無く、判定者も未確認である。** ⇒ ⛔ **本行は記録として残すだけで、以後の根拠にしない。**

⇒ ⭐ **私の §4 の位置づけを、ここで正確にする:**
- ⭐ **(A) が支えるのはここまで:** **サンプルされた 18 時刻・両アームで、開口にケーブルは無かった。** ⛔ **「保持も着座も起きなかった」とは言わない** — 着座・持ち上げは **(A) の観測範囲に無く、(B) は出所未特定**だからである。⇒ 材料は **保持についてどちら向きの主張も支えない**（**この帰結は §9 (2) が独立に与える**）。
- ⛔ **これは設計の否定ではない** — 観測されたのは **この 1 本の run** であって、**form closure という設計意図（asset `:9-11` 逐語）は依然そのまま**。
- ⇒ ⭐ **捕捉の証拠は、依然としてどちら向きにも 0 件。** 私は §4 を変更しない。

### 12.2 ⭐⭐ 着座述語も見分けていなかった（**把持述語に続く 2 例目**・私の court の設計要求）

p4 が撤回: log の `pinC1` 発火を `seat=[0.15, 0.35, 0.87]` として「C1 着座＋クリップ保持 作動」と報告した件。**視覚では最後まで溝は空**。⇒ ⛔ **着座判定が、着座していない状態で真になった。** pB の所見（`pin=C1` は着座の証拠にならない）が視覚側から独立に裏づけられた。

⇒ **設計要求（追加）:** **着座・保持・把持の各述語は、区別したい 2 状態を実際に見分けること。** 受け入れには **negative control**（**着座していない状態で偽になること**）を要求する。⛔ 「機構が発火した」ことを「状態が成立した」の証拠にしない。⚠ **これは §8.2 / §11.6 と同じ形が 3 度目に出たもの**である（合否を rc で読む／file を model の代わりに読む／発火を状態の代わりに読む）。

### 12.3 ⛔⛔ 私の指示の blocker と、その解消（私の court）

**blocker（p18 実測・私も再現した）:** banked LOCK asset `2f85_koshape.xml` は **素の MuJoCo で compile できない** — `ValueError: Error: transmission target 'split' not found in actuator 0 / Element name 'fingers_actuator', id 0, line 213`（該当 `:213` = `<general class="2f85" name="fingers_actuator" tendon="split" …>`）。⇒ 私の「**出発点は banked `2f85_koshape.xml` の爪幾何**」は、**素の MuJoCo 基盤ではそのままでは満たせない。**

⭐ **解消の鍵（p0 の実測）:** banked 側 build の `nu = 12`、`actuator_trnid` の対応 joint は **0–5 と 14–19 = 腕関節 12 本のみ**で、**gripper 関節に対応する actuator が build 後の model に 1 本も無い**。⇒ banked file `:191` の逐語「the orphaned actuator … is **SILENTLY skipped at parse**」が **runtime で確認された**（**file≠runtime の 2 例目**。1 例目 = `neq 0`）。

⛔⛔ **重大な限定を後から付ける（私の実測・p18 `-042` C-2/C-3）— 私の「runtime-neutral」の射程はこれで狭まる:**
**その `nu = 12` の build は指の servo を結線していない側（flag-OFF）である。** 私が自分で読んだ接地 = `thread_isaac_lab/envs/newton_skill_env_base.py:1502` の既定 **`grasp_actuation=False`**／`thread_isaac_lab/envs/newton_route_env.py:283` 逐語「**A flag-OFF build has 0 such actuators -> raises**」（`servo_readback_assert` は `gainprm[0] == KE` の actuator が**ちょうど 4 本**であることを要求する）／`thread_isaac_lab/configs/task_config.py:314-315` の **`GRIPPER_SERVO_TARGET_KE = 66.7` / `KD = 2.0`**。
⇒ ⛔ **「production runtime に gripper actuator は元から無い」は誤り** — 正しくは **「測られた flag-OFF build には無かった」**。**flag-ON build は誰も測っていない。**
⇒ ⭐ **したがって「孤立 actuator を落とすのは runtime-neutral」は、*flag-OFF build に対して* 成立する主張であり、production 一般に対する主張ではない。** ⛔ 逆に「生産基盤では指を閉じられない」とも読まない（**どちらも未測**）。**derived model を作る際は、どちらの flag で建てるかを宣言差分に含める。**

⇒ ⭐⭐ **私の裁定（指示の撤回ではなく、実行可能な形の確定）:**
- **出発点 = banked の「爪幾何」＋「`<exclude>` 集合」を継承した *derived model*。** ⛔ **LOCK file 自体は編集しない**（derived は別 file）。
- **宣言差分は 2 つだけ:**
  1. **孤立 actuator（`:213`）を derived から外す。** ⭐ **production 経路に対して runtime-neutral** — 上記のとおり元から runtime に存在しないからである。⇒ **落としても production の挙動は変わらず、素の MuJoCo で load 可能になる。**
  2. **駆動を明示的に足す。** ⛔ **production 経路では `<tendon>` を復活させない**（削除理由は Newton 側 `_init_tendons` の crash・11.4-3）。**banked コメントの方針どおり code 側で 4-bar を組む。**
- ⇒ **既存の拘束は不変**: **p0 は移植 model を出発点にしない。**

⭐ **精度（p18 `-025` 2 ＋ 私の再実測）:** banked の `<actuator>` block は **`:212-215`** で、その中の actuator は **`:213-214` の `fingers_actuator` ただ 1 本**（**`:37` の `<general biastype="affine"/>` は `:35` の `<default class="2f85">` 内の宣言であって actuator 実体ではない**）。⇒ **孤立 actuator を derived から外すと、その file の actuator は 0 本**になり、**production build の実測（gripper 関節に対応する actuator が 0 本）と一致する。** ⇒ runtime-neutral の主張はこの点でも整合する。
⛔ **本裁定は §0#4 の Rs 裁定を先取りしない。** derived が **LOCK 幾何をそのまま継承する**形は Rs 判断を待つ間も安全側だが、**抵触可否そのものは未決のまま**である（11.3）。

### 12.4 軸の更新（**4 本**）— 格下げを漏らさず carry する

| 軸 | 地位（**格下げ込み**） |
|---|---|
| **α 径** Ø8 対 Ø10 | **候補・未検証**（11.2 のとおり反証も支持も無い） |
| **β 除外行の脱落** | ⭐ **transplant では runtime でも実在**（p4 実測 = compile 成功・`nexclude 6`・`right_pad↔left_pad` 不在・`ntendon 1` / `nu 1` / `neq 3`）⇒ **11.6 の留保は transplant については解消**。⚠ **banked 側の runtime exclude 集合は 12.3 の blocker によりこの基盤では測定不能のまま** |
| **γ 駆動経路差** | ⚠⚠ **pZ が格下げ済 = file 面＋推論の候補仮説・model 面は未測定**（`-019` 5 は格下げ抜きで届いていた。p18 の伝達漏れ）。⛔ **旧記載にあった時刻表記は削除**（⛔ **値は再掲しない** — 再掲すると本行自身が「未実測の時刻」の走査に当たる。`-013` R1 と同型ゆえ、自分の先例を適用する）— その時刻は **p18 の stamp（`-009`〜`-029`）に由来し、p18 自身が未実測として撤回した**。**格下げという事実は維持**（p18 は技術内容を維持している）。⭐ ただし **p0 の `nu` 実測は banked 側の gripper actuator 不在を裏づける**。⛔ **`nu` の数値を両者で直接比較しない** — banked 側は腕込みの production assembly、transplant は gripper 単体の別 assembly であり、**同じ量ではない** |
| **δ ケーブル剛性**（⭐ 新規） | p4 が**認可なく** `stiffness 0.02 → 0.12` / `damping 0.004 → 0.010` に上げたと申告。⛔ **因果は誰も主張していない**。⇒ **材料にはもう 1 本、統制されていない差分がある** |

⇒ ⭐⭐ **4 本になったことは、§11.5 の裁定（実験で交絡を解くより構成でやり直す）を強める。** 実験で帰属させる costs は **4 軸 × 各軸の「動いたことの確認」** に増える一方、**C-0（banked からの宣言差分として導出）は β を構成上消し、γ を 1 経路に定め、δ を宣言値に固定する**。⇒ **私は引き続き、旧材料への帰属を設計上の必須にしない。**

### 12.5 ⛔ 12.3 の射程を直す — blocker は **基盤に付く**（p18 `MSG-P18-IMPLCHAIN-COMPILE-BLOCKER-IS-SUBSTRATE-SCOPED-20260727T1147JST-024`）

**私が自分で確認した接地:** 生産経路は **同じ banked file を出発点にして現に build している** — `thread_isaac_lab/scripts/test_newton_clip_routing.py:161` `ROBOTIQ_STRIPPED_XML = os.path.join(_UR5E_ASSET, "robotiq_2f85", "2f85_koshape.xml")`、使用箇所 `thread_isaac_lab/envs/newton_skill_env_base.py:1564` / `:1570`（両腕とも `robotiq_xml=ROBOTIQ_STRIPPED_XML`）。

⇒ **12.3 を次のとおり限定する:**
- ⭐ **生産基盤（Newton `add_mjcf` ＋ SolverMuJoCo）では、「出発点は banked `2f85_koshape.xml`」は *既に成立している*。** ⇒ **12.3 の derived model ＋ 宣言差分は、この基盤では load 可能性のためには不要。**
- ⛔ **12.3 の裁定が要るのは、素の MuJoCo を target 基盤にする場合だけ**（`:213` の `ValueError` は**この基盤限定の実測**）。
- ⛔ **12.4 β 行の「測定不能」も言い過ぎ** ⇒ 正しくは **「現行の記録項目では未取得」**。生産基盤なら測定可能で、足りないのは **`mj_model` の exclude 対という記録項目**だけ（実装ゆえ authorization 待ち・11.6-3）。**11.6 もこの語で読む。**
- ⚠ **「build できる」は「すべてが生き残る」ではない** — 同じ生産基盤でも `neq 0`（equality 消失）・`nu 12`（腕のみ）である。⇒ **file ≠ runtime の 2 例はそのまま有効**（12.3 の根拠は変わらない）。
- ⚠ **p0 実測では gripper joint に driver 4 ＋ passive 12 が在る**（Newton 側の joint drive）。⛔ **ただし「driver が在る」ことは「指が閉じる」ことを意味しない** — 本 doc が 3 度繰り返している「在る ≠ 効く」と同型ゆえ、ここでも断定しない。

### 12.6 ⭐⭐ 本当の未決 = **UR15 をどの基盤で建てるか**（私の court ＋ Rs）

p0 の基盤は **UR5e**、p4 の移植 sim は **素の MuJoCo**、**UR15 の target 基盤は未定**。⇒ **12.5 のどの枝に入るかは、これが決まるまで決まらない。** ⚠ **これは §8.1 の P1（UR15 の生産 env が無い）と同じ軸である** — env を建てるとは、基盤を選ぶことだからである。

⭐ **私の設計上の推奨（根拠つき。⛔ 決定は Rs — 基盤は env の前提であり私が確定しない）= 生産基盤（Newton / SolverMuJoCo）で建てる。**
1. ⭐ **H 系列の量（`M` / `τ_bias` / 接触）は基盤依存**であり、設計が特徴づけるべきは **production が実際に回す物理**である。⇒ **測る基盤 = 走らせる基盤**。
2. ⭐ **`:213` の blocker がそもそも発生しない**（生産経路は同 file を build 済 = 12.5）。
3. ⛔ **基盤をまたいだ規約の混同は本 project の既知の再発事故**（`prohibited.md` の PhysX / Newton 混同禁止）。**測定だけ別基盤で行うと、その risk を新規に作る。**

⚠ **反対側の考慮も書く:** 素の MuJoCo は起動が軽く反復が速い ⇒ **探索用の probe としては有用**。
⇒ ⭐ **私の裁定 = probe と測定を分ける。** **probe は素の MuJoCo で可。⛔ ただし H 系列の測定と設計値の決定は生産基盤で行う。** ⇒ **probe の結果を設計値の根拠にしない**（本 doc §9 (2) と同じ理由 = 別条件の測定である）。

## 13. 測定記録の要求 — **count は「何を数えたか」と一緒に書く**（照合着地を受けて発行）

**着地した事実**（p18 `MSG-P18-NBODY-RECONCILE-CLOSE-20260727-031`）— ⭐ **行番号は私が producing commit で自分で読んだ**（⛔ message の数値をそのまま置かない）:

| 量 | 出所（**commit とセットで書く**） | 私の実測 |
|---|---|---|
| `body_count`（Newton `Model` の面） | `746f049e8357aead0f28c48be1588c9ef2fee005:arm_control_measurement_harness.py:375` | `"body_count": probe(lambda: int(model.body_count))` |
| `body_labels` | 同 commit `:381` | `"body_labels": probe(lambda: [str(x) for x in model.body_label])` |
| `nbody`（派生 MuJoCo の面） | 同 commit `:392` | `"nbody": probe(lambda: int(solver.mj_model.nbody))` |

⇒ **68 と 69 は別 object の別 field**であり、**どちらも自分の述語の下で正しい**。⇒ **矛盾ではなかった。**

⭐⭐ **行番号そのものが面を持つ（私も再現した）:** **同じ `:381` が、`c16858c666fb5455e536b829c76f20ce0ccc7e4f` では `nbody`、`746f049e8357aead0f28c48be1588c9ef2fee005` では `body_labels` を指す。** ⇒ ⛔ **`file:line` は、値を引いたのと同じ commit とセットで書かなければ腐る。**（pZ の行番号は **pZ が読んだ commit では正確**だった — 欠陥は「動く file の行を commit 名なしで引用した」「値と行番号を別 commit から引いた」ことである。）

⭐ **私が出した world body 仮説は「支持」まで**（⛔ **確認ではない**）: 支持根拠は ①MuJoCo の一般不変則 `nbody` = 宣言 body 数 ＋ worldbody 1（**私も最小 model で独立に実測**）②差が正確に 1 ③Newton 側 `body_labels` の要素数 68・`[0]` が実在リンク ⇒ Newton 配列に world 要素が無い。⛔ **本 build の body 0 の名前そのものは誰も読んでいない**（sim run が要り RUN CLOSED）。⇒ **帰属は 3 本の整合であって直読ではない。** ⛔ **確認のための run は求めない。**

⇒ **設計要求（測定 spec 側・私の court。実装は p0 / 独立検証は pZ）:**
1. ⭐ **inventory の各 count は、値だけでなく「どの object の どの field か」を併記する**（例: `body_count` = Newton `Model` の面 ／ `nbody` = 派生 MuJoCo の面）。
2. ⭐ **数え方の scope を明示する** — **worldbody を含むか**・**名前付き部分系の和なのか model field の直読なのか**。
3. ⇒ **理由:** 本件は「**同じ名前の量が、別の測定面を指していた**」ものであり、**値を突き合わせても解けず、数え方を突き合わせて初めて解けた**。⇒ **本 doc が繰り返し出している形の系**である（合否を rc で読む／file を model の代わりに読む／発火を状態の代わりに読む／同名の量を別の面で数える）。

## 14. ⛔ 私自身の記録欠陥 2 件（時刻）— 原因側は私

p18 が自分の stamp（`-009`〜`-029`）を **未実測として撤回**したのを受け、**同じ検査を自分にかけた**結果、**私の banked artifact にも 2 件**あった。⇒ **どちらも私が書いたものなので、私が直す。**

| 箇所 | 欠陥 | 処置 |
|---|---|---|
| §8.2 | 「私の実測（**2026-07-27 11:0x JST**・probe）」— ⛔ **`date` を実測せずに書いた推定値**（`CLAUDE.md` §運用27 の **date-THEN-write** 違反） | **時刻表記を削除**。⇒ **測定を含む版を bank した commit の author time を権威**とし、**再現手順は本文の表**で示す |
| §12.4 γ | 「pZ が **〈時刻〉に** 格下げ済」と時刻つきで書いていた — ⛔ その時刻は **p18 の stamp 由来**で、**p18 自身が撤回済**（⛔ **値は再掲しない** = `-013` R1 の先例） | **時刻を削除**。⭐ **「格下げ済」という事実は維持**（p18 は技術内容を維持している） |

| §13 / §11.6-2（初版） | ⛔ **`:375` / `:392` と H-0 の field 一覧を、message から写して置いた** — **自分で読んでいなかった**。⇒ 私自身の規律「⛔ 他 pane の message の数値で裁定しない」に反する | **producing commit `746f049e8357aead0f28c48be1588c9ef2fee005` で全部読み直し**、`file:line` を **commit とセット**に書き換え、**接触対の不在は当該 file 全 1589 行の閉じた query で裏づけ**た |

| §16.3（初版） | ⛔ **「substring `pad` の geom は 12 個」を p18 の初報から写した** — 数が違ううえ、**自分で測ってもいなかった** | **測り直して訂正**: **geom 8 / body 4**（合計 12 は両者の和）。結論（部分一致では区別できない）は不変 |
| ⭐ **自分の query の欠陥（本項は私の発見）** | 最初に私が使った `grep -oP '<geom name="…"'` は **name が最初の属性であることを暗黙に仮定**しており、`<geom class="pad_box1" name="left_pad1"/>` の形を **4 個取りこぼした**（= 私の数が「4」になった原因） | ⇒ **`<tag\b[^>]*attr="…"` の形で書く。** ⚠ **属性の順序に依存する query は、静かに部分集合を返す** — 本 doc の「述語が見分けない」の系である |

⚠ **message ID 文字列に埋め込まれた時刻はそのまま**（custody chain 維持のため据え置き = p18 / pB と同じ扱い）。**ID は識別子であって時刻の主張ではない。**
⭐ **教訓（私にも当てはまる）:** **監査する側であることは、自分が同じ検査の対象外であることを意味しない。** 私は本 doc で「代理を読むな」を 4 度書きながら、**自分の時刻欄で測っていない値を書いていた。**

## 15. 目標が 1 つに絞られた — **軸の選定と順序の裁定**（p18 `MSG-P18-IMPLCHAIN-RS-DIRECTIVE-KO-CLAMP-FIRST-20260727-040`）

**Rs 指示（⚠ 種別 = p4 が報告した Rs 逐語。p18 は Rs 本人と未照合ゆえ、私も *p4 の申告* として扱う）:** 「**まず「コ」内にケーブルをクランプすることを実現しろ**」。
⇒ **単一の次目標 = コ字爪の内側でケーブルをクランプすること。** ⛔ それ以前に C1/C2 着座・工程表全体・動画完成を追わない。
⛔⛔ **本節は gate を 1 つも開かない。** 目標指示は権限付与ではない（「X を実現しろ」から「gate が開いた」を導くのは、本 doc が繰り返し記録している「**代理を読む**」と同型である）。**解錠は Rs の明示待ち。self-start しない。**

### 15.1 ⭐ 枠が変わった — 「説明」ではなく「実現」

4 本の軸は **旧 run の失敗を *説明* するための候補**だった。**新目標は説明を要求していない。** ⇒ ⭐ **§11.5 の裁定（構成でやり直す・帰属は必須ではない）は、この枠でさらに強くなる。** Rs が求めているのは **達成**であって診断ではない。

### 15.2 ⭐⭐ 順序の裁定（私の court）

| 順 | 何を | 誰の court | 状態 |
|---|---|---|---|
| **1** | ⭐ **基盤の確定**（UR15 をどの基盤で建てるか = §12.6） | **Rs**（私は推奨のみ提出済 = 生産基盤 Newton） | ⏸ **escalate 済・未回答**。⚠ **ここが決まらないと、下の C-0 を「どの基盤で導出するか」も決まらない** |
| **2** | ⭐ **C-0 = banked asset から *宣言差分* で model を導出**（§11.4 / §12.3） | **私（設計）→ p0（実装）→ pZ（検証）** | **β（除外行）は構成上消え・γ（駆動経路）は 1 経路に定まり・δ（剛性）は宣言値に固定される** ⇒ **3 軸が実験なしで片付く** |
| **3** | ⭐ **受入述語の確定**（位置 = 板の間にあるか ＋ 爪 geom との接触。**negative control 必須**） | **pZ**（⛔ 私は決めない） | p4 の材料 = 爪板は pinch 相対で `f2ext +25.8 mm` / `f1ext +38.2 mm`・板厚半 `1.2 mm` ⇒ **slot の空き 27.0–37.0 mm（10.0 mm）**。⚠ **私の §4 の内側 gap 10.00 mm と一致** |
| **4** | **到達（クランプ）を測る** | p0 実行 / pZ 検証 / **最終基準は Rs の動画** | ⛔ **解錠待ち。⚠ 解錠が出ても `scripts/check_thread_vault_prior_art.sh --fail-on-blocker` が先**（§運用4 / AGENTS.md） |

⇒ ⛔ **「4 軸を切り分ける実験」を先に置かない。** 目標が実現である以上、**構成でやり直して達成を測る**方が短く、かつ **3 軸は構成で消える**。**帰属が要るのは、構成し直した上でなお達成できないときだけ。**

### 15.3 α（径）の扱い — ⚠ **申告は採らないが、順位は動かせる**

**p4 申告（新情報）:** 既に **SSOT の Ø8 へ是正済**で、**最新 run でも `grasp` False**。⇒ **径単独では説明が付かない方向の材料**。
⛔ **私はこれを採用しない** — **artifact pin が未受領**であり、p18 も未検証だからである（⛔ 他 pane の message の数値で裁定しない）。**pin が出れば読む。**

⭐⭐ **さらに重要な限定（私の court として付す）:** **たとえ pin が出ても、「Ø8 でも `grasp` False」は α の格下げ根拠として *まだ* 使えない。** 理由 = **その `grasp` 述語こそが、本日「2 状態を見分けない」と判明したもの**である（パッド接触で真になり、コ内保持と区別できなかった）。⇒ **見分けない述語の False は、状態の不在を意味しない。**
⇒ **α の格下げは、§15.2-3 で述語が確定してから判断する。** ⛔ それまで α は **候補・未検証のまま**（§11.2 の地位を維持）。

### 15.3.1 ⭐⭐ pin が出たので、上の保留を解く — **α は格下げする**

**私が producing commit `c7ed338a82cf137e828c871c2a8437da7038927b` の blob から直読した**（⛔ message からの写しではない）:
- `ur15_steps.py:47` = `CABLE_N, CABLE_SEG, CABLE_R = 32, 0.030, 0.004  # task_config.py:137 CABLE_RADIUS = 0.004` ⇒ **SSOT の Ø8 へ是正済**。sha256 `b783f179ac97fac4b6066e39c32a0a0b704d506b89b5d76932bb60c2b7e982c3`。
- log（sha256 `65ca0d310f3eb141004675d62b820c7212c9498895be969a79fbf191a4f2c362`）逐語:
  - `GRASP L: fingers blocked by nothing` ／ `nearest cable link cab18 at 18.3 mm from the pinch, pad separation 24.0 mm, ctrl=255, pad geoms touching cable = none`
  - `GRASP R: fingers blocked by nothing` ／ `nearest cable link cab21 at 28.7 mm, pad separation 24.0 mm, ctrl=255, pad geoms touching cable = none`
  - `gates: {'grasp': False}`

⭐ **私が保留の条件にしていた「述語の確定」は、この run では満たされている** — ⭐ **しかも私が当初書いたより強い**（私が同 commit の script を直読して確認）: 診断行 `pad geoms touching cable` が数えている集合 **`PADG`** は `:214-215` 逐語で **接頭辞 `{t}g_` を持つ *全 gripper geom***であり、**爪板 4 個を包含する上位集合**である。⇒ ⛔ **旧稿の「爪 geom への接触で取られている」は狭すぎた** — 正しくは **その側の gripper geom すべてで接触ゼロ**。⇒ **名前一致の欠陥で弱まるどころか、より強い否定である。**
⚠ なお `grasped()`（`:340`）は `PADG` を substring `"ext"` でさらに絞っており、**この model ではたまたま爪板 4 個と一致する**が、**名前規約への依存であって構成上の保証ではない**（§16.3 の hard 要件は `grasped()` にも要る）。
⇒ ⭐ **α（径）を「候補・未検証」から「単独では説明にならない」へ格下げする。** ⛔ **「径は無関係」とは言わない**（クランプが成立し始めれば clearance 2.00 mm は再び効く量である）。
⚠ **本 run は NON-AUTHORIZED PROVISIONAL 群**（Rs の「動画を出せ」指示下の実施であって gate chain の認可ではない）。⇒ **私は本 run を設計値の根拠にせず、軸の順位付けにのみ使う。**

### 15.3.2 ⭐⭐ 目標が 1 つの量に落ちた

`ctrl=255`（全閉指令）に対し **パッド間隔は 24.0 mm で停止**し、しかも **`fingers blocked by nothing`**（閊えは報告されていない）。

⛔⛔ **ここで並置を 1 つ撤回する（原因側は私。p18 `-044` の訂正を受けたが、私の artifact に写したのは私である）:** 旧稿は直後に「爪 slot は 10.00 mm」と**並べて**いた。⛔ **両者は直交する別軸であり、大小を比べる意味がない**（**私の実測**: `right_pad_f1ext` と `f2ext` は **`pos` の x・y が同一（`0`, `-0.0026`）で z のみ `0.0382` / `0.0258` と違う** ⇒ **10.00 mm は同一 pad 上の *上下* の空き**。一方 `right_pad`（`:107`）と `left_pad`（`:154`）は**対向 pad** ⇒ **24.0 mm は顎の *開閉* 軸**）。⇒ **以後、この 2 つを併記しない。**
⭐ **これは私自身が §9 で書いた「別種の量どうしの比は、計算できても意味を運ばない」と同じ形**であり、**他 pane の枠付けを写したときに素通りさせた。**

⇒ ⭐⭐ **問いは並置なしで閉じる:** **全閉指令に対してパッドが 24.0 mm で止まり、しかも何にも閊えていないのはなぜか。** — これは **開閉軸だけで完結する問い**であり、10.00 mm を参照しない。⇒ **コ内クランプの直接の障害はここにあり、ケーブル側ではない。**
⇒ ⭐ **これは接触側でなく駆動・指令側の問題である**（何にも閊えずに止まっているため）。⇒ **§12.6 の基盤裁定の重みがさらに上がる** — **指の駆動機構が基盤で別だからである**（生産 Newton = **joint-target servo**〔POSITION・`66.7` / `2.0`・効力上限は `jnt_actfrcrange` 経由〕／素の MuJoCo = **MJCF actuator ＋ tendon**）。⇒ **「何を設計するか」が基盤で変わる。**

### 15.4 私が今すぐ出せるもの / 出せないもの

- ✅ **出せる:** 上の順序・C-0 の設計要求・α の限定・§13 の記録要求・§11.6 の model 側述語要求。**いずれも gate を要さない設計作業**である。
- ⛔ **出せない:** 基盤の確定（Rs）／受入述語の確定（pZ）／実行と検証（解錠待ち）／物理妥当性の判定（Rs 動画）。

## 16. 受入述語 CLAMP-1 v0.1 への設計軸からの応答（pZ 依頼・p18 `-043` 経由）

⛔ **確定は pZ の court。** 以下は **設計軸からの異議・支持**であり、私は述語を確定しない。

### 16.0 先に 2 つ、私の記録を接地し直す

- ⚠⚠ **語の分離（p18 `-042` A-3・私も採る）:** **「開口部」= コ字爪の赤板と青板の間**（asset 定義・中心間 12.40 mm / 開口 **10.00 mm**）。**「溝」= clip の溝。** ⛔ **別物であり、統合しない。** **pC は clip の溝について何も判定していない。**
- ⭐ **着座述語の欠陥の根拠を、pB の banked artifact に置き直す**（⛔ 私は読んだ）: `PB_UR15_KOGRASP_LOG_ANALYSIS_LOGANALYST_20260727.md` @ `e14afa80e690e497e2e9bc65f11bf71787befdec`（sha256 `235dfeb080294137648700480c8d0ad075337331fa10e59a0bc619794449b7da`・私の実測で一致）。核心 = **`pin=C1` は latch**（`d.eq_active` を 0 に戻す code が file 内に無い）⇒ **「eq を有効化した」以上の意味を持たず、着座の証拠にならない**。⭐ さらに pB は **「設計意図（爪の中で保持）と判定述語（`grasped()`）が一致していない」**と名指ししている。⇒ **§12.2 の要求（negative control）は、この artifact に接地する。**

### 16.1 ✅ 支持する点

1. **3 レグ（P 含有 ∧ C 爪板接触 ∧ R 保持）は banked 設計意図と一致**する（asset `:9-11` の「wrap the Ø8 cable top+bottom」）。
2. **negative control に N2（パッド面のみ接触・slot 外 = 旧述語を騙した状態）が入っている**のが要。⇒ **旧述語の失敗を再現できる control** であり、私が §12.2 で求めたものそのもの。
3. **評価 rig の要件（構成上あらかじめ slot 内に置いた rig で評価しない）** — p4 probe が捕捉を一度も試していなかった件への正しい対処。
4. **「CLAMP-1 が真で Rs 動画が偽なら述語が誤り（逆ではない）」** — 最終基準の向きが正しい。

### 16.2 ⚠ 設計軸からの異議 3 件（数で出す）

**異議 1 — P の z 範囲が「中心」の条件なら、N4 を通してしまう。**
slot の内側面は **pad-local z で 27.00 / 37.00 mm**（⛔ **旧稿の「pinch 相対」は私の座標系ラベルの誤り** — §17.2 の私自身の実測は **pad-local** であり、pinch 相対の値は別物である〔p4 材料では f2ext `+25.8` / f1ext `+38.2`〕。⚠ **数が近いので取り違えても気づきにくい** — 本 doc が繰り返している「**同じような数が別の面を指す**」の座標系版）。ケーブルは **Ø8（半径 4.0 mm）**。
⇒ **完全に slot 内に入る中心の範囲は `[27.0+4.0, 37.0−4.0] = [31.0, 33.0] mm`（幅 2.0 mm）** — ⭐ **これは §4 の clearance 2.00 mm と同じ量**である（**clearance ＝ 許容される中心帯の幅**）。
⇒ ⛔ **`[27.0, 37.0]` を中心の条件にすると、中心 27.5 mm（＝ ケーブルの 3.5 mm が下板の内側面より外）でも P が真**になる。**その状態は「下爪に載っている」＝ 負対照 N4 に極めて近い。** ⇒ **P と N4 が衝突する。**
⇒ **提案:** P を **完全含有 `[31.0, 33.0]`** にするか、**「部分含有」と明示して別レグ（例: 貫入していないこと）と組む**。⛔ どちらを採るかは pZ の court。

**異議 2 — N（連続 step 数）を step で固定しない。**
**step は基盤で意味が変わる**（physics dt が違う）。⇒ **秒で定義し、基盤の dt から step に落とす。** そうしないと基盤裁定（§12.6）で述語の厳しさが黙って変わる。

**異議 3 — 何本の腕で成立させるかが未定。**
**RS71 §0#1 は DUAL-ARM**（ケーブルは常に両腕で保持される）。⇒ **CLAMP-1 は「片腕で成立」か「両腕で成立」か**を明示しないと、**§0 不変前提に対して曖昧**になる。⛔ **私は §0 を解釈しない**（Rs 専権）。⇒ **pZ が明示し、必要なら Rs へ上げる**のが正しい。

### 16.3 ⭐ C レグへの hard 要件（私も同じ結論に独立到達している）

**geom 集合は id で厳密指定する。名前の部分一致で組まない。**
⭐ **数は私が自分で測り直した**（⛔ 旧稿の「geom 12 個」は p18 の初報を写したもので**誤り**・p18 も訂正済）: banked asset で **name に `pad` を含む geom は 8 個**（爪板 4 = `*_pad_f1ext` / `*_pad_f2ext` ＋ **collision 側の pad box 4** = `*_pad1` / `*_pad2`・いずれも `class="pad_box1"` / `"pad_box2"`）、**body は 4 個**（`*_pad` / `*_silicone_pad`）。⇒ **合計 12 は「geom 8 ＋ body 4」であって geom 数ではない。**
⇒ ⛔ **それでも結論は変わらない: 部分一致 `pad` は 8 個中 4 個の非爪板（pad box）を巻き込み、爪接触とパッド面接触を原理的に区別できない。**
⚠ **`*_silicone_pad` は body で、その geom は `class="visual"`（`:53-54` 逐語 `contype="0" conaffinity="0"`）⇒ 接触に現れない。** ⇒ **実際に接触し得るのは pad box 4 ＋ 爪板 4。**
⇒ ⭐ **これは pB が log 側から出した所見（`grasped()` が接頭辞で全 geom を拾う）の *機構側の説明* である。** ⇒ **§11.6 の「述語を model 側に置く」と同じ形**であり、**私は hard 要件として支持する。**

### 16.3.1 ⭐ レグ V（駆動が結線されているか）を支持する — ただし **今は片方向にしか判定できない**

**pZ の v0.1a レグ V** = 評価対象 build で **指の駆動が実際に結線されている**こと（生産 Newton なら `grasp_actuation=True` 側・driver servo actuator 4 本）。V 不成立なら CLAMP-1 は **False ではなく UNEVALUABLE** を返す。
✅ **強く支持する。** ⭐ 理由は 2 つあり、**どちらも本 doc が既に記録している形**である:
1. **§運用15 の ABSENT-IN-CODE（wire-then-validate）**そのものである — **結線されていない機構は、appearance だけあって working ではない**。
2. ⭐⭐ **負対照も flag-ON build で走らせないと空振りする** — flag-OFF では **N1〜N4 がすべて False** になり、**違う結果の出得ない検査**になる。⇒ **V は注記ではなく受入要件の一部。**（私の §12.3 の fence と同根: **測ったのは flag-OFF build の性質であって production 一般ではない**。）

⛔⛔ **ただし、私の court として限定を付ける — V の評価可能性は現状 *非対称* である**（出所 = p0 実測・**私も閉じた query で確認した**）:
- ✅ **V 不成立の検出は可能**（`nu` ＋ `actuator_trnid` で実証済）。
- ⛔ **V 成立の確認は不可** — **`actuator_gainprm` が記録されていない**。⭐ **私の実測**: `746f049e8357aead0f28c48be1588c9ef2fee005` の当該 file 全 1589 行で `gainprm` に一致するのは **`:1156` と `:1170` の 2 箇所だけで、いずれも説明文**である。記録される actuator 系 field は **`actuator_ctrlrange` / `actuator_forcerange` / `actuator_trnid` / `jnt_actfrcrange` / `nu` のみ**。
⇒ ⭐⭐ **片方向にしか判定できない述語は、受入基準として成立しない。** 現状の V は **「不成立を検出できるが、成立を確認できない」** ため、**CLAMP-1 はその軸で永久に UNEVALUABLE か False にしかならない。** ⇒ **これは「違う結果の出得ない検査」の鏡像**である。
⇒ **設計要求（追加）: V を受入要件にするなら、`actuator_gainprm` 相当の *成立側の正の信号* を記録項目に加えること。** ⛔ 実装は authorization 待ち（p0 繰越）。⚠ **`jnt_actfrcrange` は flag-OFF 側の証拠にはなるが、flag-ON が未測定ゆえ成立確認に使えるかは未確認。**
⚠⚠ ⇒ **基盤を生産 Newton に採る場合、「flag-ON build を誰も一度も測っていない」ことが前提の穴として残る**（§12.6 の裁定材料に加える）。

### 16.4 ⚠ 実装可能性（pZ が自ら挙げた未充足の前提）

**C レグ = 接触対が現行 harness に未記録**（§11.6）／**R レグ = RUN 認可が要る**／**P レグ = pad local への変換が既存出力に在るか未確認**。
⇒ ⛔ **v0.1 は定義であって、現行 harness では評価できない。** ⇒ **§13 の記録要求（count は何を数えたかと一緒に）と §11.6-3（接触フィルタ状態の記録）が、そのまま本述語の前提になる。**
⚠ **pZ は基盤裁定後に v0.2 で数値を固定するとしている** ⇒ **§12.6 の基盤裁定が、本述語の実装可能性も左右する。** ⇒ **私の順序（§15.2）は変えない。**

## 17. 閉じを止めている面 と **コ の実寸** — 私の court の裁定（p18 `-049`）

### 17.1 受領した測定（⚠ 出所 = p4 実測。p18 は再測せず・私も再測できない = RUN CLOSED）

`mujoco.mj_geomDistance`（負値 = 重なり・mm）で 3 指令:

| 指令 | パッド面 対向 | 爪 f1 対向 | 爪 f2 対向 | 同 pad の爪の上下 |
|---|---|---|---|---|
| OPEN | +85.19 | +75.20 | +75.19 | +10.00 |
| HALF | +28.35 | +18.27 | +18.80 | +10.00 |
| **CLAMP** | **+9.98** | **−0.07** | +0.26 | +10.00 |

⇒ ⭐ **全閉で先に当たるのは爪板どうしであり、パッド面は +9.98 mm 空いたまま。** ⇒ **閉を止めている面はパッドではなく爪板。** ⛔ **因果は誰も主張していない**（私も主張しない）。

### 17.2 ⭐⭐ 私が asset から自分で導いた寸法 — **コ は「深さ 5.00 mm の溝」である**

**私の実測**（`2f85_koshape.xml`・pad-local・half-size を展開）:

| geom | 定義 | y 範囲 | z 範囲 |
|---|---|---|---|
| `*_pad1`（背板・`class="pad_box1"` `:58-59`） | `pos 0 -0.0026 0.028125` / `size 0.011 0.004 0.009375` | **−6.60 … +1.40** | **18.75 … 37.50** |
| `*_pad2`（`class="pad_box2"` `:62-63`） | `pos 0 -0.0026 0.009375` / 同 size | −6.60 … +1.40 | 0 … 18.75 |
| `*_pad_f1ext`（下爪） | `pos 0 -0.0026 0.0382` / `size 0.011 0.009 0.0012` | **−11.60 … +6.40** | 37.00 … 39.40 |
| `*_pad_f2ext`（上爪） | `pos 0 -0.0026 0.0258` / 同 size | −11.60 … +6.40 | 24.60 … 27.00 |

⇒ **コ の構造が確定する: 背板 = `pad1` ／ 腕 = `f1ext` と `f2ext`。**（**`pad1` の z 範囲 18.75–37.50 は slot 帯 27.00–37.00 を完全に覆う** ⇒ 背板は slot の奥にある。）
⇒ ⭐⭐ **溝の深さ（y 方向）= 背板前面 `+1.40` から爪先 `+6.40` までの 5.00 mm。**
⇒ ⛔⛔ **Ø8.00 mm のケーブルは、この溝に *完全には入らない*。5.00 mm < 8.00 mm ゆえ、どの位置でも必ず爪先より外へはみ出す。**

**⇒ 設計上の帰結（私の court）:**
1. ⭐ **「コ の中に入っている」を *完全含有* で定義できない。** ⇒ **P レグの y は含有ではなく *噛み込み深さ*（ケーブル表面が爪先平面よりどれだけ奥にあるか）で定義する。** 最大でも **5.00 mm**（背板に触れた状態）。
2. ⭐ **§16.2 異議 1（z の中心帯 `[31.00, 33.00]`）は維持**する — **z 方向は完全含有が可能**（slot 10.00 mm ＞ Ø8.00 mm）だからである。⇒ **z は含有・y は噛み込み深さ**、と**軸ごとに別の述語**を使う。⛔ **1 つの箱で書かない。**
3. ⚠ **保持の向きが分かれる:** **z（上下）は爪板 2 枚で挟む**／**y（奥行き）は挟めない** ⇒ **y 方向の保持は対向 pad との間でしか成立しない。**

### 17.3 ⭐⭐ 中間指令が一度も出されていない — **値の決定は私の court**

**A-4（p4 発）:** Ø8 を対向する爪の間に保持するには **対向爪の隙間が 8 mm 以上で止まる**必要がある。実測は **HALF で 18.27 mm / CLAMP で −0.07 mm** ⇒ **必要な閉じ量は両者の間にあり、その中間指令は一度も出されていない**（**OPEN / HALF / CLAMP の 3 値のみ**）。

**⇒ 私の裁定:**
1. ⛔ **3 点から内挿して指令値を決めない。** 駆動は **4 節リンク**であり、**指令と隙間の関係は非線形**である。**HALF と CLAMP の間は未測定**であり、**「中間だからおよそ半分」は測っていない量への外挿**である。
2. ⭐⭐ **目標は *指令値* ではなく *幾何量* で書く。** ⇒ **「対向爪の隙間が Ø8.00 mm ＋ 意図した締め代 になる状態」**を設計目標とし、**それを達成する指令は測って求める**（指令 ↔ 隙間の掃引）。⭐ **理由:** 指令 → 隙間の写像は **基盤と駆動経路で変わる**（§15.3.2 の γ そのもの）。**幾何で書けば基盤が変わっても目標は動かない。**
3. ⇒ **要求する測定（解錠後）= 指令を OPEN から CLAMP まで刻んだ 1 次元掃引で、各点の「対向爪の隙間」を記録する。** ⛔ 3 点では足りない。⚠ **`mj_geomDistance` は面どうしの距離を返すので、この目的に適合する計器である**（body 原点間距離を使わない = p4 が撤回した誤りを繰り返さない）。
4. ⚠⚠ **未解決として明記する（私は解かない）:** **banked 設計は全閉（`GRIPPER_CLOSE_QPOS`）で爪どうしが重なり得ることを前提に `exclude` 行を置いている**（`:173-175` 逐語）。一方 **Ø8 を対向爪の間に保持するには全閉では閉じ過ぎ**である。⇒ **「全閉で保持する設計」と「Ø8 を挟む設計」の関係は、私が手元の数から導けない。** ⛔ **gripper 幾何は §0#4 で LOCK され Rs 専権**ゆえ、**私はここを解かず、疑問として上げる。**

### 17.4 ⭐ C レグの訂正（pZ v0.1c）を支持する — ただし **識別の本体は P**

**支持:** C を **同一 pad の コ 構成 geom `{pad1, pad_f1ext, pad_f2ext}`** にする（⛔ `pad2` は z 0–18.75 で slot 帯と重ならないので除外・⛔ 反対側 pad を混ぜない）。⇒ **私の 17.2 の実測と整合する** — **正しくコ内に在るケーブルが背板だけに触れる状態は普通に起こり得る**（clearance 2.00 mm）ので、**爪板のみの C は偽陰性を生む**。
⭐⭐ **役割の訂正も受け入れる:** 旧述語の欠陥（パッド接触で真）を排除しているのは **C ではなく P** である。⇒ **geom id の厳密指定は *偽陽性* 対策として hard 要件のまま／識別の本体は *P（含有と噛み込み）***。⇒ ⚠ **両方直さないと、厳密化しても背板除外による偽陰性が残る。**

### 17.5 レグ V の pZ 裁定を登録 ＋ ⭐ **V を 2 段に分ける提案**

⭐⭐ **p0 の field ごとの精密化（p18 `-050` 経由・混同禁止と明記されている）を受けて、私から 1 つ提案する:**

| field | 現状 | **二方向にするコスト** |
|---|---|---|
| `nu` ＋ `actuator_trnid` | **flag-OFF は banked 済 / flag-ON 未測定** | ⭐ **flag-ON を 1 回測れば負対照が揃う** |
| `actuator_gainprm` | ⛔ **両側とも未測定**（field 自体が未記録ゆえ陰性側の値すら無い） | **両側とも新規測定が要る** |
| `jnt_actfrcrange` | flag-OFF のみ banked（陽性側未観測） | pZ の不採用と整合 |

⇒ ⭐ **提案: V を 2 段に分ける。**
- **V-弱（結線の有無）= 「gripper 関節に対応する actuator が存在するか」** — **`nu` ＋ `actuator_trnid` で足り、既存の記録項目のまま**である。**足りないのは記録項目ではなく、flag-ON build を誰も測っていないこと。**
- **V-強（駆動の同定）= 「それが KE 一致の position servo 4 本か」** — **`actuator_gainprm` が要る**（記録項目の追加）。
⇒ ⭐ **今の目標（コ内クランプ）が要求しているのは「指が駆動されるか」であって「どの gain か」ではない** ⇒ **V-弱で判定を進め、V-強は gain を設計値として扱う段で要求する。** ⛔ そうしないと、**答えられる問いが、答えを要しない field の未記録で止まる。**
⚠ **どちらを採るかは pZ の court**（私は述語を確定しない）。⛔ **いずれにせよ flag-ON build の測定は要る**（§16.3.1 の「前提の穴」は解消されない）。

### 17.5.1 pZ 裁定の登録

**V 不在の検出 = 採用**（`nu` ＋ `actuator_trnid`・新規記録不要）／**V 成立の確認 = 現時点不可** ⇒ **不在でも不確認でも UNEVALUABLE**。
⛔ **帰結を隠さない: `actuator_gainprm` が記録されるまで、CLAMP-1 は肯定判定を一度も返せない。** ⭐ **これは欠陥ではなく設計上の意図**（§16.3.1 で私が「片方向述語は受入基準として成立しない」と書いた点の、pZ による正しい処理）。
⭐ **V レグ自体にも負対照を課す**（flag-ON / flag-OFF の両状態で値が分かれることを示してから採用）= **妥当性検査それ自体への再帰適用**。私は支持する。

## 18. ⭐⭐⭐ 保持機構の裁定（私の court）— **合成で、全閉が設計上のクランプ状態である**

### 18.1 逐語（私が自分で読んだ）

- **設計 doc** `thread-vault/06-Knowledge/GD-KoShape-Finger.md:11-13`: 「make the gripper finger a コ (⊏) so **the left/right pads' claws wrap the cable on all sides incl. the bottom**（intended to close the ◇'s open bottom = the verified lift-fail root）」
- **asset** `2f85_koshape.xml:9` / `:111`: 「Per pad, two protruding box claws **wrap the Ø8 cable**: f1ext (bottom) + f2ext (top), **gap ~10 mm**」／「**wrap the Ø8 cable top+bottom**」
- **私の実測（向き）:** `left_spring_link`（`:142`）は **`quat="0 0 0 1"`（z 回り 180°）** ⇒ **左側の連鎖は鏡像**であり、**両 pad は互いに向き合う**。⇒ **各 pad の溝（爪先 `+6.40` 側）は相手 pad の方を向いて開いている。**

### 18.2 ⭐⭐ 裁定 = **排他ではなく合成。しかも幾何が閉じる。**

**私の実測を組むと、設計文の 2 つの記述は矛盾せず、1 つの機構に収束する:**

| 面 | 何が壁になるか | 私の実測 |
|---|---|---|
| **左右（閉じ方向）** | **2 枚の背板 `pad1`** | 背板は z 18.75–37.50 を占め、**slot 帯 27.00–37.00 を覆う**。**全閉でのパッド面 対向は +9.98 mm**（p4 実測）⇒ **Ø8.00 ＋ 約 2 mm = §4 の clearance と同じ** |
| **上下** | **4 枚の爪**（各 pad の f1ext / f2ext） | **同 pad の爪の上下は OPEN / HALF / CLAMP のどれでも +10.00 mm で不変**（p4 実測・pZ 追認）⇒ **顎の開閉に依存しない固定の壁** |
| **奥行き（各 pad の溝方向）** | ⛔ **壁にならない** | **溝の深さ 5.00 mm < Ø8.00 mm**（§17.2・私の実測）⇒ **1 枚の pad だけでは奥行き方向を保持できない**。溝は**相手 pad に向いて開いている**（18.1） |

⇒ ⭐⭐⭐ **機構 = ケーブルは「1 枚の pad の溝の中」ではなく、「2 枚の背板の間」に居る。** 上下は 4 枚の爪、左右は 2 枚の背板。⇒ **「all sides」は左右（背板）＋上下（爪）の *合成* で成立する。** ⇒ **設計 doc と asset は同じ機構を別の面から書いている。**

### 18.3 ⭐⭐⭐ 帰結 1 — **全閉が設計上のクランプ状態であり、中間指令は要らない**

**全閉でのパッド面 対向 = +9.98 mm** は **Ø8.00 に対して clearance 約 2 mm** であり、**asset が `gap ~10 mm` と書いた設計値と一致する**。⇒ **全閉は「閉じ過ぎ」ではなく、*狙った寸法* である。**
⇒ ⛔ **§17.3 の「中間指令の値を決める」は撤回する。** **決めるべき中間値は無い** — **設計は全閉で Ø8 を保持するように寸法されている。**
⇒ ⭐ **同時に、爪どうしが全閉で当たる（−0.07 mm）ことも設計どおり**である。各 pad の爪は背板から約 5 mm 突き出しており、**9.98 mm の空間で両側から 5 ＋ 5 mm ⇒ 爪先どうしが出会う**。⭐ **これがまさに banked の `exclude` 行が存在する理由**である（`:173-175` 逐語「the protruding コ claws f1ext/f2ext **can overlap at `GRIPPER_CLOSE_QPOS`**」）。

### 18.4 ⛔⛔ 帰結 2 — **私の §15.3.2 を撤回する**

私は §15.3.2 で「**全閉指令に対しパッドが 24.0 mm で止まり、何にも閊えていないのはなぜか**」を **コ内クランプの直接の障害**と書いた。⇒ ⛔ **撤回する。**
**理由:** その **24.0 mm は body 原点間距離**であって面の隙間ではない（**p4 が撤回済**）。**同じ全閉指令での *面* の隙間は +9.98 mm**（`mj_geomDistance` 実測）⇒ ⭐ **顎は設計どおりの寸法まで閉じている。**
⇒ ⭐ **障害は「閉じないこと」ではない。** **pC のレグ（18 時刻・両アーム）でケーブルは終始 *爪の外* にあり、log でも最寄りのケーブルリンクは pinch から 18.3 / 28.7 mm 離れている。** ⇒ ⭐⭐ **これは *位置決め* の問題であって、閉じの問題ではない。**
⚠ **私はこの測定を再測できない**（`mj_geomDistance` は RUN と mesh を要し、いずれも CLOSED）⇒ **出所 = p4 実測**として扱い、**因果は主張しない。**

### 18.5 ⭐ 帰結 3 — **軸 β（除外行）の位置づけが上がる。ただし「設計の読み」であって測定ではない**

18.3 のとおり **全閉では爪どうしが必ず出会う** ⇒ **`exclude` 行が無ければ爪が互いに衝突する** ⇒ **設計が意図した全閉状態に到達できない可能性がある**。⇒ **β は「候補」から「設計の読みが指す先」へ上がる。**
⛔ **これは *設計整合の議論* であって因果の測定ではない。** ⛔ **私は因果を主張しない。** ⇒ **確かめ方は §11.5 の C-0（banked から宣言差分で導出し、`exclude` 集合を継承する）で、実験を増やさずに済む。**

### 18.6 ⚠⚠ 実装要件を 1 つ追加 — **名前依存を切ると別の仕組みが壊れ得る**

**asset `:112-113` 逐語（私が読んだ）:** 「**Names contain "pad" so the suite-wide contact filter (`test_newton_clip_routing.py`) keeps COLLIDE + cable contact.**」
⇒ ⭐ **geom 名に `pad` が入っているのは意図的**であり、**suite 全体の contact filter が名前で拾うことを前提にした設計**である。
⇒ ⚠ **したがって §16.3 の hard 要件（geom id の厳密指定）は、この filter と干渉し得る。** ⛔ **私は影響範囲を測っていない**（当該 filter の実装は未確認）。
⇒ ⭐ **要件（実装時）: 述語側を geom id 厳密指定にする場合、suite-wide filter 側の挙動が変わらないことを併せて確認する。** ⛔ **名前を変えない**（名前は他の仕組みの入力である）。⇒ **「述語の選択を id にする」ことと「名前を捨てる」ことは別である。**

### 18.6.1 ⭐ 干渉の懸念は解消した（条件つき）

**p0 実測（p18 が両箇所を直読して確認）:** 名前依存の filter 2 箇所 — `newton_skill_env_base.py:1578-1583` の `proto.shape_flags` ／ `test_newton_clip_routing.py:1436-1440` の `builder.add_shape_collision_filter_pair` — は **いずれも builder へ書く側（finalize 前）** ＝ **どの shape が接触し *得る* か**を決める面。一方 **C レグは build 済 model から「どの接触が *起きた* か」を geom id で読む面**。⇒ ⭐ **面が別なので、述語だけを id 化しても filter の挙動は変わらない。**
⛔ **条件つきである:** 独立なのは **述語だけを変える場合**に限る。**asset の geom 名から `pad` を外す**／**filter を id 方式へ書き換える**なら **両箇所が同時に効かなくなる**（asset `:112-113` の警告の経路）。⇒ ⭐ **§18.6 の要件は「名前を変えない」に絞られる。**
⚠ **p0 は 2 箇所を読んだだけで、suite 全体に他の名前依存 filter が無いことは閉じた探索をしていない** ⇒ ⛔ **「無い」とは主張しない。**

### 18.6.2 ⭐⭐ 上下 slot は閉じ量に依存しない — **§18.4 を独立に補強する**

**p4 実測（pZ 追認・p18 pin 照合済）:** 同一 pad の爪の上下は **OPEN / HALF / CLAMP のすべてで +10.00 mm** ⇒ **顎の開閉に依存しない。**
⇒ ⭐⭐ **上下で包む保持は「顎を閉じること」では成立せず、「slot をケーブルの位置へ持っていくこと」で成立する。** ⇒ **問題は grip の閉じ量ではなく *腕の位置決め* の側にある。** ⇒ **§18.4（位置決めの問題である）を、私とは独立の測定が同じ結論で支える。**
⚠ **Rs 逐語（出所 = p4 relay・⛔ p18 は Rs 本人と未照合）**「単にコがケーブル位置にいっていないだけだ。物理的にクランプ可能」も**同じ方向を指す**。⛔ **ただし未 pin ゆえ、私は本裁定の *根拠にしない*。**（本日、未 pin の観察が判定として流れた事例が既に 2 件ある。）

### 18.6.3 ⛔ 制御目標として **「対向爪の隙間 8 mm」を採らない**

p4 の A-4「Ø8 保持には対向爪の隙間 8 mm 以上」は **左右を *爪で* 挟む機構を前提にした値**である（p4 自身が前提付きと明言）。
⇒ ⛔ **私の §18.2 の裁定はこれを採らない** — **左右の壁は *背板* であり、全閉での背板間は 9.98 mm ＝ Ø8 ＋ clearance だからである。** もし爪が 8 mm で止まる設計なら、**背板間は約 18 mm 空いたままになり、asset の `gap ~10 mm` と矛盾する。**
⚠ ⭐ **加えて、狙いを *世界座標の固定オフセット* で書かない** — p4 の自己訂正のとおり「ピンチ点の上 32.0 mm」は **向きも大きさも誤り**であり（実測では爪間中央は **ピンチ点より 10.1〜11.8 mm 下**、しかも 4 節リンクで pad が傾くため **世界オフセットは姿勢と開閉量で変わる**）、**正しくは pad-local z ≈ 32.0 mm**（完全含有帯 31.0–33.0）。⇒ ⭐ **P レグが pad-local で定義されていることの妥当性が独立に裏づけられた**と同時に、**`pad` body の `xpos` / `xmat` の記録（p0 繰越）が P レグの前提**であることも確定する。

### 18.7 順序（pZ の推奨を支持・私の裁定として確定）

**保持機構の確定（本節）→ 述語の確定（pZ）→ 到達を測る。** ⇒ **中間値の決定は 18.3 により不要になった**ので、pZ が懸念した「誤った保持モデルに基づく制御目標」は**そもそも作らない**。
⚠ **D-3（片腕か両腕か）は別問題として残る** — **本節が確定したのは「1 つの gripper の中の 2 枚の pad」であって、「2 本の腕」ではない。** ⛔ **混同しない。** §0#1 の DUAL-ARM 解釈は **Rs 専権**（escalate 済）。

## 19. ⭐⭐ 参照点の裁定 — **H-4 の 3 点はどれも「狙う点」ではない**（p18 `-056`・私の中心 court）

### 19.1 私が harness で自分で読んだ定義（`746f049e8357aead0f28c48be1588c9ef2fee005`）

| 点 | 定義（逐語） | 行 | 何で作られているか |
|---|---|---|---|
| **J-a** | `ee_pos + 0.220 * z_ee` —「the point the SKILL threshold actually measures」（`EE_TO_FINGERTIP = 0.220`） | `:911` `:913` | **EE 姿勢 ＋ 固定スカラー** |
| **J-b** | `pad_midpoint_world` = `0.5 * (xpos[pads[0]] + xpos[pads[1]])` | `:965`（`pad_offs = (9, 13)` は `:928`） | **2 つの pad body の *位置* の中点**（姿勢を含まない） |
| **J-c** | `ee_pos + 0.2757 * z_ee` —「the measured KO claw tip」 | `:917` | **EE 姿勢 ＋ 固定スカラー** |

⭐ **`z_ee` は `mj_data.xmat[ee_body]` の第 3 列**（`:953`）＝ **EE body の姿勢**である。
⛔ **pad の姿勢は、この file のどこにも記録されていない** — `xmat` / `xquat` の一致は `:953` の **EE body の 1 箇所だけ**であり、pad の姿勢・回転を記録する項目は（書式を仮定しない検索で・打ち切りなしで）**1 件も無い**。⚠ **この結論は「一覧が空だったこと」に依るのであって、私がその後に表示した rc に依らない**（**pipeline 末尾の rc は当該 grep の rc ではない** — 本 doc §14 で私が記録した罠であり、**同じ turn で自分がまた踏みかけた**）。

### 19.2 裁定

1. ⭐⭐ **第 4 の参照点が要る = slot 中心。** §18 の機構裁定により、**ケーブルが在るべき場所は「2 枚の背板の間・上下の爪の間」**であり、その中心は **pad-local z ≈ 32.0 mm**（完全含有帯 31.0–33.0・§16.2）である。⇒ **H-4 の 3 点はいずれもこの点ではない。**
2. ⭐ **J-b が最も近いが、それではない。** J-b は **2 つの pad body 原点の中点**ゆえ **閉じ方向（左右）では正しい位置**にあるが、**高さは pad 原点であって slot 中心ではない**し、**姿勢を持たない**。⇒ **第 4 点 = J-b を pad-local で slot 中心へずらした点**、と構成的に書ける。
3. ⛔ **J-a / J-c は位置決めの物差しにならない。** 両者は **EE の z 軸に沿う固定スカラー**であり、**4 節リンクが pad を EE に対して傾ける**（p4 実測）ため、**world でのオフセットが slot を追わない**。
   ⚠ ⭐ **過剰に外さない — 射程を切るだけである:** 両者は **それぞれの目的（J-a =「SKILL 閾値が実際に測る点」／ J-c =「実測した KO 爪先」）では有効**であり、**EE frame の構成物としては生きている**。⛔ **私が否定するのは「pad-local の目標を world の固定オフセットで狙えるか」だけ**である。⛔ **閾値そのもの（`EE_TO_FINGERTIP = 0.220` を含む）は p5 と Rs の court ゆえ触らない。**
4. ⭐⭐ **前提が 1 項目に集まった。** 第 4 点を **world で出す**には **pad の姿勢（`xmat`）** が要る（**位置だけでは pad-local → world の変換ができない**）。⇒ **p0 の繰越「pad body の `xpos` / `xmat`」は、pZ の P レグの前提であると同時に、位置決め側の参照点の前提でもある。** ⇒ ⭐ **2 用途が同じ 1 項目に集まる ⇒ 解錠時の実装優先度は高い。**
5. ⇒ **機構の裁定が決めるものは 4 つになった**（p18 の整理を採る）: ①C レグの左右性 ②中間値か位置決めか（**§18.3 / §18.4 で後者に確定**）③H-4 に第 4 参照点が要るか（**本節で「要る」に確定**）④EE 基準固定オフセットが物差しとして生きるか（**本節で「位置決めには使えない・本来の目的では有効」に確定**）。

## 20. Rs の機構裁定を受けた訂正 ＋ ⭐⭐ **数で表せる齟齬を 1 件 Rs へ上げる**

**Rs 裁定（逐語・⚠ 出所 = p4 relay。p18 は Rs 本人と未照合。⭐ ただし p18 の確認要請への回答として得られたもの）:**
> 「爪の上下の隙間は」問題ない、左右で摩擦が生じればケーブルをコ内に固定できる

⇒ **保持の本体は「左右で摩擦」。上下 slot は含有を与えるが保持の本体ではない。** ⭐ **私が §18 で幾何から独立に到達した「ケーブルは 2 枚の背板の間に居る」と同じ向き**であり、**Rs 裁定がそれを機構として確定した。**
⭐ **p4 の符号訂正も採る:** 旧「対向面の隙間は **8 mm 以上**で止まる必要」⇒ ⛔ **逆。摩擦を立てるには対向面がケーブルに当たり、8 mm より *狭く* なって圧縮する必要がある**（8 mm ちょうどでは接触するだけで力が立たない）。

### 20.1 ⛔ 私の訂正 3 件（すべて cause-side は私）

| 箇所 | 誤り | 訂正 |
|---|---|---|
| **§18.2 の表** | 左右の壁を **背板 `pad1`** と書いた | ⚠ **「壁」ではなく「摩擦面」であるべき**（Rs 裁定）。**かつ、ケーブルの高さ（pad-local z 31–33）に在る対向面は背板だけ**である（爪は z 24.6–27.0 と 37.0–39.4 で**ケーブルの上下に外れる**）⇒ **左右で当たり得るのは背板のみ**、が正しい |
| **§18.3** | 全閉の背板間 **+9.98 mm** を **asset の `gap ~10 mm` と一致**と書き、**「全閉は狙った寸法」**と結論した | ⛔ **引用が別軸だった** — asset の `gap ~10 mm` は **f1ext と f2ext の z 方向の隙間**であって**顎軸ではない**（p18 再読・私も §17.2 で z 側として測っている）。**数が近いのは偶然。** ⇒ ⛔ **「全閉が設計上のクランプ寸法である」という *推論* を撤回する**（**測定値 9.98 mm 自体は有効**） |
| **§18.5** | 「全閉では爪どうしが必ず出会う ⇒ 落ちた `exclude` が到達を妨げ得る」として **β の位置づけを上げた** | ⛔ **前提が崩れた** — **−0.07 mm は *ケーブルが無い状態* の測定**である（p4）。**ケーブルが正しい位置に在れば爪は届かず、ケーブルを挟んで止まる** ⇒ **爪どうしの噛みは「ケーブルがそこに無いこと」の *症状* であって失敗の原因ではない。** ⇒ **β の位置づけを元に戻す**（空振り時の保険としての要否は別問題） |

### 20.2 ⭐⭐ Rs へ上げる齟齬 — **全閉でも、ケーブルの高さでは 1.98 mm 空く**

**私が測った値だけで書く:**
- ケーブルが居るべき高さ = **pad-local z 31.00–33.00**（完全含有帯・中心 32.00）
- **その高さに在る対向面は背板 `pad1` だけ**（`pad1` の z は 18.75–37.50 で 31–33 を覆う／爪 `f2ext` 24.60–27.00・`f1ext` 37.00–39.40 は**この帯に無い**）
- **全閉での背板 対向 = +9.98 mm**（p4 実測・`mj_geomDistance`）
- ケーブル = **Ø8.00 mm**

⇒ ⭐⭐ **全閉でも、ケーブルの高さでの隙間は 9.98 − 8.00 = 1.98 mm 空いたままである。** ⇒ **接触が起きず、したがって法線力も摩擦も立たない。**
⇒ ⛔⛔ **Rs の裁定（左右で摩擦を生じさせて固定する）は、banked の寸法のままでは *その高さで* 成立しない。** 摩擦を立てるには **対向面が Ø8 より狭くなる**必要がある（p4 の符号訂正）が、**全閉がすでに機構の端**である。

⚠ **私が *言っていない* こと（過剰に読まないための限定）:**
- ⛔ **「Rs の裁定が誤り」とは言わない。** 機構の裁定は Rs 専権であり、私は**寸法との齟齬を報告するだけ**である。
- ⛔ **「クランプは不可能」とも言わない。** 私が測っていないものが少なくとも 3 つある: ①**ケーブルの径方向のたわみ**（接触の `solref` / `solimp` 次第で貫入し得る）②**ケーブルが z 帯の *端* に寄った場合**（例えば z 31.0 で下爪に接する位置なら、爪も対向面になり得る）③**pad の傾き**（4 節リンクで背板が平行でなくなれば、隙間は場所により変わる）。
- ⇒ ⭐ **したがってこれは「不能の証明」ではなく、「寸法と機構裁定の突き合わせで出た 1.98 mm の穴」の報告である。**

### 20.3 ⇒ 私の court として出す選択肢（⛔ 選ぶのは Rs）

1. **A) 寸法を変えずに済む読みがある** — 上の限定 ①〜③ のいずれかで 1.98 mm が埋まる。⇒ **確かめるには測定が要る**（`solimp`/`solref` 由来の貫入量・z 帯端での爪接触・pad の傾き）。⛔ **RUN 認可が要る。**
2. **B) 保持を上下（含有）側に置く** — Rs 裁定は「上下は問題ない」であって「上下は保持しない」ではない。⇒ **上下 10.00 mm 対 Ø8.00 の 2 mm 遊びで *落ちない* ことを保持とみなす**読み。⛔ **摩擦は立たないので「固定」ではない。**
3. **C) 寸法を変える** — 背板間が Ø8 より狭くなるようにする。⛔⛔ **gripper 幾何は §0#4 で human-LOCKED ＝ Rs 専権**ゆえ、**私は提案の形すら出さない**（変更の可否そのものが Rs の判断）。
⇒ ⭐ **私の推奨 = まず A を測る。** **寸法変更（C）を検討する前に、既存寸法で摩擦が立つ余地があるかを測るのが順序として安い。** ⛔ **測定は解錠待ち。**

### 20.4 ⭐ Rs の追加制約と、その **射程の確定**（E の「解釈の確定は p11 の court」への回答）

**Rs 逐語（⚠ 出所 = p4 relay・p18 は Rs 本人と未照合）:**
> 逆に上下をきつくしすぎるとケーブルをクランプしずらくなる

⭐ **幾何として厳密に成立する**（私も算術で確認）: 爪の間 **W** に対し **完全含有帯の幅 = W − 8.00 mm** ⇒ **W を詰めると帯は 1 対 1 で縮む**（W = 9.0 で 1.0 mm・**W = 8.0 で 0**）。⇒ **上下を詰めるほど位置決めが難しくなる。**

⇒ ⭐⭐ **これは §16.2 / §20.2 の完全含有帯 `[31.00, 33.00]`（幅 2.00 mm）に *設計上の意味* を与える** — **あの帯は「厳しすぎる条件」ではなく、この設計が与えた *位置決め許容* そのもの**である。⇒ ⛔ **述語側でも幾何側でも縮めてはならない量。**

⭐⭐ **射程の確定（私の court として答える）:**
- ✅ **本制約が閉じたのは「上下（z）の slot を詰める」方向**である。⇒ ⛔ **非把持の是正として slot を詰めてケーブルに合わせる案は採らない。**
- ⚠⚠ **本制約は §20.2 の穴（左右＝顎軸で 1.98 mm）については何も言っていない。** **上下 z と 顎軸は直交する別軸**であり（§15.3.2 で私が一度並置して撤回した、まさにその 2 軸）、**「上下を詰めるな」から「左右も詰めるな」は出ない。**
- ⛔ **ただし左右も、gripper 幾何である以上 §0#4 の human-LOCK 下にあり Rs 専権**である。⇒ **私の §20.3 の選択肢 C（左右を詰める）は、本制約によって閉じたのではなく、*元から Rs 専権* ということ。** ⇒ **私の推奨は §20.3 のまま（まず A を測る）。**

### 20.4.1 ⭐ 分類器は 2 面ある — **述語を直しても生産コードは直らない**（p0 の切り分けを採る）

**geom id 厳密指定の hard 要件（§16.3）は *述語側（C レグ）* の話**である。一方 **`newton_skill_env_base.py:1392` は *生産コード側の分類器***であって述語ではない（**geom 名と body 名の連結に対する部分一致**）。
⇒ ⛔ **述語側を直しても `:1392` は直らず、`:1392` を直しても述語側の要件は別途要る。** **どちらか一方では閉じない。** ⇒ **要件を 2 本立てる**（採否のうち述語側は pZ、設計側は私）。
⚠ **p0 は当該 13 行を読んだだけで「同種の分類器が他に無い」ことは確認していない** ⇒ ⛔ **「無い」とは私も主張しない。**

### 20.4.2 ⭐⭐⭐ 「8 mm はどの面か」に答える ＋ **§20.2 の穴が解ける**（p18 `-060` A/B への回答）

⚠⚠ **先に 8.00 mm の *地位* を書く**（p18 `-063`・**Rs 本人からの直接指摘**「おれが 8mm と指定したわけではない」）:
- ⛔ **8.00 mm は Rs が指定した設計目標ではない。** 出所は **p4 が Ø8 から導いた量**であり、**p4 自身は自分の導出として書いていた**（**Rs 指定に格上げしたのは p18 で、p18 が撤回済**）。
- ✅ **量そのものは有効** — **`task_config.py:137` `CABLE_RADIUS = 0.004` ⇒ Ø8.00 mm** という **SSOT からの算術**であり、**「対向面はその隔たりで初めてケーブルに触れる」という幾何の事実**である。⛔ **設計目標ではない。**
- ⭐ **本節の裁定はこの帰属に依存しない** — 根拠は **z の重なりの計算**（下表）だけである。⇒ **撤回不要。**
- ⭐ **私の書き方の規律（採用する）: 数を回付するとき「測定」か「算術」か「人の指定」かを必ず書き分ける。⛔ 人の指定に格上げしない。**
⚠ **私の artifact に「Rs が 8 mm を指定した」という記述は無い**（閉じた query で確認 — 唯一の一致は §20.2 の見出し「**Rs へ上げる** 齟齬」であり、**上げる先**の意味であって帰属ではない）。⇒ **訂正すべき記述は無かった。**

**答: 8 mm が名指すのは *背板（パッド面）* の対向ペアである。** 理由は幾何で決まる — **ケーブルの高さに爪は無い**からである。

**私の計算（asset 値のみ・新規測定なし）:**
| 量 | 値 |
|---|---|
| slot の空き（pad-local z） | **27.00 … 37.00 mm** |
| ケーブル（中心 32.00・Ø8） | **28.00 … 36.00 mm** |
| ケーブル上端 → `f1ext` 下面 | **1.00 mm** |
| `f2ext` 上面 → ケーブル下端 | **1.00 mm** |
⇒ ⭐ **ケーブルはどちらの爪とも z で重ならない**（上下に 1.00 mm ずつ空く）。⇒ **対向する爪どうしの間にケーブルは *入らない*。** ⇒ **左右で当たり得るのは背板だけ** ⇒ **8 mm は背板の量。**

⭐⭐⭐ **⇒ ここから §20.2 の「1.98 mm の穴」が解ける。**
**対向爪が z でケーブルを外している**ということは、⛔ **爪どうしの接触（−0.07 mm）は、ケーブルが在っても同じように起きる**ということである（**ケーブルは爪の進路に無い**）。
⇒ ⭐⭐ **したがって「全閉で背板が 9.98 mm で止まる」のは *機構の行程の端* ではなく、*爪どうしが当たって止まっている* からである。** ⇒ **爪が互いを通り抜けられれば、顎はさらに約 2 mm 閉じ、背板が Ø8 に当たって圧縮する ＝ Rs の言う左右の摩擦が立つ。**
⇒ ⭐⭐⭐ **爪が互いを通り抜けられるようにする仕組みが、まさに banked の `exclude right_pad × left_pad` である**（`:173-175` 逐語「the protruding コ claws f1ext/f2ext **can overlap at `GRIPPER_CLOSE_QPOS`**」）。**p4 の移植版はその 1 行を落としている**（file 面・runtime 面とも確定）。

### 20.4.3 ⛔⛔ ⇒ **私の §20.1 の訂正（β の格下げ）を、さらに撤回する**

私は §20.1 で **p4 の C 限定（「爪どうしが噛むのはケーブルが無いときだけ」）を採り、§18.5 の β 格上げを取り消した**。⇒ ⛔ **その採用が誤りだった。**
**理由:** **私は自分で測った z の値（27.00–37.00 と 28.00–36.00）を持っていながら、それに突き合わせずに他 pane の限定を受け入れた。** **ケーブルは爪の進路に無い**のだから、**「ケーブルが在れば爪は届かない」は幾何的に成立しない。**
⇒ ⭐ **β（落ちた `exclude` 行）を再び先頭に戻す。** ⇒ **今回は「設計の読み」だけでなく *幾何の計算* が支える。**
⚠ **なお limitation は残す:** ①**因果は未測定**（`exclude` を戻した比較は誰も走らせていない）②**−0.07 はケーブル無しの測定**であり、**ケーブル在中で同値になることは推論**である（同じ指令での爪どうしの相対位置はリンク機構で決まる、という前提に依る）。⇒ **確かめ方は §11.5 の C-0**（banked から宣言差分で導出し `exclude` 集合を継承する）で、**実験を増やさずに済む。**
⭐ **私の欠陥の型（記録する）: 自分の手元に反証できる数がありながら、相手の限定をそのまま採った。** ⇒ **本日 6 回書いた「代理を読む」の、*自分の測定を代理で上書きする* 版である。**
⭐⭐ **同じ誤りを p18 も同じ材料で犯していた**（p18 `-064` D の自己申告）。⇒ **3 pane（私 / p0 / p18）が独立に同じ幾何へ到達し、私の再撤回と p18 の再撤回が一致した。**

#### 20.4.3.1 ⭐⭐ 規律を 1 つ採用する（p18 `-065` B の提案・私の lane に採る）

> **他 pane の限定を受けて自分の結論を下げる前に、その限定を否定できる数が自分の手元に無いかを先に見る。** 無ければ下げてよく、在れば突き合わせが先。

⭐⭐ **ただし、これは pZ の強化案に差し替える**（p18 `-067` B 経由。**pZ 案の方が優れている**）:

> **限定が成り立つための *前提* を先に書き出し、その前提を自分が測っているかを見る。**

⛔ **p18 案（および私が最初に採った形）では足りない理由（pZ の反例・私にもそのまま当てはまる）:** **自分の 2 つの数は、別々の目的で別々の時刻に導出したもの**であり、**記憶を走査しても引っかからない**（**実際に引っかからなかった**）。
⭐ **前提を書けば必ず気づく:** p4 の限定の前提は「**ケーブルが爪の進路に在る**」であり、これは **z の重なり**という **測定可能な量**である。⇒ **前提を書いた瞬間に、自分が両方の z を持っていることに気づく。**
⇒ ⭐⭐ **これは「recall（記憶の走査）」を「derivation（前提の明示）」に置き換える形**である。⚠ **本日の失敗は memory / recall 由来のものが繰り返し出ている**（時刻・行番号・帰属）⇒ **この置換は本件以外にも効く。** ⇒ **私の lane に採る。**

⭐ **私はまさにこれを踏んだ**（**自分で測った z を持っていながら、p4 の限定をそのまま採って β を下げた**）。
⚠ **同じ材料を持っていた 4 pane（私・p0・pZ・p18）が独立に同じ誤りを犯した**（⚠ **3 pane は誤り** — pZ の自己申告で 4 に訂正。**pZ の反証に要る 2 数は どちらも pZ 自身が導出したもの**だった） ⇒ ⭐ **これは個人の不注意ではなく、*同僚の限定は権威に見える* という構造的な引力である。** ⇒ **「代理を読む」の最終形 — 代理が *同僚の限定* だった版。**
⛔ **さらに 3 者とも「格下げ」ではなく「全否定」をした。** 正しい処置は **「爪板が止めている」を維持したまま、p4 の限定（ケーブル不在時のみ）*だけ* を検証にかける**ことだった。⇒ **私の memory にある「撤回の範囲も測定・格下げが既定」を、他人の限定を受けるときにも適用する。**

#### 20.4.3.2 ⭐ `exclude` の確認を **V レグ**に置く pZ の処置を支持する

pZ は最終的に **「`exclude` 対が model に在ることを *V レグの一部* として確認し、CLAMP-1 の合否レグには加えない」** とした。⇒ ⭐ **これは私が推奨した「理由づけの差し替え」より良い置き場所である。**
**理由:** **V は「その build で判定が成立し得るか」を問うレグ**である。⇒ **爪がケーブルに届く前に噛んで止まる build は、そもそも肯定判定を出し得ない** ⇒ **これは合否の条件ではなく *評価可能性* の条件**である。⇒ **V に置くのが正しい。**
⇒ ⭐ **§16.3.1 で私が書いた「片方向にしか判定できない述語は受入基準として成立しない」と同じ構造** — **判定できない状態を False と混ぜない**、が両方の芯である。

#### 20.4.4 ⚠ 「あとどれだけ閉じれば届くか」— **私の算術と、その仮定**

| 量 | 値 | 出所 |
|---|---|---|
| 全閉での背板 対向 | **9.98 mm** | p4 実測 |
| ケーブル | **8.00 mm** | `task_config.py:137` からの算術 |
| **背板がケーブルに触れるまでの追加行程** | **1.98 mm** | 上 2 行の差（私の算術） |
| **その時点の爪の重なり（1 対 1 を仮定した場合）** | **−2.05 mm** | `−0.07 − 1.98`（私の算術） |

⚠⚠ **仮定を明示する:** 上の **−2.05 mm は「爪の隙間と背板の隙間が同じ率で縮む」ことを仮定**している。⛔ **これは保証されていない** — **4 節リンクは pad を *傾ける*** ため（p4 実測）、**2 つの隙間は同率で縮まない可能性がある。** ⇒ **必要な重なり量は測って求める量であって、この引き算で確定する量ではない。**
⚠ **p18 が回付した値は −2.04 mm で、私の算術とは 0.01 mm 違う。** ⛔ **どちらかを黙って採らない** — **私は自分の算術（−2.05 mm）を書き、差があることを記録する。** ⇒ **差の原因は中間値の丸めと思われるが、確かめていない。**
⇒ ⭐ **結論として使える形:** **「全閉から *さらに約 2 mm* 閉じる行程が要り、その間 爪は互いを通り抜けていなければならない」** — **1 桁目までしか主張しない。**

⭐⭐ **追記: 私の「仮定」は、実は *データが既に反証している***（p18 `-066` B が 0.01 mm の差の出所として出した値から、私が導いた）。
**背板と爪の隙間の差（＝ offset）は指令ごとに違う**（⚠ **値の出所 = p0 / p18・私は再測していない**）:

| 指令 | 背板 − 爪 の offset |
|---|---|
| OPEN | 9.99 mm |
| HALF | **10.08 mm** |
| CLAMP | 10.05 mm |

⇒ ⭐ **1 対 1 で縮むなら offset は一定のはずである。実際は約 0.09 mm 動いている。** ⇒ **「同率で縮む」は仮定ではなく、*成り立っていない* と読める**（⚠ ただし **私の再測ではない**ので、**この読みも確定ではない**）。
⇒ ⭐ **0.01 mm の差の正体もこれで説明が付く** — **p18 は 3 指令の *平均* offset（10.04）を、私は **CLAMP 固有**の offset（`9.98 − (−0.07) = 10.05`）を使った**。⇒ ⛔ **どちらも誤りではなく、基準が違うだけ。** ⇒ ⭐⭐ **「どの基準を採るかで数が動く」こと自体が、この量が精密値でないことの証拠である。**
⇒ ⛔ **私は p18 の値で自分の値を黙って上書きしない。両方を、基準つきで残す。**

### 20.5 現在地

**保持機構 = Rs 裁定済（左右摩擦）。⇒ 問題は腕の位置決めへ収束**（§18.4 / §18.6.2 / §19）。**位置決めの要件 = ケーブル中心が pad-local z ≈ 32.0 mm・⛔ 世界固定オフセット不可 ⇒ pad body の `xpos` / `xmat` が前提**（§19.2-4）。
⛔ **Rs の機構裁定は解錠ではない。** 解錠は別途 Rs の明示が要る。**self-start しない。**

## 21. コ の第 2 機能（誘導）と、そこから決まること

**Rs 逐語（⚠ 出所 = p4 relay・p18 は Rs 本人と未照合）:** 「コは、半アンクランプでケーブルしごき誘導にも使用」
⇒ **コ の機能は 2 つ = ①クランプ時の固定 ②半アンクランプ時の しごき誘導。**
⭐ **工程表は元からそう書いていた**（`RL-Routing-Design.md` @ `59badc4b7a4dd7c6706c9a880d82a557fbb82c2b` 逐語・p18 実測）: `:1237` クランプ = `0.002` ／ `:1238` **半アンクランプ = フィンガ半開き（cable 軽保持・誘導用）= `0.006`** ／ `:1239` アンクランプ = `0.04`。⇒ **Rs 発言はそこに機構を与えたもので、設計は当初から内部整合していた**と読める。

### 21.1 ⭐⭐ 役割分担が確定する

| 軸 | 役割 | 根拠 |
|---|---|---|
| **左右（顎軸）** | **可変** — 締めれば固定（摩擦）／緩めれば滑走（誘導） | Rs 裁定（左右で摩擦）＋ 本節（半アンクランプで誘導） |
| **上下（pad-local z）** | **不変** — 常に含有 | **同一 pad の爪の上下は OPEN / HALF / CLAMP のすべてで +10.00 mm**（p4 実測・pZ 追認） |

⇒ ⭐ **上下の含有が顎の指令に依存しないからこそ、左右を緩めてもケーブルは コ から落ちず、滑らせて誘導できる。** ⇒ **§20 の機構裁定と完全に整合する。**

### 21.2 ⛔ slot を詰める案は **二重に**排除される

① **位置決め許容が 1 対 1 で消える**（§20.4: 帯幅 = W − 8.00）／② **詰めると しごき時の摩擦が上がり、第 2 の機能（誘導）そのものが成立しなくなる。**
⇒ ⛔ **非把持の是正として slot を詰める案は採らない**（§20.4 の射程確定を、理由 2 本で確定する）。

### 21.3 ⚠ pZ v0.2 への支持と、**理由づけ 1 点への異議**

**支持:** **C を BILATERAL に確定**（摩擦面は対向する背板ゆえ**両 pad の `pad1` との接触**を要求／爪板は**記録するが要求しない**）— **§20.4.2 の私の計算と一致する**（ケーブルは爪と z で重ならないので、爪は把持面になり得ない）。**F レグ（圧縮 = 両側接触かつ法線力 ≠ 0）と N5（両側接触・法線力 0 ⇒ False）も支持**する — **接触の存在では不足**という p4 の符号訂正が正しいからである。

⛔ **異議 1 件（理由づけについて。処置そのものではない）:** pZ は **`exclude` を受入経路の要素から外した**際、理由を「**噛み込みはケーブル不在の症状ゆえ、正しい位置なら評価経路に影響しない**」とした。
⇒ ⛔ **その理由は幾何的に成立しない。** §20.4.2 のとおり **ケーブルは対向爪の進路に無い**（上下に 1.00 mm ずつ空く）ので、**爪どうしはケーブルが在っても同じように当たる。**
⇒ ⭐ **処置（受入述語に `exclude` を入れない）は妥当**である — **`exclude` は述語の要素ではなく、*顎がケーブルまで閉じられるか* という到達性の側の問題**だからである。⇒ **理由づけだけ差し替えることを推奨する。** ⚠ **放置すると「`exclude` は無関係」と読まれ、§20.4.3 の帰結（β が先頭）を打ち消してしまう。**

### 21.4 ⭐ 述語の適用範囲（p4 の指摘を支持）

**クランプ状態と半アンクランプ状態は別の述語が要る。** 半アンクランプは **含有したまま滑る**状態で、**滑ることが正常**である ⇒ **CLAMP-1 の R レグ（保持の連続性）をそのまま適用すると偽陰性**になる。
⇒ ⭐ **CLAMP-1 の適用範囲を明示することを推奨**（確定は pZ の court）。⇒ **誘導側にはいずれ別の述語（例: 含有を保ったまま所定の向きへ移動していること）が要る**が、⛔ **今の目標はクランプゆえ、私はここで誘導側の述語を設計しない。**

### 21.5 ⭐⭐ 位置決め精度の問いに、既存の数を使わない

**p0 の予見的な封じ込めを採る:** ⛔ **p0 の Jacobian / たわみ数値を「腕は ±1.0 mm を保てるか」の答えに使わない。** 理由 4 件（いずれも本 doc 既報）: ①**点が違う**（3 点はどれも slot 中心ではなく、J-a / J-c は EE 基準の *世界固定* オフセットで pad が傾く = §19）②**基盤が違う**（UR5e 生産 build・UR15 生産 env は不在 = §8.1）③**build が違う**（flag-OFF・指の servo 未結線 = §12.3）④**たわみは方法ごと撤回済**。

⭐⭐ **その ±1.0 mm がどこから来るかを、私の court として明示する:** **完全含有帯は `[31.00, 33.00]`（幅 2.00 mm）** ⇒ **中心 32.00 に対して ±1.00 mm。** ⇒ ⭐ **位置決めの要求精度 = pad-local z で ±1.00 mm であり、これは clearance の半分に等しい。** ⇒ **設計が与えた許容そのもの**であって、私が選んだ数ではない。

⇒ **答えるのに要る測定（⛔ 解錠待ち）= slot 中心を参照点とした Jacobian を、UR15 の生産 env・flag-ON build で測る。** ⚠ **それ自体が `pad` body の `xpos` / `xmat` の記録を前提**とする（§19.2-4）。⇒ **当該記録項目は 3 用途（P レグ／参照点／位置決め要件）を持つ** ⇒ **解錠時の実装優先度は最上位。**

## 22. ⛔⛔ **私の §18–§20 は、banked 設計の再発見だった** — §運用4 の不履行を own する

### 22.1 逐語（**私が自分で読んだ**・`06-Knowledge/GD-KoShape-Finger.md`・全 237 行）

- **`:95-96`**: 「Grip = **COMPOSITE**: lateral flat-pad (`pad1`) pinch **[dominant, −1.06/−1.39]** + vertical claw (f1ext/f2ext) straddle **[−0.7]**; **f1ext bottom claw engages under lift load** = the open-bottom catch the V-groove lacked（the コ rationale, CPU-supported）」
- **`:58-59`**: 「**Gap between the two claws ≈ 10mm (Ø8 + 2mm)**. At the grasp pose: f1ext Z≈796.6（**BELOW** cable）, f2ext Z≈809（**ABOVE** cable）, cable Z≈800-808 **between them**」

⇒ ⛔⛔ **私が §18 で「幾何から導いた」保持機構は、ここに全部書いてある。** **背板 `pad1` の挟みが *dominant*、爪は *straddle*（またぎ）**であり、**私の面の裁定（左右は背板・上下は爪）と一致する。** ⇒ **新規の設計判断ではなく、再発見だった。**

⭐ **しかも doc は私の導出より多くを持っている:**
- **貫入量つき** — `pad1` の挟みは **−1.06 / −1.39 mm** の貫入として記録されている。⇒ ⭐ **これが Rs の言う「左右の摩擦」の実体であり、「圧縮が要る」（p4 の符号訂正）の裏づけでもある。** ⇒ **私が §20.2 で「1.98 mm 空くので摩擦が立たない」と報告した状態は、*設計が想定した状態ではなかった*。**
- **`f1ext` は持ち上げ荷重で効く**（open-bottom catch）⇒ **爪の役割が「またぎ」＋「落下の受け」だと明示されている。**

### 22.2 ⛔ 私の不履行

**§運用4 は「設計着手前に `06-Knowledge` の該当ファイルを参照」と定めている。** ⇒ 私は **`:11-13`（p18 の relay 経由）と `:58` の断片しか読まず**、**doc を最後まで読まないまま設計を導出した。** ⇒ **部分読みを「参照した」として扱った。**
⭐ **教訓（本日の型の最上流版）: 設計を導出する前に、設計 doc を最後まで読む。** ⇒ **「代理を読む」の代理が *doc の一部* だった版**である。
⚠ **過剰に卑下しない（自分の規律を自分に適用する）:** 導出が無価値だったのではない — **独立に同じ結論へ到達したこと自体は banked 設計の妥当性を追認している**し、**doc に無いもの**（**溝の深さ 5.00 mm**・**z の非重なり**・**位置決め許容 ±1.00 mm の出所**）も出た。⛔ **ただし順序が逆であり、doc を先に読んでいれば β の格下げ→再撤回の往復は起きなかった。**

### 22.3 ⭐⭐ `exclude` 比較が測定された — **私の読みが支持された**

**artifact = `P4_EXCLUDE_RESTORED_PINCH_MEASUREMENT_20260727.md` @ `53217d96fb1d4496cf4b58be401cabae2445ee59`（sha256 `1a0fe6a7c48e8ff92476f03cea958f2b72ba594c65a98419ecc299d2aff9e771`・p18 が pin 照合）。**
`exclude` 復帰で **`nexclude` 6 → 7**。**背板 ↔ ケーブル**（mm）:

| 指令 | L | R | 接触 |
|---|---|---|---|
| OPEN | +23.60 | +23.60 | なし |
| **HALF** | **−0.08** | **−0.08** | ⭐ **`left_pad1` と `right_pad1` の両方** |
| CLAMP | +4.60 | +4.60 | `f2ext` のみ |

⇒ ⭐ **復帰前は全指令で背板接触 0 件だった。復帰後、両側の背板がケーブルに接触する指令が存在する。** ⇒ **§20.4.2 / §20.4.3 の私の読み（`exclude` は症状でなく経路）が支持された。**
⛔ **限定 4 件を必ず併記する（p4）:** ①**CLAMP 行は実挙動の代表でない**（ケーブルが関節を持たない固定体ゆえ、強駆動で 4 節リンクが押し返され pad が乗り上げる）②**`pad1`↔`pad1` の列は面間隔として読めない**（傾きで最近接点が移る）③**`exclude` が唯一の原因までは示していない** ④**受入判定ではない。**
⚠ ⭐ **私の観察を 1 つ足す:** **接触が出たのは `HALF`** であり、これは工程表 `:1238` の **半アンクランプ（誘導用・`0.006`）**と同じ指令である。⛔ **偶然か設計かは判定しない**（限定 ①② がまさにこの行の読み方に効く）。⇒ **surface のみ。**

### 22.4 ⭐ 規律を 1 つ追加（pZ の 5 例目の自己申告から）

> **「恒等的に」「常に」「必ず」と書くときは、それが *全称主張* だと認識し、前提を書き出して手元の数で確かめる。**

⇒ **§20.4.3.1 の「前提を書き出す」の適用先を、*限定を受けるとき* から *自分が全称を書くとき* へ広げたもの。** ⇒ **私も採る。**

### 22.5 ⚠ gate について（誤読防止）

⛔ **p18 は解錠していない。** §22.3 の実行は **Rs 本人の直接指示**（逐語「はやくコでケーブルクランプして動画を！！」）によるものである。⇒ ⛔ **一般解錠ではない。** **他の実行・実装・status / gate flip は CLOSED のまま。** ⇒ **私は self-start しない。**

## 23. p5 の裁定との一致・`exclude` の位置づけ・**私の新発見 1 件**・転移リスク

### 23.1 ⭐ p5（設計 court）の裁定は私と独立に一致した

**Q1 = (a) 背板**（`pad_box1` の前面・pad-local y = +1.40 mm）。**爪板の先端対向面はケーブルに当たり得ず、爪の役割は y の摩擦ではなく z の形状拘束。** ⇒ **私の §20.4.2 と独立一致。**
**Q2 = 必要条件であって *十分条件ではない***（**到達性 = 4-bar の travel 限界は未測**）。⇒ ⭐ **この限定を私も採る** — **§20.4.4 で私が「必要な重なり量は測って求める量」と書いたのと同じ穴**であり、**背板がケーブルに届く指令が機構の可動域内に在るかは、まだ誰も測っていない。**

### 23.2 ⭐⭐ `exclude` 復帰は **設計変更ではなく LOCK への準拠**

**banked の asset 群はいずれも `exclude` を持ち、欠落しているのは生成物のみ**（p18 実測）。⇒ ⭐ **したがって「復帰」は banked LOCK 状態への復帰であり、幾何の変更ではない。** ⇒ ⭐⭐ **§0#4 の論点が 1 つ軽くなる** — **derived model が `exclude` を継承することは LOCK の変更ではなく *準拠* である**（⛔ §0#4 の裁定自体は Rs のまま）。⇒ **§11.4-1 / §12.3 の C-0（banked から宣言差分で導出し `exclude` 集合を継承）は、*準拠の形* だと確認された。**

⭐ **私の実測を 1 つ足す — `exclude` の射程は「body 対」である:** `:176` は `<exclude body1="right_pad" body2="left_pad"/>` であり、**`right_pad` body が持つ geom は `right_pad1` / `right_pad2` / `right_pad_f1ext` / `right_pad_f2ext` の 4 つ**。⇒ **除外は爪どうしだけでなく *背板どうし* も含む 16 対すべてに掛かる。** ⚠ **一方、ケーブルは別 body ゆえ pad↔ケーブル接触は掛からない**（banked コメント逐語「Cable contact is UNAFFECTED」と一致）。⇒ **だから「爪を通り抜けさせつつケーブルは掴む」が同時に成立する。**

### 23.3 ⭐⭐ **私の発見 — 同名の生成 model が 2 つあり、`exclude` 状態が違う**

**私の閉じた query（tracked ＋ 作業ツリーの `*koshape*.xml` 全件・書式の仮定なし）で判明:**

| path | tracked | mtime | sha256 | `exclude` | pad 対 |
|---|---|---|---|---|---|
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/_ur15_2f85_koshape_actuated.xml` | ✅ | 04:18:21 | `c2d65167d32b413bcbf2985a153025e5455a3d5e8051cd89733cb67e11751ffe` | **6** | ⛔ 無 |
| `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` | ⛔ untracked | 12:20:38 | `1966631e61496f980c398bee17d46bfda3eafd38b497c35d584cf403a03015c0` | **7** | ✅ 有 |

⇒ ⭐⭐ **同じ basename の file が 2 つあり、内容も `exclude` 状態も違う**（⚠ **`exclude` 行以外にも差がある** — 私が diff で確認）。**新しい方は §22.3 の復帰測定のための再生成と思われるが、私は確かめていない。**
⇒ ⛔ **basename で引用すると、どちらを指すか決まらない。** ⇒ ⭐ **要求: 生成 model は *full path ＋ sha256* で引用する。** ⚠ **今のところ既存の引用は sha256 つきで正確**（p18 `-049` は `c2d65167…` を明示）だが、**basename だけの引用が 1 つ出れば取り違えが起きる。**
⚠ **もう 1 点 surface:** 新しい方は **banked asset と同じ dir（`assets/ur5e_robotiq/robotiq_2f85/`）に untracked で置かれている** ⇒ **banked asset と見間違え得る場所**である。⛔ **私は移動も削除もしない**（他 pane の生成物）。

### 23.4 ⚠⚠ 転移リスク（p5 §7）— 私の court として答える

**p5 の指摘:** **実機では爪の相互貫入は成立しない** ⇒ それに依存した成立は **転移時 non-conservative**。
⇒ ⭐ **私の整理（分岐は 2 本で、どちらかは測れば決まる）:**
1. **爪が互いを *通り抜ける*（貫入）なら** ⇒ sim だけの現象 ⇒ ⛔ **sim の成立を転移の主張に使えない（non-conservative）。**
2. **4-bar の傾きで爪が互いの *脇を通る* なら** ⇒ 実機でも起こり得る ⇒ **`exclude` は「元々起きない接触」を消しているだけ**で、保守性に中立。
⇒ ⭐ **これは私が §20.4.4 で提起した「2 つの隙間は同率で縮まない」と同じ論点**である（**傾きが効くなら脇を通り得る**）。⛔ **どちらかは誰も測っていない。**
⇒ ⭐⭐ **測り方 — 私の案は取り下げ、pZ の v0.3 を採る**（p18 `-072` A/B 経由。**pZ の方が簡潔で、しかも十分**）:
> **CLAMP-1 が *成立した瞬間* の対向爪どうしの距離を必ず記録し、負（貫入）なら verdict に `non-conservative for transfer` の tag を付す。**

⭐ **符号だけで分岐が決まる** — **脇を通れば正のまま／貫通すれば負**。⇒ ⭐⭐ **同じ 1 つの測定が、私の §20.4.4 の論点（2 つの隙間が同率で縮むか）と p5 の転移リスクを *同時に* 閉じる。**
⛔ **私の旧案（閉じ行程を通して横オフセットと重なりを記録する）は取り下げる** — **必要以上に重い。** ⚠ **両者の違いを正確に言うと:** 旧案は **写像そのもの**を得る／pZ 案は **動作点での符号**を得る。⇒ **設計判断に要るのは後者だけ**である（**成立が貫入に依存したか否か**）。⇒ **写像が要るのは、後で指令値を設計する段になってからで、今ではない。**
⭐ **計器は既存で足りる**（`mj_geomDistance` は本 project で使用中・**新規計装は不要**）。⚠ **かつこれは 1 軸の投影ではなく 3 次元の面間距離**である ⇒ ⭐ **`pad` 姿勢（`xpos`/`xmat`）は *この識別* には要らない**（p18 の整理）。⛔ **ただし繰越の他 3 用途（P レグ／位置決め参照点／位置決め要件）では引き続き必要**ゆえ、**優先度は下がらない。**
⭐ **`exclude` 行の存在自体が設計時の主張である**（p0 の論法・私も採る）: **そもそも重ならない body 対に collision の exclude は要らない** ⇒ **行が在ること自体が「重なりが起きる」という設計時の想定**。⇒ ⚠ **これは転移リスクを弱めるのではなく *具体化* する** — **設計は sim 上で貫入が起きることを前提に置いた** ⇒ **実機で貫入しないなら、その前提は実機に無い。** ⇒ **リスクは測るまで生きている。**
⛔ **私は判定しない。** ⚠ ただし **§運用15 の conservatism 方向の規則により、1 の場合は「sim が現実より易しい」側**であり、**転移前に高 fidelity か実機確認が要る**。⭐ **Rs の恒久原則「sim は現実世界だ」に照らしても、1 のまま進めるのは筋が悪い。**

### 23.5 ⭐ pZ の CLAMP-1 修正を支持する（banked `:95` 準拠）

- **C: 爪板を「記録のみ」から格上げ** — `:95` は **COMPOSITE**（`pad1` pinch が dominant ＋ claw straddle）と書いており、**straddle も grip の一部**だからである。⭐ **私の §20.4.2（左右で当たるのは背板だけ）と矛盾しない** — **爪の寄与は *z の拘束* と *持ち上げ時の catch* であって、左右の挟みではない。** ⇒ **両立する。**
- **R: `f1ext` 接触の確認を追加** — `:95` 逐語「**f1ext bottom claw engages under lift load**」ゆえ、**R レグ（支持を外す）はまさに lift load の状態** ⇒ **`f1ext` 接触が出ないなら open-bottom catch が機能していない**、と読める。⭐ **良い設計**である。
- **F: banked の貫入量（`pad1` −1.06 / −1.39・claw −0.7）を「機能していた時の圧縮の実測参照」として記録**（⛔ **閾値としては採らない** — 基盤も build も違う）。⭐ **この限定つきなら支持する。**

### 23.6 ⭐ 規律をもう 1 つ採る（pZ 発・p18 実測で裏づけ）

> **範囲の限られた doc は grep せず読む。grep してよいのは「在ることを知っている物を探す」ときだけ。**

**裏づけ:** pZ の検索語 8 件（`held` / `grasp` / `criteri` / 判定 / 述語 / `predicate` / `slot` / `retain`）は **`GD-KoShape-Finger.md:94-96` に 1 件も当たらない**。当該箇所の語彙は **`pinch` / `straddle` / `dominant` / `COMPOSITE` / `engages` / `lift load` / `catch`**。⇒ ⛔ **keyword 検索は「doc の語彙を既に知っている」ことを前提にしている。** 知らなければ空を返し ⇒ **「書かれていない」と結論し** ⇒ **自分で導出する**、という経路に入る。⇒ ⭐⭐ **本日 5 pane が数時間かけたのは、まさにこの経路である。**
⚠ **当該 doc は 237 行** ⇒ **読める長さだった。** ⛔ **私の場合は grep ですらなく、relay された断片を受け取っただけ**であり、**より弱い接地だった。**

---
**p11 custody = 2026-07-27 / ARM-CONTROL-DESIGN (`w2:p11`)。⛔ 本書の bank commit と sha256 は提出 message の宣言値が権威**（本書は自身の commit を pin できない）。
