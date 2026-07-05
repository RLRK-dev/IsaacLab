# 幾何設計: W0-e seat/guide offset-follow (F-1a / F-1b / F-2 / F-3) — /geometric-design 6-step

対象 = EE target **計算式** の変更 (task_config 定数変更なし)。spec = `W0E_SEAT_GUIDE_OFFSETFOLLOW_SPEC_20260705.md` **v0.6** (5体反映版; 本 doc の v0.6 追補は各所に [v0.6] 注記)。

## Step 0: 機構問い直し (BOUNDED 一発)

- **必要か**: YES — 41/81 cell が決定論的に失敗 (C1 escape 36 + FAIL 系)、既知 root-cause 2 種。学習 (α) に吸収させる案は「既知の決定論的欠陥を curriculum に混ぜる」= **global CLAUDE.md Gate-FAIL default (fix root cause first) + prohibited.md hard-stop (根本原因特定後の回避策禁止) + spec RC-1 の DR/curriculum 汚染 (teacher 欠陥)** に抵触 [v0.6: NHA r2 — 無 cite の「設計方針違反」を cite 化] + 土台 49.4% のまま。
- **安価な代替 (salvage)**: 本 fix 自体が salvage — 新機構の発明ではなく、**既 banked pattern (fix-⑤ X-follow / caveat-a Y-follow / R 再 grasp cable-X follow :4477) の欠落部位への展開**。
- **より上流の代替**: clip funnel 追加 = 製品幾何の premise 変更 (Rs 専権、不採用) / cable 再分割 = 全 banked evidence の物理 premise 変更 (不採用、将来項)。
- **下流リスク**: C2 re-grasp は既に cable-X follow 済 (good pattern)。sim 分岐不要 (evidence 収集済) → FLAG なし。ONE pass 完。

## Step 1: 実測 (全て本日の run 実測値、設計値でない)

| 計測対象 | 値 | 根拠 |
|---|---|---|
| C1/C2 channel 床上面 | 825mm (=cz 820+5) | clip_parts :1165 + CLIP_FLOAT_Z 20mm |
| 内壁 (低壁) 面/上端 | x=±7.5〜±10.5 / 上端 840mm | :1166-1167、runtime 照合 (JSON LOW_WALL_TOP 840.0) |
| 外壁 面/上端 | x=±11〜±15 / 上端 850mm | :1168-1169 |
| 着座 cable 中心 z | 829.0mm (=床 825 + r4) | strict 59 cell 実測 [828.8, 829.4] |
| cable 半径 / node pitch | 4mm / **15mm** | 縞周期実測 + 40 node |
| 横捕捉公差 (channel) | **±3.5mm** (口 15mm − cable 8mm)/2 | 幾何 |
| **[v0.6] crossing X 変位 @ROUTE-end** | **bimodal {≈+0.2, ≈−16.3mm}、escape 36/36 予測 (FP2/FN0)、max −20.1 — dx 非比例** (旧「X-bow ≥7.5mm @dx−20」推定は不正確と実測訂正) | `w0e_offline_validation/percell.csv` (81 npz) |
| **[v0.6] escape 亜類** | (i) 平行 offset (ph0∧dx≤−10、span 一様 −16) / (ii) 斜行 buckle (ph5、勾配 ~17°) | 同上 (局所 3-node 形状) |
| Y bad 帯 | B1=[3.5,5.5] / B2⊂(10.5,15) 中心~12.5 (**UB は probe P-2/3 で確定**) | sweep 8 cell + grid (dy10.5=O, 12.5=X, 15=O) |
| good 台地 / δ_target | [6, 10.5] / **7.5** (margin B1 側 **区間 [1.5,2.5]** [v0.6: 縁 6.0 は n=1] / B2 側 ≥3.0mm) | 同上 |
| EE 降下 target z | GROOVE_CENTER_Z+float+ee_off (不変) | :4169 |
| **[v0.6] ROUTE-end cable 高度** | z≈846-851 ≈ 外壁上端 850 同高 (offset 時は降下前から壁掛かり得) | offline 検証 |
| reach 残差 @±20mm offset | max 1.2mm (**scope: C2_REGRASP/R-arm field のみ** [v0.6] → 補償 target は pre-build reach probe で実測) | grid 81 実測 |

## Step 2: 制約

