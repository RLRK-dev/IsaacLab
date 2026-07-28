# P18 T43 BLIND VIDEO READ — 2026-07-29

## Desk header (w2:p18 T-ROOT-OPS-SUPERVISOR)

- **Instrument**: video-analyst subagent (§453(c) instrument switch; pane court w2:pC unstaffed). Blind protocol: video path + minimal scene (L orange / R purple, claws blue-top/red-bottom, Y-yoke column, cable + clips; "the video may be short — report measured length first") + the five standing questions. NO numerics, NO step names, NO expected outcomes. Strip disclosed.
- **Status**: evidence READING, not a verdict. t43 verdict = p4 after both legs (pB leg = PB_T43_FIVE_CLAIMS… @ 38120c0d1d, §478). Formal video physical-validity authority = Rs.
- Video: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/t43_live_20260729.mp4` (sha256 `7e08ababe8f09a2e9640929bcd708e7c2ca4369bd42bfac3883965f17d482fdc`, desk-verified §476(a); committed @ `99d45e2114`).
- **Desk framing note (not the instrument's)**: the 2.200 s length is the RUN'S OWN stall-terminal (STEP2's 2.2 s allotment, trace :52; the run raised at that point by design, §475(b)C) — the instrument's "request a longer render" reads, at this desk, as "the run itself ended here"; the mid-motion cutoff is the terminal, not a render defect. Judgment = p4.

---

## Instrument report (verbatim, condensed tables preserved)

- 実測メタ: 2.200 s・30 fps・**66 frame 全抽出（欠損 0）**・4800×900 3 パネル（P1 遠景/P2 接写/P3 真上）・焼き込み文字なし ⇒ 全所見 OBSERVED。
- 総括: **2.17 秒間に離散イベント（到達・把持・持ち上げ・搬送）は一度も起きない。** 両腕とも低速の単調ドリフトのみ（往復・振動・停止切替なし）。
- 各腕: 橙（左）= ケーブル自由端の斜め上・数 cm 手前の空中で、わずかな下降 + 爪の傾き（10–15° 程度・推測）のみ・爪は閉じ気味で空・開閉変化なし・**到達フェーズに入れていない**。紫（右）= ケーブル上・クリップ横の正しい場所に居るが、**爪は全開のまま固定**・下爪を机面付近に置いて手首が回り続ける・把持姿勢に収束しない。
- 接触: 紫下爪 ↔ ケーブル = 投影重なりのみ・**ケーブルは全 66 frame で 1 px も動かず有意な力なし**（幾何接触の有無は確定不能）。⚠ 未解決フラグ 2 件（視点不足で原理的に不能）: ①橙の肘/上腕 ↔ 紫リンクの隣接（隙間視認できず・実接触未確定・「投影だから無罪」と断定しない）②紫下爪 ↔ ケーブル実接触。腕 ↔ 机/支柱/クリップ = 接触なし。クリップ 3 個は全 frame 不動（f43 以降の右クリップ非表示は紫前腕の遮蔽と他パネルで確認）。
- 把持: **不成立（FAILED）** — クランプは一度も観測されず（紫 = 爪間隔がケーブル径の約 10 倍のまま不変・ケーブルは爪の間でなく下爪の脇/下。橙 = 空・接近もしない）。紫グリッパの上下爪が著しく非対称な姿勢の注記あり。
- 物理妥当性: **PLAUSIBLE** — めり込み/貫通/瞬間移動/振動発散/NaN/消失いずれも観測なし（全 66 frame + 末尾 8 連続で確認）。「PASS は物理妥当性のみの意味・タスク成功を意味しない」と明記。動作継続中の f66 で終了（レンダ破綻ではない）。
- 難航: **左（橙）が課題達成から遠い**（どの対象とも係合せず）。紫も失敗だが位相は先（正しい場所には居る）。
- セルフチェック: blind 遵守・数値ログ不参照・全 66 frame 抽出・遮蔽と消失の区別・未解決は打ち消さずフラグ残置。
