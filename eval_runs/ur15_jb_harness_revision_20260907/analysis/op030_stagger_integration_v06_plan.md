# B 千鳥配置 v06：統合差分検査の準備

作成日: 2026-09-10。根拠は今回の明示指示、`OP030_v06_scope.md`、既存検査コードの読取り。新しい B bank / static / prepared / baked native が未完成の時点では、ここに合否を記録しない。

`check_thread_vault_prior_art.sh --fail-on-blocker OP030 千鳥 integration` は 30 findings / 24 blockers / 6 lessons を返した。主な該当は保存済み v05 の完了済み run と監査「失敗0」の文脈。今回の具体差分は、B のみを proper rigid D で反対側へ移す新ユーザー指示であり、v05 の再実行・上書きではない。root が既に範囲と C1 clip/pin 文脈との差を WORK_LOG/Vault に記録した。新しい機構、接触例外、反射スケールは追加しない。

## 再利用と追加

- `probe_op030_front_integration_v05.py::export_changed`：完成 native の entry / A→B / B→C の全保存時刻から、payload・移動機構・近傍の evaluated triangles と full affine 行列を取得する。
- `probe_op030_v05_integration.py::native_export`：C prefill と B drawer の同時刻、全固定背景を実 native から取得する。固定背景は新しい pinned static の world triangles と一致するかを別記する。
- `probe_op030_split_a_payload.py::check`：一定 stretch を頂点に焼込み、実 triangle FCL と接触面を記録する。`check_fixtures` は明示された同一機構の内部だけを外部照合から省く。外部接触例外は増やさない。
- `probe_op030_v05_background.py::Station` と `op030_split_product_delta.py::DeltaCheck`：元 FK bank と工具 spindle / UID / 変形被覆の対応を再利用する。B は新 factory `op030_split_b_stagger_v06:build_sequence(config)` を明示して使用し、旧 factory への差替えは行わない。
- 新規 `probe_op030_stagger_integration_v06.py`：saved array identity、B 初期/終端 park の world mesh export、native B 全 node と drawer / 10 UID の座標対応。
- 新規 `probe_op030_stagger_background_v06.py`：A/C の保存動作対新 B park、B 対 C loaded park、各 station context の外にある新固定背景。名前が同じでも world triangles が異なる旧 B 配置は照合対象に戻す。

## 入力契約

| 入力 | 契約 |
|---|---|
| A/C banks | v05 の SHA が不変。A 7,165 frames、C 2,430 frames / preload 264 frames。 |
| B bank | `data/op030_split_b_stagger_motion_v06.npz`。78 node IDs、baseline root (+.9, −1.7, 0)、world 化は Y+2.3 を一度。v05 bank 同一 SHA の場合は検査を停止する。 |
| B factory/config | `op030_split_b_stagger_v06:build_sequence(config)`。active UIDs、wire points/lug frames/material parameter 契約を保持。 |
| Static | `analysis/op030_stagger_static_v06.blend` / `audit/op030_stagger_static_v06.json` を予定。移設 root `OP030B_robot_supply_stagger_root`、既存 actor 名は保持。 |
| B supply | 新親 local +X 0..340 mm = world −X。10 UID は引出しへ追従し、使用 2 UID は製品へ、残り 8 UID は戻る。 |
| Prepared/native | root が生成した v06 NPZ/JSON と scene `split_animation_sha256` の一致が必須。旧 v05 配列を代用しない。 |

## 完成後の対象

1. A/C source bank の SHA と新 timeline 中の対応、製品 Z .8845 m / pallet Z .789 m、製品の回転、B proper rotation / root 座標を保存配列から記録。
2. C prefill と A 初動・新 B 待機/10 UID 提示の同時刻を native 全 frame で照合。
3. 引出し提示と残り 8 UID の戻りを含む entry / A→B / B→C の payload と移動機構の外部交差。
4. 新 B 初期 park + 提示 10 UID 対全 A、新 B 終端 park + 戻った 8 UID 対 C 本工程、C loaded park 対 A 残り/B 全工程。
5. 各 A/B/C の全 bank frame 対固定全景。元 station context に同じ world triangles で含まれる対象だけを省く。
6. native の B 78 node の world 行列、D の正の行列式、drawer の world −340 mm X、10 UID の drawer 相対姿勢、背景の新 static 対応。これにより取り残し/二重回転を数値で区別する。

全件は保存時刻での幾何・個体・座標の補助確認。接触力、摩擦、締付品質、実機安全性、正式な物理妥当性は判定しない。検査した discrete frames 間の連続衝突保証も行わない。
