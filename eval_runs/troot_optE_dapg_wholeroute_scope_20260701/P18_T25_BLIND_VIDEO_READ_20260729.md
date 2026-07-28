# P18 T25 BLIND VIDEO READ — 2026-07-29

## Desk header (w2:p18 T-ROOT-OPS-SUPERVISOR)

- **Instrument**: video-analyst subagent (§453(c) instrument switch; the pane court w2:pC is unstaffed). Blind protocol: given ONLY the video path + minimal scene description (two same-model arms on a column structure, cable + clips on a table; color coding possibly absent — attribute L/R carefully with stated confidence) + the five standing questions. NO numerics, NO step names, NO expected outcomes. Strip disclosed.
- **Status**: evidence READING, not a verdict. t25 verdict = p4 after both legs (pB t25 reads banked §§ (-508/-509/-510 era); this leg = the video side). Formal video physical-validity authority = Rs.
- Video: `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/p4_ur15_sim_20260727/t25_live_20260728.mp4` (sha256 `95d4544dc972d2070077ccb789d98bed601becd421cd67a1b51ff6ede10c3181`, desk-measured §454(a)).
- ⚠ Attribution caveat (instrument's own): no arm coloring in this run; L/R assigned by BEHAVIOURAL markers (ARM-C = cable-holder, screen-left in the front view; ARM-I = idle side, screen-right), overhead azimuth unknown ⇒ label flip possible (confidence medium; marker-based identity high).

---

## Instrument report (verbatim)

視覚のみ（数値ログ未参照）で解析しました。

- 実測メタ: 4800×900 / 30fps / 31.833 s / 3 面合成（P1 固定遠景・P2 追従近接・P3 固定俯瞰）。抽出 53 時点（要所 0.1 s 刻み）。

### タイムライン（要約）
| 時刻 [s] | ARM-C（ケーブル担当） | ARM-I（遊休側） |
|---|---|---|
| 0–2.5 | 机中央上で静止・開。赤パッドがケーブル線上に接している可能性 | 隣接して静止・開 |
| 2.5–5.0 | 手首姿勢変更（小） | 大旋回で机外へ退避 |
| 5.0–22.5 | ほぼ完全静止（机上を占位） | **机外で静止 17.5 s（全長の 55%）**。途中 **11.0–12.0 s に空振り close**（指間が空のまま閉じる）。以後も閉じた空のまま |
| 22.5–27 | **23.5–27 でケーブル端をパッド間に挟持 = 把持成立**（俯瞰拡大で赤/青パッド間からケーブルが出る） | 22.5–23.5 机上へ復帰 → 緑クリップ周辺を移動・開 |
| 28–31.0 | 安定保持（0.1 s 刻みでも不変） | 開いた指で緑クリップを跨ぐ（持ち上げ 0 回）。前腕端キャップが机面に極接近（未確定） |
| 31.0–31.7 | 保持継続 | 31.2 頃ケーブルを指間に跨ぐ（閉じ切りは動画終了で未確認） |

終端: ARM-C がケーブルを保持・緑クリップ 2 個は未装着のまま机上・ケーブルはペグ上に滑らかな S 字/アーチ。

### 所見（要点）
- **接触はすべて「手（指先パッド）」由来**。前腕・肘・上腕の衝突は観測なし（唯一 28 s 付近の前腕端キャップ↔机面は極接近・未確定）。**支柱との接触なし**（重なりは手前遮蔽・確信度 中〜高）。腕どうしの衝突・貫通なし。
- **把持**: ARM-C = 成立（確信度 高・25 s 以降安定保持）。ARM-I = 不成立（空振り close 1 回・緑クリップ持ち上げ 0・ケーブル接触は最後の 0.5 s のみ）。
- **ケーブル**: 全区間滑らかな曲線（重力整合の垂れ・ペグ上アーチ）。発散・消失・分裂・飛散なし。
- **不自然な点**: ① ARM-I の 17.5 s 無動作（挙動の不自然・物理則違反ではない） ② 空中での空振り close ③ 閉動作が非対称に見える（片パッド静止・他方が寄る — 投影効果の可能性排除できず・確信度 中） ④⑤ めり込み系 2 件は未確定（分解能限界）。テレポート・振動発散・NaN 崩壊・消失 = 該当なし。
- **難航して見える腕 = ARM-I**（机外静止 55% + 空振り close + クリップ 0 個 + ケーブル接触 0.5 s のみ）。ARM-C は機能している側。

### 物理妥当性の総合所見
**PLAUSIBLE（物理的に妥当）** — 全時刻正常描画・連続運動・発散なし・明確な貫通なし。視覚で確定不能として残す 4 件（前腕端キャップ↔机面 / 指パッド↔ペグ / 指パッド↔机面の擦れ / 31.7 s のケーブル↔緑クリップ着座）は計算的チェック向き。**タスク遂行としては不成立寄り**（クリップ 2 個未装着・片腕が半分以上無動作）— 物理バグでなく制御/シーケンス側の問題に見える（推測）。

（セルフチェック: blind 遵守・DETECTED 不使用・機構所見と成否所見の分離・フレーム密度自己増強 5→53 時点・左右ラベルは確信度 中と明示 — instrument 自己申告のとおり）
