# Dragon sauvage, direction « low-poly sculpté » : facettes visibles, silhouette exagérée,
# accents Neon par lignée. Même squelette et même découpage animable que dragon_sauvage.py.
#
# Par rapport à la version lisse :
#  - ~6 000 triangles au lieu de 40 000 (facettes = ombrage plat, une couleur par face) ;
#  - tête 30 % plus grosse, poitrail et épaules massifs, taille fine, pattes plus épaisses ;
#  - ailes à 3 doigts dont le bout s'allume (Neon), gemme Neon sur le poitrail ;
#  - le ventre et le dos sont colorés face par face (pas de couche posée par-dessus).
import numpy as np
import dragon_sauvage as D
from sdf import (Grid, ellipsoid, sphere, cone_seg, smooth_chain, chain, catmull, smin, smax, union, to_mesh)

HEAD_K = 1.3
H = np.asarray(D.J["head"], float)
R_NECK, R_NECK2, R_HEAD = 1.15, 0.98, 0.7 * HEAD_K

VARIANTS = {k: dict(v) for k, v in D.VARIANTS.items()}
VARIANTS["Feu"].update(eye="#FF7A1A", belly="#FFB43C")
VARIANTS["Ombre"].update(belly="#5E4590")
SLOTS = D.SLOTS + ["glow"]
for v in VARIANTS.values():
    v["glow"] = v["eye"]


def about_head(p):
    return tuple(H + (np.asarray(p, float) - H) * HEAD_K)


def scaled(fn, c=H, k=HEAD_K):
    """Agrandit un morceau autour d'un point (une SDF se met à l'échelle : k * d(c + (P - c) / k))."""
    c32 = np.asarray(c, np.float32)

    def f(P):
        out = {}
        for key, val in fn(c32 + (P - c32) / k).items():
            out[key] = (val[0] * k, val[1]) if isinstance(val, tuple) else val * k
        return out
    return f


def inflate(fn, skin=0.12, horn=0.04):
    def f(P):
        L = fn(P)
        L["skin"] = L["skin"] - skin
        if "horn" in L:
            L["horn"] = L["horn"] - horn
        return L
    return f


# ---------- morceaux redessinés ----------

def torso(P):
    chest = ellipsoid(P, (0, 5.6, -2.2), (1.95, 2.0, 2.2))
    keel = ellipsoid(P, (0, 4.6, -2.9), (1.2, 1.1, 1.3))
    waist = ellipsoid(P, (0, 5.5, 0.5), (1.15, 1.2, 1.8))
    hips = ellipsoid(P, (0, 5.45, 1.95), (1.38, 1.3, 1.3))
    d = smin(smin(smin(chest, keel, 0.5), waist, 0.6), hips, 0.5)
    d = smin(d, smooth_chain(P, [(0, 6.0, -3.2), (0, 6.5, -3.7), D.J["neck"]], [1.45, 1.25, R_NECK], 4, 0.1), 0.4)
    d = smin(d, smooth_chain(P, [(0, 5.4, 2.4), D.J["tail"]], [1.15, D.R_TAIL], 3, 0.1), 0.3)
    for s in (-1, 1):
        d = smin(d, ellipsoid(P, (s * 1.6, 5.25, -2.3), (0.9, 1.25, 1.05)), 0.35)     # épaules massives
        d = smin(d, ellipsoid(P, (s * 1.22, 4.95, 1.5), (0.78, 1.12, 1.12)), 0.4)     # hanches
        d = smin(d, sphere(P, D.J["wing" + ("R" if s > 0 else "L")], 0.5), 0.35)
    belly = smin(ellipsoid(P, (0, 4.0, -0.6), (1.15, 1.4, 3.6)), ellipsoid(P, (0, 5.3, -3.9), (1.15, 1.9, 1.1)), 0.4)
    back = smax(ellipsoid(P, (0, 7.3, -0.6), (1.25, 1.15, 4.6)), -belly, 0.1)
    horn = D.spikes(P, [(0, 6.6, -3.4), (0, 7.0, -1.5), (0, 6.6, 0.5), (0, 6.25, 2.2), (0, 5.95, 3.0)],
                    [1.0, 1.0, 0.95, 0.85, 0.75], 5, 1.0, 0.6, 0.32, 0.22)
    return {"skin": d, "belly": belly, "back": back, "horn": horn}


