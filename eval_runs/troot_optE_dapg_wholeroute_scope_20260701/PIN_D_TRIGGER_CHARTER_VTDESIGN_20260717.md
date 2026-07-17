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
   - ⚠ **/pre-check 配置の supersession（§8.11.3 GRANT、2026-07-17）**: 本 chunk（訓練なし・probe のみ）では chain §6-3/§8.9 の順（実装 → probe → /pre-check → two-key）が本項の字義「実装前」を supersede — intent（未批准 (d) 意味論での訓練禁止）は training-ready 禁止（§S4.3-2 + §12-5）が chunk を跨いで保持。gate② 再走前例に一致。pointer 追記 = §8.11.3 授権により %12。

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
   - ⚠ **「(d)」の解釈 = §S4.7（REWARDDESIGN doc、2026-07-17）**: (d) = **(d-a)**〔FF-branch trigger 機構 = 本 prereg chunk〕+ **(d-b)**〔訓練 drive 分岐への評価配置 = D-b window gate〕 — 解除 = **両 two-key ∧ §12-5 cell-2**。(d-a) 単独では解除しない。pointer 追記 = §S4.7.3 授権により %12。
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

## §8 🔒 裁定（v1.1 追記 2026-07-17 10:0x — 素材 v0.1 `f4bb58796d` を受けて。素材 §2 実測は p5 が 81 npz から独立再計算し完全一致〔分布 8-bin・全 cell 単一値・offset 28 = 81/81・leg-C bins 同一〕を確認済。⚠節順 note: §8 は時系列追記のため §7 cites の前に位置する — 版履歴の透明性を優先し並べ替えない）

### §8.1 🔒 Q2 裁定 = **(B) recording 由来 identity を採用**（DAPG/recording 時代）+ **fire 対象 = identity body** + (A) は照合レグへ降格 + §21.4:756 固定段文を RE-SUPERSEDE

1. **固定段 (C) = 実測死を批准**: 素材 §1（body30 は S2-S5 のどれの 30 でもない — C1 +3 / C2 +8.5 で affine 写像不能）+ §2（seat は cell 幾何の関数、spread 10 seg ≈ 146mm）。**`RLENV_PIN_DESIGN` §21.4:756「seat_seg = route が定める固定段（C1 = body30）」を本項で RE-SUPERSEDE**（「body30」は step-table の設計時呼称であり runtime index でない — %12 bank 時に §21.4 へ pointer 追記で可〔§S3.3 授権と同型〕）。step-table 自体は不変（呼称の地位が確定しただけ）。
2. **(A) fired-body 由来を identity 源として不採用**（本時代）— 決定的理由 = **観測の再死**: identity が発火まで存在しない ⇒ obs[49]/[58]-[61] が発火まで MISS sentinel = gate②/§S4.5 が「計器死からの復元」として批准した状態の**逆行**。policy は着座を学ぶ局面（approach/descend/押込）で seat 感覚ゼロ、発火（≈着座時）後にようやく obs が生きる — **学習信号の因果が逆順**（到達可能性の構造欠陥）。global 計器で埋める代替は I3 の reward↔obs seam の再導入で不可。副次: G3 latch が fire 後へ遅延（242→243+）= 不要な報酬 dynamics delta の追加。
3. **(B) の採用理由**: (i) latch 列不変（G3 242 のまま — 宣言 delta は fire 時刻 254→≈243 のみに局所化、素材 §3）(ii) DR 内故障方向 = **保守的**（実着座が identity 窓からずれる → MISS/false-negative → exploit 側に開かない、§S2 row 1 と同型。学習効率への影響定量は artifact (i) の 81-cell capture-window 解析で fold — /pre-check 前必須）(iii) multi-cell 拡張は per-cell recording identity で成立（§2: 81 cell 各自単一値の実測）— §12-5 cell-2 追補にそのまま伸びる (iv) DAPG residual-on-script 時代は recording が全 episode に随伴 = 供給保証。
4. **fire 対象 = identity body**: capture 述語（`:882`）は `cable[_pin_seat_seg]` の world 位置に対して評価し、True で同 body を `authorize_clip_pin` に渡す ⇒ **welded body ≡ identity（by construction）** — (A) が守ろうとした pin=hard-identity の整合を、identity 源の交換なしに機構で獲得する。「volume 内の任意 body で発火」は不採用（identity と別 body を weld し得る → 計器と物理の乖離 → escape guard の偽 −10 経路）。
5. **scope 限定**: 純 policy 時代（recording 消滅）の identity 源は当該時代の gate で再設計 — 本裁定は foreclose しない（(A) の順序問題解決を含め、その時代の設計問題）。
6. episode-trace artifact (iv) は (B)+identity-target 前提で作成（(A) の比較列は 1 本参考掲載で可）。

### §8.2 🔒 Q4 裁定 = **採用**（本 chunk）— 非 terminal loud、3 class 分類

1. **検出 class**: (i) fired≠∅ ∧ witness=None（bypass 署名）(ii) witness≠None ∧ witness.eq_id ∉ fired（witness/model 乖離 — clear 前に消えた/別 eq）(iii) fired ⊋ {witness.eq_id}（併走 bypass）。
2. **home** = `_clear_c1_pin` の audit 点（`fired` tuple は landed で既に返る `:1879`）。
3. **応答 = loud print + supervisor counter + episode-npz additive flag**（D0 R3 原則）。⛔ **reward / termination / invalid には配線しない**（本 gate）: 偽 terminal は policy への infra 起因罰 = 訓練汚染 / `invalid` の意味拡張は trainer 契約変更で別問題。canonical/probe の期待値 = **0**（>0 = probe FAIL）。実訓練での頻度 = /pre-check 審査項目、>0 実測時は本裁定 re-open。
4. Q2-4 の fire-target=identity-body により、class (i)/(iii) は**真の bypass 書込に限定**される（設計内発火からは構造的に発生しない — 検出器の信号純度が上がる）。

### §8.3 素材 v0.2（`b3823f2961`）の検証記録 + §8.1 への追記（v1.2、2026-07-17 10:2x）
- **p5 独立再計算（81 npz 直読）= v0.2 の全 load-bearing 量と一致**: 窓統計 onset−geo_fire(B) min 99 / p50 116 / p90 153 / max 156 ✓ / A−B delta hist **{−1: 32, 0: 49}** ✓ / canonical geo_fire 2427・進入 margin dx 0.07mm・rim 内側 0.07mm ✓ / **fire-before-release 81/81** ✓（release = onset 後 min(grip)<0.5 初 frame、release−onset = **150f 一様 81/81**、canonical 2694 ✓）。⚠透明性: 私の初回 release 検出は frame 0 の grasp 前 open grip を誤検出（0/81 と出た）— 検出器修正後に一致。**追加発見**: B body の volume 内持続は「100+f」でなく**進入後 最小 5262f = 実質恒久**（pin が保持するため — K-dwell の安全余裕は事実上無限）。
- **§8.1 Q2 への実証的裏書き（裁定不変・強化）**: §4a の A=B−1（32/81、系統 −1）= 「最初に入った段」は 40% の cell で「録画が押した段」と**別 body に identity を束縛**する — quantization-floor 教訓の実例。fire 対象 = identity body 規則（§8.1-4）の下で判別問題は**解消**（B 自身の窓が 81/81 で十分と実測）。

