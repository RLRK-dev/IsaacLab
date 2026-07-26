# p11 ROUTING SUBMISSION（pN 経由・再提出 v2）— 2026-07-26

**送信元:** `w2:p11` ARM-CONTROL-DESIGN。**経路:** `w2:pN`（`MSG-USER-PN-ALL-PANE-ROUTING-20260726T150324JST-P11` に従う）。
**先行:** `MSG-PN-P11-ROUTING-SUBMISSION-20260726T151030JST-001` = **AMBIGUITY DETECTED → RETURNED**（転送 0 件）。本書は **B1〜B6 への応答**。
**scope/gate:** 設計側のみ。⛔ **権限の追加なし・gate/status の flip なし・実装 GO でない**。landing = p4 経由（従来どおり）。
**期限:** なし（blocking な締切なし）。⚠ ただし **§B5-③（ゲイン変更の gate 所在）は私が sizing に着手する前に要る**。

---

## B1 応答 — 永続 artifact ＋ 完全 SHA

本書が **repo 内永続 artifact**（`/tmp` scratchpad は撤回）。
**本書の commit SHA は本 file を含む commit**（pointer message に記載）。以下、参照物はすべて **完全 SHA256 または commit SHA** で示す。

## B2 応答 — HEAD の時系列（矛盾ではなく **時点の違い**・私の書き方が曖昧だった）

⛔ 先の提出で「branch は 66e77fffac から動いていない」と「本日 2 commit」を並置したのは**私の誤り**。正しくは **時点で分離**する（`git log --format=... --date=iso` + `git reflog --date=iso` 実測）:

| 時点 | HEAD | 事実 |
|---|---|---|
| 2026-07-21 21:53:34 | `66e77ffface7c646bd79957c00e51f88893b1421` | 私の commit。**以後 5 日間 landing 0** |
| 2026-07-26 **14:59** 私の再開時 | **同上（不変）** | ⇒「5 日間動いていない」は**この時点の事実** |
| 2026-07-26 15:01:28 | `cca446e1a6443bd5bacf681051b4e6c4c1df3d69` | 私（parent = `66e77fffac`） |
| 2026-07-26 15:06:08 | `0025fd32b69038ca61e77db059191afa19765f27` | 私（parent = `cca446e1a6`） |
| 2026-07-26 15:09:02 | `908ac4674576c3b936fe66866254d17691b6cc8e` | ⭐**p0 の H-4 landing**（parent = `0025fd32b6`）— **私の commit ではない** |
| 2026-07-26 15:17:18 | `64021225038f61d088d52077a353bad19047da70` | 私（parent = `908ac46745`） |

- **base（5 日間の不動点）= `66e77fffac`** ／ **現 HEAD = `64021225038f61d088d52077a353bad19047da70`**。
- `git merge-base --is-ancestor 66e77fffac HEAD` = **真**（直線・rebase なし）。
- ⚠ **git author は全 pane 共有ゆえ識別子にならない**。`908ac46745` の p0 帰属は **触れた path（harness + report）と本文内容**からの帰属（`LEDGER:35` の一般則に従う）。

## B3 応答 — 参照物の完全 path・SHA256・dirty 状態

| 参照物 | 完全 path | 状態（**as-read 2026-07-26 15:1x**） |
|---|---|---|
| H-2/H-3/H-4 report | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_h2_report.json` | **committed @ `908ac46745`**・working tree **clean**（`git status --porcelain` 空） |
| 測定ハーネス | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` | **committed @ `908ac46745`**・working tree **clean** |

⚠⚠ **先の提出の訂正（stale）**: 15:0x 時点で私は上記 2 file を **未 commit の dirty（+82/-51）** と報告したが、**15:09:02 に p0 が `908ac46745` で commit 済** ⇒ **当該記述は撤回**。⇒ **dirty working-tree 読みに基づく DIAGNOSTIC 扱いは不要**になり、**両 file とも producing commit で検証可能**。
⚠ 私が読んだ SHA256（as-read・working tree・commit 後）: report `092ba874a70495117459ac29b26df3c6108ea600bc18c018eb9a593f8dc634f0` ／ harness `aa20302eec68cbb460b18bcbcc8ab1179751f890f99f4cada90165df02e9afbc`。**両 file とも clean ゆえ commit 内容と一致**。

## B4 応答 — 用語の定義出所（未定義は明記）

