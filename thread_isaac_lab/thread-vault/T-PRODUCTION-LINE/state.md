---
node_id: T-PRODUCTION-LINE
node_name: "生産ライン実現 — EV バッテリー用ジャンクションボックス + 高電圧ハーネス（⑨⑩ 除く）"
goal: "Rs 提示の生産ラインを実現する（⛔⑨電気検査 と ⑩外観検査 は除く）。対象製品 = EV バッテリー用ジャンクションボックス + 高電圧ハーネス。対象工程 = ①筐体投入 ②高電圧コネクター同時挿入 ③主配線の配索 ④分岐配線の配索 ⑤クリップ固定 ⑥ストレインリリーフ取付 ⑦カバー取付 ⑧ラッチ固定。"
goal_verification: |
  ⛔ 未定義（Rs 裁定待ち）。本 node は Rs の目標宣言を tree 上の最上位に置くものであり、acceptance 条件は未確定。
  ⛔ p6 は acceptance を発明しない（設計 = Rs 専権 / §運用4）。
  接地 = `07-Design/00-DESIGN-STATUS-LEDGER.md` 統治ブロック「2026-07-27 Rs 提示 = 最終目標」。
status: IN_PROGRESS
means: "現時点の means は 子 node `T-ROOT`（現行の中間目標）のみ。⑨⑩ を除く 8 工程の分解・担当割当は未着手（Rs 裁定待ち）。"
parent_node: null
children_nodes:
  - T-ROOT
dependencies:
  precedent: []
  blocker: []
session_history: []
created: 2026-07-27T12:26:40+09:00
last_updated: 2026-07-27T12:26:40+09:00
spec_version: LTM-1 v1.2
---

# T-PRODUCTION-LINE — 生産ライン実現（最終目標）

## 0. 起票の経緯

Rs が最終目標として本生産ラインを提示し（2026-07-27）、tree 構造について
**「最上位に、その次に現在の目標（中間目標）」** と指示（Rs 逐語）。⇒ 本 node を最上位に置き、
従来の root であった `T-ROOT`（5-clip cable routing）を **その子 = 中間目標** として接ぐ。

⚠ **node 起票は NEST §3.1 の Rs 承認 gate に該当し、Rs 承認（逐語「はい」）を得ている。**

## 1. 概念構成（⚠ 設計ではない）

双腕セルをコンベア両側へ千鳥配置・インデックス搬送・各セル = UR15 ×2 + Robotiq 2F-85 を Y 字ヨーク搭載 +
ヨーク中央に工業用ステレオカメラ 45° 下向き・搬送中に 180° 旋回して背面ストッカから次部品を取得・
クランプ完了と同時に挿入/圧入を開始・最終 2 工程（検査）は治具なしで旋回もストッカも無し・
ライン終端に取り出しロボット + 段積みストッカ・協働ロボット前提のフェンスレス構成。

⛔⛔ **参照映像および付随する数値は evidence でも設計根拠でもない** — Rs 明言 2 件:
「実機の学習ログや実測結果ではありません」＋「動画はイメージであり詳細設計に基づいたものではないので注意」。
⇒ **設計の根拠・到達性の主張・verdict の evidence に使わない。**
映像 custody（p6 実測）= `~/Downloads/UR15_production_line_v7_20260726.mp4`
sha256 `83ce966a5d0ca13d6b231852ae61a930a91ae57e5b80080b6e7158c16a7e0f43` / 26.266667 s。

## 2. 未確定（Rs 裁定待ち・p6 は決めない）

1. **acceptance 条件**（goal_verification）
2. **8 工程の node 分解**と担当 lane 割当
3. `T-ROOT` との関係の詳細（本 node が上位・T-ROOT が中間、という骨格のみ Rs 指示で確定済）
4. `04-Specs/SOMA.md`（目標定義 SSOT）/ `RS71-System-Spec-SSOT.md` §0 への反映 = **Rs 専権・CC read-only**

## 3. SSOT の分担

結果・判定の SSOT = `07-Design/00-DESIGN-STATUS-LEDGER.md`。本 state.md は lifecycle / goal / pointer のみ。
