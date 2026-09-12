# 千鳥配置に向けた座標・動作再利用の読取整理

2026-09-10。根拠は最新v05のソース、保存NPZ、固定manifest、Blenderによるframe 1の読取結果。既存source・bank・nativeを変更していない。新IK、干渉探索、配置候補の生成は実行していない。

再発防止検索 `OP040 stagger coordinate_mapping` は0 findings / 0 blockers。V7/V9/V10/V11/V12を適用。既存の千鳥配置・剛体写像・FK/UID照合の再利用を優先する。`T-PRODUCTION-LINE/state.md:35` の千鳥配置は元の概念説明であり、同文書の注意書きどおり実機設計や到達性の証拠にはしない。

## 結論

**製品とパレットの向きを固定したまま、ロボットを左右交互にできる。ただし、反対側に移すロボットの組付動作へ元qを一括適用することはできない。**

元OP010を−X側、OP020を＋X側に置く順序を維持するなら、OP030A− / OP030B＋ / OP030C− / OP040＋ / OP050−…となる。OP030分割で増えたセル数は2なので、既存下流の左右の順序は変わらない。最新ABCは全て−X側であり、千鳥配置を戻す最小変更はBのみの側変更である。A/Cは配置自体を変更しなければ保存qを維持する候補にできるが、新B設備・待機姿勢との相互干渉を別途確認する。

OP040は既に＋X側の床基台に存在する。次工程OP040の新組付動作は工程内容に沿った別の動作作成が必要であり、現在の背景parkはその工程を再現した動作ではない。

## 固定入力と読取値

| 入力 | SHA256 / 値 |
|---|---|
| `UR15_JB_OP030_split_v05.blend` | `985c7edf11a80f0e1e15ba5176b3040b9d733c30315ae6b732b4c359239afc3d` |
| `data/op030_split_animation_v05.npz` | `fbbb64e71cf068c9e6386c170c21932ad225cbcf84cf09e1b2b9a90b81155ebb`、14,826 frame |
| 固定入力 `analysis/op030_split_front_feeders_static_v05.blend` | `b3d22be1dfba8e2c0247677a6f05eb8761d357572d9aac95a372b58f074fd22f` |
| A bank `data/op030_split_a_motion_v05.npz` | `e56b610e5ee4642b16c03f7fb321936e3d1d11183218fe3fd0dbd3851dcc6c96`、7,165 frame |
| B bank `data/op030_split_b_motion_v05.npz` | `923ae01512f2d63e1ac57237b044316cce2b0fadba3701940b17f68e0dd2d1c6`、4,551 frame |
| C bank `data/op030_split_c_front_indexed_motion_v05.npz` | `238c6b233871f25c0e95113b0d4d92124a569218ab8a40926773637e1ad96e38`、2,430 frame、初回装填264 frame |

全bankのロボット基準原点は `(-0.9,-1.7,0)` m。preparedがA/B/CへそれぞれY `0/2.3/4.6` mを一度だけ加える。各bankの78 nodeはヨーク577/578と、左右腕の元visual node `1046..1083 / 1086..1123`。**固定基台576はbankにない。**

| 現在のセル | ロボット基準原点world [m] | torso yaw（bank開始→終了） |
|---|---|---|
| A | `(-.9,-1.7,0)` | `90°→90°` |
| B | `(-.9,.6,0)` | `−90°→90°` |
| C | `(-.9,2.9,0)` | `110°→110°` |
| OP040 | `(+.9,4.05,0)` | 背景parkは既存＋X基台で90° |
| OP050 / 060 / 070 / 080 / 090 / 100 | X `−.9/+.9/−.9/+.9/−.9/+.9`、Y `5.2/6.35/7.5/8.65/9.8/10.95` | 既存床基台・背景park |

保存prepared全frameで製品回転は `diag(−1,−1,+1)`、パレット回転は単位行列であり、各回転行列の最大変化は0。製品原点Z `.8845` m、パレット原点Z `.789` m。Yだけが−2.85 mから2.90 mへ進む。製品の回転とパレットの回転を同じとみなしてはいけない。

## 再利用先と使い分け

