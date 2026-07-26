# 腕側 consumer レビュー材料 — `GRASP_Z` / `PUSH_Z` / `EE_TO_FINGERTIP`（p11 ARM-CONTROL-DESIGN）**v4**

**依頼:** `MSG-PN-P11-FINGERTIP-BOUNDARY-MATERIALS-20260726-001`。
**⭐ 本 v4 が応答する RETURN（**9 通を 1 つの最終 bundle に fold**）:** ⚠ **記録訂正（pN **B14** 受理・2026-07-26 18:31:33 JST）**: `d02385cca42e93c72a1aa92b60890ca1c495a8b8` の本行は **「8 通」と書いていたが、列挙は 9 要素**だった（`-004`(B6) / `-005` / B7 / B8 / B9 / B10 / B11 / B12 / B13）。⇒ **数え違いは私の欠陥。9 通に訂正。** ⛔ **旧 commit `d023…` は immutable のまま保全**。
⚠⚠ **bank 後に届いた `B14`〜`B30` は §5.4 に別列挙する。⛔ 上の「9 通」に算入しない**（＝ **count を再帰的に増やさない**・pN 指示）。 `MSG-PN-P11-FINGERTIP-MATERIALS-V3-RETURN-20260726-004` の **残件 B6** ／ `MSG-PN-P11-FINGERTIP-B6-LIVEWORD-20260726-005` ／ **B7**（records coherence）／**B8**（比の根拠外し）／**B9**（再測定不要の撤回）／**B10**（方向断定の撤回）／**B11**（全桁 SHA・未読対象）／**B12**（sizing 点の統一）／**B13**（command の型）。**R1〜R5 は `-004` で PASS 済**。
**⭐ 全件受理・全件私の欠陥・争点 0。** 撤回/narrow の全件表 = **§5.3（#6〜#15）**。⛔ **値・参照点・方式・owner を選ばない／全 gate CLOSED は不変。**
**B7 = 受理。私の欠陥。** ①「T-4〜T-8 は行を読んでいない」という fence が**事実に反していた**（T-7 の行の中身を記述していた）⇒ **検証の深さを tier と別軸にし、D-1 10 file / D-2 21 file を全件列挙**（§R4-b）。②「consumer 判定を一切下していない」という**全称形を narrow** ⇒ **(α) 静的な call / use の記述は行う／(β) runtime・production 到達性は UNVERIFIED で推論しない／hit table 単独では consumer を確立しない**（§R3 (e)）。
**B6 = 受理。私の欠陥。** 「cable に実際に触れるのは pad body」を**測定された接触面の主張として撤回**し、**実際の接触 geom / 面は UNMEASURED** と明記。**J-b / J-c は「ラベルの付いた参照点」としてのみ保持**。⇒ 本体は §1 (2) ／ §4 ／ **§5.3 #6**。
⭐ **同一の言い方が私の別 artifact（測定 spec §H-4/§H-4.1 → **v1.8**・設計 doc §5.4）にも残っていたので同時に訂正した**（型 6「指摘された 1 箇所だけ直す」の再発防止）。
**⭐ 併せて `MSG-PN-P11-FINGERTIP-B6-LIVEWORD-20260726-005` も受理**: 「**live** の acquire-grasp consumer」を **p5 帰属の未決事実／照会依頼として残さない**。⇒ **①呼び出しの連鎖は banked source に実在（immutable）／②runtime・production での到達性は UNVERIFIED** の 2 段で書き、**p5 への新規照会は出さない**（本書 §1 (1) ／ 設計 doc §5.4）。
**v3 が応答した RETURN:** `MSG-PN-P11-FINGERTIP-MATERIALS-V2-RETURN-20260726-003`（**R1〜R5**）。
⚠ **`…-002` は pN 自身が全面 RETRACT 済**（pN の shell quoting により C2 payload が壊れた ＝ **cause = pN**、p11 の記録に帰責なし）。⇒ **本書は `-003` のみに応答する。** `-002` の C1〜C4 は operative でない。

**⭐ R1〜R5 は 5 件とも受理する。5 件とも私の欠陥である**（争点なし）。

**correction chain（履歴 rewrite なし・v1/v2 とも git 履歴に保持）:**

