# (d) policy-drive trigger — 設計 gate charter（VT-DESIGN）

**Author:** VT-DESIGN (w2:p5)。**Drafted:** 2026-07-17 09:3x JST。**Status:** CHARTER v1.0 — 0-commit（bank = %12）。
**Trigger:** %12 要請 09:26（(a)(b) chunk close `c07f75c0d7` → 次 leg）。**L = L3**（reward/env 意味論 — L-TRIAGE self=auto）。
**Governing banked design:** `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` **§21.4**（:750-765、幾何 capture trigger + reward-coupling 宣言）+ §S3.3 premise（seat ≺ pin、116f 窓）+ `REWARDDESIGN_...` §S4.5/§S4.6 standing。
**本 doc は charter であって設計解でない** — 解は §6 の gate chain（/reward-design 4 artifacts + p5 裁定）が生む。%12 は本 charter 準拠の素材から着手（materials→ruling パターン、D0 前例）。

## §1 scope / goal

- **goal**: pin 発火を recording onset（現 `_maybe_activate_c1_pin` `:1817-1850`、once-per-episode + onset frame gate）から **live 幾何 capture trigger** へ — policy が駆動する将来 run に recording clock は無い（§21.4 :752）。
- **fork-B 文脈での再 scope**（§21.11.1）: (c) mjw 書込は不要化 — 発火は proven CPU path の**唯一の書き手** `authorize_clip_pin`（`route_executor.py:914`、match_tol 5mm）経由のまま。§21.5 の per-world audit 化は **MOOT**（wc=1、landed `_clear_c1_pin` `:1851-1883` が audit-then-clear を全 reset 経路で被覆済）。
- **IN**: trigger 述語・発火規則・identity 源・witness provenance・不一致 loud 化の設計 + その /reward-design+/pre-check gate。
- **OUT**: 実装（gate PASS 後の別 chunk）/ STEP 9 release 述語の変更 / obs-space 変更 / task_config 数値変更 / S8 warp-native 系（banked のまま）。

## §2 banked 設計のうち【生きている】核（§21.4 から不変で carry）

1. **非 raise 述語 → raising authorizer の 2 段**: 毎 step は `clip_capture_predicate`（`:882-911`、pure bool・3 legs〔lateral/domain/floor-rim〕・reason 付き）で判定し、**True のときだけ** raising `authorize_clip_pin` を呼ぶ。発火は依然唯一の書き手経由（INVARIANT #5 の機構保証は不変、raise は backstop として残る）。
2. **pin-before-release**: capture 述語は STEP 7 押込中に True（§21.4 :759、step-table 接地 = §21.7 表の `CANONICAL_MOTION_TABLE_V1.md:49-51/:126-128`）⇒ STEP 8 解放より前に発火。
3. **発火窓は knife-edge でない**: canonical 実測 seat f2428 ≺ onset f2544（116 frame、§S3.3）+ (a)(b) L-D 実測 fire step 254（flag-ON、`pin_ab_lifecycle_probe_result_cell_x0_y0.json`）。
4. **reward coupling 宣言**（§21.4 :763-765）: 「いつ・どう latch するか」が recording-onset → live-geometric に変わる = 報酬 dynamics の変化 ⇒ **/reward-design（到達可能性表・因果 DAG・ground-truth 値・episode trace）+ /pre-check が実装前必須**。未通過で %12 実装不可。

## §3 ⭐ 設計 questions（gate が解くべきもの — 番号は %12 収集 4 点を包含）

