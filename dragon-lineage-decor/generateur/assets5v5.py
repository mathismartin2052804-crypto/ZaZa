# Série 5, v5 : dragon de cristal serpentin, qui VOLE (comme sur la vidéo de référence).
# Part de la v4 (assets5v4.py, gardée telle quelle). La tête (yeux, regard, gemme, crocs) est reprise
# à l'identique : Will l'a validée. Ce que la v5 change, parce que la v4 « faisait chien ou renard » :
#   - proportions : corps long et serpentin (38 morceaux de 2,6 studs, environ 9 fois plus long que haut),
#     au lieu d'un quadrupède haut sur pattes ;
#   - dos en vague (tête basse dans l'axe du cou, dos qui monte, creux, queue qui remonte au bout),
#     au lieu d'un dos droit et horizontal ;
#   - queue longue qui s'affine, avec une petite touffe au bout, au lieu d'une grosse queue de renard ;
#   - lames du dos plus couchées le long du corps (moins « fourrure ») ;
#   - pattes plus courtes par rapport au corps, qui pendent sous le ventre (pose de vol) :
#     bras presque droit, pointe au coude, grande main à quatre doigts griffus écartés (comme des serres),
#     membres épais couverts de plaques de cristal qui se chevauchent (comme sur la vidéo) ;
#     pattes arrière : genou en avant, talon en arrière avec un ergot, orteils vers l'avant ;
#   - antennes plus écartées sur les côtés (de face, elles ne montent plus droit comme des oreilles) ;
#   - longues mèches du dos plus longues et qui se relèvent en flammes au bout ;
#   - de face, corps plus large que haut, mèches des flancs écartées et collerette derrière la tête (allure « lion ») ;
#   - cou en S (petit creux derrière la nuque, tête qui se relève) ; queue plus longue et plus fine (38 morceaux) ;
#   - hanche arrière sortie du corps pour qu'on voie la cuisse ;
#   - (retouches après la v5, demandées par Will) : gueule sombre (palais, joues, plancher, langue) et dents
#     blanc glacé à part, au lieu d'une bouche du même bleu que le reste ; mèches du dessus HÉRISSÉES
#     (bristle() : base couchée puis la mèche se relève de 20 à 50°, surtout sur l'arrière du dos) au lieu
#     de plaquées ; yeux C (iris or, fente noire).
#
# Morceaux (mêmes noms qu'en v4, le script d'animation s'en sert) :
#   Head, Head_Blades, Head_Jaw, Head_Eyes, Head_Pupils, Head_Brows, Head_Gem ;
#   Head_Teeth (crocs du haut) et Head_Mouth (palais et joues sombres) : suivent Head ;
#   Head_Jaw_Teeth (crocs du bas), Head_Jaw_Mouth (plancher sombre) et Head_Jaw_Tongue (langue) :
#   suivent la mâchoire. RÈGLE pour le script : tout ce qui commence par « Head_Jaw » pivote avec Head_Jaw ;
#   Seg01..Seg38 et SegXX_Blades ;
#   SegXX_LegFL/FR/BL/BR (bras ou cuisse, pivote à l'épaule/hanche), _Shin (avant-bras ou tibia, pivote au coude
#   ou au genou), _Foot (main ou pied, pivote au poignet ou à la cheville) ;
#   SegXX_LegYY_Blades et SegXX_LegYY_Shin_Blades : les plaques de cristal (bleu clair), elles suivent
#   la cuisse et le tibia. ATTENTION au script : « Seg10_LegFL_Blades » bouge avec la patte, pas avec Seg10.
# Repère : Y vers le haut, tête vers -Z, 1 unité = 1 stud, sol à Y = 0 (le dragon vole au-dessus).
import math
import numpy as np
from meshlib import Asset, ring, tube, blob, loft, rot_matrix_x, transform
from assets5 import _oriented, frame, place, _section
import assets5v4 as v4
from assets5v4 import flame, blade3, _dirs, _smooth, _snout, STYLE as STYLE4, HEAD_PITCH, HEAD_WIDEN, HEAD_SCALE, \
    JAW_HINGE, JAW_OPEN

N_SEG = 38                 # 34 au début de la v5 : la queue est plus longue (10 morceaux après les pattes arrière)
SPACING = 2.6
FRONT_LEG_SEG = 10         # sur la vidéo, les bras sont au tiers avant du corps
BACK_LEG_SEG = 28          # et les pattes arrière vers les 4/5 ; la queue (touffue) part juste derrière
FLY_H = 24.0               # hauteur du dos au-dessus du sol (le dragon vole)

