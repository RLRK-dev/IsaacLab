# pin (a)(b) chunk — scope prereg + claim manifest (%12/RS-TECH-LEAD)

**v0.3.1 — 2026-07-17 08:00 JST** (record-fix: pN readback 異議 1 点 = guard 順を指定順へ復帰 [§0]。
v0.3 = 07:52 [pN B1/B2 + p5 折込]、v0.2 = 07:35 [[VERIFY] panel 折込]、v0.1 = 07:13。fold 差分は §0)。

**Chunk**: pin 恒久配線の (a) witness per-episode reset + (b) eq clear on reset + route_executor pin-fields
5-hunk の bundle land。**Rs GO = 2026-07-17 06:4x「1」**(選択肢① 採択、記録 = commit `7640695d9a` +
`02-Workflow/HANDOFF.md:96-107` 項3)。banked 開始手順 (順序厳守) = §21.11.1+coupling readback → 著者
claim + producer-unbanked 関係特定 → bundle (先行 land 禁止) → **scope prereg (本 doc)** → prior-art →
実装 → exact-landed 再走 (pN binding)。two-key = p5 (設計軸) + pN (evidence 軸)。

**拘束 (存続、§S4.3 = `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING_VTDESIGN_20260715.md:469-472`)**:
① committed-HEAD 限定 / dirty tree からの訓練起動禁止 ② reward-valid / training-ready 禁止 ((a)(b) +
bundle land + (d) まで) ③ pin-fields は (a)(b) と同一 landing に bundle (先行 land 禁止)。

**pN 条件付き CONCUR (07-17 07:0x message、%12 ack 07:07) の 5 条件 = binding**: (1) claim deadline =
本 doc bank 時刻 (2) diff identity freeze (3) atomic bundle 機構化 (4) acceptance legs (5) two-key まで
training-ready 禁止。**+ pN PRE-BANK HOLD (07:4x) の B1/B2 是正 = binding** (本 v0.3 で折込、bank は
fold 後 = pN 自身の指定「bank 時刻は上記 correction fold 後」)。

## §0 fold log

**v0.2 ([VERIFY] panel → 変更点)**: panel = CC2 correctness (NON-BLOCK、MAJOR2/MINOR4/refinement6) +
CC3 physics (NON-BLOCK、MINOR2/ref4) + CC6 NHA (**BLOCK**、CRITICAL1/MAJOR1/MINOR2/ref4)。CC1 裁定 =
**全指摘 ACCEPT** (CC6 自身の総括どおり「prereg 修正であって再設計でない」)。BLOCK の discharge = v0.2
修正 + §11 declared surface の p5 送付。主変更: §11 新設 / L-F → L-F1/L-F2 分割 / L-D2 新設 / (b) に
audit-then-clear + wc==1 assert / helper 抽出形 / L-B bar 列挙固定 / raise-branch fixtures / §1 に p5
direct query + post-land 競合 unwind / §6 順序訂正。

**v0.3 (pN PRE-BANK HOLD + p5 回答 → 変更点、07-17 07:4x-07:5x)**:
- **pN B1 (wc guard fail-open)**: v0.2 §4 の `getattr(self._solver, "world_count", 1)` は solver に属性が
  無いと wc=4 でも 1 扱い。**%12 独立再測で premise CONFIRM**: solver_mujoco.py の `world_count` は全て
  `model.world_count` (solver 属性でない、grep 07:47)。env authoritative = `self._world_count`
  (newton_route_env.py:509)。→ §4 を `int(self._world_count) != 1 → raise` に固定 + L-C に属性欠落 leg。
- **pN B2 (witness=None early return が audit-gap closure を破る)**: **%12 独立再測で premise CONFIRM**:
  `audit_pin_anchors` (route_executor.py:983-989) は who-wrote-it-agnostic scan (CONNECT ∧ obj2id==0 ∧
  eq_active0==0 ∧ eq_active==1) — v0.2 の witness-gated early return は bypass 書込を audit も clear も
  せず素通しにする。→ §4 を **model-state authority** に再設計 (audit 返却の fired 全 clear)、
  `audit_pin_anchors` に return-tuple を追加する **%12-authored hunk** を §3 IN に追加 (pN 推奨形、
  既存 caller 3+1 箇所は statement-position で戻り値不読 = 互換、%12 grep 07:47)。acceptance legs
  L-C3/L-C4/L-C5 新設 + L-C/L-E/L-F1 文言同期 (pN (a)-(e) 対応表 = §5 末尾)。
