# `CLAUDE.md:67`/`:72` — p4 cause-side correction **v3**（D1 / D2）

**訂正者:** RS-TECH-LEAD (`w2:p4`) = **原因側**。**発行:** 2026-07-26 23:33:27 JST（date-THEN-write）。
**応答する RETURN:** `MSG-PN-P4-CLAUDEMD67-V2-RETURN-20260726-015`（**D1 / D2 とも受理・争点なし**）。
**⛔ 改変しない:** v1 `c128bd0d17…` ／ v2 `8a9af19912…` ／ `e391b10c3f…` ／ `CLAUDE.md` ／ `.claude/rules/prohibited.md` ／ source。
**接地:** `:72` 逐語 = `e391b10c3f85723e88198be90413b93a15f48f4e:CLAUDE.md` の `:72`（1504 bytes）／実装 tip = `7ab1cc313f3de1e3fd828b3852afd9c33ca89494`

---

## D1. category を single-valued にする（部分 clause 置換では不可 — 撤回）

⛔ **撤回:** v2 §C5(b) が `:72` の**一部 clause だけ**を置換する案だったこと。`:72` 前段の「**kinematic の認可例外は clip-retention pin の 1 件のみ**」と併存すると、**「唯一例外」が 2 つある**状態になり曖昧。

⭐ **採る category（設計文に接地・single-valued）= 「seed は kinematic 例外に数えない」:**

**`charter_v231.md:474` 逐語:** 「reset-init 例外 = episode boundary の reset 直後 1 回に限る joint-state seed + `mj_forward`**（初期化例外・DRIVE でない）**… pN が旧「reset も actuator・例外 0」の広い表現を本 1-回-init について撤回・**kinematic-drive 例外 0 は維持**。」

⇒ **2 つの別カテゴリ:**

| category | 内容 | 例外の数 |
|---|---|---|
| **kinematic 例外**（＝ 走行中に物理を上書きする機構） | clip-retention pin | **1 件のみ**（不変・**変更しない**） |
| **初期条件クラス**（＝ episode の物理が走る**前**に初期状態を置く行為） | `:67` 例外② の seed | kinematic 例外では**ない**（DRIVE でない）ゆえ上の勘定に入らない |

⇒ **「clip-only」は真のまま。** ⇒ **両行に同じ category を明記する**（片方だけでは曖昧が残る）。

## D2. arm と finger を明示分離 — **finger は未裁定ゆえ例外から除外**

**実測（`task_config.py` ＋ 実装 tip）:**

| 事実 | 出典 |
|---|---|
| `ROBOT_NUM_JOINTS = ARM_DOF + GRIPPER_DOF` = 14 ⇒ **1 腕の行に gripper DOF が入る** | `task_config.py:29` |
| `GRIPPER_DRIVER_JOINT_IDX = [6, 10]`（腕内 index） | `task_config.py:34` |
| P0 は row の finger 列を明示的に詰める | `newton_grip_env.py:441-444`（`jq_solved[GRIPPER_DRIVER_JOINT_IDX[…]] = FINGER_OPEN_POS` ×4） |
| seed の書込幅 = `for k in range(2 * JOINTS_PER_ARM)` ⇒ **arm と finger を同時に書く** | `newton_grip_env.py:867` |

⛔ **撤回:** v2 §C5(a) が許可 domain を列挙せず一般形で書いたこと。**そのまま承認されると finger を黙って許可し、v2 §C4 の finger=HOLD と矛盾する。**

⭐ **本案の立場:** **finger は未裁定 ⇒ 例外から除外。** ⇒ **現行の 28-wide 実装（arm と finger を 1 回で書く `_seed_robot_joint_row`）は CLOSED**（arm だけを許可しても、実装が finger も書くため conformant にならない）。
⛔ **finger を許可候補にするか否かは Rs の別選択肢**（下記 §D2-A）。**私も pN も代入しない。**

### D2-A. finger の扱い（**Rs 選択・私は選ばない**）

- **選択肢 1: finger を例外に含めない** ⇒ 実装側は seed を **arm 列のみ**に絞る改修が要る（28-wide → arm 列限定）。finger の初期姿勢は servo で置く。
- **選択肢 2: finger も例外に含める** ⇒ `:67` の許可 domain に finger を明記し、現行 28-wide 実装がそのまま候補になる。⚠ 根拠は `charter:474` の「robot/finger」表現のみで、**finger 単独の裁定文は薄い**（v2 §C4）。

⚠ **どちらを採っても、v2 §C3 の temporal enforcement UNVERIFIED は別に残る。**

## D3. 置換案（**full `:67` ＋ full `:72` の不可分 2 面**・未承認）

### (a) `:67` 全文置換案

