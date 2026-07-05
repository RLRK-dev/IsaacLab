# W0-e F-0: route 全域 phase-target 監査 (COORD %11, read-only, build-input)

**charter:** %12 W0-e F-0 (Rs「A」+「すすめて」授権, 2026-07-05 15:45)。目的 = `_run_mujoco_grasp_route` (test_newton_clip_routing.py:3569) の全 phase (GRASP_HOVER〜C2_SETTLE) の `ik_move_both` target を全数列挙し、各 target 座標成分 (X/Y/Z 別) の錨定種別を分類して**点修正の繰り返しを断つ**。新規 nominal-錨定 cable-相対 target = F-leg 候補 flag (**監査のみ・実装なし**)。
**入力:** W0E_SEAT_GUIDE_OFFSETFOLLOW_SPEC_20260705.md v0.1 (RC 表 + F-1a/1b'/2/3 leg)。本表 = 5体 [VERIFY] の入力。
**method:** source 直読 (edit 禁止遵守)。各分類に file:line 根拠 (§運用5)。scope-fence = C2_SETTLE (:4668) 直後の M-Hook-1 PART 2 (:4867) 以降 (STEP-13 proxy / CLIP-delta / DIRECTION-B retention 等 env-gate 診断) は **route 外 = 監査対象外**。
**L-TRIAGE:** L1 (read-only 分析 + 記述 md 1 本、code/config/physics 変更なし、blast 0)。

---

## 錨定種別 legend (3 分類)

| 種別 | 定義 | 例 |
|------|------|-----|
| **N** = nominal 定数錨定 | 固定定数 (clip 位置 CLIP_X/Y/CLIP2_X/Y、z const)。cable 状態非依存 | x_clip=CLIP_X:3640, c2x=CLIP2_X:3682, z_high/z_lift/GROOVE_CENTER_Z |
| **C** = cable 実測補償済み | 実 cable body を測定して導出 (measure→compensate) | x_grasp=fix-⑤:3953, GRASP_YC=caveat-a:3941, R再grasp _cRx=argmin bow:4482 |
| **E** = 実測 EE 継承 | 現到達 EE pose を継承 (相対) | R_hold:4300, L_x0/L_y0:4301, _Lhold_r:4285, _plg |

**cable-相対?列** = 「この target は本来 cable crossing/line に整合すべき操作か」(N でも cable-相対なら fix 候補; E は相対保持で fix 不要)。tgt/tgt2 helper: `tgt(x,z)=(x,GRASP_YC∓GHS,z)` :3957, `tgt2(x,yc,z)=(x,yc∓GHS,z)` :3960 (span=2·GHS=88mm INVARIANT#2 保存)。

---

## 監査表 — canonical path (C2_DUALSEAT=1, SEAT_TOPDOWN=1 = 81-cell grid が走る枝)

| # | phase | line | target 式 | X | Y | Z | cable-相対? | W0-e leg / flag |
|---|-------|------|-----------|---|---|---|------------|-----------------|
| 1 | GRASP_HOVER | 3968 | `tgt(x_grasp, z_high)` | **C** fix-⑤ | **C** caveat-a | N z_high | X,Y=済 | ✅ **DONE** (fix-⑤/caveat-a) |
| 2 | GRASP_DESCEND | 3976 | `tgt(x_grasp, zk)` (detour wrap) | **C** fix-⑤ | **C** caveat-a | N (z_high→z_grasp) | X,Y=済 | ✅ DONE; +DQ7(ii) detour = None-path passthrough (錨定不変) |
| 3 | LIFT | 4007 | `tgt(x_grasp, zl)` | **C** fix-⑤ | **C** caveat-a | N (z_grasp+LIFT) | X,Y=済 | ✅ DONE |
| 4 | ROUTE_C1 | 4042 | `tgt2(xk, yck, z_lift)` | interp[**C** x_grasp → **N** x_clip] | interp[**C** GRASP_YC → **N** y_clip] | N z_lift | endpoint=N | ⚠ **S-1**: 到達点=(x_clip,y_clip) nominal → C1_SEAT へ接続 (F-1a/1b' 整合 sub-note) |
| 5 | **C1_SEAT** | 4173 | `tgt2(x_clip, y_clip, zk)` | **N** x_clip | **N** y_clip | N (groove+ee_off) | **YES** (crossing 追従すべき) | 🔧 **F-1a (X) / F-1b' (Y)** = RC-1a/1b |
| 6 | R_UNCLAMP_RISE | 4289 | `_Lhold_r, (prRr_x, prRr_y, _rz)` | **E** 継承 | **E** 継承 | E + N Δ(+45mm) | no (相対上昇) | ✅ E-相対 (fix 不要) |
| 7 | GUIDE_PRELIFT | 4331 | `(L_x0, L_y0, _lz), R_hold` | **E** L_x0 | **E** L_y0 | E + N Δ(+45mm) | no (相対上昇) | ✅ E-相対 (fix 不要) |
| 8 | **GUIDE_C2** | 4339 | `(lx, ly, _trav_z), R_hold` | interp[**E** L_x0 → **N** c2x] | interp[**E** L_y0 → **N** c2y] | N _trav_z | **YES** (cable line 追従すべき) | 🔧 **F-2 (X)** = RC-2; Y→c2y=traverse (C2 seat=F-3) |
| 9 | C2_REGRASP(L-move) | 4456 | `_fl→_La=(c2x, c2y−GHS, _z_above_d), R_hold` | **N** c2x | **N** c2y−GHS | N _z_above_d | L が cable 保持=carry | ⚠ **S-2**: nominal だが L は cable 保持 (carry-to-nominal, air-grip でない); 最終 seat X は F-3 が決める |
| 10 | **C2_REGRASP(R-hover)** | 4558 | `_La, _fr→_hovR=(_cRx, _R_ty, _z_above_d)` (detour) | L=**N** c2x; **R=C** _cRx(bow) | L=N; R=**N** c2y+GHS(span) | N | **R が bow 追従** | ✅ **R X-follow 既存** (Rs-LOCKED anti-revert :4477-4489); L=N(carry) |
| 11 | **C2_REGRASP(R-descend)** | 4571 | `_La, _fr→_desR=(_cRx, _R_ty, _zgrip_R)` | L=N; **R=C** _cRx | L=N; R=**N** c2y+GHS | L=N; **R=C** _cRz+ee_off | R が bow 追従 | ✅ **R X/Z-follow 既存**; L=N(carry) |
| 12 | C2_TRANSPORT | 4635 | `_La, _fr→_carR=(c2x, c2y+GHS, _z_above_d)` | L=N; **R→N** c2x | N (両腕) | N | R が cable を nominal へ carry | ⚠ **S-2**: TRANSPORT が R を bow-X から nominal c2x へ戻す (carry); 最終 seat=F-3 |
| 13 | **C2_DUAL_SEAT** | 4655 | `(c2x, c2y−GHS, _zk), (c2x, c2y+GHS, _zk)` | **N** c2x (両腕) | **N** c2y±GHS | N (groove) | **YES** (crossing 追従すべき) | 🔧 **F-3** = RC-3 **CONFIRMED**: 両腕 pure-nominal seat |
| 14 | C2_SETTLE | 4668 | (両 gripper release、ik target なし) | — | — | — | — | release/settle (EE target なし) |

## 監査表 — non-canonical 枝 (canonical grid 非走行; 完全性のため記録)

| # | phase | line | 枝条件 | X | Y | Z | flag |
|---|-------|------|--------|---|---|---|------|
| 15 | C2-LIFT | 4697 | `elif _seat_topdown` (SEAT_TOPDOWN=1, DUALSEAT=0) | interp[**E** _plg[0]→**N** c2x] | interp[**E**→**N** c2y] | N | ⚠ 非 canonical; 使用時は F-3 同族 (nominal c2x/c2y) |
| 16 | C2-PUSH | 4717 | `else` (両 gate off) | **E** _plg[0] | **E** _plg[1] | N (→c2_seat_ee_z) | ⚠ 非 canonical; E-継承 |

---

## Key findings

1. **cable-state-aware target は 3 系統存在** (2 済 + 1 既存): fix-⑤ (grasp X, C) / caveat-a (grasp Y, C) / **R 再grasp の X・Z-follow** (`_cRx`/`_cRz` argmin-bow, Rs-LOCKED :4477-4489)。**R 再grasp = offset-follow の既存 good pattern** — 欠陥ではなく calibration reference。
2. **nominal-錨定 cable-相対 seat/guide target は 4 箇所、全て spec の既存 leg に mapping**:
   - C1_SEAT X (:4173) → **F-1a** (RC-1a) / C1_SEAT Y → **F-1b'** (RC-1b)
   - GUIDE_C2 X (:4339) → **F-2** (RC-2)
   - C2_DUAL_SEAT crossing (:4655) → **F-3** (RC-3) — 本監査で **pure-nominal 両腕 seat を CONFIRM** (build-時 forensics 完了、RC-3「同 pattern か」= YES)
3. **新規の未 cover な F-leg は canonical path に無し。** 監査は spec の F-1a/1b'/2/3 が canonical path の nominal-錨定 cable-相対 target を**過不足なく閉じる**ことを確認した (点修正の繰り返しを断つ = 達成)。

## Sub-notes (新規 leg ではないが、既存 leg の設計入力)

- **S-1 (ROUTE_C1 endpoint 整合、:4042):** 空中 drag の到達点 = nominal (x_clip, y_clip)。F-1a/1b' が C1_SEAT を −δx/Δy 補償する時、drag 到達点も同補償すべきか要検討。cable は全域 held ゆえ seat-shift が held cable を動かす → **seat-only 補償で足りる公算大**だが、over-drag で seat 前に crossing がずれる可能性は F-1a 設計で確認 (降下中 k=4 再測が spec F-1a に既記載 = 吸収機構あり)。
- **S-2 (C2 re-grasp cable-follow が transport で nominal へ戻る、:4456+4635+4655):** R 再grasp は bow-X を追う (C) が、直後の TRANSPORT (:4635) が R を **nominal c2x へ carry** し、DUAL_SEAT (:4655) が両腕 nominal c2x で降下する → **最終 C2 seat X = nominal に回帰**。これが RC-3 の機構の明示化。F-3 は DUAL_SEAT の crossing を common-mode 補償すべき (両腕、INVARIANT#2)。**⚠ 現状 L は独立 cable-follow せず** (LMOVE :4456 = nominal, ただし L は cable 保持=carry ゆえ air-grip でない)。F-3 = 両腕 common-mode の crossing 補償が RC-1a と同型。
- **S-3 (GUIDE_C2 Y、:4339):** Y interp → nominal c2y は traverse 到達点 (C2 seat Y = DUAL_SEAT の c2y±GHS で処理)。**F-2 は X のみ補償で正** (spec F-2 と整合); Y は独立 leg 不要。

## Calibration check (既知錨定を本分類で再現 = 手法妥当性)

| 既知 (charter/spec) | 本監査の分類 | 一致 |
|--------------------|-------------|------|
| grasp X = fix-⑤ 済 | #1-3 X = **C** (x_grasp:3953) | ✅ |
| grasp Y = caveat-a 済 | #1-3 Y = **C** (GRASP_YC:3941) | ✅ |
| C1_SEAT :4173 = nominal X,Y | #5 X,Y = **N** (x_clip/y_clip) | ✅ |
| GUIDE :4337 = 直線 | #8 lx,ly = 直線 interp → **N** c2x/c2y | ✅ |
| C2 系 = 要分類 | #9-13: R-regrasp=**C**(bow-follow 既存) / L・transport・dual-seat=**N** → **F-3** | ✅ (RC-3 CONFIRM) |

4/4 既知錨定を独立に再現 → 分類手法 calibrated。

---

## 結論 (F-0 = build 前設計入力)

- route の cable-相対 target は **{grasp X (fix-⑤済), grasp Y (caveat-a済), C1 seat X/Y (F-1a/1b'), L-guide X (F-2), C2 seat crossing (F-3)}** で**全数閉じる**。**新規 F-leg 追加は不要** (spec v0.1 の 4 leg で過不足なし)。
- **RC-3 forensics 結論**: C2_DUAL_SEAT (:4655) = 両腕 pure-nominal (c2x, c2y±GHS) seat を CONFIRM。C2 の partial-挿入 (z 帯 +3..+16) = C1 と同型の crossing-nominal 欠陥。**F-3 は有効化推奨** (RC-3 の「forensics で同 pattern 確認後」条件 = 満たした)。
- **S-2 が最重要設計入力**: R 再grasp の cable-follow が transport-to-nominal で相殺される構造 → F-3 は DUAL_SEAT (または carry 到達点) の crossing を両腕 common-mode で補償する必要。既存 R-follow との二重補償に注意 (R は re-grasp で cable を掴む → seat で crossing 補償 = 一貫させる)。
- INVARIANTS 不触確認: 全 target が span=2·GHS 保存 (tgt/tgt2 helper)、per-arm 差動 Δ なし (F-3 も common-mode 必須)。

*v1.0 COORD %11 起草 15:5x。source cite = test_newton_clip_routing.py:3569-4729 + spec RC 表。read-only 監査 (edit なし)。判定は 5体 [VERIFY] + %12/%9。*