- **順序乖離 → pN readback で指定順へ復帰 (v0.3.1 record-fix、08:00)**: v0.3 は wc assert を先頭に置く
  乖離を提案したが、pN readback (07:5x-08:0x、B1/B2 fold 本体 = PASS・sha 全一致) が本項のみ異議 =
  **指定順 ((1) 0∉env_ids return → (2) wc raise) へ復帰**。理由 (%12 が on-disk で confirm): helper の
  責務は world-0 pin lifecycle 限定であり、CPU×wc>1 構成全体の fail-loud owner は既存 make_solver
  tripwire (`newton_skill_env_base.py:1324-1329`、診断 opt-out `THREAD_ALLOW_CPU_MULTIWORLD=1` 込み、
  `newton_route_env.py:424` が cite)。wc-first は world-0 を触らない subset-reset まで殺し opt-out 契約を
  狭める一方、pin 安全性を増やさない。指定順でも 0∈env_ids の reset / public reset() は wc>1 で RAISE =
  **B1 bar 維持** (leg (d) は 0∈env_ids で測る)。acceptance / 設計の reopen なし (pN 指定)。
- **p5 回答 (07:43)**: ① author claim = **NOT MINE** (§1 更新) ② **§S4.5 追補 = GRANT + §11 批准**
  (on-disk 発行 → %12 bank = commit `e40fd541cc`、§11 更新)。
- §2 に **frozen5-body 正規化 sha** を追加 (%12 hunk が :963 に入ると後続 5 hunk の @@ 行番号が shift
  するため、land 時照合の不変量を事前凍結)。

## §1 claim manifest (pN 条件 1)

| 項 | 記録 |
|---|---|
| standing 呼びかけ | `I0A_SCOPE_MANIFEST_RSTECHLEAD_20260716.md:18-20`「著者 pane は claim を — 本 manifest が呼び水」(bank 2026-07-16 21:15、AMENDMENT = `ad0bb76460`) |
| direct query 1 | %12 → p3 (COORD)、07-17 **07:03** 送信。**回答 07:09 = NOT MINE** + producer-unbanked set と**独立** (set 自体 07-12 09:01 `6d1cee5874` で RESOLVED、07:05 実測 clean = 現在空)。note = `I0A_AUTHOR_CLAIM_ROUTEEXEC_PINFIELDS_COORD_20260717.md` (%12 が on-disk read + `6d1cee5874`/porcelain を独立再測) |
| direct query 2 | %12 → p5 (VT-DESIGN)、07-17 07:38 送信 (CC6 指摘 (i))。**回答 07:43 = NOT MINE** — p5 は本 arc 全期間 runtime code 0-edit (write 面 = 自 design doc/handoff/memory/scratchpad のみ)。§1 UNPROVEN disposition + %12 adopter 責任形に concur (p5 message 07-17 07:43 JST) |
| その他 claim | **bank 時点 (本 v0.3 commit) で %12 への claim 着信 = 0** (受信 = p3/p5 の NOT MINE 回答のみ) |
| 帰属 | **author UNPROVEN — 推定しない** (pN 条件 1)。disposition = 「unclaimed pre-existing WIP / author UNPROVEN / content adopted by %12 under p5+pN bundle disposition」。p3 note の「pin-node track の対作業と整合」は整合所見であって帰属裁定ではない |
| 採用内容への責任 | **%12 (adopter)**。⚠CC6 指摘 (ii): 受入計器 V5 test (`test_route_reward_identity_guards.py:219`) は diff と同一 tree で共進化 (`GATE2_I3I4_IMPL_RSTECHLEAD_20260717.md:79` のねじれ) ⇒ happy-path のみでは共有誤解を検出できない → **raise-branch fixtures を §3/L-B に追加** |
| deadline 後 claim | 履歴追補として受理 (commit 帰属の遡及捏造なし)。安全 / 所有競合 claim は**即 HOLD = 後続 chunk 凍結 + p5+pN+Rs 裁定**。landed bundle の revert は Rs 専権 (自動 unwind しない)。比較基盤 = §2 凍結 sha + 本 doc |
| file mtime | route_executor.py = 2026-07-16 18:50:44 JST (p3 note 実測。manifest 事実 — 帰属推論に使わない) |

