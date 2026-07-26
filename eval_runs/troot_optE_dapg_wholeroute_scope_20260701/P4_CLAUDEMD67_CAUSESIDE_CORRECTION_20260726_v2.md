# `CLAUDE.md:67`/`:72` — p4 cause-side correction **v2**（C1〜C6）

**訂正者:** RS-TECH-LEAD (`w2:p4`) = **原因側**。**発行:** 2026-07-26 23:29 JST（date-THEN-write）。
**応答する RETURN:** `MSG-PN-P4-CLAUDEMD67-CORRECTION-RETURN-20260726-014`（**C1〜C6 全件受理・争点なし**）。
**⛔ 改変しないもの:** v1 `c128bd0d1716006b80e270d36350b7f7b9a76e30` ／ `e391b10c3f85723e88198be90413b93a15f48f4e` ／ `CLAUDE.md` ／ `.claude/rules/prohibited.md` ／ source。**amend / rewrite なし。**
**接地 commit（以下すべてこの tip で実測）= `7ab1cc313f3de1e3fd828b3852afd9c33ca89494`（`probe/pd1-arm-pd`）**

---

## C1. `_seed_robot_joint_row` の **全 callsite = 4**（v1 が reset 1 件に narrow したのは不完全 — 撤回）

⛔ **撤回:** v1 §1 が caller を `_reset_worlds` の 1 件だけ挙げたこと。

| # | callsite | 関数 | label | 渡す姿勢 |
|---|---|---|---|---|
| 1 | `newton_grip_env.py:451` | `_build_p0_clamp` | `"p0-clamp"` | `jq_solved` = **task 固有 IK 解**（`:437-439`・cable 高さへ両腕） |
| 2 | `newton_grip_env.py:493` | `_build_p0_unclamp` | `"p0-unclamp"` | `jq_target` = **task 固有姿勢** |
| 3 | `newton_grip_env.py:625` | `_load_and_restore_cache` | `"cache-restore"` | `self._settled_fk_jq`（cache 済 FK row） |
| 4 | `newton_grip_env.py:904` | `_reset_worlds` | `"reset"` | `self._settled_fk_jq` |

## C2. **4 件を 1 class に畳まない** — 少なくとも P0 2 件は `:474` の述語を満たさない

**実測（`_build_p0_clamp`）:**
- `:431-432` **`for _ in range(SETTLE_STEPS): self._physics_step_all()`** ⇒ **seed の前に物理が既に走っている**
- `:437-439` `target_l/r = wp.vec3(GRASP_X, CLIP1_Y ∓ 0.005, GRIP_Z)` → `solve_ik_single(...)` ⇒ **task 固有姿勢**
- `:451` その姿勢を seed → `:453-454` 再び `SETTLE_STEPS`

⇒ **`before-first-physics-step` は成り立たない**（物理が先に走っている）。⇒ **`charter:474` の「episode boundary の reset 直後 1 回」と同一視できない。**
⚠ さらに **task 固有姿勢の書込**は、`charter:351`/`:361`/§14.3 が「PD 実移動で到達せよ」と述べる対象に**重なる**。
⚠ `_load_and_restore_cache`（#3）も **reset とは別 leg**（cache 経路）。

⚠ **in-code comment は述語を弱めている:** `:449-450` 逐語「once, **before the next physics step**」／guard `:60` 逐語「all episode boundaries, **before the next physics step**」。⇒ **`next` であって `first` ではない。** `:474` の要求は `before-first-step`。**comment は要求より弱い述語を書いている。**

## C3. static と runtime を分ける — **temporal enforcement は UNVERIFIED（実装が見当たらない）**

**guard `scripts/validations/check_control_method.py:53-57` 逐語:**
> RESET-SEED manifest (pN follow-up ruling 18:17 JST): CLAUDE.md:67's "once at reset, before the first step" joint-state initialization is the ONLY sanctioned joint-seed class. Entries are exact (file, function) pairs allowed to deliver a reset joint seed; **the once/before-first-step semantics are enforced by in-code asserts at these sites (the static guard pins WHERE, the runtime asserts pin WHEN).**

**私の実測（同 tip）:**

| query | 結果 |
|---|---|
| `_seed_robot_joint_row`（`:852-875`）内の `^\s*(assert\|raise)\b` | **0** |
| 同範囲で `assert\|raise\|if .*first\|once` に一致した行 | **1** — ただし中身は **docstring の "once-at-reset" という語**（`:854`）であって code ではない |
| file 全体の `^\s*assert\b.*(first\|once\|boundary\|step)` | **0 行** |

⇒ **manifest が pin するのは WHERE のみ。** guard comment が主張する「runtime asserts が WHEN を pin する」は、**当該 seed 関数には見当たらない**。⛔ **comment / docstring を runtime proof として扱わない。** ⇒ **temporal enforcement = UNVERIFIED（未実装の可能性を明記）。**
⚠ evidence scope: 私が測ったのは上記 3 query のみ。「どこにも存在しない」とは主張しない。

## C4. class-B 行列（**arm 行を callsite 別に分割**）

