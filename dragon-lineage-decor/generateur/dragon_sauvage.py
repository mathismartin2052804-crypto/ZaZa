# Dragon sauvage de Dragon Lineage : style stylisé lisse (type Fortnite), découpé pour l'animation.
#
# - 21 morceaux rigides (Torso, Neck1, Neck2, Head, Jaw, Tail1-4, pattes, ailes) avec un pivot
#   par articulation : dans Studio, chaque morceau devient une MeshPart reliée par un Motor6D.
# - Chaque morceau se termine par une boule de même rayon que son voisin : pas de trou au pli.
# - Couleurs par texture « palette » (64x64) : changer de lignée = changer la texture.
# - Les yeux sont une MeshPart à part (Neon) pour pouvoir briller.
# Repère Roblox : Y en haut, le dragon regarde vers -Z, 1 unité = 1 stud.
import numpy as np
from sdf import (Grid, ellipsoid, ellipsoid_r, look_basis, sphere, cone_seg, smooth_chain, chain,
                 smin, smax, union, to_mesh)

# emplacements dans la palette (grille 4x4)
SLOTS = ["skin", "back", "belly", "horn", "membrane", "teeth", "pupil", "eye"]

VARIANTS = {
    "Feu": {"skin": "#B8281F", "back": "#7E1612", "belly": "#FFC55A", "horn": "#4A332C",
            "membrane": "#E8642C", "teeth": "#F4EAD2", "pupil": "#120806", "eye": "#FFB21C"},
    "Glace": {"skin": "#3C78C0", "back": "#244E8C", "belly": "#D4F1FF", "horn": "#EEF8FF",
              "membrane": "#86CCF2", "teeth": "#FFFFFF", "pupil": "#0B1A33", "eye": "#8CF4FF"},
    "Foret": {"skin": "#3F7B3A", "back": "#284F26", "belly": "#DCCB6E", "horn": "#5B4229",
              "membrane": "#86B44D", "teeth": "#F1E8C8", "pupil": "#0E1408", "eye": "#E2FF57"},
    "Ombre": {"skin": "#2C2440", "back": "#17121F", "belly": "#7051A0", "horn": "#CFC6DE",
              "membrane": "#56347C", "teeth": "#E6E0F0", "pupil": "#07050B", "eye": "#C34BFF"},
}

# ---------- squelette (pivots des articulations) ----------
J = {
    "neck": (0, 6.9, -4.0), "neck2": (0, 8.3, -5.0), "head": (0, 9.55, -5.6), "jaw": (0, 9.5, -6.0),
    "tail": (0, 5.35, 3.1), "tail2": (0, 4.55, 5.2), "tail3": (0, 3.75, 7.2), "tail4": (0, 3.15, 9.1),
    "tail_end": (0, 2.85, 10.9),
}
for s, n in ((1, "R"), (-1, "L")):
    J["shoulder" + n] = (s * 1.62, 4.5, -2.4)
    J["elbow" + n] = (s * 1.78, 2.75, -1.85)
    J["hip" + n] = (s * 1.42, 4.6, 1.5)
    J["knee" + n] = (s * 1.62, 2.75, 0.75)
    J["wing" + n] = (s * 1.15, 6.85, -1.85)
    J["welbow" + n] = (s * 4.0, 8.15, -0.95)
    J["wrist" + n] = (s * 6.8, 8.95, -1.55)
R_NECK, R_NECK2, R_HEAD, R_TAIL, R_TAIL2, R_TAIL3, R_TAIL4 = 1.08, 0.84, 0.7, 1.02, 0.8, 0.58, 0.38


def J_(k):
    return np.asarray(J[k], float)


def spikes(P, pts, radii, n, h0, h1, rb0, rb1, lean=0.7, t0=0.1, t1=0.9):
    """Rangée d'épines sur le dessus d'un tube (pts/radii = axe du tube)."""
    from sdf import catmull
    curve = np.array(catmull(pts, 8))
    rr = np.interp(np.linspace(0, 1, len(curve)), np.linspace(0, 1, len(radii)), radii)
    out = []
    for i, t in enumerate(np.linspace(t0, t1, n)):
        k = t * (len(curve) - 1)
        a, f = int(k), k - int(k)
        b = min(a + 1, len(curve) - 1)
        c = curve[a] * (1 - f) + curve[b] * f
        r = rr[a] * (1 - f) + rr[b] * f
        base = c + np.array([0, r * 0.82, 0])
        hh = h0 + (h1 - h0) * i / max(n - 1, 1)
        tip = base + np.array([0, hh, hh * lean])
        out.append(cone_seg(P, base, tip, rb0 + (rb1 - rb0) * i / max(n - 1, 1), 0.02))
    return union(*out)


