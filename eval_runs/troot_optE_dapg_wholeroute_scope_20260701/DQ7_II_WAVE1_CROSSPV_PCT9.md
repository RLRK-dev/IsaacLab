# DQ7 stage-(ii) wave-1 loud gate — OPS-SUPERVISOR (%9) independent cross-PV

**Written: 2026-07-03 14:30 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `dq7_ii_cp2_wave1_report.md` (%11) + %12 独立検証。**Gate:** full batch (GPU spend) は本 cross-PV の CONCUR まで launch 不可。
**Constraints:** 0-commit / rollout 禁止 / read-only + this file + log.md。

## 0. Grounding — γ⊥ を自ら再抽出(§運用28、%11/%12 数値を再利用しない)

`og_m1/og_gate.json` (clean) vs `og_m2/og_gate.json` (clean+4p2r)、`ogb_anchor_gate` から直接:

| cell | M1 | M2 | Δ(%9 再計算) | %12 主張 | 一致 |
|---|---|---|---|---|---|
| {0} GRASP_HOVER | 2.497 | 2.175 | **−0.322** | −0.322 | ✅ |
| {1} GRASP_DESCEND | 1.257 | 1.098 | **−0.159** | −0.159 | ✅ |
| {2} GRASP_CLOSE | 1.041 | 1.031 | −0.010 | down | ✅ |
| {3} LIFT | 1.055 | 1.049 | −0.006 | down | ✅ |
| {11} seg_follow | 0.282 | 0.249 | −0.033 | −0.033 | ✅ |
| {11} ee_only | 0.973 | 0.974 | **+0.001** | STATIC | ✅ |

M1 == CP-E baseline (1.257/0.282/0.973) 完全一致 ✅(測定 faithful、drift 無 → M1→M2 Δ は apples-to-apples)。両 model overall STOP ✅(絶対 verdict = CP-(ii)-5、wave-1 では expected)。

---

## 1. 判定 (1)-(5)

### (1) γ⊥ 数値 + delta の一致 — **CONCUR(exact)**
全 6 metric、%12 の delta と私の独立再抽出が完全一致(上表)。measurement-faithful(M1=baseline)確認。

### (2) 「{1} down = 機構 validated」/「{11} static = weak-signal INCONCLUSIVE」の読み — **CONCUR(+ {11} 構造的 caveat)**
- **{1} = 機構が restoring を教えている(directional)= 妥当**。強化根拠(%9 追加): **相対** drop = {0}−12.9% / {1}−12.6%(≈同率)vs {2}−1.0% / {3}−0.6%。**pre-grasp cluster {0,1} に局在した ~13% 縮小、grip/lift cluster {2,3} は <1%** = 局所的 restoring 教示のパターンであり、dataset-size artifact(全 cell 一様に動く)ではない。∴ (iv)-Outcome-B の懸念(imitation は restoring を教えられない)を**直接反証** = 正しい読み。ただし "validated" は **directional のみ**(絶対 bar 未達、STOP 継続)— %11/%12 の「NOT absolute-bar」hedge に同意。{0} 非注入 −0.322 = {1} teacher の generalization も妥当(相対率一致が裏付け)。
- **{11} ee_only STATIC = INCONCLUSIVE = 妥当だが「weak-signal(1 rec)」だけでは不十分。⚠ 構造的 dilution を追加 flag:** ee_only probe は **C2_REGRASP 全 1530 行の regression**(私が og_m2 で確認)。c11 の kick-and-recover teacher は **RHOVER sub-loop のみ**(release-margin で kk9-10 clean)= 全 phase の ~1% 行。probe は RHOVER + **RDESCEND + cage** を平均するため、RHOVER-restoring 信号が希釈される。**帰結: {11} が動かないのは (a) noise(1 rec)か (b) dilution/generalization-limited(RHOVER teacher が RDESCEND+cage に般化しない)かを weak-signal 論だけでは分離できない。** (a) なら batch の追加 {11} 収録で解消、(b) なら**追加収録でも解消しない**(各収録が希釈された RHOVER 信号のみ足す)。→ Q4 の condition W1 へ。