- 元 `inputs/v02_source/inputs/v01_source/op010_base/original/render_ur15_line.py:885` の `CELL_LAYOUT` はX±0.90 m、初期yaw∓90°の交互配置。`initial_cell_root` / `cell_root`（6142行付近）はロボットのセル基準変換。元の1.15 mピッチを新ABCの2.3 mピッチへそのまま代入しない。
- `scripts/op030_downstream_park_v04.py:apply_downstream_park_v04` は `mapping = target_root @ inv(original[577])` で、元qに対応する腕・ヨークの保存world poseを写す。既存床基台と元visual名の対応を検査している。**parkの剛体再配置候補の再利用先**であって、新しい製品接触動作の保証ではない。
- `scripts/op030_fk_fast.py:Chain` と `solve_op030_motion.capture_robots` は元UR15 FKと元Yヨークを共通利用する。新しい基準姿勢から同じ製品targetを解く場合の再利用先。
- `scripts/op030_split_layout.py:duplicate_set` はparent/driver参照を写す既存複製API。ただし `OP030B_cell` にはロボットだけでなく位置決め機構・供給台等も含む。cell全体を回すAPIとして使わない。
- `scripts/op030_motion.py:turn_frame` の中心は**ロボット基台** `(-.9,-1.7,0)`。これは現Bの胴体旋回であり、コンベア中心を挟む側変更には使えない。使うと基台が元の−X位置に残る。
- 元 `mirror_joint_pose` は同じ機体の左右腕用の符号写像。床基台の反対側移設の代用ではなく、固定工具の左右役割も変更しない。

## 座標契約

セルYを `s`、コンベア中心を `c=(0,s,0)` とし、反対側への剛体写像を `D=T(c) Rz(π) T(−c)` とする。Bなら `s=.6`。これは鏡映ではなく `det(R)=+1` の正しい剛体回転であり、−.9 m基台を＋.9 mへ移す。

同じqを使い、基台と工具を剛体で写すと `FK(D B,q)=D FK(B,q)`。よってロボット自身の形・腕同士の相対関係、取付工具・カメラのflange相対姿勢は維持できる。しかし製品を固定するなら要求targetは `P W_part T_contact` のままであり、一般に `D T_old != T_required`。ロボットだけの移設でも、元qの手先は製品中心回りに180°移動する。

例として現J1の2座はbaselineで `(+.1995,−1.3885,.9085)` / `(+.1995,−1.4115,.9085)` m。ロボットと一緒に写すと `(−.1995,−2.0115,.9085)` / `(−.1995,−1.9885,.9085)` mとなり、固定する正しい座から約`.739818/.701520` m離れる。これは保存座標からの剛体計算であり、新IK実験ではない。製品も一括でD変換すると製品回転がRzπからIになり、外部ハーネス側・端子の前後が逆転する。

配置変換は次の3種類を分離する。

1. **ライン側**：パレット、JB、ローラー、位置決め・ストッパ、F01、組付済み支持・配線・ナット。搬送路のworld座標と製品相対姿勢を維持する。
2. **ロボット側**：床基台576、ヨーク577/578、左右腕、精密フィンガ、手先カメラ・取付部、固定工具。明示したロボット用Dで移す。
3. **供給側**：B供給用パレット、引出し・受け・台・アクチュエータ、残10→8本のUID、接続ホース・支持。ロボットと同じ相対配置を保つなら同じDで移し、ライン側への取付やホース接続は新位置で確認する。ここでいう供給用パレットは搬送パレット `source_0292` とは別物。

B供給中心は格納X−2.02 / 提示X−1.68 m、引出しworld＋X .340 m。Dを適用する案では＋2.02 / ＋1.68 m、引出しworld−Xへ変わる。旧 `translations(drawer_B,2.3,0)` と、ワイヤーrootへのX加算をそのまま流用しない。baseline版Dの中心は `(0,−1.7,0)`、global版は `(0,.6,0)` であり、offsetYと回転を混ぜて二重加算しない。

## 動作の再利用と再計画

| 区間 / データ | 再利用可能な部分 | 再計画・確認する部分 |
|---|---|---|
| Bの空手park・供給上方・同時下降/同時把持 | 機体と供給台・全UIDへ同じDを適用するなら元q、開度、時間、材料弧長の把持位置を候補として再利用 | 新側の床/枠/配管/隣ST、10本列の全実メッシュを照合。供給台を元位置に残すならこの区間も再IK |
| Bの供給からワークへの両手搬送 | 線長、実6R6/6R14、OD14、UID、二手の材点、既存曲げAPI | 始点は移した供給、終点は固定した製品。新しい両手target列・連続IK接続・速度/加速度・全frame meshが必要。元qや元wire root列を一括D変換して最終座へつないではいけない |
| Bの曲げ・J1 20 mm下降・T 40 mm下降・解放後180 mm同時上昇 | 製品local最終形、着座方向、同時開放、必要な開度契約 | 全両手IKと新側の進入/退避。H1右は28 mmで隣線干渉した履歴があり、20 mm→離隔後80 mmを根拠なく解除しない |
| B終了後の空手戻り・引出し回収 | 現行固定高さtimelineと連続動作の検査方法 | 新Bの終端parkが変わるためA→B/B→C、C loaded wait、引出しとの同時刻関係を新姿勢で照合 |
| A/C（今回側変更をしない場合） | 現q・FK・工具・UID bankを保持できる候補 | 新B固定設備・park・可動供給に対する変更域照合。干渉が出た範囲だけ再計画 |
| Cも反対側へ移す場合 | 供給器ごと移す取得区間、元直形工具・TCP/ソケット・ねじ進行仕様 | 固定製品のM6/M14座への全進入/締結/退避・供給へ戻る枝を再IK。body rollとspindle位相を混同しない。固定M6左/M14右を自動交換しない |
| OP040の新工程 | 既存＋X床基台、Yヨーク、元UR15 FK、部品local定義、汎用ledger/shape/export | 今の背景parkから新工程の拘束targetと経路を作る。旧背景工程動画をchecked bankとして昇格しない |

