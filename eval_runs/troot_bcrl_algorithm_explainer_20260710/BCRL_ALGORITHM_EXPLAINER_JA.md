# THREAD における BC+RL アルゴリズム解説（現況版 v0.1a）

**著者:** PAPER-AUTHOR (w2:p9)　**日付:** 2026-07-11 00:1x JST（v0.1 = 07-10 23:58）　**HEAD:** `6e48d0a439`
**検証:** RS-TECH-LEAD (%12) 技術 cross-PV = **PASS**（2026-07-11 00:10、blocking なし。LOW 1 件 = §4.6(b) の cite `:16`→`:17` を v0.1a で修正済）
**種別:** 解説文書（paper-only / 0-commit / コード変更なし / 新規設計判断なし）
**[L-TRIAGE]** 新規ファイル作成 = L2 の質的トリガに該当。ただし本文書は `eval_runs/` 内の解説文書で、コード・config・挙動 surface はゼロ、設計判断を一切行わない（既に確定した事実の再記述のみ）。→ **final_L = L1**（p9 自己申告 → **RS-TECH-LEAD が CONFIRM、2026-07-11 00:10**）。gate = 本文書に対する %12 技術 cross-PV（PASS、2026-07-11 00:10）＋ Rs 最終 review。前例: `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md:7`（同種の降格申告、ただし当該 doc は設計提案のため L2）。

---

## 0. この文書の scope（最初に読むこと）

Rs 指示は「**いま**ここで使用されている BC+RL のアルゴリズムの解説」。したがって本文書は次の主従で書く。

| 区分 | 対象 | 本文書での扱い |
|---|---|---|
| **主（実装済・実測あり）** | R0 pure BC / OG offline gate / R1 off-path 教師 4 経路 / closed-loop runner | 現在形で記述。全記述に `file:line` または一次 JSON の根拠を付す |
| **従（Rs 承認済・未 build）** | R2 α residual / R3 RLPD / R4 | 「**設計として承認済、コード未実装**」と明記。**現在形で動作を記述しない** |
| **除外** | env6-VBD 系トラック | LEDGER で DISCARDED。歴史的言及のみ、現行アルゴリズムとして扱わない |

**「未 build」を明示する理由（本 project の規律）:** 記録がコードに先行する場合、その機構が runtime で ACTIVE か否かを区別しないと「見かけ上あるが物理的に未接続」の主張になる（GROVE rule 12 = ABSENT-IN-CODE）。本文書はこの区別を段階ラベルで担保する。

**⚠ 数値に関する注意（erratum 系譜）:** scripted route の公式成功率は **0.716（strict_v2 = 58/81）** のみである。過去に流通した 0.728 は C1 保持 leg を分子から落とした **ERRATUM 値**であり、引用してはならない。真値の系譜は 0.494 →（修正 3 世代）→ 0.716（LEDGER `00-DESIGN-STATUS-LEDGER.md:47`、packet `RS_W0APRIME_PACKET_20260705.md:34`）。

---

## 1. 問題設定 — 何を学習させようとしているのか

### 1.1 タスク

双腕（UR5e × 2、コ字型フィンガ）が、テーブル上の 8mm ケーブルを掴み、持ち上げ、クリップ C1 に着座させ、片手を持ち替えて次のクリップ C2 に着座させる。この **C1→C2 の経路全体を「1 つの学習単位」**として扱う（Rs directive 2026-07-01「(A) 経路全体」）。

- 基盤: env7 = Newton 1.2.1 / mujoco 3.8.1 SolverMuJoCo（`RS71-System-Spec-SSOT.md:15`）
- 不変前提 5 項（双腕 / 88mm 把持スパン / DiffIK のみ / コ字フィンガ幾何 LOCK / kinematic trick 禁止）は学習側からも変更不可（`RS71-System-Spec-SSOT.md:19-27`）

### 1.2 出発点 — 「動く scripted route」が既にある

学習の前に、**人手で書かれた scripted route（frozen script base）が既に動いている**。これが本 project の BC+RL 設計を他の一般的な設定と決定的に分ける。

- 公式成功率 **strict_v2 = 58/81 = 0.716**、Wilson95 信頼区間 [0.610, 0.803]（`RS_W0APRIME_PACKET_20260705.md:34`）
- 分子の定義（§運用29 準拠、predicate-complete）= 「C1 を保持し続けている ∧ C2 に正直に着座した ∧ SUCCESS 判定」
- 再現条件: 環境変数 `W0E_F1B_SNAPDOWN=1`、cuda:0 pinned

つまり本 project の学習は「ゼロから動作を獲得する」問題ではなく、**「7 割方動くスクリプトの、残り 3 割の失敗を埋める」**問題である。

### 1.3 忠実度の境界（RL が学べない範囲）

sim のケーブルは 40 節の剛体カプセル鎖で、各関節は **1 自由度の平面曲げ（曲げ平面 = 鉛直）**である（`RS71-System-Spec-SSOT.md:53-54`）。したがって：

