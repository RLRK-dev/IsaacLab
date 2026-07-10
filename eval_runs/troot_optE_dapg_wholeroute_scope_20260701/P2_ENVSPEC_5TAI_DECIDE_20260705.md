---
doc_class: reference
---

# env-spec 5体 [VERIFY] — DECIDE 記録 (CC1 = %12、2026-07-05 10:4x-11:1x)

**対象:** P2_ROUTE_ENV_SPEC_INPUT v1.4 + P2_REWARD_ARTIFACTS v1.2。**panel:** CC2 (RL 機構) / CC3 (THREAD 物理・env) / CC4 (cost・実行可能性) / CC5 (governance) / CC6 (NHA)。gate 前提 = pre-check chain (BLOCK 10:04 → WARN 再走 10:36 → fixes+spot-diff PASS 10:45、jsonl 3 entries) + %9 cross-PV 台帳 (`P2_W0C_CROSSPV_PCT9.md`)。

## Verdicts
CC2 = FAIL-as-submitted → CH1-3 fold で PASS-with-fixes / CC3 = PASS-with-fixes / CC4 = PASS-with-fixes / CC5 = PASS-with-fixes / CC6 NHA = **HOLD (sequencing、設計否定でない)** — 解除 3 条件 (a) 再走 log 化 (b) P3-grid 前倒し (c) AR-extend disposition。

## 主 CHALLENGE と disposition (全 ACCEPT; partial 1)
| # | 要旨 | disposition → 反映先 |
|---|---|---|
| CC2-CH1 CRIT | α (ii) の探索算術不成立 — per-arm σ=7.5mm は span-noise 死 / 生存 σ≤~2mm で p_hit(miss>3mm)≈0。c2 は表現可能を作るが発見可能を作らない | ACCEPT → spec §2 v1.5 (structured-common-mode σ / p_hit 事前計算 discharge / corner-mask / 境界=discovery-feasibility) + artifacts (iii) 注記 |
| CC2-CH2 HIGH | corner 上で持続力が全て逆向き (Δ≡0 anchor 床 0.5 / anti-corner relabel / α-PC(b) pause-tax) | ACCEPT → corner-mask + anchor decay 選択を P4 pre-reg に |
| CC2-CH3 HIGH | relabel の trainer 側 sink 未仕様 + devplan と矛盾 | ACCEPT → spec §2 (交互 aux imitation update 仕様) + §7 cost 行 |
| CC2-CH4 MED | β stage-mix 分布未指定 / handover 速度 alias / latch 未明文 | ACCEPT → latch 明文 + state-bank 化で quasi-static 化 + mix = design-gate 項 |
| CC2-CH5 MED | D-C yardstick 未 pre-register (metric 選択が勝敗を決める) | ACCEPT → §9-3 common comparator pre-register |
| CC3-CH1 **CRIT** | **span-guard 全 phase 適用 = canonical route 自身を殺す普遍 deadlock** (route は unclamp→guide→regrasp で span 92→170mm を正当通過; banked ruling は {1,2,3} のみ scope + informative tier) | ACCEPT (+%9 が V3 見落とし own) → spec §4 guards v1.5 (dual-grip 限定列挙 f1 + tier informative 既定 f2 + guards-quiet DoD) |
| CC3-CH2 HIGH | G4 は β で tap-hack 化 / contact 抽出 = single-world event-time | ACCEPT → G4 cable-lane 相対再定義 + batched contact §7 行 |
| CC3-CH3 HIGH | curriculum の実装 fork 未言明 (vectorized controller / state-bank / synced reset) | ACCEPT → state-bank = working assumption + DR 量子化文書化 + prefix overhead smoke 計上 |
| CC3-CH4/5 MED | converter phase-label = script-schedule だと repr-mismatch / latch 無 = +5 farming | ACCEPT → predicate-評価 label pin + 一致 check DoD + latched-monotonic 明文 |
| CC4-CH1 HIGH | curriculum 100-300 LOC は wrapper 価格 — 2,476 行 monolith 抽出が未計上 | ACCEPT → route-executor 独立行 (300-800 touched + byte-repro regression) |
| CC4-CH2 HIGH | smoke DoD 5/8 に pass 基準なし | ACCEPT → 全 8 項に数値 bar (§4 v1.5) |
| CC4-CH3 HIGH | P3 grid: n 未定 (≥95% 枝は n=16 で数学的到達不能、n≥59 要) + decision の後に sequence = timing 逆転 | ACCEPT → **P3-grid 前倒し (81 cells、n>59 確保)** = PREREG banked + %11 charter 済 |
| CC4-CH4/5 MED | env LOC 床 2.0-3.5k / gate topology 未定 / eval 床 ~18h/arm @900 / P4 数値空欄 / band 二重 sitting | ACCEPT → §7 restate + staged per-component chains + packet に提案値 + band provisional 明記 |
| CC5-CH1 HIGH | pre-check 再走が log 未記載 + 5体 が「再走要」文言と順序不整合 | **PARTIAL-ACCEPT**: 再走は実施済 (WARN) + verifier が 2 回目 full を waive (verbatim fix + spot-diff 条件、%9 実施) — ただし log 欠落は事実 → jsonl 2 entries 追記で解消 + 本 DECIDE に waiver 経緯記録 |
| CC5-CH2-4 MED | packet に L2 confirm + supersession banking 欠落 / INV #4→#5 誤番 / M-D stale 0.088 / %9 verdict 未 bank | ACCEPT → §9-3 v1.5 + renumber + M-D 注記 + `P2_W0C_CROSSPV_PCT9.md` (banked) |
| CC6 NHA | HOLD (sequencing): (a) 再走 log (b) P3-grid 前倒し (c) AR-extend 段落 + premise 再確認行 | ACCEPT → (a) 済 / (b) JOINT 済・実行中 / (c)+premise 行 = §9-3 packet v1.5 |

## NO_ACTION_EVALUATION + DECIDE
NHA の null は「packet/build を今出すな」= sequencing — 3 条件は全て充足路線に乗った ((a) 済 / (b) P3-grid charter 発行済・実行中 / (c) packet 定義に組込)。設計本体は 5 lens の敵対検証を fix 込みで生存。**DECIDE = spec v1.5 + artifacts v1.3 で PASS-with-fixes 確定; Rs W0-a′ packet は P3-grid 結果 fold 後に提示** (NHA 条件と CC4-CH3 の evidence-first を同時充足)。
**joint:** %9 = DECIDE cross-PV CONCUR (11:0x、[1][2] own + f1/f2 + common-mode 原則昇格提案 → v1.5 採用) + P3-grid JOINT (g1-g4)。

## 昇格した恒久原則
**common-mode decomposition** (spec §4 原則 0): dual-arm pair 量に作用する全機構は common-mode + differential に分解し、differential 成分は明示設計なしに導入しない — 本日 3 事故 (relabel / clamp / 探索ノイズ) の収束。

*%12 — 11:1x JST。full panel 出力は %12 session 記録; 本 file = decision-of-record。*
