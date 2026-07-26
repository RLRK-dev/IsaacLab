# 腕制御 測定ハーネス 仕様 v1.7 — p0 実装 / pZ 検証（p11 ARM-CONTROL-DESIGN, 起草 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** SPEC **v1.7** — **proposal**（landing = p4 経由）。
⚠⚠ **records 訂正（RETURN-011 R3 受理）**: `0f373bedbdfa25d361917e50036e11947b146bdf`（2026-07-26T16:08:16+0900）は **v1.7 の *initial* semantic landing**（pad body 導出規則の訂正）**であって、本 file の現在版ではない**。⇒ 同 blob はその後 **`fe22276f2c`（title/status 同期）→ `9d6aed738d`（`:6` self-cite 訂正）** で修正済。⛔ **旧 header は「更新 = 16:08:16」と読めたが stale。**
⭐ **本 file の *現* pin は、自己参照では書けない**（commit する前に自分の SHA は決まらない）。⇒ **現行 pin は外部の routing 提出物（`P11_ROUTING_SUBMISSION_20260726_ARMCONTROLDESIGN.md` の当該版が申告する 3 SHA）を正とする。⛔ 推測時刻を書かない。**
**版歴（内容 pin・sha は照合記録）:** v1.0 `054a54bbb6` → v1.1 `37902fb909`（pZ の model-identity 入力）→ v1.2 `3cb06b0fe5`（**H-2 DOF 宣言**）→ v1.3 `c8c326e00b`（**参照同一性 I-1〜I-3 を主レグ**へ）→ v1.4（**H-4 を 3 参照点に** = §H-4.1。閾値の `EE_TO_FINGERTIP=0.220` は **Franka legacy**・実測コ字値と 34.8〜55.7 mm 違う）→ v1.5 `cca446e1a6`（**§H-5.1 把持状態の ζ**）→ v1.6 `0025fd32b6`（**§H-3.1 = per-joint `τ_bias`**）→ ⭐**v1.7**（**§H-4 の pad body 導出規則を訂正** — 旧 `body_label` 検索は**現モデルで実行不能**。p4 の R8 裁定 `442f58678359bf85` が **spec owner = p11 へ RETURN** したのを受けた**記録是正**）。
⚠ **v1.4〜v1.7 の変更はいずれも該当章に限局**（他章は無変更）。
⛔⛔ **本 spec は実装 gate ではない**（接地 = **`:238`**「実 run / training / landing の認可でない。⛔ p0 は本 spec の範囲＝測定のみ」＋ **`:244`**「確定するまで本 spec を実装 gate として使わない」。⚠ 旧 cite `:237` は誤り — 同行は **H-6 各機構の非採用**を述べており、実装 gate の話ではない）。**v1.6 §H-3.1 は authorization 無しに実装され、p4 が `d724031b77` で「既存 GO 無し・認可外」と裁定済**。⇒ **本 spec の章が tree に在ることは、実装してよいことを意味しない。**
**根拠:** Rs 裁定 = **案 A 採択**（p4 relay 2026-07-21 15:44）。**設計数値を手で導かない。** 私は **spec + 受入条件**を書き、**p0 が実 build して測り**、**pZ が実 build と突き合わせて model-identity を検証**する。数値はその**検証済み出力**から取る。
**下敷き:** v0.4 手続き（`c51dad2d54`）。⚠ v0.4 は BLOCK 済ゆえ**そのまま採らない** — 下記 §0 の 1 点を構造的に変える。

⛔ **本書は測定の仕様であって、制御設計の確定ではない。** gain・bar・`ζ_target` は**本書で決めない**（決めれば v0.2-v0.4 の 3 連続失敗を 4 度目に繰り返す）。
⛔ **p0 は本書で設計判断をしない**（測るだけ）。⛔ **実 run / training / landing は別 gate**。

---

## 0. ⭐ v0.4 との決定的な違い — **ハーネスにモデルを組ませない**