def bands(P, origin, direction, period=0.42):
    d = np.asarray(direction, float); d /= np.linalg.norm(d)
    x = (P - np.asarray(origin, np.float32)) @ d.astype(np.float32)
    return 0.5 + 0.5 * np.cos(2 * np.pi * x / period)


# ---------- morceaux ----------
# Chaque fonction renvoie un dict de couches : "skin" (volume plein) et, au choix,
# "belly"/"back" (zones de couleur posées sur la peau), "horn", "teeth", "pupil", "membrane" (volumes).

def torso(P):
    chest = ellipsoid(P, (0, 5.5, -2.1), (1.75, 1.85, 2.1))
    keel = ellipsoid(P, (0, 4.55, -2.75), (1.1, 1.0, 1.25))       # poitrail bombé
    belly = ellipsoid(P, (0, 5.35, 0.4), (1.3, 1.38, 2.0))         # taille plus fine
    hips = ellipsoid(P, (0, 5.45, 1.9), (1.38, 1.32, 1.35))
    d = smin(smin(smin(chest, keel, 0.5), belly, 0.7), hips, 0.5)
    d = smin(d, smooth_chain(P, [(0, 5.8, -3.0), (0, 6.4, -3.6), J["neck"]], [1.3, 1.1, R_NECK], 4, 0.1), 0.4)
    d = smin(d, smooth_chain(P, [(0, 5.4, 2.4), J["tail"]], [1.15, R_TAIL], 3, 0.1), 0.3)
    for s in (-1, 1):
        d = smin(d, ellipsoid(P, (s * 1.45, 5.0, -2.35), (0.75, 1.1, 0.95)), 0.35)    # épaules
        d = smin(d, ellipsoid(P, (s * 1.22, 4.95, 1.5), (0.74, 1.12, 1.12)), 0.4)     # hanches (cachent le haut des cuisses)
        d = smin(d, sphere(P, J["wing" + ("R" if s > 0 else "L")], 0.46), 0.35)      # racine des ailes
    belly_region = smin(ellipsoid(P, (0, 4.1, -0.4), (1.2, 1.45, 3.6)),
                        ellipsoid(P, (0, 5.4, -3.75), (1.0, 1.7, 1.1)), 0.4)
    back_region = smax(ellipsoid(P, (0, 7.15, -0.5), (1.05, 1.1, 4.4)), -belly_region, 0.1)
    horn = spikes(P, [(0, 6.25, -3.4), (0, 6.6, -1.5), (0, 6.55, 0.5), (0, 6.25, 2.2), (0, 5.95, 3.0)],
                  [1.0, 0.95, 0.95, 0.85, 0.75], 6, 0.75, 0.5, 0.22, 0.17)
    return {"skin": d, "belly": (belly_region, ((0, 4, 0), (0.15, 0.35, 1))), "back": back_region, "horn": horn}


def tube_seg(P, a, b, ra, rb, mid=None, belly=True, spike=None):
    pts = [J_(a) if isinstance(a, str) else a, *(mid or []), J_(b) if isinstance(b, str) else b]
    d = smooth_chain(P, pts, [ra] + ([] if not mid else [(ra + rb) / 2] * len(mid)) + [rb], 4, 0.06)
    d = smin(d, sphere(P, pts[0], ra), 0.02)
    d = smin(d, sphere(P, pts[-1], rb), 0.02)
    out = {"skin": d}
    pa, pb = np.asarray(pts[0]), np.asarray(pts[-1])
    axis = pb - pa
    if belly:
        ext = axis * 0.12
        under = smooth_chain(P, [pa - ext + (0, -ra * 0.75, 0) + _front(axis) * ra * 0.25,
                                 pb + ext + (0, -rb * 0.75, 0) + _front(axis) * rb * 0.25], [ra * 0.72, rb * 0.72], 3, 0.05)
        out["belly"] = (under, (tuple(pa), tuple(axis)))
        out["back"] = smooth_chain(P, [pa + (0, ra * 0.95, 0), pb + (0, rb * 0.95, 0)], [ra * 0.62, rb * 0.62], 3, 0.05)
    if spike:
        out["horn"] = spikes(P, [pa, pb], [ra, rb], *spike)
    return out