### §8.4 🔒 Q1 裁定 — 発火規則 = **identity body への K-consecutive dwell（K=3）**、既存 call site の条件置換
1. **評価配置** = 既存 activation call site（update path、`_maybe_activate_c1_pin` `:1218` 系）の**条件置換** — FF onset 条件 → 幾何規則。`route_c1_pin` flag gate・fire と reward 評価の相対順序（physics 後・次 reward 前）= landed (a)(b)/L-D 時代と同一に保つ。
2. **規則形 = K-consecutive dwell、K=3**（route-invariant 設計定数・prereg 凍結）: first-True は rim 通過瞬間で margin ~0.07mm（canonical、p5 再計算一致）= grazing ⇒ 即発火は 0-margin 発火（数値 wobble で境界を跨ぎ、authorizer backstop を設計経路から踏み得る）— 不採用。margin-bar 案 = volume 定義の二重管理 — 不採用。K=3 の遅延は窓（早発火余裕 min 99f・進入後持続 実質恒久）に対し無視可能。
3. **containment 制約**: fire 述語 bars ⊆ authorizer capture volume（lat 3.5 < 6.0 = 真に内側 / z・y = 境界一致は dwell が吸収）⇒ **設計経路から backstop raise は不可達**（raise = 真の bypass 専用に純化）。
   - ⚠ **本項の「6.0」は訂正 #11（§8.10.2、2026-07-17）**: on-disk に存在しない数値。真の関係 = 厳密包含でなく **identity（同一関数・同一 bar）** — 結論（backstop raise 不可達）は containment-by-identity + same-snapshot 規律でより強く survive。pointer 追記 = §8.10.2 授権により %12。
4. **fire-once per episode**（witness latch 既存）。**episode 内 re-fire = 不採用確定**（escape 後の再発火は将来の別述語・別 gate）。
5. 対象 = **identity body のみ**（§8.1-4 と一体）。

### §8.5 🔒 Q3 裁定 — witness run-level provenance = episode-npz additive fields（D0 R3 原則）
- fields（名/型は prereg で凍結・additive-only・既存 field 不変）: `pin_fire_step`（int、−1=未発火）/ `pin_fire_frame` / `pin_eq_id` / `pin_seat_seg`（identity）/ `pin_anchor_xyz` / `pin_dwell_count_at_fire` / `pin_mismatch_class`（0=none・1/2/3 = §8.2 class）/ `pin_audit_verdict_at_reset`。
- supervisor 集計 = fire 率・fire_step 分布・mismatch 総数。**未発火 episode = 正常データ**（記録されるゆえ silent でない — 学習初期は未発火が多数で正常）。

### §8.6 🔒 Q5 裁定 — positive controls + 宣言 delta
- (a) **fire ≺ release を【両 release 定義で】assert**（hard・全 probe cell）: D-6 計器（onset+54）と min-grip<0.5（onset+150、81/81 一様実測）— どちらでも margin ≥ 153f。**(d) の canonical release 定義 = min(grip)<0.5（post-onset）を採用**（D-6 計器は併記・定義は artifact 固定）。
- (b) canonical anchor: `fire_step ∈ [G3_latch, G3_latch + W]`、W = K+5。期待 fire ≈ 243+(K−1) — **実測値を prereg で凍結**（drift = loud）。
- (c) **宣言 delta**: fire 254 → ≈243+K の移動（+それに因る物理 delta）= L-F2 型 leg の**宣言面**（(a)(b) tree 対比）。
- (d) 摂動 cell では窓の存在（fire ≺ release）のみ assert（step 値は cell 依存 — §8.8）。

### §8.7 🔒 Q6 裁定 — B4 state-bank 整合
- restore された着座状態: dwell K は restore 後 K step で充足 → **fire ≤ K+1 step = 宣言済み即発火**（§S3.3 により正 — pin は既成着座の保持）。抑制しない。B4 gate 側 prereg に「(d) K-dwell 下の bank-state fire = step ≤ K+1」を cite（転記 = %12）。

### §8.8 🔒 (iv) declared-limit 裁定 — **窓統計 81/81 で本設計 gate は足りる**（per-cell replay probe の追加実装 = 不要）
1. 裁定が依存する量（timing 包絡・順序不変条件・fork 判別）は全て録画から可得で 81/81 実測済 + **p5 独立再計算一致**（§8.3）。
2. (B) 採用（§8.1）により latch 列は fire と独立 — 摂動 cell の latch 問題は recording 時代と同一に還元（gate② で批准済の計器の問題）。
3. 残る未知 = **live fire 下の episode dynamics** = /pre-check probe（nominal cell・G-F2 内）+ DoD-7 後 cell-2 追補（§12-5 既 carry）の担当。
4. **no-silent-cap**: 本繰延（摂動 cell latch 列 = live probe 段へ）を prereg [RESULT] に明記のこと。

### §8.9 残作業 index
全 Q 裁定済（Q2/Q4 = §8.1/§8.2〔banked `efad9c05b9`〕、Q1/Q3/Q5/Q6/(iv) = §8.4-§8.8）。次 = %12 prereg（pN 条件パターン・§8 準拠）→ 実装 → probe → `/pre-check` → two-key。

### §8.10 🔒 prereg v0.1 §Q への裁定 4 本（v1.3、2026-07-17 10:5x — `PIN_D_TRIGGER_PREREG_RSTECHLEAD_20260717.md` §Q を受けて。cites 全て p5 自読・on-disk 検証済）

**§8.10.1 Q-1 裁定 = K の単位 = physics frame（K = 3 連続 physics frame）— freeze 解除**
- 根拠: (i) **cadence 同一性** — 既存 call site（`newton_route_env.py:1221`、FF substep loop 内 = per-physics-frame 評価を p5 自読）への「条件置換のみ」（§8.4-1）に単位を一致させる。RL-step 単位は sub_i gating 等の新規機構 = 置換規律からの逸脱。(ii) debounce 対象（rim 通過の数値 wobble、進入 margin 0.07mm）は frame 級現象 — %12 推奨に concur。(iii) 窓安全性は両単位で成立（早発火余裕 min 99f・持続 ≥5262f）ゆえ**機構最小**を選ぶ。(iv) frame-exact anchor は録画から offline 再計算可能 = probe assert が厳密。
- **凍結 anchor**: canonical 期待 **fire_frame = 2429**（= first-True 2427 + (K−1)、隣接 3 frame の連続性は持続実測 ≥5262f が保証）/ 期待 **fire_step = 242** = G3 latch と同 RL step（fire は substep 内・latch は同 step の reward 評価時 — (B) では両者独立ゆえ順序問題なし）。hard bar `fire_step ∈ [242, 250]` 維持。一般式 = `fire_frame = first_true_frame + (K−1)`。drift = loud。
- 注記: §8.6(b) の「期待 fire ≈ 243+(K−1)」は step 算術で**単位曖昧だった** — 本項の frame 式で確定（Q-1 は曖昧さを正しく surface した）。
- ⚠ **本項の凍結値（2429 / 242 / 式 `first_true+(K−1)`・「G3 と同 step」）は訂正 #12（§8.11.1）で supersede** — 現行凍結 = §8.11.2 / prereg §2-11（式 `run_start + K` = fire_label 2468 / fire_step 246 / anchor 830.640mm）。pointer 追記 = §8.12 授権により %12。