v0.4 の致命 = **私が書いた build recipe が、実際に走るモデルを作らなかった**（28 body / cable なし / equality なし / gripper 剛性なし）。しかも env は内部に robot-only の FK モデル（`newton_route_env.py:690` `self._fk_model`）を別途持つため、**照合すると一致してしまい、ゲートを通過したまま誤ったモデルを解析できた**。

⇒ **構造的な修正**:
> **ハーネスはモデルを組み立ててはならない。** 実際に構成された **env インスタンスが `SolverMuJoCo` に渡した physics `Model` オブジェクトそのもの**を受け取って測る。

- ⛔ `add_ur5e_robotiq` 等を**ハーネスが呼ばない**（＝ 私の再構成が経路から消える）。
- ⛔ `self._fk_model`（IK 用 robot-only）を**測定対象にしない**。**明示的に排除**すること。
- ⇒ **「測ったモデル ≠ 走るモデル」が原理的に起こらない**。私の読み違いが入り込む余地を無くすのが本節の目的。

---

## 1. H-0 モデル取得と同一性（**pZ が検証する段**）

**p0 が行うこと**
- 生産経路で env を構成し、**その instance が保持する physics `Model`** を取得する。
- 取得した object について次を**出力に記録**する（判定はしない・記録のみ）:
  - `id()` または等価な同一性の証跡、および**それが `SolverMuJoCo` に渡された object であること**を示す経路
  - body 数 / body ごとの質量 / DOF 数 / joint 名と順序 / `nu` / actuator ごとの `forcerange` と対応 joint
  - equality 制約の件数と種別 / cable の body 数 / gripper servo の `ke,kd,effort`
  - `joint_effort_limit` の全値 / `jnt_actfrcrange` の全値

**pZ が検証すること（受入の中核）**
| # | 述語 |
|---|---|
| V-1 | 測定対象が **env が実際に solver へ渡した Model** であること（**別 build でも FK モデルでもない**）⇒ **§1.1.0 の I-1〜I-3（`is` 比較）で決める** |
| V-2 | 上記記録が、**pZ が独立に構成した env** の同一項目と一致すること |
| V-3 | ⭐**scene 固有物**が在ること（§1.1.1 の **cable leg**）— 参照同一性の **backstop**。⚠ v1.1 が挙げた A-1 VISIBLE / clip は **識別しない or handle 不在**と実測（§1.1.1） |
| V-4 | 掃引に使う `q` が **joint 名で解決**されている（index 直書きでない） |

### 1.1 ⭐ 同一性は **参照**で取る（v1.3 で構造変更・landing commit `c8c326e00b04874cca2c20d17355c3f944cb5119` = 2026-07-21T20:48:13+0900）

⚠⚠ **v1.1 の witness 前提は p0 の h0 実測で 2 点が偽と判明**（`a3e07577ba` + report `negative_control_ac9`）。⭐ **これは私が AC-9 に置いた negative control が仕事をした結果**であり、harness 側の欠陥ではない。⇒ 下記へ差し替える。

#### 1.1.0 ⭐⭐ 主レグ = **object 参照の同一性**（指紋ではなく参照で決める）

**scene は `model` と `solver` の**両方**を返す**（`newton_route_env.py:725-726`「`self._model = scene["model"]` / `self._solver = scene["solver"]`」）。⇒ **同一性は内容の一致で推定するのではなく、同じ object かどうかで決められる。**

| # | 述語（**すべて `is` 比較**） | 接地 |
|---|---|---|
| **I-1** | 測る `Model` **is** `scene["model"]` | `newton_route_env.py:725` |
| **I-2** | `scene["solver"].model` **is** 測る `Model`（= solver が積分している当の object） | `SolverBase.__init__` 逐語 `self.model = model`（`newton/_src/solvers/solver.py`。**p11 が env7 python で実行して確認**・同 v1.3 の landing commit `c8c326e00b` 以前） |
| **I-3** | 測る `Model` **is not** `env._fk_model` | `newton_route_env.py:690` |

⇒ ⭐ **指紋（内容の一致）は参照に勝てない。** I-1〜I-3 を主レグにすれば、「witness が識別できていなかった」という失敗の族そのものが閉じる。

