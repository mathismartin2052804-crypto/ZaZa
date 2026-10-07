# Animations « une fois » du dragon v6 : décollage, atterrissage, souffle de feu.
#   Même principe que les allures (allures_v6.py) : les pieds qui touchent le sol y restent posés par IK pendant
#   que le corps s'accroupit, se cabre ou encaisse la réception ; toute la pose est échantillonnée en table (ECH
#   points) et AnimDragon.lua la rejoue avec la même interpolation (Catmull-Rom, bouts bloqués).
#   - Décollage : s'accroupit en ouvrant les ailes, pousse sur les pattes (roule sur les griffes), premier grand
#     battement, monte et replie les pattes ; finit sur la pose de départ de « Vol »
#   - Atterrissage : descend ailes en frein, pattes tendues vers le sol, touche (arrière puis avant), encaisse
#     (le corps s'enfonce, les pattes plient), replie les ailes
#   - Souffle de feu : inspire (se cabre, gorge qui s'allume), puis crache en balayant de gauche à droite,
#     gueule grande ouverte ; canal « feu » pour allumer les particules dans Roblox
# Canaux par échantillon : os du corps (ex, ey, ez), bassin (x, y, z), paupières, lueur de gorge (0..1+),
# feu (0..1), puis les 4 pattes (haut, bas en degrés, pied en quaternion).
import numpy as np
import rendu
import allures_v6 as AL
import demo_animations_v6 as D

ECH = 64
smooth = AL.smooth


def ease(a, b, t):
    return D.ease(a, b, t)


def sides(P, name, v):
    P.update(D.sides(name, v))


def sol(dy=0.0, dz=0.0, talon=0.0):
    """Les 4 pieds : (dz, dy, talon) identiques (dy au-dessus du sol, talon en degrés)."""
    return {k + sd: (dz, dy, talon) for k in ("Front", "Back") for sd in ("R", "L")}


# ---------- décollage ----------
def decollage(t):
    c = ease(0.0, 0.3, t) * (1 - ease(0.38, 0.46, t))          # accroupi
    j = ease(0.38, 0.5, t)                                     # impulsion
    y = -1.0 * c + 4.5 * ease(0.4, 0.95, t) ** 1.2
    P = {"Root": (-3 * c + 7 * j * (1 - ease(0.6, 0.9, t)) - 4 * ease(0.6, 0.9, t), 0, 0),
         "Spine": (2 * c - 3 * j * (1 - ease(0.6, 0.9, t)), 0, 0), "Chest": (3 * c - 2 * j, 0, 0),
         "Neck1": (6 * c - 4 * j - 4 * ease(0.6, 0.9, t), 0, 0), "Neck2": (4 * c - 2 * j, 0, 0),
         "Neck3": (2 * c, 0, 0), "Head": (6 * c - 3 * j + 6 * ease(0.6, 0.9, t), 0, 0), "Jaw": (-3 - 4 * j, 0, 0)}
    o = ease(0.02, 0.32, t)                                     # ailes qui se déplient
    bat = np.interp(t, [0, 0.3, 0.4, 0.52, 0.66, 0.8, 0.92, 1.0], [0, 45, 50, -35, 42, -22, 12, 8])
    bat2 = np.interp(t, [0, 0.3, 0.44, 0.58, 0.72, 0.86, 1.0], [0, 20, 25, -30, 25, -18, -23])
    sides(P, "WingUpper", (0, -38 * (1 - o) + 4 * o, -22 * (1 - o) + bat * o))
    sides(P, "WingLower", (0, -68 * (1 - o) + 6 * o, bat2 * o))
    for k in range(4):
        sides(P, f"WingFinger{k + 1}", (0, 3 * k * np.cos(-1.2) * o, (10 * np.sin(-1.3 - 0.2 * k) + 0.3 * bat2) * o))
    for i in range(6):
        P[f"Tail{i + 1}"] = (-4 * c + 6 * j * np.sin(np.pi * ease(0.4, 0.9, t)) - 3 * i * ease(0.5, 0.8, t) * 0.3, 0, 0)
    talon = 55 * ease(0.36, 0.5, t)                             # pousse sur les griffes
    pieds = sol(dy=max(0.0, y - 0.9), talon=talon)
    return P, np.array([0, y, 0.6 * j * (1 - ease(0.6, 1, t))]), 0.1 + 0.3 * c, 0.0, 0.0, pieds