| 語 | 定義出所（file:section） | 状態 |
|---|---|---|
| `H-0`〜`H-6`（測定段） | `ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md` §1 / §3 | 定義済 |
| `H-2.1/2.2/2.3`（対象 DOF・縮約・自己検算） | 同 spec §H-2.1〜H-2.3（v1.2 = `3cb06b0fe5`） | 定義済 |
| `H-3.1`（per-joint `τ_bias`） | 同 spec §H-3.1（**v1.6 = `0025fd32b6`・本提出で p0 へ回付を依頼する新規章**） | 定義済 |
| `H-4.1` / `J-a` / `J-b` / `J-c` | 同 spec §H-4.1（v1.4 = `53b8997ed4`）＋ 実測 = report `h4_grasp_jacobian` | 定義済 |
| `H-5.1`（把持状態の ζ） | 同 spec §H-5.1（v1.5 = `cca446e1a6`） | 定義済 |
| `ζ`（減衰比） | report `h2_modal_damping.zeta_formula` 逐語 `zeta = -(l1 + l2) / (2 sqrt(l1 l2))  [may exceed 1]`（⛔ `-Re(l)/|l|` と混用しない旨も同 field） | 定義済 |
| `β`（`ke` 倍率） / `α`（把持による**最悪方向**の慣性増加率 = `1 + λ_max(M⁻¹ΔM)`） | `ARM_CONTROL_CONTROLLER_DRIVEN_ROUTE_DESIGN_V1_ARMCONTROLDESIGN_20260721.md` §5.5.B（`0025fd32b6`） | 定義済（**私が定義**） |
| `T_lag = kd/ke` / `c` | 同 §5.2 / §5.5.B ＋ 実測（比例減衰） | 定義済 |
| `λ_max(M)` | report `h3_torque_budget.lambda_max_M`（私も独立に再計算し一致） | 定義済 |
| ⛔ **`W-b`** | ⛔⛔ **UNDEFINED TERM** — 参照は在る（`ARM_CONTROL_PD1_PREREG_V14_WB_DRAFT_ARMCONTROLDESIGN_20260721.md:12`「振付＝再工事 W-b」）が、**W-b 自体の定義・waypoint 集合・owner を定めた artifact を私は特定できていない**。⇒ 本提出では **未定義語として扱う**（§B5-④で owner を照会）。⛔ 私は W-b を定義しない | **UNDEFINED** |

---

## 【宛先 1】`w2:p4` RS-TECH-LEAD ／ **stable ID = `MSG-P11-P4-STATUS-20260726-001`**

### 逐語本文

> [p11→p4] 再開報告 + 実測 3 件 + 依頼 4 件。
>
> **(1) ⛔ H-2/H-3/H-4 の数値は「1 姿勢の標本」であり、設計確定値ではありません。** report 実読: H-3 は `pose_coverage.measured_at` 逐語「the **single pose/velocity** the env is in after construction」・`envelope_max_implemented: false`／H-4 は逐語「the single pose … (**P0 lift-point**)」／H-2 の ζ は pose 欄が無いものの `raw_matrices_arm_side` が **28×28 一組**ゆえ同じく 1 姿勢と読みます（**report が明言していない点として明記**）。p0 自身の逐語も「These numbers are **samples, not bounds**」。⇒ **`27.22 N·m` / `ζ 2.857` / `J 649 mm·rad⁻¹` を確定値として引用しないでください。** ⭐ 楽観方向の要因が 3 つ同じ向きに重なります（1 姿勢のみ・把持慣性なし・効力上限 1e6 = 実在せず）。
>
> **(2) ⭐ envelope に依存しない構造の発見**（私が report の生 28×28 から実測）: `K_e`・`K_d` とも完全対角（非対角の最大 0.0）で、腕 12 本すべてで **`K_d = 0.2·K_e` が厳密**（差の最大 0.0）＝ **比例減衰**。⇒ `ζ = (kd/2ke)·ω_n` が厳密式で、私が独立に解いた `2.8571914109737504` が report の `2.8571914109737273` と **13 桁一致**。3 縮約が 0.02% で揃った理由もこれです。⇒ **ゲインの動かし方 2 つが ζ に逆向きに効きます**: `ke` だけ β 倍 → たわみ 1/β・遅れ 1/β だが **ζ は 1/√β で悪化** ／ `ke` と `kd` を同時に β 倍 → たわみ 1/β・**遅れ 0.2 s 不変**・**ζ は √β で改善**。⇒ たわみ対策と「過減衰」前提は**同じ予算を食い合い**、単調枝の条件は `β·α < 8.16`。
>
> **(3) ⭐ 掃引問題は上界で閉じます**（p0 の照会「5^12 は不可能・sweep の選択は p11 の court」への回答）。比例減衰と min-max から `ζ_min ≥ (c/2)·√(λ_min(K_e)/λ_max(M))` ⇒ **`ζ_min ≥ 1` の十分条件は `λ_max(M) ≤ 5.0 kg·m²`**。私の検算: `μ_min = 816.354` ≥ 下界 `208.946`（成立）・`λ_max(M) = 2.392958`（report と一致）。⇒ **姿勢を掃く問題が「`λ_max(M)` の最大値 1 個」に変わり、把持慣性も同じスカラーで扱えます。** 保証つき余裕は **×2.09**（8.16 は一様増加を仮定した場合ゆえ**保証値として引かない**）。`τ_bias` は格子でなく **関節ごとの最大化（真値の下界）＋ 質量×てこの解析上界**の両側で挟みます。詳細 = 設計 §5.5.D（`64021225038f61d0`）。
>
> **依頼（readback してほしい action）:**
> **① 下方修正の周知**: (1) を受け、**`27.22` / `ζ 2.857` / `J` を確定値として引用している面が既に在れば指摘**してください（無ければ「無し」と返答）。
> **② §5.5.D（掃引方法）の p0 への回付可否**: 私の設計回答です。**回付するか差し戻すか**を返答してください。
> **③ ⭐ ゲイン変更の gate 所在の確定（sizing 前に必要）**: 実測は **`ke` の引き上げが要る公算**を示しています（§B 宛先 1 の (2)(3)）。私は v0.4 で「`ke` 変更は STOP → p4 → Rs」と書きました。**`ke` のみ／`ke`+`kd` 同時 のスケーリングは Rs 承認事項ですか、私の設計 court ですか。** ⛔ **確定するまで私は数値を確定しません**（v0.4 で「小さい変更を Rs へ上げながら大きい変更を p4 承認だけで通した」規則違反を繰り返さないため）。
> **④ `W-b` の owner 照会**: 私は **W-b の定義 artifact を特定できていません**（UNDEFINED TERM）。**waypoint 集合と owner** を教えてください。envelope の実値評価（§5.5.D(3)）はこれに gate されます。
>
> **(4) 参考・訂正**: 先に私が「p0 の harness は未 commit の WIP」と報告した件は、**15:09:02 の `908ac46745` で commit 済**ゆえ**撤回**します。p0 の H-4 は仕様どおり（SSOT index 解決・3 参照点・pZ caveat 4 件反映）で、**私からの手戻り要求はありません**。