**deadline = 本 doc の bank commit 時刻で固定** (bank commit hash = deadline の記録)。両 direct query
とも bank 前に NOT MINE 回答済み。

## §2 diff identity freeze (pN 条件 2 + v0.3 二成分化)

**成分 1 = 凍結 5-hunk (unclaimed、adopted content、編集禁止)**:
- file = `thread_isaac_lab/envs/route_executor.py` (working tree 未 commit)
- **patch 全文 sha256 = `625647190a445767449790af35167d34cc2f05f0fb8e50d8bc45ae5af1f17566`** (primary、
  %12-hunk 追加**前**の baseline。**07:47 再照合一致**)
- content-normalized sha256 (`^index ` 行除外) = `bb719b27ee016079ab9c5b117b3f7984ec716d2b8ab4508b81d3f221b7560cc5`
- **frozen5-body sha256 (`^index ` 除外 + `@@` 行番号中立化) = `2083786ad82e01b7f61d43c49078b996606d93c90d8bc70d728d1d92f32479ee`**
  — %12 hunk (:963 領域、file 内で 5-hunk より前) が後続 hunk の @@ 行番号を shift させるため、
  land 時の不変量はこれ。recipe:
  `git diff -- <file> | grep -v '^index ' | sed -E 's/^@@ -[0-9]+(,[0-9]+)? \+[0-9]+(,[0-9]+)? @@/@@ @@/' | sha256sum`
- **5 hunks / 19+ 1− / 全 hunk が `_prepare_recording` 内** (:4414 docstring / :4433 witness triple
  all-or-none 抽出 + ValueError / :4459 per-frame shape 検査 / :4503 return→prepared / :4517 update)
- 独立再測 3 本一致: %12 (07:0x, 07:47) / pN (co-decide) / p3 (note 07:05)

**成分 2 = %12-authored lifecycle hunk (v0.3 新設、pN B2 推奨形)**:
- 内容 = `audit_pin_anchors` (route_executor.py:963-1012) に **検証済 fired eq-id tuple の return** を
  追加 (docstring Returns + `return tuple(fired)`)。既存 caller (newton_route_env.py:1934 /
  authorize_clip_pin_controls.py:205,226,233) は statement-position = 戻り値不読 → 互換 (grep 07:47)
- 著者 = %12 (帰属明確、成分 1 と別列)。作成 = [CHANGE] 時。**正規化 patch text + sha を [RESULT] に
  land 前記録**
- aggregate (成分 1+2) staged diff sha = land 時に計測し land 記録へ

**再 open 規則 (v0.3)**: 成分 1 の **hunk body byte 変化** (frozen5-body sha 不一致) → deadline /
disposition 再 open (pN 条件 2)。%12 hunk 由来の @@ 行番号 shift = **宣言済み・良性** (loud 記録)。
`^index ` 略記 drift = 良性 (loud 記録)。land 時照合手順は §6-3。

## §3 scope (IN / OUT)

**IN (bundle = 単一 atomic commit、pN 条件 3)**:
1. `thread_isaac_lab/envs/route_executor.py` — **二成分のみ**: 1a = 凍結 5-hunk (編集禁止) / 1b =
   %12 audit-return hunk (§2 成分 2)。これ以外の編集ゼロ
2. `thread_isaac_lab/envs/newton_route_env.py` — (a)(b): **抽出 helper `_clear_c1_pin(env_ids)`**
   (§4 v0.3 形) + `_reset_worlds` 冒頭 (len==0 check 直後、:1036 state restore 前) からの呼出
3. `thread_isaac_lab/scripts/test_route_reward_identity_guards.py` — reset-lifecycle unit tests +
   **raise-branch fixtures 3 本** (§1) + **bypass fixtures (L-C3/L-C4/L-C5、実装体は probe 側でも可)**
4. `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_ab_lifecycle_probe.py` (+ `_result.json`) —
   新規 probe (L-D/L-D2/L-E/L-F 実行体 + bypass legs。直接 eq 書込 pattern は
   `authorize_clip_pin_controls.py:223-224` 踏襲)
5. 本 doc + [RESULT] 追記

