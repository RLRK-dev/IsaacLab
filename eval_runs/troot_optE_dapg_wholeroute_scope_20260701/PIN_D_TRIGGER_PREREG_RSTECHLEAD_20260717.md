# (d-a) FF live-geometric trigger chunk — scope prereg + claim manifest (%12/RS-TECH-LEAD)

**v0.6 — 2026-07-17 12:52 JST** (pN re-readback 残差 R-B2..R-B5 fold + **§S4.7 裁定 fold** [B1 formal
CLOSE]。v0.5 = 12:34 [HOLD B1-B5]、v0.4 = 12:18 [freeze 最終形]、v0.3 = 11:47 [panel]、v0.2 = 11:22、
v0.1 = 10:47。差分は §0)。

**Chunk (pN B1 で scope 命名を訂正)**: pin 恒久配線 (d) 系のうち **(d-a) = FF branch の発火 trigger を
recording-onset から live 幾何 capture trigger へ条件置換**する実装 chunk。**(d) 全体 = (d-a) + D-b**
(D-b = 残差/IK drive branch への評価配置。call site `:1221` は FF branch のみ [%12 grep 実測: call 1
箇所]、policy/IK branch `:1235+` に trigger 不在、かつ **FF は projected residual を drive しない** ⇒
本 chunk 単独は policy-drive (d) の完成でない)。
charter = `PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md` **v1.5 全裁定済** (§8.1-§8.8 bank
`efad9c05b9` + `2b8ed62366`、§8.10 bank `65879a8fae`、§8.11 bank `d5bbd18e1b`、**§8.12 = v0.4 設計軸
CONFORM PASS bank `6cbbbd0066`**)。素材 = `PIN_D_MATERIALS_RSTECHLEAD_20260717.md` v0.2 (`b3823f2961`、
81-cell 窓解析 = p5 独立再計算一致)。banked 手順 (charter §8.9) = **prereg (本 doc) → panel → 実装 →
probe → /pre-check → two-key (p5 設計軸 + pN evidence 軸)**。pattern = `PIN_AB_SCOPE_PREREG_
RSTECHLEAD_20260717.md` の pN 条件パターン (claim / freeze / legs / landing protocol) を継承。

**拘束 (存続、§S4.7 で正式化)**: ① reward-valid / training-ready 禁止 = **(d-a) two-key PASS ∧ (d-b)
two-key PASS ∧ §12-5 cell-2 追補まで — 本 chunk (d-a) の two-key 単独では解除しない**。**正式裁定 =
§S4.7 (`REWARDDESIGN_...VTDESIGN_20260715.md`、bank `e20d076912`)**: §S4.3-2 の「(d)」= 設計目標全体 =
(d-a) [FF trigger 機構 = 本 chunk] + (d-b) [訓練 drive 分岐配置 = D-b window gate、§12-6 carry と同一物]
— 保守側凍結 (v0.5) を RATIFY。Rs 明示 ablation は foreclose しない (§S4.7.3)。charter §4-5 / §8.12
standing 行への pointer = 授権執行済 (同 commit)。
② committed-HEAD 限定 / dirty tree からの訓練起動禁止 ③ 本 chunk に訓練起動なし (probe のみ)。

## §0 fold log

- v0.1 = 起草 (10:47)。open queries §Q は p5 へ同時 dispatch。
- **v0.2 = §8.10 fold (11:22)**: p5 裁定 4 本 (charter v1.3 `65879a8fae`、%12 bank + §8.4-3 訂正 #11
  pointer 授権執行) を凍結に反映 — Q-1 = K 単位 physics frame・anchor fire_frame **2429** / fire_step
  **242** 凍結 / Q-2 = containment-by-identity CONFORM + **same-snapshot 規律を load-bearing freeze 化**
  (§2-6a) / Q-3 = CONFORM + supervisor `windows_total`/`windows_with_done` 追加 (§2-D) / Q-4 = CONFORM。
  PENDING 全解除。⚠v0.1 への [VERIFY] panel 3-lens は 3 本とも API 上限で abort (finding ゼロ) —
  **panel は v0.2 に対し再走** (結果 = §9)。
- **v0.3 = panel fold (11:47)**: verdicts = CC2 NON-BLOCK (MAJ3/MIN5/ref3) / CC3 **BLOCK** (MAJ3/MIN1/
  ref1/CLEAN2) / CC6 **BLOCK** (CRIT1/MAJ3/MIN3/ref2)。**CC1 = 全 ACCEPT** — block-bearing premise は
  %12 が全て独立再測で CONFIRM してから fold: (i) collector default = flag OFF (`forkb_collector.py:
  157-168` cfg に pin key 無・`newton_route_env.py:466` default False) + budget 230 (`:124`) < fire
  242/243 < done ≈342 ⇒ **v0.2 §3 OUT の「Stage-A 収集で trigger が働く」は as-configured で偽** →
  §3 書換 + L-H vehicle 宣言 (ii) 録画 = post-step sample (`route_executor.py:1768`)・online check =
  pre-step (`:1221-1222`) ⇒ **off-by-one: 正 = fire_frame 2430 / fire_step 243 / 式 first_true+K**
  (§8.10.1 凍結値の訂正 = Q-6 で p5 裁定待ち) (iii) **anchor 深度**: npz 直読で state2429 z=835.665mm
  (rim 836 の 0.335mm 内側) vs onset-era 828.653mm (margin 7.35mm)、fire 後 ~105f で 7.035mm の追加
  降下 command、pin eq = solref default (`newton_skill_env_base.py:1605-1612`、gripper 4-bar `:2021`
  と対照) ⇒ K=3 裁定素材に無かった帰結 = Q-7 で p5 ratify/revise 裁定待ち (iv) `clip_geoms_at` は
  mj_forward を無条件呼出 (`:870`) ⇒ v0.2 §4 の「no mj_forward」と「同一 loop body」は非両立 →
  cache+hoist 設計を freeze 化 (§2-6b)。主変更: §3 OUT 書換 / L-H vehicle + HEAD-vs-bundle sub-leg /
  L-C(d)-(vi) 摂動型再仕様 (旧仕様は fail 不能 = 計器でない) / L-D に force/depth/continuity legs /
  L-F baseline 3 点 pin 復元 / §11 に anchor-depth shift + artifact surface + dormancy 宣言 / call
  site cite :1222→:1221 訂正 / §12 carry 3 本追加。**blocking 残 = Q-6/Q-7 (p5)**。
- **v0.4 = §8.11 fold (12:18)**: p5 裁定 4 本 (charter v1.4 `d5bbd18e1b`、%12 bank + 授権 pointer 2 本
  [§2-4 /pre-check supersession・§8.10.4 訂正 #13] 執行)。**⭐Q-7 = REVISE 採択** — fire 条件に深さ leg
  追加 (`Z_FIRE_DEPTH_M = ROUTE_GROOVE_Z + CABLE_RADIUS/2 = 0.831`、新 literal ゼロ; ratify 不採用根拠 =
  eq は弾性拘束で解放後 anchor 復帰 ⇒ rim anchor 835.665 では drag +0.34mm flicker で G6 sustain 構造死
  = 解析で確定、probe 待ち事項でない; %12 測定 legs 5 本は全 ADOPT)。**Q-6 = ACCEPT = 訂正 #12** (式 =
  `fire_label = run_start + K`・anchor = 録画[fire_label−1])。**凍結値再固定 (REVISE 後)**: canonical
  run_start **2465** / fire_label **2468** / fire_step **246** / anchor z **830.640mm** (band [830.604,
  830.899]、retention margin ≥5.10mm) — **%12 独立再測 = 全一致** (Z_FIRE 0.831 導出・2465・2468/246・
  830.640 exact・onset−fire 76 ∈[56,112]・release−fire 226 ≥206・bar 以下連続 True)。⚠残押込は charter
  ≈1.8mm vs %12 再測 1.99-2.01mm (anchor→onset-era rest / →min) — 桁一致・方法差、実値 = L-D 実測が
  確定 (p5 へ申告済)。Q-5 = GRANT / Q-8 = 訂正 #13 + K 根拠 downgrade 批准 (値 3 凍結)。DR carry 新設
  (§12-8: bar headroom 1.285mm・検出器 = fire 率・DR-ON 日再検)。rim 規則の経由値 (2429/2430/242/243)
  は凍結しない (§8.11.1)。
- **v0.5 = pN pre-bank HOLD B1-B5 + p5 §8.12 fold (12:34)**: **p5 設計軸 = v0.4 CONFORM PASS** (§8.12
  bank `6cbbbd0066`、bar 超過 4 点明記・実装可; 残押込 ≈1.8 = p5 丸め自認 [正 1.987]) と **pN evidence
  軸 = HOLD (B1 CRIT + B2-B5 MAJ)** が並行着信 — CC1 = pN 全 ACCEPT、premise 独立再測: **B1 CONFIRM**
  (call site grep = :1221 の 1 箇所のみ [FF branch]、IK/residual loop :1249+ に pin 呼出なし、FF は
  residual 非 drive) ⇒ **chunk = (d-a) に scope 訂正 + training-ready 禁止を (d) 全体 (d-a+D-b) two-key
  まで延長** (§S4.3-2 解釈の正式裁定 = p5 照会中、prereg は保守側凍結) + §7/§11 の unlock 主張訂正 /
  **B2 CONFIRM** (manifest の code_sha/sha256/env_fingerprint_sha/pid は構成的に変わる — 旧 L-H2 bar は
  PASS 不能) ⇒ 項目別 bar 化 (期待一致集合 vs 期待差分集合の明示) / **B3** ⇒ L-A = tests-only patch
  規律 (named IDs・exact fail reason・「不在/収集不能」を bar から削除) / **B4** ⇒ L-H = 2-run vehicle
  を exact command で事前固定 (Run A/B、budget×flag の交絡排除) + L-H2 = 別 flag-OFF run 明記 / **B5**
  ⇒ L-D bar 二値化 (fire_label exact hard・anchor band hard・force/z/reward = characterization-only
  明示) + §6 に isolated-worktree full-hook ×2 pre-commit 手順。+ p5 §8.12 注記① fold = §11 wrong-clip
  宣言。**bank = pN re-readback PASS 後** (claim deadline は HOLD 中凍結、pN 指定)。
- **v0.6 = pN re-readback 残差 R-B2..R-B5 + §S4.7 fold (12:52)**: **B1 = CLOSE** (pN 12:4x) + **§S4.7
  正式裁定 bank `e20d076912`** (「(d)」= (d-a)+(d-b)、保守側凍結 RATIFY、charter pointer 2 本執行) =
  拘束① 正式化。残差 4 点 fold (%12 premise 再測: env_fingerprint = env-var map hash [closure sha で
  ない、collector :186-196/:273-274] / closure_sha256 = proc_meta 側 / `isaaclab.sh -f` ≡ `pre_commit
  run --all-files` [format.py `command_format`]): **R-B2** = L-H2 期待差分を {code_sha, sha256} に縮小・
  env_fingerprint_sha を期待一致へ (元 map equality 込)・pid = self-consistency のみ・closure_sha256 =
  各版 self-consistency assert / **R-B3** = L-A baseline **`88b7a16681` 逐語凍結** + test-ID 表 (期待
  exception type/message substring) 事前凍結 + tests-only patch sha を production fix 着手前に記録 +
  fixture/import/collection error は FAIL として不受理 / **R-B4** = §3-8 Run A/B/C を interpreter path・
  script path・全 required args・数値 seed・隔離 outbox まで逐語凍結 / **R-B5** = §6-1a を exact
  `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -f` ×2 に固定。**第 3 readback 待ち** (claim
  deadline は継続凍結)。

## §Q open queries (v0.1 で p5 へ照会 → **v0.2 で全 4 項 RESOLVED、裁定 = charter §8.10** — 原文は記録として保持)

- **Q-1 K-dwell の単位** (§8.4-2 は「K=3」、§8.6(b) は「期待 fire ≈ 243+(K−1)」= RL step 算術):
  評価配置 = 既存 call site (`newton_route_env.py:1222`、`for step in range(PHYSICS_STEPS_PER_RL)` 内 =
  **per-physics-frame**、charter §8.4-1「条件置換」)。dwell を評価 cadence で数えると **K=3 = 3 連続
  physics frame** ⇒ 期待 fire ≈ frame 2429 = RL step **242** (G3 latch 242 と同 step)。RL-step 単位なら
  期待 fire ≈ **245**。**%12 推奨 = physics-frame 単位** (置換 ruling の cadence と一致 + §8.4-2 の
  「数値 wobble」= frame 級現象)。どちらでも hard bar `fire_step ∈ [242, 250]` (§5 L-D) 内。
  → **裁定要**: 単位 + 凍結する期待 anchor 値。
  → ✅ **RESOLVED = §8.10.1**: 単位 = physics frame (%12 推奨 concur)。anchor = §2-11 に凍結。
- **Q-2 containment の実体** (§8.4-3「lat 3.5 < 6.0 = 真に内側」): on-disk 実測では authorizer
  (`route_executor.py:956`) も audit (`:1010`) も fire 述語と**同一関数・同一 bar**
  (`clip_capture_predicate` + `rc.SEAT_LAT_BAR_M=3.5mm` / y_win=model geom / `SEAT_Z_LO/HI=821/836`) —
  「6.0」の bar は code に不在 (grep 済)。**本 prereg の設計 = containment-by-identity** (per-step check は
  authorizer と同一 loop body を共有 ⇒ fire-True ⇒ authorizer-accept が構成的に成立、⊆ は等号で充足、
  §8.4-3 の目的「設計経路から backstop raise 不可達」はより強く成立)。→ **確認要**: identity 充足で
  §8.4-3 conform としてよいか + 「6.0」の出所 (wall inner face 7.5 − hx 1.5 = 6.0 の幾何導出か)。
  → ✅ **RESOLVED = §8.10.2**: CONFORM。「6.0」= 訂正 #11 (on-disk 不在の捏造数値、%12 の幾何仮説も
  検証不能と p5 自認 — 出所推定は不採用)。**CONFORM 条件 = same-snapshot 規律 → §2-6a に freeze 化**。
  §8.4-3 訂正 pointer = 授権により %12 追記済 (`65879a8fae`)。
