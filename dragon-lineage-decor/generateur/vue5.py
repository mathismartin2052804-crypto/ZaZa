# Aperçu du dragon de cristal sous plusieurs angles.
# Usage : python3 vue5.py sortie.png [module]   (module : assets5 par défaut, assets5v3 pour la v3)
import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from meshlib import hex_to_rgb
import importlib

def polys_of(parts):
    light = np.array([0.4, 0.8, 0.45]); light /= np.linalg.norm(light)
    polys, colors = [], []
    for p in parts.values():
        v = np.array(p["v"]); base = np.array(hex_to_rgb(p["color"]))
        for f in p["f"]:
            tri = v[list(f)]; n = np.cross(tri[1]-tri[0], tri[2]-tri[0]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            sh = 1.0 if p["material"] == "Neon" else 0.35 + 0.8*max(0, (n/ln) @ light)
            polys.append(tri[:, [0, 2, 1]]); colors.append(np.clip(base*sh, 0, 1))
    return polys, colors

def draw(ax, polys, colors, el, az, title, full=False):
    ax.add_collection3d(Poly3DCollection(polys, facecolors=colors, edgecolors=np.clip(np.array(colors)*1.5, 0, 1), linewidths=0.25))
    allv = np.concatenate(polys).reshape(-1, 3); mn, mx = allv.min(0), allv.max(0)
    if full:
        c = (mx+mn)/2; r = (mx-mn).max()/2; mn, mx = c-r, c+r
    ax.set_xlim(mn[0], mx[0]); ax.set_ylim(mn[1], mx[1]); ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(mx-mn, zoom=1.0 if not full and el < 10 else 1.3); ax.view_init(elev=el, azim=az); ax.set_axis_off()
    ax.set_title(title, color="#e8e8e8", fontsize=12)

if __name__ == "__main__":
    mod = importlib.import_module(sys.argv[2] if len(sys.argv) > 2 else "assets5")
    a = mod.all_assets()[0]
    polys, colors = polys_of(a.parts)
    fig = plt.figure(figsize=(18, 11), facecolor="#1a1a1a")
    ax = fig.add_subplot(2, 3, (1, 3), projection="3d", facecolor="#1a1a1a")
    draw(ax, polys, colors, 6, 0, f"{a.name} · profil ({a.tri_count()} tris)")
    for k, (t, el, az) in enumerate([("3/4 avant", 18, -40), ("De face", 5, -90), ("Dessus", 75, 0)]):
        draw(fig.add_subplot(2, 3, 4+k, projection="3d", facecolor="#1a1a1a"), polys, colors, el, az, t, full=k > 0)
    plt.tight_layout(); plt.savefig(sys.argv[1], dpi=75, facecolor=fig.get_facecolor()); print("ok")