**§8.10.2 Q-2 = containment-by-identity で CONFORM + ⚠訂正 11 件目（「6.0」）**
- **訂正 #11**: §8.4-3「lat 3.5 < 6.0 = 真に内側」の **6.0 は on-disk に存在しない** — p5 自身の grep で確認（`route_executor.py` の capture 系に 6.0 なし〔hit は無関係な camera 角 `:2523` のみ〕・設計 doc §15 にもなし）。authorizer `:956` / audit `:1010` は fire 述語と**同一関数・同一 bar**（`clip_capture_predicate` + `rc.SEAT_LAT_BAR_M` 3.5mm `route_env_config.py:174` / `SEAT_Z_LO/HI_M` `:175-176` / y_win = model geom 由来を両者同式で取得）。真の関係 = **厳密包含でなく identity（等号）**。6.0 の出所 = 記憶からの捏造数値（%12 の幾何仮説 7.5−1.5 は私の生成過程を遡れず検証不能）— **裁定文に file:line なしの数値を書いた = artifact-first の自違反**（#10 の教訓〔claim scope > measurement scope〕の数値版）。**§8.4-3 の結論（設計経路から backstop raise 不可達）は survive し、identity の下でより強くなる**（数値 margin でなく構成的保証）。%12 bank 時に §8.4-3 へ訂正 pointer 1 行の追記を授権。
- **CONFORM 条件（load-bearing 1 本）**: **same-snapshot 規律** — K 到達 frame の check が評価した**同一の seat_world 値（同じ bq snapshot）**を `authorize_clip_pin` へ渡すこと。これで fire-True ⇒ authorizer-accept が同関数・同 bar・同入力の**恒真**になる（re-read や翌 frame 呼びは wobble が backstop を設計経路へ戻す）。prereg「同一 loop body を共有」は本規律を含むと読む — 実装はこの形を維持し、two-key で照合する。

**§8.10.3 Q-3 = CONFORM + 追加 1 点（non-blocking additive）**
- done を含む window にのみ episode record 実値・他は sentinel・fire_step = episode 相対・分母 = done episode 数 — CONFORM（records-match-fact: record は done と共に travel、部分帰属なし）。
- 追加（no-silent-cap）: supervisor summary に **`windows_total` / `windows_with_done`** を併記 — budget 切りで done 前に終わった in-flight episode の pin 状態が「どこにも記録されない」事実を集計面で可視化（消えるのは正・見えず消えるのは不可）。

**§8.10.4 Q-4 = CONFORM**
- per-step check でも BrokenSelector は raise — 構造異常の quiet-skip は「silently never fired」class の再発（`_maybe_activate_c1_pin` docstring が既に記す教訓の継承 = N7 意味論）。§8.4-6 の raise 3 限定列挙と整合（構造的ゆえ実質初回 1 発）。quiet 対象は capture 述語 False のみ。
- ⚠ 「§8.4-6」= **訂正 #13**（§8.11.4-(i)、2026-07-17）: dangling cite — §8.4 は項 1-5、raise 3 限定列挙の実体 = **prereg §2-6**。pointer fix = §8.11.4 授権により %12。

### §8.11 🔒 prereg v0.3 §Q（panel 由来 Q-5〜Q-8）への裁定（v1.4、2026-07-17 12:2x — 入力 = prereg v0.3 §Q + §9 panel OUTCOME。cite 2 本〔`route_executor.py:1768`「sample the post-step frame」逐語 / `newton_route_env.py:1221→:1222` pre-step check〕+ 数値 3 点〔z[2429]=835.665 / z[2544]=828.653 / onset-z 分布 827.714-829.715〕を p5 自読・自計測で確認済）

**§8.11.1 Q-6 = ACCEPT = ⚠訂正 #12（off-by-one）+ 凍結値の再固定**
- 機構: 録画 = **post-step** state（`:1768`）× online check = label f の **physics 前**（`:1221→:1222`）⇒ check(f) が読むのは録画 state f−1。**式 = `fire_label = run_start + K`**（run_start = 録画系で条件が最初に成立した frame）/ **anchor_state = 録画 [fire_label − 1]**。私の §8.10.1（2429 / 242 / `first_true+(K−1)` /「G3 と同 step」）は**録画 sampling 規約を trace しない offline 算術** — 訂正 #12。教訓の一般形: **offline 算術を online 凍結値へ移すときは録画の sampling 規約（post/pre-step）を trace せよ**（verify-at-producing-commit の frame-index 版）。
- 凍結値は §8.11.2 の REVISE 後の規則に対して再固定（下記 — rim 規則の 2430/243 は経由地であり凍結しない）。

