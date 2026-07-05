# Verbal-Teaching Motion Authoring — CHARTER v1 (Rs 承認 2026-07-05 20:0x)

- **目標 (Rs verbatim)**: 「今後、効率的に言葉で教示できるようにしたい」(2026-07-03) — 対象 = **scripted route の動作そのもの** (学習系は対象外、Rs 訂正 07-03 05:1x)。効率化 = motion authoring loop の往復数削減。実証例 = fix-⑤ (言葉 2 通 → ~1.5h landing)。非効率の実例 = 2026-07-05 の 3 往復 (「この動作に戻せ」→「表から逸脱するな」→「この動作が基準だ」)。
- **承認**: Rs「承認」2026-07-05 20:0x — W0-e 完了後の**最優先 charter**。本 doc = 起草のみ (paper)、実装着手は W0-e close 後。
- **memory 根拠**: `project-rs-goal-efficient-verbal-teaching-2026-07-03` / `feedback-step-table-structure-drives-guide-generation`「43step表からはずれるな」。

## W1: table-driven runner (表 = 動作の生成源)

- 現状問題: runner (`test_newton_clip_routing.py`) の choreography は code が 43-step 表 (`data/waypoints/full_43step.json`) を**手写し** — 表に無い動作を code 側で追加できてしまう (実績: W0-e の C1v2-LIFT/SHIFT/TRIM + F-3 = 発明動作、Rs 指摘 2026-07-05)。
- 目標形: C1→C2 route の leg 系列を表 (または後継 route-table) から**生成**する。表に無い動作は構造的に生成不能。
- 制約:
  - **byte-identity 移行証明**: table-driven nominal の npz sha ≡ 現 nominal npz sha (150mm 新基準、RUN1_REFERENCE v2)。
  - locked runner 編集 = L3 chain (5体 [VERIFY] → RULE-CHECK) + Rs 明示授権。
  - INVARIANTS #1-5 不触 (DUAL-ARM / 88mm span / DiffIK-only / コ-gripper LOCK / no-kinematic-trick)。
  - offset 補正 (F-1b/F-2/F-1a v1 形 = 既存 leg の座標補正) は表 param として表現 (新動作でなく)。

## W2: 教示 loop の標準化 (言葉 → 表 → 検証)

- loop: Rs の言葉 → 表の row 編集 (**座標・param のみ、構造不変**) → 動作再生成 → **機械検証 2 本** (leg-diff SAME-STRUCTURE [`w0e_video_tools/route_leg_diff.py`、GT 検証済 2026-07-05] + 参照差分 2-pass 動画 [%9 設計、dual-stream/witness-aim 込]) → Rs 確認。
- 指示語彙の最小 set を表 param に対応付け (例: 「間隔を倍に」= CLIP spacing param ×2 / 「もっと深く押し込む」= seat z target / 「ゆっくり降ろす」= leg speed_factor / 「真上から」= approach x/y = clip 座標)。
- 動画は基準 (`p2r_c11_route.mp4` = Rs-DECLARED MOTION STANDARD、LEDGER 行 2026-07-05) との差分提示を標準形に。

## DoD (charter 完了条件)

1. 実例 3 本を各 **1 往復以内**で landing (候補: 間隔変更 = 表 1 param / clip 座標 nudge / 降下速度変更)。
2. 全実例で leg-diff = SAME-STRUCTURE (座標 delta のみ) を機械証明。
3. nominal byte-identity 保持 (教示は offset/param-gated)。

## Gates / 順序

- 実装開始 = **W0-e close 後** (150mm matrix → 動画 Rs gate → 81 再走 → packet v1.1)。
- 設計 = 本 charter → 設計案 doc → L3 chain (5体) → Rs 設計承認 → build。
- 新 NEST node 起票は設計案提示時 (本承認 = [DEFINE] 相当)。