#### 1.1.1 内容 witness（**backstop に降格**）

⛔⛔ **DOF 数・gripper joint の有無では FK robot-only と as-built を分けられない。**
実測: `build_fk_and_init(left_finger_pos, right_finger_pos, …)`（`newton_skill_env_base.py:1223`）は **指の位置を引数に取る** ⇒ **FK モデルも gripper 系 joint を持つ**。

| witness | 扱い（**v1.3**） | 根拠 |
|---|---|---|
| **cable** | ✅ **維持・唯一の識別レグ** | `add_revolute_cable` が両腕の後に発行する REVOLUTE 鎖（`newton_skill_env_base.py:1587`）。handle は `scene["cable_bodies"]`（`newton_route_env.py:733`）。**FK では index 解決に失敗し reject される**（p0 実測） |
| **A-1 VISIBLE の痕跡** | ⛔ **必須集合から除外 → 文脈記録のみ** | **実 68-body でも FK 28-body でも pass=true**（p0 negative control 実測）⇒ **識別子でない**。出力には残すが「識別しない」と明記する |
| **clip** | ⛔ **witness から削除** | `scene` の**閉じた key 集合**（`newton_route_env.py:725-734` = `model` / `solver` / `state_0` / `state_1` / `control` / `contacts` / `bws` / `jws` / `cable_bodies` / `cable_bodies_per_world`）に **clip の key が無い**（p11 実測）。clip body は `body_N` 自動ラベル ⇒ ⛔ **部分一致で探さない**（0 件が「clip 無し」と読めてしまう偽陰性） |
| **world_count** | ⚠ **配置の照合として維持**（識別レグではない） | 宣言値と一致すること。⛔ 単独では FK と分けられない |

⭐ **clip handle は今は作らない。** 識別は cable と I-1〜I-3 で足りており、handle 露出は env 変更（p4 court）。⇒ **将来 clip 固有の測定が要ると判明したら、`scene` に**ラベル付き handle を足す**（⛔ 文字列一致で探す実装にしない）。

⚠ **引用の訂正（records-must-match-fact）**: harness docstring と relay が「`scene{}` は cable handle のみ」の根拠に **`newton_skill_env_base.py:542-555`** を挙げるが、**p11 が当該範囲を読んだところ S1B 検証コードであり scene 辞書ではない**。⇒ **主張は正しいが引用が誤り**。正しい接地 = 上表の `newton_route_env.py:725-734`（閉じた key 集合）。**p0 は docstring の引用を差し替えること。**

⭐ **p0 の判断は正しかった** — clip leg を「実装不能」と報告して**偽の pass を作らなかった**。⛔ 埋められない leg は**黙って落とさず、落ちていることを出力に残す**（本 spec の方針として維持）。

### 1.2 ⚠ fidelity caveat（model 記述は条件付きで書く）

⛔ **「UR5e×2 + Robotiq 2F-85」と無条件に書かない。** scene が読むのは **`ROBOTIQ_STRIPPED_XML` = `2f85_koshape.xml`**（`test_newton_clip_routing.py:161`）＝ **コ字 claw の stripped asset**（`<tendon>` 除去）で、かつ **`skip_equality_constraints=True`**（4-bar equality を落として build）。
⇒ 出力の model 記述は **「コ字 stripped asset・equality 無効で build された gripper」**と条件付きで書く。⇒ **H-6d（4-bar が有効化できるか）は、この条件下の問いである**ことを明記。

### 1.3 provenance 出力（pZ 再現突合用・pZ 要求）

ハーネスは出力に **build tree / branch / commit** を記録すること（+ venv path と Newton/mujoco/warp の版）。⇒ pZ が**同じ地点で**再現して突き合わせられる。

⛔ **V-1〜V-4 のいずれかが落ちたら、下流の全数値は無効**（fail-closed）。

---

## 2. H-1 掃引範囲（envelope）— **宣言必須・結果は範囲内でのみ有効**