- **Q-3 npz fields の window 意味論** (§8.5 の 8 fields は per-episode 量、collector の発行単位 =
  workload window [done 跨ぎなし・budget 切りあり]): **%12 案 = episode-scoped record を「done が入った
  window」にのみ実値で載せ、done の無い window は全 sentinel** (§2-D 表)。fire_step は episode-相対 RL
  step。supervisor 集計の分母 = done episode 数。→ **conform 確認要** (two-key 時で可、実装は本案で進む)。
  → ✅ **RESOLVED = §8.10.3**: CONFORM + additive 1 点 = supervisor に `windows_total`/`windows_with_done`
  (budget 切り in-flight episode の pin 状態が「見えず消える」ことの集計面可視化) → §2-D に反映。
- **Q-4 per-step check の BrokenSelector** (scene↔task tripwire): %12 案 = per-step check でも
  **BrokenSelector は raise** (構造的 config 異常は quiet-skip すると「silently never fired」класс —
  N7 意味論の継承)。quiet 対象は capture-述語 False のみ。→ conform 確認要 (two-key 時で可)。
  → ✅ **RESOLVED = §8.10.4**: CONFORM (§8.4-6 の raise 3 限定列挙と整合、構造的ゆえ実質初回 1 発)。

**v0.3 追加分 (panel 由来 — Q-6/Q-7 = freeze-blocking、Q-5/Q-8 = bank 前で可)
→ ✅ v0.4 で全 4 項 RESOLVED (裁定 = charter §8.11 `d5bbd18e1b`): Q-5 = GRANT (§8.11.3、pointer 執行済) /
Q-6 = ACCEPT・訂正 #12 (§8.11.1、式 = run_start + K) / **Q-7 = REVISE 採択** (§8.11.2、深さ leg —
%12 の ratify 提案は不採用・測定 legs 5 本は全 ADOPT) / Q-8 = 訂正 #13 + downgrade 批准 (§8.11.4)。
凍結の実体 = §2 (v0.4 反映済)。原文は記録として保持:**

- **Q-5 /pre-check の gate 順序 supersession (CC2-1)**: charter §2-4 は §21.4:763-765 の「/reward-design
  + /pre-check が**実装前**必須」を carry するが、charter §6-3/§8.9 は「prereg → 実装 → probe →
  /pre-check → two-key」を定める (gate② の実績もこの順)。→ **裁定要**: §6-3/§8.9 の順序が本 chunk
  (訓練なし・probe のみ) について §2-4 の配置を supersede する旨の 1 行 pointer を bank (p5 授権)。
- **Q-6 fire anchor の off-by-one 訂正 (CC3-2 + CC6-2、%12 独立再測 CONFIRM)**: 録画は **post-step
  state** を sample (`route_executor.py:1768` 逐語「sample the post-step frame」)、online check は
  label f の **physics step 前**に走る (`newton_route_env.py:1221→:1222`) = check(f) が読むのは録画
  state f−1。offline first-True = state 2427 ⇒ online first-True check = label 2428 ⇒ K=3 で fire =
  label **2430**、fire_step = **243** = G3 latch (242) の**翌 step**。⇒ §8.10.1 凍結値 (2429/242/式
  first_true+(K−1)/「同 step」) は録画規約の trace なしの offline 算術 — **訂正裁定要**: 提案 =
  fire_frame **2430** / fire_step **243** / 式 **`first_true_frame + K`** / §11 は「11 RL step 早発火・
  latch 翌 step」(latch ≺ fire 維持・(B) 独立性不変・hard bar [242,250] 不変)。
- **Q-7 anchor 深度の新実測 = K=3 裁定素材に無かった帰結 (CC3-1、%12 npz 直読 CONFIRM)**: 幾何 trigger
  の weld anchor = fire 時 seat_world (`route_executor.py:792-794`、eq_data[3:6]) ⇒ K=3 では **state
  2429 z = 835.665mm = retention bar (rim 836) の 0.335mm 内側** — onset 発火の anchor 828.653mm
  (margin 7.35mm) から **−7.01mm の意味論 shift** (「達成着座の保持」→「rim 進入直後の保持」)。録画は
  fire 後 ~105f で **7.035mm の追加降下を command** (position-drive vs weld の fight、pin eq = solref
  **default** [`newton_skill_env_base.py:1605-1612`、gripper 4-bar `:2021` の明示 stiffen と対照])。
  素材 §4-(i) は entry margin 0.07mm を出したが anchor 深度・retention margin・fight 帰結は未提示 =
  §8.4-2 (K=3) 裁定の入力に無い。→ **裁定要 (ratify or revise)**: %12 提案 = **K=3 ratify + 測定 legs
  追加** (expected anchor z 凍結 [drift loud] / L-D に pin eq |efc_force| max・release/done 時 seat z・
  retention 述語 fire→done continuity / §11 に shift 宣言) — 実挙動 (weld が押込に負けて深部へ drift
  するか、rim 直下で保持するか) は empirical ⇒ probe が測る。deeper-fire 代替 (K≈55 / z-深度 bar) は
  margin-bar 不採用裁定 (§8.4-2) と衝突するため提案しない。
- **Q-8 文書権限 2 件 (non-blocking、CC2-8 + CC3-4)**: (i) 訂正 #12 候補 = §8.10.4 の「§8.4-6」は
  dangling (§8.4 は項 1-5、raise 3 列挙の実体は本 prereg §2-6) (ii) §8.4-2 の K=3 根拠「数値 wobble
  吸収」は canonical 実測で不支持 (進入は単調 ~0.13mm/frame・flicker ゼロ・81/81 持続 ≥5262f;
  containment-by-identity + same-snapshot が backstop 懸念を既に moot 化) — K=3 自体は flicker 保険
  として維持提案、根拠文の地位は p5 判断。+ **K の妥当性は policy/residual drive 時代に再検証** =
  §12-6 D-b carry へ追加済 (遅い swing-through は K=3 を dwell し得る)。

## §1 claim manifest (pN 条件 1 型)

| 項 | 記録 |
|---|---|
| (d) hunks の著者 | **全 hunk = %12 が本 chunk で新規作成** (adopted 凍結 hunk なし — (a)(b) との相違点)。 |
| 対象 source の pre-state | HEAD `88b7a16681` で clean を実測 (10:3x porcelain): `newton_route_env.py` / `route_executor.py` / `forkb_collector.py` / `forkb_supervisor.py` / `test_route_reward_identity_guards.py` = **全て clean**。 |
| 例外開示 | `route_env_config.py` に**未 commit の comment-only hunk 実在** (obs[60:62] の説明文を interp 意味論へ同期する 2 hunk、logic 変更ゼロ、著者未帰属 = NOT MINE)。**(d) はこの hunk を stage しない** (B2 教訓)。(d) が同 file に K 定数を足す場合は **hunk 単位 stage + staged-diff 照合**で分離 (§6-3)。 |
| claim deadline | 本 doc の bank commit 時刻で固定 (新規著作のみゆえ形式適用)。 |

## §2 freeze (§8 裁定の凍結 — 実装・probe が従う不変量)

**A. trigger 規則 (§8.4 + §8.10.1)**
1. **K = 3、単位 = physics frame** (K = 3 連続 physics frame、§8.10.1 裁定 — route-invariant 設計定数、
   凍結)。定数 home = `route_env_config.py` (route-scope config、bars と同居; §1 の hunk 分離下で追加)。
2. 規則 = **identity body への K-consecutive dwell、fire 条件 = capture ∧ 深さ (§8.11.2 REVISE)**:
   per-frame に **`clip_capture_check(identity body) ∧ (z_B ≤ Z_FIRE_DEPTH_M)`** を評価、連続 True 数が
   K に達した frame で発火。**`Z_FIRE_DEPTH_M = ROUTE_GROOVE_Z + CABLE_RADIUS/2 = 0.831`** (既存定数
   2 本の式・新 literal ゼロ、home = `route_env_config.py` SEAT_* bars と同居)。**非連続で counter
   リセット** (strict consecutive — 深さ leg False も リセット)。first-True 即発火・rim 発火は不採用
   (§8.11.2: eq = 弾性拘束で解放後 anchor 復帰 ⇒ rim anchor では retention margin 0.335mm = G6 sustain
   構造死の解析予測)。⚠**素朴 bar 829 (=groove_z) は 27/81 fire 不能** (producer 静止高 827.7-829.7
   cell 変動 — 「固定深さは固定段と同じ罠」、§8.11.2)。**fire 集合 ⊂ authorizer 受理集合** (深さ leg の
   分だけ z 軸で真に内側 ⇒ §8.10.2 恒真は strict 化して維持)。