# ---------- atterrissage ----------
def atterrissage(t):
    y = np.interp(t, [0, 0.25, 0.42, 0.5, 0.6, 0.85, 1.0], [4.5, 3.2, 1.4, 0.6, -0.75, -0.12, 0.0])
    fr = 1 - ease(0.55, 0.95, t)                                # ailes en frein puis repliées
    bat = np.interp(t, [0, 0.12, 0.3, 0.45, 0.55], [8, 48, -5, 30, 25])
    sides(P := {}, "WingUpper", (0, (12 * fr - 38 * (1 - fr)), bat * fr - 22 * (1 - fr)))
    sides(P, "WingLower", (0, 10 * fr - 68 * (1 - fr), np.interp(t, [0, 0.2, 0.4, 0.55], [-20, 20, -10, 10]) * fr))
    for k in range(4):
        sides(P, f"WingFinger{k + 1}", (0, 4 * k * fr, -6 * fr))
    choc = ease(0.5, 0.6, t) * (1 - ease(0.62, 0.95, t))         # encaisse
    P.update({"Root": (8 * (1 - ease(0.3, 0.55, t)) - 3 * choc, 0, 0), "Spine": (-3 * choc, 0, 0),
              "Chest": (-3 * choc, 0, 0), "Neck1": (-6 + 3 * choc, 0, 0), "Neck2": (-2 + 3 * choc, 0, 0),
              "Neck3": (2 * choc, 0, 0), "Head": (6 - 4 * choc, 0, 0), "Jaw": (-4 + 3 * choc, 0, 0)})
    for i in range(6):
        P[f"Tail{i + 1}"] = (2 - 6 * choc * (i < 3) + 4 * choc * (i >= 3), 3 * np.sin(4 * np.pi * t - 0.7 * i) * fr, 0)
    pieds = {}
    for k, ext, dz in (("Back", 1.1, -0.5), ("Front", 0.9, -0.9)):       # l'arrière touche avant l'avant
        for sd in ("R", "L"):
            pieds[k + sd] = (dz * (1 - ease(0.45, 0.6, t)), max(0.0, y - ext), 30 * (1 - ease(0.45, 0.58, t)))
    return P, np.array([0, y, -0.4 * (1 - ease(0.4, 0.7, t))]), 0.1 + 0.4 * choc, 0.0, 0.0, pieds


# ---------- souffle de feu ----------
def souffle(t):
    i = ease(0.0, 0.3, t) * (1 - ease(0.34, 0.42, t))          # inspire
    f = ease(0.34, 0.42, t) * (1 - ease(0.82, 0.94, t))        # crache
    bal = 16 * np.sin(2 * np.pi * (t - 0.42) / 0.45) * f        # balaie de droite à gauche
    P = {"Root": (5 * i - 3 * f, 0, 0), "Spine": (2 * i - 1 * f, 0, 0), "Chest": (4 * i - 3 * f, 0.2 * bal, 0),
         "Neck1": (6 * i - 4 * f, 0.3 * bal, 0), "Neck2": (6 * i + 1 * f, 0.3 * bal, 0),
         "Neck3": (5 * i + 2 * f, 0.2 * bal, 0), "Head": (10 * i - 6 * f, 0.2 * bal, 0), "Jaw": (-6 * i - 38 * f, 0, 0)}
    sides(P, "WingUpper", (0, -38 + 22 * (i + f), -22 + 40 * i + 30 * f))
    sides(P, "WingLower", (0, -68 + 40 * (i + f), 12 * (i + f)))
    for k in range(4):
        sides(P, f"WingFinger{k + 1}", (0, (k - 1.5) * 5 * (i + f), 3 * f * np.sin(2 * np.pi * t * 9 + k)))
    for k in range(6):
        P[f"Tail{k + 1}"] = (3 * i + 2 * f, -0.6 * bal * (k + 1) / 3 + 3 * np.sin(2 * np.pi * t * 2 - 0.7 * k), 0)
    lueur = 0.7 * i + 1.0 * f
    return P, np.array([0, 0.2 * i - 0.15 * f, 0.3 * i - 0.2 * f]), 0.1 + 0.45 * f, lueur, f, sol()


