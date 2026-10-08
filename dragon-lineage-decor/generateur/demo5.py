# Construit la démo 3D (HTML autonome) du dragon de cristal à partir d'un gabarit.
# Usage : python3 demo5.py demo5.tpl.html sortie.html                 (v2, assets5)
#         python3 demo5.py demo5v3.tpl.html sortie.html assets5v3     (v3, marche au sol)
import sys, json, base64, importlib, os, tempfile
import numpy as np
from meshlib import export_glb

mod = importlib.import_module(sys.argv[3] if len(sys.argv) > 3 else "assets5")
a = mod.all_assets()[0]
mn, _ = a.bounds()
for p in a.parts.values():                 # même recalage que build.py : base à Y = 0
    v = np.array(p["v"]); v[:, 1] -= mn[1]; p["v"] = v.tolist()
sh = lambda q: [q[0], q[1] - mn[1], q[2]]
POINTS = ("hip", "knee", "ankle", "contact")   # points à recaler ; les directions (bend) ne bougent pas
meta = {"chain": [sh(q) for q in a.meta["chain"]], "jaw_hinge": sh(a.meta["jaw_hinge"]),
        "ground": a.meta.get("ground", 0.0) - mn[1],
        "legs": {k: {f: (sh(x) if f in POINTS else x) for f, x in L.items()} for k, L in a.meta["legs"].items()}}
tmp = os.path.join(tempfile.mkdtemp(), "d.glb")
export_glb(a, tmp)
b64 = base64.b64encode(open(tmp, "rb").read()).decode()
html = open(sys.argv[1]).read().replace("__GLB__", b64).replace("__META__", json.dumps(meta))
open(sys.argv[2], "w").write(html)
print(a.tri_count(), "tris", len(a.parts), "parties")
