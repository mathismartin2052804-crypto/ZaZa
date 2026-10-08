# Série 5 : dragon de cristal v2 (dragon oriental long, corps épais couvert de lames de glace courbes).
# Reproduit le dragon de l'ami de Will (avec son accord) d'après son image et sa vidéo.
#
# Le dragon est découpé en morceaux pour être animé par script (pas de squelette) :
#   Head, Seg01..Seg30   : la chaîne qui ondule (la tête puis le corps jusqu'à la queue) ;
#   <Chaîne>_Blades      : les lames de cristal du morceau (couleur plus claire) ;
#   Head_Jaw             : la mâchoire et la barbe (s'ouvre par script) ;
#   Head_Eyes            : les yeux (Neon) ;
#   SegXX_LegFL/FR/BL/BR : les pattes (bougent par script autour de la hanche).
# Repère : Y vers le haut, tête vers -Z (l'avant de Roblox), 1 unité = 1 stud.
# a.meta garde les pivots (colonne, hanches, charnière de la mâchoire) pour l'animation.
import math
import numpy as np
import trimesh
from meshlib import Asset, loft, ring, tube, blob, transform, rot_matrix_x

N_SEG = 30          # morceaux de corps
SPACING = 2.0       # distance entre deux morceaux (studs)
FRONT_LEG_SEG = 10
BACK_LEG_SEG = 25
HEAD_SCALE = 1.3

STYLE = {
    "body": ("#24569F", "Glass"),
    "blades": ("#4E8FE6", "Glass"),
    "eyes": ("#C8ECFF", "Neon"),
}


def _oriented(v, f):
    """Retourne les faces si le volume est négatif (normales vers l'extérieur)."""
    m = trimesh.Trimesh(np.array(v), np.array(f), process=False)
    if m.volume < 0:
        f = [(a, c, b) for a, b, c in f]
    return v, f


def blade(path, widths, thick, side_hint):
    """Lame plate de cristal (section en losange) le long d'une ligne, terminée en pointe."""
    path = [np.asarray(p, float) for p in path]
    side_hint = np.asarray(side_hint, float)
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        if i == n - 1:
            rings.append(p[None, :])
            continue
        d = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        s = side_hint - (side_hint @ d) * d
        s /= np.linalg.norm(s)
        nn = np.cross(d, s)
        w, t = widths[i], thick * widths[i] / max(widths)
        rings.append(np.array([p + s * w, p + nn * t, p - s * w, p - nn * t]))
    return _oriented(*loft(rings, cap_start=True, cap_end=False))


def sabre(rng, root, radial, tang, back, ln, w, flare, hook=1.0):
    """Lame courbe couchée vers l'arrière dont la pointe se relève (comme une flamme)."""
    pts = []
    for u, out in [(0.0, 0.0), (0.28, 0.08), (0.55, 0.17), (0.8, 0.3), (1.0, 0.3 + 0.35 * hook)]:
        sway = tang * rng.uniform(-0.18, 0.18) * ln * u * u
        pts.append(root + back * (u * ln) + radial * (out * ln * flare) + sway)
    return blade(pts, [w * 0.8, w, w * 0.85, w * 0.45, 0], 0.09, tang)


# ---------------- la colonne au repos ----------------

def spine():
    """Points de repos : 0 = tête, 1..N = morceaux du corps. Ondulation douce, comme sur la vidéo."""
    pts = []
    for i in range(N_SEG + 1):
        t = i / N_SEG
        z = i * SPACING
        y = 10.0 - 2.2 * math.exp(-(t / 0.14) ** 2) + 1.3 * math.sin(2 * math.pi * (t * 1.05 - 0.05))
        pts.append(np.array([0.0, y, z]))
    out = [pts[0]]
    for p in pts[1:]:
        d = p - out[-1]
        out.append(out[-1] + d / np.linalg.norm(d) * SPACING)
    return out


def frame(pts, i):
    """Repère de repos (droite, haut, arrière) du morceau i : l'avant regarde le morceau précédent."""
    fwd = (pts[0] - pts[1]) if i == 0 else (pts[i - 1] - pts[i])
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.stack([right, up, -fwd], 1)


def radius(i):
    t = i / N_SEG
    if t < 0.15:
        return 1.55 + 0.6 * (t / 0.15)
    if t < 0.75:
        return 2.15
    return 2.15 - 0.85 * ((t - 0.75) / 0.25)


def place(vf, M, o):
    v, f = vf
    return transform(v, M, o), f