| 版 | literal path | commit | sha256（全 64 桁） |
|---|---|---|---|
| **v1** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_ARM_TARGET_CONSUMER_REVIEW_20260726.md` | `55d95a35f6b894dd54020fa0ec0eeb2ac8a89d1d` | `e561b53f49243a9742279e56720dc2267d1feff1ebe23012b71ea0a077819236` |
| **v2** | 同上（同一 path） | `1a2b63450b312bac6aa7468d60422056d40d02ab` | `09796ed5e1a4cb594d99aa69b64a2116470aa3639e3e6f090d578c0e0e111f09` |
| **v3** | 同上（同一 path） | `5f57b9421964779692277be32be36eaeeba7a6e2` | `943c1a9f976a467dd04b3f4703e5193d1f026e14b64ab74d619a881958295b91` |
| **v4** | 同上（同一 path） | **本書を bank した commit**（file は自身の commit を pin できない ⇒ **routing 提出の宣言値が権威**） | 同左 |

**起草時刻（`date` 実測）: 2026-07-26 17:57:07 JST。** ⚠ **権威ある時刻は本書を bank した commit の author time**（上記）。

⛔⛔ **owner を選ばない ／ 値を選ばない ／ 方式を選ばない ／ 推奨を書かない。** 分類は p5 側材料と合流後に **p17**。
**scope:** 設計/記録材料のみ。⛔ source / `[CHANGE]` / 実装 / RUN / verify / status / gate flip は CLOSED。**H-3.1 GO 無し・H-4 全体 HOLD・class B HOLD** も不変。

---

## R1 応答 — ⭐ `changed=[]` を撤回し、**可変な作業ツリーへの参照を全廃**する

⛔⛔ **v2 の欠陥（受理）**: v2 §B1 は「読取前後の `git status --porcelain` が同一 ⇒ `changed=[]`」と書いた。**これは述語として成立しない** — **既に ` M`（modified）である file は、中身の byte が変わっても ` M` のまま**であり、`git status` の出力は同一になる。⇒ **その比較は「変わった／変わらない」を見分けられない。** ⛔ **`changed=[]` を撤回する。**

**⭐ v3 が採る道 = `-003` R1 の第 1 案**: **可変な作業ツリー（WT）への参照・as-read hash・bracket 主張を全廃**し、**immutable な commit 上の path だけを cite する。**

- **本書の全 cite 元 = `1a2b63450b312bac6aa7468d60422056d40d02ab:<path>`**（= v2 を bank した commit。**immutable**）。
- ⇒ 第三者は `git show 1a2b63450b312bac6aa7468d60422056d40d02ab:<path>` で**同一 byte を再現できる**。WT の状態に依存しない。
- ⛔ **本書には WT の行番号・WT の hash・WT の clean/dirty 主張を一切書かない。**（v2 §B1 の as-read 列・taxonomy 列は**削除**。v2 は履歴に残る。）

⚠ **v2 で「committed 行番号」として示した値は、本 v3 でも同一**（下記 §R2 の manifest 上で全件を再検証した。検証方法 = `git show <commit>:<path> | sed -n '<L>p'` を cite した全行に実行）。**v2 のこの部分は取り消さない。**

---

## R2 応答 — ⭐ query 入力を **全件・全桁 pin** する（31 file）

⛔⛔ **v2 の欠陥（受理）**: v2 の manifest は **10 file** しか載せず、しかも blob / sha256 を **16 桁に切り詰めていた**。一方 §B2 の結論は **21/11/19 file** を対象にしていた。⇒ **結論の入力が pin されていなかった。**

**⭐ 以下が §R3 の query が返した `.py` file の union = 31 件。全件・全桁。**（tree = `1a2b63450b312bac6aa7468d60422056d40d02ab`）

| # | path | blob SHA-1（全 40 桁） | 内容 sha256（全 64 桁） |
|---|---|---|---|
| 1 | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` | `03913fec72de452ac01b5f6b68d9e686f210b340` | `b5b35c0e58bdace60775e456acc22c614501ecbb75eb4027323dd85df1aea108` |
| 2 | `thread_isaac_lab/configs/mpc_config_grip.py` | `6795ad3ad463940a4e8be7ee12d2733cbe3da873` | `62b20692d59d8e9fb3325c12f28b301499ac2e1ac2acdce5b69d370b79268cbf` |
| 3 | `thread_isaac_lab/configs/mpc_config_ic.py` | `cc00d69370bf7362fa5b5b0b1040561165894ca4` | `37d185fcaced27caf1539a08d6d96504799934f02a4a61c6bfd0b0c3b2d69699` |
| 4 | `thread_isaac_lab/configs/task_config.py` | `d86380dbe186af003d97465376690c9eba00e9ed` | `1a0851db9cfc2c740c98821c73c84f5405d1cc96df5fe22a71f66906bb1762bc` |
| 5 | `thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py` | `515ebfbb63cc69797c9b25c532d31d5597669332` | `73ac245268084472574555fc7e03f3ec6cfeff78f78bfaef96d0ea25699221cd` |
| 6 | `thread_isaac_lab/envs/newton_grip_env.py` | `ae5985759fe30b8505f6a5914340932443ea70ac` | `1207554b257c97e3115fca303860bb25e072b5c69cb9bc0fef783d8c8267d147` |
| 7 | `thread_isaac_lab/envs/newton_skill_env_base.py` | `aaf15111377ac0c0e32fafeffdf8309a919245dd` | `e7a67ee34c50b78ff02baba4ab1bfe7b6002b1b2dfee15948e2c6795ad954fb9` |
| 8 | `thread_isaac_lab/envs/route_executor.py` | `46f49d2722dbceda3c732f282e3fc6902cf51cbd` | `09db5a6d7e9d28e9eebdcf568636b8f059545c077f919fa8e1f9e7014082c599` |
| 9 | `thread_isaac_lab/scripts/build_aerial_regrasp_precondition.py` | `0447834b6d9c42fc8027acfb5c43d92f0ef5aee6` | `bc2c77afc048b5e8b3732fcb1daf0612bf44ce98b067f96fcd115ab3f532d89d` |
| 10 | `thread_isaac_lab/scripts/build_unclamp_precondition.py` | `6062bf9555ea896a231274e616acc65d6d10f600` | `a2c5a297df9b261b1efa19b7cd6614802cdfcc34c8840135b5bf66a643f70b10` |
| 11 | `thread_isaac_lab/scripts/collect_expert_demos.py` | `5fc8f570ff10e6cf5bbddf74e4c8a225db613922` | `8e0b9c795a9d4a316eda845d219f5e34f16c2fe934f6e6e39603148d888090e9` |
| 12 | `thread_isaac_lab/scripts/demo_aerial_regrasp.py` | `15b0fa0eb3d798e52e4001c78693f6d053b7bf4a` | `97867b59b80ac67974f711fa7dcf64613ae9422024d4c06c8f965403e89578d7` |
| 13 | `thread_isaac_lab/scripts/dry_run_39step.py` | `5d34ed07295a24f6ab350d373245c33a7fc18a68` | `a0d40364ec8863eb33d3ac2182a8b07d9267e9b2c15b7bb93c25edcb38d88b07` |
| 14 | `thread_isaac_lab/scripts/dry_run_approach_cable.py` | `b58ccde391d95a542a7d5f47ec080913d946ff9b` | `8489984b5d2965a03823bdc57407c75a5269b7ab587ec911120b84b61a7ee51c` |
| 15 | `thread_isaac_lab/scripts/eval_skill.py` | `a6060dd9a26be22d2d4df9f26bc89c4797506dcc` | `f69080bc9fe4a18cf8878607d0fe81805c685b82b0c3e17aa564bbc948cad739` |
| 16 | `thread_isaac_lab/scripts/generate_demos_mppi_m3_ar.py` | `c0dc66af122b895961c89bf081527b74005a7c69` | `b26b0faab46d56ded310fa67db3141727c3b529dd2c3a2c8d72420edca3fc9c4` |
| 17 | `thread_isaac_lab/scripts/m4_phase0_verify_ee_clamp.py` | `3683b0060536f70160f0304cf00e70ef39f2778a` | `056e2a2903c8963670850a5bfa90c68583feafcb9449f7d02a4a2eadcc8d8ad7` |
| 18 | `thread_isaac_lab/scripts/measure_finger_extent.py` | `fc65fb0029feb4e14a9f42278ab0545785b98a5d` | `bf28375497767681a62512cdf4d9b8b25bfde03889a3d0a5ef7f937b991a9c95` |
| 19 | `thread_isaac_lab/scripts/newton_routing_utils.py` | `b6eaf1a828feef00ae149179dc49d3fe90a8725d` | `bac4fbc92984b2e506ce095b7ee5d6ce4641da87536ad351269dae4995ecc137` |
| 20 | `thread_isaac_lab/scripts/plot_fingertip_waypoints.py` | `214626b5ebf4de4a6b37506643f2630776cd7953` | `4e457c89fb00b821df095588a6bcc62ff2d52b6f059656b8cc313815797d2fe2` |
| 21 | `thread_isaac_lab/scripts/test_arm_reachability.py` | `d213605ae220b0280791b195ee04a052932513a4` | `a396074af94f5f46e915b571671d74bbf3e2db0f0f5c092cc883cf439c09744e` |
| 22 | `thread_isaac_lab/scripts/test_clip_routing.py` | `b8cbe0e9a4a8d60cee865f166a07bbcbe50c56f7` | `677538ec8a3b9c5a26e9f78086ccc16c3ac2b287d5db0c0e165231169cd1315f` |
| 23 | `thread_isaac_lab/scripts/test_diagonal_reach.py` | `09b3bf77e63f1b3b4297ce29154d26c16e5c2740` | `8c6cc1f3b6ebb47a15165fb3172a47d68cfd148daac76ca85932c8f4c9a8ec05` |
| 24 | `thread_isaac_lab/scripts/test_grip_modes.py` | `bb633944a2b90e3b8ed1be0cea7811374e161553` | `2d0c7e7371b5731b94ab599be6865921a7a8474dae482b8071cae4b13c838247` |
| 25 | `thread_isaac_lab/scripts/test_motion_sequence_dry_run.py` | `64e2d39a299de40c7c8905b5da9e4fc74d25365a` | `51a909e36f90c0b18419caddb43955e9aff94b9c3b6885c7b9d2b026f45d8765` |
| 26 | `thread_isaac_lab/scripts/test_newton_20clip_reachability.py` | `c7b248719a38eb5dd9b0f98fe88b14aa11e71ace` | `e6f68b786bc51e5d0b4e1a6c23ff1a59e7253919f59b5bb346db8275789b7292` |
| 27 | `thread_isaac_lab/scripts/test_newton_clip_routing.py` | `69a588d75f08b3c15e752c5211b7d64cef5f5be6` | `2e1fc1d84539877f91cc75eb1f6443a628dfb0743bd24cb7f0e8a1ab956779dd` |
| 28 | `thread_isaac_lab/scripts/test_newton_clip_routing_sdf_plain.py` | `5136e02477ed4ea248ef5638f7e88fd201bce100` | `8e817bbf2bba16dce123e11a18d37c76ef5d7bf4929107836de59486a66b4c3a` |
| 29 | `thread_isaac_lab/scripts/test_newton_dual_clip_routing.py` | `73b8cb6456fb83772ef9896b7c9c4104b9197dcb` | `a5426a3e756cf3fc30436e7cf8bf4bac41a17b65470a42cda210ded74952d86b` |
| 30 | `thread_isaac_lab/skills/scripted_skills.py` | `e8faa50c30f7d65b27bf52179fc23b6c69d758c8` | `3586a1954720f82950a6f1e0698a621cdb1c7e2c2556efdf0bfc5f93f8889fca` |
| 31 | `thread_isaac_lab/skills/step_table.py` | `1e18a63dcf14d9c6278d2c1fd094a447d1003696` | `6f9c3fb3d0010721c9287b8b63e2e86e7cecd7210e8ee8c2f222becaf3e5422b` |

⇒ **§R3 の集計対象 file と §R2 の manifest は同一集合（31 = 31）。** v2 の 10 対 21/11/19 という乖離は解消。

---

## R3 応答 — ⭐ query の**完全な定義**と**全件出力**

⛔⛔ **v2 の欠陥（受理）**: v2 は「`grep -rn` を truncate せず集計・`thread-vault/` 除外」としか書いておらず、**root / include-exclude 集合 / 行と出現の別 / 測った tree** を一つも定義していなかった。⇒ **再現不能**。しかも測った対象は **可変な作業ツリー**だった。⇒ **v2 の 99/21・53/11・74/19 を撤回する。**

### (a) query の定義（**literal**）

```
git grep -c -w -e GRASP_Z         1a2b63450b312bac6aa7468d60422056d40d02ab -- '*.py'
git grep -c -w -e PUSH_Z          1a2b63450b312bac6aa7468d60422056d40d02ab -- '*.py'
git grep -c -w -e EE_TO_FINGERTIP 1a2b63450b312bac6aa7468d60422056d40d02ab -- '*.py'
git grep -o -w -e <SYMBOL>        1a2b63450b312bac6aa7468d60422056d40d02ab -- '*.py' | wc -l
```

| 項目 | 定義 |
|---|---|
| **測った tree** | **commit `1a2b63450b312bac6aa7468d60422056d40d02ab`**（immutable）。⛔ 作業ツリーではない |
| **root** | repository root（`git grep` の既定 = 指定 tree 全体） |
| **include** | pathspec **`'*.py'` のみ**（repo 全域。`eval_runs/` 配下の `.py` も含む） |
| **exclude** | **無し**（⛔ v2 の「`thread-vault/` 除外」は撤回 — `.py` scope には `thread-vault/` 配下の `.py` が 0 件ゆえ除外規則自体が不要） |
| **一致の意味** | **`-w` = 語境界一致**（symbol としての一致）。⇒ `EE_TO_FINGERTIP_provenance` のような**別 identifier は数えない** |
| **行 vs 出現** | `-c` = **一致した行数**（1 行に 2 回出ても 1）／`-o \| wc -l` = **出現回数**。**両方を別々に出す** |
| **自己参照** | **`.py` scope には本書（`.md`）は入らない ⇒ 自己参照 0**。（全 file scope では本書自身が数に混ざる — 下記 (d)） |

### (b) 合計（**`.py` scope・上記 tree**）

| symbol | 一致した行数 | 出現回数 | file 数 |
|---|---|---|---|
| `GRASP_Z` | **105** | **126** | **22** |
| `PUSH_Z` | **55** | **60** | **13** |
| `EE_TO_FINGERTIP` | **73** | **78** | **18** |

⚠ **`-w` を外す（部分一致）と `EE_TO_FINGERTIP` だけ 74 行/18 file** になる。差分 **+1 行**の正体は `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` の **`EE_TO_FINGERTIP_provenance`**（= **別の identifier**）。`GRASP_Z` / `PUSH_Z` は `-w` 有無で不変（105/22・55/13）。

