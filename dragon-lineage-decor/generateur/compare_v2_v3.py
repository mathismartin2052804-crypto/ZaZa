# Planche v2 / v3 : squelette (vue d'ensemble + gros plan tête), porte du repaire, arche de la route.
# Usage : python3 generateur/compare_v2_v3.py comparaison-serie4.png
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from meshlib import hex_to_rgb
import assets2, assets3, assets4

light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)


def polys_of(a):
    polys, colors = [], []
    for p in a.parts.values():
        v = np.array(p["v"]); base = np.array(hex_to_rgb(p["color"])); neon = p["material"] == "Neon"
        for f in p["f"]:
            tri = v[list(f)]; n = np.cross(tri[1]-tri[0], tri[2]-tri[0]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            polys.append(tri[:, [0, 2, 1]]); colors.append(np.clip(base*(1.0 if neon else 0.35+0.75*max(0, (n/ln)@light)), 0, 1))
    return polys, colors


rows = [("v2", [assets3._with_new_skull(assets2.dragon_skeleton, "Dragon_Skeleton_v2", 21),
                assets3.gate_lair_v2("Gate_Lair_v2", 23),
                assets3._with_new_skull(assets2.egg_road_arch, "Gate_EggRoad_v2", 24)]),
        ("v3", [assets4._with_skull_v3(assets2.dragon_skeleton, "Dragon_Skeleton_v3", 21),
                assets4.gate_lair_v3("Gate_Lair_v3", 23),
                assets4._with_skull_v3(assets2.egg_road_arch, "Gate_EggRoad_v3", 24, skull_scale=1.1)])]
# (index de l'objet, titre, élévation, azimut, centre (x, z, y) ou None, rayon ou None)
cols = [(0, "squelette", 25, -50, None, None), (0, "tête du squelette", 12, 50, (1.5, 13.5, 4.0), 6.5),
        (1, "porte du repaire", 10, 80, None, None), (2, "arche route des œufs", 10, 80, None, None)]
fig = plt.figure(figsize=(18, 9), facecolor="#15171c")
for r, (tag, objs) in enumerate(rows):
    cache = [polys_of(a) for a in objs]
    for k, (i, title, el, az, c, rad) in enumerate(cols):
        polys, colors = cache[i]
        ax = fig.add_subplot(2, 4, r*4+k+1, projection="3d", facecolor="#15171c")
        ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors=colors, linewidths=0.2))
        if c is None:
            allv = np.concatenate(polys).reshape(-1, 3); c = (allv.max(0)+allv.min(0))/2; rad = (allv.max(0)-allv.min(0)).max()/2
        c = np.array(c)
        ax.set_xlim(c[0]-rad, c[0]+rad); ax.set_ylim(c[1]-rad, c[1]+rad); ax.set_zlim(c[2]-rad, c[2]+rad)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=el, azim=az); ax.set_axis_off()
        ax.set_title(f"{tag} · {title}\n{objs[i].tri_count()} tris", color="#e8e8e8", fontsize=12)
plt.tight_layout(); plt.savefig(sys.argv[1], dpi=75, facecolor=fig.get_facecolor()); print("ok")
