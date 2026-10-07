# Dragon low-poly v3 : maquette 3D de la planche de concept v3 (pose d'attaque, tête « Brute » affinée,
# ailes asymétriques, queue lame, valeurs retravaillées, 3 points Neon forts, un trait de forme par lignée).
# Même découpage en morceaux que dragon_lowpoly.py (pivots aux articulations) pour pouvoir l'animer ensuite.
# Repère : Y vers le haut, l'avant du dragon vers -Z, sol en y = 0. Côté proche de la caméra de profil : -X.
import numpy as np
import dragon_sauvage as D
from rendu import rot
from sdf import Grid, catmull, ellipsoid, sphere, cone_seg, smooth_chain, smin, smax, union, to_mesh, ellipsoid_r, look_basis

# ---------- palettes (une couleur par emplacement de la texture) ----------
VARIANTS = {
    "Feu":   {"skin": "#C42A1E", "back": "#7A1610", "limb": "#9E2016", "belly": "#F2B24A", "horn": "#E8D2B0",
              "spike": "#FF7A1A", "membrane": "#D4521E", "tip": "#FFB040", "teeth": "#F4EEDC", "claw": "#F0E2C8",
              "pupil": "#1A0606", "eye": "#FFC21A"},
    "Glace": {"skin": "#3E7CC4", "back": "#22487E", "limb": "#30629E", "belly": "#CFE6F4", "horn": "#F2FAFF",
              "spike": "#BDF2FF", "membrane": "#5C96C4", "tip": "#9CEBFF", "teeth": "#F4FAFF", "claw": "#E6F4FF",
              "pupil": "#08142A", "eye": "#7FF4FF"},
    "Foret": {"skin": "#3F8A34", "back": "#234E1E", "limb": "#2F6A28", "belly": "#C8B266", "horn": "#7A5530",
              "spike": "#A6D83A", "membrane": "#5E9A2C", "tip": "#D2F05A", "teeth": "#F2ECD6", "claw": "#E8DEC0",
              "pupil": "#0C1A06", "eye": "#D8FF3A"},
    "Ombre": {"skin": "#3A2C50", "back": "#1C1428", "limb": "#2A2038", "belly": "#6A5290", "horn": "#DCD2EA",
              "spike": "#8E3AD0", "membrane": "#42285A", "tip": "#C060F0", "teeth": "#EDE6F4", "claw": "#E2D8EE",
              "pupil": "#0A0610", "eye": "#E840FF"},
}
SLOTS = ["skin", "back", "limb", "belly", "horn", "spike", "membrane", "tip", "teeth", "claw", "pupil", "eye"]

NEAR = -1   # côté proche (caméra de profil à -X)

# ---------- squelette en pose d'attaque ----------
HB = np.array([0.0, 7.7, -5.0])          # base du crâne
HEAD_R = rot(ex=-14)                      # tête baissée, tendue vers l'avant
HS = 1.1                                 # échelle de la tête
NECK = [(0, 5.7, -2.9), (0, 6.9, -4.0), tuple(HB)]
TAIL = [(0, 4.9, 2.4), (0, 4.25, 4.9), (0, 3.55, 7.3), (0, 3.45, 9.5), (0, 4.1, 11.3), (0, 5.1, 12.5)]
TAIL_R = [1.3, 1.0, 0.74, 0.52, 0.36, 0.24]


def legs(s):
    near = s == NEAR
    dz = -0.6 if near else 0.25          # patte avant proche en avant (pas d'attaque)
    front = dict(shoulder=(s * 1.85, 4.5, -2.0), elbow=(s * 2.1, 2.75, -1.25 + dz * 0.3),
                 wrist=(s * 1.95, 1.0, -2.25 + dz), paw=(s * 1.95, 0.36, -2.75 + dz))
    hz = 0.35 if near else -0.15
    back = dict(hip=(s * 1.6, 4.5, 1.7), knee=(s * 1.85, 2.55, 0.45 + hz),
                hock=(s * 1.85, 1.35, 1.85 + hz), paw=(s * 1.85, 0.36, 1.35 + hz))
    return front, back