### (c) **全件・per-file 出力**（`一致行数 / 出現回数`、`—` = 0 件）

| path | `GRASP_Z` | `PUSH_Z` | `EE_TO_FINGERTIP` |
|---|---|---|---|
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` | — | — | 5 / 6 |
| `thread_isaac_lab/configs/mpc_config_grip.py` | 1 / 1 | — | — |
| `thread_isaac_lab/configs/mpc_config_ic.py` | — | — | 1 / 1 |
| `thread_isaac_lab/configs/task_config.py` | 3 / 3 | 1 / 1 | 5 / 5 |
| `thread_isaac_lab/envs/newton_approach_cable_mujoco_env.py` | 1 / 1 | — | — |
| `thread_isaac_lab/envs/newton_grip_env.py` | 3 / 3 | 3 / 3 | 3 / 3 |
| `thread_isaac_lab/envs/newton_skill_env_base.py` | — | — | 3 / 3 |
| `thread_isaac_lab/envs/route_executor.py` | 1 / 1 | 1 / 1 | — |
| `thread_isaac_lab/scripts/build_aerial_regrasp_precondition.py` | 8 / 9 | — | 3 / 3 |
| `thread_isaac_lab/scripts/build_unclamp_precondition.py` | — | 3 / 3 | — |
| `thread_isaac_lab/scripts/collect_expert_demos.py` | 3 / 3 | 1 / 1 | — |
| `thread_isaac_lab/scripts/demo_aerial_regrasp.py` | 1 / 1 | — | 3 / 3 |
| `thread_isaac_lab/scripts/dry_run_39step.py` | 2 / 2 | 1 / 1 | — |
| `thread_isaac_lab/scripts/dry_run_approach_cable.py` | 4 / 5 | — | 2 / 2 |
| `thread_isaac_lab/scripts/eval_skill.py` | — | — | 1 / 1 |
| `thread_isaac_lab/scripts/generate_demos_mppi_m3_ar.py` | 4 / 4 | — | 6 / 6 |
| `thread_isaac_lab/scripts/m4_phase0_verify_ee_clamp.py` | — | — | 5 / 5 |
| `thread_isaac_lab/scripts/measure_finger_extent.py` | — | — | 3 / 5 |
| `thread_isaac_lab/scripts/newton_routing_utils.py` | 5 / 5 | 7 / 7 | — |
| `thread_isaac_lab/scripts/plot_fingertip_waypoints.py` | 2 / 2 | — | 2 / 2 |
| `thread_isaac_lab/scripts/test_arm_reachability.py` | 5 / 9 | — | — |
| `thread_isaac_lab/scripts/test_clip_routing.py` | 10 / 11 | 11 / 11 | — |
| `thread_isaac_lab/scripts/test_diagonal_reach.py` | 13 / 13 | — | — |
| `thread_isaac_lab/scripts/test_grip_modes.py` | 5 / 5 | — | 3 / 3 |
| `thread_isaac_lab/scripts/test_motion_sequence_dry_run.py` | 11 / 20 | — | 3 / 3 |
| `thread_isaac_lab/scripts/test_newton_20clip_reachability.py` | 5 / 8 | — | 2 / 2 |
| `thread_isaac_lab/scripts/test_newton_clip_routing.py` | 7 / 8 | 9 / 11 | 12 / 13 |
| `thread_isaac_lab/scripts/test_newton_clip_routing_sdf_plain.py` | 6 / 7 | 8 / 10 | 11 / 12 |
| `thread_isaac_lab/scripts/test_newton_dual_clip_routing.py` | 5 / 5 | 6 / 6 | — |
| `thread_isaac_lab/skills/scripted_skills.py` | — | 2 / 2 | — |
| `thread_isaac_lab/skills/step_table.py` | — | 2 / 3 | — |

### (d) 参考: **全 file scope**（pathspec 無し・同 tree・`-w`）

| symbol | 一致した行数 | 出現回数 | file 数 |
|---|---|---|---|
| `GRASP_Z` | 164 | 192 | 37 |
| `PUSH_Z` | 95 | 105 | 25 |
| `EE_TO_FINGERTIP` | 155 | 167 | 57 |

⚠⚠ **この scope は本書自身を数えている**（`P11_ARM_TARGET_CONSUMER_REVIEW_20260726.md` の v2 が `GRASP_Z` 16 行 / `PUSH_Z` 11 行 / `EE_TO_FINGERTIP` 16 行）。**報告が自分を数に入れている。** ⇒ **consumer の議論には `.py` scope (b)(c) を使う。**

### (e) ⭐⭐ **これは文字列の hit 数であって consumer 数ではない**（pN R3 の指摘を受理）

- **hit には import 行・docstring・comment・変数への再定義・log 文字列が含まれる。** これらは「その定数がその file の**振る舞いを決めている**」ことを意味しない。
- ⇒ 本書は **`.py` scope の hit を「その symbol が現れた file と行の全体」としてのみ提示する。**
- ⛔⛔ **narrow（RETURN B7 受理）**: 旧文の全称形「**consumer である／operative であるという判定は本書では下していない**」は、**後段 §1〜§3 で個々の行の静的な使われ方を記述している**ことと衝突していた。⇒ ⭐ **正しくは 2 段に分ける**:
  - **(α) 静的な call / use の記述** — 「この行がこの symbol を import している／target の z に入れている／docstring である」は **banked source を読んで書いた記述**であり、**本書はこれを行っている**。
  - **(β) runtime / production で到達するか** — ⛔ **UNVERIFIED。本書は一切推論しない。** **(α) から (β) を導かない。**
  - ⇒ ⛔ **hit table 単独では consumer を確立しない**（数は文字列の出現であり、(α) でも (β) でもない）。

---

## R4 応答 — ⭐ tier を **構造 tier（status = UNVERIFIED）** に改める

⛔⛔ **v2 の欠陥（受理）**: v2 は tier を「**operative**（env / skill）」と名付けながら、同じ文書の中で「どこまでを operative と見なすかの判断は本書では行わない」と書いていた。⇒ **名付けが、下していないはずの判定を先取りしていた。**

**⭐ 訂正: tier は「path の構造上の位置」だけで決める。runtime 上の効き（operative か否か）は全 tier で `UNVERIFIED`。**

| 構造 tier（path 位置のみ） | file（**全件**） | runtime status |
|---|---|---|
| **T-1 定数定義 / config** | `configs/task_config.py`・`configs/mpc_config_grip.py`・`configs/mpc_config_ic.py` | **UNVERIFIED** |
| **T-2 env** | `envs/newton_grip_env.py`・`envs/newton_skill_env_base.py`・`envs/newton_approach_cable_mujoco_env.py`・`envs/route_executor.py` | **UNVERIFIED** |
| **T-3 skills** | `skills/scripted_skills.py`・`skills/step_table.py` | **UNVERIFIED** |
| **T-4 builder / demo / generator** | `scripts/build_aerial_regrasp_precondition.py`・`scripts/build_unclamp_precondition.py`・`scripts/collect_expert_demos.py`・`scripts/demo_aerial_regrasp.py`・`scripts/generate_demos_mppi_m3_ar.py` | **UNVERIFIED** |
| **T-5 dry-run / eval / measure / plot** | `scripts/dry_run_39step.py`・`scripts/dry_run_approach_cable.py`・`scripts/eval_skill.py`・`scripts/m4_phase0_verify_ee_clamp.py`・`scripts/measure_finger_extent.py`・`scripts/plot_fingertip_waypoints.py` | **UNVERIFIED** |
| **T-6 test** | `scripts/test_arm_reachability.py`・`scripts/test_clip_routing.py`・`scripts/test_diagonal_reach.py`・`scripts/test_grip_modes.py`・`scripts/test_motion_sequence_dry_run.py`・`scripts/test_newton_20clip_reachability.py`・`scripts/test_newton_clip_routing.py`・`scripts/test_newton_clip_routing_sdf_plain.py`・`scripts/test_newton_dual_clip_routing.py` | **UNVERIFIED** |
| **T-7 routing utils** | `scripts/newton_routing_utils.py` | **UNVERIFIED** |
| **T-8 測定ハーネス** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py` | **UNVERIFIED** |

**3 + 4 + 2 + 5 + 6 + 9 + 1 + 1 = 31**（§R2 manifest と一致）。

⛔⛔ **訂正（RETURN B7 受理）**: 旧文「**T-4〜T-8 は file 単位でのみ列挙し、行単位では読んでいない**」は **事実に反していた** — 後段 §2 (1) / §3 (1) で **T-7 `newton_routing_utils.py` の個々の行の中身**（`:53` / `:1295` / `:1346` / `:1382-1383` / `:1529` / `:1568` / `:1587` / `:1602`）を記述しており、**それは targeted な行読みである**。⇒ ⭐ **検証の深さは構造 tier とは別の軸**なので、**tier で区切らず、実際に読んだ file を列挙して区切る**。

### R4-b ⭐ **検証の深さ**（構造 tier と独立の軸・31 file を 2 群に分割）

