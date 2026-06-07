#!/usr/bin/env python3
"""Create flat finger with scoop claws for Franka Panda gripper.

Design spec:
- Finger dimensions: 10.5mm(X) × 13.0mm(Y) × 54.0mm(Z) — half-width/half-depth of Franka default
- Inner face is FLAT (no V-groove) — groove removed because cable only
  contacts the bottom 4mm of the finger, making the groove ineffective
- Scoop claws at fingertip and base: 3mm protrusion in -Y, 0.5mm thick
  → captures cable and prevents escape during grip
- Units: meters (STL, matching URDF convention)

Output:
- finger_v_groove_60deg.stl (collision mesh, URDF references this filename)

Left finger coordinate frame (URDF convention):
- X: lateral (width), centered at ~0
- Y: depth, 0=inner face (cable contact), positive=outer
- Z: length, 0=base, positive=tip
- When hand points down: Z_MAX = world bottom (toward table)
"""

import math
import os
import struct
import sys

# ─── Finger dimensions (meters) ───
WIDTH = 0.0105       # 10.5mm  X total (half of Franka default 21mm)
DEPTH = 0.0130       # 13mm   Y total (half of Franka default 26mm)
LENGTH = 0.0540      # 54mm  Z total

# ─── Scoop claw parameters ───
CLAW_PROTRUSION = 0.003   # 3mm inward protrusion (-Y, beyond inner face)
CLAW_THICKNESS = 0.0005   # 0.5mm extension in Z (beyond finger body)

# ─── Derived dimensions ───
HALF_W = WIDTH / 2  # 10.5mm

X_MIN = -HALF_W  # -0.0105
X_MAX = HALF_W   #  0.0105

Y_MIN = 0.0      # Inner face (flat)
Y_MAX = DEPTH    # Outer face (0.026)

Z_MIN = 0.0
Z_MAX = LENGTH   # 0.054


def compute_normal(v0, v1, v2):
    """Compute outward normal for a triangle (v0, v1, v2)."""
    ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
    bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < 1e-12:
        return (0.0, 0.0, 1.0)
    return (nx / length, ny / length, nz / length)


def build_triangles():
    """Build triangle list for flat finger + scoop claws.

    Finger body is a simple rectangular prism (box).
    Claws are small rectangular lips at tip and base.
    """
    triangles = []

    def add_tri(v0, v1, v2):
        n = compute_normal(v0, v1, v2)
        triangles.append((n, v0, v1, v2))

    # ─── Box vertices ───
    # 4 corners on inner face (Y=0), 4 on outer face (Y=DEPTH)
    # Front = Z_MIN, Back = Z_MAX
    fi0 = (X_MIN, Y_MIN, Z_MIN)  # front inner left
    fi1 = (X_MAX, Y_MIN, Z_MIN)  # front inner right
    fo0 = (X_MIN, Y_MAX, Z_MIN)  # front outer left
    fo1 = (X_MAX, Y_MAX, Z_MIN)  # front outer right
    bi0 = (X_MIN, Y_MIN, Z_MAX)  # back inner left
    bi1 = (X_MAX, Y_MIN, Z_MAX)  # back inner right
    bo0 = (X_MIN, Y_MAX, Z_MAX)  # back outer left
    bo1 = (X_MAX, Y_MAX, Z_MAX)  # back outer right

    # Front face (Z=Z_MIN, normal -Z)
    add_tri(fo0, fo1, fi1)
    add_tri(fo0, fi1, fi0)

    # Back face (Z=Z_MAX, normal +Z)
    add_tri(bo0, bi0, bi1)
    add_tri(bo0, bi1, bo1)

    # Outer face (Y=Y_MAX, normal +Y)
    add_tri(fo0, bo0, bo1)
    add_tri(fo0, bo1, fo1)

    # Inner face (Y=Y_MIN=0, normal -Y)
    add_tri(fi0, fi1, bi1)
    add_tri(fi0, bi1, bi0)

    # Left face (X=X_MIN, normal -X)
    add_tri(fo0, fi0, bi0)
    add_tri(fo0, bi0, bo0)

    # Right face (X=X_MAX, normal +X)
    add_tri(fi1, fo1, bo1)
    add_tri(fi1, bo1, bi1)

    # ─── Scoop claws ───
    claw_tris = build_claw_triangles()
    triangles.extend(claw_tris)

    return triangles


