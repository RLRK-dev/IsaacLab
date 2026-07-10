---
title: 'LL-Orchestration-Design: Skill Orchestration Architecture'
created: '2026-04-05T16:35:20.335Z'
tags:
  - knowledge
  - orchestration
  - rl-routing
  - architecture
doc_class: design-surface
---

# Skill Orchestration Architecture

> 5-clip cable routing のための skill orchestration 設計。
> 2026-04-06 CC-Rs 設計セッションで確定。

## 設計決定サマリ

| 決定 | 推奨 | 理由 | 状態 |
|------|------|------|------|
| 1: IC obs [30:42] | A1: arm-cable error に統一 | adapter が clip info [23:30] から insertion 信号を構成。IC のみ再訓練 | 確定 |
| 2: Grip action | B1: 12D + auto-close | base model + LoRA に統合可能。14D独自ネットワーク廃止 | 確定 |
| 3: P0 chain | Cascading P0 | 前スキルの実出力 snapshot → 後スキルの P0 として訓練 | 確定 |
| 4: Handedness | H2: Mirror + Clip-Relative (IC のみ) | IC 1 skill のみ mirror 必要。AR + IC に clip-relative | 確定 |

## Handedness 分析結果

### ワークスペース Y=0 対称性

```
            Y = +0.35  (RIGHT base)
                |
    C1 ────── +0.150  (X=0.35)
    C2 ────── +0.075  (X=0.40)  ← 千鳥
    C3 ──────  0.000  (X=0.35)
    C4 ────── -0.075  (X=0.40)  ← 千鳥
    C5 ────── -0.150  (X=0.35)
                |
            Y = -0.35  (LEFT base)
```

- C1↔C5, C2↔C4 がミラーペア。C3 = 中心。
- 千鳥 X-stagger: 50mm (0.35 vs 0.40)。
- Cable routing direction: C1→C5 一方向（不可逆）。

### Skill × Handedness テーブル

| Skill | 使用場面 | Mirror | Clip-Relative | X-Stagger DR | 根拠 |
|-------|---------|--------|---------------|--------------|------|
| AC | C1 のみ | 不要 | 不要 | 不要 | 初回 grasp 限定 |
| Clamp | C1 のみ (AC 後) | 不要 | 不要 | 不要 | AC.disable_finger_close=True。C2-C5 は AR auto-close で代替 |
| AR | C1→C2〜C4→C5 (4回) | 不要 | **必要** | **必要** | 腕役割固定 (RIGHT approach, LEFT re-grip)。routing方向一定 |
| **IC** | C1〜C5 (5回) | **必要** | **必要** | **必要** | +Y側の腕が C1=RIGHT, C2-C5=LEFT で flip |
| Unclamp | 全 clip | scripted | N/A | N/A | RL 不使用 |

**Mirror 必要なのは IC の 1 skill のみ。**

### Mirror 不要の根拠

- **AC**: C1 限定使用。mirror の必要なし。
- **Clamp**: C1 限定。AC 後の finger close のみ。C2-C5 では AR の auto-close が clamp を兼ねる。
  - AC env: `disable_finger_close=True` (newton_approach_cable_env.py:385-386)
  - AR env: LEFT=常時CLOSED + RIGHT=auto-close (newton_aerial_regrasp_env.py:36,224)
- **AR**: scripted routing の regrasp steps (8a-8c) は全 clip 遷移で同一パターン。
  - 8a: LEFT descend + close (re-grip) — ハードコード
  - 8b-8c: RIGHT approach + close — ハードコード
  - routing方向が C1→C5 で常に -Y 方向のため、腕役割は反転しない。

### 各 Clip の Skill Flow

**C1 (初回):**
```
AC (両腕approach) → Clamp (両腕close) → Transport (scripted)
→ IC (両腕push, R at +Y, identity) → Unclamp (scripted)
```

**C2-C5 (各遷移、共通パターン):**
```
Unclamp (scripted) → Rise (scripted) → ReClamp/LEFT (scripted, 8a)
→ AR/RIGHT (RL, 8b-8c, auto-close) → Transport (scripted, MOVE)
→ IC (RL, mirror, PUSH) → Unclamp (scripted)
```

