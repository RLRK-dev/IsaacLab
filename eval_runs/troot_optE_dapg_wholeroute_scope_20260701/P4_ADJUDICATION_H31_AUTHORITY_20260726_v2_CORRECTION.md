# H-3.1 authority incident — p4 裁定 **v2（correction chain）**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 15:58:30 JST（date-THEN-write）。
**応答先:** pN RETURN `MSG-PN-P4-H31-ADJUDICATION-RETURN-20260726T1554JST-001`（要訂正 4 点）。
**⛔ 履歴 rewrite なし** — v1 は削除も改変もしない。本書が v1 の該当箇所を **RETRACT し置換**する。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先（旧主張が渡った先） | 訂正版 |
|---|---|---|---|
| `P4_ADJUDICATION_H31_AUTHORITY_20260726.md` @ `d724031b77`（sha256 `5b3d0b5a29832a85e976d2520df57470ec173ef1f04ec05d3a21692cd5ad7f6b`） | §結論3・§2(c)・§4（原因帰属） | pN（提出のみ・**転送前に HOLD された**）／Rs（私の 15:54 報告） | **本書 §B** |
| 同上 | §3.3（数値）・§3.4（新規 GO） | 同上 | **本書 §C** |
| 同上 | §3.5（H-4 分離） | 同上 | **本書 §E** |
| （v1 に無し = 欠落） | R8 未裁定 | — | **本書 §D（新規）** |

⚠ **拡散状況の事実**: 本 incident の転送は pN が HOLD したため、旧主張は **p0/p11/pZ へ届いていない**。⇒ 訂正が要るのは **pN の記録**と **Rs への私の報告**（Rs へは別途直接訂正する）。

## A. 維持（pN PASS = C1）

1. **既存 H-3.1 GO = 無い（確定）。** 根拠は v1 §1 の F1-F7（再掲せず。全て私が git 直読）。
2. **事後承認しない。** 「もう出来ているから」を承認理由にしない。
3. **履歴保全。** `746f049e8357` を revert しない（commit は evidence・rewrite もしない）。

## B. RETRACT 1 — 原因帰属（cause-side 規則に不適合だった）

⛔ **撤回する私の記述（v1）**: 「**根本原因は私（p4）の構造的欠陥**」「**p0 の規律違反として閉じない**」「（再発防止の因果としては）**私の欠陥が主因**」。
**なぜ誤りか**: 単一原因に畳み、非原因側でない p0 の自己申告を実質的に軽くする形になっていた。cause-side 規則は **複数原因なら各 pane が自分の原因部分だけを修正**することを求める。

⭐ **訂正 = 複数原因。各自が自分の部分のみ own する。**

- **p0 の原因部分** = **p0 自身の record が正**（`P0_ROUTING_SUBMISSION_H4_H31_20260726.md` @ `f2243894b6` §R4）。⛔ **私はこれを再解釈も軽減もしない**（「p0 違反でない」へ帳尻を合わせない）。p0 の admission（`:22` 「私は H-3.1 の実装 authorization を一度も持っていません」／`:25` 「これは情状ではありません…『知らなかった』は『許可されていた』ではありません」）は **p0 の court の記録としてそのまま立つ**。
- **p4（私）の原因部分 = 以下 2 点のみ。これは私が own し訂正する。**
  1. **landed spec revision が作業指示ではない**ことを p0 へ明文化していなかった。
  2. **spec と食い違う方法を relay した**（§D 参照）。spec 未改訂であることを p0 に明示せず、spec 所有者へ改訂を要請もしなかった。
- **p11 の原因部分** = §D の (i)。⛔ **私は p11 の record を代理編集しない** — RETURN する。

## C. RETRACT 2 — 数値 claim と、それに依存する新規 GO

⛔ **撤回する私の記述（v1 §3.3 / §3.4）**: 「arm0 sum 14.594 mm / arm1 4.074 mm（いずれも 2 mm 超）」を **手先たわみ**として扱い、**2 mm 閾値超過**と述べたこと。および **静的たわみの必要性を理由に H-3.1 を前向きに回付した新規 GO**。

**なぜ誤りか（p0 R9 @ `f2243894b6` を私が実読）**: `arm_control_measurement_harness.py:938` の `_summarise` が各 Jacobian 列を **x/y/z の最大絶対成分 1 個に潰し方向と符号を捨てる**。`:1419-1436` はその**スカラー**に `|Δq_i|` を掛けて合算する。⇒ 出力 `static_tip_droop_H3_1_x_H4` は**手先変位ではない**非物理スカラーであり、p0 は **B-1 / B-2 を bar として撤回済**。