class Sequence:
    def __init__(self, nom, duree, fn, suite, fin=None, sol=False):
        self.nom, self.duree, self.fn, self.suite, self.fin = nom, duree, fn, suite, fin
        self.sol = sol                     # pieds sur le relief possibles dans Roblox (pas en l'air)
        self.bones, self.table = None, None

    def bake(self):
        sk = AL._Os()
        rest = {b[0]: b for b in sk.bones}
        rows = []
        for k in range(ECH):
            t = k / (ECH - 1)
            P, off, lid, lueur, feu, pieds = self.fn(t)
            G = sk.matrices(P, off)
            legs = []
            for kind in ("Front", "Back"):
                for sd in ("R", "L"):
                    dz, dy, talon = pieds[kind + sd]
                    Wr = np.asarray(rest[kind + "Foot" + sd][2], float)
                    piv = np.array([Wr[0], AL.SOL, AL.PIVOT_Z[kind]])
                    Rp = rendu.rot(-talon, 0, 0)
                    a1, a2, q = AL.ik(sk, G, kind, sd, piv + [0, dy, dz] + Rp @ (Wr - piv), Rp)
                    legs.append([(a1 + 180) % 360 - 180, (a2 + 180) % 360 - 180, *q])   # dans [-180, 180]
            if self.fin is not None:                            # fondu vers la pose de l'animation suivante
                w = ease(self.fin[1], 1.0, t)
                Pf, offf = self.fin[0]()
                for n in set(P) | set(Pf):
                    if n.startswith(("Eyelid", "Pupil")) or "Leg" in n or "Foot" in n:
                        continue
                    P[n] = tuple((1 - w) * np.asarray(P.get(n, (0, 0, 0))) + w * np.asarray(Pf.get(n, (0, 0, 0))))
                off = (1 - w) * off + w * offf
                c = 0
                for kind in ("Front", "Back"):
                    for sd in ("R", "L"):
                        e = [Pf.get(kind + n + sd, (0, 0, 0)) for n in ("UpperLeg", "LowerLeg", "Foot")]
                        qf = AL.quat(rendu.rot(*e[2]))
                        if qf @ legs[c][2:] < 0:
                            qf = -qf
                        legs[c] = [(1 - w) * legs[c][0] + w * e[0][0], (1 - w) * legs[c][1] + w * e[1][0],
                                   *((1 - w) * np.asarray(legs[c][2:]) + w * qf)]
                        c += 1
            rows.append((P, off, lid, lueur, feu, legs))
        names = set().union(*(r[0] for r in rows))
        self.bones = [b[0] for b in sk.bones if b[0] in names]
        tab = []
        for P, off, lid, lueur, feu, legs in rows:
            tab.append([c for n in self.bones for c in P.get(n, (0, 0, 0))] + list(off) + [lid, lueur, feu]
                       + [x for l in legs for x in l])
        tab = np.array(tab, float)
        nb = 3 * len(self.bones) + 6
        for k in range(1, ECH):
            for c in range(nb, tab.shape[1], 6):
                tab[k, c:c + 2] -= 360 * np.round((tab[k, c:c + 2] - tab[k - 1, c:c + 2]) / 360)
                if tab[k, c + 2:c + 6] @ tab[k - 1, c + 2:c + 6] < 0:
                    tab[k, c + 2:c + 6] *= -1
        self.table = AL.arrondi(tab, 3 * len(self.bones), 6)
        return self

    def pose(self, t):
        v = interp(self.table, t)
        P, c = {}, 0
        for n in self.bones:
            P[n] = tuple(v[c:c + 3]); c += 3
        off, lid, lueur, feu = v[c:c + 3], v[c + 3], v[c + 4], v[c + 5]; c += 6
        for kind in ("Front", "Back"):
            for sd in ("R", "L"):
                P[kind + "UpperLeg" + sd] = (v[c], 0, 0)
                P[kind + "LowerLeg" + sd] = (v[c + 1], 0, 0)
                P[kind + "Foot" + sd] = AL.mat(v[c + 2:c + 6])
                c += 6
        return P, off, lid, lueur, feu


def interp(tab, t):
    """Catmull-Rom non périodique (bouts bloqués) ; t de 0 à 1."""
    n = len(tab)
    x = np.clip(t, 0, 1) * (n - 1)
    i = min(int(np.floor(x)), n - 2)
    f = x - i
    p0, p1, p2, p3 = (tab[min(max(i + j, 0), n - 1)] for j in (-1, 0, 1, 2))
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)


DECOLLAGE = Sequence("Decollage", 2.0, decollage, "Vol", fin=(lambda: D.vol(0.0), 0.8)).bake()
ATTERRISSAGE = Sequence("Atterrissage", 1.8, atterrissage, "Repos", fin=(lambda: D.repos(0.0), 0.88)).bake()
SOUFFLE = Sequence("SouffleFeu", 2.8, souffle, "Repos", fin=(lambda: D.repos(0.0), 0.9), sol=True).bake()
SEQUENCES = {s.nom: s for s in (DECOLLAGE, ATTERRISSAGE, SOUFFLE)}
