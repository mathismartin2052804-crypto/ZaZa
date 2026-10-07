# Planche de comparaison v2 / v3 sous 4 angles (pour validation par Will).
# Usage : python3 generateur/compare.py generateur comparaison-crane-v2-v3.png
import sys, os
sys.path.insert(0, sys.argv[1])
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from meshlib import hex_to_rgb
import assets2, assets3, assets4
assets = [assets3._with_new_skull(assets2.dragon_skull, "Dragon_Skull_v2", 22, 1.0), assets4.dragon_skull_v3("Dragon_Skull_v3", 22)]
views = [("De face", 10, 90), ("Profil", 8, 0), ("3/4", 18, 40), ("Dessus", 70, 60)]
light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
fig = plt.figure(figsize=(16, 8.4), facecolor="#15171c")
for r, a in enumerate(assets):
    polys, colors = [], []
    for p in a.parts.values():
        v = np.array(p["v"]); base = np.array(hex_to_rgb(p["color"]))
        for f in p["f"]:
            tri = v[list(f)]; n = np.cross(tri[1]-tri[0], tri[2]-tri[0]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            polys.append(tri[:, [0, 2, 1]]); colors.append(np.clip(base*(0.35+0.75*max(0, (n/ln)@light)), 0, 1))
    allv = np.concatenate(polys).reshape(-1, 3); c = (allv.max(0)+allv.min(0))/2; rad = (allv.max(0)-allv.min(0)).max()/2
    for k, (t, el, az) in enumerate(views):
        ax = fig.add_subplot(2, 4, r*4+k+1, projection="3d", facecolor="#15171c")
        ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors=colors, linewidths=0.2))
        ax.set_xlim(c[0]-rad, c[0]+rad); ax.set_ylim(c[1]-rad, c[1]+rad); ax.set_zlim(c[2]-rad, c[2]+rad)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=el, azim=az); ax.set_axis_off()
        ax.set_title(f"{a.name} · {t}" + (f"\n{a.tri_count()} tris" if k == 0 else ""), color="#e8e8e8", fontsize=11)
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=80, facecolor=fig.get_facecolor()); print("ok")
