# `CLAUDE.md:67`/`:72` — p4 cause-side correction **v4**（E1 / E2 / E3）

**訂正者:** RS-TECH-LEAD (`w2:p4`) = **原因側**。**発行:** 2026-07-26 23:38 JST（date-THEN-write）。
**応答する RETURN:** `MSG-PN-P4-CLAUDEMD67-V3-RETURN-20260726-016`（**E1 / E2 / E3 とも受理・争点なし**）。
**⛔ 改変しない:** v1 `c128bd0d17…` ／ v2 `8a9af19912…` ／ v3 `ac79e07543…` ／ `e391b10c3f…` ／ `CLAUDE.md` ／ `prohibited.md` ／ source。
**v3 から引き継ぐ（本書で変えない）:** D1 の category 方針 ／ D2 の arm/finger 分離と `D2-A` の Rs 選択肢 ／ D4 の fail-closed 表 ／ D5 の authority ／ D6 の非主張。

---

## E1. **3 分類**にする（「2 例外＝初期条件クラス」は誤り — 撤回）

⛔ **撤回:** v3 §D3(a) の「以下 **2 例外**は『初期条件クラス』」および §D3(b) が①②を**まとめて**初期条件クラスと呼んだこと。**例外① offline replay は事後可視化であって初期条件ではない。** v3 §D1 の category 表と自己矛盾していた。

⭐ **正しい 3 分類（各々が別の理由で勘定が違う）:**

| # | category | 定義 | runtime kinematic 例外の勘定 | 理由 |
|---|---|---|---|---|
| **1** | **runtime kinematic drive** | solver loop 中に物理を上書きして駆動する機構 | **ここだけが勘定対象。認可例外 = clip-retention pin の 1 件のみ** | 本体 |
| **2** | **episode-boundary initial-state seed** | episode の物理が走る**前**に初期状態を置く | **勘定外** | **DRIVE でない**（`charter_v231.md:474` 逐語「初期化例外・DRIVE でない」「kinematic-drive 例外 0 は維持」） |
| **3** | **solver-loop 外の post-hoc offline replay** | 走行後の可視化（loop 外） | **勘定外** | **そもそも物理 loop の中にいない**（`charter_v231.md:479` 逐語「制御ループ外 replay = joint-state なら typed OFFLINE 可・body-state は不可」） |

⇒ **2 と 3 は「勘定外」である点は同じだが、理由が違うので同じ名前で括らない。**

## E2. **manifest は callsite proof ではない**（(a)(ii) の同一視を撤回）

⛔ **撤回:** v3 §D3(a)(ii) が「**exact callsite** — `RESET_SEED_MANIFEST` に `(file, function)` を登録済」と、**manifest 登録を callsite の証明と同一視**したこと。

**実測（tip `7ab1cc313f3de1e3fd828b3852afd9c33ca89494`）:**

| 事実 | 出典 |
|---|---|
| manifest の鍵は **`(file, function)` まで** — caller を pin しない | `scripts/validations/check_control_method.py:58-61`（entry = `("thread_isaac_lab/envs/newton_grip_env.py", "_seed_robot_joint_row"): {"joint_q": 1, "joint_qd": 1}`） |
| **4 caller が同一関数を通る** | `newton_grip_env.py:451` / `:493` / `:625` / `:904` |

⇒ **現 entry は `:904`（reset）だけでなく、不適合な P0 2 件と cache-restore も静的に免除してしまう。** ⇒ ⛔ **manifest は「どの関数が書いてよいか」を pin するだけで、「どの呼び出し元が書いてよいか」の証明にならない。**

⭐ **条件化（置換案に反映）— 次の**いずれか**を満たすこと:**
- **(α) 許可 callsite 専用関数へ分離** — 許可された呼び出し元だけが使う seed 関数を切り出し、その関数を manifest に登録する（他 caller は別関数を通るため静的に区別できる）／または
- **(β) exact allowed caller/callsite の明示 ＋ runtime の caller/phase 強制** — 呼び出し元と phase を実行時に検査して、許可 callsite 以外では失敗させる

## E3. **指の runtime close と 指列の初期 seed を別 clause に**（category 混在を撤回）

⛔ **撤回:** v3 §D3(b) が「指の kinematic close」の括弧の中に「**指列の初期 seed も不可**」を入れたこと。**category 1（runtime）の項に category 2（初期条件）を混ぜていた** — 私が D1 で立てた single-valued 規律を、自分の案が破っていた。

⭐ **分離:**
- **category 1:** 指の **kinematic close**（runtime に物理を上書きして閉じる）= **不許可（不変）**
- **category 2:** 指列の **初期条件 seed** = **本案では例外の domain に含めない ⇒ 不可**（⚠ **未裁定ゆえの不可**であって、category 1 の不変禁止とは理由が違う。可否は v3 §D2-A の Rs 選択）

## E4. 置換案 **v4**（full `:67` ＋ full `:72`・不可分・**未承認**）

### (a) `:67` 全文置換案