def wing_pose(s):
    if s == NEAR:   # aile proche : levée et ouverte
        return dict(root=(s * 1.15, 6.4, -1.3), elbow=(s * 3.3, 8.9, -0.3), wrist=(s * 5.5, 10.7, -1.5),
                    tips=[(s * 10.9, 11.6, 0.2), (s * 10.3, 7.8, 2.4), (s * 7.8, 5.7, 3.3), (s * 4.7, 5.7, 2.9)],
                    back=(s * 1.0, 6.0, 1.6))
    # aile éloignée : à moitié repliée (sinon on lit une aile dédoublée)
    return dict(root=(s * 1.15, 6.4, -1.3), elbow=(s * 2.7, 8.6, 0.2), wrist=(s * 3.6, 10.2, 1.7),
                tips=[(s * 4.9, 11.3, 5.9), (s * 4.7, 8.6, 6.4), (s * 3.9, 6.8, 5.3), (s * 2.9, 6.3, 3.6)],
                back=(s * 1.0, 6.0, 1.6))


# ---------- outils ----------
def octa(P, c, axes, size):
    """Octaèdre (losange 3D) : axes = matrice 3x3 (colonnes), size = demi-longueurs."""
    q = (P - np.asarray(c, np.float32)) @ np.asarray(axes, np.float32)
    return (np.abs(q) / np.asarray(size, np.float32)).sum(-1) - 1.0


def plates(P, belly, origin, direction, period=0.9):
    """Bande ventrale découpée en plaques (alternance plaque / creux)."""
    b = D.bands(P, origin, direction, period)
    return np.where(b > 0.2, belly, 1.0)


def spike_row(P, pts, radii, n, h0, h1, rb0, rb1, lean=0.7, t0=0.1, t1=0.9, lin="Feu"):
    if lin == "Glace":   # cristaux : éclats fins, par deux, inclinés différemment
        a = D.spikes(P, pts, radii, n, h0 * 2.3, h1 * 2.3, rb0 * 1.05, rb1 * 1.05, lean * 0.3, t0, t1)
        b = D.spikes(P, [np.add(p, (0.3, -0.15, 0.25)) for p in pts], radii, n, h0 * 1.5, h1 * 1.5,
                     rb0 * 0.75, rb1 * 0.75, lean * 1.2, t0, t1)
        c = D.spikes(P, [np.add(p, (-0.3, -0.15, 0.25)) for p in pts], radii, n, h0 * 1.3, h1 * 1.3,
                     rb0 * 0.7, rb1 * 0.7, lean * 1.2, t0, t1)
        return union(a, b, c)
    if lin == "Feu":     # crête en flammes : plus haute, couchée vers l'arrière
        return D.spikes(P, pts, radii, n, h0 * 1.35, h1 * 1.35, rb0, rb1, lean * 1.5, t0, t1)
    return D.spikes(P, pts, radii, n, h0, h1, rb0, rb1, lean, t0, t1)


# ---------- morceaux : chaque fonction renvoie {couche: SDF} ----------
# couches pleines : skin, horn, spike, teeth, claw, eye, pupil, glow, tip
# zones de couleur (posées face par face sur skin) : belly, back, limb

