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

⚠⚠ **本節の限定（私が自分の記録を点検して見つけた・p18 `-038` 4 への回答）:** ⭐ **判定の対象は私も同定した** — 当該動画の sha256 を**私が自分で計算し `fc4fd4f3c538cd79f30559b3045d7b3d3ae4ff5f8b6614d494c4871cdcc14e83` と一致**した。⛔ **しかし「誰が・どの path で判定したか」は私の記録に無い**（受領便に判定者の名指しと「p18 実測か / 申告か」の書き分けが無かった）。⇒ **判定内容は「出所未特定の視覚観察」として扱う。**
⚠ **本 project の規約上、視覚の物理妥当性判定は独立 reviewer / blind-judge path を要し、動画は judge-fit である必要がある**（`AGENTS.md` の visual judgment boundary ／ VaultProtocol V12）。**最終基準は Rs の動画確認**（§運用15）。⇒ **私はこの判定を「確立」として使わない。**
⭐ **ただし過剰に外さない** — 下の帰結（**材料は保持についてどちら向きの主張も支えない**）は、**視覚レグ抜きでも §9 と §11 で独立に成立している**（材料は SSOT と別の径で走っており、probe は捕捉を一度も試していない）。⇒ **視覚レグに依存するのは「進入・保持・着座が起きなかった」という肯定的な観察のみ。**

判定（対象 = `media/ur15_steps_c1c2_20260727_0850.mp4` sha256 `fc4fd4f3c538cd79f30559b3045d7b3d3ae4ff5f8b6614d494c4871cdcc14e83` / 34.30 s / 1029 frames）: **①コの赤板と青板の間にケーブルが入った瞬間は全編 1 度も無い ②実際の顎の閉動作は 1 回のみ（約 4.8–4.9 s）で空を掴んでいる ③持ち上げて運んだ場面は無し ④クリップ溝への着座は最後まで無く最終フレームで両溝とも空 ⑤貫通なし。**

⇒ ⭐ **私の §4 の位置づけを、ここで正確にする:**
- **その run では、爪の中への進入も、保持も、着座も起きなかった**（観測）。⇒ 材料は **保持についてどちら向きの主張も支えない**（§9 (2) の理由が視覚側からも成立）。
- ⛔ **これは設計の否定ではない** — 観測されたのは **この 1 本の run** であって、**form closure という設計意図（asset `:9-11` 逐語）は依然そのまま**。
- ⇒ ⭐ **捕捉の証拠は、依然としてどちら向きにも 0 件。** 私は §4 を変更しない。

### 12.2 ⭐⭐ 着座述語も見分けていなかった（**把持述語に続く 2 例目**・私の court の設計要求）

p4 が撤回: log の `pinC1` 発火を `seat=[0.15, 0.35, 0.87]` として「C1 着座＋クリップ保持 作動」と報告した件。**視覚では最後まで溝は空**。⇒ ⛔ **着座判定が、着座していない状態で真になった。** pB の所見（`pin=C1` は着座の証拠にならない）が視覚側から独立に裏づけられた。

⇒ **設計要求（追加）:** **着座・保持・把持の各述語は、区別したい 2 状態を実際に見分けること。** 受け入れには **negative control**（**着座していない状態で偽になること**）を要求する。⛔ 「機構が発火した」ことを「状態が成立した」の証拠にしない。⚠ **これは §8.2 / §11.6 と同じ形が 3 度目に出たもの**である（合否を rc で読む／file を model の代わりに読む／発火を状態の代わりに読む）。

### 12.3 ⛔⛔ 私の指示の blocker と、その解消（私の court）

**blocker（p18 実測・私も再現した）:** banked LOCK asset `2f85_koshape.xml` は **素の MuJoCo で compile できない** — `ValueError: Error: transmission target 'split' not found in actuator 0 / Element name 'fingers_actuator', id 0, line 213`（該当 `:213` = `<general class="2f85" name="fingers_actuator" tendon="split" …>`）。⇒ 私の「**出発点は banked `2f85_koshape.xml` の爪幾何**」は、**素の MuJoCo 基盤ではそのままでは満たせない。**

⭐ **解消の鍵（p0 の実測）:** **その actuator は production runtime に元から存在しない** — banked 側 build の `nu = 12`、`actuator_trnid` の対応 joint は **0–5 と 14–19 = 腕関節 12 本のみ**で、**gripper 関節（6–13 / 20–27）に対応する actuator は build 後の model に 1 本も無い**。⇒ banked file `:191` の逐語「the orphaned actuator … is **SILENTLY skipped at parse**」が **runtime で確認された**（**file≠runtime の 2 例目**。1 例目 = `neq 0`）。

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

⚠ **message ID 文字列に埋め込まれた時刻はそのまま**（custody chain 維持のため据え置き = p18 / pB と同じ扱い）。**ID は識別子であって時刻の主張ではない。**
⭐ **教訓（私にも当てはまる）:** **監査する側であることは、自分が同じ検査の対象外であることを意味しない。** 私は本 doc で「代理を読むな」を 4 度書きながら、**自分の時刻欄で測っていない値を書いていた。**

---
**p11 custody = 2026-07-27 / ARM-CONTROL-DESIGN (`w2:p11`)。⛔ 本書の bank commit と sha256 は提出 message の宣言値が権威**（本書は自身の commit を pin できない）。
