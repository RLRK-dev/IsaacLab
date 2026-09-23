# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Record the identity of the two publicly linked Atom Drive user guides."""

import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "website": "https://www.ampereev.com/wp-content/uploads/2023/10/Atom-Drive-System-User-Guide-V1.pdf",
    "support": "https://help.ampereev.com/hc/en-us/article_attachments/31296839281047",
}


def main():
    """Download public, unauthenticated source files without replacing earlier evidence."""
    receipt = ROOT / "manual_source_identity.json"
    assert not receipt.exists(), receipt
    source_dir = ROOT / "source_pdfs"
    source_dir.mkdir(exist_ok=True)
    rows = []
    for name, url in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        path = source_dir / f"atom_drive_user_guide_v1_{name}.pdf"
        assert not path.exists(), path
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                content = response.read()
                final_url = response.url
        except urllib.error.URLError as error:
            rows.append({"source": name, "requested_url": url, "error": str(error), "sha256": None})
            continue
        assert content.startswith(b"%PDF-"), name
        path.write_bytes(content)
        rows.append(
            {
                "source": name,
                "requested_url": url,
                "final_url": final_url,
                "path": str(path.relative_to(ROOT)),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    result = {
        "observed_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "sources": rows,
        "two_public_guides_byte_identical": (
            rows[0]["sha256"] == rows[1]["sha256"] if all(row["sha256"] for row in rows) else None
        ),
        "authentication_used": False,
        "connector_part_number_selected": None,
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
