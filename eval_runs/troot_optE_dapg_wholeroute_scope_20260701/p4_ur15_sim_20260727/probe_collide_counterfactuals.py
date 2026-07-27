"""Does the collision check fail when the thing it checks is broken?  Run every way of breaking it.

p5's condition for landing: a gate validated under the bug is validated by the bug, so show the
predicate turning False.  I reported "five counterfactuals, all False", and p18 was right to hold
that: my five were all the same class -- I changed the VALUE at each site, or added a site with a
different value.  p0's counterfactual A leaves the value alone and wraps the assignment in an
`if`, and the predicate does not look at ancestry at all, so it stays True.

The predicate's docstring says "unconditionally".  It does not check that.  This script enumerates
the classes so the gap is on the record rather than in a claim.
"""

import ast
import pathlib
import re

ENV = pathlib.Path("/home/rlrk/IsaacLab/thread_isaac_lab/envs/newton_skill_env_base.py")


def predicate(text):
    """The check as implemented in ur15_cell_spec._clip_collides_in_source, over supplied text."""
    tree = ast.parse(text)
    flags = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
             for t in n.targets
             if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute)
             and t.value.attr == "shape_flags"
             and isinstance(t.value.value, ast.Name) and t.value.value.id == "scene"]
    return len(flags), (bool(flags) and all(isinstance(n.value, ast.Constant)
                                            and n.value.value == 0x6 for n in flags))


src = ENV.read_text()
lines = src.split("\n")
sites = [i for i, l in enumerate(lines) if re.search(r"scene\.shape_flags\[\w+\]\s*=", l)]
n, base = predicate(src)
print(f"as committed: {n} sites on scene.shape_flags at lines {[i + 1 for i in sites]} -> {base}\n")

results = []

# A -- value untouched, assignment made conditional.  p0's case, and the one I never ran.
for i in sites:
    mut = list(lines)
    ind = re.match(r"\s*", mut[i]).group(0)
    mut[i] = f"{ind}if _flag:\n{ind}    " + mut[i].strip()
    _, val = predicate("\n".join(mut))
    results.append(("A conditional, value unchanged", i + 1, val))

# B -- value changed at one site
for i in sites:
    mut = list(lines)
    mut[i] = re.sub(r"=\s*0x6", "= 1", mut[i], count=1)
    _, val = predicate("\n".join(mut))
    results.append(("B value set to COLLIDE-off", i + 1, val))

# C -- both: conditional AND value changed
i = sites[0]
mut = list(lines)
ind = re.match(r"\s*", mut[i]).group(0)
mut[i] = f"{ind}if _flag:\n{ind}    " + re.sub(r"=\s*0x6", "= 1", mut[i].strip(), count=1)
_, val = predicate("\n".join(mut))
results.append(("C conditional and value changed", i + 1, val))

# D -- a new writer elsewhere with a different value
mut = list(lines)
ind = re.match(r"\s*", lines[sites[0]]).group(0)
mut.insert(sites[0], f"{ind}scene.shape_flags[idx] = 1  # an unrelated writer")
_, val = predicate("\n".join(mut))
results.append(("D unrelated writer added", sites[0] + 1, val))

# E -- the value moved behind a name, so it is no longer a literal
i = sites[0]
mut = list(lines)
mut[i] = re.sub(r"=\s*0x6", "= _COLLIDE", mut[i], count=1)
_, val = predicate("\n".join(mut))
results.append(("E value behind a name", i + 1, val))

print(f"{'class':34s} {'line':>6}  {'predicate':>9}  verdict")
for label, line, val in results:
    print(f"{label:34s} {line:6d}  {str(val):>9}  "
          f"{'caught' if val is False else 'MISSED -- stays True with the source broken'}")

missed = [r for r in results if r[2] is True]
print(f"\n{len(results) - len(missed)} of {len(results)} caught; {len(missed)} missed.")
if missed:
    print("The misses are all class A: the predicate reads the assigned VALUE and never asks")
    print("whether the assignment runs.  Closing that means walking each site's ancestors for")
    print("If / IfExp.  Whether to close it or accept the exposure is p5's call, not this")
    print("script's -- and my earlier 'all five' claim covered only classes B and D.")