3. **fire 対象 = identity body のみ**: `cable[_pin_seat_seg]` の world 位置で評価し、同 body を
   `authorize_clip_pin` へ渡す (§8.1-4、welded ≡ identity by construction)。
4. **fire-once per episode** (witness latch 継承)。**episode 内 re-fire = 不採用確定** (§8.4-4)。
5. **評価配置 = 既存 call site の条件置換** (`_maybe_activate_c1_pin` 本体、呼出位置 **`:1221`** 不動
   [v0.3 訂正: v0.1-2 の「:1222」は off-by-one、%12 実測 — :1221 = 呼出 / :1222 = `_physics_step_all`。
   check-precedes-physics の順序が「frame f の評価が読む state」を定義する = Q-6 の根]。
   `route_c1_pin` flag gate / fire と reward 評価の相対順序 = landed (a)(b) と同一 (§8.4-1)。
   **label 有効性 (CC3-5)**: `fired_at_frame` の route-clock label (`step_f[t]+sub_i`) は**非 held
   world-0 でのみ有効** — hold 下 (W1-B2) では label が凍結する一方 K-dwell は live 幾何を評価し続ける。
   probe は hold を使わない; hold 時代の label 意味論は D-b carry (§12-6) に含める。
6. **非 raise 化**: capture check False = quiet return (dwell リセットのみ)。raise は (i) BrokenSelector
   (structural、§8.10.4 — cache 化後は per-call count assert が担う、§2-6b-(ii)) (ii) authorizer
   backstop (設計経路から不可達 = containment-by-identity、§8.10.2) (iii) **CPU model 不在で flag ON**
   (misconfig fail-loud — **locus = check helper が authorizer `:944-947` の RuntimeError を鏡映**
   [CC2-6]、unit fixture = L-C2) に限る。`NotInAnyRouteClip` は真の bypass 専用に純化 (§8.4-3 + 訂正
   #11 pointer)。**`_last_pin_record` は sentinel record で init** (mjm-None 経路でも §2-D 表の −1
   意味論が成立、CC2-6)。
6a. **same-snapshot 規律 (§8.10.2 CONFORM 条件、load-bearing 凍結)**: K 到達 frame の check が評価した
   **同一の seat_world 値 (同じ bq snapshot)** を `authorize_clip_pin` へ渡す — fire-True ⇒
   authorizer-accept が同関数・同 bar・同入力の**恒真**になる (re-read / 翌 frame 呼びは wobble が
   backstop を設計経路へ戻すため禁止)。two-key 照合対象 + L-C(d)-(vi) の unit leg。
6b. **cache + hoist 設計 (CC3-3 fold — v0.2 §4 の「no mj_forward」×「同一 loop body」非両立の解消)**:
   `clip_geoms_at` は mj_forward を無条件に呼ぶ (`route_executor.py:870`) ため、共有は loop body でなく
   **cached clip set** で実現する: (i) **build-time cache** — model 構築後 1 回、各認可 clip の geom-id
   集合 + y_win を `clip_geoms_at` で解決し保持 (ii) **per-call count assert** — check/authorizer とも
   毎呼出で cached set の `len∈{5,6}` を assert (BrokenSelector 意味論保存 — mjm geom table と body-0
   static geom_xpos は post-build 不変 [MuJoCo]、runtime の count 変化は表現不能ゆえ cached-set assert
   ≡ 再 scan assert) (iii) **mj_forward hoist** — `clip_geoms_at` から mj_forward を呼出側 (authorizer
   `:948` / audit `:987`) へ移し挙動不変、per-frame check は mj_forward ゼロ (cable 側は Newton
   `body_q`、clip 側は cached static — per-frame の CPU mirror 依存を消す) (iv) **containment-by-
   identity の実現形** = same predicate + same bars (rc 定数) + **same cached set** (authorizer も同
   cache を消費)。per-frame cost = 純 predicate 演算のみ (Python geom scan ~100-150 geoms ×2 clips
   ×10 frames/step の常時走行を排除 — CC3 見積 step budget の 5-25% 回避)。

**B. identity (§8.1)**
7. **identity 源 = (B) recording 由来** (`_pin_seat_seg`、per-cell 供給、DAPG residual-on-script 時代)。
   (A) fired-body は不採用 (観測の再死)。identity 無し (`_pin_seat_seg is None`) = trigger 不評価
   (fail-closed、発火ゼロ)。**identity 3 属性は (d) でも不触** ((a)(b) §12 coupling carry)。
8. §21.4:756 固定段文の RE-SUPERSEDE = **反映済** (pointer 追記 `efad9c05b9`、on-disk 確認 10:3x)。

**C. mismatch loud 化 (§8.2)**
9. home = `_clear_c1_pin` の audit 点。3 class: **1** = fired≠∅ ∧ witness=None (bypass 署名) / **2** =
   witness≠None ∧ witness.eq_id ∉ fired (乖離・消滅) / **3** = witness.eq_id ∈ fired ∧ |fired| > 1
   (併走 bypass)。応答 = **loud print + counter (`_pin_mismatch_total`) + episode record flag。
   reward / termination / invalid には配線しない** (凍結)。canonical / probe 期待値 = **0** (>0 = probe FAIL)。

**D. witness run-level provenance (§8.5) — 8 npz fields 名・型凍結 (additive-only、既存 field 不変)**

| field | dtype | 意味 / sentinel |
|---|---|---|
| `pin_fire_step` | int64 scalar | 発火 RL step (**episode-相対**)。−1 = 本 window 内に done した episode の発火なし |
| `pin_fire_frame` | int64 scalar | 発火 physics frame (step_f[t]+sub_i)。−1 = 同上 |
| `pin_eq_id` | int64 scalar | 発火 eq id。−1 = 未発火 |
| `pin_seat_seg` | int64 scalar | identity ordinal (recording 由来)。−1 = identity 無し |
| `pin_anchor_xyz` | float64[3] | 発火 anchor world [m]。(NaN,NaN,NaN) = 未発火 |
| `pin_dwell_count_at_fire` | int64 scalar | 発火時 dwell counter (=K)。−1 = 未発火 |
| `pin_mismatch_class` | int64 scalar | 0=none / 1/2/3 = §8.2 class / **−1 = 本 window 内に reset なし** |
| `pin_audit_verdict_at_reset` | int64 scalar | 1=audit pass・fired≠∅ / 0=audit pass・fired=∅ / **−1 = 本 window 内に reset なし (or mjm 不在)** |

- window 意味論 = §Q-3 案 = **§8.10.3 CONFORM**: done を含む window にのみ episode record を実値記載、
  他は sentinel (record は done と共に travel、部分帰属なし)。**window↔episode = 1:1 (CC6-8)**:
  collector は publish 毎に env done/budget で episode を閉じる (`forkb_collector.py:311` 系の
  end-of-window reset) ⇒ fire-in-A/done-in-B の跨ぎは構造的に不能 — consumer は window-offset field を
  探さなくてよい (fire_step は episode=window 内 RL step)。**順序制約 (CC2-10)**: collector の
  `_last_pin_record` 読取は end-of-window `env.reset()` に**先行**すること (reset は `_clear_c1_pin` を
  再走し record を書換える — done 検出時点の読取が自然に満たすが、凍結として明記)。
- **production-default dormancy 宣言 (CC6-1 fold、v0.1-2 §3 OUT の誤記述の訂正)**: collector 既定では
  trigger は **dormant** — env cfg に `route_c1_pin` 無し (`forkb_collector.py:157-168`) + flag default
  False (`newton_route_env.py:466`) ⇒ 評価すらされず、さらに `--episode-steps` default **230**
  (`forkb_collector.py:124` / supervisor `:174`) < fire 242/243 < done ≈342 ⇒ 仮に flag ON でも既定
  budget の window に fire/done は構造的に入らない。⇒ **既定 production 収集の 8 fields = 全 sentinel・
  summary = fired 0/done 0 が正常** (declared)。有効化 = 訓練時代 config 決定: 既存 env-var
  `ROUTE_C1_PIN=1` 経路 (`:466`、新 CLI 不要 = hard-stop 準拠) + `--episode-steps ≥ ~350` (既存 arg の
  非 default 値)。L-H はこの有効化構成で fired/done window を実走する (§5)。
- **manifest mirror** (集計用 additive keys): `pin_fire_step` / `pin_eq_id` / `pin_mismatch_class`。
- **supervisor 集計** = run 終端 (+ 周期 status) に outbox manifest scan → `pin_fire_summary.json`
  (done episode 数 / fired 数 / fire 率 / fire_step 分布 / mismatch 総数 + **§8.10.3 additive:
  `windows_total` / `windows_with_done`** — budget 切り in-flight episode の pin 状態が記録されない
  事実の集計面可視化 [no-silent-cap])。**未発火 episode = 正常データ**。
- env 側 exposure = `_clear_c1_pin` が clear **前**に per-episode snapshot を `_last_pin_record` (dict)
  に確定 → collector が done 検出時に読む (auto-reset `:1971` を跨いで生存)。

**E. canonical anchors (§8.6、実測凍結 — drift = loud)**
10. offline 幾何: capture-only first-True = frame 2427 (rim、経由値 — 凍結しない) / **fire 条件
    [capture ∧ 深さ] の run_start = frame 2465 (v0.4、%12 再測一致)** / G3 latch = **242** / (a)(b)
    recorded-onset fire = **254** / release: **canonical 定義 = min(grip)<0.5 post-onset = onset+150
    (frame 2694)** 採用、D-6 計器 (onset+54) は併記 assert (§8.6(a) 両定義 hard) / 窓統計 (capture
    述語) = min 99 / p50 116 / p90 153 / max 156 (81/81)・B 窓持続 ≥5262f / **深さ規則の 81-cell 統計
    (§8.11.2 p5 自計測)** = fire-able 81/81・onset−fire ∈ [56,112]f・release−fire ≥206f・bar 以下
    連続 81/81。
11. **凍結 anchor (§8.11.1 訂正 #12 + §8.11.2 REVISE 後の最終形 — v0.4)**: **式 = `fire_label =
    run_start + K`** (run_start = 録画系で fire 条件 [capture ∧ 深さ] が最初に成立した frame)、
    **anchor_state = 録画 [fire_label − 1]** (check(f) は録画 state f−1 を読む — 録画 = post-step
    sample `route_executor.py:1768` × check = pre-step `:1221`)。canonical: **run_start 2465 →
    fire_label 2468 / fire_step 246 / anchor z 830.640mm** (%12 独立再測で全一致)。G3 latch 242 ≺
    fire 246 = **+4 step の実 gap**。**hard bar: canonical `fire_step ∈ [242, 250]` 維持** (246 ✓)。
    fire_label/anchor の drift = **loud** ([RESULT] 記録・two-key 判定)。**初回 live probe 実測値を
    [RESULT] に記録し standing anchor 化**。rim 規則の経由値 (2429/2430/242/243) は凍結しない。
    ⭐**records-fix (§8.13 裁定、2026-07-17、bank `16dde1ff5c`)**: **offline `fire_label = run_start + K
    = 2468` は RETIRE** — live は cable 再シム (byte-replay でない) ゆえ npz-index と route-clock は別
    クロック (npz z@frame2462 = 831.32mm > 深さ bar vs live anchor 830.71mm < bar、offset 6 = live-
    physics 差)。**live standing anchor = fire_label 2462 / fire_step 246 / anchor z 830.71mm** (cell_x0_y0、
    ep1≡ep2 決定的)。hard bar = `fire_step ∈ [242,250]` + anchor band + **latch ≺ fire** + retention のみ、
    **fire_label は記録・loud (gate でない、§8.13)**。以後 drift は 2462 に対し測る。
11a. **anchor 深度の凍結 (§8.11.2、v0.4 確定)**: canonical 期待 **anchor z = 830.640mm**、81-cell band
    **[830.604, 830.899]** (drift = loud) — **retention margin ≥ 5.10mm** (rim 発火案の 0.335mm から
    回復、§11 で shift 宣言)。fire 後の残押込 = charter ≈1.8mm / %12 canonical 再測 **1.99-2.01mm**
    (anchor→onset-era rest / →min — 桁一致・方法差、確定値 = L-D 実測)。fight は微小化したが
    **efc-force leg は維持** (L-D)。release−fire **≥ 206f** (canonical 226)・bar 以下連続 81/81
    (re-arm 曖昧性なし)。**DR carry** = §12-8。
12. **宣言 delta (L-F2 型、(a)(b) landed tree 対比)**: flag-ON canonical で fire 254 → §11 の値へ移動
    + それに因る fire 後物理 delta。**latch 列 (G3=242) は不変** (§8.1-3(i) の実証対象)。flag-OFF =
    **delta ゼロ (byte 一致)** — trigger は flag gate 内で完全に不活性 ((a)(b) と役割反転: あちらは
    flag-OFF が宣言 delta、こちらは flag-OFF が byte 恒等)。
13. **(iv) 繰延 (§8.8、no-silent-cap)**: 摂動 cell の latch 列検証は本 gate に不要 (窓統計 81/81 +
    p5 再計算で足りる、裁定済)。live 検証は nominal cell probe (G-F2 内) + **DoD-7 後 cell-2 追補
    (§12-5 carry) へ明示繰延** — [RESULT] に恒久記載 (§10)。

## §3 scope (IN / OUT)

**IN (bundle = 単一 atomic commit)**:
1. `thread_isaac_lab/envs/newton_route_env.py` — `_maybe_activate_c1_pin` **条件置換** (onset 比較 →
   K-dwell 幾何規則、§2-A) + dwell counter state (`_c1_pin_dwell`、init/reset) + `_clear_c1_pin` に
   mismatch 3-class 判定 + loud print + counter + `_last_pin_record` snapshot (clear 前、§2-C/D)。
2. `thread_isaac_lab/envs/route_executor.py` — **非 raise capture check helper** (`clip_capture_check`
   型): `authorize_clip_pin` の per-clip loop body を共有抽出し、authorizer 自身も同 helper 経由に
   refactor (**containment-by-identity の機構化**、§Q-2)。BrokenSelector は両経路で raise (§Q-4)。
3. `thread_isaac_lab/envs/route_env_config.py` — K 定数 1 hunk のみ (**hunk 単位 stage、§1 開示の
   comment hunk は stage しない**)。
4. `thread_isaac_lab/scripts/forkb_collector.py` — 8 npz fields + manifest mirror 3 keys (§2-D)。
5. `thread_isaac_lab/scripts/forkb_supervisor.py` — `pin_fire_summary.json` 集計 (§2-D)。
6. `thread_isaac_lab/scripts/test_route_reward_identity_guards.py` — 新 unit tests (§5) +
   既存 17 test 名前列挙固定で全 PASS 維持。
7. probe 新規 = `eval_runs/.../pin_d_trigger_probe.py` (+ `_result.json`) — §5 **L-D/L-D2/L-E/L-F
   実行体** (L-E 追加 = CC2-3)。
8. **L-H 実行体 = collector 実走、invocation 逐語凍結** (CC6-1 discharge + pN B4/R-B4。作業 dir = repo
   root、outbox 親 = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/`。bundle tree = 実装 landed
   前は隔離 integration worktree、後は landed commit の worktree):
   - **Run A (fired/done)**:
     `CUDA_VISIBLE_DEVICES=0 ROUTE_C1_PIN=1 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_collector.py --outbox eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_da_lh_runA --proc-index 0 --base-seed 20260717 --episodes 2 --episode-steps 360 --drive-mode feedforward`
     → 期待 = **windows_total 2 / windows_with_done 2**、両窓 fired (fire_step 246)・8 fields 実値。
   - **Run B (budget 切り対照、flag ON 維持 = flag-OFF と交絡させない)**:
     `CUDA_VISIBLE_DEVICES=0 ROUTE_C1_PIN=1 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_collector.py --outbox eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_da_lh_runB --proc-index 0 --base-seed 20260717 --episodes 1 --episode-steps 230 --drive-mode feedforward`
     → 期待 = **windows_total 1 / windows_with_done 0**・全 sentinel。
   - **Run C (L-H2 対、flag-OFF — ROUTE_C1_PIN 非設定)**: HEAD 側 = worktree @ `88b7a16681`、bundle 側
     = landed worktree、**同一 command** (path 部のみ各 worktree):
     `CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_collector.py --outbox <各側>/pin_da_lh_runC_{head,bundle} --proc-index 0 --base-seed 20260717 --episodes 1 --episode-steps 60 --drive-mode feedforward`
     → §5 L-H2 の項目別 bar で比較。
   - **summary 検証**: supervisor の集計 code path (関数レベル) を各 outbox root に対し実行 (scan root
     = 上記 3 outbox、期待値 = 各 Run 行; process 起動系 = E0 covered infra で本 leg 対象外)。
9. 本 doc + [RESULT] 追記。

**OUT**: 残差/IK drive 分岐 (`newton_route_env.py:1249` 系) への call site 追加 = **D-b window gate 項目
へ明示繰延** (declared limit — **正確な現状 [v0.3 訂正、CC6-1 + %12 実測]: call site `:1221` を host
するのは FF branch のみ** (`_route_drive_ff = (drive_mode=="feedforward")`、`:496`; collector default =
feedforward `forkb_collector.py:125` だが **`ik_chord` 選択時は call site 自体が不在** = trigger 完全
不評価)。さらに production 既定では FF でも trigger は dormant (flag OFF + budget 230、§2-D 宣言) —
「既定で働く」とは主張しない。有効化 = 訓練時代 config 決定; policy-drive 残差時代・ik_chord の呼出
配置はその gate で) / STEP 9 release 述語 / obs-space 変更 / `task_config.py` / S8 warp 系 / B4 prereg
への Q6 cite 転記 (= B4 起草時 %12、§8.7) / route_env_config.py の未帰属 comment hunk / 訓練起動 /
demos 再生成。

## §4 実装設計 (条件置換の形 — 実装は panel 後)

```python
# newton_route_env.py — _maybe_activate_c1_pin 本体の置換 (呼出位置・引数・flag gate 不変)
if not self._route_c1_pin or self._c1_pin_witness is not None or self._pin_seat_seg is None:
    return                                  # identity 無し = fail-closed 不評価 (§2-7)
import route_executor as rex
bq = self._state_0.body_q.numpy()
seat_body = int(self._cable_bodies[0][int(self._pin_seat_seg)])   # identity body のみ (§2-3)
seat_world = bq[seat_body, :3].copy()       # ⭐single snapshot (§2-6a): check と authorizer は
captured = rex.clip_capture_check(self._solver, seat_world)  # ...同一値を読む (fire-True⇒accept 恒真)
if not (captured and seat_world[2] <= rc.Z_FIRE_DEPTH_M):    # fire = capture ∧ 深さ (§8.11.2 REVISE —
    self._c1_pin_dwell = 0                  # ...深さは fire 時刻条件で authorizer volume の再定義でない)
    return                                  # 非 raise (BrokenSelector 除く、§8.10.4) / strict consecutive
self._c1_pin_dwell += 1
if self._c1_pin_dwell < rc.PIN_TRIGGER_DWELL_K:  # K = 3 physics frame (§8.10.1)
    return
self._c1_pin_witness = rex.authorize_clip_pin(self._solver, seat_body, seat_world)  # same-snapshot
self._c1_pin_witness["fired_at_frame"] = int(step_f[t]) + int(sub_i)   # 従前 bookkeeping 継承
self._c1_pin_witness["fire_step"] = int(self.episode_length_buf[0].item())  # episode-相対 (§2-D)
self._c1_pin_witness["dwell_count"] = int(self._c1_pin_dwell)
```

- `clip_capture_check(solver, seat_world) -> bool` (**v0.3 = §2-6b の cache+hoist 形**): check /
  authorizer / audit は **同一の build-time cached clip set (geom-ids + y_win) + 同一 predicate + 同一
  rc bars** を消費 — containment-by-identity は「同一 loop body」でなく「同一 cached 幾何 + 同一述語」
  で実現 (`clip_geoms_at` の mj_forward `:870` を per-frame に持ち込まない)。per-call `len∈{5,6}`
  assert は cached set 上で毎回走る (BrokenSelector 意味論保存、§2-6b-(ii))。
- **mj_forward hoist**: `clip_geoms_at` から mj_forward を呼出側 (authorizer/audit) へ移す (挙動不変)。
  per-frame check は **mj_forward ゼロ** — cable 側 = Newton `_state_0.body_q`、clip 側 = cached
  static。seat_world の空間混成は既存 authorize path と同一 (前例踏襲)。
- **audit_pin_anchors の loop は共有 helper に統合しない** (CC6-6): broken-selector 時の挙動が設計上
  異なる (audit = `continue` `:1007` [anchor 判定のみ] / authorizer = raise `:954`) — 「親切な統合」は
  未宣言の意味論変更になる。**audit は cache を消費せず従前の live rescan を維持** (mj_forward は自
  call site に hoist、挙動不変) — audit = who-wrote-it-agnostic の独立証拠計器であり、fire 経路の
  cache を信用しない independence が設計価値。cache 共有 = check + authorizer の 2 者のみ (identity)。
- `_clear_c1_pin` 追記 (clear 手順・guard 順・audit-then-clear = (a)(b) 形のまま): audit 返却 `fired`
  と witness から mismatch class 判定 (§2-C) → `_last_pin_record` snapshot → 既存 clear → witness None
  → `_c1_pin_dwell = 0`。
- collector: done 検出 window で `env._last_pin_record` → 8 fields、他 window = sentinel (§2-D)。

## §5 acceptance legs (事前登録 — 実測は [RESULT] へ。bypass 系は (a)(b) legs 継承)

| leg | 内容 | PASS bar |
|---|---|---|
| L-A | **before (B3+R-B3 = tests-only patch 規律、全項事前凍結)**: baseline = **`88b7a16681`** (§1 の porcelain 実測 commit、逐語凍結)。**手順**: tests-only patch を production fix **着手前**に作成・**patch sha256 を [RESULT] に記録** → 同一 patch を (i) 隔離 worktree @ `88b7a16681` (ii) landed tree の両方へ適用 → (i) で **下表 FAIL-class IDs が各 expected signature で FAIL** (逐語記録)・(ii) で全 PASS。**fixture/import/collection error は FAIL として不受理** (test-body 到達必須)。invariance-guard class (下表) は両側 PASS が bar。+ (a)(b) probe の onset fire 254 再確認 (L-F2 baseline 凍結) | FAIL-class: baseline FAIL (signature 一致) ∧ landed PASS / guard-class: 両側 PASS |
| L-B | **after**: landed commit の隔離 worktree で既存 17 test (名前列挙 = (a)(b) §5 L-B + clear×4 + raise-branch×3) + 新規 test 全 PASS | 全 PASS、exit 0 (pN binding) |
| L-C(d) | unit: dwell 論理 — (i) K−1 連続 True → False で counter リセット・発火なし (ii) K 連続 True → 発火 1 回のみ (iii) flag-OFF → 不評価 (iv) identity None → 不評価 (v) 発火対象 = identity body 引数一致 (vi) **same-snapshot 摂動型 (§2-6a、CC6-3 re-spec — 値照合単独は fail 不能)**: real `_maybe_activate_c1_pin` 実行上で double が check/authorizer 両引数を記録し、**K 到達 check の return 直後に seat body の位置 source を摂動 (毒殺)** → authorizer 受領値 = **摂動前の K 到達 snapshot 値**を assert (re-read 実装なら毒値を受けて FAIL する = 計器が両実装を判別する) + 可能なら配列 object identity も assert (vii) **深さ leg (§8.11.2)**: capture True ∧ z > Z_FIRE_DEPTH_M → 発火なし・dwell リセット / z ≤ bar で条件成立 | 7/7 |
| L-C2(d) | unit: 非 raise — 圏外座標で per-step check を N 回呼んでも raise ゼロ・発火ゼロ / BrokenSelector fixture は check でも raise (cached-set count assert 経由、§2-6b) / **mjm-None + flag ON → RuntimeError fixture (§2-6-iii、CC2-6)** / authorizer refactor 後の N1-N7 意味論不変 (既存 controls 再走) + **`NotInAnyRouteClip` の per-clip reasons payload 内容 assert (CC6-7 — 型/accept-reject のみの既存 controls では reasons 削落 regression が素通り)** | 全一致 |
| L-C3-5 | **bypass 系継承**: (a)(b) L-C3 (圏外 bypass = RAISE-before-clear) / L-C4 (圏内 bypass = clear) / L-C5 (複数候補 3 分岐) を再走 | (a)(b) bar のまま全 PASS |
| L-I | mismatch 3-class fixtures: 圏内 bypass+witness None → class 1 検出 + loud + **非 terminal** + record flag / witness 有 + fired から消滅 → class 2 / witness 有 + 併走 → class 3。canonical run の mismatch = 0 | 3 fixture 検出 + canonical 0 |
| L-D(d) | probe canonical (FF、`route_c1_pin=ON`、INIT_XY_NOISE=0、nominal cell): ep1 幾何 fire → audit PASS → reset clear → ep2 refire。**二値 hard bars (pN B5、§8.13 是正済)**: fire_step ∈ [242, 250] (両 ep) / **anchor z ∈ [830.604, 830.899] (hard band = 81-cell 実測 band)** / **latch ≺ fire (G3 latch < fire_step)** / dwell == K / **retention 述語 (z<836 系) fire→done continuity** / reset clear + witness None + ep2 refire。⭐**fire_label は hard bar でない (§8.13)**: **record/loud のみ・live standing anchor = 2462** (offline 2468 RETIRE — exact-frame は live 再シムゆえ原理的不成立)。fire ≺ release 両定義 (D-6 +54 / min-grip +150) / pre-fire 区間 raise 数 = 0 は characterization/記録 ([RESULT])。**characterization-only (記録のみ・PASS 判定に不使用と宣言、pN B5)**: pin eq \|efc_force\| max over [fire, onset+150] / seat z @ release・@ done / 残押込実測 | hard bars 全 PASS + characterization 記録 |
| L-D2(d) | ep1≡ep2 event timeline 完全一致 (fire step / G latch 列 [98,146,242,242,−,−] / done / term) — **hard**。reward per-step trace diff = **characterization-only 記録** (期待 ≈0、PASS 判定に不使用 — pN B5 二値化) | timeline 完全一致 (hard) |
| L-E | reset clear 前後 eq_active の fired 外対称差 = ∅ (継承) | = ∅ |
| L-F1(d) | **flag-OFF byte 恒等**: bundle vs baseline (下記 pin)、flag-OFF 固定長 replay で phys/obs/reward/done 全 byte 一致。**宣言済みの残余目的 (CC6-6)**: flag-OFF は refactored authorizer を実行しない (fire 時のみ到達) ため本 leg は trigger 論理に非感応 — その価値 = **out-of-scope 編集の tripwire** (audit 経路 [reset 毎実行] と env 本体の非宣言変更を捕まえる) | byte 一致 |
| L-F2(d) | **flag-ON 宣言 delta**: bundle vs baseline、flag-ON canonical で (i) fire 254 → §2-11 (Q-6 裁定値) へ移動 (ii) **G3 latch 242 不変** (iii) 分岐点 = fire 時刻差の初出 frame、以降の物理 delta は fire 起因として宣言 (**anchor 深度 shift §11 込み**) (iv) **宣言外の面に delta ゼロ** (§S4.5 付帯: 宣言外 delta ≠ 0 → 追補 re-open)。**baseline 3 点 pin (CC2-2、(a)(b) §5 L-F2 の pin 復元)**: 明示 commit hash (**L-A 実行時 HEAD を [RESULT] に記録・以後固定**) + recording sha (golden 5f1c3f92) + flag/config 全列挙 | 測定が §2-12 宣言と一致 (判定 = two-key) |
| L-H | fields (**実行体 = §3-8 Run A/B、exact command 固定済**): Run A done 窓 ×2 = 8 fields 実値・env ground truth 一致・fire_step 246 / Run B = windows_total 1・with_done 0・全 sentinel (budget cutoff 分離、flag ON 維持) / manifest mirror / summary 集計一致 (**`windows_total`/`windows_with_done` 込み**)。dtype/名 = §2-D 表と byte 一致 | 全一致 |
| L-H2 | **既存 artifact 面の不変 (CC6-4 + pN B2/R-B2 項目別 bar)**: §3-8 Run C (HEAD vs bundle、同 seed・flag-OFF・小 budget) — (i) **旧 9 arrays** (o/o_next/a_raw/a_executed/r_paid/done/time_out/invalid_mask/cable_traj) = **byte 一致** (ii) **期待一致 manifest keys** {process_index, derived_seed, episode_idx, n_steps, termination_reason, truncated_by, invalid_any, source, drive_mode, sec_S_exposure, **env_fingerprint_sha**} = **値一致** (R-B2: fingerprint = env-var key→値 map の hash [collector :195/:273-274、closure sha でない] — bundle は新 env-key read を足さず Run C は同 env ⇒ 一致が正、**元 map equality も併 assert**) (iii) **期待差分 keys = {code_sha, sha256} のみ** (source 変更 / 8 arrays 追加で必然差分 — 各版で各自の正しい hash であることを assert) (iv) **pid = self-consistency のみ** (各 run の manifest.pid == proc_meta.pid ∧ 正整数 — cross-run の一致/差分は OS 再利用のため不問) (v) **closure_sha256 = 各版 self-consistency** (proc_meta.closure_sha256 の各 entry == その tree の実 file sha) (vi) **additions = npz 8 / manifest 3 の exact set** (過不足ゼロ) | (i)-(vi) 全成立 |
| L-G | post-land: 隔離 worktree で pre-commit 13-path 型 sweep、autoformat 残渣ゼロ (継承手順) | 残渣ゼロ |

**probe cell 制約**: G-F2 fold-7 guard 不触 — nominal cell (x0_y0) のみ。cell-2 = §12-5 carry (DoD-7 後
L-D/L-D2 同型追補、それまで non-nominal/multi-cell の reward-valid・training-ready 主張禁止)。

### §5a L-A 凍結 test-ID 表 (R-B3 — production fix 着手前に本表で固定。追加 test が実装中に生じた場合は
[RESULT] に同形式で追記・分類し、FAIL-class は baseline 再走で signature を記録する)