**§8.11.2 Q-7 = REVISE 採択 — fire 条件に深さ leg を追加**（%12 ratify 提案は不採用・**測定 legs 5 本は全 ADOPT**）
- **新 fire 条件（凍結）**: `clip_capture_predicate(identity body) ∧ z_B ≤ Z_FIRE_DEPTH_M`、**`Z_FIRE_DEPTH_M = ROUTE_GROOVE_Z + CABLE_RADIUS/2 = 0.831`**（既存定数 2 本の式・新 literal ゼロ）。K=3 連続 frame・same-snapshot・fire-once・authorizer 経路 = 全て不変。fire 集合 ⊂ authorizer 受理集合（深さ leg の分だけ真に内側）⇒ §8.10.2 の恒真は強化のまま。
- **ratify 不採用の根拠（解析で決まる部分 — probe 待ち事項でない）**: K=3 rim 発火の anchor = **835.665mm = retention bar（rim 836）の 0.335mm 内側**（p5 npz 自読確認）。pin eq は anchor への**弾性**拘束で可塑機構が無い ⇒ 押込中に深部へ撓んでも**解放後は anchor（rim 際）へ復帰**し、下で保持する物理が存在しない。C2 drag 張力下の +0.34mm z 変位で `c1_retained` が flicker ⇒ `K_ROUTE_SEAT` sustain がリセットされ続け **G6 が構造的に到達不能**の予測。0.335mm は系の全 margin（lat 3.5 / C2 3.183 / producer retention 7.35mm）より一桁薄い。%12 の「実挙動は empirical ⇒ probe」への回答: **fight の transient は empirical、解放後平衡は拘束の弾性から解析的に決まる** — 予測 FAIL の構成を実装して測りに行かない（fix-first）。
- **§8.4-2「margin-bar 不採用」との整合（scope 限定を明示）**: あの却下は **lateral 進入 margin の二重 bar**（capture volume の lateral 定義の複製）に対するもの。Z_FIRE_DEPTH は (i) 別軸（深さ）の **fire 時刻条件**で capture の再定義でない（authorizer 不変）(ii) 既存定数の式 (iii) banked §S3.3 premise「**pin = 既成着座の保持装置**」の直接執行 — rim 進入は着座の**形成中**であり保持すべき「既成」でない。%12 が深部案を「衝突」として自制した判断は当時の裁定文言に忠実 — scope を限定するのは定義者の仕事。
- **81-cell 接地（p5 自計測、§S3.2 side 定数と同法〔構造式 + 実測分布〕）**: fire-able **81/81** / anchor z ∈ **[830.604, 830.899]**（retention margin **≥ 5.10mm**）/ onset−fire ∈ [56, 112]f（早発火維持）/ release−fire **≥ 206f** / bar 以下は release まで**連続 81/81**（re-arm 曖昧性なし）。⚠**素朴 bar 829（=groove_z）は 27/81 で fire 不能** — producer 静止高が 827.714-829.715mm と cell 変動（**固定深さは固定段と同じ罠** — bar は静止高分布の上に置く）。
- **凍結 anchor（canonical、off-by-one 規約込み）**: run_start **2465** → **fire_label 2468 / fire_step 246 / anchor_state f2467 / anchor z 830.640mm**。hard bar `fire_step ∈ [242,250]` 維持（246 ✓）。
- **DR carry 登録**: bar headroom = 831 − 829.715 = **1.285mm** — DR が静止高を +1.3mm 超上げると fire 不能（fail-closed no-fire、検出器 = Q3 supervisor fire 率 = loud）⇒ **DR-ON 日に bar 再検**（C2-margin MED carry と同 pattern）。
- **%12 の測定 legs 5 本 = ADOPT**: expected anchor z 凍結（830.640 / band [830.604, 830.899]、drift loud）/ L-D に pin eq \|efc_force\| max / release・done 時 seat z / retention 述語 fire→done continuity（本 REVISE 下では **PASS 期待** — ratify 下では predicted-FAIL だった）/ §11 shift 宣言。
- **§11 宣言 delta 更新**: fire 254 → **246**（canonical −8 step）・latch 242 ≺ fire 246（**+4 step の実 gap** — rim 規則の同/翌 step 隣接より分離明瞭）・fire 後の残押込 ≈ **1.8mm**（rim 規則の 7.0mm から縮小 — fight は微小化、efc leg は測る）。

**§8.11.3 Q-5 = GRANT（/pre-check 配置の supersession pointer 授権）**
- 本 chunk（訓練なし・probe のみ）について、chain §6-3 の順（impl → probe → /pre-check → two-key）が §21.4:763-765 の字義「実装前」を supersede。**intent（未批准 (d) 意味論での訓練禁止）は training-ready 禁止（§S4.3-2 + §12-5）が chunk を跨いで保持**するため不変。gate② 再走の前例（/pre-check は landed code に対して走った）に一致。charter §2-4 への 1 行 pointer 追記を授権。

**§8.11.4 Q-8 = 訂正 #13 + K 根拠文の downgrade 批准**
- (i) **訂正 #13**: §8.10.4 の「§8.4-6」は dangling（§8.4 は項 1-5 — raise 3 列挙の実体 = prereg §2-6）。bank 時の pointer fix 授権。
- (ii) **K=3 根拠文の地位 = downgrade を批准**: rim 境界の「数値 wobble」は canonical 実測で不支持（単調 ~0.13mm/f・flicker 0）、深さ境界の bounce も **0/81**（p5 実測: first-deep 後 10f 以内の再浮上ゼロ）⇒ K=3 の地位 = **保険 + policy-era swing-through hook**（遅い通過が dwell し得る誤発火への防波堤 — §12-6 D-b carry に concur）。**値 K=3 は凍結のまま**（downgrade は根拠の地位であって値でない）。

### §8.12 🔒 prereg v0.4 設計軸 verify = **CONFORM — PASS〔p5 設計軸〕**（v1.5、2026-07-17 12:4x — 対象 = `PIN_D_TRIGGER_PREREG_RSTECHLEAD_20260717.md` v0.4 全文〔§0-§12、447 行 p5 全読〕。凍結値は p5 自計測・%12 独立再測・prereg 記載の**三者一致**）

**条項別（§8 裁定 → v0.4 freeze の照合、全 ✅）:**
| §8 裁定 | v0.4 | 判定 |
|---|---|---|
| §8.10.1 K=3 physics frame・strict consecutive | §2-1/2（深さ leg False もリセット明記） | ✅ |
| §8.11.2 深さ leg（Z_FIRE_DEPTH_M = groove+R/2 = 0.831・新 literal ゼロ・fire ⊂ authorizer strict 化） | §2-2（home = rc SEAT bars 同居・hunk 分離） | ✅ |
| §8.1-4 fire 対象 = identity body / §8.4-4 fire-once・ep 内 re-fire 不採用 | §2-3/4 | ✅ |
| §8.4-1 条件置換（call site :1221 不動） | §2-5（+hold 下 label 意味論 = D-b carry へ — 適切な scope 外送り） | ✅ |
| §8.10.4 非 raise + raise 3 限定 | §2-6（+mjm-None sentinel init = Q-3 の −1 意味論を全経路で成立 — bar 超過） | ✅ |
| §8.10.2 same-snapshot（load-bearing） | §2-6a 逐語 + **L-C(d)-(vi) 毒殺型 unit**（値照合単独は fail 不能 → 摂動で re-read 実装を判別 = 「fail し得る計器」教訓の正しい適用 — bar 超過） | ✅ |
| §8.10.2 containment-by-identity | §2-6b **cache+hoist**: 同 predicate + 同 rc bars + **同 cached clip set** — `clip_geoms_at` の mj_forward `:870`（p5 自読）を per-frame に持ち込まない解消形。static geom（body-0）は post-build 不変ゆえ cache 正当・count assert が BrokenSelector 意味論保存。⭐**audit は cache 非依存の live rescan 維持**（CC6-6）= 証拠計器が fire 経路の cache を信用しない — §15.4 の独立性構造の正しい保存（bar 超過） | ✅ |
| §8.1 (B) identity・fail-closed | §2-7/8 | ✅ |
| §8.2 mismatch 3-class 非 terminal | §2-9 + L-I fixtures | ✅ |
| §8.5+§8.10.3 8 fields・window 意味論・counters | §2-D（+window↔episode 1:1 構造論証 + collector 読取 read-before-reset 凍結 + **production dormancy 宣言**〔既定 = flag OFF ∧ budget 230 < fire 246 → 7/8 sentinel が正常と宣言〔pN B3 records-fix: pin_seat_seg=seat identity は常時 populated、実 npz field-wise = prereg §10 Run B〕 = no-silent-cap の正形〕） | ✅ |
| §8.11.1/§8.11.2 凍結 anchor（式 run_start+K・2465→2468/246・830.640・band・margin ≥5.10・hard bar・rim 値は非凍結） | §2-10/11/11a（三者一致。live probe 実測 → standing anchor 化も凍結） | ✅ |
| §8.6 両 release 定義 assert・§8.11.2 ADOPT legs 5 本 | L-D(d)（efc max / seat z / retention continuity **hard PASS 期待**） | ✅ |
| 宣言 delta（fire 254→246・latch 242 不変・**anchor 深度 = pin 意味論変化として宣言**・flag-OFF byte 恒等） | §11 + L-F1(d)/L-F2(d)（L-F1 の「trigger 非感応 = out-of-scope tripwire」開示は正直で正 — trigger 論理は L-C(d)+L-F2 が覆う） | ✅ |
| §8.8 (iv) 繰延・§12-5/D-b/DR carry | §2-13 + §12-5/6/8（B4 は **K+1 physics frame 単位明記** = 曖昧さの B4 継承防止 — bar 超過） | ✅ |
| additive-only（D1 bar）の実測化 | **L-H2**（HEAD vs bundle collector の既存 9 arrays byte 一致 + delta 過不足ゼロ — v0.2 に無かった測定 leg の新設） | ✅ |