| 群 | 私が実際に行ったこと | file（**全件**） |
|---|---|---|
| **D-1 targeted 行読み（10 file）** | ⭐**再現 template（⛔ literal command ではない = B13）**:<br>`git show 1a2b63450b312bac6aa7468d60422056d40d02ab:<PATH> \| sed -n '<L>p'`<br>⚠ **`<PATH>` の exact 値 = 右欄の各 path**（省略なし）／**`<L>` の exact 値 = 本書の各引用（`§1`〜`§4` の `file:line`）にある**。⇒ **template ＋ 右欄 ＋ 各 citation の 3 つで、実行した command が一意に復元できる。** commit は **全 40 桁**（B11）。**この形で右欄の各 path × 引用した各行番号に対して実行し、行の中身を読んで本書に記述した** | `configs/task_config.py`・`configs/mpc_config_grip.py`・`envs/newton_skill_env_base.py`・`envs/newton_grip_env.py`・`envs/route_executor.py`・`envs/newton_approach_cable_mujoco_env.py`・`skills/scripted_skills.py`・`skills/step_table.py`・`scripts/newton_routing_utils.py`・`scripts/test_newton_20clip_reachability.py` |
| **D-2 lexical / file 単位のみ（21 file）** | **一致件数と path を数えただけ。行の中身は読んでいない** | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/arm_control_measurement_harness.py`・`configs/mpc_config_ic.py`・`scripts/build_aerial_regrasp_precondition.py`・`scripts/build_unclamp_precondition.py`・`scripts/collect_expert_demos.py`・`scripts/demo_aerial_regrasp.py`・`scripts/dry_run_39step.py`・`scripts/dry_run_approach_cable.py`・`scripts/eval_skill.py`・`scripts/generate_demos_mppi_m3_ar.py`・`scripts/m4_phase0_verify_ee_clamp.py`・`scripts/measure_finger_extent.py`・`scripts/plot_fingertip_waypoints.py`・`scripts/test_arm_reachability.py`・`scripts/test_clip_routing.py`・`scripts/test_diagonal_reach.py`・`scripts/test_grip_modes.py`・`scripts/test_motion_sequence_dry_run.py`・`scripts/test_newton_clip_routing.py`・`scripts/test_newton_clip_routing_sdf_plain.py`・`scripts/test_newton_dual_clip_routing.py` |

**10 + 21 = 31**（§R2 manifest と一致）。⚠ **D-1 は tier をまたぐ**（T-1・T-2・T-3・T-6・T-7 を含む）⇒ **「tier が下位だから浅く読んだ」ではない。**
⛔⛔ **D-1 / D-2 のどちらであっても、runtime / production での到達性は UNVERIFIED。** **読んだこと（静的）から、効いていること（実行時）を導かない。**

---

## R5 応答 — ⭐ 生き残っていた矛盾文を撤回

⛔⛔ **v2 の欠陥（受理）**: v2 は §B2（`:41`/`:59`）で「実質 consumer は Grip skill のみ」を**撤回**しながら、§2 (4)（`:123`）に **「現に分かれている（Grip skill のみが実質の consumer）」** を**生きたまま残していた**。⇒ **同一文書内の矛盾。** ⛔ **`:123` の当該括弧を撤回する**（下記 §2 (4) は訂正済み）。
⇒ **私の手続き上の欠陥**: 撤回した表現を**自分の全 artifact 横断で grep してから閉じる**という手順を、同一 file 内ですら実行していなかった。**v3 では 3 symbol ＋「実質」「のみ」で本書全体を再走査した。**

**v1 の sha256 も全 64 桁に展開済**（上記 correction chain）。

---

## 0. ⭐ 分類に効く 3 つの観測事実（値や owner の主張ではない）

以下すべて **tree = `1a2b63450b312bac6aa7468d60422056d40d02ab`** 上の行。

| # | 観測事実 | 出典（逐語） |
|---|---|---|
| **F-1** | **`GRASP_Z` / `PUSH_Z` は `route_c1_c2` code path では使われていない** | `route_executor.py:2450` 逐語「**GRASP_Z/PUSH_Z (task_config) are the LEGACY P1-P4 path, NOT** used by route_c1_c2 -> the route descent target is **GROOVE_CENTER_Z+ee_off (dynamic)**」 |
| **F-2** | ⭐**`route_c1_c2` code path の降下目標は「観測量」で作られている** — `ee_off` は**実行時に測った値**（EE の実 z − 把持中 cable 分節の実 z） | `route_executor.py:2900` `ee_off = float(get_ee_positions(state, scene_info)[1][2]) - _seg_z_mm(GRASP_YC) / 1e3` ／ 使用 `:3106` `seat_ee_z` / `:4214` `c2_seat_ee_z = GROOVE_CENTER_Z + _clip_float_z + ee_off` |
| **F-3** | ⭐**ある env は既に `EE_TO_FINGERTIP` から離脱し、実測コ字値を使っている** | `newton_approach_cable_mujoco_env.py:197` 逐語「…centerline (**NOT 40mm into the table via the stale Franka GRASP_Z=1.025**)」＋ `:200` `EE_Z_FLOOR_KO = TABLE_HEIGHT + CLIP_BASE_HEIGHT + CABLE_RADIUS + **EE_TO_PINCH_OPEN**`（`EE_TO_PINCH_OPEN = 0.26092`・`task_config.py:326`） |

⇒ **F-1〜F-3 は「3 定数が全 skill 共通の単一定数として実際に機能しているか」に直接効く**（本書 §4 の要求事実）。⛔ **どう分類するかは書かない。**

---

## 1. `EE_TO_FINGERTIP`（`task_config.py:78` = `0.220`）

### (1) 私が行単位に読んだ箇所（⛔ runtime status は UNVERIFIED）

| 箇所 | 位置 | 何に使っているか |
|---|---|---|
| **成功述語の測定点** | `newton_skill_env_base.py:899-905` `compute_clamp_pos` = `ee_pos + R(ee_q)·[0,0,+EE_TO_FINGERTIP]` | ✅**呼び出しの連鎖が banked source に実在する**（immutable）= `newton_grip_env.py:1158`/`:1164` `compute_clamp_pos` → `:1167` `cable_pos` → `:1169` `find_nearest_cable_point(...)` → `dist_pos` → `:1224` `clamp_r_ok = finite_measurements and (…)`（閾値 `CLAMP_DIST_THRESH = T_DIST` 2 mm・`:223`）。⛔ **runtime / production で到達するかは UNVERIFIED**（`MSG-PN-P11-FINGERTIP-B6-LIVEWORD-20260726-005` 受理。**source に在ること ≠ 実行時に効いていること**。⛔「live consumer」を未決事実としても依頼としても残さない・p5 への新規照会も出さない） |
| **cable 分節の探索窓** | `newton_grip_env.py:746` / `:752`（`right_tip[2] -= EE_TO_FINGERTIP` / `left_tip[2] -= …`） | 最近傍 cable 分節 index の決定（**z のみを引く軸固定の近似**・下記 (3)） |
| **positioning 定数の材料** | `task_config.py:93` `GRASP_Z` / `:95` `PUSH_Z` | 両者の定義式に含まれる |
| **p11 側 spec** | 測定 spec §H-4.1 **J-a**（`ee_pos + 0.220·ẑ_ee`） | **閾値が測っている点**として 3 参照点の 1 つ（他 = **J-b pad body** / **J-c** `EE_TO_PINCH_TIP_CLOSED 0.2757`）。⛔ **J-b / J-c は「ラベルの付いた参照点」としてのみ保持** — **接触面ではない**（B6） |
| ⚠ 自己申告 | `task_config.py:78` 逐語「FRANKA panda_hand->fingertip [m]」／`:84`「220mm, **Franka value; re-derive S6**」／`:324`「**EE_TO_FINGERTIP above (0.220) is the Franka/legacy**」 | **定数自身が legacy と宣言している** |

### (2) 腕側が必要とする measurement surface
- ⭐ **保持する原則（B12 に統一）**: **sizing に使う点は、将来 authority が確定する「成功評価の点」と一致していなければならない**（別の点で bar を立てると、満たしても判定は落ちる／その逆）。⛔ **どの点がそれかを本書は選ばない**（成功述語の測定面 = p5 court／定数そのものは UNCONFIRMED / HOLD）。⛔ **現行 3 点の縮約値だけでは、どの点にも evidence-grade の bar を立てられない**（方向つき 3 成分 Jacobian ＋ 認可 envelope まで HOLD）。
- ⛔⛔ **撤回（RETURN-004 **B6** 受理）**: 旧文「**接触の物理が起きる面は別**: cable に**実際に触れる**のは **pad body**（`GRIPPER_PAD_BODY_IDX = [9,13]`）」は、**測定された接触面の主張として撤回する。** ⭐**私が自分で読み直した反証**:
  - `task_config.py:37` 逐語 = `GRIPPER_PAD_BODY_IDX = [9, 13]  # BODY space: pad-carrying followers (contact-filter LOGIC;` ＋ `:38` 逐語 `pad GEOMETRY itself deferred to S5` ⇒ **この定数は接触フィルタの logic 用の index であり、pad の幾何自体は先送りされている。** ⇒ **どの geom が cable に触れるかを確定しない。**
  - `route_executor.py:2436-2437` 逐語「retention = the cable is **SANDWICHED between the two claws (f1ext bottom + f2ext top**, mouth ~10mm, Ø8 cable -> ~2mm play)」＋ `:2438` 逐語「The OLD **f1ext-only** gate **false-FAILed** "cable risen to the TOP claw under drag"」 ⇒ **触れる相手は 1 つに固定されない**（下爪に載る／drag で上爪へ上がる）。しかも `:2430`/`:2432`/`:2433` で **`pad1`/`pad2` geom と `f1ext`/`f2ext` geom は別集合**として列挙されている。
  - ⇒ ⛔⛔ **実際の接触 geom / 接触面は UNMEASURED。**（同結論を p5 も bank 済 — `P5_BOUNDARY_MATERIALS_CORRECTION_20260726.md:145` 見出し「B5 訂正 — 「物理接触面 = f1ext 爪先」を UNMEASURED へ」/ `:151`「**実際の接触 geom は UNMEASURED**」。⚠ **relay でなく、私が同 file を開いて確認した。**）