**FAIL-class (新機構 — baseline `88b7a16681` で expected signature FAIL ∧ landed PASS):**

| test ID | expected baseline failure (type + message substring) |
|---|---|
| `test_pin_da_capture_check_exists_and_shares_cache` | AttributeError, substring `clip_capture_check` (route_executor に helper 不在) |
| `test_pin_da_dwell_reset_on_gap` | AttributeError, substring `PIN_TRIGGER_DWELL_K` (route_env_config に定数不在) |
| `test_pin_da_fire_once_at_k_consecutive` | AttributeError, substring `clip_capture_check` (monkeypatch setattr が不在 attr で fail) |
| `test_pin_da_depth_leg_gates_fire` | AttributeError, substring `Z_FIRE_DEPTH_M` |
| `test_pin_da_identity_none_no_eval` | AttributeError, substring `_c1_pin_dwell` (dwell state 不在) |
| `test_pin_da_fire_target_is_identity_body` | AttributeError, substring `clip_capture_check` |
| `test_pin_da_same_snapshot_poison` | AttributeError, substring `clip_capture_check` |
| `test_pin_da_check_quiet_outside_volume` | AttributeError, substring `clip_capture_check` |
| `test_pin_da_broken_selector_raises_in_check` | AttributeError, substring `clip_capture_check` |
| `test_pin_da_mjm_none_flag_on_raises` | Failed (pytest.raises), substring `DID NOT RAISE` (baseline に fail-loud 分岐なし) |
| `test_pin_da_mismatch_class_fixtures` (3 case parametrize) | AttributeError, substring `_last_pin_record` (record 機構不在) |

