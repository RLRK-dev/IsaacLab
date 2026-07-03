# DQ7 stage-(ii) {11}(a) MECHANISM verdict — OPS-SUPERVISOR (%9) independent cross-PV (Rs-escalation load-bearing)

**Written: 2026-07-03 16:15 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `DQ7_II_BATCH_REVIEW_PCT12.md` + evidence `dq7_ii_cp2_wave1/w1a_n2/w1_discriminator_n2_results.json`。
**Trigger:** 私が W1 cross-check で「sign が Rs-load-bearing 化した時点で {11}@2 og を独立再抽出する」と約した点の履行。**非 block**({1}+adjA batch は %11 並行進行中)。0-commit / rollout 禁止。

## 0. §運用28 独立再抽出(json 直読、%11/%12 数値を再利用せず)

`w1_discriminator_n2_results.json` を自ら read:

| probe | region | n | d_ee (M2p−M1) | sign | 私の確認 |
|---|---|---|---|---|---|
| probeA (2mm) | **RHOVER (kick region)** | 56 | **+0.003387** | **wrong (+)** | ✅ = %12 主張 |
| probeA (2mm) | recovery-band | 36 | +0.001797 | wrong (+) | ✅ |
| probeA (2mm) | RDESCEND+cage (非注入) | 63 | −0.003133 | 微 right | — |
| probeA (10mm) | RHOVER | 56 | +0.004484 | wrong (+)・より大 | ✅ |
| **probeB (all-demo)** | **RHOVER** | **1053** | **+0.003313** | **wrong (+)** | ✅ 高 power 確証 |

- **seg_follow**: RHOVER 0.28107→0.23229 / whole-C2 (probe0) 0.28236→0.22771 = **down**(帯 [0.8,1.2] から更に遠) ✅。
- **sign 推移**: n=1 +0.00255 → n=2 +0.003387 = **restoring から更に遠ざかる、NEGATIVE flip なし** ✅。
- **正 control**: %12 報告 {1} γ⊥ −0.20/−0.40(私が wave-1 で独立に −0.159 を確認済 = probe 健全は既に自ら裏取り)。

---

## 1. 判定 (1)-(3)

### (1) {11}@2 own-region sign = no-flip (wrong-positive) — **CONCUR(独立確認)**
RHOVER kick-region が n=56 / **n=1053(all-demo、高 power)** / 2mm+10mm の全てで wrong-positive、n=1→n=2 で更に positive。**sign no-flip = MECHANISM(P2 通り)を独立確認**。

### (2) recovery-row 比較が volume-vs-mechanism を clean separation するか — **CONCUR(+ より強い論拠を追加)**
- P1(私の refinement)は充足: {11}@2 recovery-row ≈60-72 ≥ {1}@2 45 = teacher-row 数は {1} success 以上 → 「教師行不足」棄却。
- **さらに強い論拠(%9 追加)**: probeB は **all-demo RHOVER n=1053** で同 wrong-sign(+0.003313)= 統計 power は volume 閾値を遥かに超える。**quantity(row 数 + n=1053 power)は充分、quality(sign が wrong-direction、magnitude が小でなく)が誤り** → volume で直らない qualitative failure。P1/P3/P4 の全代替(dilution/volume/direction)が data で棄却:
  - P4 dilution: own-region(局所)で wrong = train-dilution では説明不能 ✓
  - P3 direction: c11[12,9,−5] + c11b[−10,−8,6] **両方 fail** = direction-independent(私の P3 confound 懸念は「両 fail」の outcome で moot-favorable に解消 — 逆に direction 非依存を強化)✓
  - volume: n=1053 で wrong ✓

### (3) escalation framing(following-vs-restoring MISMATCH)の妥当性 + 別解釈 — **CONCUR(leading-hypothesis として)+ 追加解釈 1 件**
- **mismatch framing は sound**。code 確認: `test:4557 _fr = 補間(_prr→_hovR)` = **{11} RHOVER target は cable-anchored MOVING**(argmin 由来 hover)。memory `reference-og-gate-moving-target`: cable-anchored 相では正解 = **following**(γ⊥≈1)、restoring(γ⊥≤0.5)でない。
  - **data が mismatch を裏付け**: ①ee_only が RHOVER で **UP**(+0.0033)= restoring 教示が counterproductive ②seg-follow が **DOWN**(0.282→0.228)= 純 restoring teacher は seg を触らぬはずが更に悪化 → restoring lesson が「全 position delta への stiffening / moving-target への chasing」に bleed。moving target への kick-recover は「移動 target を追え(following/chasing)」を教え、「摂動に抗して hold(restoring)」を教えない = **paradigm mismatch**。
  - **提示形の refinement**: これは **data-confirmed FACT(mechanism が {11} で ee-restoring を教えない)+ leading HYPOTHESIS(理由 = moving-target で following≠restoring)**。hypothesis は code+memory 接地だが直接測定でない → **OPTION B が test すべき仮説**として提示(証明済でなく)。