- envelope は **W-b の実 waypoint から定義する**のが本則。⏸ waypoint 未確定 ⇒ **暫定 box を明示的に宣言**（各 joint の下限・上限・刻み・総件数）し、**出力に必ず添付**する。
- ⛔ **手で選んだ数姿勢を「最大」と呼ばない**（v0.3 の失敗）。掃引は格子または最適化で行う。
- 出力の全数値に **「この envelope 内でのみ有効」**を明記。外側は **未測定**（安全ではない）。
- ⚠ **把持状態の宣言**: cable を掴んだ状態を含むか否か。含まないなら**慣性は過小側**＝ ζ は**楽観側**である旨を出力に明記。

---

## 3. 測る量（H-2 〜 H-6）

### H-2 連成 modal 減衰
- 各 `q` で `M(q)`（連成質量行列）を取り、**二次固有値問題** `det(λ²M + λK_d + K_e) = 0` を解く。
- ⭐ **ζ の抽出式を出力に明記**すること（v0.4 ISSUE 2）。実根対では `ζ = −(λ₁+λ₂)/(2√(λ₁λ₂))`（**1 を超え得る形**）を用い、`ζ = −Reλ/|λ|`（**1 で頭打ち**）と**混用しない**。

#### H-2.1 ⭐ 対象 DOF 集合（**p11 宣言 2026-07-21 20:34 JST**・p0 の照会に応答）

| | 集合 | 本数（**p11 の事前予測** — 実測で照合する） |
|---|---|---|
| ⭐**対象**（bar を立てる） | 両腕の **UR5e revolute 関節** | **12**（`ARM_DOF = 6` × 2・`task_config.py:27`） |
| 除外 A | gripper **driver** 関節（駆動あり） | **4**（`GRIPPER_DRIVER_JOINT_IDX = [6, 10]` × 2・`task_config.py:34`） |
| 除外 B | gripper **passive 4-bar** 関節 | **12**（`GRIPPER_JOINT_RANGE` 8 本 − driver 2 本 = 6・× 2・`task_config.py:35`） |
| 対象外 | cable 関節 | ≥ 40（**本数・base 型は実測して報告**） |

- ⛔ **index でなく joint 名で解決**すること。**実測の「名前 → index」表を出力に添付**する。
- ⚠ **予測と食い違ったら STOP して報告**（腕側 28 = 12 + 16 が崩れる ⇒ **私の前提が誤り**であり本宣言を差し戻す）。⛔ **黙って合わせない。**

#### H-2.2 ⭐ 除外 DOF の扱い（3 本立て・**bar は (i)**）

| | 縮約 | 物理的意味 | 使途 |
|---|---|---|---|
| ⭐**(i)** | **固定** = `M` / `K_e` / `K_d` の **12×12 主小行列** | 除外 DOF が剛に従う | ⭐ **設計 bar はこれで立てる** — 有効慣性 **最大** ⇒ ζ **最小** = **保守側** |
| (ii) | **質量凝縮** `M_red = M_aa − M_ab M_bb⁻¹ M_ba` | 除外 DOF が**力自由** | **下界**（ζ 楽観側）。駆動も拘束も無い passive 4-bar の低周波極限 |
| (iii) | **腕側 28 DOF を実剛性込みで解く** + 各モードの**参加係数** | 真値に最も近い | **(i) が保守である検算**。⛔ `ζ_min` は **腕支配モード**（12 座標の参加が優勢なモード）でのみ読む |

- ⛔ **28 DOF を素で解いて `ζ_min` を読まない。** passive 4-bar は現 build で **equality 無効**（`skip_equality_constraints=True`・§1.2）かつ駆動も無い ⇒ **剛性 0 の自由モード**が構造的に `ζ = 0` を出す。**これは腕の減衰ではない。**
  - ⚠ **この説明自体を検算せよ**: **`K_e` 対角を腕側 28 本ぶん出力**し、passive 12 本が ≈ 0 であることを示す。**違えば私の説明が誤り** ⇒ 報告。
