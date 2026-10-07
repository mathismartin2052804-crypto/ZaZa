# Génère tous les .obj, vérifie leur orientation et crée une planche d'aperçu.
import json
import os
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from meshlib import export_glb, hex_to_rgb
import importlib
MOD = sys.argv[1] if len(sys.argv) > 1 else "assets"
all_assets = importlib.import_module(MOD).all_assets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, sys.argv[2] if len(sys.argv) > 2 else "meshes")
os.makedirs(OUT, exist_ok=True)

assets = all_assets()
report = []
for a in assets:
    # pivot : base posée à Y=0, centrée sur X/Z du pied
    mn, mx = a.bounds()
    for p in a.parts.values():
        v = np.array(p["v"])
        v[:, 1] -= mn[1]
        p["v"] = v.tolist()
    export_glb(a, os.path.join(OUT, a.name + ".glb"))
    mn, mx = a.bounds()
    parts = {}
    for pname, p in a.parts.items():
        m = trimesh.Trimesh(np.array(p["v"]), np.array(p["f"]), process=True)
        parts[pname] = {"tris": len(p["f"]), "color": p["color"], "material": p["material"],
                        "volume": round(float(m.volume), 3)}
        if m.volume < 0:
            print("ATTENTION normales inversées :", a.name, pname, file=sys.stderr)
    report.append({"name": a.name, "tris": a.tri_count(),
                   "size_studs": [round(float(x), 1) for x in (mx - mn)], "parts": parts})
    print(f"{a.name:22s} {a.tri_count():5d} tris  taille {np.round(mx - mn, 1)}  parties {list(a.parts)}")

with open(os.path.join(OUT, "manifest.json"), "w") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)

# ---------- planche d'aperçu ----------
light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
cols = 5
rows = (len(assets) + cols - 1) // cols
fig = plt.figure(figsize=(cols * 4, rows * 4.4), facecolor="#15171c")
for k, a in enumerate(assets):
    ax = fig.add_subplot(rows, cols, k + 1, projection="3d", facecolor="#15171c")
    polys, colors = [], []
    for p in a.parts.values():
        v = np.array(p["v"])
        base = np.array(hex_to_rgb(p["color"]))
        neon = p["material"] == "Neon"
        for f in p["f"]:
            tri = v[list(f)]
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            ln = np.linalg.norm(n)
            if ln < 1e-9:
                continue
            n /= ln
            shade = 1.0 if neon else 0.35 + 0.75 * max(0, n @ light)
            # repère Roblox (X, Y haut, Z) -> matplotlib (X, Z, Y haut)
            polys.append(tri[:, [0, 2, 1]])
            colors.append(np.clip(base * shade, 0, 1))
    pc = Poly3DCollection(polys, facecolors=colors, edgecolors=colors, linewidths=0.2)
    ax.add_collection3d(pc)
    allv = np.concatenate(polys).reshape(-1, 3)
    c = (allv.max(0) + allv.min(0)) / 2
    r = (allv.max(0) - allv.min(0)).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=14, azim=-60)
    ax.set_axis_off()
    mn, mx = a.bounds()
    ax.set_title(f"{a.name}\n{a.tri_count()} tris · {mx[1]-mn[1]:.0f} studs de haut", color="#e8e8e8", fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(ROOT, sys.argv[3] if len(sys.argv) > 3 else "apercu.png"), dpi=90, facecolor=fig.get_facecolor())
print("apercu ok")
