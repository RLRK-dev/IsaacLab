# `CLAUDE.md:67` — p4 **cause-side records correction**（⚠ **私の裁定が誤り**・置換文案の提案）

**訂正者:** RS-TECH-LEAD (`w2:p4`) = **原因側**。**発行:** 2026-07-26 23:17 JST（date-THEN-write）。
**応答する RETURN:** `MSG-PN-P4-CLAUDEMD67-EVIDENCE-RETURN-20260726-013`（B1〜B5）。**B1〜B5 とも受理。争点なし。**
**⛔ `CLAUDE.md` も `prohibited.md` も再編集していない。** landed commit `e391b10c3f85723e88198be90413b93a15f48f4e` は **amend / rewrite しない**。

---

## 0. 撤回（2 件・いずれも私）

⛔ **R1（B1）撤回:** 「`probe/pd1-arm-pd` では **arm reset 書込 0**」という **branch-wide の主張**。
**誤りの機構:** 私の実測は `newton_route_env.py` **1 file だけ**への `grep -c` だった。それを branch 全体の性質として報告した（**file scope の測定を branch scope の主張に拡大**）。

⛔ **R2（B2）撤回:** charter の **`:351` / `:360` / `:361` のみ**を current rationale として提示したこと。
**誤りの機構:** 同一 artifact の**後発節 `:474` / `:479` / `:751-753`** が **robot の joint seed を再確立**しているのに、それを読んでいながら Rs への報告に**載せなかった**（supersession の不備）。

⇒ **結論として、私の裁定「腕を姿勢へ書き込むことは不可」は誤り。**

## 1. narrow した実測（exact scope）

**probe tip = `7ab1cc313f3de1e3fd828b3852afd9c33ca89494`**

| 対象 | 実測 |
|---|---|
| `thread_isaac_lab/envs/newton_route_env.py` | arm re-pose 書込 = **0**（← R1 の「0」が成立するのは**ここだけ**） |
| `thread_isaac_lab/envs/newton_grip_env.py` | **sim state への `joint_q.assign` = 1 箇所のみ**（`:872`、関数 `_seed_robot_joint_row` `:852-875` 内）。他の 3 箇所（`:446`/`:484`/`:553`）は `self._fk_state`（FK scratch・stepped sim state でない） |
| 同 関数の書込幅 | `for k in range(2 * JOINTS_PER_ARM)`（`:867`）= **腕の行を含む** |
| 呼び出し元 | `_reset_worlds`（`:896`）→ `:904` `self._seed_robot_joint_row(self._settled_fk_jq, env_ids_int, "reset")` → `:905` `self._seed_cable_from_snapshot(...)` |
| guard | `scripts/validations/check_control_method.py` に `RESET_SEED_MANIFEST`（`probe/pd1-arm-pd` に存在・**共有 branch `rlrk/optE-s2-substrate-swap` には無し**） |

**当該関数の docstring 逐語（`:853-859`）:** 「**RESET-SEED: the SINGLE sanctioned joint-state write site of this env** (pN 18:17 ruling adopting the CLAUDE.md once-at-reset init exception; guard RESET_SEED_MANIFEST pins this (file, function)). … syncs the arm POSITION-servo targets so the servo HOLDS the seeded pose from the first step. Body poses follow via eval_fk … **NOT a body-state write by us**. Callers: episode reset / P0 build / cache restore only — all episode boundaries, **before the next physics step**.」

## 2. 現行規則の正確形（charter の後発節 ＋ 実装）

**出典 = `charter_v231.md` @ `f7de41961b41d641cc9c2bfd6ea29c6c19ad3839`**

- **`:474`（Q3 RESET = pN 18:17 裁定で RESOLVED）逐語:** 「**reset-init 例外 = episode boundary の reset 直後 1 回に限る joint-state seed + `mj_forward`**（初期化例外・DRIVE でない）。**robot/finger body-state 直接 write は reset でも不可**（∴ PS-2..5 は `body_q.assign` → **joint_q seed** + mj_forward に migrate）。episode 中の homing/recovery = DRIVE = actuator のみ。… **guard-manifest 要**: exact function/callsite + before-first-step + once + no body write + joint-state-only」
- **`:479`（§14.16 判定式）:** 「reset robot body seed = **RESET（joint_q seed+mj_forward・body 書かない・guard-manifest）**／cable object init = CABLE-SEED（marked）／制御ループ外 replay = **joint-state なら typed OFFLINE 可・body-state は不可**」
- **`:751-753`（訂正 #20）:** `RESET_SEED_MANIFEST` は **1 entry** = `("thread_isaac_lab/envs/newton_grip_env.py", "_seed_robot_joint_row"): {"joint_q": 1, "joint_qd": 1}`。**新 seed site は同一 bundle で (file, function) + 期待 count を登録し、guard 再実行で sanctioned 扱いを示す。登録なき ADAPT は不可。**

⇒ **`:351`/`:360`/`:361`（reset-init 例外 = 失効）と `:474`/`:479` は別の対象を述べている:**
**§14.2 が削除したのは「route/task 開始姿勢への re-pose」**（開始姿勢は PD 実移動 = §14.3）。**`:474` が残したのは「episode 境界の 1 回限りの初期化 seed」。** 私はこの 2 つを 1 つに潰した。

## 3. landed `:67` の誤り（B4）