- **鉛直方向のたるみ（sag）は動力学的に表現される**
- **水平方向のルーティング曲率は表現されない** → 5 クリップの千鳥配置を縫う水平曲げは **kinematic**（掴んで引きずる + クリップ保持ピン）で実現されている

**帰結:** RL は「sim に存在しない物理」を学習できない。したがって水平ルーティング区間で学習が獲得しうるのは幾何・タイミング・接触の調整であって、ケーブルの水平曲げダイナミクスではない。これは欠陥ではなく Rs が受容した忠実度境界である（Rs DECISION B2）。

---

## 2. 全体設計思想（through-line）

すべての段（rung）に共通する 1 行の原理は：

> **「信頼済みの凍結 base ＋ 小さな学習部品 ＋ 参照 anchor 付きの探索 ＋ 較正済み critic ＋ gate された更新」**
> （`BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md:89`）

```
                                     ┌───────────────────────────┐
             観測 obs ──────────────▶│  frozen BASE (scripted)   │──▶ base 行動 ┐
                                     └───────────────────────────┘             │
                                                                               ├─▶ 合成 ─▶ DiffIK ─▶ sim
                                     ┌───────────────────────────┐             │
             観測 obs ──────────────▶│  小さな学習 policy         │──▶ Δ / 提案 ┘
                                     │  (+ critic は R3 以降)     │
                                     └───────────────────────────┘
                                        ▲ anchor: ‖Δ‖ 上限（非累積）
                                        ▲ gate  : 性能 drop 監視 / rollback
```

base を script → BC → （将来）vision/VLA と差し替えても同じ原理でスケールする、という設計意図である。文献側の裏付けは §9 に示す。

---

## 3. LADDER — 段階の地図

| 段 | 名称 | 状態 | 一言 |
|---|---|---|---|
| **R0** | pure BC（純模倣） | ✅ 実装済・実測完 | **問題の定義になった**（copycat であることが判明） |
| **R1** | 模倣 + off-path 教師 | ✅ 実装済・実測完 | 4 経路すべてが同じ壁に収束 → CLOSE |
| **R2** | 基本 BC+RL | ⏸ **Rs 承認済 設計・未 build** | α = residual-on-frozen-script |
| **R3** | off-policy SOTA 並走 | ⏸ **Rs 承認済 設計・未 build** | RLPD（+ IBRL 型 proposal） |
| **R4** | 超える | 探索ラベル（未確定） | THREAD 固有資産 |

段の定義は `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md:128-159`。R2/R3 の承認は Rs W0-a′ 一括承認（LEDGER `:47`、commit `b7d7857dfc`）。

---

# 第 I 部 ── 実装済みのアルゴリズム

## 4. R0: pure BC（行動クローニング）

### 4.1 データの作り方

scripted route を 1 本走らせ、各フレームの状態を記録した `route_demo_raw.npz` を作る（demo recorder、LEDGER `:45`）。これを `route_demo_to_bc.py` が (観測, 行動) の教師対に変換する。

- ケーブル位置に **±20mm の XY オフセット**を与えた複数の録画から学習データを作る
- オフセットは whitelist で管理される: 外殻 6 点 `{(20,0),(-20,0),(0,20),(20,-20),(-20,20),(-20,-20)}`（`route_demo_to_bc.py:522`）と内部 5 点 `{(0,0),(10,0),(-10,0),(0,10),(0,-10)}`（`:523`）
- オフセットの真の出所は npz の meta（`env_gates.CABLE_XY_OFFSET`）であり、ディレクトリ名はフォールバック（`:552-572`）

### 4.2 観測ベクトル（obs）— 12 + フェーズ数

観測は次の 4 ブロックの連結である（組み立ては `route_demo_to_bc.py:286`、レイアウト定義 `:448-451`）。

| 次元 | 内容 |
|---|---|
| `[0:3]` | 右手エンドエフェクタ位置 |
| `[3:6]` | 左手エンドエフェクタ位置 |
| `[6:9]` | **注目するケーブル節点の位置**（どの節点かは §4.4） |
| `[9:12]` | 次に狙うクリップの xyz（C1_PIN までは C1、以降 C2。z = 0.829） |
| `[12:12+n]` | フェーズの one-hot（n = 13 または 15） |

合計 **25 次元（13 フェーズ）または 27 次元（15 フェーズ）**。フェーズ表は `PHASES13`(`:40-54`) / `PHASES15`(`:58-74`) の 2 スキーマのみ許可され、それ以外の長さは即停止する（`:96-107`）。

### 4.3 行動表現 — なぜ「絶対目標」なのか

行動は 6 次元（右手 xyz + 左手 xyz、順序 `(Rx,Ry,Rz,Lx,Ly,Lz)`、`:134`）。表現には 2 モードがある。

**(a) delta モード（初期の既定）**
`a = (次フレームの EE 位置 − 現フレームの EE 位置) / POS_ACTION_SCALE`（`POS_ACTION_SCALE = 0.015`、`:33`, `:369-371`）

