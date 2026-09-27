# パッケージ作成の同名ファイル衝突

初回buildは、`data/hvjb_receiving_interfaces_v01.json`と
`audit/hvjb_receiving_interfaces_v01.json`を同じ平坦な`sources/`へコピーしようとして停止した。
出力上書き禁止のassertによる停止。図の生成・旧製品・旧動画への書込みは行っていない。

停止時のコードは`failed_attempt/build_review.py.txt`、途中コピーは
`failed_attempt/delivery/`へ移動して保持した。

具体的な修正は、原資料のプロジェクト相対パスを保ってコピーすること。
`sources/data/...`と`sources/audit/...`を別の保存先にし、コピー先も入力監査JSONに記録する。
形状・描画・測定値・判定条件の変更はない。修正後も新しい出力先と上書き禁止assertを使う。