**ハード (違反不可):**
- H1: 補償 = **common-mode のみ** (両腕同一 Δ) — INV#2 88mm span 不変 (W0-b CRIT1 carry: per-arm 独立 clamp 禁止)。**[v0.6 scope 明確化 (CC5-CH4)]: H1/禁止③ は span-bearing 両腕把持 phase (C1_SEAT/C2_DUAL_SEAT) に適用。F-2 は R 解放済 (:4274) の単腕 guide phase = INV#2 非該当で除外**。受入に as-executed span 列常設
- H2: **|ΔX| ≤ 22mm (F-1a/F-3) [v0.6: 観測必要量 max 20.1mm — 旧 ±12 は offline 実測で不足と判明]** / |ΔY| ≤ 7.5mm (F-1b、必要量 ≤6.5mm [v0.6 算術訂正]) / F-2 per-leg |Δlx| ≤ 8mm — 補償極値の到達性は pre-build reach probe で実測 (1.2mm 実測は regrasp field のみで外挿不可 [CC3-CH6])
- H3: offset 非活性 (未設定/(0,0)) で **byte-identical** (補償分岐に入らない)
- H4: cable qpos/node への直接書込・pin 規則改変・rollout 中 privileged 反応補正 = 禁止 (%9 bright lines)
- H5: z target 不変 (XY のみ補償) — テーブル/clip 貫通の新規経路なし
- H6: F-1b は SIM-ONLY tag (実機 playbook 除外)

**ソフト:** S1: 全 offset で z@C1→829±1 / S2: cradle 8/8 / S3: 43-step 表からの逸脱ゼロ (step 追加なし、既存 step の機能回復)

**有効設計空間:** ΔY 必要 ≤5mm vs 許容 ±7.5 → 幅 2.5mm+ / ΔX 必要 ~10mm vs 許容 ±12 → 余裕あり。**評価: 十分** (bad 帯 margin 2.0mm は「狭い」側 → 感度分析強化で対応、下記 5a)。

## Step 3: 断面図 (C1、X-Z 面 @y=y_clip)

```
z[mm]
 850 ─      ▓▓           ▓▓        ← 外壁上端 850 (+25 帯の rest = 854)
 844 ─      ▓▓  ●844     ▓▓        ← ● X-bow 失敗: 内壁上 rest (中心 844=840+r4)
 840 ─   ▓▓ ▓▓  ▓▓ ▓▓              ← 内壁上端 840 (=LOW_WALL_TOP)
      　 ▓▓ ▓▓  ▓▓ ▓▓
 829 ─   ▓▓ ▓▓ ◎829 ▓▓ ▓▓          ← ◎ 正着座 (床 825 + r4)
 825 ─   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓            ← 床 pad 上面 825
        -15 -11 -7.5 0 +7.5 +11 +15  x[mm] (clip 中心基準)
         └外壁┘└内壁┘ 口 └内壁┘└外壁┘
   捕捉公差 = ±3.5mm (cable 中心が口内に入る条件) ≪ DR ±20mm
   F-1a: 降下前に crossing 実測 → common-mode X で ◎ の直上へ
   (Y 断面の縞 [B1/B2] は F-1b が δ=7.5 位相へ退避 — 高位 rest ●857-881 は Y 機構)
```

## Step 4: トレード表 (H 満たす候補のみ; H❌ は除外欄)

| Option | 内容 | H | S1 見込み | 備考 |
|---|---|---|---|---|
| **A ★採用** | F-1a/1b/2/3 = 実測→common-mode 補償 (spec v0.5) | 全 ✅ | 高 (予測子 88.9%) | 既 banked pattern の展開、機構非依存の経験則 |
| A′ | A の δ_target=0 変形 | 全 ✅ | 同等 | margin 2.5/2.5mm と対称だが台地実測は [6,10.5] が最厚 → 7.5 優先 |
| A″ | A − F-3 (C2 は後回し) | 全 ✅ | 中 (C2-miss 5+ 残) | RC-3 CONFIRM 済につき A 優先、fallback 縮退として保持 |
| 除外: funnel 追加 | clip 幾何変更 | H(premise)❌ | — | 製品幾何 = Rs 専権 premise |
| 除外: cable 再分割 | 位相感度の根治 | H(premise)❌ | — | 全 banked evidence 波及、将来項 |
| 除外: 学習吸収 (fix なし) | α に任せる | 設計方針❌ (cite = Step 0) | — | 決定論的既知欠陥の curriculum 混入 (teacher 汚染) |
| [v0.6] 除外: DR envelope 縮小 (帯行の除外) | 支持集合の再 scope | H(premise)❌ | — | ±20mm = Rs 確認 deploy 要件 (SOMA:28、拡大方向のみ); mod-15 は deploy に不存在; dx 縞は物理で実機再現 → 隠蔽 = 非保守 banking (NHA (b) 反証) |
| [v0.6] 除外: defer (0.494 で v1.1 → fix は P2 同梱) | 逐次変更 | 自己無効化❌ | — | rider ④ で数日内に baseline 無効化; DC-1 は識別区間が branch 跨ぎで今決められない (NHA (c) 反証) |

## Step 5: 物理妥当性

