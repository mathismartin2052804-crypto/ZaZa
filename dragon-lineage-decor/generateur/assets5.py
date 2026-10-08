# Série 5 : dragon de cristal (dragon oriental long, corps couvert de lames de glace).
# Inspiré de l'image envoyée par Will (dragon bleu translucide aux lames effilées) ; modèle original.
#
# Le dragon est découpé en morceaux pour être animé par script (pas de squelette) :
#   Head, Seg01..Seg30   : la chaîne qui ondule (la tête puis le corps jusqu'à la queue) ;
#   <Chaîne>_Blades      : les lames de cristal du morceau (couleur plus claire) ;
#   Head_Jaw             : la mâchoire (s'ouvre par script) ;
#   Head_Eyes            : les yeux (Neon) ;
#   SegXX_LegFL/FR/BL/BR : les pattes (battent par script autour de la hanche).
# Le script DragonCristal.client.lua retrouve tout ça grâce aux noms.
# Repère : Y vers le haut, tête vers -Z (l'avant de Roblox), 1 unité = 1 stud.
import math
import numpy as np
import trimesh
from meshlib import Asset, loft, ring, tube, blob, transform, rot_matrix_x

N_SEG = 30          # morceaux de corps
SPACING = 1.9       # distance entre deux morceaux (studs)
FRONT_LEG_SEG = 6
BACK_LEG_SEG = 21
HEAD_SCALE = 1.35

