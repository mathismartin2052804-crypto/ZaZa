# Course du dragon v6 refaite : galop lourd, pieds posés au sol, corps qui ne rebondit plus.
#   - chaque patte suit une vraie trajectoire de pied : appui (le pied reste à plat au sol et recule à vitesse
#     constante, le talon se décolle en fin d'appui en roulant sur les orteils) puis lever (arc rapide, patte
#     repliée, orteils tendus vers l'avant juste avant de reposer)
#   - les angles des pattes sont calculés par cinématique inverse (IK 2 os dans le plan de la patte + pied orienté
#     dans le monde), puis échantillonnés (ECH points par foulée) : demo_animations_v6.py et AnimDragon.lua lisent
#     la même table avec la même interpolation (Catmull-Rom périodique), donc Roblox = générateur
#   - corps : petit balancement (0,1 stud) et léger va-et-vient au lieu du rebond, dos qui se plie une fois par foulée,
#     tête stabilisée (elle compense le tangage du tronc), cou et queue en retard, ailes repliées qui tressautent
# Le dragon court sur place : le jeu le fait avancer à VITESSE studs/s pour que les pieds ne patinent pas.
import numpy as np
import rendu
import rig_v6 as RG

DUREE = 2.2                  # secondes par boucle (comme avant)
FOULEES = 2                  # foulées par boucle
BETA = 0.45                  # part de la foulée où le pied est au sol
PAS = 3.6                    # distance parcourue par le pied au sol pendant l'appui (studs)
LEVE = {"Front": 1.3, "Back": 1.1}       # hauteur de lever du pied
# galop transversal : arrière gauche, arrière droite, avant gauche, avant droite (fraction de foulée)
PHASE = {"BackL": 0.0, "BackR": 0.11, "FrontL": 0.46, "FrontR": 0.57}
SOL = -0.62                  # dessous des pattes au repos (y)
PIVOT_Z = {"Front": -5.65, "Back": 1.85}  # bout des griffes : le pied roule dessus (z, au repos)
CENTRE_Z = {"Front": -0.3, "Back": 0.3}  # centre de l'appui par rapport au repos (le pied se pose un peu devant)
ECH = 48                     # échantillons par foulée
VITESSE = PAS / (BETA * DUREE / FOULEES)  # studs/s à donner au dragon en jeu
JAMBES = ("FrontUpperLeg", "FrontLowerLeg", "FrontFoot", "BackUpperLeg", "BackLowerLeg", "BackFoot")


def smooth(q):
    """Profil sans à-coups (vitesse et accélération nulles aux bouts)."""
    q = np.clip(q, 0, 1)
    return q ** 3 * (10 - 15 * q + 6 * q * q)