**OUT**: (d) policy-drive trigger (p5 設計待ち、別 gate — refire の非 raise 化・訓練時 trigger 規則、
+ **witness-vs-fired 不一致の runtime loud 化** [p5 optional-hardening 登録 08:00、本 chunk は
L-C3/C4/C5 + probe 検出で足りる] を含む) / FM3/FM4 (land 済) / task_config.py (不触) / dirty tree の他内容 (stage しない) / 訓練起動
(禁止継続) / route_executor.py の成分 1a/1b 外の編集 (ゼロ) / done path :1926-1934 の既存 audit block
(残置 — 二重 audit は read-only で無害) / B4 state-bank fork との相互作用 (B4 gate 側 prereg 項目)。

## §4 実装設計 (banked §21.11.1 + coupling 注記の執行、pN B1/B2 折込後)

**形 = 抽出 helper、model-state authority** (pN B2: reset(world0) は witness でなく model state を
authority にする — audit の who-wrote-it-agnostic scan が返す fired 全てを audit-then-clear):

```python
def _clear_c1_pin(self, env_ids):
    """(a)(b) clip-pin lifecycle (RLENV_PIN_DESIGN section 21.11.1; single-world CPU path).
    Model-state authority (pN B2): the clear set = ALL fired pin candidates returned by the
    section 15.4 audit's who-wrote-it-agnostic scan -- NOT the witness eq alone -- so a
    bypass write (eq_active flipped without the authorizer) is audited-then-cleared on
    EVERY reset path (done-driven AND public reset()). audit-then-clear order is
    load-bearing: the clear destroys the episode's weld evidence. Identity
    (_pin_seat_seg/_pin_onset_frame/_route_rec_step_f) is recording-derived and NEVER
    cleared (coupling note: the escape guard reads identity, not witness)."""
    if 0 not in env_ids:              # pin is world-0-only: a reset not touching world 0 is out
        return                        # of this helper's scope (wc>1 whole-config loudness is
                                      # owned by the make_solver tripwire, base:1324-1329)
    if int(self._world_count) != 1:   # env-authoritative (pN B1: solver has no world_count
        raise RuntimeError(           # attr -> getattr(solver, ..., 1) is fail-open)
            f"clip-pin lifecycle requires world_count==1 (CPU path); got {self._world_count}"
            " -- CPU eq writes are GPU-inert at wc>1 (banked hypothesis 2026-07-16)"
        )
    import route_executor as rex      # lazy, mirrors :1930
    mjm = getattr(self._solver, "mj_model", None)
    if mjm is None:                   # no CPU eq table -> no pin can exist (mirrors :1933)
        return
    mjd = self._solver.mj_data
    fired = rex.audit_pin_anchors(mjm, mjd)  # RAISEs on count/anchor violation BEFORE any
                                             # clear; returns verified fired eq ids
    for eq_id in fired:
        mjd.eq_active[eq_id] = 0
        if int(mjd.eq_active[eq_id]) != 0:
            raise RuntimeError(f"eq_active[{eq_id}] readback != 0 after clear")  # fail-loud
    self._c1_pin_witness = None       # (a): refire allowed next episode at recording onset
```

呼出 = `_reset_worlds` 冒頭 (`len(env_ids)==0` return 直後、:1036 state restore 前)。両呼出元
(done path :1935 / public `reset()` :1896) を 1 経路で被覆。

- **flag 非依存 (pN (e) 訂正)**: v0.2 の「flag-OFF / witness None = 完全 no-op」は誤り —
  正 = 「**no active candidate = state no-op (audit は read-only で常に走る)**。bypass 候補が在れば
  witness=None でも flag-OFF でも audit→clear が走る」。`route_c1_pin` flag は発火 (activation) のみを
  gate し、episode 境界の cleanup は model state が支配する。
- **guard 順 = pN 指定順** (0∉env_ids return → wc raise): helper 責務 = world-0 pin lifecycle 限定。
  wc>1 構成全体の loud 化は make_solver tripwire が owner (§0 v0.3.1 項)。
- **不触**: `_pin_seat_seg` / `_pin_onset_frame` / `_route_rec_step_f` (recording 由来、coupling 注記)。
- **anchor 残置無害** (CC3 実証): audit filter は `eq_active==1` の後にのみ `eq_data[3:6]` を読む
  (route_executor.py:989→:997)。refire 選択は xpos 距離 (:776)、eq_data 不読。`eq_active0` は全読取
  (書込ゼロ、grep 網羅) ⇒ cleared eq は再選択可能、再選択は決定的 (≈0mm vs 節 pitch ~14.6mm vs 5mm gap)。
