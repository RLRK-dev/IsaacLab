
## [2026-09-28 00:04 JST] correction | HVJB比較図の原資料コピーで相対パスを保持する

- セッション実行の観測。C工程接触域比較資料の初回buildが、dataとauditの同名JSONを
  一つのsources直下へコピーする箇所でexit 1。上書き禁止assertで停止した。
- 別checkout `work/hvjb-line-progress-20260927/work/hvjb-c-contact-layout-v01-20260927/`
  のfailed_attemptに初回コード、例外記録、途中コピーを保持。
- 具体的delta: 入力のプロジェクト相対ディレクトリを保ち、コピー先を監査JSONへ記録する。
  原図・製品形状・動作・測定条件の変更なし。修正内容は同フォルダRETRY_DELTA.md。
- 再実行前のguard `HVJB F-C ユニット搬送把持` はexit 0、findings=0/blockers=0。
  同じ平坦コピーを再試行せず、記録したパス修正後に新規出力先で作成する。
- この記録は資料作成の修正。把持・物理妥当性の判定は行っていない。