**(b) abs モード（現行採用。E15 / fork-(iv)）**
フェーズ×軸ごとに `[lo, hi]` の箱を作り、次の waypoint の**絶対**目標位置を `[-1,1]` にアフィン写像する：

```
a = 2·(wp − lo) / (hi − lo) − 1        (route_demo_to_bc.py:180-183)
箱は各フェーズの実データ範囲に margin 0.10、最小幅 0.030 m を課して構築 (:132-133, :137-177)
|a| ≤ 0.95 を assert (:487)
```

**なぜ切り替えたか（重要）:** delta 表現では、実行時に `目標 = 現在位置 + a·scale` として **差分を積分していく**。BC の微小な予測誤差がステップごとに蓄積し、開ループ 5 本すべてが reach wall に達した（把持スパンが 88mm から 122.9mm へ崩れ、把持力 0N）。これは「conservative-definite な失敗」として bank されている（devplan `:25`）。

絶対目標表現は各ステップで **絶対 anchor に再固定される**ため、この積分病理が構造的に起きない。実測でも、開ループ誤差が一度 433mm に跳ねた後に 9–16mm へ再収束する（re-anchoring）ことが確認され、Rs が正式採用した（LEDGER `:46`、DQ6 CLOSED）。

> これが本 project の BC における**唯一かつ最重要の表現上の設計判断**である。

### 4.4 「どのケーブル節点を見るか」— `_seg_rule`

obs `[6:9]` に入れる節点はフェーズ依存で切り替わる（`route_demo_to_bc.py:110-128`）。

| フェーズ | 選ぶ節点 |
|---|---|
| p ≤ 4（把持接近〜C1 へのルート） | 右手に最も近い節点（`:118-119`） |
| p ≤ 6（C1 着座・ピン） | 着座節点（= ピン節点 − 28）（`:120-121`） |
| p ≤ 8（左半開放・右上昇） | 左手が握っていれば左の保持節点、でなければ右最近傍（`:122-125`） |
| それ以降（C2 誘導〜整定） | **C2 の xy に最も近い節点**（`:126-128`） |

この規則は後に R1 で疑われることになる（§6.4）。

### 4.5 ネットワークと学習

学習の実体は `bc_pretrain.py`、それを薄く包むのが `bc_train_route.py`。

| 項目 | 値 | 根拠 |
|---|---|---|
| ネットワーク | RSL-RL `ActorCritic`、actor/critic とも MLP 隠れ層 `(128,128)`、活性化 `elu`、行動 6 次元 | `bc_pretrain.py:41-49`, `bc_train_route.py:74` |
| BC が使う部分 | **actor の平均出力のみ**。critic は未学習（後段 PPO 用に温存） | `bc_pretrain.py:107` |
| 損失 | `MSELoss`（予測行動 vs 教師行動） | `bc_pretrain.py:96,107-108` |
| 最適化 | Adam、**actor パラメータのみ**、`lr = 1e-3` | `bc_pretrain.py:94-95` |
| バッチ | 256、エポック既定 100 | `bc_train_route.py:78,45` |
| 正規化 | **obs・action ともに正規化なし**（action の正規化はデータ側のアフィン写像で済んでいる） | `bc_pretrain.py:71-72,107` |
| 学習/検証分割 | ランダム行分割 10%（内部プロキシ）。加えて **デモ丸ごと holdout** を正式な検証とする | `bc_pretrain.py:54,78-83`, `bc_train_route.py:81-95` |
| 乱数固定 | seed（既定 0）で torch / numpy / random / cuda を固定 | `bc_train_route.py:59-63` |

「ランダム行分割の val は同一デモの隣接フレームが両側に入りうるため楽観的になる」という認識から、**別デモ丸ごとの holdout を authoritative に置く**という設計になっている点は、この実装の良い性質である。

### 4.6 R0 の結果 — 「デモを写す力はある。軌道から外れると無力」

**(a) デモを写す力は本物である。** 学習した BC は、未見のオフセット（(0,0) と (−10,0) のデモ丸ごと holdout）に対して、**同一デモを 9 回複製しただけの null モデルより検証 MSE で約 18 倍良い**（BC 0.000659 vs null 0.011979、RMSE では約 4 倍。`b2_cpD_report.md:14`）。学習量・アフィン変換・seed・エポック・GPU をすべて揃え、**唯一の差はケーブルオフセットの多様性**である。したがって「BC は 9 種のオフセットに転移する写像を学んでいる」は事実である。

**(b) しかし、軌道から外れると戻れない。** 同じ report は「この 18× の差は null_beat（§5.6）を強く予測するが、18× 自体は γ⊥ 指標ではない」と明記して事前登録していた（`b2_cpD_report.md:17`）。

**(c) そして予測は外れた。** 後段の正式な γ⊥ ベース null_beat は **−0.261**（= null に**負けている**）だった（`b2_cpE_og/bc/og_gate.json`。内訳: null 側 worst 2.236 − 本 policy の worst 2.497 = −0.261）。

