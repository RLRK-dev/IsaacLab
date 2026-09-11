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
last_updated: 2026-09-11T19:56:34.238334+09:00
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


## 4. 工程検討映像の現行参照先（2026-09-11）

根拠はセッションのユーザー指示、保存モデル・動作・動画・検査報告の読取り、
および `2026-09-11T19:37:31.763717+09:00` のDownloads実ファイル照合。
ユーザーは同日 `UR15_JB_OP030_split_process_v06_review.mp4` を確認したと述べ、次のOP040へ進むよう指示した。
§1のv7は起票時の参考映像。現行v06はOP030Bだけをコンベア反対側へ移した千鳥配置版。
THREADの最終目標イメージを具体化する工程検討映像として扱う。

- [工程説明付き動画](/home/rlrk/Downloads/UR15_JB_OP030_20260910_v06/UR15_JB_OP030_split_process_v06_review.mp4) ／
  [確認ページ](/home/rlrk/Downloads/UR15_JB_OP030_20260910_v06/review_OP030_split_v06.html) ／
  [工程・部品確認書](/home/rlrk/Downloads/UR15_JB_OP030_20260910_v06/OP030_三ST工程・部品確認書_v06.md)。
- [モデル・動画・再生成データ一式ZIP](/home/rlrk/Downloads/UR15_JB_OP030_20260910_v06.zip) は
  592,879,592 bytes、SHA-256 `1c66b66a96661706d59d2931496bc9d7e62c42580ac988b774a7e9cc20a97ded`。
  同梱171ファイルの名前・サイズ・SHAとZIPのCRC・全格納ファイルSHAを照合済み。
- [Blenderモデル](/home/rlrk/Downloads/UR15_JB_OP030_20260910_v06/UR15_JB_OP030_split_v06.blend) の
  SHA-256は `e65bef607c1d29671fc982d14d72d4c2694420edd284378cb2f1445f18f354ed`、30 Hz・14,062フレーム。
- 動画は工程1280×720・15 fps・7,031フレーム、FFprobeのduration 468.734秒（約7分49秒）。
  SHA-256 `2030ae0e6de5e53e90bc5f2a86977f65fcb6cf15bed62e1d391d4a2011f35004`。
  全デコードexit 0、全画面黒区間なし。1種類への配布変更では再圧縮していない。

今後の新規生成・Downloads納品・ZIP同梱動画は、ユーザー指定により
**`*_split_process_*_review.mp4` の1種類のみ**。
工程PNGから説明付きMP4へ直接符号化し、中間raw MP4・全景動画は生成しない。
方針は `eval_runs/ur15_jb_harness_revision_20260907/data/video_delivery_policy.json`、
継続作業指示は同フォルダーの `AGENTS.md`、専用エンコーダは `scripts/encode_process_review_video.py`。
新エンコーダの短い実出力確認では3フレームのreview MP4だけが生成され、全デコードexit 0。
これは出力形式の確認であり、ロボット動作の物理検証ではない。

A/Cの動作と配置はv05を維持。Bの床基台・供給台・制御盤などを180°の剛体回転で反対側へ移し、
OP010−／OP020＋／A−／B＋／C−／OP040＋の順にした。
Bは10本の並列供給から1本の両端を同時把持し、旋回中に曲げて設置する。
着座後に両指を開き、同時に180 mm上昇してから全開にする。
B保存動作は3,787フレーム・126.2秒で、v05の151.666667秒より25.466667秒短い。
Aは238.8秒、Cは事前装填を含む80.966667秒。これらは保存アニメーション時間であり、実機量産タクトではない。
パレット原点Z789 mm・製品原点Z884.5 mmを維持し、作業のためにパレットを上げない。
支持部20個の5×4格子、ケーブル10本の並列供給、常設締結工具と専用供給器、
オンハンドカメラ、外部LED、透明パネルを除いたカバー枠を継承する。外側の青いF01は変更していない。

実Chrome確認は `2026-09-11T19:34:04.034682+09:00` に完了。
動画1本の実再生、160章のラベル・時刻・seek、相対リンク133件を確認し、JavaScript例外0。
390/1200 pxで補助資料欄を開閉した4条件で横はみ出し0。
報告は `audit/op030_split_process_page_browser_v06/completion.json`、
SHA-256 `6eb2ef6ff0cf4f8b6b36f9fa1f87e77bcc88cf70846552ba684b96349c3aa3fe`。
納品報告は `audit/op030_process_only_delivery_v06.json`。いずれも上記作業フォルダーからの相対パス。

最終Bの全保存姿勢の実メッシュ確認、搬送・周辺設備との照合は補助的な幾何観測。
元の機械照合native `8674c2483ac1fe7e3dc42e6b1d14fdc4919f28818784de4f53f878477714d338` から
最終nativeへの差分は撮影用カメラ2台だけで、非カメラの全保存レコード一致を確認した。
元報告のSHAは保持し、最終nativeに対して全FCLを再実行したとは扱わない。
根拠は `audit/op030_camera_delta_v06_evidence.json`。
元19 helperを含む23入力の隔離再ベイクでは14,062フレーム、406時刻・60,760行列の読戻しを照合。
入力SHA前後一致、外部画像/library 0。根拠は `audit/op030_split_layout_portable_rebake_v06.json`。
1動画版でもこの23入力は不変。

旧v05のZIP/nativeは以前のSHAと一致した。先に完了したv06の4動画一式は
`analysis/op030_v06_full_delivery_before_process_only/` へ移して保全し、旧報告の観測値は書き換えない。
旧v06 ZIP SHAは `96cf056ef52a0b8057b897d837d40688100f1e0389d9a2ce3943f87e162cf533`。

次工程OP040は分岐配線の接続・配索。既存の背景parkとリブ上の旧部品は、新しい組付け動作ではない。
J2/J3/J4と内部端子の接続表、本数、端末仕様、確定線長は現資料で未定義。
`analysis/op040_process_inventory.md` と `analysis/op040_stagger_motion_reuse.md` を再利用し、
v06の同一製品・H03の2本・締結済み部品を基準に詳細化を進める。
接続資料を使用するか、動画用の接続案を先に作るかはユーザーへ照会した。
**2段循環の下段空パレット返送・両端昇降移載は未実装。**
ユーザーの映像確認も含め、本記録は正式な物理妥当性、把持力、締結品質、実機成立や学習成果の判定ではない。
正式判定はVaultProtocol V12の独立レビュー経路による。goal/acceptance/means/treeおよび§0〜§3は今回変更しない。
