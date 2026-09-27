# v05d 保存表示データの復元範囲

2026-09-27。ユーザーの全体動画継続依頼と、保持・受渡し確認後の「ok」を受けた作業。
根拠は当セッションの読取り、コマンド出力、既存監査 JSON。以下は実行前の差分記録。

## 事前検索

`scripts/check_thread_vault_prior_art.sh --fail-on-blocker HVJB 動画 再生成 行列bank`
は exit 2、findings=30、blockers=30。全文は
`/tmp/hvjb-video-recovery-prior-art-20260927.log` に保持する。
短い一般語による同じ行・複製ファイルへの重複を含む。
補助検索 `HVJB concept_display 保存姿勢` は exit 0、findings=0、blockers=0。
こちらのゼロ件で前の停止記録を取り消さない。

読んだ停止記録と維持する境界：

- `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/` 配下の
  `MEMORY_OFFSITE_COPIES_20260807/CURRENT_handoff_cc_p6_plankeeper_2026-07-07.md`
  の116/211/213行と複製：I0、FM3/FM4、bank世代、撤回済み映像判定を再解釈しない。
- `eval_runs/troot_verbal_teaching_20260705/CANONICAL_MOTION_TABLE_V1.md` の3/5行：
  D5のclip幾何、D6のpin-before-release、保護された43段階の順序を変更しない。
  当該driver・学習・物理run・gate開放は今回の作業ではない。
- `eval_runs/ur15_jb_harness_revision_20260907/WORK_LOG.md` の5/6/8行と納品複製：
  古い2種類の動画納品方式を復活させず、動画は工程レビュー1種類を維持する。
- 同310/312/317行：コマンド引数・ログ保存・SHA照合・guard実行の順序を守る。
- 同579/609行とv04 scopeの複製：原本と監査記録を保持し、再生成物は別の場所へ書く。
- 同784行：OP040の未指定構成を今回の復元で決定しない。
- 既存 `work/hvjb-panel-display-v02-20260924/PRIOR_ART_DELTA.md` に記録した
  H1 LOCK、C1 planar cable/clip-retention pin、把持と全閉の区別、V12の境界を維持する。

## 今回の具体的な差分

旧一時cloneと納品先から保存行列bankがなくなっていたため、確認済み動画の表示修正を
再開できなかった。ごみ箱内のv05b保存bankを読み、そのSHAが既存監査の
`7702cadf9e412895a14c82d1a6b85a6aa659f2978c22e59ddf16e2714c793a60`
と一致することを確認した。ごみ箱からフォルダ全体を戻さず、必要な入力だけをコピーする。

既存のXYZ補正、保持表示補正、板保持表示補正の関数を、変更せずに新しい出力先で呼ぶ。
元のmainは既存監査ファイルと旧絶対パスを前提とするため、新しい実行adapterを用意する。
旧パスから現在のcloneへの対応と全使用ソースのSHAを記録する。
各段階の出力SHAを当時の監査値と比較し、不一致ならそこで停止する。
浮動小数点の許容幅や補正値を変更して一致させる処理はしない。

復元対象は製品説明用の1785時点×304ノードの4×4表示行列であり、関節指令bankではない。
既存の製品・カメラ・時間・配線を保つ。新しいIK、制御、支持構造、物理判定、受入条件は作らない。
一致後の少数PNGは既存カメラと既存描画関数で確認する。既存v06原本と既存MP4は上書きしない。
一時cloneにしかなかったv05d描画・結合スクリプトが復元できた、とは主張しない。