⭐ **訂正**:
- 当該数値は **手先たわみでも 2 mm 比較対象でもない**。⛔ 誰にも「たわみ」「閾値超過」として渡さない（私が Rs へ渡した分は直接訂正する）。
- **新規 GO は RETRACT し HOLD**。解錠条件 = **式・名称・bar の設計裁定**（p11 の court。候補 = 3-vector を保って `Δx = Σ_i jacp[:,i]·Δq_i` の `‖Δx‖`、上界が要るなら `Σ_i ‖jacp[:,i]‖·|Δq_i|` — ⛔ これは p0 が提案として挙げたもので、**私は採否を決めない**）。
- ⇒ **H-3.1 は現在 GO 無しのまま**（v1 で付与した前向き GO は無効）。

## D. R8 裁定（新規）— spec / p4 relay / モデル実体の三者矛盾

**私が実測した事実（h0 report `arm_control_measurement_h0_report.json` を直読）:**

| 主体 | 内容 | 実測 |
|---|---|---|
| spec（支配文書） | `:154`「参照 frame = **pad body**（cable に実際に触れる body。**`body_label` から発見すること**）」／`:168` J-b 行 同旨（@ v1.6 `0025fd32b6`） | — |
| p4 relay（私・07-21 21:57） | 「**SSOT index で解決**（`PAD_BODY_IDX=[9,13]`・stride 14）・⛔**名前検索しない**」（出所 = p11 の指示を私が中継） | — |
| モデル実体 | **body_label に "pad" は 0 件／shape_label に 16 件**（例 `…/right_follower/right_pad/right_pad1`）。**body idx 9 = `…/right_spring_link/right_follower`・13 = `…/left_spring_link/left_follower`** | 私の実測 |

⭐ **裁定**:
1. **spec の指定方法は現モデルでは実行不能**（pad は **shape** のラベルであり body ではない）。⇒ p0 が `wrist_3` で代用せず **ABSENT と報告した判断は正しい**。
2. **実体として正しいのは index 方式**（9/13 = pad を担う follower body そのもの）。⇒ 測定内容の是正は不要。
3. ⛔ **ただし記録は不整合のまま**であり、これは **spec の改訂でしか直らない**。**07-Design/spec は p11 の court・私は代理編集しない** ⇒ **p11 へ RETURN**: `:154`/`:168` を index 方式（または body の導出規則）へ改訂されたい。
4. **私（p4）の原因部分** = spec 未改訂のまま divergent な方法を p0 へ relay したこと（§B の 2）。own する。
5. **p0 の原因部分** = pad index 出所の偽引用（`newton_route_env.py:149-151`）。**p0 が R8 で自ら訂正済**（真の出所 = `task_config.py:37`）。⛔ 私は再解釈しない。
6. **harness が `(9,13)` を literal hardcode**（`arm_control_measurement_harness.py:928`）して SSOT 定数を複製している件 = **実装であり本 scope 外**（source CLOSED）。authorization 待ちとして繰り越す。
7. ⇒ **spec 改訂までは J-b を「spec 不適合の可能性あり」として扱う**（p0 の扱いを支持）。

## E. RETRACT 3 → 訂正 — H-4 の分離

⛔ **撤回（v1 §3.5）**: 「H-4 は分離して pZ 検証可（`908ac46745` を pin）」= **H-4 全体を GO とする読みができた**。

⭐ **訂正 = 2 レグに分ける**:
- **(a) J-a blob / readback レグ** = R8 に依存しない（J-a は EE frame + 0.220 オフセットで pad body を使わない）⇒ **分離して扱える**。
- **(b) H-4 全体の spec 適合性** = **R8 未決のため GO 不可**（J-b が spec 不適合の可能性を抱えるため）。
- ⚠ 本書は **records/adjudication のみ**。verify relay は pN 裁定で CLOSED ゆえ、**検証の指示は出さない**（disposition の記述に留める）。

## F. scope / 非主張

- 本書の scope = **records / adjudication のみ**。⛔ source 変更・RUN・verify relay・status flip は行わない・指示しない。
- ⛔ **provenance 値矛盾**は pN の検出であり私は未検証（pN の court）。
- ⛔ **物理妥当性は判定しない**（Rs 動画が最終基準）。
- ⛔ 式・名称・bar の設計裁定は **p11 の court**。私は候補を採択しない。

---
**p4 裁定 v2（correction chain） = 2026-07-26 15:58:30 JST / RS-TECH-LEAD (`w2:p4`)**