def torso(lin):
    def f(P):
        d = ellipsoid(P, (0, 5.05, -1.75), (1.95, 1.95, 1.95))                       # poitrail
        d = smin(d, ellipsoid(P, (0, 3.95, -2.3), (1.25, 1.15, 1.25)), 0.5)          # bréchet
        d = smin(d, ellipsoid(P, (0, 4.75, 0.3), (1.3, 1.35, 1.6)), 0.6)             # taille
        d = smin(d, ellipsoid(P, (0, 4.75, 1.75), (1.5, 1.45, 1.35)), 0.5)           # bassin
        for s in (-1, 1):
            d = smin(d, ellipsoid(P, (s * 1.55, 4.85, -1.9), (0.95, 1.3, 1.1)), 0.35)  # épaules
            d = smin(d, ellipsoid(P, (s * 1.3, 4.45, 1.65), (0.85, 1.25, 1.2)), 0.4)   # hanches
            d = smin(d, sphere(P, (s * 1.15, 6.3, -1.3), 0.55), 0.35)                  # attache d'aile
        d = smin(d, smooth_chain(P, [(0, 5.5, -2.7), NECK[0]], [1.55, 1.4], 3, 0.1), 0.4)
        d = smin(d, smooth_chain(P, [(0, 4.85, 2.0), TAIL[0]], [1.35, TAIL_R[0]], 3, 0.1), 0.3)
        belly = smin(ellipsoid(P, (0, 3.35, -0.5), (1.2, 1.25, 3.3)), ellipsoid(P, (0, 4.7, -3.45), (1.15, 1.6, 0.95)), 0.4)
        back = ellipsoid(P, (0, 6.55, -0.2), (1.35, 0.95, 3.9))
        spikes = spike_row(P, [(0, 6.55, -2.4), (0, 6.75, -0.8), (0, 6.45, 0.9), (0, 6.05, 2.3)],
                           [0.95, 1.0, 0.95, 0.85], 4, 1.0, 0.65, 0.3, 0.22, lin=lin)
        return {"skin": d, "belly": plates(P, belly, (0, 4, -1), (0, 0.35, -1), 0.95), "back": back, "spike": spikes}
    return f


def chest_front(y=4.75):
    z = np.linspace(-6, -2, 801, dtype=np.float32)
    pts = np.stack([np.zeros_like(z), np.full_like(z, y), z], -1)
    return float(z[np.argmax(torso("Feu")(pts)["skin"] < 0)])


def chest_gem(P):
    c = (0.0, 4.75, chest_front() + 0.1)
    return {"glow": octa(P, c, np.eye(3), (0.42, 0.62, 0.3)) * 0.25}


def neck(lin):
    def f(P):
        d = smooth_chain(P, NECK, [1.3, 1.08, 0.95], 4, 0.1)
        belly = ellipsoid_r(P, (0, 6.1, -4.1), (0.75, 0.9, 1.6), look_basis((0, 0.6, -0.8)))
        belly = smax(belly, -(P[..., 1] - 6.9 + (P[..., 2] + 4) * 0.9), 0.05)   # seulement la gorge
        back = ellipsoid_r(P, (0, 7.2, -3.3), (0.9, 0.7, 1.7), look_basis((0, 0.6, -0.8)))
        spk = spike_row(P, NECK, [1.3, 1.08, 0.95], 3, 0.55, 0.75, 0.24, 0.22, 0.9, 0.1, 0.85, lin=lin)
        out = {"skin": d, "belly": plates(P, belly, (0, 6, -4), (0, 0.8, -0.6), 0.7), "back": back, "spike": spk}
        if lin == "Foret":   # collerette de feuilles derrière les joues
            leaves = []
            for s in (-1, 1):
                for k, (dy, dz, ang) in enumerate(((0.6, 0.2, 0.5), (0.0, 0.5, 0.0), (-0.6, 0.3, -0.5))):
                    c = HB + np.array([s * 1.05, dy, 0.5 + dz])
                    leaves.append(ellipsoid_r(P, c + np.array([s * 0.5, 0, 0.5]), (0.12, 0.32, 0.85),
                                              look_basis((s * 0.6, ang, 1.0))))
            out["spike"] = union(out["spike"], *leaves)
        return out
    return f


def _hq(P):
    """Coordonnées locales de la tête (avant = -Z)."""
    return ((P - HB.astype(np.float32)) @ HEAD_R.astype(np.float32)) / HS