### (3) val confound の扱い(γ⊥ anchor 化)— **CONCUR**
- val leak は実在: **adjA ≡ clean rec_p10_0 の byte-identical dup**(%11 finding #2)→ seed-0 split が (0,0)+(10,0) を M2 val に、その twin を train に配置 → M2 val 0.001179 は optimistic-leaked、M1 val-set≠M2 val-set。%11 が discard は正。
- **γ⊥ は OG probe(固定摂動)で測定 = val split 非依存 → clean anchor** = 正しい選択。
- **dup が γ⊥ を bias しないことを確認**: adjA=p10_0 は **clean demo(注入なし)**→ 複製しても restoring を教えない(on-path)→ {1} γ⊥ 縮小は d1a/d1b(実 {1} p2r 2 本)に帰属、adjA は inert。∴ 「{1} down from 2 recs」正確、γ⊥ anchor 健全。
- **batch 要件(W3)**: adjA dup を distinct 5mm-grid offset に是正(%11 #2)+ val split を twin-leak 回避(train demo が val demo の byte-twin にならない)→ batch の val を**二次** check として再利用可(γ⊥ は一次のまま)。

### (4) proceed-to-full-batch の落とし穴 / escalate 論拠 — **CONCUR-proceed(条件 W1 付き)**
- **proceed は妥当**: abort trigger(anti-restoring ↑)は**ゼロ発火**(私の再抽出で全 movable down-or-static、{11}ee +0.001 は noise 内 static)。{1} directional 検証は (iv) 懸念を反証する major positive。cost 有界(~2h、HIGH-COST-GATE 非該当)。batch は {1} を firm 化 + CP-(ii)-5 gate(injectable-only {1}+{11})を setup。
- **⚠ 落とし穴 W1 = {11} 固定 allocation の空費 risk:** (2) の dilution ゆえ、{11} を「もっと収録すれば解消」と固定 allocation で batch に賭けると、dilution-limited だった場合に GPU を空費。**mitigation(hold でなく structure):**
  - (a) **{11} を batch 内で wave-granular に**: 全 {11} allocation を一度に spend せず、最初の {11} sub-wave 後に ee_only 移動を interim check(wave-1 の gate 原則を batch 内 {11} に適用)。
  - (b) **cheap dilution-vs-noise discriminator(batch {11} 前、~0 GPU)**: c11 の既存 recovery 行だけで、または og probe を **RHOVER-rows vs RDESCEND-rows に sub-segment** して ee_only を別々に測る。RHOVER-only ee_only が下がっていれば noise-limited(batch で解消見込み)、RHOVER でも下がっていなければ RHOVER teacher が効いていない({11} 機構再設計が必要 = escalate)。
  - **{1} portion + adjA-fix は full で進めてよい**(validated、dilution 無関係)。escalate すべきは全 batch でなく **{11} allocation の commit 前**のみ。
- **note**: {11} ee_only の phase-averaged 到達性は、私の先の gate-reachability carry({2,3} un-injectable)の弱い同族 — RDESCEND+cage の following が phase 平均を支配し得る(ただし RDESCEND target は固定軌道ゆえ restoring が correct = bar 自体は妥当、般化が open question)。W1(b) がこの open question を安価に閉じる。

### (5) converter naming blocker fix — **Option B(meta-read)を推奨、Option A は棄却**
- **`_offset_from_npz_path:520-529` を on-disk 確認**: `rec_<x>_<y>` を dir basename から parse、失敗で `SystemExit`(fail-loud)。:573-574 で train_off/held_off(demo の IC-offset 分類、hull-vertex 判定に使用)。
- **Option A(IC-offset naming `rec_<x>_<y>`)= 棄却**: **collision 実在** — d1a と c11 は**両方 IC(0,0)**(injection phase が {1} vs {11} で異なるだけ)→ 同名 `rec_0_0` で衝突。offset を fake して unique 化すると **affine/dataset の offset semantics を汚染**(offset は真に (0,0))。wave-1 が symlink 回避したのはこの理由。
- **Option B(meta-read に拡張、NON-locked、%12 review)= 推奨**: recorder meta は IC-offset を authoritative に記録済 → path-parse より robust(records-vs-fact: meta が真値)。**加えて demo identity は unique recording-ID(dir 名 or meta uuid)で key し、offset(injection 変種間で非 unique)で key しない**。regression: clean demo で meta-offset 読みが従来 path-parse と一致 + convert byte-identical を assert。

## 2. §運用14 video leg(proceed 判断での扱い — loud omission-justification)
- %11 の skill-path video-analyst(advisory、3 VALID: injection→release→recovery clean / grasp on real cable / drop・貫通・NaN ゼロ / cable held jump≤1.9mm)に**依拠して proceed 判断**し、**私は video を再走しない**。理由(loud): proceed gate は独立再抽出した γ⊥ directional に立脚し、bankable な physical verdict ではない。**bankable な物理妥当性(mj_geomDistance 貫通 cross-PV + intra-finger slip、特に {11} の real-cable grasp、human-GT)は CP-(ii)-5 の要件として繰延**(memory feedback-video-detect-intra-finger-cable-slip / grasp-verdict-human-GT)。この繰延は silent 不可・本記録で loud 化。
- **INVARIANT 実データ検証(強い)**: rec_c11 が {11} kick の**下で** release-margin guard が LOCKED regrasp_ok=True を real data で保持(reach 22mm→0.8mm 復元、%11 (i)/(iv))= 私の v2 §D 検証が real recording で確証。span-watch dev≤4.4mm<5mm(pre-contact ゆえ N1 exempt、informative)✅。

## 3. Conservatism(§運用15)
- γ⊥ directional 移動 = **non-conservative**(SHOWN, not GO — 絶対 bar 未達 STOP 継続)。wave-1 の正しい frame。
- overall STOP(絶対)= expected-at-wave-1(CP-(ii)-5 が絶対 verdict)。
- **{11} dilution = 本 leg の key non-conservative uncertainty**: 「batch で解消する」は仮定であり W1(b) で SHOWN にすべき。
- {1} = conservative 方向に良好(model-consistent、2 rec、相対率一致)。

## 4. OVERALL — **CONCUR (proceed to full batch)**、条件 W1-W3 + Q5=Option B

(1) 数値 exact 一致 (2) {1} validated(+相対率で強化)/ {11} static は weak-signal かつ**構造的 dilution**(私の追加)(3) val-confound の γ⊥ anchor 化 妥当 (4) proceed 妥当・abort ゼロ (5) Option B。

**発効条件(batch launch 前 / batch 内):**
- **W0(hard、batch convert 前)= Q5 Option B**: `_offset_from_npz_path` を meta-read に拡張(NON-locked、%12 review)+ demo key=unique rec-ID + clean regression byte-identity。convert が crash するため batch convert の hard pre-req。
- **W1({11} allocation の structure)**: {11} を batch 内 wave-granular に(interim ee_only check)+ **cheap RHOVER-vs-RDESCEND sub-segment discriminator(~0 GPU、{11} spend commit 前)** で dilution-vs-noise を分離。{1}+adjA-fix portion は full 可。
- **W2(bankable physical → CP-(ii)-5)**: mj_geomDistance 貫通 + intra-finger slip(human-GT)を CP-(ii)-5 要件として繰延(wave-1 advisory では bank 不可)。
- **W3(val/dup fix)**: adjA を distinct 5mm-grid に + val split の twin-leak 回避 → batch val を二次 check 化(γ⊥ 一次不変)。

proceed を block するのは W0(convert crash)のみ。W1 は {11} portion の structure(全 batch は block しない)、W2 は CP-(ii)-5、W3 は batch 設計。rollout 禁止不変・0-commit・band=γ は CP-(ii)-5 のみ。

*%9 OPS-SUPERVISOR — 2026-07-03 14:30 JST(書込前 `date`)。INVARIANTS untouched / 0-commit / 編集 = 本 file + log.md。*