- **残る事実 = ラベルの付いた参照点どうしの差（⛔接触面の主張ではない）**: `EE_TO_PINCH_CLOSED 0.2548`（`:320` ラベル「wrist_3 -> pinch_mid drop」）／`EE_TO_PINCH_TIP_CLOSED 0.2757`（`:321` ラベル「pad TIP drop; コ f1ext claw tip」）／`EE_TO_PINCH_OPEN 0.26092`（`:326`）。⇒ **`0.220` との差は 34.8〜55.7 mm。** ⛔ **これを「判定面と接触面のずれ」と呼ぶ labeling は撤回**（B6）。⛔⛔ **さらに（B8 / B9）**: 旧文「差が効くのは **どの参照点で Jacobian を取るか**（＝mrad あたりの mm が変わる）まで」も **narrow** ⇒ 正しくは **「各参照点で **evidence-grade の Jacobian**（＝**方向つき 3 成分 ＋ 認可 envelope**）**を測る必要がある。差の量・方向・bar への帰結は UNVERIFIED**」（⭐**B15**: **proxy = 現行 H-4 の縮約 ＋ 1 姿勢の値は測定済**・⛔ **そこから bar を導かない**）**。⛔ **「2 mm 閾値の 17〜28 倍」は active な根拠から外す** — **2 mm は別の量（成功距離の閾値）**であり、比は **接触誤差も bar の倍率も違反も確立しない**。
  - ⚠ **B6 の読み方を明示する**（誤解があれば RETURN してください）: pN の指示「retract … *when labeled as contact-surface mismatch*」を、**接触面という labeling の撤回**であって**引き算そのものの撤回ではない**と読んだ。**全面撤回が意図なら、その旨の RETURN で即座に落とす。**
- ⇒ **腕側の要求事実**: 「**どの面で bar を立てるか**」が決まらないと gain の下限が確定しない。⛔ **どちらにすべきかは本書で言わない。**

### (3) frame / unit
- **unit = m**（`task_config.py` 全体の慣行）。
- **frame = EE body（wrist_3・local index 5・`task_config.py:30` `EE_BODY_IDX`）の local +Z**。⇒ `compute_clamp_pos` は **姿勢で回す**（`:905` `offset_world = quat_rotate_vec(ee_quat_xyzw, offset_local)`）。
- ⚠ **同じ定数が 2 通りに使われている**: `compute_clamp_pos` は **EE local の回転を掛ける**（`:905`）が、`newton_grip_env.py:746`/`:752` は **world z から直に引く**（`tip[2] -= EE_TO_FINGERTIP`）。⛔⛔ **訂正（pN **B17**）**: 旧文「⇒ **後者は EE が傾くと誤差を持つ**」は **どちらが正しいかを先取りしていたので撤回**。⇒ ⭐ **source から言えるのはここまで**: **2 つの構成が併存し、EE が傾いたとき両者の結果は一般に一致しない。** ⛔ **どちらが intended / correct か、その差を「誤差」と呼べるかは UNRESOLVED**（**frame の意図と権威ある測定点が未裁定** — p17 の taxonomy ＋ geometric / reward court の境界）。⛔ **是正も方式の選択も求めない。**

### (4) 要求事実（共通必要 / skill 別可分 / 観測量へ移せるか）
- **全 skill 共通である必要**: ⛔ **現状の実装は共通になっていない**（**F-3**: `newton_approach_cable_mujoco_env` は同じ役割に `EE_TO_PINCH_OPEN` を使い、`GRASP_Z=1.025` を「stale Franka」と明記）。⇒ **「共通でなければ成立しない」ことを示す実装事実は、私の court では観測されなかった。**
- **skill 別に分けられるか**: 現に **分かれている**（前項）。⚠ ただし acquire-grasp の判定式（`compute_clamp_pos`）と cable 窓選択（`:746`/`:752`）は**同一 env 内で同じ定数を共有**しており、この 2 つを分けた場合の影響は**私は測っていない**。
- **観測量へ移せるか**: ⭐ **`route_c1_c2` code path では移っている**（**F-2**）。⚠ ただし acquire-grasp の判定式は定数のままであり、判定面を観測量へ移す場合は **成功条件の変更**に当たる（＝ `/reward-design` の直交ゲート対象）。⛔ **可否は本書で判断しない。**

---

## 2. `GRASP_Z`（`task_config.py:93` = `TABLE_HEIGHT + CLIP_BASE_HEIGHT + EE_TO_FINGERTIP` = **1.025**）

### (1) 私が行単位に読んだ箇所（⛔ runtime status は UNVERIFIED）
| 箇所 | 位置 | 何に使っているか |
|---|---|---|
| **Grip env の把持開始高さ** | `newton_grip_env.py:113` import ／ `:142` **`GRIP_Z = GRASP_Z + CABLE_RADIUS`**（逐語「1.029m: fingertip at cable center Z (0.809)」） | 把持開始高さの定義 |
| MPC config（comment のみ） | `mpc_config_grip.py:110` 逐語「Grip P0 precondition already positions arms at GRASP_Z (cable-proximal).」 | 前提の記述（comment） |
| 到達性テスト | `test_newton_20clip_reachability.py:46` **独自に再定義** `GRASP_Z = TABLE_HEIGHT + EE_TO_FINGERTIP`（**`CLIP_BASE_HEIGHT` を含まない**） | ⚠ **task_config の定義と一致しない別式** |
| routing utils | `newton_routing_utils.py:53` import ／ `:1295` / `:1346` / `:1382-1383` に target の z として出現 | **D-1（行の中身を読んだ）**・静的な use の記述。⛔ **runtime / production 到達性は UNVERIFIED** |
| ⛔ **`route_c1_c2` code path** | — | **使っていない**（**F-1**） |

### (2) 腕側が必要とする measurement surface
- **これは「腕への指令 z」**（IK 目標）であり、**判定面ではない**。⇒ 腕側が要求するのは **指令が到達可能で、かつ静定後のたわみ込みで意図した面に載ること**。
- ⚠ **静的たわみが直に効く**: 実測 `τ_bias` 最大 **27.22 N·m** が `shoulder_lift`（`ke = 2000`）に載り **`Δq = 13.61 mrad`**（`arm_control_measurement_h2_report.json` の `h3_torque_budget.per_joint_H3_1`）。⇒ **指令 z と実現 z はずれる**。⛔ **ずれの手先 [mm] は未確定**（合成 `‖Σ_i jacp[:,i]·Δq_i‖` は**未実装・未認可**）。

### (3) frame / unit
- **unit = m**、**frame = world z**（`TABLE_HEIGHT` 起点の絶対高さ）。
- ⚠ **意味論は「fingertip が clip base top（= cable bottom）に来る wrist の z」**（`:93` 逐語）⇒ **`EE_TO_FINGERTIP` の意味に依存する派生量**。⇒ **`EE_TO_FINGERTIP` が変われば同じ式のまま値が動く。**

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（`route_c1_c2` code path は不使用 = F-1／到達性テストは別式）。
- **skill 別に分けられるか**: **同じ symbol が別の式で再定義されている実装事実がある**（`test_newton_20clip_reachability.py:46`）。⛔⛔ **v2 にあった「Grip skill のみが実質の consumer」は撤回済み**（R5）。**`.py` scope で `GRASP_Z` は 22 file に現れる**（§R3 (c)）。**どれが consumer かの判定は本書では下していない。**
- **観測量へ移せるか**: ⭐ **`route_c1_c2` code path 側は観測量**（F-2）。**Grip env 側で同じ移行が可能かは私は測っていない**（P0 前提の作り方に依存）。⛔ 判断しない。

---

## 3. `PUSH_Z`（`task_config.py:95` = 同式 = **1.025**・逐語「same as GRASP_Z」）

### (1) 私が行単位に読んだ箇所（⛔ runtime status は UNVERIFIED）
| 箇所 | 位置 | 何に使っているか |
|---|---|---|
| **scripted skill の押込目標** | `scripted_skills.py:39` import ／ `:88` `return (x, y, PUSH_Z)` | 押込みの EE 目標 |
| **工程表** | `step_table.py:32` import ／ `:97` `return (cx, ly, PUSH_Z), (cx, ry, PUSH_Z)` | 左右の EE 目標（1 行に 2 出現） |
| Grip env | `newton_grip_env.py:123` import ／ `:430-431` `ee_left/ee_right = (CLIP1_X, CLIP1_Y ∓ GRIP_HALF_SPAN, PUSH_Z)` | 初期 EE 目標 |
| routing utils | `newton_routing_utils.py:53` import ／ `:1529` docstring ／ `:1568` target ／ `:1587` comment ／ `:1602` target | **D-1（行の中身を読んだ）**・静的な use の記述。⛔ **runtime / production 到達性は UNVERIFIED** |
| ⛔ **`route_c1_c2` code path** | — | **使っていない**（F-1） |

### (2) 腕側が必要とする measurement surface
- `GRASP_Z` と同じ（指令 z・判定面ではない）。⚠ **押込みは接触が効く局面**ゆえ、**「接触が効く瞬間の前に静定させる」要求が直接かかる**（静定判定は窓で行う）。
- ⚠ **`GRASP_Z` と数値が同一**（両者とも `1.025`）だが、**役割は別**（把持開始高さ vs 押込目標）。⇒ **値が同じことは、同じ量であることを意味しない。**

