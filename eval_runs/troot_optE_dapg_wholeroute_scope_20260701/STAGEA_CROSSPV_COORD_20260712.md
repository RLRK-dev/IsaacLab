# Stage-A design-gate cross-PV — COORD (%11) builder-leg verdict

**Reviewer:** COORD (%11/w2:p3、env-core/routeexec builder)。**Date:** 2026-07-12 12:2x JST。
**対象:** `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.6 + `STAGEA_REWARD_ARTIFACTS_20260712.md` v3.1。
**担当 leg (charter §3-A):** §4.1 route_t 4 消費者付替え / §6.2 bank v2 + interface v2 / §8 smoke legs の build 実行可能性。
**Grounding (§運用4 / ⚓):** spec v1.5h = `P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md` (banked basis 尊重確認) + node state (routeexec DoD②⑦(b) LOUD-CARRY) + **全 cite を on-disk 再検証** (grep/sed/npz 実読、下記 evidence)。

## VERDICT: **CONCUR-with-CORRECTIONS** (C1 HIGH ×1 / C2-C4 MED ×3 / C5-C6 LOW ×2)

アーキテクチャ (per-world route_t 単一源 / cable-metric HOLD / bank v2 producer-capture / OG nominal-scope) は builder 視点で成立。C1 は bank 前必須修正 (事実主張が cite 自身と矛盾)。C2/C3 は §6.2 内の design-pin 修正。C4 は確立済み invariant の leg 欠落。

---

## CONCUR evidence (担当 3 leg)

**§4.1 消費者 4 系統 = 完全 (独立 grep 照合):** `grep -n episode_length_buf newton_route_env.py` 全 9 site → route 系消費者 = `:1155` (grip staircase) / `:1198` (per-frame drive loop = ff replay + pin onset) / `:1597` (`_pull_route` → step_target + 下流 obs[50] `:1600-1604`) の 3 read-site = spec の ①-④ を被覆、**漏れなし**。`:1535` timeout は episode 時計残留が正 (spec 設計と一致)。`:489/:1029/:1616/:1625` = 簿記。grep-leg DoD (§8) = 正しい enforcement。**interface v2 `(k, world_ids)` は実装可能:** `apply_banked_restore` (route_executor.py:335-340) は maps の per-world index 配列書込 → world-slice 化は subset 選択のみ。v1 契約 (route_env_config.py:143-180 scalar-k) の v2 拡張は additive。

**§6.2 honest 再設計 = 私の comp3b grounding と一致:** bank = arm/gripper q のみ (`:427-433`) / qd=zeros (`:381-385`) / `reset_to_phase(k≥1)` raise (`:3235-3240`) — 全て私の 07-12 03:4x-05:0x grounding (%12 ACCEPT 済) と同一。producer-capture 根拠 (env replay t≈498 死 → k≥4 境界 env 到達不能) = 私の ⑥ (`65ae2c17fa`) + control (`dd7c97d480`) 実測と整合。

**§8 recording contract v2 = data-backed:** canonical npz (`w0e_81rerun_snapdown_0537/cell_x0_y0`) を実読 — **`cable_xyz` (7707,40,3) + `cable_quat` + `held_seg_l` (7707,) 既存** ✓ / velocity keys 不在 ✓ (ISSUE-B「速度を持たない」正) / `_prepare_recording` req=(ee_pos_r, ee_pos_l, grip_cmd, phase_id) `:3119-3123` ✓ (cable keys optional = N9 正)。→ contract v2 は検証 tuple 昇格のみ、data は既に在る。throughput/parity/hold-fires/bank-start/DR-corner legs = 既存 runner 部品 (⑥ runner + 81-grid harness + restore path) で構築可能。

**§4.2 substrate 論拠:** kinematic re-pose (qd zero、毎 frame) → EE-metric 盲目は builder 実装事実と一致。div_grip = 私の ⑥ で実測した発散量そのもの — 検出対象の実在は私の run が証明済。

---

## CORRECTIONS

### C1 (HIGH、事実 grounding — bank 前必須): 「全 route quiet = no-C2 scene」は cite 自身と矛盾

§0 N1 行「quiet が成立するのは no-C2 scene (byte-id 実証) と producer 経路のみ」+ §8 hold-quiet leg「全 route quiet leg は no-C2 scene (byte-id 実証 dd7c97d480 系) でのみ実施」→ **`dd7c97d480` は私の no-C2 control で、その実測は BYTE-IDENTICAL な発散** (grip-loss t=397 / early-done t=499 / z_c1_end 824.023mm — C2 run と全 logged 値一致。それが comp5 exoneration の機構)。**no-C2 scene は quiet でない — nominal replay は C2 の有無と無関係に発散する。** 全 route nominal quiet が成立する基板 = producer 経路のみ (58/81)。
**帰結:** §8 の no-C2 全 route quiet leg は設計のまま実行すると必ず FAIL し「HOLD 偽発火」と誤読される。**Fix:** 同 leg を削除 or「no-C2 健全域 (f0-336) fire-0 確認」に reframe (byte-id ゆえ C2 scene 健全域 leg と冗長 — 削除推奨)。N1 の核 (HOLD@nominal = 正しい警報) は不変 — むしろ強化 (C2 なしでも発散する)。

### C2 (MED-HIGH、実装可能性): bank v2 の cable 表現 = JOINT 空間に pin せよ

§6.2/ISSUE-B の dump keys「cable body_q/qd」→ **cable joint_q/joint_qd (FREE-root 7dof + revolute 角 + 速度) に変更**。根拠: (i) mujoco-backend の restore は joint 空間 — body_q は派生量 (`seed_cable_joint_state` docstring 自身が「joint_q/qd を書き eval_fk で body_q を整合」`newton_skill_env_base.py:1070-1085`; body_q 単独 assign は次 step で qpos から上書きされる)。(ii) producer 側 capture も joint slice 直読が exact かつ簡単。(iii) **restore は qd を zero しない変異体が必要** — `seed_cable_joint_state` は cable qd を zero する (post-settle rest 用) が、mid-route 境界 (G4−ε 等) の cable は運動中。body_q は検証用 optional 併載可。

### C3 (MED、実装可能性 + provenance): producer-capture の実装先 = 抽出 twin に pin (locked 不触)

「専用 producer-side dump」は **locked `test_newton_clip_routing.py` を編集できない** (D-1=C 不触、ANTI-REVERT)。実装先を明示 pin: **committed 抽出 twin `route_executor.run_route` (byte-repro 81/81 実証 `50f877c7f5`) or monkeypatch harness 前例 (`test_routeexec_byte_repro.py` 方式)**。副次利点: producer 本体は現在 +2036/-812 unbanked (Rs 裁定待ち) — committed twin 上の capture は provenance sha が clean で、integrity 問題と切り離せる。bank capture の provenance sha 要件 (ISSUE-B) はこの twin sha を指すべき。

### C4 (MED、DoD leg 欠落): flag-OFF byte-preserve leg が §8 に無い

routeexec 段の全 build が担ってきた確立 invariant (comp3 AST-strip 証明 `f089fde5f1` / comp5 flag-OFF byte-id / Stage-A gate-iii static diff) が、~1.3-2.4k LOC の本 delta の smoke 表に不在。**追加せよ:** trainer flags 全 OFF で env-core 挙動 byte-preserve (static code-diff or ⑨a′ 型 runtime leg)。interface v2 も stub/v1 経路の byte 不変を明示。

### C5 (LOW-MED、既裁定の再掲): cable restore の実装層 = env-level を §6.2 に明記

node DoD② LOUD-CARRY (%12 自身の RULING 07-07 17:13、node state.md:8): 「cable restore は env-level (route_executor joint-index 不可: free-root world-offset が world≥1 誤配置)」。§6.2 は restore-exact を言うが層を言わない — builder が route_executor 層に置く既知 trap を防ぐため一文再掲を。

### C6 (LOW、provenance 衛生): §0 cites が uncommitted working-tree を 2 箇所参照

(i) 一次データ生成元 `comp5_c2seat_fullfire.py:130-155` = 私の committed runner (`65ae2c17fa`) への **+122/-4 uncommitted 拡張** (`_DIAG` block) — committed 版の同行番号は別 code。spec bank と同時に diag 拡張を commit (additive・env-gated) or 生成元 sha を pin。(ii) c1-pin sites (`:1155-1173` 消費者③の pin-onset 分 / `route_executor.py:3396-3449`) = REFUTED c1pin、disposition (revert/stash) 後に行番号 drift + 消費者③は ff-replay のみに縮む。grep-leg は robust、行 cite は脆い — §0 に註記を。

---

## 担当外だが目についた点 (informative、verdict 外)

- Artifact 3 S 表の §運用22 比率 1:11.8 / 順位 S1>S3>S2>S4>S5 = 会計整合 ✓。Artifact 4 trace = substrate 実現可能 (v1 の EE-trace 不備の訂正は正) ✓。
- reward 本体不触 (G1-G6 banked) + INVARIANTS 不触 = 確認 ✓。

*%11 COORD — 2026-07-12。PAPER-ONLY / read-only 検証 (GPU 不使用)。*