STYLE = dict(STYLE4)
STYLE.update({
    "eyes": ("#FFB22E", "Neon"),        # yeux C, choisis par Will pour la v5 : iris or…
    "pupils": ("#120600", "Neon"),      # …et fente noire
    "teeth": ("#E6F4FF", "Ice"),        # dents blanc glacé : elles ressortent sur la gueule sombre
    "mouth": ("#070B1C", "SmoothPlastic"),   # intérieur de la gueule, presque noir
    "tongue": ("#18224C", "SmoothPlastic"),  # langue bleu nuit, à peine plus claire que la gueule
})


# antennes : elles partent sur les côtés puis filent vers l'arrière (v4 : elles montaient presque droit)
v4.ANTENNA = [(0.6, 2.1, -0.6), (2.0, 3.0, 0.0), (3.6, 3.9, 0.9), (5.0, 4.8, 2.1), (6.0, 5.7, 3.6), (6.5, 6.5, 5.4)]


# ---------------- mèches hérissées ----------------

def bristle(rng, root, radial, tang, back, ln, w, rise, hook=0.4, wave=1.0, twist=0.5, pts=5):
    """Mèche hérissée (comme sur la vidéo) : la base reste couchée sur le corps, puis la mèche se relève
    jusqu'à l'angle « rise » (radians, mesuré depuis le corps) et la pointe se redresse encore de « hook ».
    flame() restait presque à plat (moins de 15°) : les mèches avaient l'air plaquées."""
    phase = rng.uniform(0, 2 * math.pi)
    amp = 0.08 * wave * ln * rng.uniform(0.7, 1.3)
    tw = twist * rng.uniform(-1, 1)
    p = np.array(root, float)
    path, sides = [p.copy()], [tang]
    for k in range(1, pts):
        u = k / (pts - 1)
        ang = rise * (0.3 + 0.7 * u) + hook * u * u
        p = p + (back * math.cos(ang) + radial * math.sin(ang)) * (ln / (pts - 1))
        path.append(p + tang * amp * math.sin(2 * math.pi * u * 0.9 + phase) * u)
        a = tw * u
        sides.append(tang * math.cos(a) + radial * math.sin(a))
    prof = [0.8, 1.0, 0.85, 0.55, 0.25, 0.0] if pts == 6 else [0.85, 1.0, 0.7, 0.35, 0.0] if pts == 5 \
        else [0.9, 1.0, 0.5, 0.0]
    return blade3(path, [w * f for f in prof], 0.1, sides)


# ---------------- tête : celle de la v4, avec une vraie gueule ----------------

def _jaw_place(v):
    """Repère « mâchoire » de la v4 : museau raccourci, puis ouverture de JAW_OPEN autour de la charnière."""
    return transform(_snout(v) - JAW_HINGE, rot_matrix_x(-JAW_OPEN), JAW_HINGE)


