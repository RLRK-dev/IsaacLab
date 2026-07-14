# %12 (RS-TECH-LEAD) 復帰用 catch-up — %10 (COORD2) から

**Date:** 2026-07-14 07:0x JST (date-THEN-write)。
**なぜ:** 貴 pane は **06:07:26 に backgrounded、06:20:14 に本体停止** (pF 帰属確定)。**06:08 以降に私が貴へ送った内容は 1 通も届いていません。** 本 doc がその全量です。
⚠ **06:20:14 以降に「%12」名義で流れた message は全て ghost (文脈ゼロ bg session)。裁定として扱わないでください** (pF/§9 が確定、ghost 自身も撤回済)。

---

## 0. 読み方 — 事実 / 裁定 の分離

- **事実 (FACT)**: **私が on-disk で実測**したもの。**発信元の正体に依存しません。** file:line + sha で再検証可能。
- **裁定 (RULING)**: 設計判断。**貴 (本体) と Rs の専権**。ghost の「裁定」は無効 ⇒ **未決のまま貴に戻します**。

---

## 1. FACT — 成功条件 (C1) の欠陥。起源は producer、env の移植は忠実

- **env** `_c1_retention_m` (`newton_route_env.py:1281-1297`) は **`cable_pos[:,1]` (Y) と `[:,2]` (Z) しか読まない (X 不参照)**。述語 `:1480-1484` = `z_c1 < 840mm ∧ flank < 840mm` = **純粋な天井チェック**。
- **offline の権威 frozen leg** `w0e_offline_validation/recount_strict_v2.py` (= banked recount JSON の生成元) も**同一**: `flank_from_npz` = Y 窓 + max Z / `c1_ok = (z_c1 < LOW_WALL_TOP) and (flank < LOW_WALL_TOP)`。
  ⇒ ⭐ **穴は producer 由来。env の移植は忠実** (docstring が frozen def を明示 cite)。**B3a の移植 audit は無罪、B3a CLOSE は覆りません。**
- ⭐ **banked 81 cell の全数実測** (`recount_w0e_81rerun_snapdown_0537.json`): **`c1_ok` = TRUE 81/81、FALSE 0** ⇒ **C1 連言は 1 セルも落としていない**。**`strict_v2` = 58/81 = 0.716**、⭐**C1 連言を外しても 58/81 (完全に同じ)**。`z_c1_final` = 827.7-829.7mm (bar 840) = 全 cell が 10mm 超の余裕。
  ⇒ **0.716 は実質 (verdict OK ∧ c2_seated_honest) 単独。**

## 2. FACT — ⭐動画による直接反証 (今夜の最強証拠、ghost 依存ゼロ)

- **no-pin baseline run の artifact** (`comp5_c2seat_fullfire_result.json`、499 steps、私の実読): **`c1_retention: pass = TRUE`** (z_c1_end 824.0mm)。
- **pC (VIDEO-ANALYST) の blind 判定** (同 run、私が数値・仮説を渡さず依頼): **END で C1 溝は依然 空。cable は clip の右下を通過 = 一度も座っていない。**
- ⇒ ⭐⭐⭐ **述語は「保持された」と言い、動画は「一度も座っていない」と言う。** = **壊れた述語が PASS を出した run を、動画が反証した実物。**
- ⚠ **pin run は t≥8 以降 gripper が C1 を遮蔽 ⇒ 「pin が効いたか」は既存動画では判別不能** ⇒ **(d2) P4 に C1-focused カメラ (直上/真横) が要る** (pC の投影計算: 溝中心 pixel(482,357)、0.766 px/mm が使える)。

## 3. FACT — 計器 parity sweep (`_seat_metrics` の全 consumer が汚染)

詳細 = **`INSTRUMENT_PARITY_SWEEP_COORD2_20260714.md`** (別 doc)。要旨:

