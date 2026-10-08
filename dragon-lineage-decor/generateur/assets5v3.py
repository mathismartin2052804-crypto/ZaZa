# Série 5, v3 : dragon de cristal d'après la vidéo de l'ami de Will (avec son accord).
# Changements par rapport à la v2 (assets5.py, gardé tel quel) :
#   - corps plus haut et plus touffu : deux couches de lames (courtes plaquées dessous, longues dessus) ;
#   - lames couchées le long du corps, ondulées en S, légèrement tordues, section en triangle (moins de triangles) ;
#   - tête environ 1,5 fois plus grosse et plus expressive : museau long, grands crocs, gueule ouverte,
#     arcades en V (air méchant), gemme au front, joues hérissées, crinière rabattue, antennes courbées ;
#   - pattes longues en TROIS morceaux (cuisse, tibia, pied) pour que les pieds restent posés au sol
#     pendant la marche ; au repos, les griffes touchent le sol (Y = 0).
#
# Morceaux (le script d'animation s'en sert, ne pas les renommer) :
#   Head, Seg01..Seg30                 : la chaîne du corps (tête puis morceaux jusqu'à la queue) ;
#   <Chaîne>_Blades                    : les lames du morceau ;
#   Head_Jaw                           : mâchoire, crocs du bas et barbe (pivote à la charnière) ;
#   Head_Eyes                          : les yeux et la gemme du front (Neon) ;
#   SegXX_LegFL/FR/BL/BR               : la cuisse (pivote à la hanche) ;
#   SegXX_LegYY_Shin / SegXX_LegYY_Foot : le tibia (pivote au genou) et le pied (pivote à la cheville).
# Repère : Y vers le haut, tête vers -Z (l'avant de Roblox), 1 unité = 1 stud, sol à Y = 0.
# a.meta garde la pose de repos (colonne, charnière, hanche/genou/cheville/appui de chaque patte).
import math
import numpy as np
from meshlib import Asset, loft, ring, tube, blob, transform, rot_matrix_x
from assets5 import _oriented, frame, place, _section

N_SEG = 30
SPACING = 2.0
FRONT_LEG_SEG = 10
BACK_LEG_SEG = 25
HEAD_SCALE = 1.4
HEAD_PITCH = 0.2                        # museau relevé : la tête regarde devant, pas le sol
HEAD_WIDEN = np.diag([1.4, 1.2, 1.0])   # tête plus large et plus haute que longue : une vraie tête de dragon, pas de crocodile

STYLE = {
    "body": ("#24569F", "Glass"),
    "blades": ("#4E8FE6", "Glass"),
    "eyes": ("#C8ECFF", "Neon"),
}


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------- lames ----------------

def blade3(path, widths, thick, side_hints):
    """Lame plate à section en triangle (2 bords + une arête sur le dessus), terminée en pointe."""
    path = [np.asarray(p, float) for p in path]
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        if i == n - 1:
            rings.append(p[None, :])
            continue
        d = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        s = np.asarray(side_hints[i], float)
        s = s - (s @ d) * d
        s /= np.linalg.norm(s)
        nn = np.cross(d, s)
        w, t = widths[i], thick * widths[i] / max(widths) + 0.02
        rings.append(np.array([p + s * w, p + nn * t, p - s * w]))
    return _oriented(*loft(rings, cap_start=True, cap_end=False))


