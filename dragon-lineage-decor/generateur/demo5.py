# Construit la démo 3D (HTML autonome) du dragon de cristal à partir d'un gabarit.
# Usage : python3 demo5.py demo5.tpl.html sortie.html
import sys, json, base64, io, os, tempfile
import numpy as np
from meshlib import export_glb
import assets5

a = assets5.dragon_cristal()
mn, _ = a.bounds()
for p in a.parts.values():                 # même recalage que build.py : base à Y = 0
    v = np.array(p["v"]); v[:, 1] -= mn[1]; p["v"] = v.tolist()
sh = lambda q: [q[0], q[1] - mn[1], q[2]]
meta = {"chain": [sh(q) for q in a.meta["chain"]], "jaw_hinge": sh(a.meta["jaw_hinge"]),
        "legs": {k: {"seg": L["seg"], "hip": sh(L["hip"])} for k, L in a.meta["legs"].items()}}
tmp = os.path.join(tempfile.mkdtemp(), "d.glb")
export_glb(a, tmp)
b64 = base64.b64encode(open(tmp, "rb").read()).decode()
html = open(sys.argv[1]).read().replace("__GLB__", b64).replace("__META__", json.dumps(meta))
open(sys.argv[2], "w").write(html)
print(a.tri_count(), "tris", len(a.parts), "parties")