> **この食い違いこそが R0 の核心的発見である。** 「デモ行動の予測が上手いこと」と「外れた状態から復元できること」は**別の能力**であり、前者の 18 倍の優位は後者を一切保証しない。
> （注: 2 つの null は構成が異なる〔前者 = 1 デモ 9 回複製（`b2_cpD_report.md:16`）／後者 = 13 回複製（`og_offline_gate.py:39`）〕ため両数値は直接比較しない。比較しているのは「どちらの指標でも null を上回るか」という質的な帰結である。）
>
> なお `BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md:24` の「BC on-path 汎化 18×」という記載は locator としては source に忠実である（on-path の限定詞が付いている）。本節はそれを精密化するものであって、計画書や LEDGER の記載を訂正するものではない（%12 裁定、2026-07-11）。

(b)(c) を定量化するのが次章の OG gate である。

---

## 5. OG offline gate — GPU を使わずに「戻す能力」を測る

### 5.1 何のための計器か

BC policy を実際に sim で転がす（rollout）と GPU 時間が高くつく。OG gate は **sim を一切回さず**、学習済み policy に対して「観測を人工的に摂動して、出力目標がどう動くか」だけを見る **0-GPU の事前判定器**である（`og_offline_gate.py:5-14`）。判定が STOP なら GPU rollout に進まない。

評価対象は「policy の出力を実際の実行と同じ経路でデコードしたもの」= `actor(obs)` の平均 → `[-1,1]` にクリップ → フェーズ別アフィン逆変換（`og_offline_gate.py:12-13,68-77,324-333`）。

### 5.2 OG-a — waypoint 再現精度

フェーズ×軸ごとに誤差 `err_mm = (予測目標 − 真の waypoint)·1000`（`:334`）を集計し、RMSE と p95 を出す（`:346-347`）。判定は重要フェーズで p95 > 5mm なら STOP、着座 z 軸は RMSE ≤ 1.0mm で GO、など（`:25-30,56-65`）。

これは「デモをなぞれるか」を見るだけで、**「外れたら戻れるか」は見ていない**。

### 5.3 OG-b — γ∥ と γ⊥（本 gate の核心）

各ステップで、EE 位置を ±2mm（および ±10mm）動かし、policy の出力目標がどれだけ動くかを**中心差分でヤコビアン** `J = d(目標) / d(EE)` として測る（`:99-109`）。把持後は、保持している側の腕を動かすとケーブル節点の観測も一緒に動く、という物理的整合性も再現される（`_holder_axes`, `:51-53,98-106`）。

デモ軌道の接線方向を `t̂` として、

- **γ∥ = ‖J·t̂‖** … 軌道**に沿う**方向の追従ゲイン（`:116`）
- **γ⊥ = 接線直交部分空間に射影した J の最大特異値** = `svd(J·(I − t̂t̂ᵀ))[0]`（`:117`）

**直感:** γ⊥ は「軌道から横に押されたとき、policy の目標も一緒に横にずれてしまう度合い」である。

- γ⊥ ≈ **0** → 押されても目標は動かない = **元の軌道に引き戻す（restoring）**
- γ⊥ ≈ **1** → 押された分だけ目標も動く = **ずれをそのまま追認する（積分器 / copycat）**

合格帯は **γ⊥ ≤ 0.5 で GO、≥ 0.9 で STOP**（`:36`, `:418-422`）。

### 5.4 OG-b′ — 収縮 probe

デモの waypoint から ±5mm ずらした 6 点を初期値に、`x_{k+1} = decode(π(obs(x_k)))` を 5 回反復し、ずれが縮むか（contracted）を見る（`:145-215`, `:159-162`）。閉ループの安定性を sim なしで近似する。

### 5.5 pair metric — 「標的が動く」フェーズ用

C2 再把持フェーズでは、右手が狙う対象（ケーブル）が、左手が持っているせいで**動く**。この状況で単一の γ⊥ は符号の意味を失う。そこで 2 つのゲインに分解する（`:34,240-283`）。

| 指標 | 定義 | 望ましい値 |
|---|---|---|
| **seg-following gain** | ケーブル（左手 EE + 節点）を動かしたときの右手目標の追従量 | **≈ 1**（動くケーブルに追従すべき） |
| **ee-only gain** | 右手 EE だけを動かし、ケーブルは固定したときの右手目標の追従量 | **≈ 0**（自分のずれは復元すべき） |

合格帯は `0.8 ≤ seg ≤ 1.2` **かつ** `ee_only ≤ 0.3`（`:37-38,271-276`）。

### 5.6 null_beat — 「そもそも学習しているか」

学習データを 13 回複製しただけの null モデル（= 入力を無視して平均を吐く degenerate policy）に対する優位量。`null_beat = null の worst 指標 − 本 policy の worst 指標` で、**0.15 以上**を要求する（`:39,425-443,457`）。

### 5.7 総合判定

3 段の優先順で決まる（`:445-477`）：

1. carried でない STOP が 1 つでもあれば → **STOP**
2. 4 条件すべて成立 → **GO**
   （`oga_no_stop` ∧ `movable_all_GO` ∧ `cable_pair_PASS` ∧ `null_beat ≥ 0.15`）
