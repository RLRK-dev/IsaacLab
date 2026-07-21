# 腕制御 測定ハーネス 仕様 v1.1 — p0 実装 / pZ 検証（p11 ARM-CONTROL-DESIGN, 2026-07-21）

**Author:** ARM-CONTROL-DESIGN (`w2:p11`)。**Status:** SPEC **v1.1** — **proposal**（landing = p4 経由）。v1.0 = `054a54bbb6` ⇒ **pZ の model-identity 入力を折込**（§1 witness の精緻化 / fidelity caveat / provenance 出力）。
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
| V-1 | 測定対象が **env が実際に solver へ渡した Model** であること（**別 build でも FK モデルでもない**） |
| V-2 | 上記記録が、**pZ が独立に構成した env** の同一項目と一致すること |
| V-3 | ⭐**scene 固有物**が在ること（下記 §1.1 の witness）— **robot-only モデルを掴んでいないことの識別子**（v0.4 の失敗を狙って弾く leg） |
| V-4 | 掃引に使う `q` が **joint 名で解決**されている（index 直書きでない） |

### 1.1 ⭐ witness は **scene 固有物**に置く（pZ 入力・2026-07-21）

⛔⛔ **DOF 数・gripper joint の有無では FK robot-only と as-built を分けられない。**
実測: `build_fk_and_init(left_finger_pos, right_finger_pos, …)`（`newton_skill_env_base.py:1223`）は **指の位置を引数に取る** ⇒ **FK モデルも gripper 系 joint を持つ**。⇒ 「gripper が在る」類の述語は **v0.4 型の誤一致**を起こす。

**採る witness（scene にしか無いもの・p11 が実測確認）**:
| witness | 実体 |
|---|---|
| **cable** | `add_revolute_cable` が**両腕の後に**発行する REVOLUTE 鎖（`newton_skill_env_base.py:1587`。逐語「Cable: rigid-link REVOLUTE chain **AFTER both arms**」）⇒ **body 数 0 でないこと** |
| **A-1 VISIBLE pass の痕跡** | `:1574-1578` 逐語「clear COLLIDE on **non-pad arm shapes** … **KEEP COLLIDE on the gripper PAD geoms**」⇒ **非 pad の腕 shape が COLLIDE を落としており、pad は保持している**こと |
| **clip** | scene 側の clip 実体が在ること |
| **world_count** | 宣言値と一致すること |

⇒ **これらは FK/IK モデルには存在しない**ので、識別する。⛔ 「DOF 数一致」「gripper joint 在り」を witness に使わない。

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
- ⭐ **対象 DOF 集合を明記**すること。腕のみを見るなら、**除外した DOF の扱い**（固定 → Schur 補元 / 実剛性込み）を宣言。⛔ 28 DOF 全体を素で解くと gripper 側の剛性ほぼ 0 で `ζ_min = 0` が構造的に出る。
- 出力 = envelope 上の `ζ_modal,min`（**対角近似値も参考併記**し、両者の差を報告）。

### H-3 トルク予算
- **`τ_bias(q, q̇) = qfrc_bias`** を **(q, q̇) の envelope** で掃引し最大を取る（重力 **＋ Coriolis/遠心**）。⛔ 重力のみで組まない（v0.3 の失敗）。
- 加速度余裕 `a_max = (cap − max|τ_bias|) / λ_max(M(q))`。⛔ `M_ii` でなく**連成の最大固有値**。
- ⚠ `cap` は **H-6 の実測値**を使う（宣言値でなく、モデルに実在する値）。

### H-4 把持点 Jacobian
- 参照 frame = **pad body**（cable に実際に触れる body。`body_label` から発見すること）。
- ⛔ `wrist_3_link` を使わない（`wrist_2`/`wrist_3` の位置列が構造的にゼロ）。
- ⛔ `pinch` site も**単独では不可** — `collapse_fixed_joints` で `wrist_3_link` に剛体固定されており、**8 本の gripper DOF の列がゼロ**になる（v0.4 ISSUE 8）。使う場合は**その旨と誤差の向き**を明記。
- 出力 = per-joint **mm/mrad**（envelope 上の最大）＋ **回転成分の別評価**。

### H-5 ⭐ 伝達測定（cable 変位 ÷ EE 変位）— **v0.4 に欠けていた段**
- **なぜ要るか**: task 許容値 `SEAT_LAT_BAR_M`（`route_env_config.py:170` 逐語「**cable centre** geometrically inside the groove」）は **cable 中心**の量。⛔ **arm Jacobian で関節 bar に変換してはならない**（cable は arm の剛体従属ではない）。v0.4 はこれを禁じたまま**解除に要る測定を用意しなかった**ため、bar が原理的に決まらなかった（ISSUE 3）。
- **測る**: 把持中および着座中に、**EE を既知量動かしたとき cable 中心がどれだけ動くか**（phase 別）。
- 出力 = phase ごとの伝達比とばらつき。⇒ これが出て初めて **task 許容値 → 関節 bar** の変換が正当化される。

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
| AC-3 | ζ の**抽出式**と**対象 DOF 集合・除外 DOF の扱い**が出力に明記されている |
| AC-4 | `a_max` が **`τ_bias(q,q̇)`**（速度依存項込み）と **`λ_max(M)`** から算出されている |
| AC-5 | Jacobian の参照 frame が**明記**され、**gripper DOF の寄与が含まれるか否か**と誤差の向きが述べられている |
| AC-6 | H-5 の伝達比が **phase 別**に出ている（出ない限り task 許容値を関節 bar に変換しない） |
| AC-7 | H-6a〜H-6c が **実測値**として報告されている（宣言値の転記でない）。H-6b は**正対照つき**（効いたことを状態変化で示す） |
| AC-8 | **再現性**: 同一入力で再実行して同一出力（seed / 版 / env を出力に pin） |
| AC-9 | ⭐**負対照**: 意図的に **FK robot-only モデル**を渡すと **H-0 が落ちる**ことを示す。⛔ 判定は **§1.1 の scene 固有 witness** に接地していること（DOF 数・gripper joint の有無で判定していたら**この負対照を通らない**）。これが示せないハーネスは v0.4 と同じ穴を持つ |
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
