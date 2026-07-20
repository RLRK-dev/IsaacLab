# c61-c64 evidence readback — SKILL 分解能材料 v1.4-v1.7 + 棚卸 v1.3

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`, claude)。**Verdict 発行時刻:** 2026-07-21 00:24 JST。
**Requester:** p4 RS-TECH-LEAD (dispatch 2026-07-21 00:20 JST)。
**継承経緯:** 本件は `w2:pN` (T-ROOT-OPS-SUPERVISOR-CODEX) 宛に出された未応答 leg。pN が credit 上限
到達 (〜2026-07-25 12:24) で応答不能となり、**Rs 指示により pY へ引継ぎ** (Rs 逐語 = 「君は
T-ROOT-OPS-SUPERVISOR」「T-ROOT-OPS-SUPERVISOR-CODEX を引き継いで」)。pN 最終 verdict = c60 PASS
(2026-07-20 23:49:45)。**本 readback = pY による初回 verdict。**

## ⭐ VERDICT: **PASS (4/4)** — records-only・結論不変・census 35 不変

⛔ 本 verdict が閉じるのは **c61-c64 の records 整合性のみ**。設計判断・所管裁定・freeze・impl/training は
一切含まない (OPS-SUP は設計 frame の position を取らない — LEDGER:20-23)。

## 対象

| 版 | commit | 内容 |
|---|---|---|
| v1.4 | c61 `03578b7b07` | Rs 逐語 全文補完 + DDR#32 記録 + §0 撤回済み表現の除去 + 棚卸表に pX 行追加 |
| v1.5 | c62 `972fc2e60c` | §2-1 訂正 = D0 draft field 名を現行として引いていた誤り (3 項 loud-discard) |
| v1.6 | c63 `dd80ca1576` | 同型 D0 型名の doc 全体 sweep |
| v1.7 | c64 `b2bd31b8ec` | 版表の自己整合 + §8 churn 自己観察 |

**在中 branch = `probe/pd1-arm-pd` のみ** (`git branch -a --contains` で実測)。
`rlrk/optE-s2-substrate-swap` = 0 / `main` = 0 ⇒ **p4 の cross-lane 引用規律 (path + sha256 + commit 併記) は
妥当かつ必須**。本 readback も同規律で書く。

## 検証レグ

### L1. 完成物 sha256 (p4 申告 vs 独立再計算) — ✅PASS

| file | commit | 申告 | 実測 | |
|---|---|---|---|---|
| `SKILL_GRANULARITY_MATERIALS_RSTECHLEAD_20260720.md` | `b2bd31b8ec` | `844835d07ac37ee7…` | `844835d07ac37ee72cc86a2d19f414a159a114b5c76ceb90e64663763c099c85` | MATCH |
| `SKILL_ADMISSIBILITY_INVENTORY_RSTECHLEAD_20260720.md` | `03578b7b07` | `9c826135f3ac3153…` | `9c826135f3ac3153a37f11101c9e8688a1c9b1fde93cec86bd8f317285b20dc6` | MATCH |

### L2. 版表の自己整合 (c64 の主張) — ✅PASS **7/7**

版表が各版に付した sha256 を **全行 独立再計算**。系譜表が単なる申告でなく実際に blob を pin していることを確認。

| 版 | commit | 申告 prefix | 実測 prefix | |
|---|---|---|---|---|
| v1.0 | `0e1589c931` | `dcc28085547626ae` | `dcc28085547626ae` | MATCH |
| v1.1 | `334b6dc1bf` | `87589649dac2800f` | `87589649dac2800f` | MATCH |
| v1.2 | `19e8f8b1a9` | `d939ad136a88f01a` | `d939ad136a88f01a` | MATCH |
| v1.3 | `bf160e4a46` | `a8d3bc5162befb02` | `a8d3bc5162befb02` | MATCH |
| v1.4 | `03578b7b07` | `ada624047af6bb3f` | `ada624047af6bb3f` | MATCH |
| v1.5 | `972fc2e60c` | `1292d40fa8d2c568` | `1292d40fa8d2c568` | MATCH |
| v1.6 | `dd80ca1576` | `85bae9783d1576b4` | `85bae9783d1576b4` | MATCH |

⇒ c64 が直したという「版表の自己不整合」は**実際に解消されている**。

### L3. records-only / census 35 — ✅PASS

`git diff --name-only 03578b7b07^ b2bd31b8ec` = **2 path のみ**、いずれも
`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/` 配下の `.md`。**code 0 file**。
⇒ **census 35 不変は records-only から構造的に従う** (guard 再走は不要。⚠ 本 leg は guard を再実行して
いない — 「code が 0 file ゆえ census を動かし得ない」という導出であり、再測定ではない)。

### L4. c61 = Rs 逐語 (custody 実読) — ✅PASS **完全一致**

custody `WMSO_RS_SKILL_OWNERSHIP_RULING_20260720.md` @ `3cecb0d246` を **pY が独立に実読**:

- `:9` 逐語 = 「**SKILLについてはpX:SKILL-DESIGNが決めることとなった。整合性を持つように**」
  ⇒ c61 が §5-0 に補完した全文と **完全一致**。v1.3 まで欠けていた「整合性を持つように」の実在を確認。
- `:11` = 「**Rs の発話はこの 1 文のみ。** 範囲を列挙した文は存在しない。以下 §3 は**私の解釈であり Rs の
  言葉ではない**。」
  ⇒ c61 が「同 record §3 の scope 分割は裁定として扱わない」と書いた characterization は **faithful**。

⭐ **p4 が relay をそのまま採らず custody を実読して補完した点は、手順として正しい**
(欠落した後半文は「整合性を持つように」= 面の整合を命じる部分であり、落ちたままなら c61-c64 の作業自体が
発注されなかった)。

### L5. c62 = frozen contracts_v2 の disposition — ✅PASS **5/5 + 行 anchor 5/5**

`WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` を実読 (branch tip blob)。
c62 §2-1 表の主張を全項照合:

| 項 | c62 の主張 | 実読結果 | 行 anchor |
|---|---|---|---|
| `duration_cost_distribution` | loud-discard (静的 prior 廃止・分布推定 = Phase D SDM 職務) | 一致 | `:423` ✅ |
| `recovery_rollback_target` | loud-discard (NHA・消費者 = 未実装 recovery 層・再導入は schema bump) | 一致 | `:425` ✅ |
| `SkillHandoffState` 実体 | loud-discard + `E_MIGRATE_RUNTIME_CONTEXT_ABSENT` | 一致 | `:421` ✅ |
| `safe_interruption_checkpoints` | 存続・改名 → `checkpoint_specs` | 一致 | `:420` ✅ |
| `accepted_incoming_handoff_set` | 存続・改名 → `accepted_handoff` (producer/schema/version 正規化) | 一致 | `:422` ✅ |

⇒ **行 anchor も 5/5 exact** (charter §9.7.5 の「anchor は drift しやすい」警告に対し、本時点では drift なし)。

### L6. c63 = D0 専用型名の sweep — ✅PASS (**substance**)

⚠ **raw grep は 0 でない** — 最終 blob に旧名が残存する:
`SkillLifecycleContract` ×2 / `SkillActionKey` ×1 / `ExecutableIdentity` ×1 / `accepted_incoming_handoff_set` ×2。

**しかし全 occurrence が「訂正した対象を名指す」文脈であり、現行としての使用は 0**:

| 行 | 文脈 | 判定 |
|---|---|---|
| `:14` | 版表 v1.6 行 = c63 が何を掃いたかの記録 | 訂正の記録 |
| `:76` | §2-1 訂正表の**左列** = 「v1.0-v1.4 がこう書いていた」欄 | 訂正の記録 (設計上必須) |
| `:117` | 「⚠v1.5 まで D0 名 `SkillLifecycleContract` で書いていた」注記 | 訂正の記録 |
| `:121` | 「⚠v1.4 まで D0 名 `accepted_incoming_handoff_set` で書いていた」注記 | 訂正の記録 |

⇒ **現行 field/型として D0 名を引いている箇所 = 0**。`SkillDefinition` (frozen 名) = 5 箇所で正しく使用。
**sweep 主張は substance で TRUE**。

## ⚠ 精度 nit 1 件 (defect ではない・verdict を下げない)

c63 の版表 v1.6 行は「`SkillActionKey` / `ExecutableIdentity` は**本 doc に 0**」と書くが、最終 blob には
**各 1 occurrence 実在**する。その 1 件が **「0 だ」と主張している当の文それ自身** (`:14`) である
(自己言及)。主張は評価時点では真であり、実害なし。

⭐ **surface する理由 = 将来の機械 grep 対策**。D0 型名を grep する guard / 後続者が本 doc を走査すると
**hit する**。「hit = regression」と読むと誤判定になる。本 nit を読めば self-reference と判別できる。
(同型の教訓 = memory `feedback-a-gate-validated-under-the-bug-is-validated-by-the-bug-2026-07-15`
の裏面 — 機械 check は「訂正の記録」と「未訂正の残存」を区別しない。)

## ⭐ 手順面の所見 (p4 §8 自己観察への OPS-SUP 側 corroboration)

p4 は §8 で「外から指摘された箇所だけ直して bank する」を 4 連続で繰り返した手順欠陥を自己記録し、
規律「指摘を受けたら bank 前に同じクラスを doc 全体へ機械 sweep する」を立てた。

**evidence 側から見て この自己記録は正確**: v1.4→v1.7 の 4 版はいずれも前版が取り逃した同型欠陥を直して
おり、**v1.6 で初めて `grep -c` を全 D0 型名に回して 0 を確認**という経緯も diff と整合する。
⇒ **§8 は事実に接地している** (自己観察が実際の commit 系列と一致することを独立確認した)。

## 非主張 (本 verdict が閉じないもの)

- ⛔ **DDR#32 / #33 / #31 の設計・所管裁定** — いずれも Rs 専権 or 未裁定。本 readback は
  **「p4 がそれらを裁定していないこと」を確認しただけ**で、内容の当否には触れない。
- ⛔ **分解能そのもの** — 決定者 = `pX:SKILL-DESIGN` (Rs 裁定)。本 doc は材料であり提案でない、という
  p4 の自己限定が守られていることを確認した (「私は選ばない」「どちらにも裁定しない」の記述と diff が整合)。
- ⛔ **freeze / impl / training / closed-loop authority** — すべて CLOSED 継続。
- ⛔ **census 35 の再測定** — L3 のとおり導出であり測定ではない。

---
**readback 実施 = 2026-07-21 00:24 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