- **clear は次 step で構造的に honored** (CC3 実証): 拘束行は毎 forward/step で `mjd.eq_active` から
  再構築、`mj_resetData` (唯一の eq_active0→eq_active 復元元) は thread_isaac_lab に不在、per-step CPU
  sync は qpos/qvel のみ。ACTIVATE を g6_live-証明した対称性がそのまま CLEAR を証明する。
- **fight-window なし** (CC3 実証): ep1 終端 step → audit (read-only) → clear → Newton 側 restore のみ
  (mujoco 呼びゼロ) → 次 solver.step が `_update_mjc_data` (interval=1) で qpos を先に置換 → mj_step。
  {restored state ∧ active eq} で走る forward/step は存在しない。
- **done path の既存 audit (:1926-1934) は残置**: helper 内 audit と合わせ二重 audit になるが read-only
  で無害 (scope 外編集を増やさない)。
- **Dahl/grip**: 干渉なし (CC3: `reset_dahl_friction_for_envs` は本 solver で構造的 no-op /
  `reseed_grip_open` は `control.joint_target_pos` のみ)。

## §5 acceptance legs (pN 条件 4 + HOLD (a)-(e)、事前登録 — 実測値は [RESULT] に追記)

| leg | 内容 | PASS bar |
|---|---|---|
| L-A | **before**: exact committed HEAD (隔離 worktree) で V5 test FAIL 再確認 | FAIL 1 本 = `test_pin_identity_fields_survive_recording_prepare` のみ (GATE2:79 再現) |
| L-B | **after**: landed commit の隔離 worktree で **既存 10 test (名前列挙で固定: fm4_c1 / fm4_c2 / fm3 / i3×2 / i4×2 / escape_sentinel / crossing_x_dev / pin_identity_fields) 全 PASS + 新規追加 test 全 PASS** | 全 PASS、exit 0 (**pN binding**) |
| L-C | unit: `_clear_c1_pin` 決定論理 | clear 実行 iff (wc==1 ∧ 0∈env_ids ∧ audited fired ≠ ∅) / **0∉env_ids → wc に関わらず no-op (return、指定順)** / **wc≠1 (0∈env_ids 下) → raise — env `_world_count=4` かつ solver に `world_count` 属性なしでも RAISE (pN B1 leg)** / readback 失敗 → raise / audit が clear より先 (呼出記録 assert) / identity 属性 前後対称差 = ∅ / 実行後 witness = None |
| L-C2 | unit: **raise-branch fixtures** — partial witness (2/3 keys) → ValueError / per-frame shape 不一致 → ValueError / fields 全欠 → pin_fields 無しで素通り (prepared に pin key 無) | 3/3 期待どおり (§1 共進化計器の穴埋め) |
| L-C3 | **bypass + 圏外 (pN (a))**: `eq_active[k]=1` 直接書込 + anchor を capture volume 外 + witness=None → reset | **clear 前に audit RAISE** (raise 後 eq_active[k]==1 のまま = clear 未実行の証明) |
| L-C4 | **bypass + 圏内 (pN (b))**: 直接書込 + anchor 圏内 + witness=None → reset | audit PASS → **eq_active[k]==0 に clear される** (witness gate で素通しされない = B2 の直接計器) |
| L-C5 | **複数候補 (pN (c))**: (i) fired 2 本・全 anchor 圏内・n_auth 以内 → 全 clear / (ii) fired > n_auth → RAISE (clear ゼロ) / (iii) いずれか anchor 圏外 → RAISE (clear ゼロ) | (i) 全 eq==0 / (ii)(iii) raise 後 全 eq==1 のまま |
| L-D | probe: **ep1 fire → audit → reset clear → ep2 refire** (canonical recording、CPU、`route_c1_pin=ON`、**`route_drive_ff=True`**、INIT_XY_NOISE=0、**2 cells = x0_y0 + x-20_y-15**) | ep1: witness + eq_active==1 + audit PASS → reset: eq_active[eq_id]==0 ∧ witness None → ep2: onset で再発火・新 witness・audit PASS。**ep1/ep2 の trajectory byte 一致は主張しない** (CC3: `qacc_warmstart` 持越しは設計上) |
| L-D2 | **ep1≡ep2 scoring 等価** (CC6 MAJOR): 同 probe 内で ep1/ep2 の **event timeline (pin fire step / G3 latch step / termination reason / done step) 完全一致** = hard。reward per-step trace は記録し差分を [RESULT] に報告 (期待 ≈0、判定は two-key) | event timeline 完全一致 (hard)。1-step ずれも FAIL = episode 境界状態の真の発見として surface |
| L-E | 隣接状態不変: reset clear 前後で eq_active vector の **audited-fired 集合外** 対称差 (**pN (e) 文言**: no active candidate = state no-op、audit read-only) | = ∅ |
| L-F1 | **(a)(b)-hunk 不活性** (flag-OFF・**bypass 書込なし** ⇒ fired 候補 ∅ = state no-op): baseline = gate②-裁定系譜 tree (凍結 5-hunk あり) の bytes、そこに (a)(b) 追加のみを足した tree と flag-OFF replay 比較 | trace byte 一致 (state no-op の証明) |
| L-F2 | **bundle-vs-HEAD declared delta の実測** (CC6 CRITICAL discharge): baseline = committed HEAD (bank commit hash + config + recording sha で pin)、flag-OFF・固定長 stepping で bundle tree と比較。§11 の宣言 delta が**宣言どおりに・宣言した面にだけ**現れることの測定 (**§S4.5 付帯 2: 宣言外 delta ≠ 0 → 追補 re-open**) | 物理 trace = 分岐点まで一致 + 分岐後 delta が §11 宣言面と一致 (宣言外の面に delta ゼロ)。実測は [RESULT] + two-key 判定 |
| L-G | format: **post-land** に L-B と同一の隔離 worktree で `./isaaclab.sh -f`、baseline 差を記録 (pre-land は touched files 限定の ruff/py_compile) | shared tree へ autoformat 残渣ゼロ |