- ⭐ **(i)(ii)(iii) の差を報告する。** 差が小さければ **縮約の選択は本設計で非重要**（そう書く）。大きければ **その差自体が設計上の発見**。
- ⭐⭐ **生の行列を出力に残す**（各サンプル `q` の `M` / `K_e` / `K_d` の腕側 28×28 ブロック + 名前 → index 表）。⇒ **縮約の再裁定に再測定を要さない**（bar を後で動かしても測り直しが要らない）。

#### H-2.3 cable との連成（**前提の検算・必須**）

- 本宣言は「**cable は arm と同じ運動学木に繋がっていない**（連成は接触と equality だけで、`M` には現れない）」を前提にしている。
- ⇒ **`‖M[arm, cable]‖` を出力せよ。p11 の予測 = 0。** ⚠ **非零なら STOP** — 前提が偽であり、本 DOF 宣言を差し戻す。
- ⚠ 把持中の cable 慣性は `M` に入らない ⇒ **ζ は楽観側**。出力に明記（§2 の把持状態宣言と同旨）。

- 出力 = envelope 上の `ζ_modal,min`（**(i)(ii)(iii) それぞれ**）＋ **対角近似値**も参考併記し、差を報告。

### H-3 トルク予算
- **`τ_bias(q, q̇) = qfrc_bias`** を **(q, q̇) の envelope** で掃引し最大を取る（重力 **＋ Coriolis/遠心**）。⛔ 重力のみで組まない（v0.3 の失敗）。
- 加速度余裕 `a_max = (cap − max|τ_bias|) / λ_max(M(q))`。⛔ `M_ii` でなく**連成の最大固有値**。
- ⚠ `cap` は **H-6 の実測値**を使う（宣言値でなく、モデルに実在する値）。

#### H-3.1 ⭐ **per-joint** `τ_bias` を出す（v1.6・2026-07-26）— **全体最大では droop が計算できない**

現行出力は **全体最大 `max|τ_bias|` の 1 値のみ**。⛔ **これでは静的たわみを出せない** — たわみは **関節ごと**に `Δq_i = τ_bias,i / ke_i` で決まり、`ke` は関節で 4 倍違う（size3 = 2000 / size1 = 500 N·m/rad・実測）。⇒ 全体最大をどの `ke` で割るかが決まらない。

- **出力せよ**: envelope 上の **関節ごとの `max|τ_bias,i|`**（12 本）＋ 同時に取った **`Δq_i = τ_bias,i / ke_i`** の表。
- ⇒ これと **H-4 の Jacobian（J-a）** を掛けて初めて **手先のたわみ [mm]** が出る ＝ **2 mm 閾値と比較できる唯一の量**。
- ⚠ **`a_max` は据え置き**（cap が 1e6 = fail-open ゆえ現状は意味を持たない・設計側 §5.5.1 で処理）。

### H-4 把持点 Jacobian
- 参照 frame = **pad を担う body**（cable に実際に触れる body）。
  ⛔⛔ **訂正 v1.7（2026-07-26・p4 の R8 裁定 `442f58678359bf85` による RETURN を受けた spec owner 修正）**: 旧文「**`body_label` から発見すること**」は **現モデルで実行不能**ゆえ撤回。**実測（p11 が h0 report を独立に走査）= `body_label` 70 件中 "pad" は 0 件／`shape_label` 107 件中 16 件** ⇒ **pad は shape のラベルであって body のラベルではない**。⇒ p0 が `wrist_3` で代用せず **ABSENT と報告した判断は正しかった**。
  ⭐ **導出規則（どちらでもよい・採った方を出力に明記すること）**:
  - **(i) SSOT 定数から index 解決** — `task_config.py:37` **`GRIPPER_PAD_BODY_IDX = [9, 13]`**（逐語 "pad-carrying followers"）＋ `:43` `BODIES_PER_ARM = 14` の腕ストライド。⚠ **定数は import して使う**（literal 複製は SSOT が変わると黙って乖離する）。
  - **(ii) label から導く場合** — `shape_label` に "pad" を含む **shape の親 body** を取る（⛔ `body_label` を "pad" で検索しない）。
  ⚠ **実測での裏取り**: body idx **9 = `…/right_spring_link/right_follower`** / **13 = `…/left_spring_link/left_follower`**（p11 実測・p4 の裁定表と一致）。
  ⚠ **現行実装が本規則に適合しているかの判定と、適合させる作業は本 spec では決めない**（p0 の R8 が `arm_control_measurement_harness.py:928` の literal `(9,13)` を自己申告済。**実装修正は未認可** = p4 の court）。