## Clip-Relative 変換

全位置 obs から clip_pos を引算。clip quat = identity のため、回転変換不要（並進のみ）。

```python
def to_clip_relative(obs, clip_pos):
    obs_cr = obs.clone()
    obs_cr[:, 0:3]   -= clip_pos  # R arm pos
    obs_cr[:, 8:11]  -= clip_pos  # L arm pos
    obs_cr[:, 16:19] -= clip_pos  # cable target pos
    obs_cr[:, 23:26] -= clip_pos  # clip pos → [0,0,0]
    return obs_cr
```

**注意:** obs [23:26] (clip pos) が [0,0,0] になるため、policy は clip 絶対位置を失う。AR/IC のタスクには不要だが、将来 clip-dependent behavior が必要になった場合の制約。

## Mirror Transform (IC のみ)

Y-axis mirror + arm slot swap。AC/AR/Grip の obs [30:42] (arm-cable error) に対して数学的に正しい。

```python
def mirror_obs(obs_cr):
    m = obs_cr.clone()
    # Arm slot swap
    m[:, 0:8], m[:, 8:16] = obs_cr[:, 8:16].clone(), obs_cr[:, 0:8].clone()
    m[:, 30:36], m[:, 36:42] = obs_cr[:, 36:42].clone(), obs_cr[:, 30:36].clone()
    # Y-negate positions
    for y_idx in [1, 9, 17, 24]:
        m[:, y_idx] *= -1
    # Y-mirror quaternions: (qx,qy,qz,qw) → (-qx,qy,-qz,qw)
    for quat_start in [3, 11, 19, 26]:
        m[:, quat_start] *= -1
        m[:, quat_start + 2] *= -1
    # Y-mirror axis-angle errors: (ax,ay,az) → (-ax,ay,-az)
    for aa_start in [30, 36]:
        m[:, aa_start] *= -1
        m[:, aa_start + 2] *= -1
    # Y-mirror position error Y components
    for pe_y in [34, 40]:
        m[:, pe_y] *= -1
    return m

def mirror_action(action):
    m = action.clone()
    m[:, 0:6], m[:, 6:12] = action[:, 6:12].clone(), action[:, 0:6].clone()
    for idx in [1, 7]:      # Y-negate pos deltas
        m[:, idx] *= -1
    for idx in [3, 5, 9, 11]:  # X,Z-negate rot deltas
        m[:, idx] *= -1
    return m
```

**前提条件:** IC obs [30:42] が arm-cable error に統一済みであること (決定1)。

## X-Stagger 対策

千鳥 X-stagger (50mm) は clip_x を [0.35, 0.40] で Domain Randomization。
INIT_XY_NOISE (±2mm) では吸収不可能（25倍不足）。

## Orchestrator Interface

```python
class SkillOrchestrator:
    CLIP_ARM_PLUS_Y = {0: "R", 1: "L", 2: "L", 3: "L", 4: "L"}
    
    def execute_skill(self, skill, clip_idx, state):
        clip_pos = CLIP_POSITIONS[clip_idx]
        
        # Clip-relative (AR, IC)
        if skill in (SkillType.AERIAL_REGRASP, SkillType.INSERT_INTO_CLIP):
            obs = to_clip_relative(state.obs, clip_pos)
        else:
            obs = state.obs
        
        # Mirror (IC only, C2-C5)
        if skill == SkillType.INSERT_INTO_CLIP and self.CLIP_ARM_PLUS_Y[clip_idx] == "L":
            obs = mirror_obs(obs)
        
        action = self.policy.forward(obs, skill)
        
        # Un-mirror action
        if skill == SkillType.INSERT_INTO_CLIP and self.CLIP_ARM_PLUS_Y[clip_idx] == "L":
            action = mirror_action(action)
        
        return action
```

## 実行計画