# ---------------- morceaux du corps ----------------

def body_segment(rng, i, pts):
    r = radius(i)
    rc = r * 0.82                      # le cœur, presque caché par les lames
    L = SPACING * 0.75
    rings = []
    for k, (z, s) in enumerate([(-L, 0.95), (0.0, 1.05), (L, 0.92)]):
        rr = ring((0, 0, z), rc * s, 7, angle0=0.45 * k + i * 0.3, axis_u=(1, 0, 0), axis_v=(0, 1, 0),
                  jitter=0.08, rng=rng)
        rr[:, 1] *= 1.1
        rings.append(rr)
    core = _oriented(*loft(rings))

    t = i / N_SEG
    mane = math.exp(-((t - 0.08) / 0.1) ** 2)
    tuft = max(0.0, (t - 0.85) / 0.15)
    blades = []
    back = np.array([0, 0, 1.0])
    stagger = 9 if i % 2 else 0
    for a0 in range(-30, 211, 27):                       # 9 lames tout autour (sauf sous le ventre)
        a = math.radians(a0 + stagger + rng.uniform(-7, 7))
        radial = np.array([math.cos(a), math.sin(a), 0.0])
        tang = np.array([-math.sin(a), math.cos(a), 0.0])
        top = max(0.0, math.sin(a))
        ln = (5.4 + 3.2 * top + 3.0 * mane + 3.0 * tuft) * (0.6 + 0.4 * r / 2.15) * rng.uniform(0.85, 1.15)
        z0 = rng.uniform(-0.9, 0.0) * L
        root = radial * rc * 0.9 + [0, 0, z0]
        w = r * (0.62 + 0.2 * top) * rng.uniform(0.85, 1.15)
        blades.append(sabre(rng, root, radial, tang, back, ln, w, 0.5 + 0.5 * tuft, hook=0.35 + 0.5 * top))
    # deux petites lames sous le ventre
    for a0 in (250, 290):
        a = math.radians(a0 + rng.uniform(-8, 8))
        radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
        blades.append(sabre(rng, radial * rc * 0.9, radial, tang, back, 2.2 * r / 2.15, r * 0.25, 0.4, 0.4))
    if i == N_SEG:                                       # touffe au bout de la queue
        for k in range(12):
            a = 2 * math.pi * k / 12 + rng.uniform(-0.2, 0.2)
            radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
            blades.append(sabre(rng, radial * rc * 0.5 + [0, 0, 0.5], radial, tang, back,
                                rng.uniform(4.0, 5.5), 0.4, 0.9, 1.2))
    M, o = frame(pts, i), pts[i]
    return place(core, M, o), [place(b, M, o) for b in blades]


# ---------------- tête ----------------

def _section(z, w, top, bot, sides=8, bumps=()):
    pts = []
    yc, h = (top + bot) / 2, (top - bot) / 2
    for k in range(sides):
        a = 2 * math.pi * k / sides + math.pi / sides
        c, s = math.cos(a), math.sin(a)
        m = 1.0
        for ang, amp, wid in bumps:
            d = math.atan2(math.sin(a - ang), math.cos(a - ang))
            m += amp * math.exp(-(d / wid) ** 2)
        pts.append([w * m * c, yc + h * m * s, z])
    return np.array(pts)


JAW_HINGE = np.array([0, -0.4, 1.7])    # repère local de la tête
JAW_OPEN = 0.38