def head(lin):
    def f(P):
        q = _hq(P)
        d = ellipsoid(q, (0, 0.35, -0.55), (0.98, 0.88, 1.05))                         # crâne
        d = smin(d, ellipsoid_r(q, (0, 0.28, -2.25), (0.66, 0.5, 1.3), look_basis((0, -0.08, -1))), 0.45)  # museau
        d = smin(d, ellipsoid(q, (0, 0.62, -2.85), (0.4, 0.24, 0.55)), 0.25)            # bosse nasale
        d = smin(d, ellipsoid(q, (0, 0.24, -3.4), (0.48, 0.42, 0.42)), 0.3)             # truffe carrée
        for s in (-1, 1):
            d = smin(d, ellipsoid_r(q, (s * 0.55, 0.9, -1.35), (0.36, 0.24, 0.72), look_basis((s * 0.3, -0.5, -1))), 0.12)  # arcade
            d = smin(d, ellipsoid(q, (s * 0.8, 0.1, -0.85), (0.4, 0.42, 0.72)), 0.3)    # pommette
            d = smax(d, -ellipsoid_r(q, (s * 0.74, 0.55, -1.55), (0.2, 0.15, 0.36), look_basis((s * 0.2, -0.3, -1))), 0.06)  # orbite
            d = smax(d, -sphere(q, (s * 0.2, 0.42, -3.75), 0.09), 0.04)                 # narines
        # gueule : coupée par un plan qui remonte vers la joue (rictus)
        mouth = -0.12 + 0.17 * np.clip(q[..., 2] + 3.6, 0, None)
        d = smax(d, np.where(q[..., 2] < -0.7, mouth - q[..., 1], -10.0), 0.05)
        horn, spike, teeth = [], [], []
        hk = 1.3 if lin == "Feu" else 1.0
        for s in (-1, 1):
            if lin == "Foret":   # bois de cerf
                base = [(s * 0.5, 0.95, -0.3), (s * 0.85, 1.6, 0.2), (s * 1.1, 2.4, 0.4), (s * 1.2, 3.1, 0.9)]
                horn.append(smooth_chain(q, base, [0.2, 0.15, 0.1, 0.03], 4, 0.03))
                for a, b in (((s * 0.85, 1.6, 0.2), (s * 1.5, 2.0, -0.2)), ((s * 1.1, 2.4, 0.4), (s * 1.7, 2.7, 0.6)),
                             ((s * 1.0, 2.1, 0.3), (s * 0.7, 2.7, -0.3))):
                    horn.append(cone_seg(q, a, b, 0.1, 0.03))
            else:
                straight = lin == "Ombre"
                pts = ([(s * 0.5, 0.9, -0.35), (s * 0.7, 1.15, 0.5), (s * 0.85, 1.35, 1.5), (s * 0.95, 1.5, 2.5)]
                       if straight else
                       [(s * 0.5, 0.9, -0.35), (s * 0.75, 1.3, 0.35), (s * 0.95, 1.5 * hk, 1.25 * hk), (s * 1.0, 1.95 * hk, 2.0 * hk)])
                horn.append(smooth_chain(q, pts, [0.34, 0.25, 0.14, 0.02], 5, 0.03))
                horn.append(smooth_chain(q, [(s * 0.88, 0.5, -0.05), (s * 1.3, 0.55, 0.55), (s * 1.5, 0.5, 0.95)],
                                         [0.17, 0.1, 0.02], 4, 0.02))
                if lin == "Feu":   # cornes d'arcade vers l'avant
                    horn.append(cone_seg(q, (s * 0.62, 1.0, -1.15), (s * 0.85, 1.45, -1.55), 0.14, 0.02))
            spike.append(cone_seg(q, (s * 0.85, -0.25, -0.55), (s * 1.4, -0.45, 0.25), 0.16, 0.02))   # épine de joue
            spike.append(cone_seg(q, (s * 0.7, -0.5, -0.4), (s * 1.15, -0.85, 0.2), 0.13, 0.02))
            teeth.append(cone_seg(q, (s * 0.44, -0.02, -3.0), (s * 0.48, -0.72, -3.05), 0.11, 0.015))   # croc
            for z in (-2.2, -2.55):
                teeth.append(cone_seg(q, (s * 0.5, 0.0, z), (s * 0.52, -0.3, z), 0.06, 0.01))
        horn.append(cone_seg(q, (0, 0.7, -2.95), (0, 1.12, -2.75), 0.12, 0.02))   # corne de nez
        eye = union(*[ellipsoid_r(q, (s * 0.7, 0.56, -1.55), (0.1, 0.11, 0.27), look_basis((s * 0.2, -0.35, -1)))
                      for s in (-1, 1)])
        pupil = union(*[ellipsoid(q, (s * 0.8, 0.56, -1.56), (0.03, 0.1, 0.035)) for s in (-1, 1)])
        back = ellipsoid(q, (0, 1.05, -0.9), (0.75, 0.38, 1.6))
        S = lambda x: x * HS
        return {"skin": S(d), "horn": S(union(*horn)), "spike": S(union(*spike)), "teeth": S(union(*teeth)),
                "eye": S(eye), "pupil": S(pupil), "back": S(back)}
    return f