3. それ以外 → **BLOCKED_FOR_USER**

結果は `og_gate.json` に構造化出力される（`:478-522`）。

### 5.8 R0 policy の実測（一次データ: `b2_cpE_og/bc/og_gate.json`）

| 指標 | 実測 | 合格帯 | 判定 |
|---|---|---|---|
| γ⊥ GRASP_HOVER | **2.497** | ≤ 0.5 | STOP |
| γ⊥ GRASP_DESCEND | **1.257** | ≤ 0.5 | STOP |
| γ⊥ GRASP_CLOSE | **1.041** | ≤ 0.5 | STOP |
| γ⊥ LIFT | **1.055** | ≤ 0.5 | STOP |
| pair seg-following | **0.282** | [0.8, 1.2] | STOP |
| pair ee-only | **0.973** | ≤ 0.3 | STOP |
| null_beat | **−0.261** | ≥ 0.15 | FAIL |
| C2_REGRASP 収縮 | 5.0mm → **5.525mm** | 縮む | 発散 |
| **総合** | | | **STOP** |

**読み方:** γ⊥ ≈ 1.0〜2.5 は「押された分をそのまま追認する」を意味し、pair の `ee_only 0.973 / seg 0.282` は「**自分のずれは直さないのに、ケーブルの動きには追従しない**」= 完全に逆である。そして null_beat が負 ＝ **入力を無視する degenerate policy に負けている**。

結論は 1 行で言える：**この BC は、観測から状態を読んで行動を選んでいるのではなく、自分の直前の EE 位置と行動の相関を写している（copycat）。**

---

## 6. R1: off-path 教師 — 4 経路すべてが同じ壁に収束した

「off-path で戻れない」なら、off-path のデータを与えればよい。これを 4 通り試した。**結果はすべて同じ壁だった。**

### 6.1 経路 1 — B2: DR で多様性を増やす

±20mm のオフセット録画を増やして学習。→ 形式的 OG gate は **STOP 過剰決定**（movable γ⊥ すべて > 0.5、null_beat −0.261）。仮説「復元能力 = データ多様性の不足」は **REFUTED**（LEDGER `:46`）。

### 6.2 経路 2 — (iv): 合成摂動でデータ拡張

デモ状態を人工的にずらし、「正しい戻り行動」をラベルとして合成（`route_demo_to_bc.py:1044-1152`、既定 OFF）。→ 妥当性判定 3/3 未達。しかも**摂動を小さくすると悪化する**という、拡張幅の調整では消えない構造的緊張が出た。conservative-definite な STOP として bank（LEDGER `:46`）。

### 6.3 経路 3 — (ii): kick-and-recover（物理的摂動）

sim 上で実際にひと蹴り入れ、その後の**復帰フレームだけ**を教師にする（kick 窓のフレームを落とす: `route_demo_to_bc.py:320-352`）。

→ **機構としては効いた**：γ⊥ {GRASP_DESCEND} が 1.257 → 1.098 → 1.056 と単調に下がる。しかし **1.05 付近で頭打ち**（合格帯 0.5 の 2 倍）。改善量は 2 録画で −0.159、続く 10 録画で −0.042 と逓減（LEDGER `:46`）。

### 6.4 経路 4 — obs-switch: 「見ている節点が間違っているのでは？」

C2 再把持フェーズで、obs が渡す節点は「クリップ中心に最も近い節点」(`_seg_rule:128`) だが、右手が実際に狙うのは「把持レーン（C2 中心 ± 44mm）に最も近い節点」である。約 44mm ずれた**別の節点**を見ていた。→ obs を実際の狙いに合わせて切り替えて再学習。

→ **REFUTED**。seg 0.249 → 0.24（実質不変）、ee_only 0.973 → 0.958（依然 STOP）（LEDGER `:46`）。

### 6.5 4 経路の収束 — 何が確定したか

| 経路 | 仮説 | 結果 |
|---|---|---|
| B2 | データ多様性の不足 | REFUTED |
| (iv) | 合成摂動で教えられる | STOP（構造的緊張） |
| (ii) | 物理摂動で教えられる | 機構は効くが plateau ~1.05 |
| obs-switch | 観測対象の取り違え | REFUTED |

さらに **capacity pre-test は PASS**（ネットワーク容量の問題ではない）。

> **確定した結論:** 純粋な BC は、off-path からの復元（restoring）を合格水準まで教えられない。原因はデータ量でも容量でも観測対象でもなく、**BC の目的関数そのもの**（デモ分布上の教師付き回帰）にある。

これが R2 で強化学習の項を入れる根拠である。DAgger 系の追試（β=0）は単調発散を示したが、これは「予算不足」と「専門家が状態盲」のどちらが原因か切り分けられず、**A-vs-B は未解決のまま R1 を CLOSE**（Rs 判断、LEDGER `:47`）。この未解決は将来 oracle が動いた時点で named probe として再検証するよう事前登録されている。

---

## 7. closed-loop runner — 学習した policy を実際に走らせる