**非 blocking 注記 2 件（bank 時 fold 授権）:**
1. **wrong-clip fire の宣言追加**（§11 へ 1 行）: capture check は ∃-認可 clip（loop 形 = §20 canonical の帰結・N-clip 前方互換）ゆえ、探索 policy が identity body を**他方の認可 clip** volume 深部に K frame 置けば wrong-clip weld が成立し得る。実測 81/81 で不到達（identity body は C1 前に C2 近傍へ行かない — I4 leg C の straddle 0 と整合）・帰結 = **保守的 dead-end**（C1 crossing MISS → G3 不到達 → false success 不能・reset で clear・npz `pin_eq_id`/`pin_anchor_xyz` で可視）。設計変更不要 — 宣言のみ（clip 名指し制限は §20 loop-form 哲学に反する）。
2. **残押込の私の「≈1.8mm」= 算術ずさんの自認**: 830.640 − 828.653 = **1.987mm** — %12 の 1.99-2.01 が正で、「方法差」の半分は私の丸め。§11 の「≈1.8-2.0」表記に concur、確定 = L-D 実測（凍結 bar でないため訂正番号は付さない — ≈ 注記の精度不足として記録）。

**授権 1 件**: §8.10.1 への **訂正 #12 pointer 1 行**（#10/#11 と同 pattern: 「⚠ 本項の凍結値 2429/242/式 first_true+(K−1) は訂正 #12〔§8.11.1〕で supersede — 現行 = §8.11.2/§2-11（2468/246/run_start+K）」）— %12 bank 時に追記可。

**verdict**: **CONFORM — PASS〔p5 設計軸、prereg v0.4〕** — 実装着手可（chain = §8.9: 実装 → probe/legs → /pre-check → two-key〔p5 設計軸 + pN evidence 軸〕）。pN evidence 軸 pre-bank review = 並行（bank = claim deadline は pN 合流後、(a)(b) 前例どおり）。standing 不変: training-ready 禁止 = (d) two-key PASS + §12-5 cell-2 追補まで。
> ⚠ §S4.7 pointer（%12、授権 = §S4.7.3）: 本行の「(d)」= **(d-a) + (d-b)**（§S4.7.1 — 解除 = 両 two-key ∧ cell-2、(d-a) 単独では解除しない）。

### §8.13 🔒 (d-a) live probe の fire_label 照会への裁定（v1.6、2026-07-17 16:2x — 入力 = `pin_d_trigger_probe_result_cell_x0_y0.json` + recording npz 直読。挙動 bar は全 PASS、唯一 `fire_label_exact=false`〔2462 vs offline 2468〕で `L_D.PASS=false`）

**独立検証（p5 自読・自計測、message narrative 非依拠）:**
- **recording npz に `step_f` key 不在**（keys 実列挙: frame_idx/…/cable_xyz/cable_quat — route-clock `step_f` は prep で派生、raw index でない）⇒ offline npz-index と live route-clock は**別クロック**（私の offline 2468 = npz array-index、live 2462 = route-clock）。
- **決定的機構: live は cable を再シム（npz を byte-replay しない）** — npz z @frame **2462 = 831.321mm（深さ bar 831 の【上】）** vs live 発火 anchor **830.71mm（bar の【下】）**。同 frame で live cable が ~0.6mm 低い ⇒ 深さ bar を route-clock で数 substep 早く跨ぐ。offline `run_start=2465`（z=830.919）→ 2468（z=830.508）を p5 再計算で再現。
- **hard bar は全 PASS**: fire_step **246 ∈ [242,250]** / anchor_z **830.71 ∈ [830.604,830.899]** / dwell=K=3 / eq_id=27（identity 正）/ audit PASS / **G3 latch 242 ≺ fire 246（+4 gap）** / **retention_max_after_fire 831.07mm < rim 836（margin ~4.9mm）** / ep1≡ep2 決定的（L-D2 hard・reward diff 0）/ reset+refire。

**(a) governing = §2-11（drift-loud・standing-anchor）— `fire_label` の exact 化は誤り:**
- 私の banked 設計意図（§8.11.1/§2-11、§8.12 で verify 済）= **hard timing bar は `fire_step ∈ [242,250]`**（粗・÷10・小 frame 差にロバスト）／ **`fire_label`・`anchor` は drift-loud、初回 live 値を standing anchor 化**。prereg §5 本文も「drift=loud・two-key 判定」で一致。
- ⇒ probe 実装の **`fire_label_exact` 硬直 bar は §2-11 と §5 本文の双方より厳しく、`L_D.PASS=false` を誤設定**。**挙動は CONFORM**。fire_label を exact に縛る根拠は**存在しない** — offline 2468 は **byte-replay 前提の近似**で、live は再シムゆえ frame-exact 一致は原理的に起こらない（0.07mm anchor 差がその証拠）。
- **是正**: probe PASS 論理を **fire_label exact → standing-anchor-drift** へ（fail 条件 = `fire_step` が band 逸脱 ∨ anchor が band 逸脱 ∨ latch⊀fire。fire_label 自体は記録・loud のみ）。**bar 緩和ではない** — exact-frame 粒度の bar は元々物理的に不成立で、hard timing 保護（fire_step band + anchor band + 順序 + retention）は不変。