**invariance-guard class (refactor 退行防止 — baseline/landed 両側 PASS が bar):**

| test ID | 守る不変条件 |
|---|---|
| `test_pin_da_n1n7_semantics_unchanged` | authorizer refactor 後の N1-N7 意味論 (既存 controls 意味論の unit 化) |
| `test_pin_da_reasons_payload_content` | `NotInAnyRouteClip` の per-clip reasons 内容 (CC6-7 — baseline でも成立している既存挙動) |
| `test_pin_da_audit_independent_rescan` | audit_pin_anchors が cache 非依存の live rescan のまま (§2-6b) — baseline では cache 自体不在ゆえ trivially PASS、landed で意味を持つ |

## §6 landing protocol ((a)(b) §6 継承 + 本 chunk 固有)

1. 実装 + pre-land legs (L-A/L-C/L-C2/L-C3-5/L-I/L-D/L-D2/L-E/L-F1/L-F2/L-H/L-H2) PASS。
1a. **pre-commit full-hook 手順 (pN B5/R-B5 — AGENTS.md「hook は commit 前」+ shared dirty tree 回避、
   invocation 逐語)**: 隔離 integration worktree @ HEAD に bundle 変更を適用 → worktree 内で
   **`VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -f` 1 回目** (≡ `pre_commit run --all-files`
   [CLI format.py `command_format` 実測]; VIRTUAL_ENV 明示 = worktree venv fallback 死の既知 trap 回避、
   bare `pre-commit` は staged-only 既定で非同値) → hook rewrite を review・bundle へ fold →
   **同 command 2 回目 = 全 Passed** → clean 状態を shared tree の staging へ転写。
   L-G (post-land fresh worktree 再確認) は残す。
2. `git add` = 一括 1 回、§3 IN のみ。**`route_env_config.py` は hunk 単位 stage** (K 定数 hunk のみ、
   §1 開示 hunk 除外)。
3. **staged-hunk 検査 (hard step)**: `git diff --cached --stat` + per-file hunk 列挙 ↔ §3 IN 対称差 = ∅。
   route_env_config staged diff に comment hunk が**混入していないこと**を diff text で確認。