STYLE = {
    "body": ("#2C63B8", "Glass"),
    "blades": ("#6FA8F0", "Glass"),
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


# ---------------- la colonne au repos ----------------

def spine():
    """Points de repos : 0 = tête, 1..N = morceaux du corps. Légère courbe en S, comme sur l'image."""
    pts = []
    for i in range(N_SEG + 1):
        t = i / N_SEG
        z = i * SPACING
        # tête basse, cou qui remonte, bosse aux épaules, dos qui redescend, queue un peu relevée
        y = 6.0 + 5.0 * math.exp(-((t - 0.24) / 0.2) ** 2) + 1.2 * math.exp(-((t - 1.0) / 0.15) ** 2)
        pts.append(np.array([0.0, y, z]))
    # recale à SPACING exact le long de la courbe
    out = [pts[0]]
    for p in pts[1:]:
        d = p - out[-1]
        out.append(out[-1] + d / np.linalg.norm(d) * SPACING)
    return out


def frame(pts, i):
    """Repère de repos (droite, haut, avant) du morceau i : l'avant regarde le morceau précédent."""
    if i == 0:
        fwd = pts[0] - pts[1]
    else:
        fwd = pts[i - 1] - pts[i]
    fwd = fwd / np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    # matrice qui envoie le repère local (x droite, y haut, z arrière) vers le monde
    return np.stack([right, up, -fwd], 1)


def radius(i):
    t = i / N_SEG
    if t < 0.2:
        return 1.05 + 0.65 * (t / 0.2)
    if t < 0.5:
        return 1.7
    return 1.7 - 1.4 * ((t - 0.5) / 0.5) ** 1.15


def place(vf, M, o):
    v, f = vf
    return transform(v, M, o), f


# ---------------- morceaux du corps ----------------

def body_segment(rng, i, pts):
    r = radius(i)
    L = SPACING * 0.7
    rings = []
    for k, (z, s) in enumerate([(-L, 0.93), (0.0, 1.05), (L, 0.9)]):
        rr = ring((0, 0, z), r * s, 7, angle0=0.45 * k + i * 0.3, axis_u=(1, 0, 0), axis_v=(0, 1, 0),
                  jitter=0.08, rng=rng)
        rr[:, 1] *= 1.12          # un peu plus haut que large
        rings.append(rr)
    core = _oriented(*loft(rings))

    t = i / N_SEG
    blades = []
    # longueur des lames : très longues aux épaules (crinière), plus courtes au milieu, touffe au bout
    mane = math.exp(-((t - 0.12) / 0.14) ** 2)
    tuft = max(0.0, (t - 0.8) / 0.2)
    base_len = SPACING * (1.9 + 2.6 * mane + 0.8 * tuft) * (0.55 + 0.45 * r / 1.7)
    angles = [90, 90 - 38, 90 + 38, 90 - 78, 90 + 78, -10, 190]
    if tuft > 0.3:
        angles += [90 - 18, 90 + 18, 30, 150, -40, 220]
    for a in angles:
        a = math.radians(a + rng.uniform(-9, 9))
        radial = np.array([math.cos(a), math.sin(a), 0.0])
        tang = np.array([-math.sin(a), math.cos(a), 0.0])
        top = max(0.0, math.sin(a))                     # les lames du dos sont plus grandes
        ln = base_len * (0.45 + 0.65 * top) * rng.uniform(0.85, 1.15)
        flare = 0.16 + 0.4 * tuft + 0.12 * mane
        z0 = rng.uniform(-0.5, 0.1) * L
        p0 = radial * r * 0.85 + [0, 0, z0]
        p1 = radial * (r * 0.98 + ln * flare * 0.4) + [0, ln * 0.05 * top, z0 + ln * 0.4]
        p2 = radial * (r * 1.0 + ln * flare * 0.9) + [0, ln * 0.13 * top, z0 + ln * 0.72]
        p3 = radial * (r * 1.0 + ln * flare * 1.6) + [0, ln * 0.3 * top, z0 + ln]
        w = r * 0.42 * (0.7 + 0.3 * top)
        blades.append(blade([p0, p1, p2, p3], [w, w * 0.85, w * 0.5, 0], 0.12, tang))
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


def head(rng, pts):
    """Renvoie (crâne, lames, mâchoire, yeux), chacun liste de (v, f) déjà placés au repos."""
    up = math.pi / 2
    brow = [(up - 0.8, 0.35, 0.3), (up + 0.8, 0.35, 0.3)]
    # la tête regarde vers -Z en local (z négatif = avant)
    prof = [(1.6, 1.25, 1.45, -0.45, ()), (0.6, 1.4, 1.65, -0.4, brow), (-0.5, 1.05, 1.25, -0.25, brow),
            (-1.7, 0.8, 0.85, -0.15, ()), (-2.8, 0.68, 0.7, -0.12, ((up, 0.2, 0.4),)),
            (-3.7, 0.55, 0.75, -0.1, ((up, 0.35, 0.5),)), (-4.2, 0.35, 0.45, -0.05, ())]
    skull = [_oriented(*loft([_section(z, w, t, b, 8, bm) for z, w, t, b, bm in prof]))]

    blades = []
    # dents du haut
    for side in (-1, 1):
        for k in range(6):
            z = -3.9 + k * 0.62
            x = side * (0.42 + 0.11 * k)
            tooth = [[x, -0.05, z], [x * 1.02, -0.55 + 0.04 * k, z + 0.08]]
            blades.append(_oriented(*tube(tooth, [0.12, 0], 3, tip=True)))
    # crinière : longues lames qui partent de l'arrière du crâne vers l'arrière et le haut
    for k in range(16):
        a = math.radians(-35 + 250 * k / 15 + rng.uniform(-6, 6))
        radial = np.array([math.cos(a), math.sin(a) * 1.1, 0.0])
        tang = np.array([-math.sin(a), math.cos(a), 0.0])
        top = 0.5 + 0.5 * max(0.0, math.sin(a))
        ln = rng.uniform(4.5, 6.5) * top + 1.2
        z0 = rng.uniform(-0.6, 1.2)
        p0 = radial * 1.0 + [0, 0.5, z0]
        p1 = radial * (1.4 + ln * 0.2) + [0, 0.6 + ln * 0.12, z0 + ln * 0.38]
        p2 = radial * (1.6 + ln * 0.33) + [0, 0.6 + ln * 0.22, z0 + ln * 0.72]
        p3 = radial * (1.7 + ln * 0.5) + [0, 0.6 + ln * 0.42, z0 + ln]
        w = rng.uniform(0.3, 0.45)
        blades.append(blade([p0, p1, p2, p3], [w, w * 0.85, w * 0.5, 0], 0.1, tang))
    # cornes / bois : deux longues pointes vers l'arrière, légèrement écartées
    for side in (-1, 1):
        path = [[side * 0.6, 1.4, 0.4], [side * 1.0, 2.3, 1.6], [side * 1.5, 3.0, 3.2], [side * 1.7, 3.4, 5.0]]
        blades.append(_oriented(*tube(path, [0.32, 0.25, 0.15, 0], 5, tip=True)))
        # petite branche
        br = [[side * 1.05, 2.4, 1.8], [side * 1.6, 3.4, 2.0], [side * 1.9, 4.1, 2.6]]
        blades.append(_oriented(*tube(br, [0.16, 0.1, 0], 4, tip=True)))
        # moustaches de cristal sur les joues
        wh = [[side * 0.7, 0.2, -2.6], [side * 1.6, -0.2, -1.6], [side * 2.4, -0.4, -0.2], [side * 3.0, -0.2, 1.4]]
        blades.append(blade(wh, [0.22, 0.2, 0.12, 0], 0.08, [0, 1, 0]))
        # lames de pommette
        ck = [[side * 1.1, 0.3, 0.3], [side * 1.9, 0.5, 1.2], [side * 2.6, 0.9, 2.2], [side * 3.1, 1.4, 3.3]]
        blades.append(blade(ck, [0.35, 0.3, 0.16, 0], 0.1, [0, 1, 0]))

    # mâchoire, entrouverte (charnière à l'arrière)
    jprof = [(1.3, 1.0, -0.3, -0.9), (0.2, 1.05, -0.25, -1.0), (-1.2, 0.75, -0.2, -0.8),
             (-2.6, 0.58, -0.15, -0.62), (-3.7, 0.4, -0.12, -0.5)]
    jaw = [_oriented(*loft([_section(z, w, t, b, 8) for z, w, t, b in jprof]))]
    for side in (-1, 1):
        for k in range(5):
            z = -3.5 + k * 0.65
            x = side * (0.33 + 0.1 * k)
            jaw.append(_oriented(*tube([[x, -0.2, z], [x, 0.3, z - 0.05]], [0.11, 0], 3, tip=True)))
        # barbe : lames sous le menton
        bd = [[side * 0.4, -0.85, -0.8], [side * 0.7, -1.6, 0.2], [side * 1.0, -2.0, 1.5], [side * 1.2, -2.1, 2.8]]
        jaw.append(blade(bd, [0.3, 0.26, 0.14, 0], 0.08, [1, 0, 0]))
    bd = [[0, -0.95, -0.2], [0, -1.9, 0.6], [0, -2.5, 1.7], [0, -2.8, 3.0]]
    jaw.append(blade(bd, [0.32, 0.28, 0.15, 0], 0.08, [1, 0, 0]))
    piv = np.array([0, -0.3, 1.3])
    jaw = [(transform(np.array(v) - piv, rot_matrix_x(-0.28), piv), f) for v, f in jaw]

    eyes = []
    for side in (-1, 1):
        v, f = blob([side * 0.98, 1.05, -0.55], 0.26, scale=(0.8, 0.6, 1.3), jitter=0.0, subdiv=0)
        eyes.append(_oriented(v, f))

    # la tête est un peu plus en avant que le point 0 de la colonne
    M, o = frame(pts, 0) * HEAD_SCALE, pts[0] + np.array([0, -0.8, -2.0])
    pl = lambda lst: [place(x, M, o) for x in lst]
    return pl(skull), pl(blades), pl(jaw), pl(eyes)


# ---------------- pattes ----------------

def leg(rng, pts, i, side, back):
    """Patte au repos, pendante. Renvoie une liste de (v, f) placés."""
    r = radius(i)
    M, o = frame(pts, i), pts[i]
    s = 1.4 if back else 1.3
    hip = np.array([side * r * 0.75, -r * 0.35, 0.0])
    knee = hip + np.array([side * 0.5, -2.4, -0.9 if not back else 0.6]) * s
    ankle = knee + np.array([side * 0.1, -2.2, 0.8 if not back else -0.7]) * s
    foot = ankle + np.array([0, -0.9, -0.4]) * s
    out = [_oriented(*tube([hip, (hip + knee) / 2, knee], [0.62 * s, 0.5 * s, 0.38 * s], 5, jitter=0.1, rng=rng)),
           _oriented(*tube([knee, (knee + ankle) / 2, ankle], [0.4 * s, 0.32 * s, 0.26 * s], 5, jitter=0.1, rng=rng)),
           _oriented(*tube([ankle, foot], [0.3 * s, 0.34 * s], 5)),
           # épines au coude / genou
           blade([knee, knee + [side * 0.3, 0.3, 1.0], knee + [side * 0.5, 0.8, 1.9]], [0.22, 0.14, 0], 0.08, [1, 0, 0])]
    for k in range(4):
        a = math.radians(-50 + 33 * k) if k < 3 else math.radians(180)
        d = np.array([math.sin(a) * 0.55, 0, -math.cos(a)])
        c0 = foot + d * 0.25
        out.append(_oriented(*tube([c0, c0 + d * 0.6 + [0, -0.25, 0], c0 + d * 0.95 + [0, -0.7, 0]],
                                   [0.14 * s, 0.1 * s, 0], 4, tip=True)))
    return [place(x, M, o) for x in out]


# ---------------- assemblage ----------------

def dragon_cristal(name="Dragon_Cristal", seed=55):
    rng = np.random.default_rng(seed)
    pts = spine()
    a = Asset(name)
    col_b, mat_b = STYLE["body"]
    col_l, mat_l = STYLE["blades"]
    col_e, mat_e = STYLE["eyes"]

    skull, blades, jaw, eyes = head(rng, pts)
    for v, f in skull:
        a.add("Head", v, f, col_b, mat_b)
    for v, f in blades:
        a.add("Head_Blades", v, f, col_l, mat_l)
    for v, f in jaw:
        a.add("Head_Jaw", v, f, col_l, mat_l)
    for v, f in eyes:
        a.add("Head_Eyes", v, f, col_e, mat_e)

    for i in range(1, N_SEG + 1):
        core, bl = body_segment(rng, i, pts)
        nm = f"Seg{i:02d}"
        a.add(nm, *core, col_b, mat_b)
        for v, f in bl:
            a.add(nm + "_Blades", v, f, col_l, mat_l)

    for seg, back, tag in ((FRONT_LEG_SEG, False, "F"), (BACK_LEG_SEG, True, "B")):
        for side, sname in ((-1, "L"), (1, "R")):
            for v, f in leg(rng, pts, seg, side, back):
                a.add(f"Seg{seg:02d}_Leg{tag}{sname}", v, f, col_b, mat_b)
    return a


def all_assets():
    return [dragon_cristal()]