**pN HOLD (a)-(e) → legs 対応表**: (a)→L-C3 / (b)→L-C4 / (c)→L-C5 / (d)→L-C wc leg (属性欠落込み) /
(e)→L-C・L-E・L-F1 の文言同期 (済、本 v0.3)。

**land 後**: L-B (pN binding) → two-key (p5 設計軸 [§11 批准済 + v0.3 §4 正式 conform] + pN evidence 軸)。
**それまで reward-valid / training-ready 主張禁止** (pN 条件 5、§S4.3-2)。

## §6 landing protocol (pN 条件 3、v0.3 二成分照合)

1. 実装 + legs L-A/L-C/L-C2/L-C3/L-C4/L-C5/L-D/L-D2/L-E/L-F1/L-F2 PASS (L-B/L-G は land 後) +
   pre-land 形式チェック = touched files 限定 ruff/py_compile。
2. `git add` は **一括 1 回**: §3 IN の 5 系統のみ。
3. **add 後・commit 前の staged-hunk 検査 (hard step、B2 教訓)**: `git diff --cached --stat` + per-file
   hunk 列挙を §3 IN と**対称差照合 (=∅)**。route_executor staged patch は二成分照合:
   (i) staged diff から %12 hunk ([RESULT] 記録の正規化 text) を除去 → §2 recipe で正規化 →
   **== frozen5-body sha `2083786a…`** (ii) %12 hunk = 記録 text と byte 一致 (iii) aggregate staged
   sha を land 記録へ。不一致 → §2 再 open 規則。
4. **単一 atomic commit** (explicit-path)。route_executor 単独 commit / 先行 stage / 一時 land 禁止。
   pre-commit hook (validate.sh --staged-only) は check-only — **`--no-verify` は記録付き正当化なしに禁止**。
5. commit 後: 隔離 worktree @ landed commit で L-B + L-G。
6. push は Rs 提案のみ (standing)。

## §7 prior-art guard (層4、07:1x 実行 — BLOCKER 文脈と delta 説明)