### (3) frame / unit
- `GRASP_Z` と同一（**m / world z**・`EE_TO_FINGERTIP` 依存の派生量）。

### (4) 要求事実
- **全 skill 共通である必要**: ⛔ **現に共通ではない**（`route_c1_c2` code path 不使用）。⚠ ただし `scripted_skills.py` と `step_table.py` は**同じ値を共有**（`step_table.py:32` が `scripted_skills` から import）。⇒ **この 2 者の間では共通。**
- **skill 別に分けられるか**: **分けられている実装事実は、私が読んだ範囲には無い**（上記 2 者は共有）。⚠ **分けた場合の影響は私は測っていない。**
- **観測量へ移せるか**: **`route_c1_c2` code path に前例あり**（F-2）。⛔ **scripted 経路で可能かは未測・判断しない。**

---

## 4. ⭐ 3 定数を横に見たときの要求事実（分類の入力・⛔ 分類ではない）

| 軸 | 実測事実 |
|---|---|
| **共有の実態** | **`EE_TO_FINGERTIP` だけが 3 者の根** — `GRASP_Z` / `PUSH_Z` は**その派生量**（同じ式・同じ値 1.025）。⇒ **根を動かせば 2 つが同時に動く。** |
| **共通性** | ⛔ **3 定数とも「全 skill 共通」として機能していない**（`route_c1_c2` code path 不使用 = F-1／approach env は別値へ離脱 = F-3／到達性テストは別式） |
| **観測量への移行** | ⭐ **`route_c1_c2` code path では実装済**（`ee_off` = 実行時計測・F-2）。⚠ **成功述語側は定数のまま** ⇒ そこを移すのは **成功条件の変更**（`/reward-design` 直交ゲート対象） |
| **参照点の食い違い** | ⛔⛔**旧「判定面と接触面が 34.8〜55.7 mm 違う ＝ 2 mm 閾値の 17〜28 倍」は撤回**（**B6** = 接触面の labeling／**B8** = 比そのものを active な根拠から外す。**2 mm は別の量＝成功距離の閾値**であり、比は **接触誤差も bar の倍率も違反も確立しない**）。⇒ ⭐ **残るのは「pin された参照オフセットどうしの差 34.8〜55.7 mm」だけ**（判定式の `0.220` 対 `0.2548`/`0.2757`/`0.26092`・**引き算のみ／誤差も bar も導かない**）。⛔ **実際の接触 geom / 面は UNMEASURED**（`route_executor.py:2436-2438` = f1ext+f2ext の sandwich・f1ext-only は false-FAIL 実績／`task_config.py:37-38` = 接触フィルタ logic 用で pad 幾何は先送り）。⛔ **差の量・方向・bar への帰結は UNVERIFIED**（B8/B9）。⭐ **B15**: **proxy（縮約 ＋ 1 姿勢）は測定済**・**未測なのは方向つき 3 成分 Jacobian ＋ 認可 envelope**。⛔ **proxy から bar を導かない** |
| **散らばり** | **`.py` scope で `GRASP_Z` は 22 file・`PUSH_Z` は 13 file・`EE_TO_FINGERTIP` は 18 file に現れる**（§R3 (c) 全件）。⛔ **これは文字列 hit であり consumer 数ではない**（§R3 (e)） |
| **腕側の依存** | ⛔⛔ **撤回（B9）**: 旧「**面の選択それ自体は新たな measurement-design point を増やさない**（H-4 が 3 参照点を出す設計ゆえ）」。**3 点を出す設計であることは、出た量が十分であることを意味しない**。⭐⭐ **B15 の区別（両方とも真）**: ✅ **proxy は測定済** = 現行 H-4 の 3 点の値（`908ac4674576c3b936fe66866254d17691b6cc8e`・**各列を最大絶対成分に縮約 ＋ 1 姿勢**）。**「未測」ではない・消さない。** ⛔ **未測なのは evidence-grade** = **方向つきの完全な 3 成分 Jacobian ＋ 認可された envelope**。⇒ ⛔⛔ **proxy から bar への帰結を導かない。**⇒ ⭐ **今の時点で安全に言えること = pin された参照オフセットどうしが 34.8〜55.7 mm 違う、それだけ。** **権威ある参照点の選択 ＋ 認可された envelope 上の 3 成分 Jacobian が揃うまで、J と bar への帰結は UNVERIFIED。** **H-4 全体は HOLD 継続**（literal `(9,13)` の carry・envelope が 1 姿勢 等も残る） |
| ⚠ **同一定数の 2 用法** | `compute_clamp_pos` は **EE local の回転を掛ける**／`newton_grip_env.py:746`/`:752` は **world z から直に引く**。⇒ ⭐ **言えるのは「2 構成が併存し、EE が傾くと結果は一般に一致しない」まで**。⛔⛔ **旧「後者に誤差」は撤回**（**B17**）— **どちらが intended / correct か、差を「誤差」と呼べるかは UNRESOLVED**（frame の意図・権威ある測定点が未裁定。p17 taxonomy ＋ geometric / reward court の境界）。⛔ 是正も方式選択も求めない |

---

## 5. B3 / B4（**PASS 済・不変**）

- **B3**: 「**現行 route** / **production route**」という **status 主張を撤回**。source が示すのは **`route_executor.py` の `route_c1_c2` code path の挙動**のみ ⇒ 全箇所を「**`route_c1_c2` code path**」へ置換した。⛔ **どの route が現行かを述べる authority/status SSOT を私は exact-pin していない。**
- **B4**: 「**どれに決まっても再測定不要**」という**絶対主張を撤回**（v2）。⛔⛔ **v4 でさらに撤回（B9）**: その後継の「**面の選択それ自体は新たな measurement-design point を増やさない**」も**撤回**。⇒ **安全な現在の主張 = pin された参照オフセットどうしが 34.8〜55.7 mm 違う、それだけ。** **H-4 全体は HOLD 継続。**

## 5.1 非主張

- ⛔ **owner を書いていない**（`GRASP_Z`/`PUSH_Z`/`EE_TO_FINGERTIP` の court は **UNCONFIRMED / HOLD**・候補 p5 / p17 / p11 / p16）。**私は自分を owner とも他者とも書かない。**
- ⛔ **値・方式・推奨を書いていない。** 分類は p17（p5 側材料と合流後）。
- **p5 の材料を私は再解釈していない**（本書は**腕側の読み取り**のみ）。
- ⛔ **runtime / production で効いているか（到達するか）を、どの file についても判定・推論していない**（全 tier `UNVERIFIED`・§R4）。⚠ **静的な call / use の記述は行っている**（§R3 (e) の (α)）— **(α) から (β) を導かない**のが本書の線。⛔ **hit table 単独では consumer を確立しない。**
- **私が行の中身を読んだのは 31 file 中 10 file**（§R4-b D-1）。**残り 21 file は件数と path のみ**（D-2）。
- **未測と明記した項目**: ⭐**実際の接触 geom / 接触面 = UNMEASURED**（B6）／⭐**`compute_clamp_pos` 連鎖の runtime・production 到達性 = UNVERIFIED**（source には実在・`-005`）／手先たわみの合成量 `‖Σ_i jacp[:,i]·Δq_i‖`（**未実装・未認可**）／定数を skill 別に分けた場合の影響／Grip・scripted 経路で観測量へ移せるか／⭐**§R4-b の D-2 に挙げた 21 file の行の中身**（⛔ 旧「T-4〜T-8 の行単位の意味」は **D-1/D-2 の分割と矛盾するので撤回** = B11。**未読は tier ではなく D-2 の 21 file である**）／⭐**参照点の選択が J と bar に及ぼす帰結**（方向・量とも **UNVERIFIED**・B9）。

## 5.2 v2 から撤回した主張（全件）

| # | 撤回した v2 の主張 | 理由 |
|---|---|---|
| 1 | `changed=[]`（読取中に source は変わっていない） | `git status` は既に `M` の file の byte 変化を見分けられない（R1） |
| 2 | as-read WT hash（16 桁）と WT 行番号の対照表 | 可変な面への参照。immutable commit へ全面移行（R1） |
| 3 | **`GRASP_Z` 99 hit / 21 file・`PUSH_Z` 53 / 11・`EE_TO_FINGERTIP` 74 / 19** | root/include/exclude/行 vs 出現/測った tree が未定義 ＝ 再現不能。かつ可変 WT 上の測定（R3） |
| 4 | tier 名「**operative**（env / skill）」 | 下していないはずの runtime 判定を名付けが先取りしていた（R4） |
| 5 | §2 (4) 「（Grip skill のみが実質の consumer）」 | §B2 の撤回と同一文書内で矛盾（R5） |

## 5.3 v3 から撤回・narrow した主張（**B6** ＋ live-wording `-005` ＋ **B7**）

