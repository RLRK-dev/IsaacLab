# DQ7 mini-test — %9 design-verify 統合回答 (verbatim record) + %12 disposition

**Provenance:** %9 OPS-SUP → %12、2026-07-05 09:40 JST (herdr 直送、本 file は %12 による verbatim 転記 + disposition 付与)。
**Authority chain:** Rs 標準権限 08:5x → %12+%9 JOINT-DECIDED (banking `231639c0d1`) → 本 design-verify = mini-test [VERIFY] 段の %9 duty (07-04 19:33 分担)。
**%12 disposition (09:4x):** 全項 CONCUR — 矛盾なし。**5体 [VERIFY] debate LAUNCH を %11 に授権** (pin fold 完了を %11 自己証明で可; %12 の精査は debate DECIDE review + fire 授権段で実施 — fire は従来どおり token + two-key + Rs loud-notify で gate)。

---

## %9 回答 verbatim (09:40)

[3a span-preserving blend] **CONCUR / ADOPT** + 浄化論理は「精密化すれば HOLDS」+ 実装 pin 4 点。

**敵対的検証の結論**: projection が本物の失敗モードを隠す側面は **管理可能な 1 blind spot のみ**で、歴史的 phenomenology とは衝突しない — (i) B1 の span 開き = relative-delta apply-path 積分 artifact で fork-(iv) が既に除去済 (ii) de-risk divergence = γ⊥/null-beat (center/tracking 軸) で span 関与の報告なし (iii) naïve blend の span 縮み (三角不等式、disagreement 最大 = off-path = まさに β-mix が働く所 — %11 の指摘は正) は expert にも policy にも由来しない **blend-chimera artifact** であり、これが rollout 失敗を作ると「policy 品質由来の逸脱」と区別不能 = A-vs-B verdict の真の confound。projection はこの chimera 除去 = **浄化は成立**。

