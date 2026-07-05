# RUN-1 byte-identity 基準 v2 (150mm + lift-raise 世代、%12 2026-07-06 01:3x 凍結)

- **基準 npz sha256 = `5f1c3f9238f45057011cfad1d010ac43000cb179b76b61d0461733a9075416cf`**
- 対象 = `w0e_liftraise_smoke/2037_nominal/route_demo_raw.npz` (CLIP2_Y=0.000 [Rs 間隔倍化] + LIFT_M 0.08 [Rs「クリップ上面かすり」修正] 適用後の nominal)。
- 二鍵確定: ①p3 (%11) 報告値 ②%12 自前 `sha256sum` on-disk 再計算 — EXACT 一致。%9 照合は standby leg。
- **旧基準の系譜 (loud supersession、silent 上書きなし)**:
  - v1 `3f44125551868e278ff53e3ad454242e7ade17bd7a87237061f03d1d9cc3235d` (`RUN1_REFERENCE.md`) = 旧 geometry (spacing 75mm) 基準として **retire** — W0-e 初期 build (F-1b/F-2/F-1a) の nominal byte-identity 証明はこの基準で成立済 (歴史記録として有効)。
  - 中間 `bd7a4f413d…` (150mm、LIFT_M 0.05) = Rs「かすり」修正で同日 retire (正式 doc 化前)。
- **v2 変更理由 (いずれも Rs 直接指示 = 基準動作自体の口頭修正)**: ①C1-C2 間隔 ×2 (07-01 lever 再適用、C2 着座 FIX) ②搬送高さ +30mm (cable bottom 857 > clip 上面 850、かすり解消 + offset C1 の垂直進入で escape 解消)。
- **構造保証**: 全 4 smoke cell が Rs 宣言基準動作 (`p2r_c11_route.mp4` = LEDGER MOTION STANDARD 行) に対し leg-diff **SAME-STRUCTURE** (追加/欠落 leg 0、座標 delta のみ 47-53 本) — `w0e_video_tools/route_leg_diff.py` (%12 実行 2026-07-06 01:3x)。
- RUN-1 受入 (81 再走前の nominal 照合) = 対象 build の nominal npz sha が本 v2 値と一致 (%12 が raw file から独立再計算、引用値を鵜呑みにしない)。meta 側 head_sha/git_diff_sha256 の build 差は期待どおり — 比較対象は npz のみ。

## 追記 (2026-07-06 01:4x)

- **%9 COUNTERSIGN 成立** (01:40、直読 + 私鍵 sha256sum EXACT) → 三鍵完成 (p3 %11 / %9 / %12)。
- **flank producer field = 不追加 決定** (%12 提案 + %9 CONCUR、loud 記録): 再 grid の C1 flank leg は両 parser (recount_strict_v2.py / p9_recount_strict_v2.py) の npz fallback — 同一凍結定義 (|y−0.15|≤10mm・final frame・max z) の独立実装、旧 grid 40/81 相互較正済 — で走る。**受入条件: 再 grid 読みで両 parser が [FLANK-FALLBACK] を loud 表示すること。** note: field-vs-npz 較正 leg は消滅 (drift 源 = locked file の将来編集のみ、file locked + 定義 pin で実害なし)。