- **Q1〔=①〕発火規則と refire**: fire-once-per-episode latch（witness）は維持（pin = 保持装置、§S3.3）。(a)(b) 後は reset が witness/eq を clear ⇒ **episode 間 refire は既に landed**。設計対象 = (i) per-step 述語評価の配置（reward loop 内 or update_sync — 現 activate は FF loop `:1218` のみ）(ii) **episode 内 re-fire は default 不採用**（escape 後の再発火 = 別述語の別問題 — 採否は artifacts で顕在化）(iii) False 述語で authorizer を**呼ばない**ことによる非 raise 化（`NotInAnyRouteClip` は本来の backstop に退く）。
- **Q2〔=②〕⭐ 核心: identity 源の再設計**: §21.4 :756 の「seat 段 = route 固定段（body30）」は **81-cell 実測（per-cell seat_k = 25..34、`gate2_rerun_i3i4_probe_result.json` leg C）より前の記述** — DR/cell 変動下で固定段は成立しない。選択肢: **(A) fired-body 由来 identity**（発火時に capture volume 内に実在した body を authorizer が world-position で解決 → その segment を `_pin_seat_seg` に = §13.1「pinned = hard identity」の直接実装、recording 不要化）/ (B) recording 由来（現行、DAPG residual-on-script 時代は recording が全 episode に随伴するため有効）。**(A) には順序問題がある**: 現 instrument は identity が無いと seat を測れない（fail-closed）⇒ G3 latch は発火後に始めて可能になり、latch 順序が recording 時代と変わる（§S3.3 の「seat が先」は**幾何**の話であり、**計器上**は identity 供給後にしか seat=True にならない）。⇒ episode-trace artifact で「発火 step → identity 確立 → G3 latch」の因果列を canonical + 摂動 cell で明示し、旧列との差を宣言すること。**番号空間の照合を素材段で必須化**（G-item: step-table「body30」vs producer body 55 vs env cable-相対 seg 27 vs seat_k 25..34 — 4 つの番号空間の対応表、file:line 付き）。
- **Q3〔=③〕witness の run-level provenance**: per-episode ephemeral 化（(a)(b)）後の訓練時代 equivalents = **collector episode-npz への additive fields**（D0 R3 の additive manifest 原則）: fire_step / eq_id / seat_seg / anchor_xyz / audit_verdict / witness-vs-fired flag。supervisor 集計に per-episode fire 率・fire step 分布を載せる（fire しない episode = 学習信号として正常 — 記録されれば silent でない）。
- **Q4〔=④〕witness-vs-fired 不一致の loud 化**: **本 chunk で採用**（08:00 登録の審査どおり）。home = `_clear_c1_pin` の audit 点: `fired` 集合と witness の不一致（fired≠∅ ∧ witness=None、または eq_id 不一致 = bypass 署名）→ **loud print + counter + episode-npz flag（非 terminal）**。terminal 化はしない（audit raise が圏外/double を既に殺す — 圏内単発 bypass の検出は記録で足り、偽 terminal は訓練を汚す）。
- **Q5 timing 適合の positive control**: canonical で「(d) trigger の fire step ∈ [seat 成立, STEP 8 解放)」を probe assert（≈254 anchor、drift = loud）。摂動 cell では window の存在のみ assert（step 値は cell 依存）。
- **Q6 B4 state-bank 相互作用**（prereg §12-4 の引受け）: post-onset bank state から restore → 幾何述語は即 True → **即発火は §S3.3 により正しい**（pin = 既成着座の保持）。抑制しない・宣言する。B4 gate 側 prereg 項目との整合を素材で cite。

## §4 不変制約（本 gate で動かさないもの）

1. **INVARIANT #5 clip-only**: 発火は `authorize_clip_pin` 経由のみ・capture volume 外は raise（backstop）。trigger 側が緩めない。
2. **timeouts 純度**: trigger/fire/witness は `time_outs` に一切触れない（prohibited.md、(a)(b) probe で term.time_outs=0 実証済の線を維持）。
3. **identity-persistence coupling**（§21.11.1 + `dfbddb4777` pointer）: episode 内で identity を null 化しない。Q2-(A) 採用時も「発火後〜reset まで永続」は不変（escape guard は identity を読む）。
4. **成功述語は幾何を読む — pin 状態を読まない**: c1_seated/c1_retained/G6 は `_seat_metrics`（gate② 批准計器）のまま。pin は物理保持のモデルであって採点入力でない（honest instrument、§S4.5.2）。
5. **training-ready 禁止の解除条件**は §S4.3-2 のまま: **(d) two-key PASS + §12-5 cell-2 追補**。本 charter は解除を約束しない。
6. **(d) probe の cell 制約**: G-F2 fold-7 guard は不触 — 初期 probe は nominal cell、cell 多様性は DoD-7 後追補（§12-5 と同型・no-silent-caps で [RESULT] に記録）。
7. **INIT_XY_NOISE disposition**（(d) 日送り登録分）: 到達可能性表・DR 感度の素材で処置（trigger 自体は後半 step 事象ゆえ直接影響は限定的 — が、Q2 の identity 源が DR に露出する）。