def head(rng):
    """Tête en repère local (avant = -Z). Renvoie (crâne, lames, mâchoire, yeux)."""
    up = math.pi / 2
    brow = [(up - 0.8, 0.35, 0.3), (up + 0.8, 0.35, 0.3)]
    prof = [(2.0, 1.5, 1.8, -0.6, ()), (0.8, 1.65, 2.05, -0.5, brow), (-0.6, 1.25, 1.55, -0.3, brow),
            (-2.0, 0.95, 1.05, -0.2, ()), (-3.4, 0.8, 0.85, -0.15, ((up, 0.2, 0.4),)),
            (-4.6, 0.62, 0.95, -0.1, ((up, 0.4, 0.5),)), (-5.3, 0.4, 0.55, -0.05, ())]
    skull = [_oriented(*loft([_section(z, w, t, b, 8, bm) for z, w, t, b, bm in prof]))]

    bl = []
    back = np.array([0, 0, 1.0])
    # dents du haut (crocs plus grands devant)
    for side in (-1, 1):
        for k in range(7):
            z = -5.0 + k * 0.62
            x = side * (0.42 + 0.13 * k)
            ln = 0.95 if k == 1 else 0.55
            bl.append(_oriented(*tube([[x, -0.05, z], [x * 1.02, -0.05 - ln, z + 0.1]],
                                      [0.15 if k == 1 else 0.11, 0], 3, tip=True)))
    # crinière : beaucoup de lames courbes qui partent de l'arrière du crâne
    for k in range(24):
        a = math.radians(-50 + 280 * k / 23 + rng.uniform(-5, 5))
        radial = np.array([math.cos(a), math.sin(a), 0.0])
        tang = np.array([-math.sin(a), math.cos(a), 0.0])
        top = max(0.0, math.sin(a))
        ln = rng.uniform(5.0, 7.5) * (0.65 + 0.35 * top)
        root = radial * np.array([1.3, 1.5, 0]) + [0, 0.7, rng.uniform(-1.2, 1.4)]
        bl.append(sabre(rng, root, radial, tang, back, ln, rng.uniform(0.5, 0.75), 0.65, 0.8 + 0.5 * top))
    for side in (-1, 1):
        # lames de joue, couchées vers l'arrière
        for k in range(3):
            a = math.radians(90 - side * (70 + 25 * k))
            radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
            bl.append(sabre(rng, radial * 1.1 + [0, 0.3, -1.4 + 0.5 * k], radial, tang, back, 4.0 + k, 0.35, 0.6, 1.0))
        # arcades : petite corne recourbée au-dessus de l'œil
        bl.append(_oriented(*tube([[side * 0.9, 1.8, -0.4], [side * 1.4, 2.6, 0.6], [side * 1.7, 3.0, 1.9]],
                                  [0.28, 0.18, 0], 5, tip=True)))
        # antennes : très longues, montent en s'écartant puis repartent vers le haut (vue de face)
        ant = [[side * 0.7, 2.0, -1.0], [side * 2.2, 4.2, -0.2], [side * 4.0, 6.4, 0.6], [side * 5.6, 8.0, 1.2],
               [side * 5.9, 10.5, 1.8], [side * 5.7, 13.5, 2.4]]
        bl.append(_oriented(*tube(ant, [0.2, 0.17, 0.14, 0.12, 0.09, 0], 4, tip=True)))
        # moustaches qui partent du museau vers l'arrière
        wh = [[side * 0.6, 0.3, -4.6], [side * 1.7, 0.1, -3.6], [side * 2.6, -0.3, -2.0], [side * 3.2, -0.5, 0.0],
              [side * 3.4, -0.4, 2.0]]
        bl.append(_oriented(*tube(wh, [0.14, 0.12, 0.1, 0.07, 0], 4, tip=True)))
    # crête centrale : une grande lame dressée au milieu du front
    bl.append(blade([[0, 1.9, -1.2], [0, 3.4, -0.4], [0, 4.8, 0.6], [0, 5.8, 1.9]], [0.6, 0.5, 0.3, 0], 0.15, [0, 0, 1]))

    # mâchoire entrouverte + barbe (lames qui pendent vers l'arrière)
    jprof = [(1.7, 1.2, -0.4, -1.1), (0.2, 1.2, -0.35, -1.2), (-1.6, 0.9, -0.3, -1.0),
             (-3.4, 0.68, -0.25, -0.8), (-4.8, 0.45, -0.2, -0.6)]
    jaw = [_oriented(*loft([_section(z, w, t, b, 8) for z, w, t, b in jprof]))]
    for side in (-1, 1):
        for k in range(6):
            z = -4.6 + k * 0.65
            x = side * (0.33 + 0.12 * k)
            ln = 0.8 if k == 0 else 0.45
            jaw.append(_oriented(*tube([[x, -0.25, z], [x, -0.25 + ln, z - 0.05]], [0.13 if k == 0 else 0.1, 0], 3,
                                       tip=True)))
    for k in range(7):
        a = math.radians(200 + 140 * k / 6)              # dessous de la mâchoire
        radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
        root = radial * 0.8 + [0, -0.8, -2.8 + 0.5 * abs(k - 3)]
        jaw.append(sabre(rng, root, radial, tang, np.array([0, -0.35, 1.0]) / 1.06, rng.uniform(3.5, 5.0),
                         0.32, 0.6, 0.9))
    jaw = [(transform(np.array(v) - JAW_HINGE, rot_matrix_x(-JAW_OPEN), JAW_HINGE), f) for v, f in jaw]

    eyes = []
    for side in (-1, 1):
        v, f = blob([side * 1.12, 1.1, -0.9], 0.3, scale=(0.7, 0.55, 1.3), jitter=0.0, subdiv=0)
        eyes.append(_oriented(v, f))
    return skull, bl, jaw, eyes