> - **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。⚠ 以下 2 例外は「初期条件クラス」であり、`:72` の *kinematic 例外*（= clip-retention pin の 1 件のみ）とは**別カテゴリ**（DRIVE でない・`charter_v231.md:474`）。例外①: 制御ループ外の事後可視化（オフライン replay）は **joint-state に限り**許可（body-state は不可）。例外②: **episode 境界の初期条件 seed** — 次を**すべて**満たす場合に限る: (i) **domain = 腕関節列のみ**（⛔ **指（gripper）列は本例外に含まない**）(ii) **exact callsite** — guard `RESET_SEED_MANIFEST` に `(file, function)` と期待 count を登録済（**登録なき seed は不可**）(iii) **その episode の最初の物理 step より前**(iv) **境界あたり 1 回**(v) **loop へ持ち越さない**(vi) **joint-state のみ**（body-state 書込ゼロ・body は `mj_forward`/`eval_fk` で関節から従属）(vii) **同一 turn でサーボ目標を同姿勢へ同期**(viii) **(iii)(iv) を runtime assert で強制**（comment / docstring は proof でない）。⛔ **task / route の開始姿勢をこの例外で置くことは不可** — 開始姿勢は PD 実移動で到達する。⛔ **episode 途中の homing / recovery は actuator のみ。** ケーブルの seed は CABLE-SEED として現行のまま。**

### (b) `:72` 全文置換案（**追加は 1 文＋列挙の括弧のみ・他は現行のまま**）

> - 〔上記のうち *具体 API 名*（`DifferentialIKController`/`write_joint_*`/`set_joint_*`）は PhysX 実装形。**不変前提「IK 制御のみ・kinematic トリック（物理無視の強制配置＝アーム関節角の直接書き込み等）禁止・制御方式変更は Rs 承認」は全 substrate 共通（§0#3/#5、`validate.sh` Layer 8 が機械検証）**。**kinematic の認可例外は clip-retention pin の 1 件のみ** ＝ **clip 側がケーブルを保持する機構**（⚠ gripper の把持ではない。工程表の「クランプ」「ケーブル固定」は `RL-Routing-Design.md:1312` のとおり **gripper の把持動作**を指す語なので、本例外の読みに流用しない）。**⭐ category（`charter_v231.md:474`）: `:67` 例外①② の「初期条件クラス」は DRIVE でないため *kinematic 例外に数えない* — 本行の「1 件のみ」は kinematic 例外の勘定であり、初期条件クラスによって変わらない。** ⛔**不許可（不変）= 腕関節角の直接書込〔**唯一の除外 = `:67` 例外② の条件 (i)-(viii) をすべて満たす初期条件 seed。それ以外の腕関節角書込は一切不可**〕/ 指の kinematic close**（⭐ **指列の初期 seed も未裁定ゆえ本項に含む = 不可**）**/ `update_kinematic_bodies`（FK→physics の body 複写）/ weld・cable-finger attachment。** 根拠 = RS71 §0#5（本節は 07-19 以降も本例外を保持していた）＋ Rs 裁定 2026-07-21 逐語「ただし、クリップのケーブル固定だけは kinematic を使用する」が 07-19 の「完全削除」directive を上書き（custody = `STEP43_C69_EVIDENCE_READBACK_OPSSUP_20260721.md:23`。⚠**Rs 発話は 01:3x と 02:0x の 2 回あり、両 receipt の全体は `RS_PIN_UTTERANCE_CUSTODY_RSTECHLEAD_20260721.md` @ c73 `23c320850e`（branch `probe/pd1-arm-pd`）**）。Newton の対応 API・制御制約は `thread-vault/06-Knowledge/LL-Newton.md` 参照〕

⚠ **(a)(b) は同時採否**（片方だけ landing すると矛盾が残る）。⛔ **未承認。**

## D4. 承認しても即 OPEN にならないもの（fail-closed の維持）

| 項目 | 状態 | 理由 |
|---|---|---|
| 現行 28-wide 実装（`_seed_robot_joint_row`） | **CLOSED** | finger 列を同時に書くため (a)(i) に非適合（§D2） |
| P0 2 件（`:451` / `:493`） | **CLOSED** | 物理実行後・task 固有姿勢（v2 §C2） |
| cache-restore（`:625`） | **HOLD** | reset とは別 leg・未判定 |
| temporal enforcement | **UNVERIFIED** | (a)(viii) の runtime assert が見当たらない（v2 §C3） |

## D5. authority（v2 §C6 を維持）

**再判断まで `e391b10c3f85723e88198be90413b93a15f48f4e` が banked governing text。** 承認（2026-07-26 22:50:51 逐語「承認」）は存在し、**私は失効させられない**。誤っていたのは承認入力の material basis。**§D3 は未承認。** ⛔ p5 / pN の旧裁定が自動で Rs 承認を上書きするとは扱わない。

## D6. 非主張

⛔ gate flip なし ／ p11 relay なし ／ H-3.1 GO なし ／ H-4 全体 HOLD ／ B-C owner HOLD ／ source・`[CHANGE]`・実装・experiment・RUN・verify・status は **CLOSED**（V10 blocker）／ **MEMORY 不触** ／ `prohibited.md` 現状固定 ／ 他 pane の record を代理編集しない ／ 物理妥当性は判定しない ／ **finger の可否を私は選ばない**。

---
**p4 cause-side correction v3 = 2026-07-26 23:33:27 JST / RS-TECH-LEAD (`w2:p4`)**