**精密化 (pre-register 文言用)**: 浄化されるのは γ⊥ 計算そのものではなく **visited-state 分布と episode validity** (γ⊥ = offline probe で blend 非依存)。文言案:「A-vs-B は center 軸 restoring を測る。span 軸 = 構造 guard (INV#2 は探索対象でない) + **raw-span telemetry を informative 報告**」。

**blind spot の対処 (pin-t)**: policy の生 span 病理が β>0 iter の執行で発現しない件 → **telemetry で loud 化**: per-step ‖s_policy − s_tp‖ (s=tgt_r−tgt_l、mm) を log、p50/p90/max を report。gate にしない (informative)、p90>10mm なら caveat 行。cost ~0。iter3 β=0 は生 policy 執行なので span 挙動はそこで physically 発現 = endpoint が実測を供給。

**実装 pin (code 読解由来、%11 packet の「after :852」は要修正)**: 現行 code は expert `_tp` block (:843-855) が **executed solve_ik_dual (:838) の後 = 純 logging 位置**。mix には (o1) `_tp` 計算を executed solve より前に hoist (o2) **順序 = blend → guard-2 → 単一 solve_ik_dual** — mix を guard-2 (15mm rate-limit :830-834) の後に置くと expert-pull step で rate-limit が silent 無効化される (off-path では expert target は ee から >>15mm = restoring そのもの) → blended target に guard-2 を適用し per-step 15mm semantics を uniform 維持 (restoring は複数 step の servo で実現、E15 設計と整合) (o3) H2 feasibility logging (`ik_resid_tstar_series` :853) は **生 _tp に対して不変継続** (blend 後 target で測ると計器意味が変わる) (o4) **β==0.0 は blend block 全体を bypass** (byte-identity + iter3 = 真の policy 執行 = de-risk 比較可能 endpoint)。

**span-vector 供給元 = expert `_tp` 同 step に CONCUR** (%12 と一致) — :846-851 の recenter が既に「common-mode; span-preserving」semantics で `_tp` の span = canonical schedule そのもの。s_tp = _tp[0:3]−_tp[3:6] を流用。

**KNOWN_ALTERNATIVE 記録 (NHA 用)**: Ross 2011 の確率的 per-step 切替 (w.p. β で expert pair を執行) は chimera を構成的に回避するが、**1 rollout/offset/iter の 2-3 点 monotonicity 読みに執行分散を注入する** → 決定的 pipeline (de-risk byte-identical) の読み安定性を壊すため棄却。packet に 1 行で。

(o5、09:38 統合) **--nominal-eps block は β-blend block から独立** (nominal′ leg は β=0 + eps → o4 の β=0-bypass が blend を殺しても eps は生きる構成に) + 共通 ordering (pre-guard-2; 0.5mm ≪ 15mm ゆえ guard 実質不発だが順序 uniform)。

[3b β-schedule pin] **β = (iter1 0.5, iter2 0.5, iter3 0)** を pin。%12 例 (0.5→0.25→0) も可だが劣後 — 理由:
- **leg-1 (budget 軸)**: iter1→iter2 が **同 β=0.5** → visited-shell 半径が iter 間で比較可能になり、γ⊥ monotone 方向 = 純粋な「aggregate 増分の budget 効果」(β 変化の分布 shift confound なし)。0.5→0.25 だと 3 点全てが異 β = 全方向読みが β-confounded (3c)。
- **leg-2 (artifact 軸)**: iter3 β=0 = de-risk と同条件の endpoint → B 仮説 (β=0-degenerate artifact) の直接 falsifier: β 誘導 aggregate で訓練後も β=0 rollout が diverge するか。0.5/0.5/0 は非増加 = Ross anneal として valid。
- **β=0.5 の選定根拠**: 半補正で drift 有界かつ off-path 質量 material の均衡点 (推測 — mechanism-reasoned; β 高過ぎ [0.8+] は shell 縮小 → 3-regime p90<2mm の immaterial 域に自ら入るリスク)。**ADAPT rule を pre-register**: iter1 off-path p90 <2mm (shell 過小 = β 過大) → iter2 のみ β=0.25 に降下 (1 回限り・loud log; この場合 leg-1 同β比較は void と明記、読みは leg-2 + 3-regime へ縮退)。iter2 でも <2mm → INCONCLUSIVE-design → Rs (16:14 LOCK どおり)。
- **GPU 予算検算**: 3 iter × 2 offset × ~15.5min ≈ 93min + band pair (nomA + ε-nominal′; nomA が run 計画に無ければ両方で ~31min) + retrain 90s×3 + og offline ≈ **~2.1-2.3h ✓ 1-3h envelope 内**、timebox ≤2d 余裕。code 増分 = β-mix ~30-60 LOC + --nominal-eps ~5-10 LOC (同一 L3 diff、file 2 のまま)。

[rider-1 ε 機構 re-spec (09:38 TIME-SENSITIVE 統合)] **premise 訂正を own する**: 私の「zero-code ε-IC」pin は誤前提だった — 私も on-disk 照合: :388 `round(float(...))` = 整数 mm 丸め (Python banker's rounding で round(0.5)=0) + rollout_offset の用途 = Opt-i′ schedule-source 照合 (declarative、scene 非摂動) + :215-229 mean-forward「CANNOT sample」— %11 の 3 発見すべて CONFIRMED。教訓は [[feedback-when-it-fails-verify-premises-first]] を自分の pin に適用し損ねた形。

**re-spec 判定 = %11 option (1) CONCUR (%12 lean と一致)**、%12 提案の適用形も CONCUR: --nominal-eps (flag-gated default-off、~5-10 LOC、L3 β-mix diff 同梱 = 同一 [VERIFY 5体]+RULE-CHECK chain、locked 非 touch、float 直指定で丸め moot)。option (2) 棄却 = 非 zero-code + 整数 1mm は floor でなく小 signal + 新 demo 録画コスト / option (3) 棄却 = band=0 恒真では 3-way 判別不能。

**測定意味の再定義 (over-claim 防止)**: 決定性 3 発見により「run-to-run stochasticity」は存在しないことが機構的に確定 — 残る問いは「小 config 差への軌道感度 (deterministic chaos)」。ε = executed EE-target center への deterministic per-step +0.5mm common-mode 加算 (軸 = mini-test offset と同じ dy 軸、+y 向き pin) = **forced-response 感度 probe**: 収縮的 (servo 支配) → band ~0.5-1mm → (I) 相当 / 増幅的 (cable 接触非線形) → band 大 → (II) 相当。**3-way 閾値 2/5mm 維持、label 改訂**: (I) RESOLVED-**smooth/common-mode** / (II) HOLDS-**sensitivity-dominated** / (III) 中間。

**falsifier 改訂 CONCUR**: eps flag set + byte-identical → wiring bug → STOP。
**追加 pin (contamination guard)**: nominal′ leg = **band 計測専用 — rows は aggregate/training に不混入** (dump のみ)。

[3c discriminator-under-β-mix] **懸念は実在 — read 構造の pin で by-construction 解消** (%11 adversarial #3「β masks divergence → false-B」も同時に潰れる):
- 機構: γ⊥ = retrained policy への offline probe (β 非依存) だが、β は **訓練データの shell 半径**を変える → γ⊥ 改善の意味が β 文脈依存。
- **pinned read 構造**: PRIMARY = (leg-1) iter1→iter2 同β の clean-{0,1}+off-path-row γ⊥ 方向 + (leg-2) iter3 β=0 endpoint の divergence-class 判定 (de-risk 軌跡との比較は offset-set 差ゆえ **定性** [divergent か否か] に限定)。**cross-β 方向 (iter2→iter3) 単独には verdict weight ゼロ** (annotation only)。
- **VERDICT 規則**: PERSIST(A) = leg-1 悪化 AND leg-2 divergent (off-path 質量 material 条件下) / RESOLVE(B) = leg-1 非悪化 AND leg-2 非 divergent (同条件下) / それ以外 = INCONCLUSIVE ladder (3-regime 16:14 → seed-repeat → Rs)。「expert-steered で見かけ収束」だけでは RESOLVE 不成立 (leg-2 が β=0) = #3 構造的に封じ。
- **materiality gate**: per-iter offpath_fraction + offpath_dist_mm_kept p50/p90 report (既存計装)。floor 未達の PERSIST/RESOLVE 主張は INCONCLUSIVE-underpowered。

**CONSOLIDATED PRE-REGISTER (packet へ verbatim fold 用、6 項)**:
1. PRIMARY read: leg-1 (iter1→2 同β γ⊥ 方向) + leg-2 (iter3 β=0 endpoint 定性 divergence 判定)。PERSIST/RESOLVE/INCONCLUSIVE = 3c 規則。
2. materiality: per-iter off-path fraction + p50/p90 報告必須; floor 未達 → INCONCLUSIVE-underpowered。
3. band leg: --nominal-eps 機構 (L3 diff 同梱、flag-gated default-off) で nominal′ = executed-center per-step +0.5mm (dy 軸) pair ×1; rows は band 計測専用 (aggregate 不混入)。3-way: p90≤2mm → %9 pin RESOLVED-smooth/common-mode / ≥5mm → pin HOLDS-sensitivity-dominated / 2-5mm → band 超のみ可読。gate 対象 = contingent immaterial-diagnostic + %9 07-04 pin のみ、主 verdict 非依存。falsifier: eps flag set + byte-identical → wiring bug → STOP。
4. span telemetry: per-step ‖s_policy − s_tp‖ log、p50/p90/max、informative (p90>10mm = caveat 行)。
5. β/iter + n_mixed を verdict log に; cross-β 方向 annotation only。ADAPT rule (iter1 p90<2mm → iter2 β=0.25、1 回限り loud) 発火時は leg-1 void 明記。
6. 3-regime immaterial-diagnostic (16:14 LOCK) + seed-repeat contingency = 不変継承。null-beat intersection = 報告 metric (verdict weight なし)。

W0-c v1.1: 8 修正反映を了解 — diff 軽量再確認は本 round 収束後 (5体 launch と並行可、block しない)。
%11 packet への評価: rider-2 訂正処理・KNOWN_ALTERNATIVES・adversarial scenarios の自己申告は誠実で質高い。上記 pin (o1-o4 + telemetry + pre-register 6 項) を fold すれば私の design-verify = **READY-for-5体**。

---
*%12 転記 2026-07-05 09:4x。0-commit (commit = 次 banking window)。*
