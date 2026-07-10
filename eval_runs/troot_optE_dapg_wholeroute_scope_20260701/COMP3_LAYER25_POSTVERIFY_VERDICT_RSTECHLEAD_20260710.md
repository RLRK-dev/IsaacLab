# comp3+comp4 §運用15 層2(事後)+層5(多視点) 統合 VERDICT — RS-TECH-LEAD (%12) — 2026-07-10

**Object (on-disk):** commits af9c8f2eae (chunk 1) / f089fde5f1 (chunk 2) / 1ef5376f81 (chunk 3) @ HEAD.
**Structure:** 4 independent parallel verifiers — GEOMETRY / PHYSICS-SERVO / SSOT-RULES / REGRESSION-NHA (層5 の幾何・物理・SSOT 3 視点 + 層2 事後 on-disk verify を統合 wave で実施; 層3 = scoped ruff + module tests + my re-runs、済)。

---

## DECIDE = **PASS-WITH-FOLDS**

- **Build itself = SOUND.** No CRITICAL code defect in any view. flag-OFF default path = **PRESERVED (AST-strip proof: flag-ON 分岐除去後、全共有関数が pre-bundle base と AST 一致)**。R1-R8 全て on-disk 実装確認 (SSOT view fidelity table)。banked 面 (env-core / Layer-A byte-repro / locked monolith / golden npz) いずれも本 bundle からの侵害なし。
- **BUT: G1 (flag-ON live rollout) は現定義のまま実行不可** — 幾何 HIGH (G-F1) が G1 の前提を崩す（下記）。fold 群 + Rs 裁定を経てから G1 surface。
- 両中断 pass の priority lead は今回決着: 「import alias 除去」= REFUTED (誤読)、「q/qd index 空間」= NO DEFECT (maps は qd-space で正しい、newton API 直読で確認)。

## 受理 findings (REBUT なし; 全 4 view の全 findings ACCEPT)

**HIGH×2:**
- **G-F1 (geometry): 録画シーン ≠ env flag-ON シーン — support-clip トポロジ差、未裁定。** 録画 (RUN1_REFERENCE_V2 系, w0e_81rerun_snapdown_0537) のシーン = table+C1+spacer+C2+spacer+PERCLIP_PIN で **support clip なし** (run.log:34-41、私の直読で確認)。env は add_support_clips=True (:498) → 4 REST clips、P0 cable は **clip-吊り** (probe leg D: cable↔bare-table=0 / cable↔clip=23、私の直読で確認) vs 録画の **table-resting z≈0.804**。録画済み z_grasp 降下 + grip 階段のタイミングは table-resting cable 前提 → 現 env で G1 を回すと「録画が前提とした位置に cable がいない」まま grip を検証することになる。さらに geometric-design doc の前提 0.809 は GROOVE_CENTER_Z (seated 値) で録画実測 0.804 と混同。**env-core 期から存在した差だが、arms が kinematic の Stage-A では不可視、grip live 化で初めて material 化。**
- **P-F1 (physics): multi-world (N≥2) flag-ON grip 経路の runtime 検証ゼロ。** probe は world_count=1 で q≠qd stride 誤りが構造的に不可視; L1/L4 は mock。build 時 servo_readback_assert が map 誤りは捕まえるが、solver kernel の per-world ctrl routing は runtime のみ。**cheap fix あり: N=2 CPU probe (world-1 だけ CLOSE → world-1 動く/world-0 動かない/ctrl routing 読返し、数秒)。**

**MEDIUM×5:** S-F1 evidence dir 未 commit (唯一の耐久コピー) / P-F2 grip readback が f=0 (OPEN==0.0) で武装→永久空虚 (K6 再発、first-CLOSE-onset で武装に修正) / P-F3 PHYSICS_STEPS_PER_RL==_REC_CADENCE cross-assert なし + sub_i 境界 check なし / P-F4 step_target docstring「grippers latched」が canonical 録画 (frame 7617 で両手 RELEASE→OPEN) と矛盾 + horizon 尾部 ~139 step の unheld 意味論は trainer 段 surface / G-F2 recording↔env cell 幾何互換 guard なし (flag-ON は nominal-provenance assert 要)。

**LOW×7:** S-F2 locked monolith worktree に既存未 commit 変更 (+2036/−812、本 bundle 起因でない、意味中立と bound 済 — owner 処置要、触らない) / S-F3 byte-repro「81/81 stands」は 1-cell 実証 + 静的論証 (scope 限定記録、§運用30) / S-F4 plan 文言と R1a の整合 / G-F4 settled patch world-0→all-worlds (DR 導入時に再訪) / G-F5 probe leg D 非空虚カウンタの分類緩さ / G-F6 L4 transit test の自己参照性 (golden npz 列 assert 追加で閉じる) / P-F5 sub-frame 積分粒度 (env-core 既存性質) + P-F6 mjw-eq-deferred は G1-GPU precondition として再掲。

## Fold 指示 (COORD、no-GPU)

1. evidence dir commit (S-F1)。2. **N=2 CPU flag-ON grip probe** (P-F1)。3. **P0 cable-parity probe leg** (G-F1a: env settled cable_xyz vs golden npz pre-grasp、per-segment y/z tol — support-clip 差を測定で定量化)。4. grip readback 武装点修正 (P-F2)。5. cadence cross-assert + sub_i bounds (P-F3)。6. docstring 訂正 + 尾部意味論 loud 記録 (P-F4)。7. nominal-provenance assert (G-F2)。8. 文書修正群 (0.809→0.804 / plan 文言 / leg D 分類 / L4 golden 列 assert)。9. G1 gate 定義 = grasp/lift leg のみ + C1-seat 以降除外 (G-F3) + mjw-eq precondition (P-F6)。

## Rs surface 項目 (folds 完了後に一括)

1. **G1 GPU 承認** (再定義版: grasp/lift のみ、world-0、as-coded cpu-newton substrate)。
2. **worlds≥1-frozen escalation** (別 campaign item、5体 K3)。
3. **⭐support-clip 裁定 (G-F1b)**: A) flag-ON G1 は add_support_clips=False で録画基盤に合わせる (G1 = 統制実験として clean; trainer 段のシーン定義は別途) / B) clips 維持で期待値再基準化 (録画との整合喪失)。**私の推奨 = A** (G1 の目的 = build_multiworld close-kinematics の統制検証; cable-parity probe の実測を添付して判断材料化)。
4. locked monolith worktree 未 commit 変更の処置 (hygiene、owner 特定要)。

---
*%12 RS-TECH-LEAD, 2026-07-10。4 view 並列・独立 context。DECIDE=PASS-WITH-FOLDS。G-F1/P-F1 の鍵事実は私が独立照合 (§運用28: run.log scene inventory / :498 / probe leg D json / newton control.py:32-33 dof-space)。*