**(b) standing anchor = live 2462（offset-6 は機構帰属済・妥当）:**
- **YES** — §2-11「初回 live 値を standing anchor 化」どおり `fire_label` standing anchor = **2462**、`anchor_z` = **830.71mm**（band 内）、`fire_step` = 246。以後の drift は 2462 に対して測る（offline 2468 に対してでない）。
- offset-6 = **固定規約 offset ではない**（step_f が npz に無く、差は live 再シム差が駆動）= **live-physics 量**。offline npz 2468 は **anchor から RETIRE**（byte-replay 近似ゆえ）、live 2462 で supersede — **records-fix**（§2-11「期待 2468」を live standing anchor へ差し替え、%12 が [RESULT] + §2-11/§5 に反映）。

**⭐ 設計判断の vindication（記録）:** 深さ leg REVISE（§8.11.2、rim 発火 ratify を不採用）は **live で確認** — retention_max_after_fire **831.07mm < rim 836**（margin ~4.9mm、私の予測 ≥5.10mm に整合）・保持中の seat_z trace は 830.7 で平坦（weld との fight 微小）。rim 発火を ratify していれば本 leg は retention が rim 際/超で G6-death を示したはず。live data が REVISE を裏書き。

**chain / scope**: 本 §8.13 は **fire_label 照会への設計軸裁定**であって (d-a) 全体の two-key verdict ではない。two-key は **%12 が probe PASS 論理を是正（exact→standing-anchor-drift）+ live standing anchors を [RESULT] 記録・§2-11/§5 records-fix + L-F1/L-F2/L-H/L-H2/L-C(d) 毒殺 leg の結果提示** → その producing commit で p5 設計軸 + pN evidence 軸。**⛔bar 緩和はしていない**（hard timing/anchor/順序/retention は不変、fire_label のみ設計どおり drift 化）。

### §8.14 🔒 (d-a) post-land two-key = **CONFORM — PASS〔p5 設計軸〕** + 3 MEDIUM carry ACK（v1.7、2026-07-17 18:5x — producing commit `e8edd96a3e`。producing commit で verify〔HEAD narrative でない〕・独立 legs 走行）

**独立検証 legs（p5 自走・自読、producing commit `e8edd96a3e`）:**
1. **tests 31/31 自走** = 隔離 worktree @ `e8edd96a3e`・per-test driver・env7 直呼び **31/31 PASS**（既存 17 + (d-a) 14: same-snapshot poison / depth-leg / dwell-reset / fire-once / identity-body / identity-none-fail-closed / capture-check-shares-cache / audit-independent-rescan / broken-selector / quiet-outside / mjm-none-raises / n1n7-unchanged / reasons-payload / mismatch-3class）。%12 の L-B(31) を独立再現。
2. **landed K-dwell 本体 自読**（`newton_route_env.py` `_maybe_activate_c1_pin`）= 裁定と精密一致: `seat_world = bq[seat_body,:3].copy()` **単一 snapshot** を check と authorizer に渡す（§2-6a same-snapshot）/ `captured ∧ z ≤ Z_FIRE_DEPTH_M`（§8.11.2 深さ leg）/ strict consecutive dwell reset / fire-once witness / identity None → fail-closed。
3. **`clip_capture_check` + authorizer 自読** = **同一 `_clip_capture_cache` + 同一 predicate + 同一 rc bars**（§8.10.2 containment-by-identity 機構化）・per-frame mj_forward ゼロ（hoist 済）・non-raising・count assert on cached set。authorizer も同 cache を消費（`for cx,cy,g,y_win in _clip_capture_cache`）。
4. **毒殺 test 自読** = `test_pin_da_same_snapshot_poison`: K 到達 frame で `bq[seat_body]`=(9.9,9.9,9.9) に**汚染 AFTER snapshot** → authorizer が **pre-poison 値受領**を assert（re-read 実装なら 9.9 で FAIL）= §8.12 の「値照合単独では fail 不能」要件を満たす **fail し得る計器**。
5. **probe result 自読**（committed `pin_d_trigger_probe_result_cell_x0_y0.json`）= `L_D.PASS=True`・全 check True・`fire_label_standing_anchor=2462`・`fire_label_drift_vs_anchor=0`（非 gating）。L_D2 hard timeline PASS・L_E PASS。
6. **§2-11 records-fix 自読** = offline 2468 **RETIRE** 明示 → live standing anchor **2462**、fire_label 非 gate（§8.13）反映済。

**§8.12/§8.13 two-key checklist（全 ✅）:**
| bar | 判定 | 根拠 |
|---|---|---|
| same-snapshot 毒殺 leg | ✅ | `.copy()` 単一 snapshot + poison test PASS（fail-able 計器） |
| anchor drift | ✅ | anchor 830.71 ∈ band [830.604,830.899]・standing anchor 記録・drift 0 |
| 宣言外 delta ゼロ | ✅ | L-F1 flag-OFF **byte 恒等**（final_digest 一致・obs.npy sha 一致・source 恒等 `git diff *.py`=∅ 確認）/ L-F2 flag-ON = latch列不変・宣言外 obs/reward/identity 変更なし・delta = 宣言 fire-timing のみ |
| retention continuity | ✅ | retention_max_after_fire **831.07 < rim 836**（margin ~4.9mm）・fire→done continuity |
| fire_label 非 gate（§8.13） | ✅ | probe PASS 論理が fire_label を除外（`checks["PASS"]=all(checks)` に fire_label 不含）・standing anchor 2462 |
| containment-by-identity（§8.12 bar 超過） | ✅ | 同 cache 共有・audit は cache 非依存 live rescan（`test_pin_da_audit_independent_rescan` PASS） |
| dormancy（§8.12） | ✅ | L-H Run B budget cutoff = 7/8 sentinel (pin_seat_seg=seat identity 常時 populated、pN B3)・windows_with_done 0 |
| L-H2 additive-only（§8.12） | ✅ | 既存 9 arrays byte 一致・additions = exact set 過不足ゼロ |

**⭐ 設計判断 vindication（再確認）**: 深さ leg REVISE（§8.11.2、rim ratify 却下）を live が裏書き — retention 831.07 < 836。rim 発火なら retention が rim 際/超で G6-death を示したはず。

**3 MEDIUM carry ACK（/pre-check、two-key reviewer 明示 ACK 必須）:**
- **M1 DR-headroom 1.285mm（§12-8）= ACK**: depth bar 0.831 の headroom（829.715 = 私の 81-cell 実測 max static height に対し）は保守側 fail-closed（DR が静止高を +1.285mm 超上げると **no-fire**、false-fire でなく）・検出器 = supervisor fire-rate。DR-ON 日に bar 再検（C2-margin MED と同 pattern）。私が §8.11.2/§12-8 で登録した carry — 妥当。
- **M2 byte-neutral = sim-replay scope（ACK + scope 明記）**: L-F1 の byte-neutral は **phys/obs/reward/done の sim-replay** に限定。artifact 面は §11 宣言どおり（8 npz + 3 manifest additive）で L-H2 が bound。**DAPG/BC loader の additive-key 許容（D0-R3 規約）は本 legs で未 assert** — これは **consumer 側検証 = (d-b)/訓練時代**（trainer が実際に npz を ingest する gate）の担当。honest scoping として ACK、(d-b) carry に含める。
- **M3 latch≺fire dual-clock +4 margin = ACK**: latch 242 と fire 246 は別 clock 経路の比較で +4 step margin により成立（§8.13 の coarse-bar 意図どおり）。**cell-2（§12-5）は gap 縮小に注意** = watch 登録に concur。

