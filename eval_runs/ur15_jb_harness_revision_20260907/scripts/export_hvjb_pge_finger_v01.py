# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Embed the saved sample geometry [m] in an offline comparison viewer."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def _color_key(name: str, category: str) -> str:
    names = {
        "comparison_wire": "wire",
        "illustrative_sleeve": "sleeve",
        "illustrative_busbar_coupon": "coupon",
    }
    return names.get(name, category)


def main() -> None:
    """Export actual saved triangles without mesh simplification or network calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    payload = json.loads(gzip.decompress(args.mesh.read_bytes()))
    candidate = payload["candidates"]["PGE_SAMPLE"]
    objects = {}
    for name, obj in candidate["objects"].items():
        identity = [[int(i == j) for j in range(4)] for i in range(4)]
        if candidate["states"]["contour"]["transforms"][name] != identity:
            raise AssertionError("Viewer requires the stored contour vertices in world coordinates")
        objects[name] = {
            "vertices": obj["vertices"],
            "faces": obj["faces"],
            "side": obj["side"],
            "color_key": _color_key(name, obj["category"]),
        }
    data = {"objects": objects, "opening_m": candidate["states"]["open"]["opening_per_jaw_m"]}
    template = Path(__file__).with_name("hvjb_pge_finger_v01.html").read_text()
    html = template.replace("__MODEL_DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    raw = html.encode()
    if len(raw) >= 1_000_000:
        raise AssertionError("Inline visualization exceeds the one MB budget")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "triangles_preserved": True}))


if __name__ == "__main__":
    main()