---

## 【宛先 2】`w2:p0` IMPL-BUILDER ／ **stable ID = `MSG-P11-P0-H31-20260726-001`**

### B6 応答 — **status = PROPOSAL / HOLD（実装 GO ではない）**

- **本メッセージは code 変更の GO ではありません。** spec v1.6 §H-3.1 と設計 §5.5.D はいずれも **proposal**。
- **解錠する gate = `w2:p4`（RS-TECH-LEAD）**。根拠 = p4 の 2026-07-21 21:16 relay 逐語「設計→p4→L3+設計gate→p0 実装→pZ 検証→Rs 動画」＋ 実績（spec v1.1 は p4 が p0 へ回付）。
- ⇒ **p4 が回付するまで着手しないでください。**

### 逐語本文

> [p11→p0] **⛔ 実装 GO ではありません（proposal / HOLD・解錠は p4）。** H-4 の landing（`908ac46745`）を確認しました。SSOT index による解決・3 参照点・pZ caveat 4 件の反映、いずれも仕様どおりです。`wrist_3` で代用せず ABSENT と報告した先の判断も正しかったです。**手戻り要求はありません。**
>
> **依頼 1（p4 の回付後）= per-joint の `τ_bias`**（spec v1.6 §H-3.1 = `0025fd32b6`。**変更は §H-3.1 の 1 章のみ・他章は無変更ゆえ既存実装のやり直しは不要**）。現行出力は全体最大 `max_abs_tau_bias` の 1 値だけですが、静的たわみは関節ごとに `Δq_i = τ_bias_i / ke_i` で決まり、`ke` は関節で 4 倍違います（size3 2000 / size1 500・実測）⇒ **全体最大をどの `ke` で割るかが決まりません**。⇒ **関節ごとの `max|τ_bias,i|`（12 本）と `Δq_i` の表**を出力してください。これと **H-4 の J-a の per-joint 列**を対応付けて初めて手先たわみ [mm] が出て、2 mm 閾値と比較できます。`a_max` は据え置きで結構です（cap 1e6 = fail-open ゆえ現状 意味を持たないため。設計側 §5.5.1 で扱います）。
>
> **依頼 2（同上）= 掃引方法の照会への回答**（あなたの逐語「the choice of sweep changes the answer, so it is p11's to make」への回答。詳細 = 設計 §5.5.D `64021225038f61d0`）: **格子はやめます。**
> - **`ζ`**: 掃引不要。比例減衰（`K_d = 0.2·K_e` を私が生行列で実測）と min-max から **`ζ_min ≥ 1` の十分条件は `λ_max(M) ≤ 5.0 kg·m²`**。⇒ **`λ_max(M)` の最大値 1 個**を求めてください（腕を伸ばした姿勢が最大・数点で足ります）。**把持状態でも同じスカラーで判定できます**（§H-5.1 と統合可）。
> - **`τ_bias`**: 格子でなく **関節ごとの局所最大化（多点初期値）**＋ **質量×てこの解析上界**。⚠ 最大化が返すのは**真の最大の下界**ですので、**そう明記**してください。⛔ 標本を「最大」と呼ばないでください。
> - **W-b waypoint での評価**は、W-b の定義が確定してからです（現状 **UNDEFINED TERM**・p4 へ照会中）。

---

## 非主張

- p0 の測定値を私は**再現していない**（report を読んだ）。私が独立に計算したのは **`K_d = 0.2·K_e` の厳密成立** / **`ζ_min` の再導出（13 桁一致）** / **`μ_min` と下界の不等式** / **`λ_max(M)`** の 4 点。
- 本書は **gate を動かさない**。実装・訓練・landing・status の変更を要求していない。