> - **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。⚠ 本項の例外は `:72` の *runtime kinematic 例外*（= clip-retention pin の 1 件のみ）とは**別の分類**であり、その勘定を変えない（`charter_v231.md:474`/`:479`）。例外①【**solver-loop 外の post-hoc offline replay**】: 走行後の可視化は **joint-state に限り**許可（body-state は不可）。例外②【**episode-boundary initial-state seed**】: 次を**すべて**満たす場合に限る: (i) **domain = 腕関節列のみ**（⛔ **指（gripper）列は含まない**）(ii) **callsite が特定できること** — 次のいずれか: **(α)** 許可 callsite 専用の seed 関数へ分離し、その関数を guard `RESET_SEED_MANIFEST` に `(file, function)` と期待 count で登録する ／ **(β)** 許可 caller/callsite を明示し、**runtime に caller/phase を検査して他 callsite では失敗させる**。⚠ **`(file, function)` の登録だけでは callsite の証明にならない**（同一関数を複数 caller が通るため）(iii) **その episode の最初の物理 step より前**(iv) **境界あたり 1 回**(v) **loop へ持ち越さない**(vi) **joint-state のみ**（body-state 書込ゼロ・body は `mj_forward`/`eval_fk` で関節から従属）(vii) **同一 turn でサーボ目標を同姿勢へ同期**(viii) **(iii)(iv) を runtime assert で強制**（comment / docstring は proof でない）。⛔ **task / route の開始姿勢をこの例外で置くことは不可** — 開始姿勢は PD 実移動で到達する。⛔ **episode 途中の homing / recovery は actuator のみ。** ケーブルの seed は CABLE-SEED として現行のまま。**

### (b) `:72` 全文置換案

> - 〔上記のうち *具体 API 名*（`DifferentialIKController`/`write_joint_*`/`set_joint_*`）は PhysX 実装形。**不変前提「IK 制御のみ・kinematic トリック（物理無視の強制配置＝アーム関節角の直接書き込み等）禁止・制御方式変更は Rs 承認」は全 substrate 共通（§0#3/#5、`validate.sh` Layer 8 が機械検証）**。**runtime kinematic の認可例外は clip-retention pin の 1 件のみ** ＝ **clip 側がケーブルを保持する機構**（⚠ gripper の把持ではない。工程表の「クランプ」「ケーブル固定」は `RL-Routing-Design.md:1312` のとおり **gripper の把持動作**を指す語なので、本例外の読みに流用しない）。**⭐ 3 分類（`charter_v231.md:474`/`:479`）: ①runtime kinematic drive（本行の勘定対象）／②episode-boundary initial-state seed（DRIVE でないため勘定外）／③solver-loop 外の post-hoc offline replay（物理 loop の外ゆえ勘定外）。②③ は `:67` が規律し、本行の「1 件のみ」を変えない。** ⛔**不許可（不変）= ①腕関節角の直接書込〔**唯一の除外 = `:67` 例外② の条件 (i)-(viii) をすべて満たす初期条件 seed。それ以外の腕関節角書込は一切不可**〕/ ②**指の kinematic close**（runtime に物理を上書きして閉じる）/ ③`update_kinematic_bodies`（FK→physics の body 複写）/ ④weld・cable-finger attachment。⭐**別項（category ② に属し、理由が異なる）: 指列の初期条件 seed は本規則では例外に含めない ⇒ 不可（未裁定）。**」 根拠 = RS71 §0#5（本節は 07-19 以降も本例外を保持していた）＋ Rs 裁定 2026-07-21 逐語「ただし、クリップのケーブル固定だけは kinematic を使用する」が 07-19 の「完全削除」directive を上書き（custody = `STEP43_C69_EVIDENCE_READBACK_OPSSUP_20260721.md:23`。⚠**Rs 発話は 01:3x と 02:0x の 2 回あり、両 receipt の全体は `RS_PIN_UTTERANCE_CUSTODY_RSTECHLEAD_20260721.md` @ c73 `23c320850e`（branch `probe/pd1-arm-pd`）**）。Newton の対応 API・制御制約は `thread-vault/06-Knowledge/LL-Newton.md` 参照〕

⚠ **(a)(b) は同時採否。** ⛔ **未承認。**

## E5. 承認しても即 OPEN にならないもの（v3 §D4 ＋ E2 由来を追記）

| 項目 | 状態 | 理由 |
|---|---|---|
| 現行 28-wide 実装 | **CLOSED** | finger 列を同時に書く（v3 §D2） |
| P0 2 件（`:451`/`:493`） | **CLOSED** | 物理実行後・task 固有姿勢（v2 §C2） |
| cache-restore（`:625`） | **HOLD** | reset とは別 leg・未判定 |
| temporal enforcement | **UNVERIFIED** | (viii) の runtime assert が見当たらない（v2 §C3） |
| **callsite enforcement** | **UNVERIFIED / 未実装** | manifest は `(file, function)` 止まり。(α)(β) いずれも未実装（**E2 新規**） |

## E6. 非主張

⛔ gate flip なし ／ p11 relay なし ／ H-3.1 GO なし ／ H-4 全体 HOLD ／ B-C owner HOLD ／ source・`[CHANGE]`・実装・experiment・RUN・verify・status は **CLOSED**（V10 blocker）／ **MEMORY 不触** ／ `prohibited.md` 現状固定 ／ 他 pane の record を代理編集しない ／ 物理妥当性は判定しない ／ **finger の可否も (α)(β) の選択も私は代入しない**（実装方式は実装 court）。

---
**p4 cause-side correction v4 = 2026-07-26 23:38 JST / RS-TECH-LEAD (`w2:p4`)**
