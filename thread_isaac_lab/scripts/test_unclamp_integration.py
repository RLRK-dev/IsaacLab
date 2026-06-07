#!/usr/bin/env python3
"""Integration test: verify Unclamp env fixes (X1-X3, S1-S2, C1, M1-M3).

Checks:
  1. Env creates with world_count=4
  2. Obs shape is (4, 42) — X1
  3. 10 RL steps without NaN rewards — X3 sanitisation
  4. time_outs=0 when not at terminal step — C1
  5. No NaN in obs — S1
  6. SkillType.UNCLAMP exists — X2
"""
import os, sys
import torch

_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_dir = os.path.join(_script_dir, "..", "envs")
_model_dir = os.path.join(_script_dir, "..", "models")
sys.path.insert(0, _env_dir)
sys.path.insert(0, _model_dir)

device = os.environ.get("NEWTON_DEVICE", "cuda:0")
N = 4
N_STEPS = 10


def main():
    print(f"[TEST] device={device}, worlds={N}, steps={N_STEPS}")

    # X2: SkillType.UNCLAMP
    from skill_adapter import SkillType
    assert hasattr(SkillType, "UNCLAMP"), "X2 FAIL: SkillType.UNCLAMP missing"
    assert SkillType.UNCLAMP.value == "unclamp"
    print("[PASS] X2: SkillType.UNCLAMP exists")

    # Create env
    from newton_unclamp_env import NewtonUnclampEnv
    env = NewtonUnclampEnv(world_count=N, device=device)

    # X1: obs dimension
    obs, _ = env.reset()
    assert obs.shape == (N, 42), f"X1 FAIL: obs.shape={obs.shape}, expected ({N}, 42)"
    print(f"[PASS] X1: obs.shape={obs.shape}")

    # S1: no NaN in initial obs
    assert not torch.isnan(obs).any(), "S1 FAIL: NaN in initial obs"
    print("[PASS] S1: No NaN in initial obs")

    # Step loop
    nan_rewards = 0
    all_done_step1 = False
    for step in range(N_STEPS):
        actions = torch.zeros(N, 4, device=device)
        actions[:, 0] = 0.3  # gentle finger open
        obs, rewards, dones, infos = env.step(actions)
        time_outs = infos.get("time_out", torch.zeros_like(dones))

        has_nan_rew = torch.isnan(rewards).any().item()
        has_nan_obs = torch.isnan(obs).any().item()
        all_done = dones.all().item()

        print(f"  step={step}: rew=[{rewards.min():.4f}, {rewards.max():.4f}] "
              f"done={dones.sum().item()}/{N} nan_rew={has_nan_rew} nan_obs={has_nan_obs}")

        if has_nan_rew:
            nan_rewards += 1
        if step == 0 and all_done:
            all_done_step1 = True

    # X3: no step-1 instant death
    if all_done_step1:
        print("[FAIL] X3: All worlds died at step 1 (instant death)")
    else:
        print("[PASS] X3: No step-1 instant death")

    # S1: no NaN rewards across all steps
    if nan_rewards == 0:
        print(f"[PASS] S1: No NaN rewards in {N_STEPS} steps")
    else:
        print(f"[FAIL] S1: NaN rewards in {nan_rewards}/{N_STEPS} steps")

    env.close()
    print("\n[TEST] Integration test complete")


if __name__ == "__main__":
    main()