# ---------------- pattes ----------------

def leg(rng, side, back):
    """Patte en repère local de son morceau, hanche à l'origine. Renvoie une liste de (v, f)."""
    if not back:   # patte avant : pend sous l'épaule, longues griffes
        j = [np.array([0, 0, 0]), np.array([side * 0.6, -3.0, 0.6]), np.array([side * 0.4, -6.0, -0.3]),
             np.array([side * 0.4, -7.2, -1.0])]
        rad = [1.1, 0.75, 0.55, 0.55]
    else:          # patte arrière : accroupie comme un lézard, pied à plat
        j = [np.array([0, 0, 0]), np.array([side * 0.7, -2.4, -2.0]), np.array([side * 0.5, -5.0, 0.4]),
             np.array([side * 0.5, -6.4, -0.8])]
        rad = [1.2, 0.8, 0.55, 0.55]
    out = []
    for a, b, ra, rb in zip(j[:-1], j[1:], rad[:-1], rad[1:]):
        out.append(_oriented(*tube([a, (a + b) / 2, b], [ra, (ra + rb) / 2 * 1.05, rb], 6, jitter=0.12, rng=rng)))
    # lames au coude/genou et sur l'épaule
    for jj, ln in ((j[1], 2.2), (j[0] + [0, -0.6, 0], 2.6)):
        a = math.radians(90 - side * 60)
        radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
        out.append(sabre(rng, jj, radial, tang, np.array([0, 0.2, 1.0]) / 1.02, ln, 0.3, 0.6, 1.0))
    foot = j[3]
    for k in range(4):
        a = math.radians(-35 + 35 * k) if k < 3 else math.radians(180)
        d = np.array([math.sin(a) * 0.6, 0, -math.cos(a)])
        ln = 1.5 if k < 3 else 0.8
        c0 = foot + d * 0.3
        out.append(_oriented(*tube([c0, c0 + d * ln * 0.55 + [0, -0.15, 0], c0 + d * ln + [0, -0.75, 0]],
                                   [0.26, 0.18, 0], 4, tip=True)))
    return out


# ---------------- assemblage ----------------

def dragon_cristal(name="Dragon_Cristal", seed=55):
    rng = np.random.default_rng(seed)
    pts = spine()
    a = Asset(name)
    col_b, mat_b = STYLE["body"]
    col_l, mat_l = STYLE["blades"]
    col_e, mat_e = STYLE["eyes"]
    meta = {"chain": [p.tolist() for p in pts], "legs": {}}

    # la tête : un peu en avant du point 0 de la colonne
    Mh, oh = frame(pts, 0) * HEAD_SCALE, pts[0] + np.array([0, -0.3, -3.0])
    skull, blades, jaw, eyes = head(rng)
    for nm, lst, c, m in (("Head", skull, col_b, mat_b), ("Head_Blades", blades, col_l, mat_l),
                          ("Head_Jaw", jaw, col_l, mat_l), ("Head_Eyes", eyes, col_e, mat_e)):
        for vf in lst:
            a.add(nm, *place(vf, Mh, oh), c, m)
    meta["jaw_hinge"] = (Mh @ JAW_HINGE + oh).tolist()

    for i in range(1, N_SEG + 1):
        core, bl = body_segment(rng, i, pts)
        nm = f"Seg{i:02d}"
        a.add(nm, *core, col_b, mat_b)
        for v, f in bl:
            a.add(nm + "_Blades", v, f, col_l, mat_l)

    for seg, back, tag in ((FRONT_LEG_SEG, False, "F"), (BACK_LEG_SEG, True, "B")):
        M, o = frame(pts, seg), pts[seg]
        r = radius(seg)
        for side, sname in ((-1, "L"), (1, "R")):
            hip = np.array([side * r * 0.6, -r * 0.45, 0.0])
            nm = f"Seg{seg:02d}_Leg{tag}{sname}"
            for v, f in leg(rng, side, back):
                a.add(nm, *place((np.array(v) + hip, f), M, o), col_b, mat_b)
            meta["legs"][nm] = {"seg": seg, "hip": (M @ hip + o).tolist()}
    a.meta = meta
    return a


def all_assets():
    return [dragon_cristal()]
