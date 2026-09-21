# 内側ハウジングの4つの配線出口と指の退避

2026-09-21。前回の本体・配線・退避比較 `2b1c5a7637` の続き。
メーカー資料の4つの端子入口を整理し、保存CADの出口付近の投影を、同じ指の並進範囲と比較した。
実電線の経路、採用電線、製作寸法、アーム軌道、受入条件を決めたものではない。

## 成果物

- `output/pdf/内側ハウジングの4つの配線出口と指の退避_v01_20260921.pdf`：2ページ。
- `output/pages/`：最終PDFをPopplerで描画した全ページ。
- `output/exit_projection_observations.json`：5口の断面・比較・入力SHA・限界。
- `output/public_interface.json`：公開資料の4口構成と未確定の接続欄。
- `output/document_audit.json`：描画コード、PDF、観測JSONのSHA。

## 出口の対応

[TE 2103245 Rev A1][drawing]の後面図と、[408-32095 Rev B][instruction]の
p.1 Figure 1およびp.3 Figure 5を画像と本文で確認した。
電力用MCP 2.8接点が左右2口、HVIL用MQS接点が中央2口にある。
図面の電線側から見た口番号は左2、右1、中央上3、中央下4。
口番号を写真のWI線へ割り当てたり、実線の極性・行き先を確定したりしていない。

5口分の必要構成は電力10接点・HVIL10接点。これは従来の対応台帳を維持した数であり、
電線の物理本数や実配線の全数確定ではない。各口のHVILは[Ampere公式記事][ampere]とも整合する。
TE手順では接点の内側ハウジングへの挿入・保持確認と、内側の外側ヘッダーへの挿入が別段階。
保持確認の方法をロボットの力・信号・しきい値へ変換してはいない。

公開ページは2026-09-21に確認。図面はA1、説明書はBの表示だった。
保存PDFのSHAを照合し、説明書p.3と図面全頁をPopplerで描画して確認した。
資料内の写真は説明書p.3 Figure 5の埋込原画像（PDF object 70 0、255×146画素）を抽出した。
画像SHAを固定し、部品・配線を描き足していない。
MQS検索では接頭辞付き別品番も見つかったが、旧説明書の候補やAmpere採用品番へ同一視していない。

## 新しい幾何比較

元CADの後端電力2口の断面輪郭を前回の関数で抽出した。
中央はsource Z=-33.8995 mmの断面にある中央ループの凸包を使い、2口をまとめた比較範囲とする。
**中央の個別穴寸法・MQS端子位置を確定した結果ではない。**
0.5 μm内側の断面は数値抽出位置で、公差や製作寸法ではない。

この3領域を、source X/Y（製品相対X/Z）の平面上で比較する。
軸方向の座標を除くため、仮にその輪郭を軸方向へ延ばした全領域との比較になる。
実際の電線を挿入・曲げ・束ねた形状や、許容電線径を作ったものではない。
元の指・支持部・取付座・本体は前回スクリプトから再利用し変更していない。
純並進の全中間位置を凸包に含め、その投影と出口領域をクリップした。
1 nmの内縮と面積1e-16 m²の数値設定は前回から維持し、受入基準へ使わない。

| 比較 | I01〜I05の電力2口 | 中央HVILの一括範囲 |
| --- | --- | --- |
| 閉じた指 | 投影の重なり0 | 投影の重なり0 |
| 0〜各4 mm開放 | 投影の重なり0 | 投影の重なり0 |
| 各4 mm開放後、上方0〜50 mm | 投影の重なり0 | 投影の重なり0 |
| 比較対照：各2 mm開放後、上方0〜50 mm | 左右とも投影の重なりあり | 投影の重なり0 |

投影の重なりありは、必ずしも同じ軸位置での3D衝突ではない。
重なり0は、定義した仮想領域と今回のハンド形状についての補助観測。
曲がった実電線の非干渉、端子や被覆の収まり、接点・内側ハウジングの残留保持を保証しない。
前回見つかったWI41/WI51との後方退避時の重なりは、この直線投影比較で消えたことにはしない。

## 未確定の接続を残す

`public_interface.json`には各口4接点の必要欄を保持し、次をnullのまま残した。

- 写真WI線と物理穴番号・実接点・電気ノードの対応。
- 採用電線径、出口からの3D中心線、最小曲げ半径、束ね方・支持。
- I03の出口線、HVILの実周回順、隠れた区間・共締め積層。

図面の口番号と、写真の「近くに見える線」のIDは別。
既存表示モデルへ線を足して接続済みに見せたり、今回の仮想領域を実電線として保存したりしていない。
配線の対応が揃った時点で、同じ4 mm開放案と曲がる実配線の形状を照合する。
5腕・20仕事、OP010のXYZと20枠共用、1段往復パレットの構成は維持する。

## 検証・再現

`probe_exit.py`は前回のCAD読込・指生成・並進包絡・クリップ計算を再利用する。
既存CADと前回観測のSHAを照合し、既知の面積3例と、端点では見落とす中間交差1例も照合した。
画像・数値は補助資料であり、独立レビューを経た物理判定ではない。
新しい物理シミュレーション、IK、工程動画は生成していない。

事前検索語：`HVJB 2103245 WI41 電線出口`。guard終了0、findings/blockers/lessonsはいずれも0。
加えて既存のwire-origin・final-connection・tool-wire-sources・写真対応v03を読み、
写真の可視区間と実端子接続を分離する訂正を引き継いだ。

描画はPDFスキルに従いReportLabを使用。既存Python環境には未導入だったため、
`/tmp/hvjb_pdf_runtime_20260921`だけへ4.4.3を導入した。IsaacLabの依存設定・本体環境は変更しない。
数値計算は既存NumPy/SciPy/trimesh、図は既存Matplotlibを使用する。

```bash
./isaaclab.sh -p work/hvjb-inner-wire-exit-v01-20260921/probe_exit.py
PYTHONPATH=/tmp/hvjb_pdf_runtime_20260921 ./isaaclab.sh -p work/hvjb-inner-wire-exit-v01-20260921/build_review.py
pdftoppm -scale-to 1654 -png work/hvjb-inner-wire-exit-v01-20260921/output/pdf/内側ハウジングの4つの配線出口と指の退避_v01_20260921.pdf work/hvjb-inner-wire-exit-v01-20260921/output/pages/page
```

既存観測JSONがあればprobeは停止する。再実行のために納品結果を削除せず、新規作業コピーを使う。
ログ内の`EXIT_PROJECTION_COMPLETE`、`WIRE_EXIT_PDF_COMPLETE`と成果物SHAも確認する。
PDF全2ページを描画して、文字・図・配置を目視確認した。

[drawing]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=2103245&DocType=Customer+Drawing&PartCntxt=2103245-1
[instruction]: https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=408-32095&DocType=Specification+Or+Standard&PartCntxt=2103245-1
[ampere]: https://help.ampereev.com/hc/en-us/articles/31292470232087-High-Voltage-Junction-Box-HVJB-5-400
