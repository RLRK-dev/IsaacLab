# Inner-housing grip review checkpoint

Published on 2026-09-21 at the user's explicit push request.

## Review documents

[Open the two-page Japanese review](output/pdf/内側ハウジングの把持候補と指の退避_v01_20260921.pdf).
The [delivery README](output/README.md) describes the candidate, sources and limitations.

The delivered PDF, two page images, JSON and README are preserved byte for byte.
Their original Downloads identity is recorded in `audit/delivery.json`.
This checkpoint contains comparison diagrams, not selected finger dimensions,
robot motion, acceptance criteria or a formal physical-validity result.

## Included dependencies

- Saved official TE CAD cache, drawing and assembly instruction under
  `eval_runs/ur15_jb_harness_revision_20260907/`.
- Original drawing style and 20-job hand plan under
  `work/hvjb-hand-plan-v01-20260920/`.
- Original D45/D50 handoff record under
  `work/hvjb-header-retention-v01-20260921/output/retention_review.json`.

The historical records retain their original source paths and SHA-256 values.
The CAD and documents are manufacturer reference material, not newly designed
parts or evidence of approved automated gripping loads.

## Regeneration

From the repository root, with the existing Python environment containing
NumPy, trimesh, Matplotlib and Pillow, and Noto Sans CJK fonts installed:

```bash
./isaaclab.sh -p work/hvjb-inner-grasp-v01-20260921/build_review.py \
    --output_root /tmp/hvjb-inner-grasp-review-regenerated
```

The publishing change makes the reference directory checkout-relative and adds
`--output_root` for a fresh regeneration directory. Source geometry, numerical
observations and graphic content are unchanged. Running without this argument
stops because the delivered version is protected by `audit/delivery.json`.
Regenerated PDF metadata and source-path strings will differ from the archived
delivery. The original delivery is not overwritten.

The previous reviews' complete packages, unrelated shared-tree changes and
the Vault's shared log are not part of this focused checkpoint.