def head5(rng):
    """Tête v4 à l'identique (validée), mais les dents sont sorties dans leurs propres parties (blanc glacé)
    et la gueule a un intérieur sombre : palais, joues, plancher et langue. Avant, tout était du même bleu."""
    skull, bl, jaw, eyes, pupils, gem, brows = v4.head(rng)
    # v4.head : Head_Blades commence par les 2 x 9 crocs du haut ; Head_Jaw = [os], puis par côté 8 crocs
    # et 4 pointes de joue, puis 7 mèches de barbe
    assert len(jaw) == 1 + 2 * 12 + 7
    teeth, bl = bl[:18], bl[18:]
    jaw_teeth = jaw[1:9] + jaw[13:21]
    jaw = jaw[:1] + jaw[9:13] + jaw[21:]

    # palais : une plaque sombre sous le crâne, du fond de la gorge au bout du museau
    pal = [(1.7, 1.25, -0.62), (0.3, 1.3, -0.52), (-2.0, 0.98, -0.32), (-3.6, 0.82, -0.27),
           (-5.2, 0.74, -0.22), (-6.6, 0.64, -0.17), (-7.3, 0.4, -0.13)]
    mouth = [_oriented(*loft([_section(z, w, b + 0.28, b - 0.07, 8) for z, w, b in pal]))]
    mouth = [(_snout(v), f) for v, f in mouth]
    # plancher de la gueule (dans la mâchoire) et langue posée dessus, la pointe un peu relevée
    flo = [(1.7, 1.2, -0.42), (0.3, 1.25, -0.36), (-1.8, 1.0, -0.31), (-3.8, 0.78, -0.29),
           (-5.6, 0.6, -0.23), (-6.7, 0.42, -0.19)]
    jaw_mouth = [_oriented(*loft([_section(z, w, t + 0.07, t - 0.3, 8) for z, w, t in flo]))]
    ton = [(1.2, 0.5, -0.33, 0.22), (-0.8, 0.48, -0.3, 0.28), (-2.8, 0.4, -0.28, 0.26),
           (-4.3, 0.3, -0.2, 0.22), (-5.2, 0.17, -0.05, 0.15)]
    tongue = [_oriented(*loft([_section(z, w, t + h, t - 0.05, 8) for z, w, t, h in ton] + [np.array([0, 0.1, -5.7])]))]
    # joues : une membrane sombre de chaque côté, au fond de la gueule, entre le palais et la mâchoire ouverte
    # (de face, on voit un trou noir au lieu du bleu du crâne à travers la bouche)
    for side in (-1, 1):
        rings = []
        for z, wu, yu, wl, yl in ((1.6, 1.15, -0.55, 1.1, -0.42), (0.3, 1.2, -0.48, 1.15, -0.36),
                                  (-1.2, 1.05, -0.36, 1.02, -0.32), (-2.6, 0.92, -0.3, 0.9, -0.3)):
            up = _snout(np.array([[side * wu, yu, z], [side * (wu - 0.12), yu, z]]))
            lo = _jaw_place(np.array([[side * wl, yl, z], [side * (wl - 0.12), yl, z]]))
            rings.append(np.array([up[0], lo[0], lo[1], up[1]]))
        mouth.append(_oriented(*loft(rings)))
    jaw_mouth = [(_jaw_place(v), f) for v, f in jaw_mouth]
    tongue = [(_jaw_place(v), f) for v, f in tongue]
    return dict(Head=skull, Head_Blades=bl, Head_Jaw=jaw, Head_Eyes=eyes, Head_Pupils=pupils, Head_Gem=gem,
                Head_Brows=brows, Head_Teeth=teeth, Head_Mouth=mouth, Head_Jaw_Teeth=jaw_teeth,
                Head_Jaw_Mouth=jaw_mouth, Head_Jaw_Tongue=tongue)


HEAD_STYLE = {"Head": "body", "Head_Blades": "blades", "Head_Jaw": "blades", "Head_Eyes": "eyes",
              "Head_Pupils": "pupils", "Head_Gem": "gem", "Head_Brows": "brows", "Head_Teeth": "teeth",
              "Head_Mouth": "mouth", "Head_Jaw_Teeth": "teeth", "Head_Jaw_Mouth": "mouth",
              "Head_Jaw_Tongue": "tongue"}


# ---------------- la colonne au repos ----------------

def spine():
    """Points de repos : 0 = tête, 1..N = morceaux. Une grande arche comme sur la vidéo : tête basse,
    dos le plus haut vers les 3/5, queue qui redescend ; une petite vague par-dessus pour casser la ligne."""
    pts = []
    for i in range(N_SEG + 1):
        t = i / N_SEG
        y = (FLY_H - 6.0 + 13.0 * math.sin(math.pi * t ** 1.36)  # l'arche (environ 15 % de la longueur), au plus haut vers t = 0,6
             + 4.0 * t                                             # la queue retombe moins bas que la tête
             + 0.8 * math.sin(4 * math.pi * t)                     # petite vague
             + 1.8 * math.exp(-(t / 0.035) ** 2)                   # cou en S : la tête se relève…
             - 1.4 * math.exp(-((t - 0.09) / 0.05) ** 2))          # …après un petit creux derrière la nuque
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
    return 3.3 - 2.5 * ((t - tb) / (1 - tb)) ** 0.8    # queue longue qui s'affine, 0,8 au bout


# ---------------- morceaux du corps ----------------

