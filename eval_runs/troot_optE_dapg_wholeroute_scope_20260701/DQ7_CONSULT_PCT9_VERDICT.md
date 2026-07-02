# DQ7 consult verdict — OPS-SUPERVISOR (%9) independent adjudication of D-1〜D-5 / O-1〜O-3

**Written: 2026-07-03 05:44 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Charter:** `consult_dq7_decisions_opssup_20260703.txt` (%12, Rs verbatim 07-03 05:3x「T-ROOT-OPS-SUPERVISORと相談して決めて良い」).
**Protocol compliance:** decision = %12 position + %9 CONCUR で確定 (deadlock 項のみ Rs escalate)。Writes = this file + log.md append only。0-commit / no planning-surface / no spec / no code edits。HEAD = `6365884e4f` (verified `git rev-parse`).

## 0. Grounding — 一次 SSOT を自ら read (相談状 narrative 非依存)

| Source | What I verified myself |
|---|---|
| `DQ7_OFFPATH_SCOPING_COORD2.md` (152 行全読) | §1 two-failing-legs / §3 injection map + Fact A/B / §4 options + (iv) m1-m4 / §5 reuse / §6 staged rec / §7 D-1..D-5 |
| `b2_cpE_og/bc/og_gate.json` | overall STOP; movable γ⊥ = 2.497/1.257/1.041/1.055 (全 >0.5 bar); C2_REGRASP pair seg-follow **0.282** (band [0.8,1.2]) + ee-only **0.973** (≥0.9 STOP); null_beat **−0.261** (bar +0.15); carried={GUIDE_C2}; 2mm vs 10mm = 2.497→2.498 / 1.257→1.258 (スケール不変 obs-following 実証); guard2 L_max 18.77mm |
| `b2_cpD_report.md` | BC whole-demo val 0.000659 vs NULL 0.011979; **0.011979/0.000659 = 18.18 ≈ 18× 再計算一致** (§運用28); 9 train demos (6930=9×770) + val (0,0),(−10,0); GPU-1 90-91s |
| `00-DESIGN-STATUS-LEDGER.md:45` tail | B2 完結 = OG STOP banked / 仮説 REFUTED (rollout GPU 0 分) / fork-(iv) 不変 / Rs「A」→ DQ7 / fix-⑤ `0b711c6b31` / CP-A′ 17/17 |
| `T-ROOT-optE-route-dapg-C1C2/state.md:38-44` | DQ namespace: DQ1=B / DQ3 GO / DQ5 ratified / DQ6 fork-(iv) ADOPTED / B2 chain 全記録 |
| `log.md:7208/7214/7218` | Rs「A」verbatim 05:00 / prior-art 8hit→3source→delta→続行承認 + %12 鋭利化指示 ((a) first-class + (ii)vs(iv) 判別軸 — doc §4 に反映済を確認) / scoping 受理 + stale cite 是正 (:4404) |
| `og_offline_gate.py:51,97-104,172,193` | (iv) sampler の基盤 = `_holder_axes` + `co_seg = p >= grasp_close` co-move 機構が committed gate に実在 |
| `B_BC_BUILD_SPEC.md:155-162` | E15 prior-art 原文: augmented corrective 棄却理由 (a) post-grasp EE/seg obs 不整合 (b) 新 perturbation 設計面 + **「将来再訪可」条項の実在** を独立確認 |
| `docs/upstream_newton_xfrc_inert_2026-06-11.md` (→ newton#3128) | xfrc_applied = SolverMuJoCo **CPU path で silently discarded** (提出済 upstream bug) — D-2 の技術的裏付け |
| 実測 (07-03 05:3x-05:4x) | `git log --branches --not --remotes` = 未 push **正確に 3 件** (6365884e4f/f7693b67a3/4e7cbc70c7) ✓ / nvidia-smi compute apps **0** (両 GPU 空き) / disk 198G free / preflight **8/11 PASS・0 FAIL・3 WARN** (P7 stale locks >1h + P8 paused=True + P11 NEST snapshot stale) / %11・%10 pane = IDLE (tmux capture) / recorder P3 latent defect = **FIXED on-disk** (`route_demo_recorder.py:276-277` CLIP2_X/Y in env_gates + `:311` resolved_clip_c2_xy setdefault None) |

**Prior-art gate (V10、%9 独立再走):** `check_thread_vault_prior_art.sh --fail-on-blocker detour injection perturb-and-recover dagger offpath` → BLOCKER_CONTEXT_FOUND、ただし**全 hit = DQ7 scoping doc 自身 + self-referential ledger 行** = 本 task の provenance であり prior FAILED path ではない。実質 prior-art = E15 `B_BC_BUILD_SPEC.md:158` のみ → 原文読了、doc §2 の delta ①-④ 成立を独立確認 (②: 棄却時 live だった「restoring=B2-DR 学習対象」仮説を B2 が REFUTED = 前提変化; ④: 再訪可条項 verbatim 実在)。**続行正当 (documented delta)。**

---

## 1. 判定 D-1〜D-5

### D-1 staged package 採否 — **CONCUR (ADOPT)** + 条件1
- 受入幾何 (§1) を一次計器で再確認: **falsify すべき足が 2 本** (restoring: movable 全 STOP + ee-only 0.973 / following: seg-follow 0.282) + null_beat −0.261。off-manifold 教師の構造的不在は CP-D/CP-E の測定と整合。
- (iv)→(ii)→[(iii) 繰延/(i) escalation] = cheapest-falsifier-first は evidence-per-GPU-h 最大化として正当。**(iv) Outcome B の非対称価値**: teach-to-the-test 条件下でも γ⊥ 不動なら capacity/data 構造問題 → (ii) (物理データ、同じ manifold 族) も失敗が予測される → GPU 消費前 Rs escalate は正しい停止規則。
- **%9 追加根拠 (相談状未引用):** og_bprime 閉ループ収縮 probe で **C2_REGRASP contracted=false (5.0→5.525mm 発散)** vs C1_SEAT/C1_PIN/C2_DUAL_SEAT/C2_SETTLE は収縮 — {11} の restoring 欠落を独立計器が裏書き。
- (iv) 単独 GO 非 bankable (m1-m4) ✓、(ii) frames = (iv) の独立 eval (m3) ✓。
- **条件1 (pre-registration 鋭利化):** (iv) charter で **Outcome A/B の数値境界を train 前に事前登録**すること。「γ⊥ 不動」の文言のままでは事後裁定になる (例: A = m1 held-out 方向での worst-movable γ⊥ が bar 0.5 到達 or 改善率 ≥X% / B = それ未満、+ m2 augmented-null beat の bar ≥0.15 再利用を明記)。数値は %12/%11 が charter で確定してよい — 「事前に数値で固定する」ことが条件。
- 非拘束の付記: (ii) の hook build (0-GPU コーディング) は (iv) 実行と並行可能 (outcome gate が拘束するのは (ii) の **GPU 収録 launch**)。wall-clock 短縮が欲しい場合の option、%12 判断。

### D-2 注入機構 envelope = EE-target detour のみ — **CONCUR** (補強あり)
- 診断された病理は **EE 側 obs-following** (γ⊥ = d(tgt)/d(ee) transverse; failing cells {0,1}+{11} は全て EE-restoring 失敗) → EE detour が直接カバー。かつ EE 系は **復元 expert が構造的に実在** (Fact A: ik_move_both 絶対 target servo、B1′ P2a 実測 433mm→9-16mm 再 anchor)。
- governance: xfrc = 新 disturbance class = Rs 授権事項 — 本委任 (D-2) で技術的には決められるが、診断された必要性が無い以上 %12 の「不採用 + residual gap 時に Rs へ別途提案」が正しい保守形。
- **%9 技術的補強:** `docs/upstream_newton_xfrc_inert_2026-06-11.md` (newton#3128 提出済) — **xfrc_applied はこの stack の CPU path で毎 step silently discarded**。GPU/MJWarp path は未検証。つまり xfrc は「Rs 授権があっても instrument-first の較正検証 (probe-instrument calibration triple) なしには使えない」チャネル。EE-only 選択は governance と技術の両面で支持される。

### D-3 (ii) 振幅 envelope = probe-matched 2-10mm + tail ~20mm — **CONCUR** + 条件2
- probe-matched ✓ (og_gate.json の og_b は正確に "2mm"/"10mm" 族)。tail ~20mm は **データ自身の自然逸脱スケールと一致** (guard2_expected_fires L_max = 18.77mm) — probe 族の僅か外まで教師を張る合理的拡張。
- INV#1 (both-arms-engaged) / INV#2 (span-watch 収録 validity filter) の組込 ✓。
- **条件2 (phase 差別化 cap):** **20mm tail は pre-contact cells ({0,1} + {11} R-arm pre-contact) に限定**すること。held/in-contact phases (§3 map の「small」= 4,9,10,12 / 「tiny pre-seat」= 5,13,14) は **≤10mm 以下で charter に phase 別数値を明記** (「small」の未定量のまま実装に渡さない)。理由: dual-hold 中の片腕 detour は把持セグメントを張る (WR retention は choreography-sensitive、RS71:26; drop risk r3) — span-watch は事後 filter であり、振幅 cap は収録の無駄打ちを事前に防ぐ。LIFT 回避 ✓ (§3 map どおり)。
- carried gap (doc 自認、%9 も確認): (ii)-v1 verdict の有効域は ≤20mm 族。B1′ 実測の 56-95mm regime は未カバー → stage-2/(iii) 判断は (ii)-v1 verdict 後で正しい。

### D-4 leg-2 (seg-follow 0.282) 教師 = BOTH — **CONCUR**
- (iv) seg-co-move leg = **leg 2 を直接教える唯一の機構** (co-moved label は構成上 gain→1 を教える; band [0.8,1.2] に対する設計として正しい)。co-move model = 線形近似の model-consistency 残余 risk の明示 ✓。
- adj-A = ~0 限界 build、かつ **非 load-bearing の宣言が実測に基づき正しい** (B2: on-path val 18× 良好でも seg-follow 0.282 だった = on-path 多様性は leg 2 を直さないことが測定済)。cross-validate 用の副次として同梱 = 正当。

### D-5 (i) DAPG re-scope spec 起草 = (ii) verdict 後 — **CONCUR**
- (ii) の結果が (i) の要否と形を決める / 並行起草 = anchor bias + %10/%12 bandwidth / DQ1 precedent = 「保持」であって前倒しではない — いずれも成立。
- 加えて §4.2-(i) の anatomy (CRIT2 demos 解消 / HIGH5・MED10 moot / M-A env-ABSENT が standing CRITICAL) が既に banked = escalation 発火時の高速起草の下地は確保済 → 今書く限界価値は小さい。

## 2. 判定 O-1〜O-3

### O-1 spend/authorization — **CONCUR** (blocking Rs GO 不要と判定) + 条件3
- **(iv):** 実質 0-GPU (GPU-1 90s×2 + OG offline)、locked-file 不触 (converter + og param のみ) → 本委任下で %9 CONCUR 後の即 launch に同意。ただし build charter 自体には通常の §運用2 gates (L-TRIAGE / rule-check / 必要なら pre-debate) が適用される — 本 consult はそれを免除しない。
- **(ii):** HIGH-COST-GATE **非該当を確認** (2-3h ≪ 10h / production launch でない / multi-skill chain でない)。two-key ((iv) outcome + %9 concur) + **Rs への loud 事前通知 (non-blocking) + early-abort 構造** = Rs が design 決定を明示委任した本状況では十分と判定する。blocking Rs GO を要求する代案は検討したが棄却: (a) 委任 verbatim が decision を許す、(b) loud notify が veto 窓を保存、(c) B2 で同構造 (wave 粒度 early-abort) が機能した実績、(d) faster-pace directive (確認ゲートの削減、正しさチェックは維持)。
- locked-file hooks = 確立済 L3-lite pattern (byte-identity precedent ×2: `fd005ab83f` recorder / `0b711c6b31` fix-⑤) + §0 keyword match で層2/層5 chain — この経路を (ii) build に必ず踏ませる (既定どおり)。
- **条件3 (loud notify の内容要件):** Rs 通知には最低限 (a) GPU-h 見積と device pins (cuda:0 / MUJOCO_GL=egl+DISPLAY unset)、(b) (iv) outcome の数値結果、(c) early-abort 基準 = **CP-C wave 粒度 precedent の再利用** (wave-1 = 4 収録 → validity/span-watch 通過率を loud 確認してから継続)、(d) 中断手順、を含めること。
- GPU 実測: compute apps 0 (両 GPU 空き)、Rs「2gpu 最大8プロセス」枠内に十分な headroom。

### O-2 pane assignment — **CONCUR**
- stage (iv) 実装 charter → %11: (iv) の touch-points = `route_demo_to_bc.py` (augmentation branch) + `og_offline_gate.py` (held-out-direction param) = **%11 が B2 で build した当のファイル群** (converter v2 `c5e58d5636` / CP-D / fix-⑤ 実装者)。owner 整合 ✓。
- 実測: %11・%10 とも現在 IDLE (05:4x tmux capture) → 即 dispatch 可能。%10 = 次 task 待ち ✓ (M1/CP-A の planning-surface hold 作業は昨夜完了想定 — 未完なら %12 が確認のこと)。

### O-3 ops リスク — **CONCUR + %9 追加 5 点**
- 相談状記載分を実測で確認: 未 push = 正確に 3 件 (4e7cbc70c7/f7693b67a3/6365884e4f、Rs「push」待ち intentional) ✓ / GPU topology = GPU-0 (A6000) 収録・GPU-1 (Blackwell) 学習は cpD 実測と整合 ✓ / stale locks = preflight P7 WARN 11 件 (>1h; **P8 paused=True と整合 = 停止中ハーネスの design どおり**) / P11 NEST snapshot stale (state.md の方が新しい) ✓。0 FAIL → 作業続行可。
- **追加1 (解消済の確認):** P3 cross-PV で %9 が挙げた recorder latent defects (meta C2 hardcode / CLIP2 env_gates 欠落) は **修正済を on-disk 確認** (`route_demo_recorder.py:276-277,:311`)。(ii) は meta に**新 field (injection windows)** を足す → 同じ records-vs-fact 審査 (meta が嘘をつく将来 config が無いか) を (ii) review で再適用のこと。
- **追加2 (durability):** B2 STOP verdict + DQ7 scoping の evidence は **未 push 3 commits = 単一 disk 上の git のみ**。P3 durability 教訓の同族 (弱形)。次の Rs 接点で「push」の再提示を推奨 (non-blocking)。
- **追加3:** xfrc #3128 は upstream 提出済 — 将来 D-2 を再訪する場合は instrument-first 較正 (calibration triple) を必須とする。
- **追加4 (schedule):** Fable-5 常用窓 = 7/7 まで (Rs 07-02 決裁、log.md:6973)。(iv)+(ii) ≈ ≤1 日で窓内に余裕 — schedule risk なし。
- **追加5 (§運用28 調停):** 相談状 §1.1「survivor train 11 + held-out 3」vs cpD 一次「9 train (6930=9×770) + val (0,0),(−10,0)」→ **調停: 18 − R_MISS 2 − seat-filter 2 = 14 valid = 9 train-fit + 2 whole-demo-val + 3 held-out-hull** ((−8,+8) 除外で 4 corner → 3)。「train 11」= val 2 を含む train pool の意。実質矛盾なし — (ii)/(iv) charter では cpD の語法 (9 fit + 2 val) を使うことを推奨。

## 3. Conservatism 方向 (§運用15 必須 field)
- **OG STOP** (B2 で発生した側) = 保守的確定 — bank 済で正しい。
- **OG GO** (これから (ii)/(iv) が狙う側) = **offline 主張 = closed-loop 成功に対し non-conservative** (必要条件であり十分条件でない; gate は 2× in-sim 予測実績があるが、GO の bank は §8-1 held-out rollout を通過して初めて成立 — doc §6-2 と一致、ここで明文化)。
- **(iv) GO** = 循環性により単独 bank 不可 (m1-m4) — 方向: teach-to-the-test 側に non-conservative、doc 自認どおり。
- **(ii)-v1 GO** = ≤20mm 族に対して有効、56-95mm regime へは未外挿 (non-conservative for deploy) → stage-2 判断が gate。

## 4. OVERALL VERDICT

**CONCUR ×8 / CHALLENGE 0 / ABSTAIN 0 — deadlock 項なし (Rs escalation 不要)。**
D-1〜D-5 + O-1〜O-3 の %12 position を全て承認。付帯条件 3 点 (拘束):
1. **(iv) Outcome A/B の数値境界を train 前に事前登録** (D-1)
2. **(ii) 振幅は phase 差別化 cap を charter に数値明記** — 20mm tail は pre-contact {0,1}+{11} 限定、held phases ≤10mm + phase 別数値 (D-3)
3. **(ii) launch の Rs loud notify 内容要件** — GPU-h/device pins/(iv) 結果/wave 粒度 early-abort 基準 (O-1)

決定は本 CONCUR により確定 (相談状 §0: %12 position + %9 CONCUR)。次アクション = %12: (iv) charter → %11 (即時可、両 pane IDLE 確認済)。

*%9 OPS-SUPERVISOR — 2026-07-03 05:44 JST (書込前 `date` 取得)。INVARIANTS untouched / 0-commit / 編集 = 本 file + log.md のみ。*