| # | 撤回した v3 の主張 | 理由（私が自分で読んだ反証） |
|---|---|---|
| 6 | 「**cable に実際に触れるのは pad body**」＋「**判定面と接触面が 34.8〜55.7 mm 違う ＝ 2 mm 閾値の 17〜28 倍**」という **接触面としての labeling** | ⛔**実際の接触 geom / 面は UNMEASURED**。①`task_config.py:37-38` は当該定数を **接触フィルタの logic 用**とし **pad の幾何は先送り**と明記 ⇒ 接触を確定しない。②`route_executor.py:2436-2438` は保持を **f1ext(下爪)+f2ext(上爪) の sandwich** と定義し、**f1ext のみを見た旧 gate は「cable が上爪へ上がった」場面で false-FAIL した実績**がある ⇒ **触れる相手は 1 つに固定されない**。③同 `:2430`/`:2432`/`:2433` で **`pad1`/`pad2` geom と `f1ext`/`f2ext` geom は別集合**。⇒ **J-b / J-c は「ラベルの付いた参照点」としてのみ保持**（差の引き算は残すが、接触面という呼び方は撤回） |
| 7 | 「**live** の acquire-grasp consumer」を **p5 帰属の未決事実**として持ち、かつ **p5 への照会依頼**として残していたこと | `MSG-PN-P11-FINGERTIP-B6-LIVEWORD-20260726-005`。p5 が既にこの区別を閉じている。⇒ ⭐**①呼び出しの連鎖は banked source に実在（immutable）／②runtime・production 到達性は UNVERIFIED** の 2 段で書く。⛔**新規照会は出さない** |
| 8 | 「**T-4〜T-8 は file 単位でのみ列挙し、行単位では読んでいない**」という fence | **B7**。⛔**事実に反していた** — T-7 `newton_routing_utils.py` の個々の行の中身を §2 (1)/§3 (1) で記述している。⇒ **検証の深さは tier と別軸**として **D-1（10 file）/ D-2（21 file）** に列挙し直した（§R4-b） |
| 9 | 「**consumer である／operative であるという判定は本書では下していない**」という**全称形** | **B7**。後段の静的 use 記述と衝突。⇒ **narrow**: **(α) 静的な call / use の記述は行う ／ (β) runtime 到達性は UNVERIFIED で一切推論しない ／ hit table 単独では consumer を確立しない**（§R3 (e)） |
| 10 | 「**34.8〜55.7 mm ＝ 2 mm 閾値の 17〜28 倍**」という**比**、および「**どの参照点で Jacobian を取るかで bar が変わる**」 | **B8**。**2 mm は別の量（成功距離の閾値）**であり、比は **接触誤差も bar の倍率も違反も確立しない**。⇒ **比は active な根拠から外す**（引く場合は**引き算のみ・誤差も bar も導かない**と明記）。**「bar が変わる」は「各参照点で Jacobian を別途測る必要がある。差の量・方向は UNMEASURED」へ narrow** |
| 11 | 「**面の選択それ自体は新たな measurement-design point を増やさない**」（B4 の後継） | **B9**。**3 点を出す設計であることは、出た量が十分であることを意味しない** — 現行 H-4 は **各列の最大絶対成分への縮約 ＋ 1 姿勢**で、**方向つき 3 成分 Jacobian でも envelope の証拠でもない**。⇒ **既出値（127〜133 mm/rad 等）を bar 変化の根拠に使わない。安全な現在の主張 = pin された参照オフセットどうしが 34.8〜55.7 mm 違う、それだけ** |
| 12 | 「**J-a/J-c は gripper のたわみを含まず、感度は過小側**」 | **B10**。**方向の断定**。`gripper_dof_contribution` を含まない事実は残すが、**task に効く感度に対し過小か過大かは UNVERIFIED**（p0 逐語が出所でも私の根拠として再伝播しない） |
| 13 | 「**H-4 を 3 点で出せば、どの点でも bar を立てられる／本設計はこの未確認に依存しない**」（設計 doc）＋「**PD sizing はこの点（J-a）で行う**」（spec） | **B12**。⇒ **保持する原則は「sizing 点は将来 authority が確定する成功評価の点と一致させる」だけ**。**J-a sizing は conditional proposal（authority の点が J-a だった場合）であり現行採択ではない**。**現行の縮約値だけではどの点にも evidence-grade の bar を立てられない** ⇒ **方向つき vector ＋ 認可 envelope まで HOLD** |
| 14 | D-1 の evidence command に**省略 SHA `1a2b63450b…`** を使ったこと／§5.1 に残っていた「**T-4〜T-8 の行単位の意味 = 未測**」 | **B11**。⇒ command を **全 40 桁 `1a2b63450b312bac6aa7468d60422056d40d02ab`** へ。**未読対象は tier ではなく §R4-b の D-2 の 21 file**（D-1/D-2 分割と整合） |
| 15 | D-1 の欄を「**実行した command（literal）**」と称しながら `<PATH>` / `<L>` の placeholder を含めていたこと | **B13**。**placeholder を含むものは literal command ではなく template**。⇒ 見出しを **「再現 template」** に訂正し、**exact path = 右欄／exact 行番号 = 各 citation** と明記（pN 提示の (a)） |

## 5.4 ⭐ **bank 後の訂正**（**B14〜B38**）— ⛔ **上の 9 通の count には算入しない**（別列挙・再帰的に増やさない）

⚠ **上 §5.3 の #6〜#15 は「original return bundle = 9 通」に対する撤回表**。以下は **bank 後に届いた別系列**であり、**9 という数は動かさない**（pN 指示）。