def _front(axis):
    """Direction « ventre » perpendiculaire à l'axe (vers le bas/l'avant)."""
    a = axis / np.linalg.norm(axis)
    down = np.array([0, -1.0, 0])
    f = down - a * (down @ a)
    n = np.linalg.norm(f)
    return f / n if n > 1e-6 else np.array([0, 0, -1.0])


def neck1(P):
    return tube_seg(P, "neck", "neck2", R_NECK, R_NECK2, spike=(3, 0.55, 0.45, 0.18, 0.15, 0.6, 0.15, 0.85))


def neck2(P):
    return tube_seg(P, "neck2", "head", R_NECK2, R_HEAD, spike=(3, 0.45, 0.35, 0.15, 0.12, 0.6, 0.15, 0.85))


EYE_C = [(s * 0.6, 10.12, -6.72) for s in (-1, 1)]


def head(P):
    d = sphere(P, J["head"], R_HEAD)
    skull = ellipsoid(P, (0, 10.0, -6.0), (0.88, 0.8, 1.05))
    snout = ellipsoid_r(P, (0, 9.86, -7.35), (0.58, 0.46, 1.2), look_basis((0, -0.12, -1)))
    nose = ellipsoid(P, (0, 9.9, -8.2), (0.3, 0.27, 0.32))
    d = smin(d, skull, 0.45)
    d = smin(d, smin(snout, nose, 0.25), 0.45)
    for s in (-1, 1):
        d = smin(d, ellipsoid_r(P, (s * 0.48, 10.5, -6.6), (0.3, 0.16, 0.6), look_basis((s * 0.25, -0.35, -1))), 0.18)
        d = smin(d, ellipsoid(P, (s * 0.62, 9.68, -6.05), (0.36, 0.42, 0.62)), 0.3)   # joues
        d = smax(d, -sphere(P, (s * 0.17, 10.1, -8.55), 0.075), 0.04)                 # narines
        d = smax(d, -ellipsoid(P, (s * 0.7, EYE_C[0][1], EYE_C[0][2]), (0.15, 0.17, 0.3)), 0.05)
    # bouche : le bas du museau est plat, la mâchoire vient dessous
    d = smax(d, np.where(P[..., 2] < -6.3, 9.42 - P[..., 1], -10.0), 0.05)
    horn = []
    teeth = []
    for s in (-1, 1):
        horn.append(smooth_chain(P, [(s * 0.42, 10.55, -5.7), (s * 0.66, 10.95, -5.0), (s * 0.82, 11.15, -4.15),
                                     (s * 0.86, 11.05, -3.3)], [0.27, 0.2, 0.11, 0.02], 5, 0.03))
        horn.append(smooth_chain(P, [(s * 0.75, 10.3, -5.45), (s * 1.08, 10.48, -4.95), (s * 1.25, 10.45, -4.5)],
                                 [0.15, 0.09, 0.02], 4, 0.02))
        for y, z in ((9.75, -5.55), (9.45, -5.6)):
            horn.append(cone_seg(P, (s * 0.85, y, z), (s * 1.3, y - 0.05, z + 0.65), 0.12, 0.02))   # collerette
        horn.append(cone_seg(P, (s * 0.2, 10.18, -8.25), (s * 0.24, 10.45, -8.1), 0.07, 0.015))  # cornes de nez
        for z in (-7.25, -7.65, -8.05):
            teeth.append(cone_seg(P, (s * 0.38 * (1 + (z + 7.25) * 0.35), 9.48, z), (s * 0.38 * (1 + (z + 7.25) * 0.35), 9.24, z),
                                  0.055 if z > -8 else 0.07, 0.01))
    horn += [spikes(P, [(0, 10.3, -5.9), (0, 10.0, -5.1)], [0.6, 0.6], 3, 0.25, 0.35, 0.1, 0.12, 0.8, 0.0, 1.0)]
    pupil = union(*[ellipsoid(P, (np.sign(e[0]) * 0.735, e[1], e[2] - 0.03), (0.03, 0.13, 0.045)) for e in EYE_C])
    return {"skin": d, "horn": union(*horn), "teeth": union(*teeth), "pupil": pupil,
            "belly": (ellipsoid(P, (0, 9.25, -6.2), (0.55, 0.3, 0.9)), ((0, 9.5, -6.0), (0, 0, -1)))}


def eyes(P):
    return {"eye": union(*[ellipsoid(P, e, (0.13, 0.15, 0.28)) for e in EYE_C])}


