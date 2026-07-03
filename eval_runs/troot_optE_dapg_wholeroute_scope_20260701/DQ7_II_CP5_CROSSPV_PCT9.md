# DQ7 stage-(ii) CP-(ii)-5 OG verdict (STOP) — OPS-SUPERVISOR (%9) independent cross-PV (core verdict + 戦略転換点)

**Written: 2026-07-03 17:28 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `dq7_ii_cp3_batch/og/og_gate.json` + %12 §運用28。**依頼:** wave-1 と同 %12+%9 pattern で Rs escalation を裏付け。非 block。
**Constraints:** 0-commit / rollout 禁止 / read-only + this file + log.md。band=γ は CP-(ii)-5 のみ(適用済 instrument)。

## 0. §運用28 独立再抽出(og_gate.json 直読、%12 数値を再利用せず)

| metric | 独立抽出値 | %12 主張 | 一致 |
|---|---|---|---|
| overall / oga / ogb | STOP / GO / STOP | 同 | ✅ |
| go_conditions | movable_all_GO=**False** / cable_pair_PASS=**False** / null_beat_ge_margin=**True** | 同 | ✅ |
| movable γ⊥ | {0}1.744 / {1}1.056 / {2}1.055 / {3}1.034 全 STOP | 同 | ✅ |
| C2_REGRASP pair | seg 0.249 / ee_only 0.973 STOP (n=2482) | 同 | ✅ |
| null_beat | 0.492 = dr_worst 1.744 − null_worst 2.236(margin 0.15) | 同 | ✅ |
| og_bprime C2 | contracted=**False** [5.0→3.118→2.979→3.366→3.675→3.905 発散] | 5.0→2.979→3.905 | ✅ |

---

## 1. 判定 (1)-(4)

### (1) 6-metric 独立一致 — **CONCUR(exact)**
全 6 metric、独立再抽出が %12 と完全一致(上表)。carried_stops=['GUIDE_C2'] も一致。

### (2) plateau 判定 — **CONCUR(+ composition-confound-robust な marginal-collapse 定量)**
{1} γ⊥ 軌跡: baseline **1.257** → wave-1 **1.098**(Δ−0.159、2 {1}-rec) → batch **1.056**(Δ−0.042、~10 追加 {1}-rec)。
- **%9 追加(per-rec marginal collapse)**: wave-1 −0.0795/rec → batch increment −0.0042/rec = **~19× 崩壊**。現 rate で GO≤0.5 到達に **~132 追加 rec**(非現実)。→ auto-add は ~1.05 plateau を越えぬ = **robust**。
- **composition-confound(%12 flag)への評価**: wave-1(m2=clean+4p2r)vs batch(11 survivor+12 {1})は別 model composition → Δ は純 marginal でない。**だが結論は confound-robust**: batch は 6× の {1}-teacher を持ちながら γ⊥ は −0.042 のみ。confound が plateau を「偽装」するには、大きな teaching 効果を base-shift が丁度打ち消す adversarial 一致が必要。base は両者とも clean/survivor demo(count 9 vs 11 のみ差)ゆえ base-γ⊥ shift は小 → 19× marginal 崩壊を説明不能。honest caveat: 純 marginal は controlled increment(base 固定 + {1}-teacher のみ追加)で確定すべきだが、**寛大に 2-3× 過小評価を許しても GO≤0.5 は経済的に到達不能(~44-66 rec)→ 戦略結論(BC-only p2r 不十分)は robust**。

### (3) 戦略 framing(3 BC approach 全 fail = convergent)— **CONCUR + IL-principle 接地 + ⚠ {11} 分離を強調**
- **convergent 妥当**: B2(DR diversity: on-path val 18× 動くが γ⊥ restoring 不動)/ (iv)(synthetic p2r: Outcome-B)/ (ii)(physical p2r: mechanism-validated だが plateau ~1.05)= **3 つとも pure BC(obs→action mimic、policy-in-loop 無・reward 無)**。共通限界 = **BC は demonstrated distribution 外の restoring を産めない**(= IL の教科書的結果: BC の compounding error off-distribution → DAgger/RL が既知 remedy)。∴ framing は IL 原理に接地して robust。
- **別解釈の棄却**: ①「bar が厳しすぎ」= 否 — γ⊥≈1.0 = 摂動を 1:1 追従(integrator)= 95mm-wall drift の原因機構、og_bprime C2 発散が closed-loop 失敗を直接裏付け、fork-(iv) OG-predicts-closed-loop calibration ゆえ bar は現実要件を反映(arbitrary でない)。②「batch 固有 flaw」= 否 — wave-1 で validated な機構を scale up、機構は動いた(−0.159→plateau)= 根本的 diminishing return であって batch bug でない。
- **⚠ %9 重要 refinement(escalation で混同禁止)**: 「pure BC 不十分」は **movable {0-3} restoring 軸**に適用される。**{11} seg-follow は別問題(obs-target mismatch root-cause = obs-fix、BC 限界でない)**。∴ **D-1 next-stage(DAgger/RL)は movable-restoring plateau を target、{11} を DAgger/RL に lump しない**({11} は obs-fix が先、RL を obs-bug に投げない)。%12 の「{11} 別 thread」を強調 — remedy が異なる(movable→distribution-matching/reward、{11}→obs 整合)。

