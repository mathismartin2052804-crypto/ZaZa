# Série 5, v5 : dragon de cristal serpentin, qui VOLE (comme sur la vidéo de référence).
# Part de la v4 (assets5v4.py, gardée telle quelle). La tête (yeux, regard, gemme, crocs) est reprise
# à l'identique : Will l'a validée. Ce que la v5 change, parce que la v4 « faisait chien ou renard » :
#   - proportions : corps long et serpentin (34 morceaux de 2,6 studs, environ 8 fois plus long que haut),
#     au lieu d'un quadrupède haut sur pattes ;
#   - dos en vague (tête basse dans l'axe du cou, dos qui monte, creux, queue qui remonte au bout),
#     au lieu d'un dos droit et horizontal ;
#   - queue longue qui s'affine, avec une petite touffe au bout, au lieu d'une grosse queue de renard ;
#   - lames du dos plus couchées le long du corps (moins « fourrure ») ;
#   - pattes fines, plus courtes par rapport au corps, qui pendent sous le ventre (pose de vol) :
#     bras presque droit, pointe au coude, grande main à quatre doigts griffus écartés (comme des serres).
#     Les pattes arrière sont tendues vers l'arrière, pieds tournés vers la queue.
#     Plus de talon relevé « de chien ».
#
# Morceaux (mêmes noms qu'en v4, le script d'animation s'en sert) :
#   Head, Head_Blades, Head_Jaw, Head_Eyes, Head_Pupils, Head_Brows, Head_Gem ;
#   Seg01..Seg34 et SegXX_Blades ;
#   SegXX_LegFL/FR/BL/BR (bras ou cuisse, pivote à l'épaule/hanche), _Shin (avant-bras ou tibia, pivote au coude
#   ou au genou), _Foot (main ou pied, pivote au poignet ou à la cheville).
# Repère : Y vers le haut, tête vers -Z, 1 unité = 1 stud, sol à Y = 0 (le dragon vole au-dessus).
import math
import numpy as np
from meshlib import Asset, ring, tube, blob, loft, rot_matrix_x
from assets5 import _oriented, frame, place
import assets5v4 as v4
from assets5v4 import flame, _dirs, _smooth, STYLE, HEAD_PITCH, HEAD_WIDEN, HEAD_SCALE, JAW_HINGE

N_SEG = 34
SPACING = 2.6
FRONT_LEG_SEG = 10         # sur la vidéo, les bras sont au tiers avant du corps
BACK_LEG_SEG = 28          # et les pattes arrière vers les 4/5 ; la queue (touffue) part juste derrière
FLY_H = 24.0               # hauteur du dos au-dessus du sol (le dragon vole)


# ---------------- la colonne au repos ----------------

def spine():
    """Points de repos : 0 = tête, 1..N = morceaux. Une grande arche comme sur la vidéo : tête basse,
    dos le plus haut vers les 3/5, queue qui redescend ; une petite vague par-dessus pour casser la ligne."""
    pts = []
    for i in range(N_SEG + 1):
        t = i / N_SEG
        y = (FLY_H - 6.0 + 13.0 * math.sin(math.pi * t ** 1.36)  # l'arche (environ 15 % de la longueur), au plus haut vers t = 0,6
             + 4.0 * t                                             # la queue retombe moins bas que la tête
             + 0.8 * math.sin(4 * math.pi * t))                    # petite vague
        pts.append(np.array([0.0, y, i * SPACING]))
    out = [pts[0]]
    for p in pts[1:]:
        d = p - out[-1]
        out.append(out[-1] + d / np.linalg.norm(d) * SPACING)
    return out


def radius(i):
    """Corps épais jusqu'aux pattes arrière, puis une longue queue qui s'affine."""
    t = i / N_SEG
    if t < 0.12:
        return 3.6 + 0.5 * (t / 0.12)
    tb = BACK_LEG_SEG / N_SEG
    if t < tb:
        return 4.1 - 0.7 * _smooth(0.12, tb, t)
    return 3.4 - 2.0 * ((t - tb) / (1 - tb))           # queue courte et touffue, 1,4 au bout


# ---------------- morceaux du corps ----------------

