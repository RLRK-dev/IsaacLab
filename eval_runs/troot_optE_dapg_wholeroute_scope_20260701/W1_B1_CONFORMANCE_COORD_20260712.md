# W1 B1 (route_t 骨格) — conformance 表 v2.1 (5体 fold + %12 CONCUR + %9 F-1 fold 済 → build 解禁)

**v2.1 (16:4x):** %12 verify = CONCUR (ERRATUM-2 ce6cdebf29 発行 = B1 セル + §4-2 template の表面適合規則へ一般化; grep-leg = one-off 確定) / %9 verify = PASS-WITH-1-CORRECTION → **F-1 fold**: R12 の test 呼出し W = **non-prefix・world-0 除外 subset (例 {1,3}) を pin** (W=全 world/prefix だと「banked 先頭 |W| block 読み」bug class が値一致で不可視 — distinct bank と W 選択で判別力が完成) + R9 に slice 順序 1-line (下記)。

**Author:** COORD (%11/w2:p3、builder = CC1)。**Date:** 2026-07-12 16:0x JST (v1 15:3x → **v2 = 5体 fold**)。
**Node:** T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild。**設計 SSOT:** spec v0.8.1 §4.1 + §8 + charter v0.2 §3 B1。
**5体 verdict:** CC2 PASS (fix 3) / CC3 REVISE (6) / CC4 REVISE (**CRIT 1**) / CC5 REVISE (HIGH 1) / CC6 CHANGE_JUSTIFIED-conditional (HOLD 2)。CC1 DECIDE = **REVISE → 本 v2** (全 fold、ESCALATE なし — 設計欠陥不検出、v1 の leg 選定・周辺の誤りのみ)。disposition 全数 = §5。
**行番号:** v2 は 5体の on-disk 検証値で再 anchor 済 (alloc :483 / ② :1175 / ③ :1139 / ① :1574 / reset :1593 / r2p 呼出 :1594 / #6 :1608-1610 / interface :158 / timeout :1512)。leg script/コマンドは行番号でなく pattern anchor を用いる。

## §1. 実装方式 (mirror pattern) — v2 で経験 leg を訂正

route_t = per-world int64 新設、消費者 ①-④ は常に route_t を読む。flag `route_t_clock` (cfg、default False) = 乖離機構 (B2 凍結/B3 fork) の gate。OFF = increment/reset を episode_length_buf と同一 4 write 点 (:483 alloc / :1013 per-world / :1593 global / :1602 increment) で mirror → **値恒等 by construction** (CC2/CC4 が write-set 完全性・破れ channel 不検出を独立検証)。
**⭐v2 訂正 (CC4-CH1 CRIT + CC5-1 HIGH):** v1 の経験的柱「5-cell byte-repro」は **producer 経路専用で env を実行しない** (harness は newton_route_env を import しない、on-disk 実証) — B1 の env 側 diff に感度ゼロの偽検証構造だった。v2 の経験的柱 = **env 側 flag-OFF leg 群** (R17 v2、spec §8 が「clock 付替え後」と名指しする既存 leg の再実行 — 全て既存 script 再利用、新ファイル不要):
1. **⑨a′ EXACT 再実行**: `dod9a_prime.py` → banked `dod9a_prime.json` と EXACT (25/81 + per-cell 81/81)。
2. **DoD⑤ drift-zero 0.0 EXACT + DoD⑩ span-projection 0.0mm 再実行** (envcore smoke scripts 再走 vs banked 値)。
3. **DoD⑥ predicate unit 再実行**。
4. **env-trajectory byte-anchor**: gate-6 runner (CABLE_XYZ_DIAG=1、全 flag-OFF) 再走 → committed cablediag artifact (311f18cb9b、env_cxyz 499×40×3 + per-phase json) と EXACT 比較 — env 側の pre-B1 baseline は**既に bank 済**でありここに新 pin 不要 (決定論は no-C2 control の byte-identical trace で実証済)。
5. producer 5-cell byte-repro vs ca33d1e1a0 = **route_executor.py 側 diff 用に維持** (spec §8「route_executor.py diff 毎」— 必要だが env には不十分、役割を明示)。

## §2. Conformance 表 (v2)

| # | spec 要求 | 実装 (再 anchor 済 cite) | B1/後続 |
|---|---|---|---|
| R1 | route_t per-world int | `self.route_t` alloc :483 隣、torch.long | B1 |
| R2 | 消費者① step_target | `_pull_route` :1574 t := route_t[w] | B1 |
| R3 | 消費者② grip staircase | :1175 route_steps := route_t 読み。timing 不変量 (increment :1602 が両読みの後) は mirror で保存 (CC2 検証: B2 HOLD mask も increment 点 = 不変量継続)。**:1173-1174 の comment も route_t 表現に書換え** (grep 清浄化、CC2-CH1) | B1 |
| R4 | 消費者③ ff replay | :1139 同型。③ = ff replay のみ (c1-pin onset は B0-1 revert 消滅 = charter B0-2 帰結、spec 逸脱でない) | B1 |
| R5 | 消費者④ obs[50] + 凍結配管 | :1577-1581 簿記が t=route_t 化で自動追従 (CC2 検証: 凍結→_phase_entry 無更新→[50] 定値; fork 時は :1012 _prev_phase_id=-1 で自己再seed) | B1 (配管) / B2 (凍結) |
| R6 | increment/reset 規律 | increment :1602 隣 / reset :1593 (global) + :1013 (per-world) 隣で mirror。**fork 時の route_t := bank_boundary[k] は B3 が所有** (v1 R14 hook は v2 で削除、下記) | B1 / B3 (fork 値) |
| R7 | interface v2 `(k, world_ids=None)` | route_env_config.py :158 signature + docstring。既定 None = v1 恒等。**全 call site 無破壊を網羅検証済** (CC3: 実装 3 + 呼出 5、全て位置引数) | B1 |
| R8 | disposition 1/6 stub | NominalRouteStub (**newton_route_env.py:224-243** — v1 の route_executor 帰属は誤記) 互換受け | B1 |
| R9 | disposition 2/6 RouteExecutor world-slice | :3216 v2 化。**co-slice 契約 (CC3-CH1)**: 対象 world 集合 W に対し maps **と banked の両方**を per-map block 長 (arm 12 / gripper 16 / driver 4) で block-slice し、grip_target の enumerate index を **W 内で再基底化** (v1 案の「maps subset のみ」は tiled bank 下で silent world-0 読みになる罠)。**maps/banked 両 slice の world 順序 = 昇順で一致** (%9 R9 note)。forbid_banked_fork raise = **不変維持** (撤去 = B3) | B1 (slice) / B3 (forbid 撤去) |
| R10 | disposition 3/6 env reset() | :1594 呼出 不変 (位置引数・None 既定) | B1 (無変更) |
| R11 | disposition 4/6 writesite test | **B1 DoD leg = 「writesite test 不変 PASS を assert」** (raise :3227 は world_ids 処理より先 = 構造保証、CC3/CC5 検証)。期待値反転 = B3 (spec §4.1 :76 verbatim「bank v2 後に」)。⚠charter B1 セル文言「期待値更新」との差 = **charter ERRATUM-2 依頼** (§5、silent divergence 回避 — CC3-CH3/CC5-4/CC6 3者収束) | B1 (不変 assert) / B3 (反転) |
| R12 | disposition 5/6 state_bank world-slice case | B1 追加。**判別力条件 (CC3-CH2 + %9 F-1)**: per-world **相違**の synthetic bank (tile 同値 bank では slice バグ不可視) **かつ W = non-prefix・world-0 除外 subset (例 {1,3})** (W=prefix だと旧 enumerate ≡ 新 enumerate で「先頭 |W| block 読み」bug が値一致 — W 選択が判別力の半分) で world w の書込値 == w の block を assert + 他 world sentinel 不変。**+ `assert 0 not in state_bank`** (k=0 不変量 pin、CC3/CC4/CC5 3者収束) **+ flag-OFF `route_t ≡ episode_length_buf` unit assert (強制 per-world reset 後)** (CC6 条件 — done-mid-run 経路の穴を閉じる) | B1 |
| R13 | disposition 6/6 = 消費者#6 done-reset re-fork | step() :1608-1610 `_reset_worlds(done_ids)` 直後に `reset_to_phase(0, world_ids=done_ids)` 追加。**文言精密化 (CC2/CC4 収束)**: 現経路に fork 型 (reset_to_phase) 呼出は無し — `reseed_grip_open` :1031 は存在 (servo-gate 下・不変)、#6 挿入は その後 (restore-after-reseed 順、B4 順序依存として記録)。**no-op の構造化 (3者収束)**: `reset_to_phase` に k==0 明示 early-return (\_requested_phase 記帳後、bank lookup 前 — 挙動恒等 [\_requested_phase は tree-wide write-only 検証済]、B3 の k=0 bank entry 地雷を構造排除) | B1 |
| ~~R14~~ | ~~step-0 hook~~ | **v2 で B1 から削除 (CC6 HOLD + CC5-2 採択)**: B1 では k=0→0 が R6 と重複する dead-code。route_t := bank_boundary[k] の所有 = **B3** (R6 の label どおり)。CC3-CH5 の設計 note (env-side wiring / k≥1 fail-loud raise / call-order last) は **B3 carry** として §5 に登録 | B3 |
| R15 | flag-gate default-OFF | cfg `route_t_clock` default False。Rs 裁定 (envcore state.md:73) の指名計器 = ⑨a′ EXACT → **R17 v2 が充足** (v1 は未充足だった) | B1 |
| R16 | grep leg | **one-off 文書化コマンド + 出力を chunk evidence に pin** (新 script file は charter 未授権 = CC6 HOLD 採択; %12 が script 化を望めば 1-line 承認で昇格可)。許容 site 集合 = **正確に {alloc :483, per-world reset :1013, global reset :1593, increment :1602, timeout :1512}** を pattern-anchor・fail-closed (v1 の「horizon」は独立 site 無しの phantom 区分 = 削除; comment :1173-1174 は R3 で書換え済みになるため hit しない) | B1 |
| R17 | flag-OFF byte-preserve legs | **§1 v2 の env 側 leg 群 (⑨a′ / DoD⑤⑩ / DoD⑥ / cablediag byte-anchor) + producer 5-cell (route_executor 側)** — 全て既存 script/artifact 再利用 | B1 (毎 chunk 継承) |

## §3. est LOC / 触るファイル (v2)

newton_route_env.py (~90-160: R1/R2-R5/R6/#6/**stub v2 受け**) + route_env_config.py (~15) + route_executor.py (~45-85: RouteExecutor v2 + co-slice + k==0 guard) + test_routeexec_state_bank.py (~35-45: 判別力 world-slice case + 2 assert)。**計 ~185-305 ≤800 cap。** 新規 file ゼロ (grep leg = one-off、env legs = 既存 script)。task_config / locked producer / INVARIANTS 不触。

## §4. KNOWN_ALTERNATIVES (v1 から、CC6/CC4 の補正込み)

accessor / 全分岐 とも mirror と消費者接触行数は同等 (CC6 補正: v1 の非対称リスク記述を撤回)、grep 清浄度と凍結配管の一元性で mirror 維持。両代替は 5体でも再審され棄却 (CC4/CC5 VERIFIED-OK)。

## §5. 5体 disposition 全数 + carries + 依頼

**fold 済 (ACCEPT):** CC4-CH1/CC5-1 env-leg (CRIT/HIGH→§1・R17) / CC3-CH1 co-slice / CC3-CH2 判別 test / CC3-CH4+CC4-CH3+CC5-7 k=0 構造 guard / CC2-CH3+CC4-CH4 R13 文言 / CC2-CH1+CC4-CH2 allowlist+comment / CC2-CH2+CC3-CH6+CC4-CH5+CC5-5 cite 再anchor (4体) / CC5-6 stub 帰属 / CC6-HOLD① R14 削除 / CC6-HOLD② grep-leg 非file化 / CC6条件 route_t≡episode assert。
**REBUT (根拠付き棄却):** なし (全 challenge 受容 — v1 の誤りは実在した)。
**NO_ACTION 評価:** CC6 = core CHANGE_JUSTIFIED (spec 明示要求 + 既存機構の代替不能をコード実読で確認) → NO_ACTION 棄却。
**B3 carries (CC5-3 の無所有者 crack + R14 繰延分、B3 conformance 表の必須行として登録):** (i) fork 時 G1..Gk latch pre-set (spec §6.2-3/-6 — HOLD arming「1 step 目から有効」の前提) (ii) route_t := bank_boundary[k] wiring (env-side、call-order = reset 系の最後、k≥1 で boundary 未定義なら fail-loud raise) (iii) post-fork assert route_t == bank_boundary[k] (iv) writesite 期待値反転 (v) forbid_banked_fork 撤去 (vi) k=0-bank-entry 禁止不変量の維持。
**%12 への依頼 2 点:** (a) **charter ERRATUM-2** (1-line): B1 DoD セル「test_routeexec_writesite・state_bank の期待値更新」→「state_bank world-slice case 追加 + writesite 不変-PASS assert (反転 = B3、spec §4.1 verbatim)」 (b) grep-leg の script file 化を望むか (現 plan = one-off + evidence pin; script 化なら 1-line 授権を)。

*%11 — PAPER-ONLY。build = %12+%9 verify + [RULE-CHECK] 後。*
