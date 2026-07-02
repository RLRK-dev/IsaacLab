# Carried-STOP pre-registration (§3.4, B2) — declared NOW to avoid hindsight risk

Source = `b1p_og_e2000_v31regression/og_gate.json` (v31 anchor-class gate on the n=1 B1′ baseline). Machine-readable: `CARRIED_STOPS_PREREG.json`. Declared 2026-07-03 (BEFORE B2, per %12 — declaring at B2 adjudication = the same NEW-1 pathology).

**Rule (§3.4):** a **DECOUPLED**-phase STOP = **carried = exempt-if-persist** (DR structurally can't move it; the rollout's seat-verified pin confirms funneling). **MOVABLE {0-3} + C2_REGRASP (b)-pair = NOT-exempt** (what DR must fix; persistence in B2 = a REAL blocking STOP). OG-a decode STOPs inherit their phase's class.

| STOP cell (n=1) | leg | class | disposition |
|---|---|---|---|
| **GUIDE_C2** (γ⊥ 1.015) | OG-b γ⊥ | decoupled | **CARRIED** (exempt-if-persist) |
| GRASP_HOVER/Lz (23.0mm) | OG-a decode | movable | NOT-exempt (B2 must fix) |
| GRASP_DESCEND/Rz (5.1mm), /Lz (7.5mm) | OG-a decode | movable | NOT-exempt |
| GRASP_HOVER (5.279), GRASP_DESCEND (1.499), LIFT (0.968) | OG-b γ⊥ | movable | NOT-exempt |
| C2_REGRASP (seg 0.096 / ee 0.929) | OG-b (b)-pair | cable | NOT-exempt |

**B2 usage (1 line):** run `og_offline_gate.py … --carried-stops GUIDE_C2` (the gate honors carried names ONLY on decoupled phases; movable/cable STOPs can never be carried by construction). = the sole carried phase is GUIDE_C2.