def jaw(lin):
    def f(P):
        q = _hq(P)
        d = ellipsoid(q, (0, -0.4, -0.95), (0.82, 0.55, 0.75))                          # muscle de mâchoire
        d = smin(d, ellipsoid_r(q, (0, -0.32, -2.35), (0.56, 0.3, 1.2), look_basis((0, 0.12, -1))), 0.35)
        d = smin(d, ellipsoid(q, (0, -0.3, -3.25), (0.4, 0.26, 0.3)), 0.2)               # menton
        mouth = -0.12 + 0.17 * np.clip(q[..., 2] + 3.6, 0, None)
        d = smax(d, q[..., 1] - (mouth - 0.04), 0.04)
        teeth = []
        for s in (-1, 1):
            teeth.append(cone_seg(q, (s * 0.36, -0.2, -3.25), (s * 0.4, 0.35, -3.3), 0.09, 0.015))   # crocs du bas
            teeth.append(cone_seg(q, (s * 0.44, -0.15, -2.4), (s * 0.46, 0.08, -2.4), 0.05, 0.01))
        belly = ellipsoid(q, (0, -0.75, -1.8), (0.5, 0.25, 1.6))
        S = lambda x: x * HS
        return {"skin": S(d), "teeth": S(union(*teeth)), "belly": S(belly)}
    return f


def tail(i, lin):
    def f(P):
        a, b = TAIL[i], TAIL[i + 1]
        last = i == 3
        pts = TAIL[i:i + 3] if last else [a, b]
        rr = TAIL_R[i:i + 3] if last else TAIL_R[i:i + 2]
        d = smooth_chain(P, pts, rr, 4, 0.05)
        d = smin(d, sphere(P, a, TAIL_R[i] * 0.98), 0.05)
        spk = spike_row(P, pts, rr, 2 if not last else 3, 0.75 - 0.15 * i, 0.65 - 0.15 * i,
                        0.24 - 0.04 * i, 0.2 - 0.04 * i, 0.9, 0.2, 0.8, lin=lin)
        out = {"skin": d, "spike": spk,
               "belly": plates(P, smooth_chain(P, [np.add(p, (0, -r * 0.75, 0)) for p, r in zip(pts, rr)],
                                                [r * 0.55 for r in rr], 3, 0.05), (0, 0, 0), (0, -0.1, 1), 0.8)}
        if last:   # lame en fer de lance, tranchant Neon
            e, p = np.array(TAIL[-1]), np.array(TAIL[-2])
            u = (e - p) / np.linalg.norm(e - p)
            w = np.array([1.0, 0, 0])
            v = np.cross(w, u)
            ax = np.stack([u, v, w], 1)
            c = e + u * 1.15
            out["spike"] = union(out["spike"], octa(P, c, ax, (1.75, 1.05, 0.2)) * 0.3)
            edge = octa(P, c + u * 0.1, ax, (1.8, 1.12, 0.09)) * 0.3
            edge = smax(edge, -((P - c.astype(np.float32)) @ u.astype(np.float32)) + 0.15, 0.02)
            out["glow"] = edge
        return out
    return f