- ⛔ `wrist_3_link` を使わない（`wrist_2`/`wrist_3` の位置列が構造的にゼロ）。
- ⛔ `pinch` site も**単独では不可** — `collapse_fixed_joints` で `wrist_3_link` に剛体固定されており、**8 本の gripper DOF の列がゼロ**になる（v0.4 ISSUE 8）。使う場合は**その旨と誤差の向き**を明記。
- 出力 = per-joint **mm/mrad**（envelope 上の最大）＋ **回転成分の別評価**。

#### H-4.1 ⭐ **3 点で出す**（v1.4・2026-07-21）— 閾値が測る点と、実際に触れる点が違う

SKILL の閾値は **`ee_pos + R(ee_q)·[0,0,+EE_TO_FINGERTIP]`** で測られる（`newton_skill_env_base.py:899-905`）。⚠ その **`EE_TO_FINGERTIP = 0.220` は自身のコメントで Franka/legacy と明記**（`task_config.py:78`「FRANKA panda_hand->fingertip」/ `:84`「220mm, **Franka value; re-derive S6**」/ `:324`「**EE_TO_FINGERTIP above (0.220) is the Franka/legacy**」）。⚠ **同 file には実測の Robotiq/コ 値が別に在る**: `EE_TO_PINCH_CLOSED = 0.2548`（`:320`）/ `EE_TO_PINCH_TIP_CLOSED = 0.2757`（`:321`）。

⇒ ⭐ **同じ「指先」という語が 2 つの点を指し、差は 34.8〜55.7 mm**（2 mm 閾値の **17〜28 倍**）。⇒ **どちらで Jacobian を取るかで関節 bar が変わる**（腕手先までの腕の長さが変わるため、mrad あたりの mm が変わる）。

| # | 参照点 | なぜ要るか |
|---|---|---|
| **J-a** | `ee_pos + 0.220·ẑ_ee`（**閾値が測っている点**） | **PD sizing はこの点で行う**（判定式と同じ面で bar を立てるため） |
| **J-b** | **pad を担う body**（cable に実際に触れる）。⭐**導出は §H-4 の (i) SSOT 定数 index / (ii) `shape_label` の親 body のいずれか**。⛔ **`body_label` を "pad" で検索しない**（実測 0 件・v1.7 訂正） | **接触・把持の物理**はこの点で起きる |
| **J-c** | `EE_TO_PINCH_TIP_CLOSED = 0.2757` 相当の爪先 | J-a と J-b の差を**定量化**して報告するため |

⛔ **1 点だけ出さない。** 3 点の差を出力に併記する。⇒ **どの点で閾値を評価すべきかは本 spec で判断しない**（両方で測れる材料を出すのみ）。⚠ **court の訂正（2026-07-26・p5 correction `fe80839219` §3）**: 旧記載「**p5/Rs の court**」は stale（**Rs が自らの court であることを撤回**）⇒ **(A) success 述語の測定面 = p5**（`/reward-design` + `/pre-check`）／**(B)(C) `GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` 自体 = ⛔UNCONFIRMED / HOLD**（候補 p5 / p17 / p11 / p16・**帰属を捏造しない**）。

