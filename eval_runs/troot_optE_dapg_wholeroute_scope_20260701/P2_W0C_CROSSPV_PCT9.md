# P2 W0-c spec/artifacts — %9 OPS-SUP cross-PV verdicts (per-version scope、provenance bank)

**Author:** %9 OPS-SUP (w2:p1)。**Written:** 2026-07-05 10:57 JST (`date` 同一ターン取得)。**Charter:** CC5-CH4 (env-spec 5体) の provenance 要件に基づく %12 依頼 (10:54)。
**Authority chain:** Rs 標準権限 08:5x「次の選択は T-ROOT-OPS-SUPERVISORと相談して決定して良い」→ %12+%9 JOINT-DECIDED [2] = W0-c 並行開始 (banking `231639c0d1`) → %9 = W0-c cross-PV verifier (9-lens checklist 09:08、%12 受入基準として採用)。
**Status:** 記録 bank (0-commit、commit = %12 banking window)。verdict はすべて発行時点の対象 version に scope される — 後続 version には自動継承しない。

---

## Verdict 台帳 (per-version scope)

| # | 時刻 (JST) | 対象 | verdict | 主内容 | scope 限定 / 事後判明事項 |
|---|---|---|---|---|---|
| V1 | 09:28 | spec v1.0 (108行) | **CONCUR-W-CORRECTIONS** (blocker なし) | CHALLENGE 4 = E-1 transition-export 欠落 / E-2 reward 成分ログ欠落 / D-1 oracle mid-servo ACHIEVED-vs-COMMANDED 未 pin / H-1 reach 0.9mm fragility 欠落。精緻化 4 = M-C option(d)+P3-grid evidence-gate 化 / β-F2 predicate 結合単一障害点 risk + unit-test DoD / HIGH4 α-12D cross-ref / horizon p99>810 rule。独立検証 = T=7707 quad-source (LEDGER row44 + B_BC_BUILD_SPEC:14 + 自身の 07-02 recompute [P3_RECORDER_CROSSPV_OPSSUP.md:13] + batch meta ×3)、771=ceil(7707/10)、900=×1.167、§運用22 (当時 6×5+200=230 構成で検算)、M-C 反例 = CP-C 4/18 base task-FAIL | v1.0 のみ。§運用22 の 230 は v1.2 で 225 (5×5+200) に正しく訂正された |
| V2 | 09:43 | spec v1.1 diff | **PASS (8/8 着地、9-lens 全 PASS)** | V1 の 8 修正の着地を grep+読解で確認 (D-1 は ACHIEVED 大文字表記で初回 grep が外れたのみ = 実在) | v1.1 のみ |
| V3 | 10:19 | spec v1.3 + artifacts v1.1 (pre-check BLOCK 10-issue 反映版) | **CONCUR-W-1-CORRECTION** | 10/10 disposition 完全性 PASS (pre-check-log.jsonl 10:04 全列挙と照合、silent drop なし)。指定 5 領域検証 (92.4 再中心 / counting rule 81.25% vs 77.78% / obs v2.1 57D / draw 経済 / 性質② sunk-cost)。ground-truth 表 4 値・γ 減衰 (0.99^180=0.164 / 0.99^600=0.0024)・§運用22 225:19 全て独立検算 EXACT。**CORRECTION 1 = c3「oracle corner-relabel」の役割誤帰属** (oracle = script-faithful → base-FAIL corner に beyond-script 補正を教えられない = mini-test 機構 C と同型) → (i) drift-recovery 教師 / (ii) c2-sized 局所 RL = primary / (iii) 超過 miss = draw 会計、に再構成 | ⚠ **見落とし (own、5体 CC3-CRIT が捕捉):** 「92.4 再中心 = FAITHFUL-to-banked-ruling CONFIRM」は **center 次元のみ正しく、ruling の phase-scope 次元を検査しなかった** — ruling (`DQ7_INV2_ASSERT_RULING_PCT9…PCT12.md`) は absolute check を **{1,2,3} のみ + {0} は絶対 assert 禁止 (span 可変 ~92-403mm) + optional/informative tier** と明示していたが、spec の「span-guard 全 phase 92.4 中心 (M-D 行: SEAT まで全 phase 適用)」+ hard-guard 化はこれに不忠実 — route 自身の choreography (unclamp→guide→regrasp で span 92→~170mm) を殺す普遍 deadlock。私は当該 ruling を同一 session で読み {1,2,3}-only 文言を quote までしていたのに、spec 照合時に headline (center 値) だけ照合した。**lesson: ruling-faithfulness 検査は ruling の全次元 (center 値 / phase-scope / hard-vs-informative tier) を列挙して各個照合する — headline 一致で FAITHFUL を宣言しない** |
| V4 | 10:27+10:31 | spec v1.4 + artifacts v1.2 (CORRECTION 1 + nit 2 反映) → N1-N7 spot-diff | **PASS (6/6) → spot-diff CONCUR → 5体 launch GO** | (i)(ii)(iii) 構造・DAG driver・§5「corner 教師ではない」・obs v2.1 冒頭・[53:55]/[55:57] 全着地。N1 = retired-term 全文 absence grep 0 hit / N2 truncate 3 注意 (quit-button / draw-flag aliasing / time_outs 純度) + DR-support 除外推奨 CONCUR / N3 prefix 3 pin / N4 §A10 dangling 除去 / §A8 増分 4 行 (0.995^10=0.9511 検算 EXACT) / 57D 整合維持 | ⚠ V4 時点の私の grep は「新文言 presence」のみで「旧文言 absence」を欠いた (N1 残存 2 箇所は pre-check 再走が捕捉)。以後 correction 反映確認 = retired-term 全文 absence grep を必須 leg 化 |

## 検証方法の記録 (再現用)
- 一次計器: `logs/pre-check-log.jsonl` (10:04 BLOCK 10 / 10:36 WARN / 10:45 FIXES-APPLIED+SPOT-DIFF-PASS — 後者 2 entry は %9 が 10:57 tail で実在確認)。
- on-disk 独立検証: `DQ7_INV2_ASSERT_RULING_PCT12.md` (92.383-92.418 実測表) / `DQ7_DAGGER_BUILD_SPEC_V2_MINIMAL_COORD2.md:69-73` / `test_newton_clip_routing.py:4593-4600` (regrasp_ok ANTI-REVERT block) / `task_config.py:264/:368/:373` / `policy_route_runner.py` :826-834 (per-arm guard、mini-test CRIT1 の carry 根拠)・:843-851 (state-blind _tp)。
- 算術検算: 7707/10→771 / 900÷771=1.167 / 88+5−92.4=0.6mm / 13/16=81.25% vs 14/18=77.78% / 42+6+1+1+1+2+2+2=57 / 225:19=1:11.8 / γ 減衰 3 値 / hover −9・drop −11・G1G2drop −4・T771 +217.29・T900 +216.00。

## 現在 status (10:57 時点)
V4 後に env-spec 5体 実施 → CC2 FAIL-as-submitted→fix可 / CC3・CC4・CC5 PASS-w-fixes / NHA HOLD (sequencing)。decisive catches ([1] span-guard 全 phase deadlock = 上記 V3 own / [2] 探索算術 / [3] G4 tap-hack / [4] P3-grid N 問題ほか) への %9 DECIDE cross-PV = 別送 (10:5x dispatch)。本 file は V1-V4 の provenance bank であり、DECIDE round の verdict は含まない (発行後に %12 が別途 bank)。

*%9 OPS-SUP — 2026-07-05 10:57 JST。0-commit。*