def body_segment(rng, i, pts):
    r = radius(i)
    rc = r * 0.84
    L = SPACING * 0.72
    rings = []
    for k, (z, s) in enumerate([(-L, 0.95), (0.0, 1.05), (L, 0.93)]):
        rr = ring((0, 0, z), rc * s, 8, angle0=0.4 * k + i * 0.3, axis_u=(1, 0, 0), axis_v=(0, 1, 0),
                  jitter=0.08, rng=rng)
        rr[:, 0] *= 1.2                        # plus large (de face, il faisait « colonne »)
        rr[:, 1] *= 1.05
        rings.append(rr)
    core = _oriented(*loft(rings))

    t = i / N_SEG
    mane = math.exp(-((t - 0.05) / 0.08) ** 2)
    tuft = max(0.0, (t - 0.9) / 0.1)
    rs = 0.55 + 0.45 * min(r, 4.1) / 4.1
    back = np.array([0, 0, 1.0])
    blades = []
    # couche du dessous : lames courtes plaquées (cachent le cœur foncé)
    st = 13 if i % 2 else 0
    for a0 in range(-40, 221, 52):          # 6 lames (7 au début de la v5) : on garde des triangles pour la queue
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (3.0 + 1.0 * top) * rs * rng.uniform(0.85, 1.2)
        root = radial * np.array([rc * 1.2, rc * 1.05, 0]) * 0.92 + [0, 0, rng.uniform(-0.8, 0.2) * L]
        blades.append(flame(rng, root, radial, tang, back, ln, r * 0.7, 0.22, 0.15, 0.4, 0.3, pts=4))
    # couche du dessus : longues mèches HÉRISSÉES (bristle) : base couchée, puis elles se relèvent,
    # davantage sur le dos que sur les flancs, et davantage sur l'arrière du corps (comme sur la vidéo)
    st = 15 if i % 2 else 0
    rear = _smooth(0.35, 0.75, t)
    for a0 in range(-35, 216, 30 if r > 2.2 else 40):    # moins de mèches sur le bout de la queue
        a = math.radians(a0 + st + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        top = max(0.0, math.sin(a))
        ln = (6.6 + 5.4 * top + 3.0 * mane + 3.0 * tuft) * rs * rng.uniform(0.75, 1.3)
        if rng.uniform() < 0.15:               # quelques très longues mèches qui sortent de la masse
            ln *= 1.4
        root = radial * np.array([rc * 1.2, rc * 1.05, 0]) * 0.95 + [0, 0, rng.uniform(-0.9, 0.0) * L]
        w = r * (0.42 + 0.16 * top) * rng.uniform(0.85, 1.15)
        rise = (0.32 + 0.3 * top + 0.2 * rear * top + 0.15 * mane) * rng.uniform(0.75, 1.25)
        blades.append(bristle(rng, root, radial, tang, back, ln, w, rise, hook=0.25 + 0.35 * top,
                              wave=1.1, twist=0.6))
    for a0 in (250, 290):
        a = math.radians(a0 + rng.uniform(-8, 8))
        radial, tang = _dirs(a)
        blades.append(flame(rng, radial * rc * 1.1, radial, tang, back, 2.2 * rs, r * 0.25, 0.3, 0.3, pts=4))
    if i <= 3:                                  # collerette : grandes lames qui s'écartent derrière la tête (vue de face « lion »)
        for k in range(9):
            a = math.radians(-60 + 300 * k / 8 + 10 * i + rng.uniform(-8, 8))
            radial, tang = _dirs(a)
            side = abs(math.cos(a))                 # les lames des côtés sont les plus longues : la tête paraît large de face
            root = radial * np.array([rc * 1.2, rc * 1.05, 0]) * 0.9
            ln = (8.0 + 6.0 * side - 1.5 * (i - 1)) * rng.uniform(0.85, 1.15)
            d = back * (0.75 - 0.4 * side) + radial * (0.25 + 0.4 * side)   # sur les côtés, elles partent vers l'extérieur
            blades.append(flame(rng, root, radial, tang, d / np.linalg.norm(d), ln, r * 0.5,
                                1.2, 0.7, wave=1.0, twist=0.5, pts=5))
    if i == N_SEG:                              # petite touffe au bout de la queue
        for k in range(6):
            a = 2 * math.pi * k / 6 + rng.uniform(-0.2, 0.2)
            radial, tang = _dirs(a)
            blades.append(flame(rng, radial * rc * 0.5 + [0, 0, 0.5], radial, tang, back,
                                rng.uniform(3.0, 4.2), 0.35, 0.5, 0.8, wave=1.2))
    M, o = frame(pts, i), pts[i]
    return place(core, M, o), [place(b, M, o) for b in blades]


# ---------------- pattes de vol (bras, avant-bras, main) ----------------

def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def leg_pose(pts, seg, side, front):
    """Pose de vol d'une patte (repère monde) : épaule/hanche, coude/genou, poignet/cheville, direction des doigts.
    Avant : bras vers le bas et un peu en arrière (coude en arrière), avant-bras presque vertical, main qui pend.
    Arrière : cuisse vers l'avant (genou en avant), tibia vers le bas et l'arrière (talon en arrière),
    pied et orteils tournés vers l'AVANT, comme une vraie patte arrière de reptile (en v5 du début, le pied
    partait vers la queue : patte « à l'envers »)."""
    M, o = frame(pts, seg), pts[seg]
    r = radius(seg)
    # la hanche arrière sort davantage du corps, sinon la cuisse disparaît sous les mèches
    hip = M @ (np.array([side * r * 0.7, -r * 0.55, 0.0]) if front else np.array([side * r * 0.95, -r * 0.75, 0.0])) + o
    out = side * np.array([1.0, 0, 0])
    if front:
        l1, l2 = 4.4, 5.6
        d1 = np.array([0.25 * side, -0.85, 0.45]); d2 = np.array([0.1 * side, -0.97, -0.2])
        hand = np.array([0.05 * side, -0.75, -0.65])      # doigts vers le bas et l'avant
    else:
        l1, l2 = 4.6, 5.0
        d1 = np.array([0.45 * side, -0.6, -0.7]); d2 = np.array([0.08 * side, -0.8, 0.6])
        hand = np.array([0.05 * side, -0.6, -0.8])        # orteils vers l'avant et le bas
    d1, d2, hand = (d / np.linalg.norm(d) for d in (d1, d2, hand))
    knee = hip + d1 * l1
    ankle = knee + d2 * l2
    bend = np.array([0, 0, 1.0]) if front else np.array([0, 0, -1.0])
    return dict(hip=hip, knee=knee, ankle=ankle, hand=hand, out=out, l1=l1, l2=l2, bend=bend)


def _perp(d):
    """Deux directions perpendiculaires à d : e1 vers l'extérieur (X), e2 qui complète."""
    e1 = np.array([1.0, 0, 0]) - d[0] * d
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(d, e1)


def _plates(rng, a, b, rad, rows, per_row, ln, w):
    """Plaques de cristal qui se chevauchent le long d'un os (de a vers b), comme des écailles :
    chaque lame part de la surface et file vers le bout du membre en s'écartant un peu."""
    d = b - a
    L = np.linalg.norm(d); d = d / L
    e1, e2 = _perp(d)
    out = []
    for i in range(rows):
        t = (i + 0.2) / rows
        for j in range(per_row):
            ang = 2 * math.pi * (j + 0.5 * (i % 2)) / per_row + rng.uniform(-0.25, 0.25)
            radial = e1 * math.cos(ang) + e2 * math.sin(ang)
            tang = np.cross(d, radial)
            root = a + d * (t * L) + radial * rad(t) * 0.8
            out.append(flame(rng, root, radial, tang, d, ln * rng.uniform(0.85, 1.2), w, 0.9, 1.0, 0.4, 0.3, pts=4))
    return out


def _claw_hand(rng, ankle, hand, out, big):
    """Main en serres : paume épaisse, trois longs doigts écartés, griffes recourbées, un pouce opposé.
    Le dos de la main est calculé pareil des deux côtés (sinon une main se plie à l'envers)."""
    up = np.cross(np.array([1.0, 0, 0]), hand)         # dos de la main : vers l'avant et le haut
    up /= np.linalg.norm(up)
    parts = [_oriented(*blob(ankle + hand * 0.35, 0.5 * big, scale=(1.1, 0.7, 1.2), jitter=0.06, rng=rng, subdiv=1))]
    for k, spread in enumerate((-0.6, 0.0, 0.6)):
        d = hand * math.cos(spread) + out * math.sin(spread)
        d /= np.linalg.norm(d)
        ln = (2.1 if k == 1 else 1.8) * big
        p0 = ankle + hand * 0.4
        p1 = p0 + d * ln * 0.55 + up * 0.2
        p2 = p1 + (d * 0.95 - up * 0.3) * ln * 0.45
        tip = p2 + (d * 0.6 - up * 0.8) * 0.95 * big
        parts.append(_oriented(*tube([p0, p1, p2], [0.36 * big, 0.3 * big, 0.24 * big], 5)))
        parts.append(_oriented(*tube([p2, (p2 + tip) / 2 + d * 0.15 * big, tip], [0.22 * big, 0.14 * big, 0], 4, tip=True)))
        # petite plaque sur le dos de chaque doigt
        parts.append(flame(rng, p0 + up * 0.25 * big, up, np.cross(d, up), d, ln * 0.6, 0.22 * big, 0.3, 0.3, 0.2, 0.2, pts=4))
    p0 = ankle + hand * 0.2
    p1 = p0 - up * 0.95 * big - hand * 0.15
    tip = p1 + hand * 0.7 * big - up * 0.2
    parts.append(_oriented(*tube([p0, p1, tip], [0.28 * big, 0.18 * big, 0], 4, tip=True)))
    return parts


def leg_parts(rng, P, side, front):
    """Renvoie (bras/cuisse, ses plaques, avant-bras/tibia, ses plaques, main/pied) en listes de (v, f), repère monde.
    Les plaques sont à part pour avoir la couleur des lames (bleu clair) dans Roblox.
    Membres plus épais qu'au début de la v5 et couverts de plaques de cristal, comme sur la vidéo."""
    hip, knee, ankle = P["hip"], P["knee"], P["ankle"]
    k = 1.0 if front else 1.15
    r1 = lambda t: (1.5 - 0.6 * t) * k
    r2 = lambda t: (0.85 - 0.25 * t) * k
    upper = [_oriented(*tube([hip, (hip + knee) / 2, knee], [r1(0), r1(0.5), r1(1)], 7, jitter=0.08, rng=rng))]
    upper.append(_oriented(*blob(knee, r1(1) * 1.05, jitter=0.05, rng=rng, subdiv=0)))   # coude / genou
    shin = [_oriented(*tube([knee, (knee + ankle) / 2, ankle], [r2(0), r2(0.5) * 1.1, r2(1)], 6, jitter=0.08, rng=rng))]
    upper_pl = _plates(rng, hip, knee, r1, 2, 3, 2.8, 0.6 * k)
    shin_pl = _plates(rng, knee, ankle, r2, 3, 3, 2.4, 0.5 * k)
    # pointe de cristal au coude (vers l'arrière) ou au talon (vers l'arrière aussi)
    spike_dir = np.array([0, 0.1, 1.0]); spike_dir /= np.linalg.norm(spike_dir)
    shin_pl.append(_oriented(*tube([knee, knee + spike_dir * 1.3 + [0, 0.15, 0], knee + spike_dir * 2.6],
                                [0.4, 0.25, 0], 4, tip=True)))
    if not front:                                # ergot au talon
        shin_pl.append(_oriented(*tube([ankle, ankle + spike_dir * 0.9, ankle + spike_dir * 1.8 + [0, 0.3, 0]],
                                    [0.3, 0.18, 0], 4, tip=True)))
    foot = _claw_hand(rng, ankle, P["hand"], P["out"], 1.45 if front else 1.4)
    return upper, upper_pl, shin, shin_pl, foot


# ---------------- assemblage ----------------

def dragon_cristal_v5(name="Dragon_Cristal_v5", seed=57):
    rng = np.random.default_rng(seed)
    pts = spine()
    a = Asset(name)
    col_b, mat_b = STYLE["body"]
    col_l, mat_l = STYLE["blades"]
    meta = {"chain": [p.tolist() for p in pts], "legs": {}, "ground": 0.0}

    # tête v4 (avec la gueule sombre et les dents à part), dans l'axe du cou
    Mh, oh = frame(pts, 0) @ rot_matrix_x(HEAD_PITCH) @ HEAD_WIDEN * HEAD_SCALE, pts[0] + np.array([0, 0.4, -3.6])
    for nm, lst in head5(rng).items():
        c, m = STYLE[HEAD_STYLE[nm]]
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
            upper, upper_pl, shin, shin_pl, foot = leg_parts(rng, P, side, front)
            for suffix, lst, c, m in (("", upper, col_b, mat_b), ("_Blades", upper_pl, col_l, mat_l),
                                      ("_Shin", shin, col_b, mat_b), ("_Shin_Blades", shin_pl, col_l, mat_l),
                                      ("_Foot", foot, col_b, mat_b)):
                for v, f in lst:
                    a.add(nm + suffix, v, f, c, m)
            meta["legs"][nm] = {"seg": seg, "front": front, "side": side,
                                **{k: (P[k].tolist() if isinstance(P[k], np.ndarray) else P[k])
                                   for k in ("hip", "knee", "ankle", "hand", "l1", "l2", "bend")}}
    a.meta = meta
    return a


def all_assets():
    return [dragon_cristal_v5()]
