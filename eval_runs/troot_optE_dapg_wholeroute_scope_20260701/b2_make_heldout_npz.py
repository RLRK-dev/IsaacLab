# B2 CP-E: encode the 3 held-out survivor demos with the FROZEN train union affine (NO recompute).
# %12 correction 2026-07-03 (CP-E §2): the OG-b' held-out leg (spec §3.2) consumes the (±8,±8)
# survivors [(+8,+8),(+8,-8),(-8,-8)] — the val npz (0,0),(-10,0) is a train-grid whole-demo holdout,
# a DIFFERENT thing. Affine is REUSED from bc_dataset_abs_meta.json (spec §1.3 hull semantics: the
# union box is a train-demo property; recomputing it from held-out would move the goalposts).
# Hull (closed, max|a|<=1.0) + decode-clip (round-trip <=1e-3mm) asserts fire HERE, per instruction.
# 0-commit eval_runs driver (precedent: b2_cpC_wave*.sh); imports the committed converter functions.
import json
import os
import sys

import numpy as np

ROOT = "/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701"
sys.path.insert(0, "/home/rlrk/IsaacLab/thread_isaac_lab/scripts")
import route_demo_to_bc as r2b  # noqa: E402

SURVIVOR_DIRS = ["rec_p8_p8", "rec_p8_m8", "rec_m8_m8"]  # (+8,+8),(+8,-8),(-8,-8); (-8,+8) excluded (R_MISS §5.3)

train_meta_path = os.path.join(ROOT, "b2_dataset_v2", "bc_dataset_abs_meta.json")
train_meta = json.load(open(train_meta_path))
affine_list = train_meta["abs_affine"]  # keep the ORIGINAL list -> byte-identical affine in the output meta
affine = np.asarray(affine_list, np.float64)
PHASES = tuple(train_meta["phase_names"])
n_phases = affine.shape[0]
assert n_phases == len(PHASES) == train_meta["phase_schema"], "schema mismatch in train meta"
disp_by_off = {tuple(e["offset"]): e for e in train_meta["heldout_disposition"]}

obs_all, lab_all, per_demo, rt_max_mm, mx_all = [], [], [], 0.0, 0.0
for d in SURVIVOR_DIRS:
    npz = os.path.join(ROOT, "b2_cpC_waves2_5", d, "route_demo_raw.npz")
    meta = os.path.join(ROOT, "b2_cpC_waves2_5", d, "route_demo_raw_meta.json")
    off = r2b._offset_from_npz_path(npz)
    demo = r2b._compute_demo(npz, meta, strict_e4=False)
    assert demo["n_phases"] == n_phases, f"{d}: schema {demo['n_phases']} != {n_phases}"
    labels = r2b._abs_encode(demo["wp"], demo["ph"], affine)  # FROZEN union affine — not recomputed
    mx = float(np.abs(labels).max())
    mx_all = max(mx_all, mx)
    # hull assert (closed: boundary counts as inside, spec §1.3-ii)
    assert mx <= 1.0, f"B2 STOP: held-out {off} max|a|={mx:.4f} > 1.0 -> EXTRAPOLATION (hull under-covers)"
    # cross-check vs the convert-time disposition recorded in the train meta (identity proof)
    rec_disp = disp_by_off.get(tuple(off))
    assert rec_disp is not None, f"{off} not in train meta heldout_disposition"
    assert round(mx, 6) == rec_disp["max_abs_a"], (
        f"{off}: recomputed max|a| {round(mx, 6)} != convert-time {rec_disp['max_abs_a']}"
    )
    src_sha = r2b._sha256_file(npz)
    assert src_sha == rec_disp["source_npz_sha256"], f"{off}: source npz sha drifted since convert"
    # decode-clip check: round-trip through the frozen affine loses nothing (<=1e-3mm)
    rec = r2b._abs_decode(labels, demo["ph"], affine)
    rt = float(np.abs(rec - demo["wp"]).max()) * 1000.0
    rt_max_mm = max(rt_max_mm, rt)
    assert rt <= 1e-3, f"B2 STOP: held-out {off} round-trip {rt:.3e}mm > 1e-3mm (decode-clip loss)"
    obs_all.append(demo["obs"])
    lab_all.append(labels)
    per_demo.append(
        {
            "offset": list(off),
            "dir": d,
            "source_npz_sha256": src_sha,
            "source_meta_sha256": r2b._sha256_file(meta),
            "max_abs_a": round(mx, 6),
            "roundtrip_max_mm": round(rt, 9),
            "n_ctrl": int(demo["obs"].shape[0]),
            "seat_quality": demo["seat_quality"],
        }
    )
    print(f"[heldout] {d} off={off} n_ctrl={demo['obs'].shape[0]} max|a|={mx:.6f} rt={rt:.3e}mm OK")

obs = np.concatenate(obs_all, axis=0)
labels = np.concatenate(lab_all, axis=0)

ds_meta = dict(train_meta)  # inherit schema fields + the FROZEN affine (same list object -> byte-identical)
ds_meta.update(
    {
        "dataset_kind": "b2_heldout_frozen_affine",
        "heldout_note": (
            "OG-b' held-out leg (spec §3.2): 3 (±8,±8) survivor demos encoded with the FROZEN train "
            "union affine from bc_dataset_abs_meta.json (NOT recomputed); hull + decode-clip asserts PASSED"
        ),
        "train_meta_source": train_meta_path,
        "train_meta_sha256": r2b._sha256_file(train_meta_path),
        "per_demo": per_demo,
        "n_heldout_demos": len(SURVIVOR_DIRS),
        "obs_heldout_shape": list(obs.shape),
        "heldout_max_abs_a": round(mx_all, 6),
        "heldout_roundtrip_max_mm": round(rt_max_mm, 9),
    }
)
for k in ("obs_train_shape", "obs_val_shape", "n_train_demos", "n_val_demos"):
    ds_meta.pop(k, None)  # not applicable to the held-out artifact

out_dir = os.path.join(ROOT, "b2_dataset_v2")
out = os.path.join(out_dir, "bc_dataset_abs_heldout.npz")
tmp = out + ".tmp.npz"
np.savez(tmp, obs=obs.astype(np.float32), actions=labels.astype(np.float32), meta=json.dumps(ds_meta))
os.replace(tmp, out)
with open(os.path.join(out_dir, "bc_dataset_abs_heldout_meta.json"), "w") as fh:
    json.dump(ds_meta, fh, indent=2)
print(
    f"[heldout] WROTE {out} obs={obs.shape} labels={labels.shape} "
    f"max|a|={mx_all:.6f} rt_max={rt_max_mm:.3e}mm sha={r2b._sha256_file(out)[:8]}"
)
