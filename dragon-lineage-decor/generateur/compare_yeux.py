# Planche de comparaison des yeux du crâne v3 (gros plan sur la tête).
# Usage : python3 generateur/compare_yeux.py comparaison-yeux-v3.png
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from meshlib import hex_to_rgb
import assets4
variants = [("v3 actuel", "v3"), ("Orbites sombres", "sombre"), ("Lueur braise", "braise"), ("Lueur cyan", "cyan")]
views = [("De face", 8, 90), ("3/4", 14, 40), ("Profil", 6, 0)]
light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
fig = plt.figure(figsize=(13, 16), facecolor="#15171c")
for r, (label, eyes) in enumerate(variants):
    a = assets4.dragon_skull_v3("Dragon_Skull_v3", 22, eyes)
    polys, colors = [], []
    for p in a.parts.values():
        v = np.array(p["v"]); base = np.array(hex_to_rgb(p["color"])); neon = p["material"] == "Neon"
        for f in p["f"]:
            tri = v[list(f)]; n = np.cross(tri[1]-tri[0], tri[2]-tri[0]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            polys.append(tri[:, [0, 2, 1]]); colors.append(np.clip(base*(1.0 if neon else 0.35+0.75*max(0, (n/ln)@light)), 0, 1))
    c, rad = np.array([0, 0.5, 3.0]), 3.6   # gros plan sur la tête (repère matplotlib : x, z, y)
    for k, (t, el, az) in enumerate(views):
        ax = fig.add_subplot(4, 3, r*3+k+1, projection="3d", facecolor="#15171c")
        ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors=colors, linewidths=0.2))
        ax.set_xlim(c[0]-rad, c[0]+rad); ax.set_ylim(c[1]-rad, c[1]+rad); ax.set_zlim(c[2]-rad, c[2]+rad)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=el, azim=az); ax.set_axis_off()
        ax.set_title(f"{label} · {t}", color="#e8e8e8", fontsize=12)
plt.tight_layout(); plt.savefig(sys.argv[1], dpi=75, facecolor=fig.get_facecolor()); print("ok")
