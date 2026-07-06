# W0-a′ packet v1.1 — %9 OPS-SUP cross-PV 台帳 (2026-07-06 10:2x)

**対象:** `RS_W0APRIME_PACKET_20260705.md` v1.1 (10:2x %12 起草、uncommitted working-tree)。
**verdict: CONCUR-WITH-CORRECTIONS (blocker なし)。** ③④⑥ + evidence cite EXACT 性を独立検証。数値は banked H-drape 私鍵 (`w0e_phi10_arc_probe/0948_hdrape/hdrape_leg1_out.txt` sha f4640d27) + round-2 npz 独立再計算。

## VERIFIED EXACT / CORRECT

- **§2 SR 系譜** 0.716 = 58/81 / [0.610,0.803] / any-seat 77/81 / floor-rest 829.0 EXACT / crossing 848 / clip-top node 61/62 / O-D 58/23 / three-peaks {0.32/0.368/0.380} — 全て私鍵と EXACT。
- **③ horizon**: round-2 81 cell 独立再計算 max = **7710 frames = 771.0 RL-step < 810 (bump 非発動)** = %12 主張 EXACT。
- **③ span phase-13**: 全 81 cell [92.417, 92.421] (per-cell intra-range ≤0.003) → round 92.42 定数 = EXACT。INV#2 運用 pin 健在。
- **④ DC-1s3 分離判定**: LEDGER L47 末尾 + state.md `eba71929b3` の 08:3x 記録 = **DC-1=α 本体のみ、6D/12D sub 言及なし** → 「sub 未提示・Rs-PENDING 分離」CORRECT。α-6D は DQ2 BC fork-(i) の position-only 6D (state.md:40) と一貫 = 6D/12D discrepancy なし。
- **⑥ supersession 行**: LEDGER grep (DQ1/B→A′/supersession) = 独立 supersession 行**不在**、L47 inline 記述のみ → 「未発行」判定 CORRECT。
- **cite 実在**: devplan:236 (「D-C 採択時は DQ1=B→A′ supersession を LEDGER/state に明記」) EXACT / spec:115 (§9-3 packet 定義 + 「同 turn banking 義務」) EXACT。

## CORRECTIONS (verdict-neutral、Rs 提示前に反映推奨)

1. **③ span window (要 fix)**: §2/§4-Q10 の「dual-grip phase **(1-7/12-14)** で [92.38, 92.42]」は **phase 12 で矛盾** — per-phase 独立再計算で phase 12 = [92.38, **127.10**] (再把持後 dual-grip 復帰 transition)。[92.38,92.42] が成立するのは **phases {1-7, 13, 14} のみ**。phase 12 は phase 10-11 (私計測 [95.5, 246.2]、%12「~160mm」も過小) と同様 transition ゆえ span-constant window から除外すべき。**fix: 「(1-7/12-14)」→「(1-7/13-14)」** (INV#2 pin は phase-13 で健在、verdict 不変)。
2. **⑥ supersession の timing (要 governance 判断)**: 判定 (未発行) は CORRECT だが **§8-1「承認時執行」への defer が devplan:236「D-C 採択時」+ spec:115「同 turn banking 義務」+ §運用4 即反映 gate と tension**。§0 で **DC-1=α は既 DECIDED (08:3x)** ゆえ supersession banking は**今 due (採択時)**、承認時でない。内部不整合 = DC-1 DECIDED なのに coupled supersession を承認まで defer。**推奨: %12 が supersession 行を今発行** (DC-1=DECIDED + devplan:236 と一貫、packet 承認と decouple)。low-risk (α 採択は L47 inline に既反映で silent-stale でない) だが rule-consistency は now-issue を支持。
3. **④ rot-delta 精度 (minor)**: 「demo rot-delta ≡0」は実測で per-step max ≈0.13-0.16° / whole-episode ≤0.41° (negligible だが厳密 0 でない)。**fix: 「≡0」→「≈0 (≤0.4°)」**。α-6D 推奨 (rot near-inert) の根拠は成立。
4. **③ horizon tie (minor)**: max 771 step は **≥5 corner cell の tie** (x15_y-20 / x15_y-5 / x15_y10 / x20_y-20 / x20_y-5…)、x15_y-20 は unique でない。**fix: 「cell x15_y-20」→「tied across ≥5 corner cells (e.g. x15_y-20)」**。
5. **§2(i) honest-F basin-gap 「~5-9mm」(要 reconcile)**: 私鍵で honest-F crossX 0.367-0.370 / clip-basin 0.379-0.381 → **gap-to-clip-basin ~9-14mm** (threshold x*=0.3676 まで ~0-3mm)。「~5-9mm」は clip-basin までの gap を過小、閾値までなら過大。**どの基準か明記推奨** (authority ±22mm 内は不変、verdict-neutral)。

## 判定
CONCUR-WITH-CORRECTIONS: ③④⑥ の核心判定は全て健全 (horizon/span-13/DC-1s3 分離/supersession 未発行 = 正)。corrections 1 (span window phase-12) + 2 (supersession timing) は Rs 提示前に反映推奨 (1 = cite 事実誤り、2 = 規則整合)。3-5 は minor 精度。blocker なし → 修正反映後 Rs 提示可。