4. 単一 atomic commit (explicit-path)。`--no-verify` 禁止 (記録付き正当化なしに)。**aggregate staged
   diff sha を [RESULT] に land 前記録** (CC2-11 — (a)(b) §6-3 の provenance parity)。
5. commit 後: 隔離 worktree @ landed commit で L-B + L-G。
6. push = Rs 提案のみ (standing)。

## §7 prior-art guard (層4、10:47 実行 = BLOCKER_CONTEXT_FOUND → discharge)

`check_thread_vault_prior_art.sh --fail-on-blocker pin trigger capture dwell fire geometric` の hit =
(i) r2a_track_a (2026-05-2x) kinematic finger pose-pin 系 — **charter §5 で discharge 済と同根**: r2a の
'pin' = 禁止 kinematic-attachment class、本件 = clip-retention pin = RS71 §0 INVARIANT #5 の唯一の認可
例外 + Rs 逐語「クリップのみ」(LEDGER:57)。(d) は認可済 authorizer path への **trigger 時刻の条件置換**
のみ、新 kinematic 例外を作らない。(ii) C8U payload-collection package の 'capture/dwell' hit = 一般語
一致 (single-arm DISCARDED track の payload schema 文書、機構無関係)。新 directive = charter §8 全裁定
(bank `2b8ed62366`) + Rs「prereg チャンクに着手」(2026-07-17 10:3x)。**charter §5 の転記条項を継承**:
「active-at-completion ≠ product success」= transfer 境界注記として本設計に固定 (**v0.5 訂正 [pN B1]:
本 chunk (d-a) は training-block を解除しない — 解除 = (d) 全体 two-key + cell-2 [拘束①]; transfer
主張はさらにその外**)。

## §8 gate 状態

| gate | 状態 |
|---|---|
| [L-TRIAGE] | **L3** (charter :4 self=auto — reward/env 意味論 + diff keyword [reward/fire/success 系]) |
| [DESIGN-GATE] | /reward-design 4 artifacts = 素材 v0.2 (i)-(iv) DELIVERED (charter §6-1 対応) + p5 全 Q + §Q 裁定 banked (`2b8ed62366` + `65879a8fae`)。**/pre-check = 実装後・two-key 前** (banked 手順 §8.9 の位置) |
| [VERIFY] panel | **完了 (v0.2 対象、fold = v0.3 → §Q-5..8 裁定 fold = v0.4)** — CC2 NON-BLOCK / CC3 BLOCK / CC6 BLOCK → CC1 全 ACCEPT + %12 独立再測 → v0.3 修正 + §8.11 裁定 (Q-7 REVISE 込) で **全 discharge** (§9)。(v0.1 への初回 panel = API 上限 abort・finding ゼロ、§0) |
| pre-bank two-key | **p5 設計軸 = v0.4 CONFORM PASS (§8.12 bank `6cbbbd0066`)** / **pN evidence 軸 = HOLD B1-B5 → v0.5 fold (§0) → re-readback 待ち**。bank (= claim deadline) は pN readback PASS 後 |
| [RULE-CHECK] stage2 | [CHANGE] (実装 session) 直前に実行・出力貼付 |
| post-land two-key | p5 (設計軸 bar = same-snapshot 毒殺 leg・anchor drift・宣言外 delta ゼロ [§8.12]) + pN (evidence 軸: legs 実測) — land 後 |

## §9 [VERIFY] panel OUTCOME (v0.2 に対し実施、fold = v0.3 / 2026-07-17 11:47)

| lens | verdict | 主要 finding → 処置 (CC1 = 全 ACCEPT) |
|---|---|---|
| CC2 correctness | NON-BLOCK (MAJ3/MIN5/ref3) | /pre-check 順序矛盾 → **§Q-5** / L-F baseline 可動 HEAD → **3 点 pin 復元 (L-F2)** / L-H・L-E 実行体未指名 → §3-7/8 / call site :1222→:1221 (%12 実測確認) → §2-5 / ±1 規約 → Q-6 に合流 / raise-(iii) locus+fixture → §2-6/L-C2 / §8.2-3 re-open carry → §12 / §8.10.4 dangling cite → **§Q-8** / §12-4 単位 → §12 / 露出順序 → §2-D / staged sha → §6-4。A-F check: freeze 完全性・leg 反証可能性・数値整合・claim manifest (porcelain 独立照合)・landing protocol・§Q fold 忠実性 = PASS 系 |
| CC3 physics | **BLOCK** (MAJ3/MIN1/ref1/CLEAN2) | **anchor 深度** (rim 直下 835.665 vs onset 828.653、7mm push fight、eq solref default — %12 npz 直読 CONFIRM) → **§Q-7 + §2-11a + L-D 追加 legs + §11 宣言** / **off-by-one** (録画 post-step vs check pre-step — %12 :1768/:1221 CONFIRM) → **§Q-6** / **§4 自己矛盾** (clip_geoms_at の mj_forward :870 — %12 CONFIRM) + cost 未計上 → **§2-6b cache+hoist freeze** / K=3 根拠不支持 (K 維持・根拠地位 = §Q-8) + D-b carry → §12-6 / held-world label → §2-5 注記。CLEAN: radius 二重計上なし・class-2 偽陽性経路なし |
| CC6 NHA | **BLOCK** (CRIT1/MAJ3/MIN3/ref2) | **CRIT: §3 OUT「収集で働く」= as-configured 偽** (flag OFF default :466 / cfg に pin key 無 :157-168 / budget 230 :124 — %12 全 CONFIRM + ik_chord では call site 不在 :496 追加実測) → **§3 OUT 書換 + §2-D dormancy 宣言 + L-H vehicle** / same-snapshot leg fail 不能 → **L-C(d)-(vi) 摂動型 re-spec** / additive-only bar の測定 leg 欠 → **L-H2 新設** / ±1 → Q-6 / §11 artifact 面 → §11 追記 / L-F1 tautology → 残余目的宣言 / reasons 未 assert → L-C2。attack N1 (E0 determinism pin) = dissolve (same-code 決定論のみ・D1 :38 additive 許容)・N2(a) 繰延 = charter 適合・N6 算術 = 検証済 |

**CC1 裁定記録**: blocking 3 系統の premise は全て %12 独立再測で CONFIRM (§0 v0.3)。discharge = 本 v0.3
修正 + §Q-5..8 (p5)。panel の CLEAN 所見 (radius/class-2/N1/N2(a)/N6) は leg 設計の根拠として §5 に反映。

**pre-bank two-key 経過 (v0.5 追記)**:
| 鍵 | verdict | 処置 |
|---|---|---|
| p5 設計軸 (§8.12、v0.4 対象) | **CONFORM — PASS** (全 freeze = §8 裁定一致・凍結値三者一致・bar 超過 4 点明記) | 注記① wrong-clip 宣言 → §11 fold / 注記② 残押込 1.987 (p5 丸め自認) / 授権 #12 pointer → 執行済 `6cbbbd0066` |
| pN evidence 軸 (pre-bank、v0.4 対象) | **HOLD (B1 CRIT + B2-B5 MAJ)** | 全 ACCEPT + premise 独立再測 CONFIRM → v0.5 fold: B1 = (d-a) scope 訂正 + 拘束① 延長 + §7/§11 訂正 / B2 = L-H2 項目別 bar / B3 = L-A tests-only 規律 / B4 = L-H 3-run exact command / B5 = L-D/L-D2 二値化 + §6-1a full-hook 手順 |
| pN re-readback (v0.5 対象、12:4x) | **HOLD 継続 — B1 CLOSE + 残差 R-B2..R-B5** (records/executability、設計再 open なし) | v0.6 fold (§0): R-B2 = L-H2 期待差分 {code_sha, sha256} 縮小・fingerprint 期待一致化・pid/closure self-consistency / R-B3 = baseline 逐語凍結 + §5a test-ID 表 / R-B4 = §3-8 invocation 逐語 / R-B5 = §6-1a exact command |
| p5 §S4.7 (B1 の解釈裁定、12:48) | **「(d)」= (d-a)+(d-b) RATIFY** (bank `e20d076912`) | 拘束① 正式化 + charter §4-5/§8.12 pointer 執行 — B1 formal CLOSE |
| **pN 第 3 readback (v0.6 対象、13:0x)** | ✅ **CONCUR / PASS-CLOSE — pre-bank HOLD LIFT・bank GO** (1-5 全照合: B1 formal CLOSE / R-B2..R-B5 CLOSE、collector :195/:273-275・CLI format.py 実測照合込) | bank = claim deadline 実行。**執行時義務 (bank blocker でない)**: Run A/B/C の各 outbox = fresh/non-existing を assert + `<各側>` 具体化後 command を [RESULT] に逐語記録。**scope 注記**: 本 PASS = pre-bank 鍵のみ — 実装・legs・/pre-check・land 後 two-key は未実施、(d-a) CLOSE でも training-ready/reward-valid 不解除 |

## §10 [RESULT] (legs 実測 — 実装 session で追記)

- **(iv) 繰延の恒久記載 (§8.8-4 no-silent-cap)**: 摂動 cell の latch 列は本 gate で検証しない (窓統計
  81/81 + p5 独立再計算で裁定済)。live 検証 = nominal cell probe のみ (G-F2 guard 内)。**cell-2
  (x-20_y-15) の L-D/L-D2 同型追補 = DoD-7 後必須 (§12-5 carry)、完了まで non-nominal/multi-cell の
  reward-valid・training-ready 主張禁止。**
- **執行時義務の事前登録 (pN 第 3 readback、13:0x)**: L-H Run A/B/C 実行時に (i) 各 outbox が
  fresh/non-existing であることを assert (ii) `<各側>` メタ変数を具体化した command を本節に逐語記録。
- **claim deadline = 本 doc の bank commit** (pN PASS-CLOSE 後の bank — hash は git が記録)。

### [RESULT] legs 実測 (2026-07-17 実装 chunk、cell_x0_y0 nominal / cuda:0)

**bundle 6 files (未 commit、working tree)**: route_env_config (K/depth 定数) / route_executor (mj_forward hoist + `clip_capture_check` + `_clip_capture_cache` + authorizer refactor) / newton_route_env (K-dwell trigger + mismatch 3-class + record) / forkb_collector (8 npz + 3 manifest mirror) / forkb_supervisor (`pin_fire_summary` + windows_total/with_done) / test (14 新 tests)。probe = `pin_d_trigger_probe.py` 新規。

