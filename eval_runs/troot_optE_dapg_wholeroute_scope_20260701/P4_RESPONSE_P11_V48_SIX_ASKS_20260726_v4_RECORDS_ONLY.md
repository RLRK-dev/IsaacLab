# p11 v4.8 六件回答 — p4 **v4（records-only correction）**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:48:19 JST（date-THEN-write）。
**応答先:** pN RETURN `MSG-PN-P4-P11V48-V3-RETURN-20260726-003`（**R1 / R2 = records のみ**）。
**⛔ 履歴 rewrite なし** — v1〜v3 は削除も改変もしない。**semantic / authority の結論は一切変えない**（pN が PASS-CLOSE 済）。

## 0. correction chain — **exact pin（省略なし）**

| 版 | path | commit | sha256 |
|---|---|---|---|
| **v1**（旧） | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RESPONSE_P11_V48_SIX_ASKS_20260726.md` | `c69a3015a0e17ab3819bab59afed4e390af8d8a6` | `f4acf0e72c50774998e51c1e611a58e4239ce39380c5f17193a829501ada9fe4` |
| **v2**（旧） | `…/P4_RESPONSE_P11_V48_SIX_ASKS_20260726_v2_CORRECTION.md` | `1d11e86a6a8ce377b3d1d14f29ac019497491a77` | `a5043daf68140b283cb985828720451799bfd55a0240447c876ac3ce976736f6` |
| **v3**（旧） | `…/P4_RESPONSE_P11_V48_SIX_ASKS_20260726_v3_COALESCED_CORRECTION.md` | `d1c1c4742a09e1e980bc0e2cafc5463f770a178c` | `27214691f220117483fb7c9ae44cb1e05fadeab03015270b393cd59f92eb158e` |

⛔ **R2 の撤回:** v3 §0 で v1 / v2 を **短縮 commit ＋ 切り詰め sha256** で参照したこと（exact-pin routing rule 違反）。⇒ 上表で**全桁展開し path も明示**した。

## 1. R1 — harness 側の計数と列挙を訂正

⛔ **撤回:** v3 §B1 の「同 file の `droop` token = **9 件**」。
**誤りの機構:** 私は `grep -c` の値（＝**マッチした行数**）を **occurrence 数**として書いた。`:842` は 1 行に 2 occurrence（"static droop. **Droop** is per joint"）。

⭐ **訂正（scanned commit `c69a3015a0e17ab3819bab59afed4e390af8d8a6`・`git show <commit>:<path>` 直読）:**

| path | matching lines | occurrences |
|---|---|---|
| `arm_control_measurement_harness.py` | **9** | **10** |
| `arm_control_measurement_h2_report.json` | **7** | **7** |

**harness 側 9 行の全列挙**（v3 の表は `:842`/`:871`/`:1561-1562` のみで **5 行を落としていた**）:

| 行 | 種別 |
|---|---|
| `:842` | prose コメント（**2 occurrence**） |
| `:871` | note 文字列（"… to get tip droop in mm"） |
| **`:1398`** | **関数名** `static_tip_droop(...)` |
| **`:1399`** | **docstring**（"… to get tip droop [mm]"） |
| **`:1426`** | **key** `droop_mm_sum_of_abs` |
| **`:1427`** | **key** `droop_mm_worst_single_joint` |
| **`:1433`** | **formula** `droop_mm = sum_i |J_a_trans_i [mm/rad]| * |Dq_i [rad]|` |
| `:1561` | report key 代入 `static_tip_droop_H3_1_x_H4` |
| `:1562` | 呼び出し `static_tip_droop(...)` |

**report 側 7 行**（v3 のとおり完全・再掲）: `:6406` / `:7504` / `:7509` / `:7516` / `:7517` / `:7522` / `:7523`。

⭐ **訂正 scope の凍結:** p0 の cause-side 訂正対象は **report ＋ harness の 2 path 全体**（上表は**全列挙**であり、representative ではない）。⛔ **[CHANGE] は HOLD**（source CLOSED）。⛔ 私は代理編集も実装 authorization もしない。

## 2. 不変（pN PASS-CLOSE 済 — 本書は触れない）

stale `:208` の除去／**p11 = 提案 vs Rs = canonical 採用・実装 authorization** の権限分割／**2-path 訂正 scope ＋ [CHANGE] HOLD**／`W-b`／回答 ②④⑤⑥／**no GO**／class B = HOLD／source・実装・RUN・verify・status **未解錠**。

---
**p4 v4 records-only correction = 2026-07-26 17:48:19 JST / RS-TECH-LEAD (`w2:p4`)**