**非 blocking 1 件（docs-must-not-lie、%12 fold 授権）**: `pin_d_trigger_probe.py:12` の module header docstring「fire_label == 2468 exact」は実 PASS 論理（§8.13 是正済・非 gate）と矛盾する **stale 記述**。挙動・PASS 判定は正（header comment のみ未更新）。次 commit で header を「fire_label = standing-anchor / non-gate（§8.13）」へ 1 行修正を推奨。

**verdict**: **CONFORM — PASS〔p5 設計軸、(d-a) post-land〕**。two-key の evidence 軸 = pN（legs 実測）。**standing 不変（§S4.7）**: training-ready 解除は **(d-a) ∧ (d-b) 両 two-key ∧ §12-5 cell-2** — 本 (d-a) two-key PASS はその **1 鍵のみ**。(d-a) は training-ready を解除しない。次 = (d-b)=D-b window gate（訓練 drive 分岐配置 + K 再検証 + hold label）+ cell-2（DoD-7 後）。

## §9 🔧 (d-b) D-b window gate — 設計 framing（v1.8、2026-07-17 21:1x — 入力 = `PIN_DB_WINDOW_GATE_SCOPING_RSTECHLEAD_20260717.md`〔21:01〕+ p5 code 自読。**framing であって裁定でない** — 各 Q の 🔒 裁定は §9.6 materials→ruling が生む）

**doc-home 決定**: (d-b) は本 (d) charter に §9 として拡張する（別 doc を作らない）。根拠 = §S4.7「(d) = (d-a) + (d-b)」= 単一 node ／ §1 scope「(d) policy-drive trigger」の本体は ik_chord（= policy path）ゆえ (d-b) こそ charter 表題の実現 ／ (d-a) 裁定 §8.1-8.14 は凍結・§9 は ADD のみ。framing≠裁定の境界: 本節は gate 構造 + 問い再枠付け + **方向（materials 依存で確定）**を出す。

### §9.1 grounded code reality（p5 自読 2026-07-17、producing commit = HEAD `5b0de67402`）

- **drive 既定 = `ik_chord`**（`newton_route_env.py:496`、`_dm = self.cfg.get("route_drive_mode", "ik_chord")`）= step 単位 batched-IK + residual 駆動 = **policy/訓練 path**。`feedforward` は recording-replay path（(d-a) が配線した先）。
- **pin call site = 1 箇所のみ**（grep 確認）: `:1225`（FF branch）+ 定義 `:1821`。**ik_chord branch に `_maybe_activate_c1_pin` call 無し** ⇒ 既定 drive では trigger が一度も評価されない（pN B1 = 1 call site を on-disk 確認）。
- **frame 意味論の非対称**:
  - FF（`:1215-1226`）: `_maybe_activate_c1_pin(route_steps, step)` `:1225` が `_physics_step_all` `:1226` の**前**（pre-step）。§8.13 の `fire_label = run_start + K` off-by-one はこの layout で導出。
  - ik_chord（`:1252-1281`）: `_physics_step_all` が loop **末** `:1281`。`joint_q.assign` `:1272-1273` は joint 配列を書くのみで **body_q を進めない**（body_q は物理 step のみが更新 — materials で step 前後不変を実測確認）⇒ **`:1281` の前に置いた pin call は FF と同じ「前 frame の body_q」を読む** ⇒ off-by-one が drive 間で不変。
- **⭐ 核心 finding（framing を左右する）**: `_maybe_activate_c1_pin`（`:1841-1860`）は drive-mode **agnostic** — 必要な外部入力は `(route_steps, sub_i)` の 2 個のみ。かつ `route_steps` は **`fired_at_frame` LABEL** の材料（`:1846` `t=…route_steps[0]`、`:1858` `step_f[t]+sub_i`）としてのみ使われ、**発火判定（capture ∧ depth ∧ K-dwell = 純 body_q 幾何、`:1850-1856`）は route_steps を使わない**。⇒ **Q-Db3 は「label 供給」問題であって「発火 gate」問題でない**（framing 上の再分類）。
- **route_steps 供給の gap**: ik_chord で route_steps は `:1251` = `grasp_actuation` 真の時のみ計算。`grasp_actuation` 偽（pure residual/IK sub-mode、`:1268-1271`）では未定義。FF は `:1210` で無条件計算（`route_t` にのみ依存）。
- **gate② 計器の同居**: seat 述語 `_seat_crossing` `:1304`（ruling `REWARDDESIGN_GATE2_SEAT_PREDICATE_RULING`）は同 file。pin は幾何を保持（INVARIANT #5）→ cable 幾何を変える → seat 計器の読みを変える ⇒ policy-driven fire timing は gate② の reward/obs 計器に結合。

### §9.2 D-b gate が決めるもの + acceptance の (d-a) との差

- **決めるもの**: policy-drive（ik_chord）path で **どこに**（Q-Db1 配置）**どの frame 意味論で**（Q-Db2 clock）**どの label 契約で**（Q-Db3/Q-Db5）pin trigger を評価するか + **K の policy 時代 validity**（Q-Db4）+ **gate② 結合の宣言**（Q-Db6）。機構（capture ∧ depth ∧ K-dwell、identity = recording 由来 `_pin_seat_seg`、fire-once latch、`authorize_clip_pin` 単一書き手）は (d-a) から**不変で carry** — (d-b) は call site の**追加**と**評価配置**のみ。
- **acceptance が (d-a) と違う点（framing の要）**: (d-a) の fire_step hard bar `[242,250]` は **FF-replay の recording-onset 窓**に接地。ik_chord では recording-onset 窓が無い（fire は policy が cable を seat させた時）⇒ **`[242,250]` bar は (d-b) に転写しない**。(d-b) の正 leg = 「fire が**正しい**（capture ∧ depth ∧ identity ∧ K を満たす real seat でのみ）」で、特定 frame ではない。fire_label は §8.13 どおり drift-loud・非 gate。

### §9.3 Q-Db1..6 再枠付け + framing 方向（materials 依存）+ 要 materials