def flame(rng, root, radial, tang, back, ln, w, flare, hook=0.5, wave=1.0, twist=0.5, pts=6):
    """Lame couchée vers l'arrière, ondulée en S, qui se tord un peu et dont la pointe se relève."""
    path, sides = [], []
    phase = rng.uniform(0, 2 * math.pi)
    amp = 0.1 * wave * ln * rng.uniform(0.7, 1.3)
    tw = twist * rng.uniform(-1, 1)
    for k in range(pts):
        u = k / (pts - 1)
        out = flare * ln * (0.05 + 0.18 * u + 0.35 * hook * u ** 3)
        sway = amp * math.sin(2 * math.pi * u * 0.9 + phase) * u
        path.append(root + back * (u * ln) + radial * out + tang * sway)
        a = tw * u
        sides.append(tang * math.cos(a) + radial * math.sin(a))
    prof = [0.75, 1.0, 0.95, 0.75, 0.45, 0.2, 0.0] if pts == 7 else \
           [0.8, 1.0, 0.85, 0.55, 0.25, 0.0] if pts == 6 else [0.9, 1.0, 0.5, 0.0]
    return blade3(path, [w * f for f in prof], 0.1, sides)


def _dirs(a):
    return np.array([math.cos(a), math.sin(a), 0.0]), np.array([-math.sin(a), math.cos(a), 0.0])


# ---------------- la colonne au repos ----------------

def spine():
    """Points de repos : 0 = tête, 1..N = morceaux. Tête basse, cou qui monte, dos haut, queue qui retombe."""
    pts = []
    for i in range(N_SEG + 1):
        t = i / N_SEG
        y = 8.4 + 3.8 * _smooth(0.0, 0.34, t) - 3.0 * _smooth(0.62, 1.0, t) + 0.35 * math.sin(2 * math.pi * t * 1.4)
        pts.append(np.array([0.0, y, i * SPACING]))
    out = [pts[0]]
    for p in pts[1:]:
        d = p - out[-1]
        out.append(out[-1] + d / np.linalg.norm(d) * SPACING)
    return out


def radius(i):
    t = i / N_SEG
    if t < 0.14:
        return 1.9 + 0.6 * (t / 0.14)
    if t < 0.72:
        return 2.5
    return 2.5 - 1.25 * ((t - 0.72) / 0.28)


# ---------------- morceaux du corps ----------------