def body_segment(rng, i, pts):
    r = radius(i)
    rc = r * 0.84
    L = SPACING * 0.72
    rings = []
    for k, (z, s) in enumerate([(-L, 0.95), (0.0, 1.05), (L, 0.93)]):
        rr = ring((0, 0, z), rc * s, 8, angle0=0.4 * k + i * 0.3, axis_u=(1, 0, 0), axis_v=(0, 1, 0),
                  jitter=0.08, rng=rng)
        rr[:, 1] *= 1.15
        rings.append(rr)
    core = _oriented(*loft(rings))

    t = i / N_SEG
    mane = math.exp(-((t - 0.05) / 0.08) ** 2)
    tuft = max(0.0, (t - 0.85) / 0.15)
    rs = 0.55 + 0.45 * min(r, 4.1) / 4.1
    back = np.array([0, 0, 1.0])
    blades = []
    # couche du dessous : lames courtes plaquées (cachent le cœur foncé)
    st = 13 if i % 2 else 0
    for a0 in range(-40, 221, 40):
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (3.0 + 1.0 * top) * rs * rng.uniform(0.85, 1.2)
        root = radial * np.array([rc, rc * 1.15, 0]) * 0.92 + [0, 0, rng.uniform(-0.8, 0.2) * L]
        blades.append(flame(rng, root, radial, tang, back, ln, r * 0.7, 0.22, 0.15, 0.4, 0.3, pts=4))
    # couche du dessus : longues mèches couchées le long du corps (flare faible = plaquées, pas dressées)
    st = 15 if i % 2 else 0
    for a0 in range(-35, 216, 30):
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (6.4 + 3.4 * top + 3.0 * mane + 3.0 * tuft) * rs * rng.uniform(0.75, 1.3)
        if rng.uniform() < 0.12:
            ln *= 1.3
        root = radial * np.array([rc, rc * 1.15, 0]) * 0.95 + [0, 0, rng.uniform(-0.9, 0.0) * L]
        w = r * (0.46 + 0.18 * top) * rng.uniform(0.85, 1.15)
        blades.append(flame(rng, root, radial, tang, back, ln, w, 0.35 + 0.2 * (1 - top) + 0.4 * tuft,
                            hook=0.25 + 0.3 * top, wave=1.0, twist=0.6))
    for a0 in (250, 290):
        a = math.radians(a0 + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        blades.append(flame(rng, radial * rc * 1.1, radial, tang, back, 2.2 * rs, r * 0.25, 0.3, 0.3, pts=4))
    if i == N_SEG:                              # petite touffe au bout de la queue
        for k in range(8):
            a = 2 * math.pi * k / 8 + rng.uniform(-0.2, 0.2)
            radial, tang = _dirs(a)
            blades.append(flame(rng, radial * rc * 0.5 + [0, 0, 0.5], radial, tang, back,
                                rng.uniform(3.5, 5.0), 0.4, 0.6, 0.8, wave=1.2))
    M, o = frame(pts, i), pts[i]
    return place(core, M, o), [place(b, M, o) for b in blades]


# ---------------- pattes de vol (bras, avant-bras, main) ----------------

def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def leg_pose(pts, seg, side, front):
    """Pose de vol d'une patte (repère monde) : épaule/hanche, coude/genou, poignet/cheville, bout de la main.
    Avant : bras vers le bas et un peu en arrière, avant-bras presque vertical, main qui pend.
    Arrière : cuisse vers l'avant et le bas, tibia tendu vers l'arrière, pied tourné vers la queue."""
    M, o = frame(pts, seg), pts[seg]
    r = radius(seg)
    hip = M @ np.array([side * r * 0.6, -r * 0.55, 0.0]) + o
    out = side * np.array([1.0, 0, 0])
    if front:
        l1, l2 = 4.4, 5.6
        d1 = np.array([0.25 * side, -0.85, 0.45]); d2 = np.array([0.1 * side, -0.97, -0.2])
        hand = np.array([0.05 * side, -0.75, -0.65])      # doigts vers le bas et l'avant
    else:
        l1, l2 = 4.4, 5.6
        d1 = np.array([0.25 * side, -0.7, -0.65]); d2 = np.array([0.08 * side, -0.55, 0.83])
        hand = np.array([0.0, -0.35, 0.94])               # pied tendu vers la queue
    d1, d2, hand = (d / np.linalg.norm(d) for d in (d1, d2, hand))
    knee = hip + d1 * l1
    ankle = knee + d2 * l2
    bend = np.array([0, 0, 1.0]) if front else np.array([0, 0, -1.0])
    return dict(hip=hip, knee=knee, ankle=ankle, hand=hand, out=out, l1=l1, l2=l2, bend=bend)


def _claw_hand(rng, ankle, hand, out, front, big):
    """Main en serres : paume, trois longs doigts écartés en éventail, griffes recourbées, un pouce opposé.
    Le dos de la main est calculé pareil des deux côtés (sinon une main se plie à l'envers)."""
    x = np.array([1.0, 0, 0])
    up = np.cross(x, hand) if front else np.cross(hand, x)   # dos de la main : vers l'avant (bras), vers le haut (pied)
    up /= np.linalg.norm(up)
    parts = [_oriented(*blob(ankle + hand * 0.3, 0.5 * big, scale=(1.0, 0.8, 1.1), jitter=0.05, rng=rng, subdiv=0))]
    for k, spread in enumerate((-0.65, 0.0, 0.65)):
        d = hand * math.cos(spread) + out * math.sin(spread)
        d /= np.linalg.norm(d)
        ln = (2.0 if k == 1 else 1.7) * big
        p0 = ankle + hand * 0.35
        p1 = p0 + d * ln * 0.55 + up * 0.2                  # première phalange, un peu relevée
        p2 = p1 + (d * 0.95 - up * 0.3) * ln * 0.45          # deuxième, presque dans l'axe : la main reste ouverte
        tip = p2 + (d * 0.6 - up * 0.8) * 0.85 * big         # seule la griffe se recourbe
        parts.append(_oriented(*tube([p0, p1, p2], [0.26 * big, 0.21 * big, 0.17 * big], 4)))
        parts.append(_oriented(*tube([p2, (p2 + tip) / 2 + d * 0.15 * big, tip], [0.16 * big, 0.1 * big, 0], 4, tip=True)))
    # pouce (ergot) : vers l'arrière de la main, griffe qui se referme
    p0 = ankle + hand * 0.2
    p1 = p0 - up * 0.9 * big - hand * 0.15
    tip = p1 + hand * 0.6 * big - up * 0.2
    parts.append(_oriented(*tube([p0, p1, tip], [0.2 * big, 0.14 * big, 0], 4, tip=True)))
    return parts


def leg_parts(rng, P, side, front):
    """Renvoie (bras, avant-bras, main), chacun une liste de (v, f) en repère monde."""
    hip, knee, ankle = P["hip"], P["knee"], P["ankle"]
    k = 1.15 if front else 1.25                  # fines, comme sur la vidéo
    upper = [_oriented(*tube([hip, (hip + knee) / 2, knee], [1.05 * k, 0.75 * k, 0.5 * k], 6, jitter=0.08, rng=rng))]
    shin = [_oriented(*tube([knee, (knee + ankle) / 2, ankle], [0.48 * k, 0.4 * k, 0.33 * k], 5, jitter=0.08, rng=rng))]
    # facettes de cristal : une longue pointe au coude/genou vers l'arrière, deux lames sur le bras
    a = math.radians(90 - side * 60)
    radial = np.array([math.cos(a), math.sin(a), 0.0]); tang = np.array([-math.sin(a), math.cos(a), 0.0])
    upper.append(flame(rng, hip + [0, -0.3, 0], radial, tang, np.array([0, 0.25, 1.0]) / 1.03, 2.8, 0.4, 0.4, 0.6, pts=4))
    spike_dir = np.array([0, -0.2, 1.0]) if front else np.array([0, -0.2, -1.0])
    spike_dir /= np.linalg.norm(spike_dir)
    shin.append(_oriented(*tube([knee, knee + spike_dir * 1.0 + [0, 0.1, 0], knee + spike_dir * 2.0],
                                [0.3, 0.18, 0], 4, tip=True)))
    shin.append(flame(rng, (knee + ankle) / 2, radial, tang, -spike_dir if not front else spike_dir,
                      1.6, 0.3, 0.4, 0.5, pts=4))
    foot = _claw_hand(rng, ankle, P["hand"], P["out"], front, 1.45 if front else 1.35)
    return upper, shin, foot


# ---------------- assemblage ----------------

def dragon_cristal_v5(name="Dragon_Cristal_v5", seed=57):
    rng = np.random.default_rng(seed)
    pts = spine()
    a = Asset(name)
    col_b, mat_b = STYLE["body"]
    col_l, mat_l = STYLE["blades"]
    meta = {"chain": [p.tolist() for p in pts], "legs": {}, "ground": 0.0}

    # tête v4 à l'identique, dans l'axe du cou
    Mh, oh = frame(pts, 0) @ rot_matrix_x(HEAD_PITCH) @ HEAD_WIDEN * HEAD_SCALE, pts[0] + np.array([0, 0.4, -3.6])
    skull, blades, jaw, eyes, pupils, gem, brows = v4.head(rng)
    for nm, lst, key in (("Head", skull, "body"), ("Head_Blades", blades, "blades"), ("Head_Jaw", jaw, "blades"),
                         ("Head_Eyes", eyes, "eyes"), ("Head_Pupils", pupils, "pupils"), ("Head_Gem", gem, "gem"),
                         ("Head_Brows", brows, "brows")):
        c, m = STYLE[key]
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
            upper, shin, foot = leg_parts(rng, P, side, front)
            for suffix, lst in (("", upper), ("_Shin", shin), ("_Foot", foot)):
                for v, f in lst:
                    a.add(nm + suffix, v, f, col_b, mat_b)
            meta["legs"][nm] = {"seg": seg, "front": front, "side": side,
                                **{k: (P[k].tolist() if isinstance(P[k], np.ndarray) else P[k])
                                   for k in ("hip", "knee", "ankle", "hand", "l1", "l2", "bend")}}
    a.meta = meta
    return a


def all_assets():
    return [dragon_cristal_v5()]