## §5 prior-art BLOCKER の discharge（`check_thread_vault_prior_art.sh` 07-17 09:2x = BLOCKER_CONTEXT_FOUND）

- **hit**: r2a_track_a（2026-05-25）Sim2real Product Predicate — kinematic support / fixture pinning / hidden support / **active-at-completion as product success** の排除。
- **同一 failed path でない理由**（(a)(b) prereg §7 と同根 + (d) 固有分）: r2a の 'pin' = robot finger の kinematic pose-pin（禁止 class）。本件 = **clip-retention pin = RS71 §0 INVARIANT #5 の唯一の認可例外** + Rs 逐語「クリップ**のみ** pin を RL env に恒久配線しろ」（LEDGER:57）。(d) は認可済 authorizer path への **trigger 時刻の設計変更**のみで、新たな kinematic 例外を作らない。採点計器は幾何を読む（§4-4）ため「hidden support が成功に数えられる」構造も無い。
- **⭐ hit の有用 fold（新規条項として採用）**: 「**active-at-completion ≠ product success**」を transfer 境界注記として (d) 設計に固定 — 訓練内 G6 は INVARIANT #5 の下で pin 保持を含む sim 成功として正当（Rs 承認済モデル化）だが、**sim2real/product 主張には §15 conservatism + RS71 §4 境界 + §S4.5 の producer-equivalence 条件がそのまま適用**される（(d) が解除するのは training-block であって transfer 主張ではない）。

## §6 gate chain / deliverables（pattern = D0 materials→ruling + (a)(b) prereg）

1. **素材（%12）**: /reward-design 4 artifacts の (d) 版 — (i) 到達可能性表（capture volume への到達 margin、canonical + 81-cell 統計、INIT_XY_NOISE/DR 感度）(ii) 因果 DAG（述語→発火→identity→latch→reward の因果列、Q2 順序問題を明示）(iii) ground-truth 値（volume bar 群 = built-model 由来を再 cite、fire step anchor 254、seat_k 分布）(iv) episode trace（canonical + 最低 1 摂動条件、旧 onset 経路との diff 列挙）。+ Q2 番号空間対応表（G-item）。
2. **p5 裁定**: 素材が揃った Q から順に裁定 → banked（%12）。
3. **prereg**（pN 条件パターン: claim/freeze/legs/landing protocol）→ 実装 → probe/legs → **/pre-check** → two-key（p5 設計軸 + pN evidence 軸）。
4. **acceptance legs の骨格**（prereg で確定）: 正 = canonical fire-window positive control（Q5）+ ep1≡ep2（(d) trigger 版 L-D2 相当）/ 負 = pre-capture 不発火・圏外 不発火**かつ不 raise**・fire-once・bypass 系継承（L-C3-5 型）/ 宣言 delta = (a)(b) tree 対比の L-F2 型（発火時刻分布の変化は**宣言面**）。

## §7 cites（本 charter の接地、全て p5 自読 2026-07-17）

| 項 | cite |
|---|---|
| banked (d) 設計 | `RLENV_PIN_DESIGN_VTDESIGN_20260715.md:750-765`（§21.4）+ :761（§S3.3 pointer）|
| 現 activation | `newton_route_env.py:1817-1850`（once-per-episode witness・onset gate・raising authorizer）|
| capture 述語 | `route_executor.py:882-911`（pure bool・3 legs・reason）|
| authorizer / audit | `route_executor.py:914`（match_tol 5e-3）/ `:963-1012`（audit、fired tuple return）|
| (a)(b) landed lifecycle | `newton_route_env.py:1851-1883`（`_clear_c1_pin`）+ `:1038`（call site）|
| seat_k 分布 / L-D anchor | `gate2_rerun_i3i4_probe_result.json` leg C（25..34）/ `pin_ab_lifecycle_probe_result_cell_x0_y0.json`（fire 254・time_outs=0）|
| standing | `REWARDDESIGN_...VTDESIGN_20260715.md` §S4.3-2 / §S4.5 / §S4.6（training-ready 解除条件・(iii) 状態・付帯）|
| carry 引受け | `PIN_AB_SCOPE_PREREG_RSTECHLEAD_20260717.md` §12-2（witness provenance）/ §12-4（B4）/ §12-5（cell-2）|