def jaw(P):
    d = sphere(P, J["jaw"], 0.46)
    d = smin(d, ellipsoid_r(P, (0, 9.25, -7.05), (0.5, 0.24, 1.15), look_basis((0, 0.1, -1))), 0.35)
    d = smin(d, ellipsoid(P, (0, 9.24, -7.95), (0.32, 0.2, 0.3)), 0.2)
    d = smax(d, P[..., 1] - 9.43, 0.04)
    teeth = []
    for s in (-1, 1):
        for z in (-7.0, -7.45, -7.85):
            x = s * 0.33 * (1 + (z + 7.0) * 0.3)
            teeth.append(cone_seg(P, (x, 9.36, z), (x, 9.58, z), 0.045, 0.01))
    return {"skin": d, "teeth": union(*teeth),
            "belly": (ellipsoid(P, (0, 9.0, -7.0), (0.42, 0.22, 1.2)), ((0, 9.5, -6.0), (0, 0, -1)))}


def tail(i):
    keys = ["tail", "tail2", "tail3", "tail4", "tail_end"]
    radii = [R_TAIL, R_TAIL2, R_TAIL3, R_TAIL4, 0.12]
    sp = [(3, 0.5, 0.4, 0.18, 0.15), (3, 0.4, 0.32, 0.15, 0.12), (3, 0.3, 0.22, 0.12, 0.09), (3, 0.2, 0.12, 0.08, 0.05)][i]

    def f(P):
        out = tube_seg(P, keys[i], keys[i + 1], radii[i], radii[i + 1], spike=sp + (0.8, 0.15, 0.85))
        if i == 3:  # pointe en fer de lance
            e = J_("tail_end")
            fin = smin(ellipsoid(P, e + (0, 0, 0.55), (0.62, 0.09, 0.62)),
                       ellipsoid(P, e + (0, 0, 0.15), (0.25, 0.12, 0.45)), 0.1)
            fin = smax(fin, -ellipsoid(P, e + (0, 0, 1.25), (0.3, 0.3, 0.32)), 0.05)
            out["membrane"] = fin
        return out
    return f