- **L-A (tests-only patch、R-B3)** = **PASS**。patch sha256 `cc366caa7d571538be45ef15e72d53528e06f883877e474e99bf3e9de5510724`。baseline = `88b7a16681` (source == HEAD 実測、doc-only commits since)。隔離 worktree で pytest: **11 FAIL-class 全 FAIL ∧ 20 PASS (既存 17 + 不変 guard 3)**、landed tree = 31 PASS。実測 signature (§5a 表への追補 — 予測と差異は actual を採用): capture_check→AssertionError"must exist" / dwell_reset→AttributeError`PIN_TRIGGER_DWELL_K` / depth→AttributeError`Z_FIRE_DEPTH_M` / fire_once・identity_none・target・poison・quiet・broken_selector・mjm_none→AttributeError`clip_capture_check` / mismatch→AttributeError`_pin_mismatch_class`。全 test-body 到達 (collection/import error ゼロ)。
- **L-B (after)** = **PASS**。landed で既存 17 + 新 14 = **31 PASS** (pytest exit 0 3.99s + standalone main() exit 0)。
- **L-C(d)/L-C2/L-I (unit)** = **PASS** (14 新 tests: dwell reset / fire-once@K / depth gate / identity None / target=identity body / same-snapshot 毒殺 / quiet outside / broken-selector raise / mjm-None raise / mismatch 1/2/3 / N1-N7 predicate 不変 / reasons payload / audit cache-independence)。
- **L-C2 controls (authorizer refactor 不変性)** = **PASS 14/14** (`authorize_clip_pin_controls.py` 再走: bars lat=3.50/z=821-836/y_win=15.0mm・geoms C1=5 C2=6 = refactor 前と一致 = containment-by-identity 確認)。**L-C3-5 (bypass 継承)** = pending (`pin_ab_lifecycle_probe.py --bypass` 再走で、extended `_clear_c1_pin` の class-1 mismatch print 込み検証)。
- **L-D(d)** = ✅**PASS (§8.13 是正後、charter bank `16dde1ff5c`)**。ep1≡ep2 決定的、全 check True: **fire_step 246 ✓ ∈[242,250] / anchor z 830.71mm ✓ ∈[830.604,830.899] / latch ≺ fire ✓ (G3 242 < 246) / dwell 3 ✓ / eq_active 1 / audit PASS / retention max 831.07mm < 836 ✓ / reset cleared + witness None ✓ / ep2 refire ✓**。**fire_label = 2462 = live standing anchor (record/loud non-gate、§8.13)** — offline 2468 RETIRE (live 再シムゆえ exact-frame 原理的不成立: npz z@2462=831.32mm > 深さ bar vs live 830.71mm < bar = live-physics offset)。⭐**深さ leg REVISE を live が裏書き** (retention 831.07 < rim 836、margin ~4.9mm — rim 発火なら G6-death を示したはず)。probe PASS 論理是正 (fire_label exact→standing-anchor-drift + latch≺fire) → 再走 L-D=True 確認。result = `pin_d_trigger_probe_result_cell_x0_y0.json`。
- **L-D2(d)** = **PASS (hard timeline)**。ep1≡ep2 完全一致 (fire_step / G first-latch 列 / done_step 347 / term)。reward per-step trace diff = **0.0** (characterization-only, pN B5)。
- **L-E** = **PASS** (reset clear 前後 eq_active 対称差 ∅、両 ep)。
- **L-H Run A (fired/done、flag ON)** = **PASS**。逐語 command 実行 = `CUDA_VISIBLE_DEVICES=0 ROUTE_C1_PIN=1 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_collector.py --outbox eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_da_lh_runA --proc-index 0 --base-seed 20260717 --episodes 2 --episode-steps 360 --drive-mode feedforward` (outbox fresh 実測)。2 window published (steps 348 env_done)、8 fields 実値 = pin_fire_step **246** / pin_fire_frame 2462 / pin_eq_id 27 / pin_seat_seg 27 / anchor [0.3508,0.1457,0.8307] / dwell **3** / mismatch **0** / audit_verdict **1**、old-9 arrays present (additive)、manifest mirror {246,27,0}。**supervisor `_pin_fire_summary`** = windows_total **2** / windows_with_done **2** / fired **2** / fire_rate 1.0 / fire_step 246 / mismatch_total 0。⚠ **summary bug fix**: flat outbox を拾えるよう `glob("proc_*/...")`→`rglob("ep_*.manifest.json")` (production proc_*/ + L-H flat 両対応)。
- **L-C3-5 (bypass 継承)** = **PASS_all**（`pin_ab_lifecycle_probe.py --cell cell_x0_y0 --bypass` on bundle tree）: C3 outside bypass = RAISE-before-clear ✓ / C4 inside bypass = audited-then-cleared ✓ / C5_i all-legit cleared ✓ / C5_ii count>2 = double-pin RAISE ✓ / C5_iii outside = RAISE no-partial ✓。⭐extended `_clear_c1_pin` の **class-1 mismatch print が bypass 書込 (witness None + fired=[0]/[0,1]) で発火**確認（LOUD、reward 非配線）。(a)(b) harness L-D/L-D2/L-E も True（K-dwell trigger で fire+audit+clear+refire）。
- **L-H Run B (budget cutoff、flag ON)** = **PASS**。逐語 = `... --outbox pin_da_lh_runB --episodes 1 --episode-steps 230 --drive-mode feedforward`（outbox fresh 実測）。1 window published（steps 230、end=workload_step_budget）、8 fields = **field-wise (pN B3 訂正)**: fire_step/fire_frame/eq_id/dwell/mismatch/audit = **−1** ・anchor_xyz = **NaN×3** ・**pin_seat_seg = 27 (armed identity、非 sentinel — §2-D identity 意味論: seat_seg は fire 前も既知)**、summary = windows_total **1** / windows_with_done **0** / fired **0**（budget cutoff の in-flight 可視化）。
- **fire_label** = ✅**§8.13 裁定済 (L-D PASS 確定)** — §2-11 governs、live 2462 standing anchor、offline 2468 RETIRE、probe PASS 論理是正済。
- **L-F1(d) (flag-OFF byte 恒等、bundle vs baseline `88b7a16681`)** = ✅**PASS** (2026-07-17 17:56)。逐語 (両側 concurrent、trace 360、各 outbox 隔離 wt): bundle = `cd <bundle_wt> && CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_d_trigger_probe.py --cell cell_x0_y0 --trace 360 --tag bundle` (bundle wt = HEAD `16dde1ff5c` + (d-a) bundle patch) / baseline = 同 script `--tag f1base` (@ `wt_base_88b7a1`、source `88b7a16681`)。結果: **final_digest 完全一致** `4e81516ca74e1b2d6e20b0fb0a72ad8933de395c2e7f5a8ce03105963e5bc73c`、per-field mismatch ∅ (phys/obs/reward/done_steps/term_at_done 全 360 step)、**obs.npy sha256 一致** `f313f5598c7c944f`、done_steps [342] 一致。⇒ flag-OFF で (d-a) は byte-neutral (audit 経路 + env 本体の out-of-scope 編集 tripwire 通過)。⚠source 恒等前提を実測: `git diff --stat 88b7a16681 HEAD -- 'thread_isaac_lab/**/*.py'` = ∅ (間の commit は doc-only ⇒ bundle = baseline + (d-a))。
- **L-F2(d) (flag-ON 宣言 delta、bundle vs baseline)** = ✅**measured delta = §2-12 宣言と一致 (判定 = two-key)** (2026-07-17 17:58)。baseline flag-ON = `cd <wt_base_88b7a1> && CUDA_VISIBLE_DEVICES=0 …python eval_runs/…/pin_ab_lifecycle_probe.py --cell cell_x0_y0` ((a)(b) recorded-onset): ep1/ep2 **fire 254** / latch [98,146,242,242] / done 343 / audit PASS。bundle flag-ON = L-D canonical (**fire 246** / latch [98,146,242,242] / done 347)。宣言 delta 実測: **fire 254→246 (−8 RL step)** ✓ / **G3 latch 242 不変** ✓ / full latch 列不変 ✓ / latch ≺ fire 両側 ✓。宣言外の obs/reward/latch identity 変更なし (§11)。
- **L-H2 Run C (既存 artifact 面不変、HEAD vs bundle、flag-OFF、ep1 steps60)** = ✅**全 hard bar (i)-(vi) PASS** (2026-07-17 17:59)。逐語 (両側 outbox = `rm -rf` 後 fresh 実測): head = `cd <wt_base_88b7a1> && CUDA_VISIBLE_DEVICES=0 /home/rlrk/env_isaaclab7/bin/python thread_isaac_lab/scripts/forkb_collector.py --outbox <repo>/eval_runs/troot_optE_dapg_wholeroute_scope_20260701/pin_da_lh_runC_head --proc-index 0 --base-seed 20260717 --episodes 1 --episode-steps 60 --drive-mode feedforward` / bundle = 同 command (@ bundle wt) `--outbox …/pin_da_lh_runC_bundle`。結果: (i) **旧 9 arrays byte 一致** (a_executed/a_raw/cable_traj/done/invalid_mask/o/o_next/r_paid/time_out) / (ii) 期待一致 manifest keys 値一致・**env_fingerprint_sha 一致** `876fb3b5…` / (iii) 期待差分 = {code_sha, sha256} のみ (各版 own hash: code_sha 3baf1631 vs e6b96874、sha256 1e4fdba5 vs 13e8983b) / (iv) pid self-consistent 両側 (manifest.pid==proc_meta.pid) / (v) closure_sha256 各版 self-consistency (9/9 entry = 実 file sha 一致) / (vi) additions = npz 8 fields + manifest 3 keys の exact set (過不足ゼロ)。
- **byte legs 完了 (2026-07-17 17:56-17:59、cuda:0)**: L-F1 / L-F2 / L-H2 Run C = 全 PASS ⇒ **pre-land legs 全数 PASS**。**pending**: L-G (post-land pre-commit sweep) / L-B (post-land 隔離 wt @ landed commit) / **/pre-check** (banked §8.9) / land (explicit-path atomic、config hunk3+4 のみ) / post-land two-key。
- **/pre-check = ✅PASS (WARN-level、2026-07-17 18:1x、banked §8.9 位置)**: skeptical sub-agent 独立 code-trace で全 load-bearing path CORRECT 確認 — witness-dict contract closed (KeyError path なし) / weld anchor == fire snapshot (`route_executor.py:795` eq_data[3:6]=seat_world) / same-snapshot regime (1 body_q read が check+authorizer 両方、fire-True⇒accept 構成的) / dwell+mismatch §2-A/§2-C exact / mj_forward hoist 完全 (clip_geoms_at:870 除去、両 caller self-forward、audit は cache-agnostic live rescan) / 定数 exact (K=3・0.831・821/836) / FF-branch-only call site 単一 / **no NEW kinematic exception (INVARIANT #5 intact、単一 authorize_clip_pin→activate_c1_pin writer)** / mismatch = LOUD-only 非配線 (reward/term/invalid/time_outs 不接続) / **(d-a) 訓練非起動・(d)=(d-a)+(d-b)+cell-2 unlock 保存 (§S4.7)** / SRG 非over-bind (mechanism verdict、fidelity-bound success 非 bind)。**0 CRITICAL / 0 HIGH**。**3 MEDIUM = two-key reviewers が明示 ACK 必須**: (M1) depth bar 0.831 headroom 1.285mm = §12-8 DR-ON re-check (conservative fail-closed no-fire、検出 = supervisor fire-rate) — 829.715 は p5 の 81-cell 実測ゆえ DR-ON で再確認 / (M2) "byte-neutral" = **sim-replay** byte-neutral (L-F1 が phys/obs/reward/done を測定; artifact 面は §11 宣言どおり 8npz+3manifest 追加、L-H2 が bound; DAPG/BC loader の additive-key 許容は D0-R3 規約だが本 legs では未 assert) / (M3) latch≺fire は 2 clock 比較・+4 margin で成立 (§8.13 の coarse bar 意図どおり、cell-2 §12-5 は gap 縮小に注意)。2 LOW = obs[60:62] NOT-MINE comment hunk (§6-3 hunk 除外で対応) / 行番号 stale (call site now `:1225`、post-land [RESULT] に記録; `:1225` の "(d2)" inline comment は baseline=本 bundle scope 外・不触)。verifier caveat: code-trace + doc cross-check (probe/legs 非再実行、runtime 値 [831.07/L-F1 digest] は internally-consistent 扱い)。
- **land = ✅完了 (producing commit `e8edd96a3e`、land `1e89eb50b4`→amend、2026-07-17 18:33、branch `rlrk/optE-s2-substrate-swap`)**: §6 explicit-path atomic (9 files, 1765+/46−)。staged = §3 IN 正確 **9 files** (route_env_config [**hunk3+4 のみ** = K/depth+owned-param、obs[60:62] NOT-MINE comment hunk は working tree に温存確認] + newton_route_env + route_executor + forkb_collector + forkb_supervisor + test + probe + result.json + prereg)。**§6-3 staged-hunk 検査**: staged↔§3 IN 対称差 = ∅ / config staged = 2 hunk (@177/@286)・comment-hunk leak = **0**。**§6-4 aggregate diff sha (CC2-11)**: 初回 stage `460ce53702b2d970c78132f75f4bb8d33f886a208e1eaaf4ad5014c1f0892cc3` → **amended (L-G residue fix 後) = `ae0b1bab237b0a729020feeed3ea1c134da3ea2dd49adebfb4f3e2f692ff66d6`**。pre-commit `validate.sh --staged-only` = **PASS w/29 WARN** (全既存・本 commit 無関係: forkb_supervisor subprocess [supervisor の collector 起動、正当] + data/ video>30MB×27)。**post-land 行番号 (/pre-check Issue 5 是正)**: call site `newton_route_env.py:1225` / K def `route_env_config.py:183` / depth def `:187` (`:1225` の "(d2)" inline comment は baseline=本 bundle scope 外・不触)。⚠**先祖返り防止 verify**: `git diff 88b7a16681..HEAD -- '**/*.py'` = ∅ 前提は land 前に確認済 / 400-file の repo-wide format debt (`isaaclab.sh -f --all-files`) は本 bundle scope 外ゆえ **fold せず** ((a)(b) 継承 debt label 分離と同旨)、私の 6 files は scoped pre-commit で全 hook PASS・変更ゼロ実測。
- **post-land L-B + L-G = ✅PASS (隔離 wt @ `e8edd96a3e`)**: **L-B** = pytest **31 passed** (既存17+新14) exit 0 (4.27s、pN binding) / **L-G** = pre-commit 9-file sweep 全 hook Passed・**porcelain 0**。⚠**L-G 初回 sweep が `result.json` の end-of-file newline 欠を検出 → fix + amend (`1e89eb50b4`→`e8edd96a3e`、diff = 末尾 `\n` のみ・data 不変) → 再 sweep = porcelain 0** (commit-time hook = `validate.sh --staged-only` [custom SSOT] は標準 pre-commit hooks を走らせないゆえ L-G が捕捉、Gate-FAIL-fix-first)。
- **pending (post-land)**: **post-land two-key のみ** — p5 設計軸 (same-snapshot 毒殺 leg・anchor drift・宣言外 delta ゼロ・retention continuity・fire_label 非gate §8.13) + pN 証拠軸 (legs 実測)。/pre-check の 3 MEDIUM carry [M1 DR-headroom §12-8 / M2 sim-replay byte-neutral / M3 latch≺fire dual-clock] を明示 ACK 対象として提示。
- 執行時義務 (pN 第3 readback): Run A/B/C outbox = 各 fresh/non-existing 実測済 ✓ (Run C = `rm -rf` 後 launch) / 逐語 command 上記記録 ✓。
- **post-land two-key = 両軸受領 (2026-07-17 18:5x)**: **p5 設計軸 = CONFORM PASS** (charter §8.14、本 records-fix commit で bank; producing commit `e8edd96a3e` で独立 legs 自走 — tests 31/31・same-snapshot 毒殺 = fail-able 計器 [K 到達で bq 汚染→authorizer pre-poison 受領 assert]・L_D non-gate/standing 2462・L-F1 byte 恒等 [source *.py diff ∅]・L-F2 delta のみ [latch 列不変]・retention 831.07<836; checklist 全 ✅ + containment 同 cache/audit 独立/dormancy/L-H2 additive)。**pN 証拠軸 = MECHANISM/LANDED PASS / EVIDENCE HOLD→records-fix** (独立実測 全 PASS: e8 full hash・parent diff 9 paths・aggregate `ae0b1bab`・隔離 wt pytest 31/31・9-file pre-commit porcelain 0・raw byte 照合 [L-F1 trace `227ec171`/obs `f313f559`・Run C old9 byte+差分{code_sha,sha256}]・§8.13 npz z 独立再計算 [z@2462=831.321 vs z@2467=830.640/z@2468=830.508])。**3 MEDIUM (M1 DR-headroom §12-8 / M2 sim-replay byte-neutral [loader assert=(d-b) consumer] / M3 latch≺fire dual-clock) = 両軸 binding carry ACK**。⛔training-ready 未解除 ((d-a)=1 鍵のみ、§S4.7 (d-a)∧(d-b)∧cell-2)。
- **pN B1/B2/B3 records-fix (本 commit、rerun 不要)**: **B1** = 23 raw byte-leg artifacts を bank + immutable closure record `PIN_D_EVIDENCE_CLOSURE_RSTECHLEAD_20260717.json` (各 sha256 + as-run source closure 結合: baseline `88b7a16681`+tests-patch [f1base/Run C head/L-F2 baseline] / bundle worktree [16dde+(d-a) patch = e8 source: L-F1 bundle/Run C bundle] / bundle main-tree [e8+B2 exec-neutral delta: Run A/B])。**B2** = Run A/B proc_meta closure が main-tree dirty bytes を記録 → e8 committed tree と **exactly 2 files 差**、両者 exec-neutral (configs/__init__.py = SPDX header のみ / route_env_config.py = obs[60:62] comment hunk のみ [NOT-MINE、working-tree 温存])、closure record に as-run/e8 両 sha を記録・loud disposition (runtime 値不変ゆえ Run A/B 測定有効・rerun 不要)。**B3** = §10 Run B「全 sentinel」→ field-wise 訂正済 (pin_seat_seg=27 = armed identity) + land/post-land [RESULT] 行を本 commit で bank。**probe.py header docstring** (p5 non-blocking) = "fire_label==2468 exact" → "latch < fire; fire_label non-gate (sec 8.13)" 訂正。**pN readback で HOLD 解除見込み (数値再走なし)**。

## §11 declared semantic surface (flag 別 + flag 非依存の delta 宣言)

- **flag-OFF**: **env 挙動 delta ゼロ** (trigger 評価は flag gate 内 — 条件置換は helper 先頭 return の
  後段のみ)。L-F1(d) が byte 恒等で測定。
- **flag-ON (canonical、§8.11.2 宣言 delta = v0.4 確定)**: fire 時刻が recorded-onset 254 → **fire_step
  246 / fire_label 2468** (hard bar [242, 250] 内) = **−8 RL step 早発火・G3 latch (242) ≺ fire (246)
  = +4 step の実 gap** (latch 先行が明瞭) + fire 後の物理は fire 時刻差起因の delta。
  **⭐anchor 深度 shift (§8.11.2)**: pin が保持する状態が「達成着座 (anchor z 828.653mm)」から
  「**深部進入時 (anchor z 830.640mm、band [830.604, 830.899]、retention bar 836 まで ≥5.10mm)**」へ
  変わる — 残押込 ≈1.8-2.0mm の weld との fight は微小 (rim 案の 7.0mm から縮小、efc-force leg が測定)。
  これは generic「fire 後 delta」でなく**pin の意味論変化**として宣言する。**G3/G latch 列・reward
  述語・obs 契約は不変** (identity は (B) のまま、§8.1-3(i))。fire 分布の変化 = 宣言面、L-F2(d) が測定。
- **flag 非依存の artifact 面 (CC6-5)**: 全 published window の npz に 8 additive fields + manifest
  3 keys + supervisor に `pin_fire_summary.json` (counters 込み) が加わる (§2-D/§3) — 既存 field/key は
  不変 (L-H2 が項目別 bar で測定 — provenance keys は期待差分)。**production 既定では全 sentinel**
  (§2-D dormancy 宣言)。
- **wrong-clip fire の宣言 (p5 §8.12-①、v0.5 fold)**: capture check は ∃-認可 clip (loop 形 = N-clip
  前方互換) ゆえ、探索 policy が identity body を**他方の認可 clip** volume 深部に K frame 置けば
  wrong-clip weld が成立し得る。実測 81/81 で不到達 (I4 leg C straddle 0 と整合)・帰結 = **保守的
  dead-end** (C1 crossing MISS → G3 不到達 → false success 不能・reset で clear・npz `pin_eq_id`/
  `pin_anchor_xyz` で可視)。設計変更不要 — 宣言のみ。
- **scope 宣言 (pN B1、v0.5)**: 本 chunk (d-a) の delta は **FF branch に限る** — residual/IK branch に
  trigger は不在のまま (D-b)。**(d-a) two-key は training-ready を解除しない** (拘束①)。
- 摂動 cell の fire 分布 = 窓統計どおり per-cell 変量 (fire≺release 81/81) — live 実測は §12-5 追補時。

## §12 carry notes ((a)(b) §12 の引受け状態 + 本 chunk 発の carry)

1. `notify_model_changed` 禁止 (live pin 中) — **継続** (LL-Newton 転記待ちも継続)。
2. witness run-level provenance — **本 chunk §2-D で discharge** (実装完了時に (a)(b) §12-2 を CLOSED
   と記録)。
3. wc>1 opt-out 文脈の audit 走行 note — **継続** (本 chunk は guard 順・wc raise を不触)。
4. B4 state-bank: **§8.7 裁定済** (bank-state restore → fire ≤ **K+1 physics frame (≤ 1 RL step)**
   [CC2-9: 単位を frame と明記 — B4 prereg が曖昧さを継承しないこと] = 宣言済み即発火、抑制しない)。
   B4 prereg への cite 転記 = B4 起草時 %12 — **継続 carry**。
5. cell-2 DoD-7 追補 — **継続** (§5 probe cell 制約 + §10 恒久記載)。
6. **新規 carry (本 chunk 発)**: 残差/IK drive 分岐への trigger call site 追加 = **D-b window gate 項目
   = (d) 全体の残り半分 (pN B1 で格上げ — training-ready unlock の必要条件)**。(§3 OUT の明示繰延 —
   policy-drive 残差時代・ik_chord の評価配置はその gate で設計)。**+ K=3 の妥当性再検証を同 carry に
   含める (CC3-4)**: 遅い policy swing-through は K=3 frame (6.25ms) を dwell し得る — K は FF 押込の
   文脈で裁定された値であり、policy 時代の適正は D-b gate の設計項目。**+ hold 下の fired_at_frame
   label 意味論 (§2-5 注記) も同 gate**。
7. **§8.2-3 訓練時 re-open 条件 (CC2-7)**: mismatch counter の実訓練頻度 = /pre-check 審査項目、
   **>0 実測時は §8.2 裁定 re-open** — 本 chunk を越えて訓練時代まで存続する carry。
8. **DR carry (§8.11.2 新設)**: Z_FIRE_DEPTH bar の headroom = 831 − 829.715 (producer 静止高 81-cell
   max) = **1.285mm** — DR が静止高を +1.3mm 超上げると fire 不能 (fail-closed no-fire、検出器 = Q3
   supervisor fire 率 = loud)。**DR-ON 日に bar 再検** (C2-margin 3.183mm MED carry と同 pattern)。
