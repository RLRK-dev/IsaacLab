# 15度版のデフォルト化と、次の工具側確認

2026-09-14。ユーザー「ok これをデフォルトとしてすすめて」を受けた作業記録。

## 作業用デフォルト

**今後のケーブル保持手先はT050、時計回り15度をデフォルトとする。**
黒被覆の端子側をつかみ、根元でもケーブルを保持する。後退量40 mmを維持する。
他対象の手先まで一律に2本指や同じ輪郭へ変更する指示とは扱わない。

| 設定 | 作業用の値・状態 |
|---|---|
| 現在の手先 | 既存2F-85の機構＋専用の被覆側・根元パッド |
| 傾斜 | 画像の側面で時計回り15度。world X軸まわり−15度 |
| 使用候補 | T050、初期状態near |
| 保存状態 | near / early / open / clear |
| 上端逃げ | T050の0.5 mmを作業モデルとして維持。製造公差の承認とは別 |
| 保存元 | `THREAD_フィンガ15度傾斜_v01_20260914`、commit `d91cd07d25` |

`data/hand_working_default_v01.json`を今後の入口とし、入力SHAを照合する
`scripts/prepare_hand_working_default_v01.py`で選択する。古いD30/H050等の比較設定は履歴として保存。
新規作業のデフォルトには使わない。新しい選択器は造形・行列変更を行わず、承認された候補を抽出する。

```bash
VIRTUAL_ENV=/home/rlrk/src/ur15-line-render/venv ./isaaclab.sh -p \
  eval_runs/ur15_jb_harness_revision_20260907/scripts/prepare_hand_working_default_v01.py \
  --output_directory /tmp/hand_working_default_new
```

入力パッケージを移した場合は`--source_directory`で場所だけ変更できる。SHAが異なる入力は停止する。
抽出後のJSONも再読込し、T050の全オブジェクト・保存行列が元データと一致することを確認した。
v06・15度比較版のnative/GLB/観測記録は上書きしていない。

## 次に確認する工具側

次段では、**保持したまま締付ける位置へ、供給機構を含む工具が入るか**を確認する。
15度版では上部が離れる一方、端子側の把持面は元の位置のため、先端域の空間は増えていない。
主軸の円筒だけを見て供給ノーズまで入ると判断しない。

2026-09-14の公式サイト確認で、DFMには固定設置用や追加Z送り付きの構成がある。
E-SFMには固定ノーズ、能動的に開く爪、傾動・旋回ノーズ、ピックアンドプレースの選択肢がある。
これらは**比較対象の構成の違い**であり、採用型式は選定していない。
[DFM公式](https://www.deprag.com/en/automation/screwdriving-units/deprag-feed-module.html)、
[E-SFM公式](https://www.deprag.com/en/automation/screwdriving-units/e-sfm.html)、
[E-SFMカタログ p.3–4](https://www.deprag.com/fileadmin/bilder_content/emedia/broschueren_pics/emedia_Automation/D0062/D0062en.pdf#page=3)。

| 比較する状態 | 必要になる形状 |
|---|---|
| ボルト・ナット受取 | 供給口、保持される締結部材、供給ホース |
| 接近 | 閉じたノーズ、前端のスリーブ／ソケット、工具本体 |
| 締付け | ノーズ開放外形、工具の突出量、取付部、配線 |
| 軸抜き・退避 | ノーズを閉じる途中の形、引込み、追従ホース |

表は確認対象の整理であり、実機シーケンスや受入閾値ではない。現時点では各状態の一式CADがなく、
ノーズ付き工具全体の干渉測定は行っていない。
供給ノーズと工具を組み合わせた寸法、相手のボルト／ナット・座金の積層、取付基準が必要。
寸法と必要隙間は`data/hand_tool_interface_inputs_v01.json`に未確定値として残す。

## CADの入手経路で確認できたこと

[公式のCAD・寸法図入口](https://www.deprag.com/en/emediacenter/pdf-screwdriving-technology/technical-information.html)
は[myDEPRAGの製品ページ](https://my.deprag.com/products/category/electricScrewdriver/)へつながる。
今回の未認証Chromeでの表示は`myDEPRAG Login`で、Email／Password／Login／Registerを確認した。
ログイン後の内容は読んでおらず、目的のノーズCADがその先にあることも未確認。
ログイン・会員登録・問い合わせ送信はしていない。公開ページと、未認証画面の観測を区別する。

## 引き継ぐ工程条件

締付け完了までフィンガ保持を続ける。上押さえは追加しない。
保持2腕＋ST側2工具の比較方向と、大小同時締付けの要求を維持する。
1工具の逐次締付けを、同時締付けの解決として置き換えない。
今回のデフォルト化は、把持力・材料・実機成立の判定や、全工程のアーム軌道決定とは別である。
正式物理判定はVaultProtocol V12の経路に留める。

## 記録

- prior-art guard（T050／締付ユニット／供給ノーズ）：0件、停止文脈0件。
- デフォルト選択器：5入力のSHA照合、4状態と20実体メッシュ、抽出後の候補一致を確認。
- 公開資料と未認証ポータル画面は当日の観測。工具CAD取得済みという記録にはしない。
