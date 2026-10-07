# Corps de dragon v4 : tout le corps en polygones placés à la main (comme la tête v6/v7), proportions de prédateur
# adulte au lieu de la silhouette « jouet » de la v3 :
#   - tête v7 inchangée mais relativement plus petite : le corps, le cou et la queue sont allongés
#     (tête ≈ 12 % de la longueur au lieu de ≈ 20 %)
#   - long cou en S qui porte la tête haut, garrot marqué, poitrail profond en carène, taille fine, hanches musclées
#   - pattes avant plus courtes et écartées, pattes arrière digitigrades (genou en avant, jarret en arrière)
#   - longue queue effilée terminée par une lame propre à chaque lignée
#   - grandes ailes (envergure ≈ longueur du corps) avec membrane en deux tons et bord par lignée
#   - bande ventrale continue en plaques alternées de la gorge au bout de la queue, bande dorsale + motif lumineux
#   - crête dorsale du style des collerettes de la tête (flammes, lames de glace, feuilles, lames déchirées)
# Mêmes noms de morceaux que la v3 (Torso, Neck, Head, Jaw, Tail1-4, pattes, ailes) pour export_dragon.py.
# Usage : python3 corps_v4.py  ->  ../concept-dragon-v4.png   (python3 corps_v4.py [cache_v3] ajoute la comparaison)
import os
import sys
import pickle
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import rendu
import tete_v7 as T7
import palette_corps as PC
from tete_v5 import loft, mesh, blade, sweep, cone, curve, both, mirror, FONT, FONT_B

LIGNEES = ["Feu", "Glace", "Foret", "Ombre"]
NOMS = {"Feu": "Feu", "Glace": "Glace", "Foret": "Forêt", "Ombre": "Ombre"}

# ---------- squelette (monde : avant = -Z, Y vers le haut, sol à y = 0) ----------
HS = 1.1                                   # échelle de la tête (comme la v3 : la tête ne change pas)
HEAD_R = rendu.rot(ex=-12)
NECK = [(0, 7.9, -4.3), (0, 8.9, -6.0), (0, 10.4, -7.1), (0, 11.5, -7.9), (0, 11.85, -8.5)]
HB = np.array([0.0, 11.75, -8.75])         # base du crâne, au bout du cou
# tronc : (z, dessus, dessous, demi-largeur)
TRONC = [(-5.0, 8.4, 5.6, 1.35), (-3.6, 8.9, 4.5, 1.9), (-2.0, 8.7, 4.35, 2.0), (-0.3, 8.25, 4.9, 1.8),
         (1.3, 7.95, 5.55, 1.4), (2.9, 8.1, 5.55, 1.6), (4.3, 7.75, 5.8, 1.35), (5.4, 7.3, 6.0, 1.0)]
TAIL = [(0, 6.75, 5.0), (0, 6.35, 7.6), (0, 5.4, 10.4), (0, 4.2, 13.3), (0, 3.4, 16.2), (0, 3.3, 19.0), (0, 3.9, 21.6)]
TAIL_RAD = [1.05, 0.88, 0.7, 0.52, 0.36, 0.24, 0.14]
TAIL_CUT = [0, 2, 3, 4, 6]                  # Tail1 = points 0-2, Tail2 = 2-3, Tail3 = 3-4, Tail4 = 4-6


def legs(s):
    front = dict(shoulder=(s * 1.75, 7.0, -3.1), elbow=(s * 2.45, 4.35, -2.2),
                 wrist=(s * 2.55, 1.35, -3.15), paw=(s * 2.6, 0.32, -3.75))
    back = dict(hip=(s * 1.65, 7.1, 3.2), knee=(s * 2.15, 4.7, 1.3),
                hock=(s * 2.1, 2.2, 4.3), paw=(s * 2.1, 0.32, 3.75))
    return front, back


def wing(s):
    return dict(root=(s * 1.3, 8.45, -2.5), elbow=(s * 4.6, 11.4, -1.1), wrist=(s * 8.0, 13.6, -2.3),
                tips=[(s * 16.5, 14.6, 0.2), (s * 15.6, 10.2, 4.6), (s * 12.2, 7.2, 7.0), (s * 7.6, 6.9, 6.6)],
                back=(s * 1.3, 7.6, 3.4))