def body_segment(rng, i, pts):
    r = radius(i)
    rc = r * 0.84
    L = SPACING * 0.78
    rings = []
    for k, (z, s) in enumerate([(-L, 0.95), (0.0, 1.05), (L, 0.93)]):
        rr = ring((0, 0, z), rc * s, 8, angle0=0.4 * k + i * 0.3, axis_u=(1, 0, 0), axis_v=(0, 1, 0),
                  jitter=0.08, rng=rng)
        rr[:, 1] *= 1.22                       # corps plus haut que large
        rings.append(rr)
    core = _oriented(*loft(rings))

    t = i / N_SEG
    mane = math.exp(-((t - 0.06) / 0.09) ** 2)
    tuft = max(0.0, (t - 0.82) / 0.18)
    rs = 0.6 + 0.4 * r / 2.5
    back = np.array([0, 0, 1.0])
    blades = []
    # couche du dessous : lames courtes et larges, plaquées contre le corps (cachent le cœur foncé)
    st = 13 if i % 2 else 0
    for a0 in range(-40, 221, 37):
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (2.8 + 1.2 * top) * rs * rng.uniform(0.85, 1.2)
        root = radial * np.array([rc, rc * 1.22, 0]) * 0.92 + [0, 0, rng.uniform(-0.8, 0.2) * L]
        blades.append(flame(rng, root, radial, tang, back, ln, r * 0.7, 0.28, 0.2, 0.4, 0.3, pts=4))
    # couche du dessus : longues lames ondulées, couchées vers l'arrière, plus longues sur le dos
    st = 15 if i % 2 else 0
    for a0 in range(-35, 216, 28):
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (5.8 + 3.6 * top + 3.0 * mane + 3.5 * tuft) * rs * rng.uniform(0.75, 1.3)
        if rng.uniform() < 0.12:
            ln *= 1.35                          # de temps en temps une très longue mèche
        root = radial * np.array([rc, rc * 1.22, 0]) * 0.95 + [0, 0, rng.uniform(-0.9, 0.0) * L]
        w = r * (0.48 + 0.2 * top) * rng.uniform(0.85, 1.15)
        blades.append(flame(rng, root, radial, tang, back, ln, w, 0.42 + 0.2 * (1 - top) + 0.4 * tuft,
                            hook=0.3 + 0.4 * top, wave=1.0, twist=0.6))
    # deux petites lames sous le ventre
    for a0 in (250, 290):
        a = math.radians(a0 + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        blades.append(flame(rng, radial * rc * 1.1, radial, tang, back, 2.2 * rs, r * 0.25, 0.3, 0.3, pts=4))
    if i == N_SEG:                              # grosse touffe au bout de la queue
        for k in range(12):
            a = 2 * math.pi * k / 12 + rng.uniform(-0.2, 0.2)
            radial, tang = _dirs(a)
            blades.append(flame(rng, radial * rc * 0.5 + [0, 0, 0.5], radial, tang, back,
                                rng.uniform(5.0, 7.0), 0.5, 0.8, 0.9, wave=1.2))
    M, o = frame(pts, i), pts[i]
    return place(core, M, o), [place(b, M, o) for b in blades]


# ---------------- tête ----------------

JAW_HINGE = np.array([0, -0.45, 1.9])   # repère local de la tête
JAW_OPEN = 0.5                          # la gueule est modélisée ouverte (air menaçant)


def head(rng):
    """Tête en repère local (avant = -Z). Renvoie (crâne, lames, mâchoire, yeux)."""
    up = math.pi / 2
    brow = [(up - 0.75, 0.4, 0.3), (up + 0.75, 0.4, 0.3)]
    nose = [(up, 0.35, 0.45)]
    prof = [(2.2, 1.6, 1.9, -0.6, ()), (1.0, 1.85, 2.25, -0.55, brow), (-0.5, 1.55, 1.8, -0.4, brow),
            (-2.0, 1.15, 1.2, -0.3, ()), (-3.6, 0.98, 0.95, -0.25, ()), (-5.2, 0.88, 0.9, -0.2, ()),
            (-6.6, 0.78, 1.05, -0.15, nose), (-7.6, 0.5, 0.75, -0.1, ())]
    skull = [_oriented(*loft([_section(z, w, t, b, 8, bm) for z, w, t, b, bm in prof]))]

    bl = []
    back = np.array([0, 0, 1.0])
    # dents du haut : deux grands crocs par côté, le reste plus petit
    for side in (-1, 1):
        for k in range(9):
            z = -7.1 + k * 0.62
            x = side * (0.42 + 0.11 * k)
            big = {1: (1.6, 0.24), 4: (1.1, 0.19)}.get(k, (0.5, 0.11))
            bl.append(_oriented(*tube([[x, -0.05, z], [x * 1.03, -0.05 - big[0] * 0.6, z + 0.05],
                                       [x * 1.0, -0.05 - big[0], z + 0.2]], [big[1], big[1] * 0.6, 0], 3, tip=True)))
    # narines : deux petites bosses sur le nez
    for side in (-1, 1):
        bl.append(_oriented(*tube([[side * 0.35, 0.9, -7.0], [side * 0.5, 1.2, -6.5], [side * 0.55, 1.05, -6.0]],
                                  [0.18, 0.15, 0], 4, tip=True)))
    # crinière : lames couchées vers l'arrière et les côtés, autour de la nuque
    for k in range(26):
        a = math.radians(-60 + 300 * k / 25 + rng.uniform(-5, 5))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = rng.uniform(5.5, 8.0) * (0.7 + 0.3 * top)
        root = radial * np.array([1.4, 1.6, 0]) + [0, 0.6, rng.uniform(-1.0, 1.6)]
        bl.append(flame(rng, root, radial, tang, back, ln, rng.uniform(0.5, 0.75), 0.5 + 0.2 * (1 - top),
                        hook=0.6 + 0.4 * top, wave=1.1))
    # collerette : une couronne de grandes lames qui rayonnent autour de la nuque (silhouette de lion vue de face)
    for k in range(16):
        a = math.radians(-50 + 280 * k / 15 + rng.uniform(-4, 4))
        radial, tang = _dirs(a)
        bk = radial * 0.75 + np.array([0, 0, 0.66])
        root = radial * np.array([1.5, 1.7, 0]) + [0, 0.5, 1.4]
        bl.append(flame(rng, root, radial, tang, bk / np.linalg.norm(bk), rng.uniform(4.5, 6.5), 0.6, 0.35, 0.6, wave=0.9))
    for side in (-1, 1):
        # joues hérissées : un éventail de lames qui élargit la tête vue de face
        for k in range(5):
            a = math.radians(-35 + 18 * k)
            radial = np.array([side * math.cos(a), math.sin(a), 0.0])
            tang = np.array([-side * math.sin(a), math.cos(a), 0.0])
            bk = np.array([side * 0.55, 0, 0.84])
            root = np.array([side * 1.35, 0.1 + 0.25 * k, -0.6 + 0.35 * k])
            bl.append(flame(rng, root, radial, tang, bk, 3.6 + 0.5 * k + rng.uniform(0, 1), 0.45, 0.7, 0.8, wave=0.8))
        # arcades en V : épaisses, elles descendent vers le museau (regard méchant)
        bl.append(blade3([[side * 1.75, 2.0, 0.8], [side * 1.45, 2.05, -0.4], [side * 1.0, 1.8, -1.6],
                          [side * 0.55, 1.35, -2.6]], [0.55, 0.6, 0.45, 0.0], 0.35,
                         [[side, 0.3, 0]] * 4))
        # cornes d'arcade : partent au-dessus de l'œil et filent vers l'arrière
        bl.append(_oriented(*tube([[side * 1.3, 2.1, 0.0], [side * 1.9, 3.0, 1.3], [side * 2.3, 3.5, 3.0],
                                   [side * 2.4, 3.6, 4.6]], [0.38, 0.28, 0.16, 0], 5, tip=True)))
        # couronne : deux lames de chaque côté de la crête
        bl.append(blade3([[side * 0.7, 2.2, -0.6], [side * 1.0, 3.5, 0.0], [side * 1.25, 4.6, 0.9],
                          [side * 1.3, 5.3, 2.0]], [0.45, 0.4, 0.25, 0], 0.12, [[0, 0, 1]] * 4))
        # antennes : longues, elles montent en s'écartant et en se courbant vers l'arrière
        ant = [[side * 0.6, 2.1, -0.6], [side * 1.8, 3.8, 0.0], [side * 3.0, 5.6, 0.8], [side * 3.8, 7.6, 1.7],
               [side * 4.1, 9.6, 2.8], [side * 4.0, 11.3, 4.2]]
        bl.append(_oriented(*tube(ant, [0.2, 0.17, 0.14, 0.12, 0.09, 0], 4, tip=True)))
        # moustaches qui partent du museau et flottent vers l'arrière
        wh = [[side * 0.6, 0.3, -6.6], [side * 1.8, 0.0, -5.4], [side * 2.8, -0.5, -3.4], [side * 3.4, -0.9, -0.8],
              [side * 3.6, -0.8, 2.2], [side * 3.4, -0.4, 4.6]]
        bl.append(_oriented(*tube(wh, [0.15, 0.13, 0.11, 0.09, 0.06, 0], 4, tip=True)))
    # crête centrale : une grande lame dressée au milieu du front
    bl.append(blade3([[0, 2.0, -1.0], [0, 3.6, -0.3], [0, 5.2, 0.7], [0, 6.4, 2.2]], [0.75, 0.6, 0.35, 0],
                     0.18, [[0, 0, 1]] * 4))

    # mâchoire ouverte : crocs du bas, pointes au menton et barbe qui pend vers l'arrière
    jprof = [(1.9, 1.25, -0.45, -1.15), (0.3, 1.3, -0.4, -1.3), (-1.8, 1.0, -0.35, -1.1),
             (-3.8, 0.78, -0.3, -0.9), (-5.6, 0.6, -0.25, -0.7), (-6.9, 0.42, -0.2, -0.55)]
    jaw = [_oriented(*loft([_section(z, w, t, b, 8) for z, w, t, b in jprof]))]
    for side in (-1, 1):
        for k in range(8):
            z = -6.5 + k * 0.7
            x = side * (0.3 + 0.11 * k)
            big = {0: (1.3, 0.2), 3: (0.9, 0.16)}.get(k, (0.45, 0.1))
            jaw.append(_oriented(*tube([[x, -0.3, z], [x, -0.3 + big[0], z - 0.1]], [big[1], 0], 3, tip=True)))
        for k in range(3):                                    # pointes sur le côté de la mâchoire
            jaw.append(_oriented(*tube([[side * 1.0, -0.9, -1.5 + 1.2 * k], [side * 1.9, -1.3, -0.6 + 1.2 * k]],
                                       [0.2, 0], 3, tip=True)))
    for k in range(7):
        a = math.radians(200 + 140 * k / 6)
        radial, tang = _dirs(a)
        root = radial * 0.85 + [0, -0.9, -4.0 + 0.6 * abs(k - 3)]
        jaw.append(flame(rng, root, radial, tang, np.array([0, -0.4, 1.0]) / 1.08, rng.uniform(4.0, 5.8),
                         0.36, 0.55, 0.8, wave=1.0))
    jaw = [(transform(np.array(v) - JAW_HINGE, rot_matrix_x(-JAW_OPEN), JAW_HINGE), f) for v, f in jaw]

    eyes = []
    for side in (-1, 1):
        v, f = blob([side * 1.28, 1.3, -1.1], 0.42, scale=(0.5, 0.36, 1.35), jitter=0.0, subdiv=0)
        eyes.append(_oriented(v, f))
    v, f = blob([0, 2.15, -1.7], 0.42, scale=(0.8, 1.0, 1.2), jitter=0.0, subdiv=0)   # gemme du front
    eyes.append(_oriented(v, f))
    return skull, bl, jaw, eyes


# ---------------- pattes (cuisse, tibia, pied) ----------------

def ik_knee(hip, ankle, l1, l2, bend):
    """Position du genou pour une patte à deux os (hanche -> genou -> cheville), plié du côté de `bend`."""
    d = ankle - hip
    D = min(max(np.linalg.norm(d), abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    dn = d / np.linalg.norm(d)
    a = (l1 * l1 + D * D - l2 * l2) / (2 * D)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    b = bend - (bend @ dn) * dn
    return hip + dn * a + b / np.linalg.norm(b) * h


ANKLE_H = 1.1      # hauteur de la cheville au-dessus du sol


def leg_pose(pts, seg, side, front):
    """Pose de repos d'une patte (repère monde) : hanche, genou, cheville, point d'appui au sol."""
    M, o = frame(pts, seg), pts[seg]
    r = radius(seg)
    hip = M @ np.array([side * r * 0.62, -r * 0.5, 0.0]) + o
    contact = np.array([hip[0] + side * 0.9, 0.0, hip[2] - (0.6 if front else -0.2)])
    ankle = contact + [0, ANKLE_H, 0.45]
    l1, l2 = (5.6, 5.4) if front else (4.9, 4.7)
    bend = np.array([0, 0, 1.0]) if front else np.array([0, 0, -1.0])   # coude vers l'arrière, genou vers l'avant
    knee = ik_knee(hip, ankle, l1, l2, bend)
    return dict(hip=hip, knee=knee, ankle=ankle, contact=contact, l1=l1, l2=l2, bend=bend)


def leg_parts(rng, P, side, front):
    """Renvoie (cuisse, tibia, pied), chacun une liste de (v, f) en repère monde."""
    hip, knee, ankle, contact = P["hip"], P["knee"], P["ankle"], P["contact"]
    k = 1.3 if front else 1.4
    thigh = [_oriented(*tube([hip, (hip + knee) / 2, knee], [1.3 * k, 1.0 * k, 0.75 * k], 6, jitter=0.1, rng=rng))]
    shin = [_oriented(*tube([knee, (knee + ankle) / 2, ankle], [0.75 * k, 0.6 * k, 0.48 * k], 6, jitter=0.1, rng=rng))]
    # lames : épaule/cuisse et coude/genou, couchées vers l'arrière
    for lst, root, ln in ((thigh, hip + [0, -0.4, 0], 3.2), (thigh, (hip + knee) / 2, 2.4), (shin, knee, 2.4)):
        a = math.radians(90 - side * 60)
        radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
        lst.append(flame(rng, root, radial, tang, np.array([0, 0.25, 1.0]) / 1.03, ln, 0.4, 0.5, 0.7, pts=4))
    # pied : articulation, trois longs doigts griffus vers l'avant et un ergot vers l'arrière
    foot = [_oriented(*blob(ankle, 0.55, scale=(1.0, 0.8, 1.2), jitter=0.05, rng=rng, subdiv=0))]
    for t in range(4):
        if t < 3:
            a = math.radians(-28 + 28 * t)
            d = np.array([math.sin(a) * side if t != 1 else 0.0, 0, -math.cos(a)])
            toe_end = contact + d * 1.7 + [0, 0.35, 0]
            tip = toe_end + d * 1.1 + [0, -0.35, 0]
            foot.append(_oriented(*tube([ankle, (ankle + toe_end) / 2 + [0, 0.05, 0], toe_end],
                                        [0.3, 0.24, 0.18], 4)))
            foot.append(_oriented(*tube([toe_end, toe_end + d * 0.6 + [0, 0.05, 0], tip], [0.2, 0.14, 0], 4, tip=True)))
        else:
            d = np.array([0, 0, 1.0])
            foot.append(_oriented(*tube([ankle, ankle + d * 0.7 + [0, -0.5, 0], contact + d * 1.3],
                                        [0.22, 0.14, 0], 4, tip=True)))
    return thigh, shin, foot


# ---------------- assemblage ----------------

def dragon_cristal_v3(name="Dragon_Cristal_v3", seed=57):
    rng = np.random.default_rng(seed)
    pts = spine()
    a = Asset(name)
    col_b, mat_b = STYLE["body"]
    col_l, mat_l = STYLE["blades"]
    col_e, mat_e = STYLE["eyes"]
    meta = {"chain": [p.tolist() for p in pts], "legs": {}, "ground": 0.0}

    # la tête : en avant du point 0 ; l'arrière du crâne chevauche le premier morceau
    Mh, oh = frame(pts, 0) @ rot_matrix_x(HEAD_PITCH) @ HEAD_WIDEN * HEAD_SCALE, pts[0] + np.array([0, 0.6, -3.6])
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

    for seg, front, tag in ((FRONT_LEG_SEG, True, "F"), (BACK_LEG_SEG, False, "B")):
        for side, sname in ((-1, "L"), (1, "R")):
            P = leg_pose(pts, seg, side, front)
            nm = f"Seg{seg:02d}_Leg{tag}{sname}"
            thigh, shin, foot = leg_parts(rng, P, side, front)
            for suffix, lst in (("", thigh), ("_Shin", shin), ("_Foot", foot)):
                for v, f in lst:
                    a.add(nm + suffix, v, f, col_b, mat_b)
            meta["legs"][nm] = {"seg": seg, "front": front, "side": side,
                                **{k: (P[k].tolist() if isinstance(P[k], np.ndarray) else P[k])
                                   for k in ("hip", "knee", "ankle", "contact", "l1", "l2", "bend")}}
    a.meta = meta
    return a


def all_assets():
    return [dragon_cristal_v3()]