def _chest_front(y=5.75):
    """Position Z de la surface du poitrail à la hauteur y (pour poser la gemme dessus)."""
    z = np.linspace(-6, -2, 801, dtype=np.float32)
    pts = np.stack([np.zeros_like(z), np.full_like(z, y), z], -1)
    return float(z[np.argmax(torso(pts)["skin"] < 0)])


GEM_C = None


def chest_gem(P):
    global GEM_C
    if GEM_C is None:
        GEM_C = (0.0, 5.75, _chest_front() + 0.12)
    q = np.abs(P - np.asarray(GEM_C, np.float32)) / np.asarray((0.5, 0.75, 0.34), np.float32)
    return {"glow": (q.sum(-1) - 1.0) * 0.2}


def neck1(P):
    return D.tube_seg(P, D.J_("neck"), D.J_("neck2"), R_NECK, R_NECK2, spike=(2, 0.7, 0.6, 0.24, 0.2, 0.6, 0.2, 0.8))


def neck2(P):
    return D.tube_seg(P, D.J_("neck2"), H, R_NECK2, R_HEAD, spike=(2, 0.6, 0.5, 0.2, 0.18, 0.6, 0.2, 0.8))


WING_TIPS = [(12.6, 8.7, 1.0), (10.9, 5.6, 3.4), (6.8, 4.4, 3.9)]


def _finger(w, tip):
    return [w, w + (tip - w) * 0.5 + (0, 0.15, -0.1), tip]