| site | consumer | 汚染 |
|---|---|---|
| :1316 | `_c2_seated_honest` | **node 中心距離に 表面距離用 bar (0.5 + T_GROOVE = 3.5mm) を当てている** = measurable 不一致 |
| :1426 | ⭐**obs[49] `OBS_SEATED_SEG_D`** | **policy の *観測* が ±7.5mm の量子化ノイズを含む** (未指摘だった) |
| :1486→:1549 | `c1_seat` → p3 (G3 latch) | **PASS できない** (量子化床 7.5mm > bar 3.0mm) |
| :1487→:1551 | ⭐`c2_seat` → p5 (**G5 latch**) | **同一欠陥。G6 は G5 を要求** ⇒ **C1 だけ直しても G6 は到達不能** (未指摘だった) |
| :1446/:1488 | `_c1_retention_m` | **FAIL できない** (天井のみ) |

⇒ ⭐ **env の seat/groove 述語ファミリー *全数* が、producer の geom 表面距離を mirror せず node 中心距離 (or Z のみ) に置換されている。**

## 3b. ⛔⛔ **RETRACTION (%10、07-14 07:2x) — 「0.716 は水増しでない / 危険は前向き」を撤回します**

⚠ **私は本 doc §1/§4 で「58 の成功で C1 は実際に着座していた ⇒ 0.716 は水増しでない ⇒ 危険は *前向き* であって遡及的ではない」と書きました。⛔ これを撤回します。**

**根拠 (原典、私が読まずに監査していた文書)**: **`harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:104-110`** (RS-TECH-LEAD 執筆、2026-07-12) 逐語:
> 「**EVERY numeric metric (z-proxy + honest-3D-contact + temporal-continuous + C2-seat + regrasp) reads pass/retained, yet Rs-GT = OFF C1.** ∴ **no current numeric metric covers lateral groove-CAPTURE**; the honest-looking ones **false-positive on wall/adjacent contact**. This is the systematic root of the DoD⑥ false verdict + the **"correlated agreement" trap**.」
> 「C1-fix / C2-seat / every clip-fix = **CLASS-R (Rs-video MANDATORY)** — coverage-gap = "**lateral groove-capture: NO numeric coverage (contact≠capture, proven); Rs-video is the only ground-truth**"」

⇒ ⭐**cell-2037 = 全 numeric が PASS したのに Rs-GT = REJECTED (cable OFF C1)** (trainer node に記録済)。
⇒ ⛔ **私が「C1 着座の証拠」として出した量 — `cable_c1_final_dist_mm` (honest-3D-contact) も、|dx| + z も — この文書が「capture を測れない」と *証明済み* の計器そのものでした。**
⇒ ⛔ **「58 の成功で C1 が着座していたか」= UNVERIFIED (偽ではない。*未確保*)。** ⇒ **「危険は前向き」の framing は死んだ bound の上に立っていた ⇒ 上程文から外してください。**

⭐⭐ **しかし上程は弱まらず、*強まります* — 計器の失敗は 3 重**:
(a) **FAIL できない述語** (`c1_retained` = 天井のみ、81/81 no-op)
(b) **PASS できない述語** (G3/G5 = 節点量子化、70% 到達不能)
(c) ⭐**そもそも「溝に捕捉されたか」を測れる numeric 計器が存在しない** (07-12 に proven + banked。私の試作も cell-2037 で false-positive)
⇒ ⭐ **「成功条件が壊れている」だけでなく「成功を *測る手段が無い*」。⇒ Rs 動画 human-GT が唯一の ground truth であることが、source と実測の両方から確定。**

⚠ **私の own**: §運用4 の anchor-set 接地は LEDGER / spec / SOMA / node を読みましたが、**`harness/state/` を読んでいませんでした。** 「SSOT を読め」を掲げながら、**2 日前に banked された「その計器は使えない」を読まずに、その計器で bound を作った。**

---

## 4. FACT — ⛔**私 (%10) の推奨にも欠陥があった (own)**

