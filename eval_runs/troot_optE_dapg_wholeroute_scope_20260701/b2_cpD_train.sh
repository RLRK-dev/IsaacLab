#!/usr/bin/env bash
# CP-D: BC (9 diverse demos) ∥ replicate-null ((+10,0)x9) on GPU-1 in parallel. seed=0, epochs=2000,
# whole-demo val on _val.npz. GPU-1 = physical index1 (Blackwell), CUDA_VISIBLE_DEVICES=1 -> relative cuda:0.
set -u
cd /home/rlrk/IsaacLab
PY=/home/rlrk/env_isaaclab7/bin/python
D=/home/rlrk/IsaacLab/eval_runs/troot_optE_dapg_wholeroute_scope_20260701
DS=$D/b2_dataset_v2; CPD=$D/b2_cpD
echo "=== CP-D launch $(date '+%H:%M:%S') GPU-1 procs before: $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null|wc -l) ==="
CUDA_VISIBLE_DEVICES=1 $PY thread_isaac_lab/scripts/bc_train_route.py \
    --dataset $DS/bc_dataset_abs.npz --val-dataset $DS/bc_dataset_abs_val.npz \
    --out-dir $CPD/bc --epochs 2000 --seed 0 --device cuda:0 --tag _b2_e2000 > $CPD/bc_train.log 2>&1 &
BC=$!
CUDA_VISIBLE_DEVICES=1 $PY thread_isaac_lab/scripts/bc_train_route.py \
    --dataset $CPD/null_dataset.npz --val-dataset $DS/bc_dataset_abs_val.npz \
    --out-dir $CPD/null --epochs 2000 --seed 0 --device cuda:0 --tag _null_e2000 > $CPD/null_train.log 2>&1 &
NU=$!
wait $BC; echo "BC exit=$?"; wait $NU; echo "NULL exit=$?"
echo "=== CP-D DONE $(date '+%H:%M:%S') ==="
echo "############ BC ############"; grep -E "final train_loss|whole.demo val|Loaded|Train:|repr=" $CPD/bc_train.log 2>/dev/null | tail -6
echo "############ NULL ############"; grep -E "final train_loss|whole.demo val|Loaded|Train:|repr=" $CPD/null_train.log 2>/dev/null | tail -6
echo "############ artifacts ############"; ls -la $CPD/bc/*.pt $CPD/bc/loss_curve.json $CPD/null/*.pt $CPD/null/loss_curve.json 2>/dev/null
