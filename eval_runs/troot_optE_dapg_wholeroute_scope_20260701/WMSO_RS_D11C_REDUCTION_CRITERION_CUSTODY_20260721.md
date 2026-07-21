# WMSO D1.1-C — Rs 発話 custody（縮小判断の基準・自律付与）

- 記録者 = `w2:pQ` RS-TECH-LEAD2（node `T-WMSO`）／記録 = **2026-07-21 15:4x JST**（shell 実測）
- 作成契機 = debate cycle-2 の指摘 **F-10**「本 doc が引く Rs 逐語に custody artifact が無い（grep = design 1 file のみ）」

## 1. 逐語（3 件・すべて本 pane `w2:pQ` の user turn = **relay 0 hop**）

| # | 時刻 | 逐語 |
|---|---|---|
| U-1 | 2026-07-21 **14:1x** | **進んで** |
| U-2 | 2026-07-21 **15:0x** | **確かな前提条件があるほうを選べ** |
| U-3 | 2026-07-21 **15:1x** | **どんどん進んで。今後も推奨で進んで** |

## 2. 各発話の直前文脈（何に対する応答か）

- **U-1** — 私が「D1.1-C = prereg 二鍵充足・⛔Rs scope 承認待ち・design authoring 未解錠・self-start しません」と報告した直後。⇒ 別 custody `WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md`（`2b64a66352ce5f50…` @ `d57ec90df1`）に記録済。
- **U-2** — 私が **A（縮小版）と B（全 fold 版）** の差を提示し、**B を推奨**した直後。⇒ Rs は案を選ばず**選択基準**を与えた。私はその基準を適用して**推奨を B から A へ撤回**した。
- **U-3** — cycle-2 前、私が「fixture bank → cycle-2 → two-key に進みます。止める場合は一言ください」と述べた直後。

## 3. 各発話が決めたこと / 決めていないこと

| # | 決めたこと | ⛔決めていないこと |
|---|---|---|
| U-1 | D1.1-C の **design authoring 解錠** | impl / training / authority / push / freeze / slice（別 custody §3.2） |
| U-2 | **選択基準**（前提の確かさで選べ） | ⛔**どちらの案を採るか**（適用は CC1）／⛔**承認済 scope（prereg §2 IN 5 項）を 2 項へ縮小してよいか** |
| U-3 | **以後の逐次承認を求めず、CC1 推奨で前進してよい**（standing） | ⛔既存の fence の解除（U-1 の §3.2 は不変）／⛔Rs 専権事項（凍結編集・freeze・scope 変更） |

## 4. ⛔ U-2 から導かれる未決（cycle-2 F-10・本 custody の主目的）

**承認済 scope の縮小そのものが Rs 事項である**。
- prereg §2 IN は **5 項**で、pS 設計軸 PASS + pY evidence 軸 PASS + Rs scope 承認を経ている。
- v2.1 は **2 項のみ**を設計しており、**過小履行も scope 逸脱**である（過大履行と同様）。
- U-2 は「前提の確かさで選べ」という**基準**であって、「承認済 scope を縮めてよい」という**許可ではない**。私がその 2 つを同一視していた。
- ⇒ **Rs 判断 (c) として上程する**（既存の (a) 凍結併記訂正／(b) D-1 無影響の正式確認 に追加）。

## 5. 誠実な範囲

- 本記録は **CC1 の transcription** である。私は Rs channel の一次ログを持たない。⚠ **逐語の byte 忠実性は独立検証されていない**（pS が prereg verify §1 で同種の注記を既に置いている）。
- U-3 の standing 付与は**逐次承認の省略**であって、**Rs 専権事項の委譲ではない**。迷う場合は止めて報告する既定は不変。