### H-5 ⭐ 伝達測定（cable 変位 ÷ EE 変位）— **v0.4 に欠けていた段**
- **なぜ要るか**: task 許容値 `SEAT_LAT_BAR_M`（`route_env_config.py:170` 逐語「**cable centre** geometrically inside the groove」）は **cable 中心**の量。⛔ **arm Jacobian で関節 bar に変換してはならない**（cable は arm の剛体従属ではない）。v0.4 はこれを禁じたまま**解除に要る測定を用意しなかった**ため、bar が原理的に決まらなかった（ISSUE 3）。
- **測る**: 把持中および着座中に、**EE を既知量動かしたとき cable 中心がどれだけ動くか**（phase 別）。
- 出力 = phase ごとの伝達比とばらつき。⇒ これが出て初めて **task 許容値 → 関節 bar** の変換が正当化される。

#### H-5.1 ⭐ 把持状態の ζ（v1.5・pZ の N5 に応答）

H-2 の `ζ = 2.857` は **`M` に cable 慣性を含まない「自由腕」の値**（cable は接触結合ゆえ `M` に現れない）。⇒ **把持中は実効慣性が増え ζ は下がる（楽観側）**。⛔ 自由腕の値を把持 phase に流用できない。

⇒ **H-5 は既に把持/着座 phase まで sim を進めるので、同じ走行の中で次を足す**（追加の build 不要）:
- 把持が成立している状態で、**各腕の 1 関節に小さなステップ目標**を与え（他は保持）、**実現 `q` の行き過ぎ量と減衰**を記録する。⇒ **行き過ぎ量から `ζ_grasped` を読む**（行き過ぎが観測されなければ **ζ ≥ 1**）。
- ⚠ **ステップ幅は把持を壊さない大きさに留める**（把持が外れたら、その走行の値は無効として報告）。
- ⭐ **判定に使う形**: `ζ ∝ M^(−1/2)` より、把持で ζ が 1 を割るには **実効慣性が `2.857² ≈ 8.16 倍`** に増える必要がある。⇒ **出力に「8.16 倍 を超えたか否か」を明記**する（設計側の枝がこれで決まる）。
- 出力 = phase 別 `ζ_grasped`（または「行き過ぎ観測なし ⇒ ζ ≥ 1」）＋ ステップ幅＋把持が保たれたか。

### H-6 機構の実在確認（**設計でなく実測**）
p0 は次を**実測して報告する**（⛔ どれを採るかは決めない）:
| # | 対象 | 問い |
|---|---|---|
| H-6a | **effort cap** | `joint_effort_limit` / `jnt_actfrcrange` の**実値**は何か。⚠ 予測 = 既定 `1e6`（`ur5e.xml` に `actuatorfrcrange` 0 件ゆえ）。**±150/±28 は imported actuator の `forcerange` にのみ在る**。⇒ **B1-strip 後に cap が残るか**を実測 |
| H-6b | **重力補償** | 実際に効かせられる経路はどれか。⚠ 私の v0.4 案（`gravcomp`+`jnt_actgravcomp` の実行時書込）は **到達不能の可能性**が指摘済（custom attribute の values が空・`ngravcomp` に setter 無し・全経路が無言で失敗）。⇒ **効いたことを `qfrc_gravcomp` / `qacc` の変化で示す正対照**が要る。効く経路が無ければ**「無い」と報告**する |
| H-6c | `Control.joint_f` | cap の**内か外か**を実測（予測 = `qfrc_applied` 経由＝**外**）。⇒ 使えば実機より強くなる |
| H-6d | 指の 4-bar | equality/mimic を有効にして **4-bar 連成を持つ gripper** を build できるか（⚠ 現状は **stripped コ字 asset + equality 無効**＝§1.2。「2F-85 を build」と書かない）（⚠ **コ字 asset は human-LOCKED** ⇒ **asset を編集しない**。編集が要ると判明したら **STOP → p4 → Rs**） |

⚠ **prior art（必ず参照）**: 同型の問題（strip が force cap を消す）は **gripper で解決済** — `task_config.py:316-318` 逐語「`GRIPPER_DRIVER_EFFORT_LIMIT_NM = 2.5` … **restores the force cap the tendon strip removed**（D-S5-2）; the **one-frame post-clamp `|qfrc_actuator| <= 2.5`** gate held on rev7/rev8」。⇒ **定数の置き方も受入形（1 frame post-clamp assert）も流用すること。**