Bでは腕0=`T`端、腕1=`J1`端という機体上の役割を保持する。180°後の「画面左/右」を根拠にnode ID、H1/H2、J1/T、M6/M14を交換しない。供給列も180°回すだけなら中心線配列や端子名を反転しない。H2は `OP030B_H03_2_UID001`（row5）、H1は `OP030B_H03_1_UID005`（row4）である。

## native階層での注意

Blender frame1読取でも、`OP030B__source_0576` と `OP030B_wire_supply_fixed` は `OP030B_cell` の子だが、577/578、1067/1107、drawer、active wire root、JB、`source_0292` はparent無しでanimationを持つ。`op030_split_animation.bake_world` が明示的にunparentしてworld行列を焼いているためである。

従って親 `OP030B_cell` の回転だけでは、床基台と供給台は動いても腕・引出しが残る。また `OP030B_positioner_base_v04` もcellの子であり、親全体の回転はラインの位置決め機構まで巻き込む。**静的配置とpreparedのactor別world列の両方を、対象別の写像で作る必要がある。**

一方、C固定工具rootは元flange1067/1107の子、spindleは工具内部のlocal回転、wireのJ1/T端子はwire rootの子である。親と子へ二重にworld Dを加えず、`parent_world @ local_pose = expected_world` を確認する。位置決めピンのdriverはcarriage local Z `−.051..−.014` を参照しており、親を外してworld Zを流用しない。

## 誤回転・ID違い・残置を防ぐ検査案

1. 入力native/manifest/bankのSHAを固定し、新しい版へ出力。actorをline / robot / supply / held / installedの明示所有表で分類し、未分類を検出する。basename一致だけで移す対象を選ばない。
2. 新prepared全frameで製品R=Rzπ、パレットR=I、Z=.8845/.789、Y搬送連続をassert。組付済み全UIDの `inv(product) @ UID` は搬送中一定とし、B開始/終了/C到着で同一行列・同一端子名を照合する。
3. floor base576の新world座標と、bank577/578の原点を照合。床基台だけ・腕だけが旧側へ残るケースを検出。全78nodeについて元FK→新基台FK→native評価poseを照合し、poseの単純書換えだけでqを据え置かない。
4. 元visual名とside、末端1067/1107、精密指、カメラ、工具の対応表を検査する。reflection `det(R)<0`、部品CADのscale変更、left/right index入替えを禁止。カメラintrinsicsとflange相対姿勢を保持する。
5. 供給10本のUID集合・H1/H2個数・row選択・全端子フレーム・材料弧長を照合。所有を供給→左右手→製品と追跡し、解放・着座で姿勢が飛ばないことを確認。Cではspindle位相と保持/設置ナットworld姿勢を別項目で照合する。
6. 各可動actorの旧worldと新worldを照合し、固定設備・床・搬送機構は対象外world/局所mesh署名が一致することを確認。移設群の旧側AABBに同名cloneや古いstocker/driverが残っていないかを全visible meshから調べる。新側の電線・ホースは端点と支持の接続まで確認する。
7. OP040の `source_1171/1211` と `1213..1219` は、最新v04/v05で旧腕parkに伴う浮遊を修正しJBリブへ戻した枝線群である。`source_0354` も支持へ戻している。元の「腕38node以降はpuck/collar」の汎用追従を盲目的に再適用すると、この部品を工具として連れ去る。`downstream_restored_v04` の所有・world記録を基準に、新工程で扱う同一UIDへ明示的に接続する。
8. 新側の供給/進入/作業/同時退避/隣ST parkを実メッシュで検査。内部全体の除外ではなく既存のnamed contactを照合。A/C保存bankは新B固定・可動背景に対する差分検査、B新bankは全native30HzのFK/FCL/速度加速度、搬送はpayloadと機構を分けて確認する。

既存再利用可能な検査入口は `probe_op030_front_integration_v05.py`、`probe_op030_v05_background.py`、`probe_op030_split_a_payload.check`、`probe_op030_split_v04_transfer.check_fixtures`。ただし現コードのY並進専用処理、B drawerの符号、global offset、固定576・追従UID分類は新配置に合わせた別版が必要である。過去の合格数値を新側へ自動継承しない。

この文書はソース・配列・階層の読取と再利用範囲の整理であり、新配置の到達性、荷重、保持力、連続的干渉、全ライン物理妥当性の判定ではない。