def paw(P, c, fwd=-1):
    c = np.asarray(c, float)
    d = ellipsoid(P, c, (0.62, 0.36, 0.72))
    claws = []
    for k in (-1, 0, 1):
        t = c + np.array([k * 0.36, -0.06, fwd * 0.62])
        d = smin(d, ellipsoid(P, t, (0.2, 0.22, 0.3)), 0.12)
        claws.append(cone_seg(P, t + (0, 0, fwd * 0.18), t + (0, -0.22, fwd * 0.62), 0.12, 0.02))
    return d, union(*claws)


def front_upper(s):
    L, _ = legs(s)

    def f(P):
        d = smooth_chain(P, [L["shoulder"], L["elbow"]], [1.0, 0.72], 3, 0.05)
        d = smin(d, ellipsoid(P, np.add(L["shoulder"], (0, -0.3, 0)), (0.85, 1.1, 0.95)), 0.3)
        return {"skin": d}
    return f


def front_lower(s):
    L, _ = legs(s)

    def f(P):
        d = smooth_chain(P, [L["elbow"], L["wrist"], L["paw"]], [0.72, 0.58, 0.54], 4, 0.05)
        pd, claws = paw(P, L["paw"])
        spur = cone_seg(P, np.add(L["elbow"], (0, 0.05, 0.25)), np.add(L["elbow"], (0, 0.2, 0.95)), 0.2, 0.02)   # éperon de coude
        return {"skin": smin(d, pd, 0.15), "claw": claws, "spike": spur, "limb": d * 0 - 1}
    return f


def back_upper(s):
    _, L = legs(s)

    def f(P):
        d = ellipsoid_r(P, np.add(L["hip"], (s * 0.15, -0.75, -0.2)), (0.95, 1.45, 1.3), look_basis((0, -0.3, -1)))
        d = smin(d, smooth_chain(P, [L["hip"], L["knee"]], [1.1, 0.75], 3, 0.05), 0.3)
        return {"skin": d}
    return f


def back_lower(s):
    _, L = legs(s)

    def f(P):
        d = smooth_chain(P, [L["knee"], L["hock"], L["paw"]], [0.72, 0.54, 0.52], 4, 0.05)
        pd, claws = paw(P, L["paw"])
        return {"skin": smin(d, pd, 0.15), "claw": claws, "limb": d * 0 - 1}
    return f


def _finger(w, t):
    w, t = np.asarray(w, float), np.asarray(t, float)
    return [w, w + (t - w) * 0.5 + (0, 0.2, -0.1), t]


def wing_upper(s):
    W = wing_pose(s)

    def f(P):
        a, b = np.array(W["root"]), np.array(W["elbow"])
        d = smooth_chain(P, [a, (a + b) / 2 + (0, 0.3, -0.2), b], [0.5, 0.4, 0.34], 4, 0.05)
        return {"skin": d}
    return f


def wing_lower(s):
    W = wing_pose(s)

    def f(P):
        e, w = np.array(W["elbow"]), np.array(W["wrist"])
        d = smooth_chain(P, [e, (e + w) / 2 + (0, 0.35, -0.35), w], [0.34, 0.3, 0.28], 4, 0.05)   # bord d'attaque courbe
        tips = []
        for k, t in enumerate(W["tips"]):
            r0 = 0.19 - 0.025 * k
            d = smin(d, smooth_chain(P, _finger(w, t), [r0, r0 * 0.6, 0.04], 4, 0.03), 0.06)
            c = catmull(_finger(w, t), 6)
            n = len(c)
            tips.append(smooth_chain(P, c[int(n * 0.72):], [r0 * 0.5 + 0.04, 0.07], 3, 0.02))
        claw = cone_seg(P, w + (0, 0.15, -0.05), w + (s * 0.1, 0.8, -0.5), 0.18, 0.02)
        return {"skin": d, "horn": claw, "tip": union(*tips)}
    return f