`policy_route_runner.py` が学習済み policy の閉ループ実行を担う。

- **決定論的**: `torch.no_grad` 下で actor の**平均**を取り、分布を作らない（＝サンプリングしない、`:215-229`）
- **観測の再構成**: 実行時に obs を学習時と同一レイアウトで組み立てる（`:200-212`, `:788-803`）
- **行動の適用**: abs モードならフェーズ別アフィン逆変換で絶対目標へ（`:811-813`）、delta モードなら `目標 = EE + a·scale`（`:816-818`）。いずれも `solve_ik_dual` を 1 回解き、関節差分を 10 フレームに補間して適用（`:836-885`）
- **安全弁 1（t=0 canary）**: 初手の目標が現在 EE から 30mm 以上離れていたら即異常終了（`:819-824`）
- **安全弁 2（guard-2）**: 1 ステップの目標移動量が 15mm を超えたら、方向を保ったまま 15mm に縮める（`:55,825-835`）
- **fail-closed**: 学習 policy を走らせるには `--rs-go` トークンが必須（`:1529-1534`）、sha ピンや cadence（=10）も assert（`:149-167,346`）

---

# 第 II 部 ── Rs 承認済・未 build の設計

> **以下はすべて「設計として Rs に承認されているが、コードは存在しない」。現在動いている挙動ではない。**
> 承認: W0-a′ packet v1.1 一括承認（2026-07-06、LEDGER `:47`、commit `b7d7857dfc`）

## 8. R2: α = residual-on-frozen-script（承認済・未 build）

### 8.1 何をする設計か

凍結した scripted route を base とし、学習 policy はその**絶対目標に対する 1 ステップぶんのオフセット Δ** だけを出力する（`RS_W0APRIME_PACKET_20260705.md:45`、DC-1 = α 採択、Rs 2026-07-06 08:3x）。

### 8.2 Δ 非累積契約（最重要の hard 要件）

R0 の delta モードが破綻した機構（§4.3）が residual channel の中で再現しないよう、**Δ は base の絶対目標への per-step offset であり、積分してはならない**。`Δ = 一定 → drift = 0` の回帰テストを env の DoD に含めることが義務づけられている（`P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md:30`）。

### 8.3 α の必須機構 3 点

「完全状態が観測できる sim で、位置 DR だけを与えたら residual の最適解は 0 になってしまう」という批判（M-C）に対し、次の 3 点が必須要素として設計に組み込まれている（`P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md:32`、packet `:45`）。

1. **oracle による drift-recovery relabel** — base 近傍から逸脱したときの復帰教師（ただし oracle は script 忠実であり、base 自体が失敗する corner の修正は教えられない、と限界が明記されている）
2. **構造化 common-mode 探索による局所 RL 発見** — 腕ごとに独立なノイズを乗せると把持スパンが壊れて即終了するため、**両腕共通成分（common-mode）主体**にノイズを構造化する。発見確率 `p_hit` を事前計算して discharge 条件に加える
3. **発見不能領域の draw 会計** — 幾何的に勝てない cell（bow-chord 112mm > スパン窓）は「引き分け」として扱い、DR の台から除外して limitation として文書化する

補足として、**恒久原則 0**：双腕の対量に作用する全機構（探索ノイズ / クランプ / rate-limit / relabel / obs-DR）は **common-mode と differential に分解して設計し、differential 成分は正当化なしに導入しない**（`:63`）。これは同型の事故が 3 件収束した結果として昇格した原則である。

### 8.4 env の契約（承認値）

| 項目 | 値 | 根拠 |
|---|---|---|
| 観測 | **62 次元**（57D → 60D → 62D と 2 度改訂。`[60]` C1 域 cable-z、`[61]` C1 flank 最大 z を追加） | `P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md:133`（Rs、v1.5g） |
| 行動 | **6 次元 position-only residual**（回転次元は近似不活性のため除外を推奨、DC-1s3） | packet `:47` |
| グリッパ | 行動次元に**含めない**（scripted 2 段サーボの predicate） | spec `:51` |
| horizon | **900 RL step**（canonical 実測 max 771 に ×1.17 の余裕） | packet `:62` |
| 報酬 | **sparse 主体** — フェーズ完了 predicate G1–G6 + 終端 SUCCESS + 時間罰 −0.01/step | spec `:67` |
| 成功条件 | **strict_v2 の完全 mirror**（C2 正直着座を K=10 持続 ∧ C1 保持 ∧ 非落下 ∧ 順序 gating ∧ スパン guard） | spec `:68` |
| 終了 | success ∨ timeout(900) ∨ explosion ∨ drop。`time_outs` は **timeout のみ**（value bootstrapping 汚染の禁止） | spec `:69` |

**報酬の健全性検算（§運用22）:** 正の予算 = 5×5（G1–G5）+ 200（G6）= 225、罰の最悪累積 = 0.01×900 + 10 = 19 → 比 1:11.8（`spec:67`）。dense な距離整形は初期不採用（過去の hover デッドロックの教訓）。