`scripts/check_thread_vault_prior_art.sh --fail-on-blocker pin witness reset eq_active episode refire`
= **BLOCKER_CONTEXT_FOUND** (r2a_track_a 2026-05-21: kinematic **finger-support** pose-pin/auto-reset)。
**同一 failed path でない理由**: r2a の 'pin' = robot finger 体の kinematic pose-pin (hidden support) =
禁止 kinematic-attachment class。本 chunk の pin = **clip-retention pin** = RS71 §0 INVARIANT #5 の唯一の
認可例外 + Rs 逐語「クリップのみ pin を RL env に恒久配線しろ」(LEDGER:57)。authorizer が capture volume
外を raise で拒否 — 機構的に例外 scope 内。本 chunk は banked authorizer path への lifecycle 追加のみ。
新 directive = Rs GO 06:4x + banked §21.11.1 ⇒ guard escape 条件 (new directive + concrete delta) 充足。
r2a の有用残渣 = reset 時 `body_q_prev` sync 整合 (既存 `restore_world_body_state` が処置、L-E で実測)。

## §8 gate 状態 + DESIGN-GATE carry の正確な主張 (CC2 MAJOR-1 / CC6 CRITICAL 折込)

| gate | 状態 |
|---|---|
| [L-TRIAGE] | **L3** (self=auto) |
| [VERIFY] panel | **完了** (§0/§9)。BLOCK 1 (CC6) → 全 ACCEPT + v0.2 修正 + §11 宣言面で discharge。**+ pN evidence-axis HOLD B1/B2 → v0.3 折込 (§0)** |
| DESIGN-GATE | **baseline 明示の上で carry 充足** (下記) — §11 = **p5 批准済 (§S4.5、`e40fd541cc`)** |
| [RULE-CHECK] stage2 | [CHANGE] 直前に実行・出力貼付 |
| 層2 事後 / 層5 | L3 ⇒ 実装後 (two-key と併走) |

**carry 主張の正確形 (v0.1 の「reward 意味論を変えない」を訂正)**:
- **gate②-裁定系譜 tree (5-hunk あり) に対して**: (a)(b) は reward 意味論を変えない lifecycle 配線
  (leg1 /reward-design `1b59f23c44` + leg3 /pre-check `6ec126b1bb` + §S3/§S4 は**この系譜上で**産出・
  批准された — L-A 自身が「HEAD では V5 invariant FALSE」= HEAD 側が anomaly であることの証明)。
- **committed HEAD に対して**: bundle land は **§S3-批准済 FM4 identity path を flag-OFF 構成でも活性化
  する** (declared delta、§11)。これは「未批准の意味論を持ち込む」のではなく「批准済み意味論が HEAD の
  計器死 (pin keys drop) で不発だったのを、批准時の姿に戻す」— **§S4.5 で批准済** (宣言なしの ship では
  なくなった)。

## §9 [VERIFY] panel + evidence-axis OUTCOME

| lens | verdict | 主要 finding → 処置 |
|---|---|---|
| CC2 correctness | NON-BLOCK (MAJOR2/MINOR4) | §8 carry 主張の baseline 不在 → §8 訂正 / L-F 誤参照・方向未定 → L-F1/L-F2 分割 / reset() audit gap → §4 audit-then-clear / wc>1 readback 空洞 → §4 assert / L-D ff 未指定 → 指定 / L-C stub 不能 → helper 抽出。R1-R6 全折込 |
| CC3 physics | NON-BLOCK (MINOR2) | qacc_warmstart 持越し → L-D byte 非主張 + L-D2 は event-timeline bar / notify_model_changed の live-anchor clobber (今日 caller ゼロ・pre-existing) → §12 carry invariant。clear honored / anchor 残置無害 / fight-window なし / eq_active0 不変 / Dahl no-op = 実証済み clean |
| CC6 NHA | **BLOCK** (CRIT1/MAJ1/MIN2) | flag-OFF 非不変 + §S4 fence 結合の空洞化 → **§11 宣言面 + p5 批准 + L-F2** / ep1≡ep2 計器欠落 → **L-D2 新設** / reset() 監査消失 → §4 / wc>1 → §4 / manifest 残差 → §1。CC1 裁定 = 全 ACCEPT、discharge = v0.2 + p5 批准 (済、§S4.5) |
| **pN evidence 軸 (PRE-BANK HOLD 07:4x)** | **B1 + B2 = blocker** | B1 wc guard fail-open → §4 env-authority raise + L-C 属性欠落 leg / B2 witness-gated audit skip → §4 model-state authority + %12 audit-return hunk + L-C3/C4/C5 + 文言同期。**両 premise を %12 が独立再測で CONFIRM (§0)** → v0.3 折込。bank = fold 後 (pN 指定) |