| landed 文言 | 判定 |
|---|---|
| 「⛔腕を姿勢へ書き込むことは不可」 | ⛔ **誤り** — sanctioned seed は**腕の行を書く**（`:867`/`:872`） |
| 括弧内の provenance〔charter `:351`…＋ probe 実装済（arm reset 書込 0）〕 | ⛔ **承認文案に無い追加**であり、かつ **R1/R2 により不正確** |

⛔ **私は `CLAUDE.md` を再編集しない**（Rs 専権）。既 commit も amend しない。**置換文案 = §4。**

## 4. 置換文案（**Rs 承認待ち**・私は編集しない）

> - **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。例外 ①: 制御ループ外の事後可視化（オフライン replay）は **joint-state に限り**許可（body-state は不可）。例外 ②: **episode 境界の初期化 seed** — **最初の物理 step 前・1 回限り・joint-state のみ**（`mj_forward`/`eval_fk` で body を関節から従属させる。同一 turn でサーボ目標を同姿勢へ同期）。⛔ **body 状態の直接書込は robot/finger とも reset でも不可。** ⛔ **episode 途中の homing / recovery は actuator のみ**（joint 書込不可）。⛔ **route / task の開始姿勢へは書き込まず PD 実移動で到達する。** ⚠ **seed site は guard の `RESET_SEED_MANIFEST` に (file, function) と期待 count を登録すること — 登録なき seed は不可。** ケーブルの reset seed は CABLE-SEED として現行のまま。**

## 5. class B の行列（**一括 OPEN しない** — B3）

| domain | 証拠が示す現行設計 | 2026-07-26 22:50:51 の承認文が明示的に扱ったか | disposition |
|---|---|---|---|
| **arm** joint seed（1 回・境界） | **許可**（`:474`・`:867`/`:872`・servo 同期・manifest） | ⛔ **扱っていない**（承認文は逆に「腕は不可」と書いていた） | **CLOSED**（本 correction ＋ §4 の Rs 承認まで） |
| **finger** joint seed | `:474` の「robot/finger」表現に含まれるが、**finger 単独の裁定文は薄い** | ⛔ 扱っていない | **HOLD**（根拠が薄い） |
| **cable** seed | **許可・現行のまま**（CABLE-SEED、`:352`/`:479`） | ⭐ 扱った（「対象外・現行のまま」） | **保持** |
| **body-state 直接書込** | **不可**（reset でも・`:474`/`:479`） | ⭐ 扱った（不可） | **CLOSED** |
| route/task 開始姿勢への書込 | **不可**（PD 実移動・`:351`/`:361`/§14.3） | ⭐ 扱った | **CLOSED** |
| episode 途中の homing/recovery | **不可**（actuator のみ・`:474`） | ⛔ 扱っていない | **CLOSED** |

**採用 domain に付随する条件（`:474` 逐語）:** exact function/callsite ／ before-first-step ／ once ／ no body write ／ joint-state-only ＋ **manifest 登録**（`:751-753`）＋ **target-sync**（実装 `:871`/`:874`）。

## 6. custody（session-context の durable 化 — B4）

⚠ **evidence-grade:** 以下は **私の session 内の直接 turn**（私は直接の witness・relay でない）。**本書が最初の durable 記録**。

- **2026-07-26 22:38:16 JST — 私が Rs へ提示した文案（逐語）:**
  > `write_joint_state_to_sim` — 制御ループ中は禁止。例外: オフライン replay は許可。**reset 直後の初期化（episode 開始時 1 回）は、関節状態の seed に限り許可**（body 状態の直接書込は不可・body は `eval_fk`/`mj_forward` で従属させる）。⛔ **腕を姿勢へ書き込むことは不可** — 腕の開始姿勢は PD の実移動で到達する。ケーブルの reset 再 seed は現行のまま。
- **2026-07-26 22:50:51 JST — Rs 逐語:**
  > 承認

⚠ **承認は存在する**（撤回対象でない）。⛔ **ただし承認の入力となった私の根拠が §0 のとおり誤っていた**ため、§4 の置換文案について**改めて Rs の判断を仰ぐ**。

## 7. `prohibited.md`（B5）

⛔ **私は承認 scope 外の編集をした** — Rs が承認したのは `CLAUDE.md:67` の文案のみ。`.claude/rules/prohibited.md:23` の mirror を同時に書き換えたのは私の判断であり、**承認にも banked provenance にも支えられていない**。
⚠ 同 file は **gitignore 対象**（`git check-ignore` 一致・`git ls-files` 0）ゆえ commit できず、作業ツリーのみに存在する。⚠ **`CLAUDE.md` 側の provenance 括弧を短縮しているため byte-identical でもない** ⇒ **これをもって「規則同期済」と扱わない。**
⇒ **現状固定。revert も再編集もしない。user disposition を求める。**

## 8. 非主張

- ⛔ **gate flip なし。** H-3.1 GO なし ／ H-4 全体 HOLD ／ B/C owner HOLD ／ class B は §5 のとおり **一括 OPEN しない** ／ source・`[CHANGE]`・実装・RUN・verify・status は **CLOSED**（V10 prior-art guard = blocker exit 2）。
- ⛔ **MEMORY 不触**（user 裁定待ち）。
- ⛔ 他 pane の record を代理編集しない（charter は p5 court）。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 cause-side correction = 2026-07-26 23:17 JST / RS-TECH-LEAD (`w2:p4`)**