**フェーズ predicate（G1–G6）:** G1 cage（フィンガ閉 ∧ 接触 ∧ スパン 92.4mm）→ G2 lift（静置時からの持ち上げ +40mm）→ G3 C1 着座（<3mm ∧ ピン発火）→ G4 再把持成立 → G5 C2 着座（<3mm）→ G6 SUCCESS（G5 を 10 step 持続）。latch 済みで一度だけ発火し、取り消されない（`P2_REWARD_ARTIFACTS_W0C_DRAFT_20260705.md:10`）。

> **⚠ 88mm と 92.4mm の区別（混同注意）:** 不変前提 #2 の「88mm」は**指令値**（`GRIP_HALF_SPAN 0.044` × 2）である。一方 G1 と span guard が見るのは**実測の achieved coupling スパン = 92.4mm**（81 cell × dual-grip フェーズで [92.38, 92.42]、packet `:39`）。設計初期に窓を 88±5mm で置いたのは**中心の誤り**であり、実測 92.4 に対して余裕が 0.6mm しかなく DR 下で G1 が永久に発火しない episode を生む、と訂正されている（`P2_REWARD_ARTIFACTS_W0C_DRAFT_20260705.md:10`）。指令値と実測値を取り違えないこと。

### 8.5 未解決の設計論点

- **phase-clock（CRIT1）**: base が時間で進む間に Δ がケーブル状態を変えると同期が壊れる。逸脱が閾値を超えたら base を止めて oracle に問い直す案 (b) が推奨だが、Rs 決定待ち（packet `:58`）
- **OG gate の移植**: 現在の OG の検証実績は「27 次元 obs / 6 次元絶対目標」契約の上でのもの。契約が変われば**検証状態はリセットされる**。さらに composite（base + Δ）では Δ→0 のとき γ⊥ ≈ 0 となり、**壊れた residual を GO と誤判定する縮退**が起きる。移植と再検証が完了するまで OG を abort 規則に使わないことが明記されている（devplan `:117-121`、spec `:90`）

---

## 9. R3 / R4（承認済・未 build、および探索）

**R3 既定 = RLPD**（DC-2、packet `:50`）: SAC + 「各バッチの 50% をデモ、50% をオンライン replay から取る対称サンプリング」+ critic の LayerNorm + アンサンブル + 高 UTD。**offline 事前学習を行わない**のが設計点であり、そのため Cal-QL / WSRL は条件付き部品に留まる。

そこに **IBRL 型の提案機構**（凍結 policy の提案と RL の提案を Q で選ぶ）を、caveat 付きで併設する。caveat の中身は正直に記録されている：IBRL の検証済み形は「scripted demo で訓練した **IL policy** を提案に使う」であり、**script oracle を直接提案にするのは THREAD 独自の未検証変形**である（KN `:35`、devplan `:66`）。したがって fallback として BC policy を提案に使う arm を併設する。

さらに **horizon 対策を最低 1 本、R3 の設計時に事前登録する**（Q-chunking / JSRL 型 roll-in / demo 状態からの reset curriculum のいずれか）。文献の一致点は「10–100K step 級の手法をそのまま whole-route 単段に適用してはならない」である（KN `:116`）。

**R4** は探索ラベル。ただし「stage 分解」は前提変更に触れるため、提案時に STOP-and-flag の手続きを踏むことが決められている（devplan `:159`）。

---

## 10. 文献との対応（なぜこの構成なのか）

調査記録は `06-Knowledge/KN-BCRL-Frontier-2026-07.md`（17 検索 / 60+ 一次ソース）。

| 本 project の部品 | 文献上の系譜 | 採否と理由 |
|---|---|---|
| 凍結 base + per-step residual | **ResiP** (arXiv:2407.16677) / Residual off-policy (arXiv:2509.19301) | **R2 の実体**。「chunked BC = 開ループ計画器、residual = 反応性の補完」という分解が核 |
| BC 正則化付き on-policy PG | **canonical DAPG** (RSS 2018, arXiv:1709.10087) | 名称の混同を訂正済み。DAPG は residual 構造では**ない**。R2a として contingent（R2b 不合格時のみ） |
| 50/50 replay + LayerNorm critic | **RLPD** (ICML 2023) | **R3 既定**。事前学習なしで最初から online が設計点 |
| 凍結 IL policy を提案に、Q で選択 | **IBRL** (arXiv:2311.02198) | R3 に caveat 付きで併設。布 Hang 85% = 変形物体への適用証拠 |
| offline 事前学習の dip 対策 | Cal-QL (NeurIPS 2023) / WSRL (ICLR 2025) | **条件付き**。「再較正すべき事前学習 Q がある」ときのみ意味を持つ |
| 凍結 base + 小 head + 参照 anchor | **RL Token** (arXiv:2604.23073) | 実ケーブル精密作業（zip-tie / Ethernet / charger）での 2026 年の直接証拠。R3 構造の同型 |
| 長 horizon の advantage 条件付け | RECAP / π*0.6 (arXiv:2511.14759) | R4 の発想源。5B VLA 前提のため数値は借りない |

