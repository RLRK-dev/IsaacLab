#!/usr/bin/env python3
"""route_leg_diff — reference-motion deviation detector (W0-e video-capability upgrade, 2026-07-05).

Parses the per-leg motion labels from two route run.logs (reference vs candidate) and
diffs the LEG-LABEL SEQUENCE. Any leg present in the candidate but not in the reference
(or vice versa) = a motion-structure deviation from the Rs-approved reference route
(step-table-first principle: fixes may adjust coordinates of EXISTING legs, never add
new motions). Coordinate-only changes on a matching leg are reported separately.

Usage: route_leg_diff.py <reference_run.log> <candidate_run.log>
Exit: 0 = same motion structure, 2 = structure deviates (added/removed legs).
"""
import difflib
import re
import sys

LEG_RE = re.compile(r"^\s{2}\[([A-Za-z0-9_\-/ .]+)\] dist=([0-9.]+)mm, steps=(\d+)")


def parse(path):
    legs = []
    for line in open(path, errors="replace"):
        m = LEG_RE.match(line)
        if m:
            label = re.sub(r"\d+/\d+$", "k/N", m.group(1).strip())  # normalize leg counters
            legs.append((label, float(m.group(2)), int(m.group(3))))
    return legs


def main(ref_path, cand_path):
    ref, cand = parse(ref_path), parse(cand_path)
    ref_seq = [l for l, _, _ in ref]
    cand_seq = [l for l, _, _ in cand]
    sm = difflib.SequenceMatcher(a=ref_seq, b=cand_seq, autojunk=False)
    added, removed, coord_changed = [], [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for di in range(i2 - i1):
                rl, cl = ref[i1 + di], cand[j1 + di]
                if abs(rl[1] - cl[1]) > 1.0:  # >1mm leg-distance change = coordinate delta
                    coord_changed.append((rl[0], rl[1], cl[1]))
        if op in ("insert", "replace"):
            added += cand_seq[j1:j2]
        if op in ("delete", "replace"):
            removed += ref_seq[i1:i2]
    print(f"reference: {ref_path} ({len(ref)} legs)")
    print(f"candidate: {cand_path} ({len(cand)} legs)")
    print(f"ADDED legs (not in reference — step-table deviation): {len(added)}")
    for label in dict.fromkeys(added):
        print(f"  + {label} x{added.count(label)}")
    print(f"REMOVED legs (in reference, missing here): {len(removed)}")
    for label in dict.fromkeys(removed):
        print(f"  - {label} x{removed.count(label)}")
    print(f"coordinate-only deltas on matching legs (>1mm): {len(coord_changed)}")
    for label, rd, cd in coord_changed[:12]:
        print(f"  ~ {label}: dist {rd:.1f} -> {cd:.1f}mm")
    verdict = "SAME-STRUCTURE" if not (added or removed) else "STRUCTURE-DEVIATES"
    print(f"VERDICT: {verdict}")
    return 0 if verdict == "SAME-STRUCTURE" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
