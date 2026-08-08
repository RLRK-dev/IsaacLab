# ITEM 7 — 取付（mounting）menu v0.1（p5 組成・settle は Rs）

**地位**: Rs 指示「**p5 に menu を組ませて**」（p4 卓 `9e3d21d6` 2026-08-08 10:43:48 JST・len=15・p18 first-hand 検証 `m-p18-75`）。**scope = menu 組成のみ** — run 0・training 0・実行 0・⛔ **推奨を書かない**（settle = Rs・p4 の artifact は「material であって recommendation でない」を保存）。
**材料（全て tracked・p4 測定・as-read 2026-08-08 10:47-10:50）**: `p4_ur15_sim_20260727/` の `GRID_24_VS_240_20260802.txt`・`CROWN_SWEEPS_240_READING_20260802.md`・`CROWN_AT_PASSING_MOUNTING_20260802.txt`・`GRASP_CENTRE_240_READING_20260802.md`・`WORK_ROW_240_READING_20260802.md` ＋ DDR **#54/#57/#60**（`:158`/`:161`/`:164` as-read）。
**測定の共通単位**: 240 draws・start-pose 段の**証人**（witness = L clear ≥1 ∧ R clear ≥1 ∧ pair 分離）。⛔ **witness pose pair ≠ route**（p4 逐語・全 option 共通）。

---

## §1 決定の構造（axes — menu の行はこの組合せ）

| axis | 現物（built） | 動かすと |
|---|---|---|
| mounting = spread × tilt | **0.220 / 45°** | cell 再構成 |
| crown 半径 | **0.110 m**（⚠ **写真由来の設計値**・reference asset に collision shape 無し — #60・`sweep_mounting.py:3-5`） | **変更可否そのものが Rs 裁定**（実 cell 忠実性） |
| grasp centre x | 現状 | cable 上の把持対の移動（cell 不変） |
| work row y | +0.280 | 作業列の移動（cell 不変） |
| **#54 部材** | **無い**（支柱-腕 298 mm 空隙） | **入力 未決・全 clearance 数値は部材を含まない**（計器は黙って除外） |

**built cell の現況（基準点）**: L **0 clear**（24→240 で solved 8 倍・clear 0 のまま = sampling でない）・R 19・chosen pair +26.2。⇒ **現物のままでは左腕の clear start pose が無い** — menu はこれを開く選択肢の一覧。

## §2 witnessed options（全て 240 draws の実測・行 = 選べる形）

### family A — **cell を一切変えない**（mounting・crown とも built のまま）
| opt | 動かす量 | 値 | L clear / R clear | witness gap | 未解像 |
|---|---|---|---|---|---|
| A-1 | grasp centre x | **−0.150** | 15 / 3 | **+10.7 mm** | 境界 −0.100〜−0.150 未 sample |
| A-1′ | grasp centre x | **−0.200** | 31 / 4 | **+10.7 mm** | （−0.250 は open だが witness 無し） |
| A-2 | work row y | **+0.200**（cable y +0.480） | 1 / 5 | **+34.5 mm** | 境界 +0.150〜+0.200 未 sample |
| A-2′ | work row y | **+0.250** | 1 / 3 | **+29.5 mm** | +0.300 は L7 開くが pair 接触 |
- 出所: `GRASP_CENTRE_240_READING`（**mounting は run から読取り = built cell**・swept は centre のみ）・`WORK_ROW_240_READING`。
- ⚠ **A-1 × A-2 の併用は未測**（sweep は各軸単独。組合せの数値は存在しない）。

### family B — **crown を変える**（⚠ 可否 = Rs・#60）
| opt | mounting | crown | 読み | 値 |
|---|---|---|---|---|
| B-1 | built 0.220/45 | **除去** | best pair | **+37.5 mm**（L3×R14 = 42 対から） |
| B-1′ | built 0.220/45 | **0.020** | best pair | **+37.5 mm**（L1×R14） |
- ⚠ **chosen pair は +0.0（接触）** ⇒ B 系は **driver に pose-pair 選択の実装が要る**（best は在るが、solver が今選ぶ対は触れる）。左腕の閉止境界 = **(0.020, 0.050) 未解像**。