- **実機で成立するか**: F-1a/2/3 = 「実対象の位置を測って押し込み位置を合わせる」— 実機でも成立する普通の制御。F-1b のみ sim 固有 (node 位相) = SIM-ONLY tag で実機 playbook から除外済み。
- **境界条件**: 下記 5a。
- **逆方向検証**: 補償後 crossing = clip 中心 ±1mm (C2 で実測済の到達精度) → 口 ±3.5mm 内 ✓。

### 5a: 感度分析

| 変動要因 | 幅 | 影響 | H |
|---|---|---|---|
| settle 測定 noise | 同 device 決定論 6/6 (再現完全) | 補償量に bit 級以外の分散なし | ✅ |
| bad 帯縁の不確実性 | ±1mm padding 済 (over-trigger 良性 2 点実測) | 退避が保守側に発火するのみ | ✅ |
| δ_target margin | B1 側 **[1.5,2.5] 区間** (縁 6.0 は n=1) | ⚠「狭い」側: annex 8 cell (5.75 含む) で縁を pin、v1.1 で margin 再評価 | ⚠→対策済 |
| bow の降下中変化 | k=4 再測 1 回 (**残差形式** [v0.6 CC2-CH2: nominal 参照は補償自己解除]) + 30-step settle + |Δ|≤**22** clamp | 過補償防止 + 自己解除防止 | ✅ |
| [v0.6] 測定異常 (窓 0 node / \|δ\|>30) | plausibility gate | 補償 0 + loud flag = 現状 class に降格 (単調安全の担保) | ✅ |
| 二重補償 (F-3 × R-follow) | S-2 guard: 座標系一貫 (掴み=cable-X / seat=crossing)、単一適用 | 設計 rule 化済 | ✅ |

### 5b: 連動パラメータ

```
F-1a ΔX ──→ C1_PIN anchor (現 world pos 使用 :4211 → 正着座点で pin される = 改善方向、変更不要)
F-1a/1b ──→ GUIDE 開始 L_x0/L_y0 (:4301 = 実測 EE 継承 → 自動追従、変更不要)
F-2 lx 補正 ──→ cradle 判定 (:4354 既存計測、閾値不変)。[v0.6 訂正] F-2 の制御入力は新規 per-leg guarded read (:4354 は X を持たず、:4305 guide_body は開始時固定で不適 — CC5-CH8)
F-3 ──→ C2_SETTLE 以降 (scope-fence 外、E 継承のみ = 波及なし [F-0 監査])
z 系・GRASP 系・task_config = 不変
```

### 5c: 動的因果連鎖 (5 step)

| Step | 状態 | Event | 物理応答 | 影響 | 問題 |
|---|---|---|---|---|---|
| 0 | ROUTE_C1 settle 済 | δx,δy 実測 | — | — | — |
| 1 | 補償降下 (common-mode) | cable crossing が口内へ | 床接触 829 | seat 完了 | — |
| 2 | C1_PIN | pin が正着座点で anchor | 浅座凍結が消滅 | 保持◎ | — |
| 3 | L half-clamp + GUIDE (F-2 追従) | cable が throat 内に留まる | cradle 維持・しごき回復 | C1 浮上消滅 | — |
| 4 | C2 crossing 補償 (F-3) → DUAL_SEAT | C2 口内へ降下 | C2 着座 | strict_v2↑ | — |
| 5 | 記録 npz → BC 教材 | clean demo | curriculum 汚染解消 | 学習品質↑ | — |
| 失敗分岐 | 補償不足 | clamp 内で部分補償 | 現状と同じ失敗 class に留まる | 単調安全 | — |
| 失敗分岐′ [v0.6] | 測定異常 (tail 誤選択・過大値) | **plausibility gate が補償 0 に落とす** | 現状 class に降格 (**gate なしでは wrong-sign ±22mm で現 strict cell を壊し得た** — CC2/CC3 CRIT 指摘の閉止) | **単調安全 = gate 条件付き** | — |

### 5d: 軸分解保持

新規の保持主張なし (seat = 既存 channel 幾何の本来機能の回復)。X = channel 壁が enclose (幾何) / Y 軸方向 slide = **carried が正** (しごきで滑らせる設計そのもの) / 上方 = pin (承認済例外) + guide 後は重力+壁。μ0 falsifier は本 fix の対象外 (保持設計変更なし) — residue として明示。

## Step 6: 設計記録

Rs 承認 + build + RUN 証明後に `thread-vault/06-Knowledge/GD-W0E-OffsetFollow.md` へ (未承認案は記録しない)。

**GATE 判定: 6-step 完 — 5体 [VERIFY] へ (入力 = 本 doc + spec v0.5 + F-0 監査表 + sweep evidence)。**