裁定注記 (CC6 CRITICAL の独立確認): %12 が canonical npz を直接検分 —
`w0e_81rerun_snapdown_0537/cell_x0_y0/route_demo_raw.npz` に `pin_active/pin_eqid/pinned_body` 実在、
onset=2544 (CC6 測定と一致)。⇒ 5-hunk land 後は flag-OFF でも identity が wire される、は事実。

## §10 [RESULT] (legs 実測後追記)

(pending)

## §11 declared semantic surface (flag-OFF delta の宣言) — **p5 批准済 (§S4.5 GRANT)**

**宣言**: bundle land 後の committed HEAD では、route-executor 経由の全 run (canonical recordings は
pin fields を実際に持つ — §9 裁定注記) で `_wire_c1_pin_from_recording` が `_pin_seat_seg` を wire する
(`newton_route_env.py:576-582` 無条件呼出 + `:1807`)。**`route_c1_pin=OFF` でも**: seat identity 計器が
live 化 → G3/G5 latch 可能化・`c1_escape` → dropped −10 terminate 可能化 (`:1645,:1651,:1707-1715`)・
obs[49]/[58]-[61] が MISS sentinel から live 値へ。**pin の発火だけが flag-gated のまま** (発火なし ⇒
B0_NOPIN のとおり cable は C1 を離れ、escape 終了が早期 done を作る — HEAD の timeout 挙動と異なる)。

- **これは §S3/§S4 で批准済みの FM4 identity 意味論そのもの** (gate② 全 evidence はこの意味論の tree 上
  で産出)。HEAD の「計器死」状態が批准外の anomaly (L-A が証明)。
- **批准 = §S4.5 (2026-07-17 07:5x p5 発行 → %12 bank `e40fd541cc`、REWARDDESIGN doc :477-499)**:
  §S4.2 を 3-state へ supersede、(iii) wired-not-fired を §S4.4 exemption に包含 (正直採点 = RS71 §4
  境界報告)。**境界不変**: (iii) run は producer 等価 outcome を主張してはならない。付帯 2 本 =
  系譜断絶 1 回記録 (land 記録に、I0-a FF-replay anchor は landed HEAD で再現不可) + **L-F2 で宣言外
  delta 検出 → 追補 re-open**。obs[57] 除外は正 (global crossing は identity 非依存で従前から live)。
- **§4 helper への p5 判定 = PRELIMINARY CONFORM (対象 = v0.2 text)**。⚠v0.3 §4 は pN B1/B2 fold で
  改定 (witness-単独 clear → audited-fired 全 clear の model-state authority / wc = env `_world_count` /
  %12 audit-return hunk) — p5 の conform 5 条件 (identity 不触 / audit-then-clear 全経路 / wc==1
  tripwire / blanket clear なし [clear 対象は audit 検証済 fired 集合のみ = §15.4 filter、無差別 zero
  でない] / witness per-episode ephemeral) は**全て維持**。正式 conform = post-land two-key で
  **v0.3 §4 を対象に**回す (delta は p5 へ 07:5x dispatch で通知)。

## §12 carry notes (standing、本 chunk の外へ持ち出す不変条件)

1. **live pin 中の `notify_model_changed` 禁止** (CC3: `solver_mujoco.py:6550-6551` の blanket eq_data
   resync が live anchor を build 値へテレポートさせる。今日 caller ゼロ = latent。将来の DR/dof-tuning
   実装時の hard 前提。LL-Newton への転記は bank 後)。
2. **witness の run-level provenance** (CC6-ref): (a) 化で witness は per-episode ephemeral → probe json
   は per-episode 記録 (L-D artifact)。訓練時代の等価物 = (d) gate の設計項目。
3. wc>1 opt-out 文脈では frozen worlds の timeout done が world-0 mid-episode に audit を走らせ得る
   (CC3-R3: 無害・pass するが、audit 呼出を episode 境界と読み替えるな)。**v0.3.1 guard 順では
   0∈env_ids の reset が wc>1 で raise / 0 非含有 subset-reset は no-op — 本 note は診断 opt-out
   (`THREAD_ALLOW_CPU_MULTIWORLD=1`) 構成への carry**。
4. B4 state-bank fork: post-onset bank state は最初の ff step で位置発火する → **B4 gate の prereg 項目**。
