# DQ7 stage-(ii) charter — OPS-SUPERVISOR (%9) concur verdict (残 two-key)

**Written: 2026-07-03 08:48 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `charter_dq7_stage_ii_coord.txt` (%12, 8 節)。**Role:** decider≠verifier — 条件2/3 準拠 + ops + two-key 裁定 + band §7 扱いを独立検証。
**Constraints honored:** 0-commit / no code / no spec / no planning-surface。Writes = this file + log.md append。HEAD = `6365884e4f`。

## 0. Grounding — 一次 instrument を自ら read + 裏取り

| Claim (charter) | 一次 source 検証 | 結果 |
|---|---|---|
| (iv) = Outcome B banked de61f74c7c | `git show de61f74c7c` = "Bank DQ7 stage-iv Outcome B: synthetic supervision insufficient"; msg = ladder 3/3 fail・dial-back 非感応・cells moved-not-to-bar・null-beat own/off-slice で inconclusive・physics undoomed・budget+band pre-flag → `dq7_iv_pathfinder_report.md` §1-§5 と全一致 | ✅ |
| Rs「推奨で良い」= Option A | `log.md:7282-7284` (08:4x): (iv) Outcome B escalation への応答 = (ii) 前進承認、%11 relay 同解釈・%12 一次 capture、**解釈は Rs 訂正可能と明示** | ✅ (interpreted — §2-(4) 参照) |
| band faithful pair ≈0.667 < 0.8 | `DQ7_IV_MINISPEC_DEBATE_DECIDE.md:20-21` U4 = **CC1 code-verified**: test:4377 `_La` frozen / test:4405 `_R_ty` HOLD Y=88mm (INV#2) / og:252-265 per-axis R-response → mean(X:1,Y:0,Z:1)≈0.667 | ✅ code-grounded |
| baseline γ⊥/pair/null_beat | `b2_cpE_og/bc/og_gate.json` = 2.497/1.257/1.041/1.055 / pair 0.282,0.973 / null_beat −0.261 (私が §運用28 再確認済 05:44 verdict) | ✅ |
| 条件2/3 = 私の verdict | `DQ7_CONSULT_PCT9_VERDICT.md:87`(条件2)/`:61`(条件3) = charter §3/§8 が正確に参照 | ✅ |
| meta 契約 (U7) | `DEBATE_DECIDE:29` U7 = truthful override + per-phase n basis check + per-leg×bin accept/reject → charter §2/§5 が _p2r schema へ継承 (%9 P3 追加1 の記録-vs-事実審査) | ✅ |
| live ops | GPU 両基 ~0% util (compute 2330/420MiB = 残 context)、%11・%10 IDLE、%12 稼働。未 push = 3 commits 継続 | ✅ 08:48 時点 |

Prior-art (V10): charter §8 が DQ7 系 2 走破 + delta 記録を cite、新 keyword (injection/detour/dwell) は CP-(ii)-0 で自走宣言 — 継続正当 (%9 は 05:44 で同 keyword 走破済、hit 全て self-reference)。

---

## 1. 判定対象 (1)-(5)

### (1) 条件2 充足(§3 phase 別振幅表)— **CONCUR**(+ N1 refinement)
私の条件2 (`:87`): 「20mm tail = pre-contact {0,1}+{11} 限定 / held ≤10mm + phase 別数値」。charter §3 照合:
- {0,1} = [2,20] pre-contact ✅ / {11} = [2,20] **R-arm** pre-contact ✅ (L は holding — INV#1 保全、R のみ detour = 正しい)
- held {4,9,10,12} = [2,8] (≤10 ✅、私の閾値より strict) / pre-seat {5,13} = [2,5] / {14} C2_SETTLE = **skip** (私は ≤5 と言ったが charter は verdict-window 汚染回避で全 skip = **より保守的**) / {3} LIFT = **skip** (WR retention drop risk、私の「LIFT 回避」と一致)
- {1} は Z≤0 成分禁止 (table 衝突) = 物理的に妥当な追加制約
→ **charter §3 は条件2 を満たし、複数 phase で私の閾値より厳格**。数値変更時 %9 再 concur 要 = 明記あり ✅

### (2) 条件3 充足(§8 notify 要件)— **CONCUR**
私の条件3 (`:61`) 4 項 vs charter §8 CP-(ii)-0 notify:
(a) GPU-h + device pins → 「~3-5h・device pins」✅ / (b) (iv) 数値結果 → 「(iv) 数値要約」✅ / (c) early-abort = wave 粒度 → 「wave 粒度 early-abort」✅ (§4: wave-1 = 4 本 → validity+span-watch+video → %12 loud gate) / (d) 中断手順 → 「中断手順」✅
→ 4/4 present。**N2**: notify に (ii)-vs-(iv) budget 関係も含めるべき (§2-N2)。

### (3) ops 面 — **CONCUR**
- device: cuda:0 / MUJOCO_GL=egl + DISPLAY unset (X11 BadWindow 教訓) / GPU-0 4-way ≤4 proc ✅ — memory `reference-mujoco-headless-egl` + `canonical-route-device-fragile` と整合
- budget ~3-5 GPU-h: ~32 本 (24 injection + 8 adj-A)、CP-C 実測 18 本≈1.5-2h/4-way から外挿 ≈2.7-3.5h → **~3-5h は妥当〜やや保守的**。HIGH-COST-GATE (10h) 非該当を確認 ✅
- live GPU headroom: 両基 ~0% util、full headroom (Rs「2gpu 最大8プロセス」枠内) ✅
- span-watch validity: §3 「dual-hold 中 detour 後 span 逸脱 >5mm = invalid-mark + loud 計数」= INV#2 保護 ✅ (→ N1)
- adj-A: fix-⑤ reach screen 通過 offset のみ + R_MISS (−8,+8) 除外継承 = device-fragility 対応 ✅
- video legs: skill-path 必須 (claw-zoom slip/drop) = §運用14 + intra-finger-slip 教訓 honor ✅

### (4) two-key 裁定の妥当性 — **CONCUR**(governance 確認済)
私の O-1 two-key = [K1] (iv) outcome 確認 + [K2] %9 concur + Rs loud notify。実際:
- (iv) = Outcome B → 事前登録 escalation (D-1「Outcome B → GPU 前 Rs escalate」) が発火 → Rs 直接承認「推奨で良い」。
- **K1 (自動 outcome gate) が human 裁定に置換 = より強い authority (automated < human)。gate の目的 (証拠が判断を informs + 独立 %9 check) は両方保全**: (iv) は (ii) が直面する budget tension を pre-flag した証拠を産出、Rs はそれを見て承認、K2 (%9) = 本 request。**gate bypass ではない。** ✅
- **安全性の補強**: charter §8 の順序 = %9 concur → Rs loud notify → build → GPU。∴ Rs notify が GPU 前の最終 veto 窓。「推奨で良い」が load-bearing interpretation でも、notify が spend 前に Rs 訂正機会を保証 → 本 concur は low-risk (build+notify を解錠、GPU は別 checkpoint)。

### (5) band §7 の扱い — **CONCUR**(sequencing + γ soundness、α は劣位と advise)
- **sequencing 正当**: band は最終 verdict 計算 (CP-(ii)-5 OG gate) にのみ影響 → 収録・学習は band 非依存で進行可、CP-(ii)-5 を Rs 決定まで hold = 正しい (band が GO bar を変える = Rs 専権)。
- **γ (%12 推奨) の physics soundness を独立確認**: faithful pair = mean(X:1,Y:0,Z:1)。Y=0 は **INV#2 (88mm HOLD) による正しい挙動であって failure ではない** (U4 code-verified test:4405)。集約 [0.8,1.2] は正しい Y:0 を penalize → per-axis (X,Z∈[0.7,1.3] AND Y≤0.3 AND ee-only≤0.3) が力学に忠実。memory `reference-og-gate-moving-target-gamma-perp-wrong-sign` (decoupled 軸を exempt、per-axis 化) と同 fix pattern。
- **advisory (Rs 判断材料)**: **α (現行 [0.8,1.2] 維持) は劣位** — faithful behavior を既知で STOP させる = false-negative gate。β (mean [0.5,0.85]) は per-axis 診断を失う。**γ を推奨** (Rs 専権は不変)。

---

## 2. Notes(N1 = 拘束的 refinement、N2/N3 = advisory)

**N1 [CP-(ii)-0 で解決すべき実質 refinement] held-phase 振幅 × span-watch の干渉:**
真の dual-hold + 88mm-span phase ({4} ROUTE_C1 / {12} C2_TRANSPORT) で **random-3D [2,8]mm detour の Y (span 軸) 成分 >5mm は span-watch を trip** (>5mm = invalid-mark)。→ (a) yield loss (無効収録)、(b) survivor bias (小 Y 成分の detour のみ生存)。**安全ではある** (span-watch が catch、INV#2 保護は機能) が非効率 + dataset 偏り。**推奨: CP-(ii)-0 mini-spec で dual-hold phase の detour 方向を span 軸 (Y) 成分制限 (XZ-bias or Y≤~3mm) に固定** → [2,8] 振幅を span-preserving 方向に使う。振幅 envelope は不変ゆえ %9 再 concur 不要 (方向の数値確定は元々 CP-(ii)-0 scope)。非 blocking (span-watch + §6 unmet-ladder「held 振幅半減」が self-correct) だが mini-spec で pin すべき。

**N2 [advisory] 共有 2× budget bar の conservatism framing:** §6 v1-analog bar (≤0.001318 = 2× clean) は (iv) が 3/3 失敗した同 bar。(iv) report §4 が「(ii) も同 on-path/off-path budget tension に直面」と pre-flag 済。ただし (ii) = **physical** restoring frame (genuine off-path signal) vs (iv) = synthetic (model-consistent) → (ii) は budget 単位あたり γ⊥ をより動かし得る (これが (ii) の賭け)。**帰結の対称的価値**: (ii) も budget を破れば「imitation-only restoring 教師は synthetic も physical も budget-limited」= (iii)/(i) escalation への収束的証拠。→ **Rs notify に (ii)-vs-(iv) budget 関係を 1 行含める**と Rs が両 outcome の意味を把握できる。

**N3 [advisory] beat metric fragility:** (iv) で null_beat が aug-null の ignore-obs collapse で INCONCLUSIVE 化した (own 1.198≈off 1.204 uniform + val 29×)。(ii) は **CP-D replicate-null そのまま** (augmented せず) → CP-D null は γ⊥ 2.236 = HIGH (obs 応答) ゆえ **同 collapse を構造的に回避** = 正しい選択。ただし beat は依然 confound し得る (null が別の degenerate 理由で低 γ⊥ を持てば) → charter §5「CP-(ii)-0 で beat 解釈 1 行明記」を **必須遵守** + own/off-slice split (U5 手法) を (ii) でも適用推奨。

---

## 3. Conservatism 方向(§運用15)
- (iv) Outcome B = **conservative-definite STOP** (teach-to-the-test 最有利条件でも未達) — bank 済で正しい (report §5 と一致)。
- (ii) OG GO を狙う = **closed-loop に non-conservative** (§6 明記あり: rollout が bank 条件、GO≠自動 rollout、別途 Rs GO) ✅
- band γ 未確定 = CP-(ii)-5 verdict の pending 前提 (Rs 決定まで結論不能) — sequencing で正しく hold。
- (ii)-v1 有効域 = ≤20mm 族 (56-95mm regime 未外挿、deploy へ non-conservative) → stage-2/(iii) 判断が gate (D-3 carry 不変)。

## 4. INVARIANTS(charter 全 8 節が不変更を確認)
INV#1 dual-arm (per-arm single-sided、{11} は R のみ・L holds、span-watch) / INV#2 88mm (span-watch >5mm invalid = N1 の要) / INV#3 DiffIK (EE-target detour via IK、teleport 無) / INV#4 コ (untouched) / INV#5 no-kinematic-trick (physics-faithful servo-restore、新例外 無) — **全て untouched**。

---

## 5. OVERALL — **CONCUR**(残 two-key 解錠)

判定対象 (1)-(5) 全て CONCUR。charter は私の条件2/3 を満たし(複数 phase で更に厳格)、two-key 裁定は governance-sound(human 承認 > automated gate、Rs notify が GPU 前 veto 窓を保存)、band §7 の hold-sequencing + γ 推奨は physics-faithful かつ code-verified。

**発効**: 本 concur により CP-(ii)-0 以降 (build + Rs notify) が解錠。GPU wave-1 は Rs loud notify 後(条件3 の最終 veto 窓)。
**拘束条件**: N1 (dual-hold detour 方向を span 軸制限、CP-(ii)-0 mini-spec で pin)。
**advisory**: N2 (notify に (ii)-vs-(iv) budget 関係)、N3 (beat 解釈 pin + own/off-slice split)、band α は劣位 → γ 推奨 (Rs 専権)。

*%9 OPS-SUPERVISOR — 2026-07-03 08:48 JST (書込前 `date`)。0-commit / INVARIANTS untouched / 編集 = 本 file + log.md のみ。*