- **別解釈の棄却(%12 が問うた点)**:
  - probe-blindness: 正 control {1} 健全 + ee_only=0.973 は policy が実際に ee 追従(memorize でない、gain~1)→ probe は実挙動を測定。棄却 ✓
  - metric-unreachability(§7 band / {2,3} と同族か?): **否 — 区別せよ**。{11} pair(seg-follow∈帯 AND ee-only≤0.3)は良い following policy(cable 追従 + spurious-ee 無視)で**到達可能**。現 policy は both 失敗(under-follow seg + over-follow ee)= 悪い following policy。∴ **metric は健全、MECHANISM(restoring teacher)が following-deficiency に不適合**。gate-reachability 問題でない。
  - hook-bug: c11 regrasp_ok=True + window 一致 + video injection→recover clean → hook は機構的に動作。学習信号が wrong-paradigm(bug でない)✓
- **⚠ %9 追加解釈(OPTION B が rule in/out すべき、%12 未列挙)= obs-sufficiency(§運用21)**: seg-follow 0.282 の under-following は **obs 問題の可能性**。もし {11} obs の `seg_pos`(`_seg_rule` 由来)が R-arm が regrasp すべき **C2 セグメントを表現していない**(例: C1-pinned セグメントを指す)なら、policy は追うべき cable を**見えない** → seg-follow は**どの teacher(restoring も following も)でも直らない構造欠陥**。→ **OPTION B は「following vs restoring」の前に「{11} obs は追従対象 cable segment を含むか」の obs-sufficiency check を含めよ**(§運用21: obs に無い情報依存の metric は勾配ゼロ)。B2 の diversity も seg-follow を動かせなかった事実(on-path diversity 失敗)は obs-blindness 仮説と整合。

## 2. %12 の決定(exclude {11} / batch {1}×12+adjA×8 / escalate)への評価 — **CONCUR + 3 note**
- **exclude {11} = 妥当**(壊れた機構に GPU を注がない)。**batch {1}×12 = 妥当**(validated)。12:11 GPU GO 内(~20 rec ~2h/4-way)✓。
- **note-1(batch real-yield の honest framing)**: {11} 除外ゆえ batch は **injectable-only {1}+{11} の full GO に到達しない**。bankable = **「{1} restoring を scale で実証」**、{11} = 別 redesign track。CP-(ii)-5 framing は「{1} 達成 + {11} pending-redesign」で、full injectable-only GO の試行と誤読させないこと。
- **note-2(adjA の reframe)**: adjA = on-path dense diversity = **following-type teacher**。B2 で疎 diversity は seg-follow を動かさなかったが、adjA×8(密)が seg-follow を動かすなら「密 following-diversity が {11} を助ける」証拠 → **OPTION B の入力**。adjA を「leg-2 adjunct」でなく **{11} following 質問への安価な probe** と位置付ければ {11}-除外 batch でも目的が明確(seg-follow が動かなければ obs-blindness 仮説を補強)。
- **note-3(OPTION 順序)**: **B(following-vs-restoring + %9 の obs-sufficiency check)は A/C/D に先行必須** — A/C/D は「restoring が正解」を仮定した機構変種ゆえ、B が paradigm を確定するまで GPU を注げば mismatch なら空費。**C(release-margin 緩和)は Rs-only 最終手段**(LOCKED regrasp_ok 抵触、v2 §D 保護を崩す)。

## 3. Conservatism(§運用15)
- {11} MECHANISM verdict = **conservative-definite**(teach-to-the-test 最有利 [同 co-move probe] + volume 充分 + 両方向 + 高 power n=1053 で wrong-sign → より難しい条件でも改善せぬ)= bank/escalate 妥当。
- {1} = validated(directional、non-conservative for GO — 絶対 bar は CP-(ii)-5)。
- obs-sufficiency 仮説 = unknown、OPTION B で SHOWN すべき(推測で埋めない)。

## 4. OVERALL — **CONCUR: {11} MECHANISM 確定、Rs escalation 妥当**

(1) sign no-flip 独立確認 (2) volume 棄却(row 数 + n=1053 高 power + 両方向)(3) mismatch framing sound(leading-hypothesis 形)+ 別解釈(probe-blind/metric-unreach/hook-bug)棄却 + **追加: obs-sufficiency(§運用21)を OPTION B に**。

**Rs escalation packet 推奨内容**: (a) own-region wrong-sign(n=1053 高 power)+ recovery-row≥{1} = mechanism-not-volume の証拠、(b) mismatch は data-confirmed-fact(機構失敗)+ hypothesis(moving-target following≠restoring)の区別、(c) **OPTION B を first-gate 化**(following-vs-restoring **かつ** obs-sufficiency)、A/D は B 後、C は Rs-only、(d) {11}≠gate-reachability(metric 健全・機構不適合)。batch = {1}×12+adjA×8 PROCEED、{11} 除外。rollout 禁止・0-commit・band=γ は CP-(ii)-5 のみ。

*%9 OPS-SUPERVISOR — 2026-07-03 16:15 JST(書込前 `date`)。INVARIANTS untouched / 0-commit / 編集 = 本 file + log.md。*