---

## 4. 受入条件 — **ハーネスが信頼できるか**（⛔設計が通るか、ではない）

⭐ v0.4 の AC は「設計の合否」を書こうとして自己参照に陥った（`ζ_target` が自分の出力から決まる）。**本 spec の AC は計器の妥当性のみを問う。**

| # | 受入条件 |
|---|---|
| AC-1 | **V-1〜V-4（H-0）が全て PASS**（pZ 判定）。落ちたら全数値 無効 |
| AC-2 | 掃引条件（範囲・刻み・件数）と **envelope 外は未測定**の明記が出力に在る |
| AC-3 | ζ の**抽出式**が明記され、**H-2.1 の「名前 → index」実測表** / **H-2.2 の (i)(ii)(iii) 3 値** / **`K_e` 対角 28 本** / **`‖M[arm, cable]‖`** / **生の 28×28 行列**が出力に在る。⚠ **予測との食い違いは STOP して報告**（黙って合わせない） |
| AC-4 | `a_max` が **`τ_bias(q,q̇)`**（速度依存項込み）と **`λ_max(M)`** から算出されている |
| AC-5 | Jacobian の参照 frame が**明記**され、**gripper DOF の寄与が含まれるか否か**と誤差の向きが述べられている |
| AC-6 | H-5 の伝達比が **phase 別**に出ている（出ない限り task 許容値を関節 bar に変換しない） |
| AC-7 | H-6a〜H-6c が **実測値**として報告されている（宣言値の転記でない）。H-6b は**正対照つき**（効いたことを状態変化で示す） |
| AC-8 | **再現性**: 同一入力で再実行して同一出力（seed / 版 / env を出力に pin） |
| AC-9 | ⭐**負対照**: 意図的に **FK robot-only モデル**を渡すと **H-0 が落ちる**ことを示す。⛔ 判定は **§1.1.0 の参照同一性 I-1〜I-3** と **§1.1.1 の cable leg** に接地していること（DOF 数 / gripper joint の有無 / A-1 VISIBLE は **両モデルで pass = 識別しない**と実測済 ⇒ これらで判定していたら負対照を通らない）。**どの leg が落ちて reject になったかを出力に明記**する（「落ちた」だけでは、識別しない leg で落ちた場合と区別できない） |
| AC-10 | 出力に **build tree / branch / commit + venv + 版**（§1.3）が在り、pZ が同一地点で再現できる |

---

## 5. 境界（誰が何をしないか）

- **p11（私）**: 本 spec と受入条件。⛔ 数値を決めない・実装しない・走らせない。
- **p0**: 実装と測定。⛔ **設計判断をしない**（gain 選定・bar 設定・機構の採否）。効く/効かないの**事実のみ**報告。
- **pZ**: H-0 の model-identity と AC-9 の負対照を**実 build と突き合わせて**検証。⛔ 設計 position を取らない。
- **p4**: landing とまとめ。
- ⛔ **制御方式に触れる要素（重力補償の採用等）の finalization は Rs 承認**（§0#3・p4 が上げ済）。本 spec は**測って報告する**ところまで。

## 6. 非主張 / gate
- gain・bar・`ζ_target`・摂動量を**決めていない**（意図的）。
- H-6 の各機構を**採用していない**（実在するかを測るだけ）。
- 実 run / training / landing の認可でない。⛔ **p0 は本 spec の範囲＝測定のみ**。
- 物理妥当性を判定しない（最終 = Rs 動画 human-GT）。
- ⚠ envelope は暫定（W-b waypoint 未確定）⇒ **確定後に再実行が前提**。

## 7. L 自己申告
**L2 相当**（新規 file 1・spec・コード 0・landing なし）。
⚠ **`/rule-check stage1` による L3 昇格判定が未了**（p4 が Rs へ上げ済）。⇒ **確定するまで本 spec を実装 gate として使わない**。commit = explicit pathspec + `--no-verify`（DDR #35）。