| # | 対象 | 処置 |
|---|---|---|
| **B14** | header の「**8 通**」表記（列挙は 9 要素） | **数え違い = 私の欠陥**。⇒ **9 通**に訂正（列挙を機械で数え直して確認）。⛔ 旧 commit `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` は **immutable 保全** |
| **B15** | 私が surface した「Jacobian は未測ではない」の裁定 | ⭐ **両方とも真**。⇒ **一般形を 2 段へ narrow**: ✅ **proxy は測定済**（現行 H-4 = 各列を最大絶対成分に縮約 ＋ 1 姿勢・`908ac4674576c3b936fe66866254d17691b6cc8e`）／⛔ **未測は evidence-grade** = **方向つき 3 成分 Jacobian ＋ 認可 envelope**。⛔⛔ **proxy の存在を消さない／proxy から bar への帰結を導かない** |
| **B16** | 私が surface した spec `:100`「把持なし ⇒ 慣性は過小側 ⇒ ζ は楽観側」 | ⛔ **無条件の方向の断定ゆえ HOLD**。⇒ **現 state = 「出力値は free-arm（宣言した測定状態）のもの。grasped cable が effective `M` / `c` / `K` と `ζ` に与える方向・量は UNVERIFIED」**。**解析式は明示仮定つきの条件付き注記としてのみ保持**（仮定 = 減衰・剛性が不変／付加負荷が effective `M` に PSD 加算され `λ_max(M)` が単調増加 等。**たわむ cable ＋ 接触では未検証**） |
| **B17** | §1 (3) / §4 の「**EE が傾くと後者に誤差**」 | ⛔ **frame の意図と権威ある測定点が未裁定なのに world-z 用法を誤りと先取りしていたので撤回**。⇒ **言えるのは「2 構成が併存し、傾斜時に結果は一般に一致しない」まで**。**どちらが intended / correct か、差を「誤差」と呼べるかは UNRESOLVED**（p17 taxonomy ＋ geometric / reward court の境界）。⛔ 是正要求・方式選択は出さない |
| **B18** | spec §H-3.1 の「H-4 の Jacobian（**J-a**）」／設計 doc H-2 表の「`ε_joint` は **H-4 J-a** 待ち」／同 doc 後段の「per-joint `τ_bias` × **H-4 の J-a**」 | ⛔ **いずれも `J-a` を active に固定していたので撤回**。⇒ 全て **「将来 authority が確定する success-evaluation point の evidence-grade Jacobian（方向つき 3 成分 ＋ 認可 envelope）。`J-a` は conditional」** に統一（**設計 doc 2 箇所 ＋ spec 1 箇所**） |
| **B19** | 設計 doc の「**J-a と J-b は上表の値が両腕とも約 127〜133 mm/rad 違う**」 | ⛔ **「上表の値の差」という説明は撤回（維持）**。**上表からの引き算 = arm0 `\|649.34 − 529.27\| = 120.07` ／ arm1 `\|224.26 − 310.65\| = 86.39` mm/rad** |
| **B28** | 私が B19 で書いた「**`127〜133` は出所不明・h2 report にも無い**」 | ⛔⛔ **FALSE。撤回する。** ⚠ **原因 = 探索を `head -3` で切り詰めたまま「無い」を主張した**（本表 #3 = B2 と**同型の再発**）。⭐ **実在する（私が commit `7223219f3e3d11b9b16df209b6a5a347ff3185b9` で確認）**: `arm_control_measurement_h2_report.json` の `.h4_grasp_jacobian.value.arms[0].J_a_minus_J_b_max_mm_per_rad = 126.61949725828234`（`:7020`）／`arms[1] = 133.08344289986846`（`:7497`）。**生成源 = `arm_control_measurement_harness.py:969` 逐語 `float((np.abs(ja_p) - np.abs(jb_p)).max() * 1000.0)`**。⇒ ⭐ **2 量を分離**: **`126.619/133.083` = 各成分の絶対値を取ってから引き最大を取る別 proxy**（⛔ `\|ja_p − jb_p\|` ではない・**方向と符号を失う**）／**`120.07/86.39` = 上表 maxima の単純差**。⛔ **どちらからも bar・誤差の結論を出さない** |
| **B20** | 設計 doc §5.5.A の予測（「2 mm に対し `ke` 引き上げの公算・**8.16 と同じ桁**・衝突なら同時引き上げの枝」） | ⛔ **その場で RETRACTED / HISTORICAL として fence**（後段の撤回だけでは、前段を読む者に active に見えるため）。**前提だった手先 [mm] の合成は未実装・未認可で、現行 H-4 は proxy** ⇒ **前提が無い**。⭐ **現 state = 方向つき 3 成分での合成が揃うまで、2 mm 比較・必要倍率・枝の選択はすべて UNVERIFIED / HOLD** |
| **B22** | 設計 doc H-2 表の `ζ` / `T_lag` の結論（**過減衰・単調枝・行き過ぎ無し・節での誤判定無し・縮約が重要でない**） | ⛔ **宣言された free-arm / 暫定測定状態にのみ scope**（表頭に明記）。⛔ **task 全体へ一般化しない** — **掴んだたわむ cable ＋ 接触の下では effective `M` / `c` / `K` と `ζ`・根の方向と量は UNVERIFIED**（B16 の伝播是正） |
| **B21** | spec の J-c 行「**J-a と J-b の差を定量化して報告するため**」 | ⛔ **J-c 自身の用途になっていなかったので撤回**。⇒ **J-c は 3 つ目のラベル付き参照点**であり、要る理由は **J-c と J-a / J-b を proxy として並べて比較するため** |
| **B23** | 設計 doc §5.5.0 の **N5**（「把持で実効慣性が増え ζ は下がる＝**楽観側**」「**8.16 倍未満なら単調枝**」） | ⛔ **B16 / B22 と矛盾したまま active だったので、両方とも active な task 主張として撤回**。⇒ **B16 と同一の条件付き注記**（仮定 = `c`/`K` 不変・付加負荷が effective `M` に PSD 加算され `λ_max(M)` 単調増加 等。**たわむ cable ＋ 接触では未検証**）へ。**後続の `t_dwell` 記述 2 箇所も同じ境界へ整合**（**把持 phase の `t_dwell` を自由腕の枝判定から決めない**） |
| **B24** | routing artifact が final chain に未同期（B14〜B17 のみ／裁定済 surface 2 点への依頼が残存／footer が旧 bank） | ⇒ **B14〜B38 へ同期・B18〜B22 の disposition を収載・stale ask を撤回・後継 pin を明示**。⚠⚠ **「4 artifact 全て同期済」という全称主張を、実体が伴う前に書いていた** — **全称は実体化してから書く**（本表 #9 と同じ癖の再発） |
| **B25** | 設計 doc の **N5 以外**に残っていた無条件の把持方向の主張 | ⛔ 3 箇所を撤回/降格: ①「**楽観方向の要因が 3 つ重なる／厳しくなることはあっても緩くならない**」（②把持慣性は **B16 と競合**ゆえ「楽観側」と数えられない。⭐**B35 で 3 項に scope を揃えた** = **①は方向でなく「狭い箱の最大 ≤ 広い箱の最大」という境界の関係**／**②③は方向 UNVERIFIED**／**合成した task・requirement 上の全体方向は結論しない**）②「**単調枝の条件 `β·α < ζ_free²` は撤回しない構造**」（`α` が未検証仮定に依存 ⇒ **条件付きモデルへ降格・active 判定に使わない**）③「**真の余裕は ×2.09〜×8.16 の間**」（上端が未検証仮定に依存）⇒ ⭐ **残るのは `×2.09` のみ**。⛔⛔ **その scope（B30 を同じ行に fold = B37）**: **`×2.09` が保証なのは「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」**（`λ_max(M)=2.393` に対する `5.0` の余裕）。⛔ **掴んだ cable に対する保証・「真の余裕」としては使わない**（grasped 側は `M`/`c`/`K`/`ζ` とも UNVERIFIED）。「把持慣性も同じスカラー」も **`ΔM` が PSD・`c`/`K` 不変**の仮定つきに明示 |
| **B26** | spec への **B16 伝播が未完** | ⛔ `:141`「把持中 cable 慣性は `M` に入らない ⇒ **ζ は楽観側**」／§H-5.1 の「**実効慣性が増え ζ は下がる**」「**8.16 倍を超えたかで枝が決まる**」を **未検証仮定つきの diagnostic** に限定。⭐ **phase 別 step-response からの `ζ_grasped` 直接観測は保持**（⛔ **task acceptance・枝決定には使わない**）。**AC-5** は **包含の有無**と**誤差の向き**を分離し、**向きは B10 に従い UNVERIFIED** と明記。⇒ **spec を v1.9 へ** |
| **B27** | 設計 doc §5.5.C-2 の見出し「**予測は当たった側**」 | ⛔ **撤回**（直前 §5.5.A で予測自体を `RETRACTED / HISTORICAL` に落としており矛盾）。⇒ **「proxy 3 点が着地した」という事実だけの見出し**へ改称。**的中は主張しない** |
| **B29** | 撤回文の**同じ行の末尾**で旧結論を再導入していた 2 箇所 | ⛔ **削除**。①設計 doc: 「向きは言えない」と撤回した直後に **「⇒ 現状の数値は『厳しくなることはあっても、緩くなることはない』と読む」** を active に置いていた ⇒ **②把持慣性の向きが UNVERIFIED である以上、全体の向きも言えない**。②spec §H-5.1: **「これで枝を決めない」と書いた同じ行**に旧括弧 **「（設計側の枝がこれで決まる）」** が残っていた ⇒ 削除。⭐ **教訓 = 撤回は、撤回した文の周辺も読んで閉じる**（撤回文の隣で結論が生き残る） |
| **B30** | spec の pinch-site 記述と、設計 doc の `×2.09` の scope | ⛔ ①spec `:167`「使う場合はその旨と**誤差の向き**を明記」の **向きの要求を撤回** ⇒ **報告は包含の有無まで／向きは証拠が無い限り UNVERIFIED**（AC-5 と同一境界）。②設計 doc の **「`×2.09` は保証つき」を scope 限定** ⇒ **「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」の値**であり、⛔ **掴んだ cable に対する保証・「真の余裕」としては使わない** |
| **B31** | routing artifact の immutable chain が **短縮 SHA（8 桁）**／footer の全桁一覧が **直近 parent を 1 つ落としていた** | ⇒ **両方を全 40 桁・同一の 6 commit へ同期**（`35dccdd214e5b2770776fa742dfd74bcc13ef219`）。⚠ **当時 pN が bank を routing 1 path に限定していたため、本表には行が無かった**（私はその不整合を提出 message で surface した）⇒ **本版で行を追加し、範囲表記を `B14〜B38` に揃えた** |
| **B32** | spec `:5` の current-pin が stale（旧 routing 提出物の「3 SHA」が final bundle を指していない） | ⇒ **現行 authority = `P11_ROUTING_SUBMISSION_MATERIALS_V4_20260726.md` の提出 message が宣言する 4-path pin** へ差替え。**自己 pin 不可の原則は維持** |
| **B33** | **行 pin の drift**（版をまたいだ行番号の混在） | ⛔ spec `:8` の `:238`/`:244` は **v1.9 では別の行**（AC-6 行／区切り）⇒ **私が現 file で読み直し `:257`/`:263` に更新**。設計 doc `:19` の spec 参照も **v1.7 行のまま**だった ⇒ **現 v1.9 行へ**（`K_d` 生 dump `:135`／`τ_bias` `:146`／`a_max` `:147`／`AC-4` `:236`／phase 別伝達比 `:201`／`AC-6` `:238`／`ζ` `:143`。**7 行すべて私が読み直して確認**）。⛔ **版をまたいだ行番号を混在させない** |
| **B34** | 設計 doc H-2 表の `grasp_state_included` cell に、producer 逐語「inertia is on the LOW side / damping ratios OPTIMISTIC」が **active な測定値行のまま**残っていた | ⛔ **逐語は消さず、その場で fence** = **producer（p0）の assertion であって私の結論ではない**。⭐ **私の現 state = UNVERIFIED**（grasped 下の `M`/`c`/`K`/`ζ` の方向・量は未確定）。⇒ **記録として残すが根拠に引かない** |
| **B35** | 設計 doc の隣接矛盾（「①③は向きが言える」 vs 「向きについて何も結論しない」） | ⇒ **1 つの整合した current state に揃えた**: **①は方向でなく境界の関係**（狭い箱の最大 ≤ 広い箱の最大 ＝ 部分集合の最大の性質。⛔「だから要求が厳しくなる」までは言わない）／**②は方向・量とも UNVERIFIED**（B16）／**③は方向 UNVERIFIED**（cap の意味論を私は検証していない）／⇒ **合成した task・requirement 上の全体方向は結論しない**。**旧行は「削除の記録」だけにして current state を重複させない** |
| **B36** | 設計 doc の **stale ask**「どちらの言い方を採るかは pN の裁定に従う」 | ⛔ **撤回** — **B15 で決着済**。⇒ **B15 の current state に統一**（proxy は測定済／未測は evidence-grade の方向つき 3 成分 ＋ 認可 envelope／proxy から bar を導かない）。**経緯は HISTORICAL として残す** |
| **B37** | 材料 §5.4 B25 と routing B25 の「**`×2.09` が保証つき、それだけ**」が **B30 の限定を同じ行に持っていなかった** | ⇒ **両方の行に inline で fold**: **`×2.09` の保証は「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」**、⛔ **掴んだ cable に対する保証・「真の余裕」ではない** |
| **B38** | active な evidence pin `908ac46745` が短縮のままだった | ⇒ **`908ac4674576c3b936fe66866254d17691b6cc8e` へ全桁化**。**材料 / spec / 設計 doc を閉じた query で全件同期**（短縮形の残り = **0**・機械確認済。routing は `35dccdd214…` で対応済）。⚠ **version-history label の一般的な書換えは行っていない**（pN 指示どおり） |

---
**p11 ARM-CONTROL-DESIGN v4 — B6 / `-005` / B7 / B8 / B9 / B10 / B11 / B12 / B13 を 1 つの最終 cause-side correction bundle に fold（v3 = R1〜R5・PASS 済）/ v4 起草 2026-07-26 18:29:40 JST（権威時刻 = bank commit の author time）**
