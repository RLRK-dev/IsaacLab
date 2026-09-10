# B 千鳥 v06：両腕同時自由接続 helper

2026-09-10。`OP030B / 12D / RRTConnect` gate は関連0/blocker0。今回の新しい依頼は、正規の左右タスク割当を用いた両腕の自由接続を同じ時刻の12関節状態で検査すること。

既存 `op030_free_paths.plan_free_path` は6Dが関数内に固定されている。そのまま腕別に呼んだ軌道を同時再生すると、左右の相互干渉が確認できないため採用しない。新 `scripts/op030_b_stagger_free_12d.py` は既存 module の OMPL toolchain、LIMITS（安全端1e−6 rad）、RRTConnect、range .35、内部 .005 rad、最終 .0025 rad の手順を再利用し、状態次元だけを12へ拡張した。

API: `plan_free_path_12d(start[2,6], stop[2,6], score) -> (points[K,2,6] | None, audit)`。score は常に実左右 `[2,6]` を受け取る。身体ID/関節配列/モデルの交換を行わない。

直線を .0025 rad 以下の12D Euclidean間隔で先に確認し、交差した場合だけ OMPL solve(25秒) を一度呼ぶ。exact solution のみ受け入れ、既存と同じ .5秒 simplify 後の全 segment を .0025 rad 以下で再照合する。実メッシュscoreに非ゼロ/非有限値が出た場合はNoneを返す。関節制限外・非有限入力・端点不一致もNone。新しい接触例外は無い。

25秒は OMPL solve の上限で、初回直線確認・callback・最終検査時間を含む全wall時間の保証ではない。auditに呼出回数、各検査点数、失敗理由、関節限界、解の種別、実測wall時間を返す。本 helper の準備時点では、実B自由接続を実行していない。全経路の補間/retime/native 30fpsでの確認は呼出側の担当。

既存OMPLの局所再利用で足りるため、依存追加や別のcontroller/IK/機構を導入しない。離散実メッシュ確認は補助根拠であり、連続衝突保証や正式な物理妥当性判定ではない。