def front_upper(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a, b = J_("shoulder" + n), J_("elbow" + n)
        d = smooth_chain(P, [a, b], [0.74, 0.52], 4, 0.05)
        d = smin(d, ellipsoid(P, a + (side * 0.08, -0.6, 0.1), (0.72, 1.05, 0.78)), 0.3)   # épaule musclée
        d = smin(smin(d, sphere(P, a, 0.74), 0.02), sphere(P, b, 0.52), 0.02)
        return {"skin": d}
    return f


def front_lower(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a = J_("elbow" + n)
        w = a + (side * -0.05, -1.85, -0.6)
        d = smooth_chain(P, [a, a + (0, -0.9, -0.2), w], [0.52, 0.45, 0.38], 4, 0.05)
        d = smin(d, sphere(P, a, 0.52), 0.02)
        d = smin(d, ellipsoid(P, a + (0, -0.55, -0.12), (0.52, 0.78, 0.56)), 0.2)     # avant-bras
        d = smin(d, paw(P, w + (0, -0.55, -0.42)), 0.25)
        d = smax(d, -P[..., 1], 0.02)
        claws = paw_claws(P, w + (0, -0.55, -0.42))
        return {"skin": d, "horn": claws}
    return f


def paw(P, c):
    """Patte large avec 3 orteils ronds."""
    d = ellipsoid(P, c, (0.58, 0.32, 0.72))
    for dx in (-0.32, 0.0, 0.32):
        d = smin(d, ellipsoid(P, c + (dx, -0.08, -0.62), (0.2, 0.2, 0.3)), 0.12)
    return d


def paw_claws(P, c):
    return union(*[cone_seg(P, c + (dx, -0.08, -0.85), c + (dx * 1.1, -0.26, -1.18), 0.11, 0.02)
                   for dx in (-0.32, 0.0, 0.32)])


def back_upper(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a, b = J_("hip" + n), J_("knee" + n)
        d = ellipsoid_r(P, (a + b) / 2 + (side * 0.02, 0.25, 0.3), (0.85, 1.45, 1.12), look_basis((0, 0.3, 1)))
        d = smin(d, smooth_chain(P, [a, b], [0.78, 0.56], 4, 0.05), 0.3)
        d = smin(smin(d, sphere(P, a, 0.78), 0.02), sphere(P, b, 0.56), 0.02)
        return {"skin": d}
    return f


def back_lower(side):
    n = "R" if side > 0 else "L"

    def f(P):
        k = J_("knee" + n)
        hock = k + (0, -1.25, 1.25)
        ankle = k + (0, -2.35, 0.75)
        d = smooth_chain(P, [k, hock, ankle], [0.56, 0.4, 0.34], 4, 0.06)
        d = smin(d, sphere(P, k, 0.56), 0.02)
        d = smin(d, ellipsoid(P, k + (0, -0.5, 0.45), (0.45, 0.7, 0.55)), 0.2)        # mollet
        d = smin(d, paw(P, ankle + (0, -0.12, -0.38)), 0.25)
        d = smax(d, -P[..., 1], 0.02)
        claws = paw_claws(P, ankle + (0, -0.12, -0.38))
        claws = np.minimum(claws, cone_seg(P, hock + (0, 0, 0.1), hock + (0, 0.1, 0.5), 0.1, 0.02))   # ergot
        return {"skin": d, "horn": claws}
    return f


WING_TIPS = [(12.0, 8.4, 0.8), (11.2, 6.1, 2.8), (8.8, 4.5, 3.9), (5.6, 4.7, 3.3)]
WING_ROOT = (0.9, 6.0, 1.7)


def wing_upper(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a, b = J_("wing" + n), J_("welbow" + n)
        d = smooth_chain(P, [a, (a + b) / 2 + (0, 0.25, 0), b], [0.45, 0.36, 0.3], 4, 0.05)
        d = smin(smin(d, sphere(P, a, 0.45), 0.02), sphere(P, b, 0.3), 0.02)
        return {"skin": d}
    return f


def wing_lower(side):
    n = "R" if side > 0 else "L"

    def f(P):
        a, w = J_("welbow" + n), J_("wrist" + n)
        d = smooth_chain(P, [a, w], [0.3, 0.22], 4, 0.05)
        d = smin(smin(d, sphere(P, a, 0.3), 0.02), sphere(P, w, 0.25), 0.08)
        for t in WING_TIPS:
            tip = np.array([side * t[0], t[1], t[2]])
            d = smin(d, smooth_chain(P, [w, w + (tip - w) * 0.5 + (0, 0.15, -0.1), tip], [0.13, 0.08, 0.03], 4, 0.03), 0.06)
        claw = cone_seg(P, w + (side * 0.05, 0.12, -0.05), w + (side * 0.15, 0.55, -0.35), 0.12, 0.02)
        return {"skin": d, "horn": claw}
    return f


def membrane(center, border_pts, festoon, per_edge=10, rings=8, sag=0.22, billow=0.25, thick=0.04):
    """Membrane d'aile en éventail, festonnée entre les doigts, gonflée vers le bas."""
    import trimesh
    c = np.asarray(center, float)
    border = []
    for i in range(len(border_pts) - 1):
        a, b = np.asarray(border_pts[i], float), np.asarray(border_pts[i + 1], float)
        for t in np.linspace(0, 1, per_edge, endpoint=False):
            p = a + (b - a) * t
            if festoon[i]:
                p = p + (c - p) * sag * np.sin(np.pi * t)
            border.append(p)
    border.append(np.asarray(border_pts[-1], float))
    border = np.array(border)
    nrm = np.zeros(3)
    for i in range(len(border) - 1):
        nrm += np.cross(border[i] - c, border[i + 1] - c)
    nrm /= np.linalg.norm(nrm)
    if nrm[1] < 0:  # gonflement toujours vers le bas
        nrm = -nrm
    verts = [c]
    for k in range(1, rings + 1):
        t = k / rings
        for p in border:
            q = c + (p - c) * t
            verts.append(q - nrm * billow * np.sin(np.pi * t) * np.linalg.norm(p - c) / 3.0)
    verts = np.array(verts)
    m = len(border)
    faces = [(0, 1 + i, 2 + i) for i in range(m - 1)]
    for k in range(rings - 1):
        a0, b0 = 1 + k * m, 1 + (k + 1) * m
        for i in range(m - 1):
            faces += [(a0 + i, b0 + i, b0 + i + 1), (a0 + i, b0 + i + 1, a0 + i + 1)]
    faces = np.array(faces)
    sheet = trimesh.Trimesh(verts, faces, process=True)
    vn = sheet.vertex_normals
    top = trimesh.Trimesh(sheet.vertices + vn * thick, sheet.faces, process=False)
    bot = trimesh.Trimesh(sheet.vertices - vn * thick, sheet.faces[:, ::-1], process=False)
    return trimesh.util.concatenate([top, bot])


def wing_membranes(side):
    n = "R" if side > 0 else "L"
    tips = [np.array([side * t[0], t[1], t[2]]) for t in WING_TIPS]
    a, e, w = J_("wing" + n), J_("welbow" + n), J_("wrist" + n)
    root = np.array([side * WING_ROOT[0], WING_ROOT[1], WING_ROOT[2]])
    lower = membrane(w, [e] + tips + [e], [False, True, True, True, False])
    upper = membrane((a + e + tips[3] + root) / 4, [a, e, tips[3], root, a], [False, False, True, False], sag=0.18)
    return upper, lower


# ---------- liste des morceaux : nom, parent, pivot, fonction, budget de triangles ----------

def segments():
    S = [("Torso", None, (0, 5.3, 0), torso, 7000),
         ("Neck1", "Torso", J["neck"], neck1, 1800), ("Neck2", "Neck1", J["neck2"], neck2, 1600),
         ("Head", "Neck2", J["head"], head, 6000), ("Jaw", "Head", J["jaw"], jaw, 1400),
         ("Eyes", "Head", J["head"], eyes, 300),
         ("Tail1", "Torso", J["tail"], tail(0), 1600), ("Tail2", "Tail1", J["tail2"], tail(1), 1300),
         ("Tail3", "Tail2", J["tail3"], tail(2), 1100), ("Tail4", "Tail3", J["tail4"], tail(3), 1200)]
    for s, n in ((1, "R"), (-1, "L")):
        S += [("FrontUpperLeg" + n, "Torso", J["shoulder" + n], front_upper(s), 1100),
              ("FrontLowerLeg" + n, "FrontUpperLeg" + n, J["elbow" + n], front_lower(s), 1500),
              ("BackUpperLeg" + n, "Torso", J["hip" + n], back_upper(s), 1300),
              ("BackLowerLeg" + n, "BackUpperLeg" + n, J["knee" + n], back_lower(s), 1600),
              ("WingUpper" + n, "Torso", J["wing" + n], wing_upper(s), 900),
              ("WingLower" + n, "WingUpper" + n, J["welbow" + n], wing_lower(s), 2200)]
    return S


SHELL_LAYERS = ("belly", "back")
SOLID_ORDER = ["skin", "horn", "teeth", "pupil", "membrane", "eye"]


def find_bbox(fn, lo=(-12, -0.2, -9.5), hi=(12, 12.5, 12.5), h=0.2):
    g = Grid(lo, hi, h)
    layers = fn(g.P)
    inside = None
    for k, v in layers.items():
        if k in SHELL_LAYERS:
            continue
        m = v < h
        inside = m if inside is None else inside | m
    idx = np.argwhere(inside)
    return g.lo + idx.min(0) * h - 0.3, g.lo + idx.max(0) * h + 0.3


def build_segment(name, fn, budget, h=0.045):
    """Renvoie {couche: trimesh} pour un morceau."""
    lo, hi = find_bbox(fn)
    g = Grid(lo, hi, h)
    L = fn(g.P)
    meshes = {}
    skin = L.get("skin")
    total_solid = 0
    for k in SOLID_ORDER:
        if k in L:
            total_solid += 1
    for k in SOLID_ORDER:
        if k not in L:
            continue
        share = {"skin": 0.6, "eye": 1.0}.get(k, 0.08)
        meshes[k] = to_mesh(g, L[k], max(120, int(budget * share)), smooth_iter=8 if k == "skin" else 3)
    for k in SHELL_LAYERS:
        if k not in L or skin is None:
            continue
        v = L[k]
        if isinstance(v, tuple):
            region, (o, ax) = v
            lift = 0.035 + 0.035 * bands(g.P, o, ax) ** 4
        else:
            region, lift = v, 0.03
        shell = smax(smax(skin - lift, -(skin + 0.12), 0.001), region, 0.06)
        if (shell < 0).sum() < 50:
            continue
        meshes[k] = to_mesh(g, shell, max(150, int(budget * 0.11)), smooth_iter=4)
    return meshes


def build():
    out = {}
    for name, parent, pivot, fn, budget in segments():
        meshes = build_segment(name, fn, budget)
        if name.startswith("WingUpper") or name.startswith("WingLower"):
            side = 1 if name.endswith("R") else -1
            up, low = wing_membranes(side)
            meshes["membrane"] = up if name.startswith("WingUpper") else low
        out[name] = {"parent": parent, "pivot": tuple(float(x) for x in pivot), "layers": meshes}
        print(f"{name:16s}", {k: len(m.faces) for k, m in meshes.items()}, flush=True)
    return out