# ---------- outils ----------
def tube(ctrl, radii_at, sides=6, n=2, rides=0.0):
    """Tube polygonal sur une courbe ; radii_at : [(t, r)…] interpolé le long de la courbe."""
    p = np.asarray(curve(ctrl, n), float)
    t = np.linspace(0, 1, len(p))
    ts, rs = zip(*radii_at)
    return sweep(p, np.interp(t, ts, rs), sides, rides)


def frame_rings(path, rads, shape, wscale=1.0):
    """Anneaux d'une forme (x, y) normalisée posés le long d'un chemin, x reste horizontal."""
    path = np.asarray(path, float)
    T = np.gradient(path, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    rings = []
    for p, t, r in zip(path, T, rads):
        x = np.array([1.0, 0, 0])
        up = np.cross(t, x); up /= np.linalg.norm(up)
        up = up if up[1] > 0 else -up
        rings.append([p + r * (sx * wscale * x + sy * up) for sx, sy in shape])
    return rings, T


def slab(poly, th=0.06):
    """Panneau plat épais (membrane) à partir d'un polygone 3D, triangulé en éventail."""
    P = np.asarray(poly, float)
    c = P.mean(0)
    n = np.cross(P[1] - P[0], P[2] - P[0])
    if np.linalg.norm(n) < 1e-9:
        n = np.cross(P[1] - c, P[2] - c)
    n = n / np.linalg.norm(n) * th / 2
    k = len(P)
    V_ = np.concatenate([P + n, P - n, [c + n, c - n]])
    F = []
    for i in range(k):
        j = (i + 1) % k
        F += [(2 * k, i, j), (2 * k + 1, k + j, k + i), (i, k + i, k + j), (i, k + j, j)]
    return trimesh.Trimesh(V_, np.array(F), process=False)


def crest_piece(lin, base, t, up, h, w):
    """Une pièce de crête dorsale dans le style des collerettes de la tête."""
    a, b = base - t * w, base + t * w
    tip = base + up * h + t * h * 0.55
    if lin == "Feu":
        return T7.flame(a, b, tip)
    if lin == "Glace":
        return [T7.crystal(base, up + t * 0.35, w * 0.45, h * 1.05)]
    if lin == "Foret":
        return [T7.leaf(a, b, tip, th=0.06)]
    return T7.torn(a, b, tip)


def cat(ms):
    ms = [m for m in ms if m is not None]
    return trimesh.util.concatenate(ms) if ms else None


# ---------- pièces ----------
SHAPE_TRONC = [(0, 1.0), (0.5, 0.92), (0.88, 0.58), (1.0, 0.08), (0.93, -0.4), (0.64, -0.78), (0.24, -0.98), (0, -1.0),
               (-0.24, -0.98), (-0.64, -0.78), (-0.93, -0.4), (-1.0, 0.08), (-0.88, 0.58), (-0.5, 0.92)]


def torso(lin):
    rings = []
    for z, top, bot, w in TRONC:
        cy, h = (top + bot) / 2, (top - bot) / 2
        rings.append([(sx * w, cy + sy * h, z) for sx, sy in SHAPE_TRONC])
    skin = loft(rings, (0, 7.0, -5.6), (0, 6.7, 5.9))
    # omoplates et pointes de hanche : petites arêtes qui cassent le « sac » du tronc
    bones = []
    for x, y, z, ln in ((1.25, 8.55, -3.4, 1.6), (1.15, 8.0, 2.9, 1.3)):
        bones += both(T7.plate((x, y, z), (0.15, 0.2, 1), (0.5, 1, 0), 0.5, ln, 0.18))
    crest = []
    for z in np.arange(-4.4, 5.2, 0.85):
        top = float(np.interp(z, [r[0] for r in TRONC], [r[1] for r in TRONC]))
        h = 0.75 - 0.25 * abs(z + 2.5) / 7
        crest += crest_piece(lin, np.array([0, top - 0.05, z]), np.array([0, 0, 1.0]), np.array([0, 1.0, 0.25]), h, 0.32)
    return {"skin": skin, "back": cat(bones), "spike": cat(crest)}


SHAPE_COU = [(0, 1.08), (0.62, 0.82), (1.0, 0.18), (0.9, -0.5), (0.45, -0.92), (0, -0.98),
             (-0.45, -0.92), (-0.9, -0.5), (-1.0, 0.18), (-0.62, 0.82)]


def neck(lin):
    path = np.asarray(curve(NECK, 2), float)
    rads = np.interp(np.linspace(0, 1, len(path)), [0, 0.35, 1], [1.55, 1.05, 0.88])
    rings, T = frame_rings(path, rads, SHAPE_COU)
    skin = loft(rings, path[0] - T[0] * 0.3, path[-1] + T[-1] * 0.1)
    crest = []
    for i in range(1, len(path) - 1):
        p, t, r = path[i], T[i], rads[i]
        up = np.cross(t, [1.0, 0, 0]); up /= np.linalg.norm(up); up = up if up[1] > 0 else -up
        crest += crest_piece(lin, p + up * r * 1.0, t, up, 0.35 * r + 0.15, 0.24)
    return {"skin": skin, "spike": cat(crest)}


def tail(i, lin):
    a, b = TAIL_CUT[i], TAIL_CUT[i + 1]
    pts = TAIL[max(a - 1, 0):b + 2] if i < 3 else TAIL[a - 1:]
    path = np.asarray(curve(pts, 3), float)
    # on ne garde que la portion entre TAIL[a] et TAIL[b]
    za, zb = TAIL[a][2] - (0.35 if i else 0.6), TAIL[b][2] + (0.3 if i < 3 else 0)
    keep = (path[:, 2] >= za) & (path[:, 2] <= zb)
    path = path[keep]
    rads = np.interp(path[:, 2], [p[2] for p in TAIL], TAIL_RAD)
    rings, T = frame_rings(path, rads, SHAPE_COU, 1.0)
    skin = loft(rings, path[0] - T[0] * 0.05, path[-1] + T[-1] * (0.05 if i < 3 else 0.3))
    crest = []
    for k in range(1, len(path) - (1 if i < 3 else 2), 2):
        p, t, r = path[k], T[k], rads[k]
        up = np.cross(t, [1.0, 0, 0]); up /= np.linalg.norm(up); up = up if up[1] > 0 else -up
        crest += crest_piece(lin, p + up * r * 0.95, t, up, 0.45 * r + 0.12, 0.2 + 0.1 * r)
    L = {"skin": skin, "spike": cat(crest)}
    if i == 3:
        L["tailblade"], L["glow"] = tail_blade(lin, path[-1], T[-1])
    return L


def tail_blade(lin, e, u, k=1.7):
    """Lame de bout de queue, une forme par lignée ; le tranchant (glow) prend la couleur lumineuse."""
    body, edge = _tail_blade(lin, np.zeros(3), u)
    for m in (body, edge):
        m.vertices = e + m.vertices * k
    return body, edge


def _tail_blade(lin, e, u):
    u = u / np.linalg.norm(u)
    up = np.array([0, 1.0, 0]) - u * u[1]; up /= np.linalg.norm(up)
    x = np.array([1.0, 0, 0])
    if lin == "Feu":      # fer de lance flamboyant : deux ailerons en flamme
        body = [slab([e, e + u * 1.2 + x * 0.95, e + u * 3.0, e + u * 1.2 - x * 0.95], 0.2)]
        body += [blade(e + u * 0.6 + x * 0.6, e + u * 1.4 + x * 0.8, e + u * 0.1 + x * 1.7 + up * 0.5, 0.1),
                 blade(e + u * 0.6 - x * 0.6, e + u * 1.4 - x * 0.8, e + u * 0.1 - x * 1.7 + up * 0.5, 0.1)]
        edge = [slab([e + u * 1.2 + x * 1.0, e + u * 3.15, e + u * 2.9, e + u * 1.25 + x * 0.85], 0.24),
                slab([e + u * 1.2 - x * 1.0, e + u * 3.15, e + u * 2.9, e + u * 1.25 - x * 0.85], 0.24)]
    elif lin == "Glace":  # prisme de glace + éclats
        body = [T7.crystal(e - u * 0.2, u, 0.3, 3.4)]
        body += [T7.crystal(e + u * 0.4, u + x * 0.9 + up * 0.3, 0.22, 1.5),
                 T7.crystal(e + u * 0.4, u - x * 0.9 + up * 0.3, 0.22, 1.5)]
        edge = [T7.crystal(e + u * 0.3 + up * 0.18, u, 0.12, 3.6)]
    elif lin == "Foret":  # grande feuille plate à nervure
        body = [T7.leaf(e - x * 0.9 + u * 0.1, e + x * 0.9 + u * 0.1, e + u * 3.4, th=0.14)]
        edge = [blade(e + u * 0.2 - up * 0.02, e + u * 0.6 - up * 0.02, e + u * 3.1, 0.18)]
    else:                 # faux recourbée vers le haut
        body = [slab([e, e + up * 0.7 + u * 0.8, e + up * 2.2 + u * 2.4, e + up * 0.4 + u * 2.0, e + u * 1.2], 0.18)]
        edge = [slab([e + up * 2.2 + u * 2.4, e + up * 0.42 + u * 2.15, e + up * 0.3 + u * 2.0, e + up * 1.9 + u * 2.15], 0.24)]
    return cat(body), cat(edge)


def paw(p, fwd, s, lin):
    """Patte : coussinet + 3 doigts griffus vers l'avant + ergot."""
    p, fwd = np.asarray(p, float), np.asarray(fwd, float) / np.linalg.norm(fwd)
    side = np.array([s * 1.0, 0, 0])
    pad = tube([p - fwd * 0.45 + [0, 0.15, 0], p, p + fwd * 0.4], [(0, 0.45), (1, 0.38)], 6)
    toes, claws = [pad], []
    for k in (-1, 0, 1):
        d = fwd + side * 0.35 * k; d /= np.linalg.norm(d)
        a = p + d * 0.25 + side * 0.2 * k
        b = a + d * 0.75 - [0, 0.12, 0]
        toes.append(tube([a, b], [(0, 0.2), (1, 0.15)], 5))
        claws.append(cone(b, b + d * 0.5 - [0, 0.3, 0], 0.14, 5))
    claws.append(cone(p - fwd * 0.35 + [0, 0.35, 0] - side * 0.3, p - fwd * 0.75 + [0, 0.05, 0] - side * 0.35, 0.1, 4))
    return toes, claws


def front_upper(s, lin):
    F, _ = legs(s)
    sh, el = np.array(F["shoulder"]), np.array(F["elbow"])
    skin = tube([sh + [0, 0.5, -0.2], (sh + el) / 2 + [0, 0, -0.35], el], [(0, 1.3), (0.5, 1.0), (1, 0.66)], 7)
    return {"skin": skin}


def front_lower(s, lin):
    F, _ = legs(s)
    el, wr, pw = (np.array(F[k]) for k in ("elbow", "wrist", "paw"))
    skin = tube([el, (el + wr) / 2 + [0, 0, 0.1], wr, pw], [(0, 0.66), (0.6, 0.5), (1, 0.42)], 6)
    toes, claws = paw(pw, (0, 0, -1), s, lin)
    spur = cone(el + [s * 0.1, 0.1, 0.3], el + [s * 0.25, 0.25, 1.05], 0.16, 4)   # éperon de coude
    return {"skin": cat([skin] + toes), "claw": cat(claws), "spike": spur}


def back_upper(s, lin):
    _, B = legs(s)
    hp, kn = np.array(B["hip"]), np.array(B["knee"])
    skin = tube([hp + [0, 0.4, 0.4], (hp + kn) / 2 + [0, 0, 0.35], kn], [(0, 1.7), (0.5, 1.3), (1, 0.72)], 7)
    return {"skin": skin}


def back_lower(s, lin):
    _, B = legs(s)
    kn, hk, pw = (np.array(B[k]) for k in ("knee", "hock", "paw"))
    skin = tube([kn, (kn + hk) / 2 + [0, 0, -0.15], hk, pw + [0, 0.25, 0.1], pw], [(0, 0.72), (0.45, 0.55), (0.7, 0.42), (1, 0.4)], 6)
    toes, claws = paw(pw, (0, 0, -1), s, lin)
    spur = cone(hk + [0, 0.1, 0.15], hk + [s * 0.1, 0.4, 0.95], 0.15, 4)          # ergot de jarret
    return {"skin": cat([skin] + toes), "claw": cat(claws), "spike": spur}


def scallop(a, b, depth, toward):
    """Bord de fuite entre deux pointes de doigt, creusé vers l'intérieur."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = (a + b) / 2
    return m + (np.asarray(toward, float) - m) * depth


EDGE = {"Feu": 0.16, "Glace": 0.12, "Foret": 0.1, "Ombre": 0.3}


def wing_parts(s, lin):
    W = wing(s)
    root, elbow, wrist, back = (np.array(W[k], float) for k in ("root", "elbow", "wrist", "back"))
    tips = [np.array(t, float) for t in W["tips"]]
    dep = EDGE[lin]
    upper = {"wingbone": tube([root, (root + elbow) / 2 + [0, 0.3, 0], elbow], [(0, 0.55), (1, 0.38)], 6)}
    lower = {"wingbone": [tube([elbow, (elbow + wrist) / 2 + [0, 0.25, 0], wrist], [(0, 0.38), (1, 0.28)], 6)],
             "membrane": [], "membrane2": [], "horn": [], "spike": [], "tip": []}
    for t in tips:
        mid = wrist + (t - wrist) * 0.5 + [0, 0.25, 0]
        lower["wingbone"].append(tube([wrist, mid, t], [(0, 0.2), (1, 0.05)], 5))
    lower["horn"].append(cone(wrist, wrist + [s * 0.2, 0.9, -0.7], 0.18, 5))         # griffe du pouce
    # panneaux entre doigts : intérieur (membrane) + bande de bord (membrane2)
    seq = tips + [back]
    for k in range(len(seq) - 1):
        a, b = seq[k], seq[k + 1]
        hub = wrist if k < len(seq) - 2 else None
        if hub is None:   # dernier panneau : du dernier doigt au flanc, accroché au bras
            sc = scallop(a, b, dep, elbow)
            inner = [elbow, wrist, a + (wrist - a) * 0.22, sc + (elbow - sc) * 0.22, b + (elbow - b) * 0.15, root]
            outer = [a + (wrist - a) * 0.22, a, sc, b, b + (elbow - b) * 0.15, sc + (elbow - sc) * 0.22]
            upper["membrane"] = slab([root, elbow, sc + (elbow - sc) * 0.22, b + (elbow - b) * 0.15], 0.07)
            upper["membrane2"] = slab([b + (elbow - b) * 0.15, sc + (elbow - sc) * 0.22, sc, b], 0.07)
            lower["membrane"].append(slab([elbow, wrist, a + (wrist - a) * 0.22, sc + (elbow - sc) * 0.22], 0.07))
            lower["membrane2"].append(slab([a + (wrist - a) * 0.22, a, sc, sc + (elbow - sc) * 0.22], 0.07))
        else:
            sc = scallop(a, b, dep, wrist)
            f = 0.3
            ia, isc, ib = a + (wrist - a) * f, sc + (wrist - sc) * f, b + (wrist - b) * f
            lower["membrane"].append(slab([wrist, ia, isc, ib], 0.07))
            lower["membrane2"].append(slab([ia, a, sc, isc], 0.07))
            lower["membrane2"].append(slab([isc, sc, b, ib], 0.07))
        # décor du bord de fuite par lignée
        for q in (0.3, 0.7):
            e0 = (a + (sc - a) * q * 2) if q < 0.5 else (sc + (b - sc) * (q - 0.5) * 2)
            out = e0 - (wrist if hub is not None else elbow); out /= np.linalg.norm(out)
            tgt = upper if hub is None and q > 0.5 else lower
            if lin == "Feu":
                tgt.setdefault("tip", [])
                if isinstance(tgt["tip"], list):
                    tgt["tip"] += T7.flame(e0 - out * 0.2 + [0, 0.2, 0], e0 - out * 0.2 - [0, 0.2, 0], e0 + out * 0.9)
            elif lin == "Glace":
                if isinstance(tgt.get("spike", []), list):
                    tgt.setdefault("spike", []).append(cone(e0, e0 + [0, -0.9, 0] + out * 0.2, 0.09, 5))
    if lin == "Foret":    # nervures de feuille sur la membrane
        for t in tips:
            for f0 in (0.35,):
                p0 = wrist + (t - wrist) * f0
                lower["tip"].append(tube([p0, p0 + (t - p0) * 0.3 + [0, -1.4, 0.9]], [(0, 0.06), (1, 0.02)], 4))
    for d in (upper, lower):
        for k, v in list(d.items()):
            d[k] = cat(v) if isinstance(v, list) else v
            if d[k] is None:
                del d[k]
    return upper, lower


# ---------- tête v7 placée au bout du cou ----------
def place(m, local=True, up=False):
    """up : membranes — les deux faces du panneau sont éclairées comme sa face du dessus (rendu double face)."""
    w = m.copy()
    if local:
        w.vertices = HB + HS * (w.vertices @ HEAD_R.T)
    w = trimesh.Trimesh(w.vertices, w.faces, process=False)
    fn = T7.flat_quads(w)
    if up:
        fn = np.where(fn[:, 1:2] < 0, -fn, fn)
    w.unmerge_vertices()
    w.vertex_normals = np.repeat(fn, 3, axis=0)
    return w


def body_slots(m, kind):
    c, n = m.triangles_center, m.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if kind == "leg":
            out.append("limb" if y < 3.0 else "skin")
            continue
        band = int(np.floor((z - 0.4 * y) / 0.75)) % 2
        if ny < -0.5:
            out.append("belly2" if band else "belly")
        elif ny > 0.72:
            out.append("marking" if (kind != "neck" and abs(x) < 0.7 and ((z / 1.3) % 1) < 0.22) else "back")
        else:
            out.append("skin")
    return out


def build(lin="Feu"):
    out = {}

    def add(name, parent, pivot, L, kind=None):
        L = {k: v for k, v in L.items() if v is not None}
        layers = {k: place(v, False, k.startswith("membrane")) for k, v in L.items()}
        slots = {}
        if kind and "skin" in layers:
            slots["skin"] = body_slots(L["skin"], kind)
        for k in ("membrane2", "wingbone", "tailblade", "belly", "limb", "marking"):
            if k in layers:               # couches sans nom de couche standard : couleur par face
                slots[k] = [k] * len(layers[k].faces)
        out[name] = {"parent": parent, "pivot": tuple(float(v) for v in pivot), "layers": layers, "slots": slots}

    add("Torso", None, (0, 7.0, 0), torso(lin), "body")
    add("Neck", "Torso", NECK[0], neck(lin), "neck")
    for name, fn, piv, which in (("Head", T7.head_layers, HB, "head"),
                                 ("Jaw", T7.jaw_layers, HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS, "jaw")):
        L = {k: trimesh.util.concatenate(v) for k, v in fn(lin).items() if v}
        out[name] = {"parent": "Neck" if name == "Head" else "Head", "pivot": tuple(float(v) for v in piv),
                     "layers": {k: place(m) for k, m in L.items()}, "slots": {"skin": T7.slots(L["skin"], which)}}
    for i in range(4):
        add(f"Tail{i + 1}", "Torso" if i == 0 else f"Tail{i}", TAIL[TAIL_CUT[i]], tail(i, lin), "body")
    for s, n in ((1, "R"), (-1, "L")):
        F, B = legs(s)
        W = wing(s)
        add("FrontUpperLeg" + n, "Torso", F["shoulder"], front_upper(s, lin), "leg")
        add("FrontLowerLeg" + n, "FrontUpperLeg" + n, F["elbow"], front_lower(s, lin), "leg")
        add("BackUpperLeg" + n, "Torso", B["hip"], back_upper(s, lin), "leg")
        add("BackLowerLeg" + n, "BackUpperLeg" + n, B["knee"], back_lower(s, lin), "leg")
        up, lo = wing_parts(s, lin)
        add("WingUpper" + n, "Torso", W["root"], up)
        add("WingLower" + n, "WingUpper" + n, W["elbow"], lo)
    return out


def tris(model):
    return sum(len(m.faces) for seg in model.values() for m in seg["layers"].values())


def gather(model, pal, black=False):
    if black:
        pal = {k: "#000000" for k in pal}
    return PC.gather(model, pal)


def silhouette(it, eye, target, size, fov):
    im = rendu.render(it, eye, target, size=size, fov=fov, bg=("#e8e4da", "#e8e4da"))
    a = np.asarray(im.convert("L"))
    return Image.fromarray(np.where(a < 200, 24, 232).astype(np.uint8)).convert("RGB")


C = np.array([0, 7.5, 5.0])
VUES = [("3/4 héros", C + [-28, 10, -30], C + [0, 1.0, -2.5], 38), ("Profil", C + [-56, 1.5, 2.5], C + [0, 0, 2.5], 34),
        ("Face", C + [0, 2.5, -46], C + [0, 1.5, 0], 33), ("3/4 arrière bas", C + [30, -2, 34], C + [0, 1.0, 2.0], 42)]


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else None
    cw, ch, lw = 470, 380, 170
    rows = len(LIGNEES) + 1
    W, H = lw + cw * len(VUES) + 10, 110 + ch * rows + 20
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — corps v4 en polygones", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Tête v7 ; cou en S, poitrail profond et taille fine, pattes arrière digitigrades, longue queue à lame, "
                      "grandes ailes ; palette de corps v7.", font=f(17), fill=(150, 160, 184))
    for i, lin in enumerate(LIGNEES):
        m = build(lin)
        it = gather(m, PC.palette(lin))
        y0 = 100 + i * ch
        dr.text((20, y0 + 20), NOMS[lin], font=f(24, True), fill=(230, 232, 240))
        dr.text((20, y0 + 56), f"{tris(m)} triangles", font=f(14), fill=(140, 150, 172))
        for j, (t, eye, tg, fov) in enumerate(VUES):
            board.paste(rendu.render(it, eye, tg, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        print(lin, tris(m), flush=True)
        if lin == "Feu":
            feu = m
    # dernière ligne : silhouettes v3 / v4 à la même échelle
    y0 = 100 + len(LIGNEES) * ch
    dr.text((20, y0 + 20), "Silhouettes", font=f(22, True), fill=(230, 232, 240))
    dr.text((20, y0 + 52), "v3 / v4, même échelle", font=f(14), fill=(140, 150, 172))
    eye, tg = C + [-56, 1.5, 2.5], C + [0, 0, 2.5]
    board.paste(silhouette(gather(feu, PC.palette("Feu"), True), eye, tg, (cw * 2 - 8, ch - 8), 34), (lw + cw * 2, y0))
    p = os.path.join(cache, "model_Feu.pkl") if cache else None
    if p and os.path.exists(p):
        v3 = PC.recolor(pickle.load(open(p, "rb")), "Feu")
        board.paste(silhouette(gather(v3, PC.palette("Feu"), True), eye, tg, (cw * 2 - 8, ch - 8), 34), (lw, y0))
        dr.text((lw + 12, y0 + 8), "v3", font=f(16, True), fill=(200, 60, 40))
    dr.text((lw + cw * 2 + 12, y0 + 8), "v4", font=f(16, True), fill=(200, 60, 40))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-dragon-v4.png"))


if __name__ == "__main__":
    main()
