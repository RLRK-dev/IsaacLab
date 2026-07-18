# LATENT FINDING — `newton_grip_env.py` timeout-purity gap (co-terminal contamination)

**⚠ SEPARATE FROM #18** (grip-slip route-env fix). p4-domain latent finding. **NOT actioned** — recorded for separate disposition.
**Discovered:** OPS-SUP-CODEX WMSO inventory, 2026-07-18 14:32 JST. **Grounded (on-disk read):** RS-TECH-LEAD, 2026-07-18 14:38 JST.
**Env:** `newton_grip_env.py` = env7-mujoco **GRIP** env (ACTIVE per CLAUDE.md). This is NOT `newton_route_env.py` (the #18 route env).

## Premise — CONFIRMED (on-disk)
Three reward/done sites set `timeouts[w] = int(timeout)` where `timeout = self._world_episode_length[w] >= self.max_episode_length`, **without excluding co-occurring terminal events**:
- `:1258` (dual-arm branch): `done = success or timeout or explosion` (`:1252`); `timeouts[w] = int(timeout)`.
- `:1266` (per-arm branch): `timeouts[2*w] = timeouts[2*w+1] = int(timeout)`.
- `:1441` (other reward path): `done = success or timeout or explosion or cable_dropped` (`:1437`); `timeouts[w] = int(timeout)`.

**Gap:** at a step where `timeout=True` AND (`explosion` / `cable_dropped` / `success`) is also True, the episode ends on a **terminal** event but `timeouts=1` → RSL-RL PPO applies γV(s′) value-bootstrapping to a terminal state → the **value_loss-explosion class** (CLAUDE.md hardstop; BUG-1 history: value_loss 448 → 46,889, ×105).

The `:1264-1266` comment ("BUG-1 fix: explosion is a true terminal state (value=0), not a timeout") shows BUG-1 fixed **explosion-alone** (mid-episode explosion → `timeout=False` → `timeouts=0` ✓) but did **NOT** exclude the **co-terminal** case (explosion/drop AT the max-episode step, `timeout=True`) → residual gap.

## Impact — UNVERIFIED
Depends on how often `explosion`/`cable_dropped`/`success` co-occur exactly at `episode_length >= max`, and whether that produces an observable value_loss spike. Not measured. Could be rare (terminal exactly at the max step) but the class is catastrophic when it hits.

## Correct fix (for the separate task — NOT applied here)
Pure timeout excludes all co-occurring terminals, at all three sites:
```python
timeouts[w] = int(timeout and not (explosion or cable_dropped or success))
```
(`cable_dropped` term only where it exists in that path.)

## Disposition
- **Latent, deferred.** Fix = a **separate task**: env change (L3) + reward/env **design-gate** (`/reward-design` + `/pre-check`) + **Rs approval** (touches `time_outs` semantics = CLAUDE.md hardstop + prohibited.md `timeouts汚染禁止`).
- **Do NOT mix into #18** (OPS-SUP directive; scope boundary §運用24).
- Next step is Rs's to decide (schedule as a task now, or backlog) — surfaced in the RS-TECH-LEAD checkpoint.