### (4) conservatism(OG offline STOP = conservative-definite FAIL)— **CONCUR**
- calibration: fork-(iv) で OG offline が in-sim closed-loop を予測(B1′/B2 で 0 GPU surprise)→ offline STOP は closed-loop 失敗を予測。
- **方向**: OG は小摂動(2-10mm)局所測定 = closed-loop(compounding drift)より **easy**。easy test の fail(γ⊥≈1.0 = 局所 restoring 無)→ hard reality(compounding)も definite fail = **conservative-definite**。
- **二重裏付け**: 局所 γ⊥(movable≈1.0)+ og_bprime C2 収縮 probe **発散**(contracted=False)= closed-loop-ish 直接証拠。→ bankable STOP。

## 2. null_beat=True の semantics 明確化(%9 追加、STOP との非矛盾)
null_beat 0.492=True は **矛盾でなく "mechanism validated" を corroborate**: dr_worst 1.744(HOVER {0})が null_worst 2.236 を beat = p2r policy が replicate-null を genuine に上回る(**{1}-teaching が {0} へ generalize、2.497→1.744 で null を beat**)= real teaching。**STOP は null_beat でなく absolute bar(movable_all_GO=False plateau + cable_pair_PASS=False {11})から来る**。∴ verdict = **「機構は real restoring を教える(null_beat + {1} −0.159)が absolute GO bar 下で plateau」= mechanism-validated-but-bar-unmet を正確に裏付け**(null_beat=validated 証拠、movable/pair STOP=bar-unmet 証拠)。

## 3. %12 の ASSESS / rec への評価 — **CONCUR + 2 sequencing note**
- **NOT (c) auto-add** = CONCUR(plateau、marginal 19× 崩壊)。
- **accept mechanism-validated-but-bar-unmet** = CONCUR(null_beat + {1} 移動 = validated、絶対 bar = unmet、honest)。
- **D-1 staged next-stage(iii DAgger / i DAPG-RL)escalate** = CONCUR(pre-registered D-1 escalation path、IL remedy に合致)。**note-1(sequencing)**: iii は i より conservative(ii machinery + expert 再利用 + policy-in-loop 追加、新 reward 設計不要)vs i は whole-route MDP env = P2 の standing CRITICAL cost。→ **iii 先行が正**(D-1 順序)。**note-2(expert-dependency caveat)**: 3 BC の共通根は「scripted expert が off-path で state-blind(waypoint のみ)」。iii DAgger も同 expert 依存 → movable {0-3}(pre-contact grasp approach、target=固定 waypoint ゆえ waypoint-restoring で**十分**)には iii 有効だが、iii も plateau すれば expert 非依存の i(RL、reward 駆動)へ = より強い証拠。escalation に「iii の value は expert が visited off-path state で有用 label を出せるかに依存(pre-contact では waypoint で十分、{11} 型 cable-aware では不足=別 obs thread)」を carry。
- **{11} obs-mismatch = 別 thread(cheap obs-fix)** = CONCUR(§1-(3) refinement 通り)。

## 4. Conservatism 総括(§運用15)
- CP-(ii)-5 STOP = **conservative-definite**(offline easy-test fail + calibration + og_bprime 発散の二重裏付け → closed-loop definite fail)= bank 妥当。
- mechanism-validated(null_beat + {1} 移動)= real but insufficient(non-conservative to claim GO — 絶対 bar unmet)。
- plateau ~1.05 = composition-confound を寛大補正しても GO≤0.5 経済的到達不能(robust)。

## 5. INVARIANTS
batch は {1}×12(adjA drop reconciled)= 既 verified な kick-and-recover 機構の scale、INV#1-5 untouched(EE-detour=DiffIK / span-watch / コ / no-kinematic-trick / LOCKED regrasp_ok guard は batch でも保持)。band=γ instrument は CP-(ii)-5 に適用済(design 承認済)。

## 6. OVERALL — **CONCUR: CP-(ii)-5 STOP + 戦略転換 (D-1 next-stage escalate)**

(1) 6-metric exact (2) plateau robust(19× marginal 崩壊、confound 補正でも到達不能)(3) convergent framing IL-接地 robust + **{11} 分離必須** (4) conservative-definite bankable。rec(NOT auto-add / mechanism-validated-but-unmet accept / iii→i escalate / {11} 別 obs-thread)= CONCUR。

**Rs escalation packet 推奨**: (a) plateau = per-rec marginal 19× 崩壊(confound-robust)/ (b) 3 BC convergent = pure-BC が off-distribution restoring を GO bar まで教えられぬ(IL 原理)/ (c) null_beat=True は validated を corroborate、STOP は絶対 bar 由来 / (d) **movable-restoring(→iii DAgger 先行、expert-dependency caveat、→i RL)と {11}(→obs-fix)を分離** / (e) conservative-definite STOP。rollout 禁止・0-commit・band=γ=CP-(ii)-5。

*%9 OPS-SUPERVISOR — 2026-07-03 17:28 JST(書込前 `date`)。INVARIANTS untouched / 0-commit / 編集 = 本 file + log.md。*