def _build_claw_box(cy_inner, cy_outer, cz_bot, cz_top):
    """Build triangles for a rectangular claw lip.

    Args:
        cy_inner: Y coordinate of claw tip (-Y direction, toward cable)
        cy_outer: Y coordinate connecting to finger body (Y=0 inner face)
        cz_bot: Z start
        cz_top: Z end
    """
    tris = []

    def add_tri(v0, v1, v2):
        n = compute_normal(v0, v1, v2)
        tris.append((n, v0, v1, v2))

    # 8 vertices of the claw box
    v0 = (X_MIN, cy_inner, cz_bot)
    v1 = (X_MAX, cy_inner, cz_bot)
    v2 = (X_MAX, cy_outer, cz_bot)
    v3 = (X_MIN, cy_outer, cz_bot)
    v4 = (X_MIN, cy_inner, cz_top)
    v5 = (X_MAX, cy_inner, cz_top)
    v6 = (X_MAX, cy_outer, cz_top)
    v7 = (X_MIN, cy_outer, cz_top)

    # Bottom face (-Z normal)
    add_tri(v0, v2, v1)
    add_tri(v0, v3, v2)
    # Top face (+Z normal)
    add_tri(v4, v5, v6)
    add_tri(v4, v6, v7)
    # Front face (-Y normal, cable contact)
    add_tri(v0, v1, v5)
    add_tri(v0, v5, v4)
    # Back face (+Y normal, connects to finger)
    add_tri(v3, v7, v6)
    add_tri(v3, v6, v2)
    # Left face (-X normal)
    add_tri(v0, v4, v7)
    add_tri(v0, v7, v3)
    # Right face (+X normal)
    add_tri(v1, v2, v6)
    add_tri(v1, v6, v5)

    return tris


def build_claw_triangles():
    """Build triangles for upper and lower scoop claws.

    Claws protrude CLAW_PROTRUSION (3mm) inward from inner face (Y=0),
    with CLAW_THICKNESS (0.5mm) extension beyond the finger body in Z.

    Lower claw (at finger tip, Z_MAX) — scoops cable from table.
    Upper claw (at finger base, Z_MIN) — prevents cable from escaping upward.
    """
    cy_inner = -CLAW_PROTRUSION   # -3mm (claw tip, toward cable)
    cy_outer = Y_MIN              #  0mm (inner face)

    # Lower claw (at finger tip)
    lower = _build_claw_box(
        cy_inner=cy_inner,
        cy_outer=cy_outer,
        cz_bot=Z_MAX,
        cz_top=Z_MAX + CLAW_THICKNESS,
    )

    # Upper claw (at finger base)
    upper = _build_claw_box(
        cy_inner=cy_inner,
        cy_outer=cy_outer,
        cz_bot=Z_MIN - CLAW_THICKNESS,
        cz_top=Z_MIN,
    )

    return lower + upper


def write_binary_stl(filepath, triangles, header_text="Flat finger + claw"):
    """Write triangles as binary STL."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        header = header_text.encode('ascii')[:80].ljust(80, b'\0')
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for (nx, ny, nz), v0, v1, v2 in triangles:
            f.write(struct.pack('<3f', nx, ny, nz))
            f.write(struct.pack('<3f', *v0))
            f.write(struct.pack('<3f', *v1))
            f.write(struct.pack('<3f', *v2))
            f.write(struct.pack('<H', 0))
    print(f"  Written: {filepath} ({len(triangles)} triangles, {os.path.getsize(filepath)} bytes)")


def verify_mesh(triangles, label=""):
    """Print verification info for a triangle mesh."""
    xs = [v[i] for _, v0, v1, v2 in triangles for v in (v0, v1, v2) for i in [0]]
    ys = [v[i] for _, v0, v1, v2 in triangles for v in (v0, v1, v2) for i in [1]]
    zs = [v[i] for _, v0, v1, v2 in triangles for v in (v0, v1, v2) for i in [2]]

    print(f"\n  {label} Mesh verification:")
    print(f"    Triangles: {len(triangles)}")
    print(f"    X range: [{min(xs)*1000:.2f}, {max(xs)*1000:.2f}] mm  (width={(max(xs)-min(xs))*1000:.2f} mm)")
    print(f"    Y range: [{min(ys)*1000:.2f}, {max(ys)*1000:.2f}] mm  (depth={(max(ys)-min(ys))*1000:.2f} mm)")
    print(f"    Z range: [{min(zs)*1000:.2f}, {max(zs)*1000:.2f}] mm  (length={(max(zs)-min(zs))*1000:.2f} mm)")
    print(f"    Claw protrusion: {CLAW_PROTRUSION*1000:.1f} mm")
    print(f"    Claw thickness: {CLAW_THICKNESS*1000:.1f} mm")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_dir = os.path.dirname(base_dir)
    mesh_dir = os.path.join(
        repo_dir,
        "source/extensions/isaaclab_tasks_thread/data/robots/franka_description/meshes/collision"
    )

    print("=" * 60)
    print("Flat Finger + Scoop Claw Collision Mesh Generator")
    print("=" * 60)
    print(f"\nFinger dimensions: {WIDTH*1000:.1f} x {DEPTH*1000:.1f} x {LENGTH*1000:.1f} mm")
    print(f"Inner face: FLAT (no groove)")
    print(f"Scoop claw: {CLAW_PROTRUSION*1000:.1f} mm protrusion, {CLAW_THICKNESS*1000:.1f} mm thick")

    print("\n--- Building mesh ---")
    tris = build_triangles()
    verify_mesh(tris, "Finger")

    print("\n--- Output Files ---")
    # URDF-compatible output (same filename as before)
    urdf_stl = os.path.join(mesh_dir, "finger_v_groove_60deg.stl")
    write_binary_stl(urdf_stl, tris, "Flat finger + scoop claw for URDF")

    print("\n" + "=" * 60)
    print("DONE — URDF references unchanged (finger_v_groove_60deg.stl)")
    print("=" * 60)


if __name__ == "__main__":
    main()