| domain / callsite | 設計文の許可根拠 | 実装 conformance | disposition |
|---|---|---|---|
| **arm/robot seed @ `:904` `_reset_worlds`** | `charter:474`（episode boundary・reset 直後 1 回） | ⚠ WHERE は manifest 済／**WHEN は UNVERIFIED**（C3） | **CLOSED**（fail-closed。再承認まで） |
| **arm/robot seed @ `:451` `_build_p0_clamp`** | ⛔ **無し** — `:474` の述語を満たさない（C2） | ⛔ 物理実行後・task 固有姿勢 | **CLOSED** |
| **arm/robot seed @ `:493` `_build_p0_unclamp`** | ⛔ **無し**（同上） | ⛔ task 固有姿勢 | **CLOSED** |
| **arm/robot seed @ `:625` `_load_and_restore_cache`** | ⚠ **別 leg**（reset でない） | 未判定 | **HOLD** |
| **finger** joint seed | `:474` の「robot/finger」表現のみ・単独裁定は薄い | — | **HOLD** |
| **cable** seed（CABLE-SEED） | `charter:352`/`:479` | 実装あり（`_seed_cable_from_snapshot`） | **保持** |
| **body-state 直接書込** | ⛔ 不可（`:474`/`:479`・reset でも） | — | **CLOSED** |
| **route/task 開始姿勢への書込** | ⛔ 不可（`:351`/`:361`/§14.3） | — | **CLOSED** |
| **episode 途中の homing/recovery** | ⛔ 不可（actuator のみ・`:474`） | — | **CLOSED** |

⇒ **確実に許可根拠がある**のは **`charter:474` の設計文（episode 境界・reset 直後 1 回）まで**。**各 callsite の conformance は別判定**であり、**P0 2 件は少なくとも同条件を満たさない。**

## C5. 置換案は **`:67` と `:72` の不可分 2 面**（`:67` 単独置換は `:72` と再衝突する）

⚠ **理由:** `:72` は「**腕関節角の直接書込**」を**例外なしの不許可**として列挙している。`:67` だけを直すと、同じ衝突が再発する。⛔ **generic な joint-state seed の carve-out にはしない** — **exact callsite/domain に pin する。**

**（a）`:67` 置換案:**
> - **`write_joint_state_to_sim` — 制御ループ中は禁止（物理破壊防止）。例外 ①: 制御ループ外の事後可視化（オフライン replay）は **joint-state に限り**許可（body-state は不可）。例外 ②: **episode 境界の初期化 seed** — 許可条件を**すべて**満たす場合に限る: (i) **exact callsite**（guard `RESET_SEED_MANIFEST` に `(file, function)` と期待 count を登録済。**登録なき seed は不可**）(ii) **その episode の最初の物理 step より前**(iii) **境界あたり 1 回**(iv) **loop へ持ち越さない**(v) **joint-state のみ**（body-state 書込ゼロ・body は `mj_forward`/`eval_fk` で関節から従属）(vi) **同一 turn でサーボ目標を同姿勢へ同期**(vii) **(ii)(iii) を runtime assert で強制**。⛔ **task / route の開始姿勢をこの例外で置くことは不可** — 開始姿勢は PD 実移動で到達する。⛔ **episode 途中の homing / recovery は actuator のみ。** ケーブルの seed は CABLE-SEED として現行のまま。**

**（b）`:72` 置換案（不許可列挙の該当項のみ）:**
> ⛔**不許可（不変）= 腕関節角の直接書込〔**唯一の例外 = `:67` 例外② の条件 (i)-(vii) をすべて満たす episode 境界 seed。それ以外の腕関節角書込は一切不可**〕/ 指の kinematic close / `update_kinematic_bodies`（FK→physics の body 複写）/ weld・cable-finger attachment。**

⚠ **(a)(b) は同時に採否を決める**（片方だけ landing すると矛盾が残る）。

## C6. authority の正確形（⛔ 私は Rs 承認を失効させられない）

⛔ **撤回（v1 の書き方）:** 「**landed `:67` は誤り**」を **operative nullification** として書いたこと。

⭐ **正確形:**
- **承認は存在する**（2026-07-26 22:50:51 JST 逐語「承認」）。**私はこれを自力で失効させられない。**
- **誤っていたのは、承認の入力となった私の material basis**（v1 §0 の R1/R2）。
- ⇒ **再判断まで `e391b10c3f85723e88198be90413b93a15f48f4e` が banked governing text。**
- ⇒ ただし **class-B の arm seed は fail-closed**（C4 のとおり CLOSED / HOLD）。
- ⇒ **§C5 の置換案は未承認。**
- ⛔ **p5 / pN の旧裁定が自動で Rs 承認を上書きするとは扱わない。**

## C7. 非主張

⛔ gate flip なし ／ p11 relay 要求なし ／ H-3.1 GO なし ／ H-4 全体 HOLD ／ B-C owner HOLD ／ source・`[CHANGE]`・実装・experiment・RUN・verify・status は **CLOSED**（V10 prior-art guard = blocker）／ **MEMORY 不触**（user 裁定待ち）／ `prohibited.md` は現状固定（user disposition 待ち）／ 他 pane の record を代理編集しない ／ 物理妥当性は判定しない。

---
**p4 cause-side correction v2 = 2026-07-26 23:29 JST / RS-TECH-LEAD (`w2:p4`)**