def corps(s):
    """Pose du tronc, du cou, de la tête, de la queue et des ailes repliées ; s = phase de foulée (0..1)."""
    ph = 2 * np.pi * s
    P = {}
    P["Root"] = (2.0 * np.sin(ph - 0.4), 2.5 * np.sin(ph), 1.2 * np.sin(ph + 0.3))
    P["Spine"] = (-3.0 * np.sin(ph + 0.3), -2.0 * np.sin(ph + 0.5), 0)
    P["Chest"] = (1.8 * np.sin(ph + 1.0), -1.5 * np.sin(ph + 0.9), -0.8 * np.sin(ph + 0.9))
    P["Neck1"] = (-7 + 2.5 * np.sin(ph + 1.6), 1.5 * np.sin(ph + 1.3), 0)
    P["Neck2"] = (-3 + 1.5 * np.sin(ph + 2.0), 1.0 * np.sin(ph + 1.7), 0)
    P["Neck3"] = (1.0 * np.sin(ph + 2.4), 0, 0)
    # tête stabilisée : compense presque tout le tangage et le lacet accumulés
    tang = sum(P[n][0] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3"))
    lac = sum(P[n][1] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2"))
    P["Head"] = (-0.85 * tang - 8 + 1.0 * np.sin(ph + 2.8), -0.7 * lac, -0.6 * (P["Root"][2] + P["Chest"][2]))
    P["Jaw"] = (-6 - 4 * (0.5 + 0.5 * np.sin(ph + 2.2)), 0, 0)          # halète
    P["WingUpperR"] = (0, -38, -22 + 3 * np.sin(ph - 0.8))
    P["WingUpperL"] = (0, 38, 22 - 3 * np.sin(ph - 0.8))
    P["WingLowerR"] = (0, -68, 2 * np.sin(ph - 1.4))
    P["WingLowerL"] = (0, 68, -2 * np.sin(ph - 1.4))
    for i in range(6):                                                    # vague qui part du bassin, amplifiée au bout
        P[f"Tail{i + 1}"] = (-1.5 + 2.5 * np.sin(ph - 0.6 * i - 0.8) + 0.6 * np.sin(2 * ph - 0.9 * i),
                             (3 + 1.2 * i) * np.sin(ph - 0.75 * i - 0.5), 0)
    off = np.array([0, -0.32 + 0.1 * np.cos(ph - 2 * np.pi * 0.78), 0.12 * np.sin(ph - 1.2)])
    return P, off


def pied(u, kind):
    """Pied selon la phase u de la patte : (dz, dy) du pivot des orteils et levée du talon (degrés)."""
    if u < BETA:                                           # appui : recule à vitesse constante, à plat
        q = u / BETA
        dz = CENTRE_Z[kind] - PAS / 2 + PAS * q
        talon = 55 * smooth((q - 0.7) / 0.3)               # roule sur les orteils en fin d'appui
        return dz, 0.0, talon
    q = (u - BETA) / (1 - BETA)                            # lever : revient vers l'avant
    dz = CENTRE_Z[kind] + PAS / 2 - PAS * smooth(q)
    dy = LEVE[kind] * np.sin(np.pi * smooth(q) ** 0.75)
    replie = 85 if kind == "Front" else 60
    talon = 55 + (replie - 55) * smooth(q / 0.35) - (replie + 8) * smooth((q - 0.35) / 0.5) + 8 * smooth((q - 0.85) / 0.15)
    dy += 0.02 * max(0.0, -talon)                         # orteils relevés : le talon ne touche pas le sol
    return dz, dy, talon


def angle(v):
    return np.arctan2(v[2], v[1])                          # angle dans le plan (y, z) ; Rx(a) ajoute a


def quat(R):
    """Matrice de rotation -> quaternion (x, y, z, w)."""
    w = np.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = np.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2 * np.sign(R[2, 1] - R[1, 2] or 1)
    y = np.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2 * np.sign(R[0, 2] - R[2, 0] or 1)
    z = np.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2 * np.sign(R[1, 0] - R[0, 1] or 1)
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


def mat(q):
    """Quaternion (x, y, z, w), normalisé ici -> matrice (comme CFrame.new(0, 0, 0, x, y, z, w))."""
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class _Os:
    """Squelette seul (sans maillage) pour calculer les matrices vite."""
    def __init__(self):
        self.bones = RG.skeleton()
        self.index = {b[0]: i for i, b in enumerate(self.bones)}

    matrices = RG.Rig.matrices


def ik(sk, G, kind, sd, cible, R_pied):
    """Angles (degrés) du haut et du bas de la patte pour mettre le poignet/jarret sur cible, et pied orienté."""
    up, low, foot = (n + sd for n in (kind + ("UpperLeg"), kind + "LowerLeg", kind + "Foot"))
    Sh, El, Wr = (np.asarray(sk.bones[sk.index[n]][2], float) for n in (up, low, foot))
    par = sk.bones[sk.index[up]][1]
    Gp = G[sk.index[par]]
    T = np.linalg.solve(Gp, np.append(cible, 1))[:3]       # cible dans le repère de repos du parent
    a, b = (El - Sh)[1:], (Wr - El)[1:]
    l1, l2 = np.linalg.norm(a), np.linalg.norm(b)
    d_v = (T - Sh)[1:]
    d = np.clip(np.linalg.norm(d_v), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    sens = np.sign(a[0] * (Wr - Sh)[2] - a[1] * (Wr - Sh)[1])        # côté où plie l'articulation au repos
    alpha = np.arccos(np.clip((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    a1 = angle(np.r_[0, d_v]) - sens * alpha - angle(np.r_[0, a])
    R1 = rendu.rot(np.degrees(a1), 0, 0)
    E2 = Sh + R1 @ (El - Sh)
    a2 = angle(np.r_[0, (T - E2)[1:]]) - angle(np.r_[0, (R1 @ (Wr - El))[1:]])
    R2 = rendu.rot(np.degrees(a2), 0, 0)
    Rf = (Gp[:3, :3] @ R1 @ R2).T @ R_pied                 # pied : orientation voulue dans le monde
    return np.degrees(a1), np.degrees(a2), quat(Rf)


def bake():
    """Table (ECH, 4 pattes x 6 valeurs) : haut, bas (degrés), pied (quaternion x, y, z, w) ;
    avant R, avant L, arrière R, arrière L."""
    sk = _Os()
    tab = np.zeros((ECH, 6 * 4))
    for k in range(ECH):
        s = k / ECH
        P, off = corps(s)
        G = sk.matrices(P, off)
        col = 0
        for kind in ("Front", "Back"):
            for sd, x in (("R", 1), ("L", -1)):
                u = (s - PHASE[kind + sd]) % 1
                dz, dy, talon = pied(u, kind)
                foot = kind + "Foot" + sd
                Wr = np.asarray(sk.bones[sk.index[foot]][2], float)
                piv = np.array([Wr[0], SOL, PIVOT_Z[kind]])
                Rp = rendu.rot(-talon, 0, 0)               # talon qui monte = l'avant du pied qui descend
                cible = piv + [0, dy, dz] + Rp @ (Wr - piv)
                a1, a2, q = ik(sk, G, kind, sd, cible, Rp)
                v = np.array([a1, a2])
                ref = tab[k - 1, col:col + 2] if k else np.zeros(2)
                v -= 360 * np.round((v - ref) / 360)        # pas de saut de 360° d'un échantillon à l'autre
                if k and q @ tab[k - 1, col + 2:col + 6] < 0:
                    q = -q                                 # même rotation, signe qui reste continu
                tab[k, col:col + 6] = (*v, *q)
                col += 6
    return tab


def catmull(tab, s):
    """Interpolation Catmull-Rom périodique de la table à la phase s."""
    x = (s % 1) * len(tab)
    i = int(np.floor(x)) % len(tab)
    f = x - np.floor(x)
    p0, p1, p2, p3 = (tab[(i + j) % len(tab)] for j in (-1, 0, 1, 2))
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)


TABLE = np.round(bake(), 4)       # arrondie comme dans AnimDragon.lua


def pose(t):
    """Pose complète à l'instant t de la boucle (0..1) et décalage du bassin."""
    s = (t * FOULEES) % 1
    P, off = corps(s)
    v = catmull(TABLE, s)
    col = 0
    for kind in ("Front", "Back"):
        for sd in ("R", "L"):
            P[kind + "UpperLeg" + sd] = (v[col], 0, 0)
            P[kind + "LowerLeg" + sd] = (v[col + 1], 0, 0)
            P[kind + "Foot" + sd] = mat(v[col + 2:col + 6])
            col += 6
    return P, off
