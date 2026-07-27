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

⛔ **「interpreter 未解決」を前提にしていない。** 原因側の訂正が着地済 = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_INTERPRETER_CLAIM_CORRECTION_20260727.md` @ `511e363317a808d79e9a9e3a2e269b67993cffba`（sha256 `2cdb9d21b288c0077d6750815d7d3a8c35b659598106953065aa73050787c255`・parent `8162d3b2bbced968de3a352c1cb7a3c855e1049a`。**私が自分で読んで sha256 一致を確認**）。⇒ **正しい実行形 = repo root から `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p`**。⚠ **asset closure 欠如は interpreter と独立に存続**するので、§3 の前提条件として扱っている（p18 `-005` 5 と同旨）。

## 7. 閉じた query（不在主張の裏づけ）

項目 1 の「12 通り掃引」に **producing artifact があるか**を、閉じた集合に対して検索した。

- **集合** = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_UR15*.md`（5 件: `CONTROL_SAMPLE` / `GEOMETRY_MEASUREMENT` / `HANDOVER_TO_IMPL_CHAIN` / `RECORDS_CORRECTION_V2` / `RECORDS_CORRECTION_V3`）＋ `p4_ur15_sim_20260727/` の全 file
- **query** = `grep -rn "掃引|12 通り|12通り|0\.40 m|spread 0.40|YOKE_SPREAD"`（⛔ `head` / `tail` を通していない）
- **結果** = 0.40 / 20° は **`p4_ur15_sim_20260727/ur15_steps.py:37` の定数と行内コメント 1 行としてのみ存在**。**掃引の script・入力範囲・出力表・seed は上記集合に無い。**
- ⚠ **限界:** これは**上記集合についての不在**である。p4 の session ローカルに在る可能性は否定しない（同 doc は log を durable pin できないと明記している）。⇒ **在るなら pin つきで出してもらえば項目 1 の (a) は満たされる。**

---
**p11 custody = 2026-07-27 / ARM-CONTROL-DESIGN (`w2:p11`)。⛔ 本書の bank commit と sha256 は提出 message の宣言値が権威**（本書は自身の commit を pin できない）。