def wing_membranes(s, lin):
    W = wing_pose(s)
    tips = [np.array(t, float) for t in W["tips"]]
    a, e, w = np.array(W["root"]), np.array(W["elbow"]), np.array(W["wrist"])
    root = np.array(W["back"])
    kw = dict(per_edge=4, rings=3, thick=0.05)
    border, fest = [e], [False]
    for i, t in enumerate(tips):
        if lin == "Ombre" and i < len(tips) - 1:   # membrane déchirée : encoches entre les doigts
            nxt = tips[i + 1]
            border += [t, t + (nxt - t) * 0.35 + (w - t) * 0.45, t + (nxt - t) * 0.55 + (w - t) * 0.1]
            fest += [False, False, True]
        else:
            border.append(t)
            fest.append(True)
    border.append(e)
    fest[-1] = False
    lower = D.membrane(w, border, fest[:len(border) - 1], sag=0.3, **kw)
    upper = D.membrane((a + e + tips[-1] + root) / 4, [a, e, tips[-1], root, a], [False, False, True, False],
                       sag=0.22, **kw)
    return upper, lower


# ---------- liste des morceaux ----------
def segments(lin="Feu"):
    S = [("Torso", None, (0, 4.8, 0), torso(lin), 700),
         ("ChestGem", "Torso", (0, 4.75, -3.9), chest_gem, 24),
         ("Neck", "Torso", NECK[0], neck(lin), 260),
         ("Head", "Neck", tuple(HB), head(lin), 760),
         ("Jaw", "Head", tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS), jaw(lin), 220)]
    for i in range(4):
        S.append((f"Tail{i + 1}", "Torso" if i == 0 else f"Tail{i}", TAIL[i], tail(i, lin), 130))
    for s, n in ((1, "R"), (-1, "L")):
        F, B = legs(s)
        W = wing_pose(s)
        S += [("FrontUpperLeg" + n, "Torso", F["shoulder"], front_upper(s), 130),
              ("FrontLowerLeg" + n, "FrontUpperLeg" + n, F["elbow"], front_lower(s), 210),
              ("BackUpperLeg" + n, "Torso", B["hip"], back_upper(s), 160),
              ("BackLowerLeg" + n, "BackUpperLeg" + n, B["knee"], back_lower(s), 210),
              ("WingUpper" + n, "Torso", W["root"], wing_upper(s), 120),
              ("WingLower" + n, "WingUpper" + n, W["elbow"], wing_lower(s), 230)]
    return S


SOLID = {"skin": None, "horn": 110, "spike": 160, "teeth": 70, "claw": 60, "eye": 40, "pupil": 24, "glow": 40, "tip": 60}
ZONES = ("limb", "belly", "back")   # ordre de priorité des zones de couleur sur la peau


def build_segment(fn, budget, h=0.07):
    lo, hi = D.find_bbox(fn, lo=(-13, -0.3, -10), hi=(13, 13.5, 14.5))
    g = Grid(lo, hi, h)
    L = fn(g.P)
    layers, slots = {}, {}
    for k, tb in SOLID.items():
        if k not in L or not (L[k] < 0).any():
            continue
        m = to_mesh(g, L[k], budget if tb is None else tb, smooth_iter=6 if k == "skin" else 2, strict=False)
        m.unmerge_vertices()
        layers[k] = m
        if k == "skin":
            R = fn(m.triangles_center.astype(np.float32))
            col = np.array(["skin"] * len(m.faces), dtype=object)
            for zone in ZONES[::-1]:
                if zone in R:
                    col[np.asarray(R[zone]) < 0] = zone
            slots[k] = col.tolist()
    return layers, slots


def build(lin="Feu", verbose=False):
    import trimesh
    out = {}
    for name, parent, pivot, fn, budget in segments(lin):
        layers, slots = build_segment(fn, budget)
        if name.startswith("WingUpper") or name.startswith("WingLower"):
            up, low = wing_membranes(1 if name.endswith("R") else -1, lin)
            m = up if name.startswith("WingUpper") else low
            m.unmerge_vertices()
            layers["membrane"] = m
        out[name] = {"parent": parent, "pivot": tuple(float(x) for x in pivot), "layers": layers, "slots": slots}
        if verbose:
            print(f"{name:16s}", {k: len(m.faces) for k, m in layers.items()}, flush=True)
    return out


def tri_count(model):
    return sum(len(m.faces) for seg in model.values() for m in seg["layers"].values())
