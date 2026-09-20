# 内側ハウジング指先の3D比較・開放空間 v01

2026-09-21。前回の後端把持模式図を、保存CADに沿う交換指先の3D比較へ進めたもの。
ハンドの製作仕様、荷重条件、アーム軌道、物理成立の受入判定は作成していない。

## 見るもの

- `output/pdf/内側ハウジング指先の3D比較と開放空間_v01_20260921.pdf`：3ページの確認図。
- `output/pages/`：最終PDFをPopplerで描画した画像。
- `output/tip_access_observations.json`：5接続口の数値・試行寸法・範囲と限界。
- `output/trial_tip_meshes.json.gz` / `output/rear_only_tip_meshes.json.gz`：元案と後端寄せ比較の三角形。
- `output/document_audit.json`：PDF、観測JSON、描画コードのSHA。

## 比較と観測

元案は、TE 2103245-1の後端外周断面を囲う左右の指先と、小さなつば押し面を持つ。
4.5 mmの接触帯、0.1 mmの表示用逃げ、パッド外端1.0 mm、支持部外端3.0 mmは
今回の比較入力であり、ユーザーが採用した製作寸法ではない。
KEY A/D/E/FのI01〜I05を別々に照合する。

保存された表示位置では、元案の指先体積に外側ヘッダーの三角形表面が入る。
閉じた位置で該当三角形はI01/I02/I03/I04/I05の順に6112/6112/5978/6128/6054枚。
数はテッセレーションに依存し、力、重なり体積、重大度、受入基準を表さない。
各面を凸な指先区画で切り出した補助観測で、ゼロ枚でも全面的な非干渉を証明しない。

閉じた指先の開口への公称投影余白は、23.0 mm開口で約0.125 mm、22.8 mmで約0.025 mm。
これは公差を積んだ余裕や実物の通過判定ではない。指先を左右各2 mm開くと、
筐体壁の表示範囲内の段付き面が開口外へ0.9/1.0 mm出る。
8 mm後退した終点は切出し0枚だが、途中の開放・保持解除・ロック状態を求めていない。
部品を保持したまま引く手順を採用したわけではない。

比較Bは、接触帯をCAD後端の3.1 mmへ寄せ、つば押し面を外す。
今回の5口の表示位置ではヘッダー表面の切出し0枚となる一方、軸方向へ押す面がない。
保持と挿入力の伝達、短い樹脂部の変形、電線出口、開放時の残留保持は未解決。
比較Bを採用品として選定していない。

## 元データと座標の意味

内側CADは前回と同一の`hvjb_photo_cad_v01.json.gz`（SHA `1ac417ba…`）。
source Z=0は差込み先端、source Z=−42.6 mmは電線側後端。
TE図の参考32.40 mmはこの全長と範囲が違う。

外側CADは旧`data/header_review_v03/meshes.json.gz`（SHA `8c0bbe8c…`）の
`headers`配列から各行を変更せず分離。`prepare_inputs.py`が親SHA、抽出後の完全一致、
分割ファイルSHAを記録する。大きな旧ハンドデータは再配布に含めない。
TE外側図面2本も変更せず保存した。来歴は`data/provenance.json`。

内側からヘッダー局所座標への変換は既存の`build_hvjb_photo_model_v01.py`の
表示配置を継承し、`(X,Y,Z)=(source X + bay X, -source Z - 0.0311, source Y)`。
既存`build_header_review_v03.py`の壁表示を継承し、ヘッダー局所Y=0〜3 mmとした。
これは測定済みの嵌合姿勢、実物の壁厚、Ampereの加工図寸法ではない。
内外CADの実装位置の確定は別に必要であり、今回の重なりもこの表示登録に依存する。

筐体開口は既存の`hvjb_header_interface_inputs_v01.json`を使用。
高さ13.5 mm、R4.4 mm、幅23.0/22.8/23.0 mmと22.8/23.0 mmを保つ。
式への入力・元CAD・指先寸法は観測JSONへ保存。
CAD三角形は変更せず、指先輪郭に限り直線上の分割点を10 nm以内で整理する。
1e-16 m²は切出しの数値ノイズを除く値であり、許容干渉面積ではない。

## 再生成

Python環境は既存IsaacLab環境のNumPy、trimesh、Matplotlib、Pillowを使用。
新規依存、シミュレーション、Blenderシーン保存、動画生成は行わない。

```bash
./isaaclab.sh -p /path/to/work/hvjb-inner-tip-access-v01-20260921/geometry.py
./isaaclab.sh -p /path/to/work/hvjb-inner-tip-access-v01-20260921/build_review.py
```

初回の親アーカイブからの抽出が必要な場合だけ：

```bash
./isaaclab.sh -p /path/to/work/hvjb-inner-tip-access-v01-20260921/prepare_inputs.py --source_root /path/to/eval_runs/ur15_jb_harness_revision_20260907
```

クリップ計算はCADとは別の三角形3例で解析値0.5/0.125/0.0と照合した。
PDFの本文はページ外にはみ出さないことを記録し、最終PDF全3ページを描画して目視確認する。
TEの手順とAmpere映像の順序は引き続き分ける。接触器等の20仕事、5腕の役割、
XYZ・20枠共用・1段往復パレットの構成は今回変更していない。