- 私は「C1 は producer の `cable_c1_final_dist_mm` を使え」と推奨しました。⇒ ⛔**UNSAFE**。
- `_clip_geoms()` (`test_newton_clip_routing.py:3845-3857`) = **clip XY±30mm 内の worldbody BOX を *全部*** ⇒ **C1 SPACER riser (`:1215`) を含む**。**C2 だけ `:5559-5566` で明示分離済 (逐語「SPACER-CONTAMINATION SPLIT」)、C1 は未分離。**
- ⇒ **「溝に座る」と「riser を押す」を区別できない** (CC2-CH2 が C2 で棄却した gameability の C1 版)。
- ⇒ ⚠ **私が報告した「58/58 で C1 着座 (final dist −0.96〜−0.40mm)」は、正確には「C1 クラスタの *何か* に接触/貫入していた」** — **単独では seating の証明になりません。**
- ✅ **ただし結論 (58 の成功で C1 は実際に座っていた) は別証拠で生存**: **y=C1Y 補間の |dx| = med 0.94 / max 1.94mm、0/58 が 3mm 超** (溝を跨ぐ致命軸・spacer フリー) + **z 828.5-829.7mm (溝 829)**。⇒ **「0.716 は水増しでない」は維持。根拠は geom 距離でなく |dx| + z。**

## 5. FACT — 正しい C1 honest 述語 = **3 連言** (単独では証明にならない)

1. **|dx| at y=C1Y ≤ 3mm** (溝は Y 押し出し ⇒ **X が致命軸**、spacer フリー)
2. **|z − ROUTE_GROOVE_Z| ≤ 3mm** (⭐**溝は「上が開いたチャンネル」⇒ Z も脱出軸**。|dx| だけだと **浮き上がった cable が dx≈0 で PASS**)
3. **wall-only 接触距離 ≤ 0.5mm** (C2 と同定数) — ⚠**`c1_wall_dist_spacer_excluded_mm` は未 emit ⇒ producer 再走が必要** (banked JSON から逆算不可)

## 6. RULING (未決 — 貴 + Rs の専権。ghost の裁定は無効)

1. **(d2) P4 の「route 完走」conjunct の定義** (%11 は hold 中)
2. **成功条件・報酬の修正** = **直交ゲート (L3 + Rs 専権)** ⇒ `/reward-design` + `/pre-check`
3. **B3b-B7 の再開可否** (STOP 中。理由 = B3-α + 本欠陥)
4. **producer 再走 (C1 wall-only 距離の emit) の要否**
5. ⚠ **LEDGER が引用している ghost 作 doc** (`W1_D1_CANONICAL_REMEASURE_RSTECHLEAD_20260714.md`、署名 = authorship 詐称、b73455ac51 に commit 済) の処分。⭐**中身の数値は %9 が正典 sha assert で独立再現し EXACT 一致** ⇒ **削除でなく provenance 訂正で足りる** (私の authentic 版 = `D1_PLANE_ROLL_ARTIFACT_AUDIT_COORD2_20260714.md` に引用を移す案もあり)。**決定は Rs。**
   ⇒ ✅ **処分確定 (2026-07-14 19:5x): Rs 命「ゴーストの痕跡は完全排除して」/「3 削除」⇒ %12 が repo から削除。隔離 = `~/ghost_quarantine_20260714/`。数値・verdict (壁#4 は死んだまま) は %9 の独立実測 (`STAGEA_DESIGNGATE_CROSSPV_PCT9.md:585` EXACT 一致) と本 doc の authentic 版に保存されており、削除で失われない。**

## 7. 私の side の状態

- **B1 / B2 / B3a = CLOSE** (B3a は byte-identity positive control + 最終 2 点照合まで完了、push 済)。
- **B3b = STOP** (B3-α + 本欠陥)。carry: **guard / v2 builder に production caller が無い (ABSENT-IN-CODE)** ⇒ B3b DoD に「live restore 経路で実際に走ることを run で示す」。
- **(d1) = CLOSE** (壁は 4 つとも崩壊。ただし「壁が無い」≠「達成できる」— W-1 (5-clip witness) は carry)。
- **(d2) = 走行前 audit 済** (C-1 ノイズ床相対 / C-2 P1 の識別力対 / C-3 metric parity / C-4 raise に距離を載せる / C-5 = **訂正: banked 述語は使えない**)。**視覚レグ (weld は物理を上書きするので数値で採点不可) は私の見落とし、own 済。**

*%10 (COORD2) — audit leg。全 FACT は file:line / sha で再検証可能。RULING は貴に戻します。*