**成立性の確認（Gap 判定）:** 「demo で補強した **RL** で、**双腕**の**クリップ経路全体**を端到端」に相当する公開事例は **ゼロ**（2026-07 時点、上記探索範囲）。最も近いのは単腕・RL なしの階層 IL によるケーブル routing（IEEE T-RO 2024）と、stage 局所 RL の RL Token である（KN `:89`）。

**保守性の注記:** 上記実機系の結果は THREAD sim への直接転移を保証しない。algorithm class の成立性の証拠としては **non-conservative**（現実 → sim 方向の壁: 接触モデル差、horizon 長）である（KN `:115`）。

---

## 11. 現況サマリ

| 要素 | 状態 | 一次根拠 |
|---|---|---|
| scripted route（凍結 base 候補） | 動作、SR **0.716** | packet `:34` |
| BC データ変換器 / 学習器 / runner | 実装済 | `route_demo_to_bc.py` / `bc_train_route.py` / `policy_route_runner.py` |
| 絶対目標 action 表現（fork-(iv)） | **採択済・実装済** | LEDGER `:46` |
| OG offline gate | 実装済・稼働 | `og_offline_gate.py` |
| pure BC の性能 | デモ予測は null の 18×、しかし **off-path で STOP**（copycat） | `b2_cpD_report.md:14` / `b2_cpE_og/bc/og_gate.json` |
| off-path 教師 4 経路 | すべて壁に収束、R1 CLOSE | LEDGER `:46-47` |
| R2 α residual | **設計承認済・未 build** | packet `:45`, LEDGER `:47` |
| R3 RLPD | **設計承認済・未 build** | packet `:50` |
| whole-route RL env（P2） | 建設中（env-core 完了、route-executor 進行中） | LEDGER `:47` |

**律速はアルゴリズムではなく env である。** whole-route の RL 環境が存在しないことが、R2 以降に進めない唯一の構造的理由である（devplan `:51`）。

---

## 12. 用語集

| 用語 | 意味 |
|---|---|
| **BC**（行動クローニング） | デモの (観測, 行動) を教師付き回帰で写す |
| **on-path / off-path** | デモ軌道の上 / 軌道から外れた状態 |
| **restoring** | off-path から元の軌道へ戻す能力 |
| **copycat** | 観測から状態を読まず、自分の直前の動きの相関を写す退化 |
| **γ⊥** | 軌道に直交する方向の追従ゲイン。0 = 復元、1 = ずれの追認 |
| **null_beat** | 入力を無視する degenerate policy に対する優位量 |
| **residual** | 凍結 base の出力に足す小さな補正 Δ |
| **非累積契約** | Δ を積分せず、毎ステップ絶対目標に対する offset として適用する規約 |
| **common-mode / differential** | 双腕に共通な成分 / 左右差の成分 |
| **draw class** | 幾何的に勝てない初期条件。引き分けとして会計する |
| **strict_v2** | 成功判定の分子（C1 保持 ∧ C2 正直着座 ∧ SUCCESS）。predicate-complete |
| **conservative / non-conservative** | sim が現実より難しい / 易しい。前者の FAIL は確定的、後者の PASS は要追試 |

---

## 13. 根拠一覧（本文で引用したもの）

**設計 SSOT**
- `thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md`（成否 SSOT）行 43/45/46/47
- `thread-vault/04-Specs/RS71-System-Spec-SSOT.md` §0 (:19-27), §4 (:53-54), :15
- `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md`
- `.../RS_W0APRIME_PACKET_20260705.md`（Rs 決定 packet v1.1 + amendment）
- `.../P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md`（env spec v1.5〜v1.5g）
- `.../P2_REWARD_ARTIFACTS_W0C_DRAFT_20260705.md`（G1–G6 predicate）
- `thread-vault/06-Knowledge/KN-BCRL-Frontier-2026-07.md`（文献調査）

**実装**
- `thread_isaac_lab/scripts/route_demo_to_bc.py`（demo → BC データ変換、1220 行）
- `thread_isaac_lab/scripts/bc_train_route.py` + `bc_pretrain.py`（BC 学習）
- `thread_isaac_lab/scripts/og_offline_gate.py`（OG offline gate）
- `thread_isaac_lab/scripts/policy_route_runner.py`（閉ループ実行、1554 行）

**一次実測データ**
- `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/b2_cpE_og/bc/og_gate.json`（R0 BC の OG 判定）
- `.../b2_cpD_report.md:14`（on-path 汎化 18×）

---

*v0.1 初版 — PAPER-AUTHOR (w2:p9), 2026-07-10 23:58 JST.*
*v0.1a — 2026-07-11 00:1x JST. %12 cross-PV PASS 反映（§4.6(b) cite `:16`→`:17` / null 構成差の cite 明示 / devplan:24 は訂正対象でない旨を明記 / L-TRIAGE L1 = CONFIRM 反映）。*
*paper-only / 0-commit. 設計判断ゼロ（既存の確定事実の再記述のみ）。scope の最終権威 = Rs。*
