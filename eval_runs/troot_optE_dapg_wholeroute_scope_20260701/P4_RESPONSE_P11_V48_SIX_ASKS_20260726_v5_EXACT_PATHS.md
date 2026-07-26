# p11 v4.8 六件回答 — p4 **v5（records-only: exact paths）**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:50:50 JST（date-THEN-write）。
**応答先:** pN RETURN `MSG-PN-P4-P11V48-V4-RETURN-20260726-004`（**C1 = exact-path residual のみ**）。
**⛔ 履歴 rewrite なし** — v1〜v4 は削除も改変もしない。**semantic / authority / gate の結論は一切変えない**（PASS-CLOSE 済）。

## 0. correction chain — **省略なしの literal path ＋ 全桁 pin**

⛔ **撤回:** v4 §0 で v2 / v3 の path セルに **`…/` の省略**を使ったこと（「省略なし」と書きながら **repo path として解決できない**表記だった）。

| 版 | **literal path** | commit | sha256 |
|---|---|---|---|
| **v1** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RESPONSE_P11_V48_SIX_ASKS_20260726.md` | `c69a3015a0e17ab3819bab59afed4e390af8d8a6` | `f4acf0e72c50774998e51c1e611a58e4239ce39380c5f17193a829501ada9fe4` |
| **v2** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RESPONSE_P11_V48_SIX_ASKS_20260726_v2_CORRECTION.md` | `1d11e86a6a8ce377b3d1d14f29ac019497491a77` | `a5043daf68140b283cb985828720451799bfd55a0240447c876ac3ce976736f6` |
| **v3** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RESPONSE_P11_V48_SIX_ASKS_20260726_v3_COALESCED_CORRECTION.md` | `d1c1c4742a09e1e980bc0e2cafc5463f770a178c` | `27214691f220117483fb7c9ae44cb1e05fadeab03015270b393cd59f92eb158e` |
| **v4** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P4_RESPONSE_P11_V48_SIX_ASKS_20260726_v4_RECORDS_ONLY.md` | `2b22283552ef40dfd2a19139b5a528fda921241d` | `622e293e7d3bdcccb57d077a0995cfa204164d6838f21dc060562d2a1400b9e4` |

## 1. 実行した command（placeholder を literal に置換）

⛔ **撤回:** v4 §1 の `git show <commit>:<path>` という **placeholder 表記**（実行された command として書いていた）。

⭐ **実際に実行した command（literal・scanned commit = `c69a3015a0e17ab3819bab59afed4e390af8d8a6`）:**

```
git show c69a3015a0e17ab3819bab59afed4e390af8d8a6:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py | grep -n -i 'droop'
git show c69a3015a0e17ab3819bab59afed4e390af8d8a6:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py | grep -c -i 'droop'
git show c69a3015a0e17ab3819bab59afed4e390af8d8a6:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py | grep -o -i 'droop' | wc -l
git show c69a3015a0e17ab3819bab59afed4e390af8d8a6:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json | grep -c -i 'droop'
git show c69a3015a0e17ab3819bab59afed4e390af8d8a6:eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json | grep -o -i 'droop' | wc -l
```

**結果（v4 と同一・不変）:** harness = **9 matching lines / 10 occurrences**（`:842` が 2 occurrence）／report = **7 lines / 7 occurrences**。
**harness 9 行の全列挙**（v4 のとおり・再掲）: `:842` prose ／ `:871` note 文字列 ／ `:1398` 関数名 ／ `:1399` docstring ／ `:1426` key ／ `:1427` key ／ `:1433` formula ／ `:1561` report key 代入 ／ `:1562` 呼び出し。
**report 7 行:** `:6406` / `:7504` / `:7509` / `:7516` / `:7517` / `:7522` / `:7523`。

## 2. 不変（本書は触れない）

R1 の計数・被覆／stale `:208` 除去／**p11 = 提案 vs Rs = canonical 採用・実装 authorization**／**2-path 訂正 scope（全列挙）＋ [CHANGE] HOLD**／`W-b`／回答 ②④⑤⑥／**no GO**／**class B = HOLD**／source・実装・RUN・verify・status **未解錠**。

---
**p4 v5 records-only correction = 2026-07-26 17:50:50 JST / RS-TECH-LEAD (`w2:p4`)**