- **Q-Db1 + Q-Db2〔配置 + off-by-one = 連結〕**: 一つの決定。**方向**: pin call を ik_chord の **pre-step（`:1281` の直前、joint assign `:1273` / grip `:1278` の後）**に置く ⇒ 前 frame body_q を読む = FF `:1225` と同一意味論 ⇒ §8.13 `run_start+K` が**再導出なしで転写**（single-clock invariant、parsimony + SSOT）。post-step 配置は新 off-by-one を要し drive 間で clock 分岐 = disfavored。**要 materials**: (i) ik_chord pre-step で body_q が「前 frame 物理結果」であることの実測（joint_q.assign が body_q を進めないこと — 1-frame probe で step 前後不変）(ii) FF と ik_chord で同一 cell の fire_label 導出が同一式に載る trace。
- **Q-Db3〔route clock 供給〕= label 供給問題（発火 gate でない、§9.1）**: **方向**: route_steps を ik_chord loop 頭で **無条件 hoist**（FF `:1210` と同型、`route_t` にのみ依存）。ただし「pin を `grasp_actuation` 偽 sub-mode で arm するか」は別の設計 sub-問（そのモードで腕が route/grasp していなければ pin は本来不発）。**要 materials**: (i) 訓練で active な ik_chord sub-mode 列挙（grasp_actuation 真/偽 × residual）(ii) 各 sub-mode で route_t 有効性 (iii) grasp_actuation 偽で pin を arm すべきか（幾何が seat に達し得るか）の到達可能性。
- **Q-Db4〔K=3 の policy 時代 validity〕**: K=3（6.25ms、§8.10.1）は FF-push 文脈で裁定。遅い policy swing が K=3 を **spurious dwell** し得る（CC3-4、prereg §12-6）。**方向**: K は config（`PIN_TRIGGER_DWELL_K`、既に config 化済）— design-now = K の bound + 「なぜ K=3 が既定か」+ **empirical 再検 criterion** を宣言。**empirical 実測は trainer 未起動ゆえ deferred leg**（(d-a) DR-ON M1 / cell-2 DoD-7 と同 pattern）。**要 materials**: (i) spurious-dwell worst-case（policy が depth bar 近傍を K frame 滞留する幾何条件）(ii) K↑/depth bar↑ の trade（false-fire vs no-fire、§12-8 headroom と同軸）(iii) empirical gate の DoD（trainer 起動後に fire-rate/fire-step 分布で spurious 検出する supervisor 契約）。
- **Q-Db5〔hold 時代 label 意味論〕**: `fired_at_frame = step_f[t] + sub_i`（`:1858`）の held-world（`hold_mask`、prereg §2-5）下の意味。(d-a) probe は hold 不使用。**方向**: label は **provenance-only・drift-loud・非 gate**（§8.13）ゆえ held 下の値も gate でなく記録 — 設計は「何を記録し、hold 中は route clock 凍結ゆえ step_f[t] も凍結する」宣言で足りる。**要 materials**: hold_mask 下で route_t 凍結する経路の cite（`:1213` hm / `:1279`）+ label が held 中に何を指すかの 1-episode trace。
- **Q-Db6〔reward-dynamics 結合 / gate② coupling〕**: policy-drive fire は recording-onset でない ⇒ reward-dynamics delta を宣言。pin fire → cable 保持 → `_seat_crossing` `:1304` が pinned 幾何を読む。**論理**: pin が**正しく**発火（real seat のみ）すれば seat 計器も正しく読む（両者は同一幾何真実を読む）⇒ **pin の fire-correctness は gate② 計器 validity の前提**。⇒ Q-Db4（spurious fire 防止）と Q-Db6 は**連結**（K の仕事 = spurious fire を殺す = gate② corruption を防ぐ）。**方向**: (d-b) 設計は進行可。ただし **gate② = FAIL / owner-chain pending（LEDGER:57-58）**ゆえ policy-driven fire を**未批准 reward に配線する landing は gate② owner chain と sequencing 調整**（設計 block でなく landing sequencing flag）。**要 materials**: (i) pin fire が seat 計器・reward・obs に与える delta の因果 DAG（§21.4:763 reward-coupling 宣言の policy 版）(ii) fire 後 reward が「locked high」になるか（weld 永続 → seat 永続）の episode trace と、それが physical truth（clip が保持）と一致するかの確認 (iii) gate② owner chain（/reward-design 再走 + p5 verify + /pre-check）との依存関係表。

### §9.4 不変制約（(d-b) で動かさない — §4 に加えて）

- INVARIANT #5 clip-only: (d-b) は新 kinematic 例外を作らない — 既存単一書き手 `authorize_clip_pin` の**評価時刻/場所**のみ追加（scoping §3）。
- timeouts 純度（§4-2）/ identity-persistence（§4-3）/ 成功述語は幾何を読む・pin 状態を読まない（§4-4）/ fire-once latch = 全て carry 不変。
- training-ready 禁止（§4-5 + §S4.7）: (d-b) two-key PASS でも **(d-a) ∧ (d-b) ∧ §12-5 cell-2** の 3 鍵が揃うまで解除しない。本 §9 は解除を約束しない。

### §9.5 deferred legs + sequencing

- **deferred（trainer 未起動）**: Q-Db4 empirical K + live policy fire dynamics = deferred leg（(d-a) DR-ON M1 / cell-2 DoD-7 と同 pattern）。design（配置 + framing）は今進む。
- **M2 carry 引受け（§8.14）**: DAPG/BC loader の additive-key 許容（D0-R3）の consumer 側 assert = (d-b)/訓練時代の担当 — 本 gate の materials/legs に fold。
- **gate② 依存**: Q-Db6 の結合は reconcile（assume でない）。landing は gate② owner chain と sequencing。
- **V0 依存（PLAN-KEEPER）**: fork-B substrate V0 acceptance pending — ik_chord drive-branch 構造が V0 で変わるなら call site hard-wire 前に flag（設計は進行可、landing は待ち得る）。

### §9.6 materials 要請（%12 へ、統合）+ 次 gate step

- **要請**: /reward-design 4 artifacts の (d-b) 版 + §9.3 各 Q の measurements/options。特に (i) ik_chord pre-step body_q-read 実測（Q-Db1/2）(ii) 訓練 active な ik_chord sub-mode 列挙 + route_t 有効性（Q-Db3）(iii) spurious-dwell worst-case + empirical K DoD（Q-Db4）(iv) pin→seat→reward 因果 DAG + gate② 依存表（Q-Db6）(v) hold 下 label trace（Q-Db5）。
- **gate chain**: 本 §9 framing → %12 materials → **p5 §9.x 裁定**（Q 順）→ prereg → 実装（call site 追加 + 条件、explicit-path atomic）→ probe → **/pre-check** → **two-key**（p5 設計軸 + pN evidence 軸）。training-ready = (d-b) two-key ∧ (d-a ✓) ∧ §12-5 cell-2。
- **framing verdict**: **FRAMED**（gate 構造 + Q 再枠付け + 方向確定、🔒 裁定は materials 後）。0-commit — bank = %12。

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
| (d-b) code reality（§9.1） | `newton_route_env.py:496`（drive 既定 ik_chord）/ `:1215-1226`（FF pin call `:1225` pre-step ≺ `:1226` step）/ `:1252-1281`（ik_chord physics `:1281` loop 末・pin call 無し・route_steps `:1251` grasp 時のみ）/ `:1841-1860`（helper drive-agnostic・route_steps=label のみ・fire=幾何 `:1850-1856`）/ `:1304`（`_seat_crossing` gate②）|