### family C — **mounting を変える**（cell 再構成）
| opt | mounting | crown | 読み | 値 |
|---|---|---|---|---|
| C-1 | **0.280 / 20°** | **無し** | **chosen pair PASS** | **+22.7 mm**（唯一の chosen-pair PASS・L1/R4） |
| C-1′ | 0.280 / 20° | ≤ 0.075（height 族） | best pair | **+35.7〜+38.9 mm**（546 対・全 head に witness） |
| C-2 | 0.280 / 20° | 0.110 | grid witness | **+14.7 mm**（L5/R30） |
| C-3 | 0.340 / 20° | 0.110 | grid witness | **+15.3 mm**（L2/R34） |
| C-4 | 0.400 / 20° | 無し | grid witness | **+17.2 mm**（L8/R34） |
| C-5 | 0.280 / 45° | 無し | grid witness | **+11.9 mm**（L4/R8） |
- C-1 の crown 境界 = **(0, 0.005] m**（0.005 で左腕の唯一の clear pose が消える — 腕同士の接触は 0.010 から。**crown はこの mounting を「腕衝突」でなく「左腕の pose 剥奪」で閉じる**）。C-1′ は chosen-pair では fail ⇒ B 系と同じく pose-pair 選択要。
- **crown × tilt は相互作用**（p4 finding）: 0.280/20 は r=0.075 を許容・0.220/45 は r≤0.020 が要る ⇒ **「crown をどこまで許すか」は mounting の性質**であり、どちらの数字も境界ではない（次の swept 値まで未測）。

## §3 全 option 共通の穴（選ぶ前に見える所へ）

1. **witness ≠ route**: 全数値は start-pose 段。route（43-step）は別測定（succession DoD 側）。
2. **#54 部材**: 全 clearance は **298 mm 空隙の将来部材を含まない**。部材入力が決まれば全 option の数値が動き得る ⇒ **「部材入力を先に決める」か「選んでから部材込みで再測」かも Rs の選択**。
3. **#57**: chosen-pair の数値は solver の start-pose 選択に依存（best-pair との差 = 選択実装の有無）。
4. **fail は弱い**: PASS = 証人・fail ≠ 反証（interleave は N×M 対中 1 対の読み）。240 でも zero が残った 12 点は「強い fail」だが依然 反証ではない。~~0.340/30 は **未測**（driver segfault）~~〔⛔ **訂正 2026-08-08 11:1x（p4 発・`m-p18-80` 経由・当卓 KINONLY `:44`/`:56` 実読）: 0.340/30 は *未測ではなく実測済の fail*** — kin-only 再走（fix `2bb1aad4e7`）で両 sheet とも L clear 0・「L put back」で fail。**「未測」と「実測済 fail」は menu では別物**（前者は情報が無い・後者は弱い fail が在る）。PASS 4 点の一覧は不変。〕
5. **#60**: crown 0.110 自体が最も接地の弱い数（写真）— family B/C の crown 行は、その数の上に立つ。

## §4 Rs が settle する点（menu の外側）

1. **family の選択**（A = cell 不変 / B = crown / C = mounting）と行の選択。
2. **crown 変更の可否**（実 cell との忠実性 — #60・B/C-1′ の前提）。
3. **#54 部材入力**の時期（先決 or 選択後再測）。
4. B/C-1′ を選ぶ場合: **pose-pair 選択の実装**を lead lane に発注するか（chosen→best の差を実現する装置）。

## §5 sources（全て実読・witness commit は bank 後に版表へ追記）

- `GRID_24_VS_240_20260802.txt`（22 comparable 点・zero 分類 4 sample / 12 real・witness 4 点）
- `CROWN_SWEEPS_240_READING_20260802.md`（radius/height 240・all-pairs 602 対・crown×tilt 相互作用・§5 の 2 註）
- `CROWN_AT_PASSING_MOUNTING_20260802.txt`（0.280/20 の radius 掃引・boundary (0,0.005]・2 controls 再現）
- `GRASP_CENTRE_240_READING_20260802.md`（built cell 明記・witness −0.150/−0.200）
- `WORK_ROW_240_READING_20260802.md`（witness +0.200/+0.250・境界 50mm 未解像）
- DDR #54 `:158` / #57 `:161` / #60 `:164`（as-read 10:50・LEDGER moving file ⇒ 行番号は同時刻限り）