def wing_lower(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a, w = D.J_("welbow" + n), D.J_("wrist" + n)
        d = smooth_chain(P, [a, w], [0.36, 0.28], 4, 0.05)
        d = smin(smin(d, sphere(P, a, 0.36), 0.02), sphere(P, w, 0.32), 0.08)
        for t in WING_TIPS:
            tip = np.array([side * t[0], t[1], t[2]])
            d = smin(d, smooth_chain(P, _finger(w, tip), [0.17, 0.11, 0.04], 4, 0.03), 0.06)
        claw = cone_seg(P, w + (side * 0.05, 0.15, -0.05), w + (side * 0.2, 0.75, -0.45), 0.17, 0.03)
        return {"skin": d, "horn": claw}
    return f


def wing_glow(side):
    """Le bout des doigts de l'aile s'allume (comme des os lumineux)."""
    n = "R" if side > 0 else "L"

    def f(P):
        w = D.J_("wrist" + n)
        parts = []
        for t in WING_TIPS:
            tip = np.array([side * t[0], t[1], t[2]])
            curve = catmull(_finger(w, tip), 6)
            r = np.interp(np.linspace(0, 1, len(curve)), [0, 0.5, 1], [0.17, 0.11, 0.04]) + 0.03
            k = int(len(curve) * 0.45)
            parts.append(chain(P, curve[k:], r[k:], 0.02))
        return {"glow": union(*parts)}
    return f


def wing_membranes(side):
    n = "R" if side > 0 else "L"
    tips = [np.array([side * t[0], t[1], t[2]]) for t in WING_TIPS]
    a, e, w = D.J_("wing" + n), D.J_("welbow" + n), D.J_("wrist" + n)
    root = np.array([side * 0.9, 6.0, 1.9])
    kw = dict(per_edge=4, rings=3, thick=0.05)
    lower = D.membrane(w, [e] + tips + [e], [False, True, True, False], sag=0.3, **kw)
    upper = D.membrane((a + e + tips[-1] + root) / 4, [a, e, tips[-1], root, a], [False, False, True, False],
                       sag=0.22, **kw)
    return upper, lower


# ---------- liste des morceaux ----------

def segments():
    S = [("Torso", None, (0, 5.3, 0), torso, 800),
         ("ChestGem", "Torso", (0, 5.75, -4.5), chest_gem, 24),
         ("Neck1", "Torso", D.J["neck"], neck1, 200), ("Neck2", "Neck1", D.J["neck2"], neck2, 190),
         ("Head", "Neck2", tuple(H), scaled(D.head), 850),
         ("Jaw", "Head", about_head(D.J["jaw"]), scaled(D.jaw), 200),
         ("Eyes", "Head", tuple(H), scaled(D.eyes), 60),
         ("Tail1", "Torso", D.J["tail"], D.tail(0), 170), ("Tail2", "Tail1", D.J["tail2"], D.tail(1), 140),
         ("Tail3", "Tail2", D.J["tail3"], D.tail(2), 120), ("Tail4", "Tail3", D.J["tail4"], D.tail(3), 120)]
    for s, n in ((1, "R"), (-1, "L")):
        S += [("FrontUpperLeg" + n, "Torso", D.J["shoulder" + n], inflate(D.front_upper(s), 0.16), 130),
              ("FrontLowerLeg" + n, "FrontUpperLeg" + n, D.J["elbow" + n], inflate(D.front_lower(s), 0.16, 0.06), 200),
              ("BackUpperLeg" + n, "Torso", D.J["hip" + n], inflate(D.back_upper(s), 0.12), 160),
              ("BackLowerLeg" + n, "BackUpperLeg" + n, D.J["knee" + n], inflate(D.back_lower(s), 0.14, 0.06), 210),
              ("WingUpper" + n, "Torso", D.J["wing" + n], inflate(D.wing_upper(s), 0.06), 150),
              ("WingLower" + n, "WingUpper" + n, D.J["welbow" + n], wing_lower(s), 260),
              ("WingGlow" + n, "WingLower" + n, D.J["wrist" + n], wing_glow(s), 120)]
    return S


SOLID_BUDGET = {"horn": 100, "teeth": 72, "pupil": 32, "membrane": 60}


def build_segment(fn, budget, h=0.06):
    import trimesh
    lo, hi = D.find_bbox(fn)
    g = Grid(lo, hi, h)
    L = fn(g.P)
    layers, slots = {}, {}
    for k in ("skin", "horn", "teeth", "pupil", "membrane", "eye", "glow"):
        if k not in L:
            continue
        tgt = budget if k in ("skin", "eye", "glow") else SOLID_BUDGET[k]
        m = to_mesh(g, L[k], tgt, smooth_iter=6 if k == "skin" else 2, strict=False)
        m.unmerge_vertices()  # facettes : chaque face a ses propres sommets
        layers[k] = m
        if k == "skin":
            # couleur face par face selon les zones ventre / dos
            R = fn(m.triangles_center.astype(np.float32))
            col = np.array(["skin"] * len(m.faces), dtype=object)
            for zone in ("back", "belly"):
                if zone in R:
                    v = R[zone][0] if isinstance(R[zone], tuple) else R[zone]
                    col[np.asarray(v) < 0] = zone
            slots[k] = col.tolist()
    return layers, slots


def build():
    out = {}
    for name, parent, pivot, fn, budget in segments():
        layers, slots = build_segment(fn, budget)
        if name.startswith("WingUpper") or name.startswith("WingLower"):
            up, low = wing_membranes(1 if name.endswith("R") else -1)
            m = up if name.startswith("WingUpper") else low
            m.unmerge_vertices()
            layers["membrane"] = m
        out[name] = {"parent": parent, "pivot": tuple(float(x) for x in pivot), "layers": layers, "slots": slots}
        print(f"{name:16s}", {k: len(m.faces) for k, m in layers.items()}, flush=True)
    return out