```
[Phase 0] IC obs [30:42] → arm-cable error 統一 (決定1)       ✅ Done (2026-04-06)
[Phase 0'] Grip 12D 化 (決定2, 並行)                         ✅ Done (2026-04-06)
[Phase 1] Clip-Relative + Mirror (決定4)                      ✅ Done (2026-04-06)
  1a. AR env に clip_pos parameterization + clip_x DR          ✅
  1b. IC env に上記 + mirror wrapper                           ✅
  1c. 検証: 36/36 PASS (involution, pipeline, clip Z)          ✅
[Phase 1'] Stage A 再訓練 (D1/D2 対応)                        🔶 全4スキル並行訓練中 (2026-04-06)
  - IC demo v5 再収集: 160/160 ep, 100% success, 19200 tr      ✅ Done
  - IC v19: cuda:1, iter 1/200                                 🔶 Running
  - Grip clamp v5: cuda:0, iter 17/200                         🔶 Running
  - AC v36: cuda:2, iter 86/200 (継続)                         🔶 Running
  - AR v23: cuda:0, iter 53/200 (継続)                         🔶 Running
[Phase 2] Cascading P0 (決定3)                                🔶 設計完了、Stage A完了待ち
[Phase 3] Orchestrator 実装 + 5-clip end-to-end テスト        ⬜ 未着手
```


## Cascading P0 設計 (決定3, 2026-04-06)

### 概念

前スキルの **成功時終端状態** を後スキルの **P0キャッシュ** として使用。
現在: 各env独立の合成P0 (IK配置→VBD settle→cache)。
目標: スキルチェーンの実行時状態分布で訓練。

### データパイプライン

```
[Stage A] 合成P0で各スキル独立訓練 (現行) → 初期policy
[Stage B] collect_cascaded_p0.py:
          skill N policy → run 1000 episodes → success terminal states → .npz
[Stage C] skill N+1 env の --p0-cache に Stage B の .npz を指定して訓練
```

### スキルチェーン P0 遷移

| From → To | 転送する状態 | Finger遷移 | 備考 |
|-----------|-------------|-----------|------|
| AC → Clamp | body_q/qd, fk_jq, EE targets | OPEN → OPEN (Clampが close) | AC: disable_finger_close=True |
| Clamp → Transport | body_q/qd, fk_jq | CLOSED → CLOSED | scripted維持 |
| Transport → IC | body_q/qd, fk_jq, clip_pos | CLOSED → CLOSED | scripted移動後 |
| IC → Unclamp | body_q/qd, cable in groove | CLOSED → scripted L=HALF+R=OPEN | IC成功=groove到達 |
| Unclamp → Rise → ReClamp → AR | scripted chain | L=HALF+R=OPEN → L=CLOSED+R=auto | ReClamp: L full close |
| AR → Transport → IC | body_q/qd | L=CLOSED+R=auto-closed → CLOSED | AR成功=cable受渡 |

### StateSnapshot (既存: snapshot.py)

```python
@dataclass
class StateSnapshot:
    step_id: int
    body_q: np.ndarray      # 全body位置/姿勢
    body_qd: np.ndarray     # 速度
    fk_jq: np.ndarray       # 関節角
    clip_status: list[bool]  # C1-C5 固定状態
    finger_l: float          # 左finger [m]
    finger_r: float          # 右finger [m]
    ik_target_l: tuple       # 左EE目標 (x,y,z)
    ik_target_r: tuple       # 右EE目標 (x,y,z)
```

### Env interface (未実装)

各envに以下を追加:
- `export_terminal_state(world_idx) -> dict`: 成功episode終端のstate dict
- `load_p0_from_cascade(npz_path)`: 外部P0キャッシュからのリセット

### 実装順序

1. Stage A: 現行の合成P0訓練を完了 (AC v36, IC re-train, AR v23, Grip re-train)
2. Stage B: 訓練済みpolicyで terminal state 収集
3. Stage C: cascaded P0 で fine-tune (optional — Stage A の policy品質次第)

## Related
- [[RL-Routing-Design]]
- [[RL-Routing-Progress]]
- [[SOMA]]
