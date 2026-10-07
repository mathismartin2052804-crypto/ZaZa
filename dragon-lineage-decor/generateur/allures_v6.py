# Allures du dragon v6 : course (galop lourd) et marche (pas à 4 temps), pieds posés au sol.
#   - chaque patte suit une vraie trajectoire de pied : appui (le pied reste à plat au sol et recule à vitesse
#     constante, le talon se décolle en fin d'appui en roulant sur les griffes) puis lever (arc, patte repliée,
#     orteils tendus vers l'avant juste avant de reposer) ; angles calculés par cinématique inverse (IK 2 os dans
#     le plan de la patte + pied orienté dans le monde)
#   - course v2 : le corps s'enfonce un peu à chaque réception (arrière puis avant) et s'allège pendant la suspension
#     au lieu d'osciller en sinus, dos qui se ramasse et s'étend, foulée plus longue, ailes repliées qui s'entrouvrent
#     pendant la suspension (équilibre), queue en contrepoids du tangage, tête stabilisée
#   - marche : pas latéral (arrière G, avant G, arrière D, avant D), poids qui passe d'un côté à l'autre (roulis),
#     dos en S, tête qui hoche à chaque pose d'une patte avant, queue qui balaie
#   - toute la pose est échantillonnée (ECH points par foulée) : demo_animations_v6.py et AnimDragon.lua lisent les
#     mêmes tables avec la même interpolation (Catmull-Rom périodique), donc Roblox = générateur
# Le dragon avance sur place : le jeu le déplace à allure.vitesse studs/s (AnimDragon : d:setSpeed(v) choisit
# l'allure et cale la cadence pour que les pieds ne patinent pas).
import numpy as np
import rendu
import rig_v6 as RG

SOL = -0.62                  # dessous des pattes avant au repos (y)
PIVOT_Z = {"Front": -5.65, "Back": 1.85}  # bout des griffes : le pied roule dessus (z, au repos)
ECH = 48                     # échantillons par foulée
JAMBES = [k + n + sd for k in ("Front", "Back") for sd in ("R", "L") for n in ("UpperLeg", "LowerLeg", "Foot")]


def smooth(q):
    """Profil sans à-coups (vitesse et accélération nulles aux bouts)."""
    q = np.clip(q, 0, 1)
    return q ** 3 * (10 - 15 * q + 6 * q * q)


def bump(s, c, w):
    """Bosse périodique centrée sur la phase c, de largeur w."""
    d = (s - c + 0.5) % 1 - 0.5
    return np.exp(-(d / w) ** 2)


def stabilise(P, k=0.85, base=-8.0, extra=0.0):
    """Tête qui compense le tangage, le lacet et le roulis accumulés par le tronc et le cou."""
    tang = sum(P[n][0] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3"))
    lac = sum(P[n][1] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2"))
    P["Head"] = (-k * tang + base + extra, -0.7 * lac, -0.6 * (P["Root"][2] + P["Chest"][2]))


def ailes_repliees(P, haut=0.0, bas=0.0):
    P["WingUpperR"], P["WingUpperL"] = (0, -38, -22 + haut), (0, 38, 22 - haut)
    P["WingLowerR"], P["WingLowerL"] = (0, -68, bas), (0, 68, -bas)


def corps_course(s):
    ph = 2 * np.pi * s
    P = {}
    # réceptions : arrière vers s≈0.15, avant vers s≈0.65 ; suspension vers s≈0.97
    charge_ar, charge_av, susp = bump(s, 0.15, 0.12), bump(s, 0.65, 0.12), bump(s, 0.97, 0.07)
    P["Root"] = (3.0 * bump(s, 0.38, 0.14) - 2.0 * charge_av + 1.0 * susp, 2.2 * np.sin(ph), 1.2 * np.sin(ph + 0.3))
    P["Spine"] = (-4.5 * np.sin(ph + 0.2), -2.0 * np.sin(ph + 0.5), 0)          # dos qui se ramasse / s'étend
    P["Chest"] = (2.5 * np.sin(ph + 0.9) - 1.5 * charge_av, -1.5 * np.sin(ph + 0.9), -0.8 * np.sin(ph + 0.9))
    P["Neck1"] = (-7 + 2.5 * np.sin(ph + 1.6) - 2.0 * charge_av, 1.5 * np.sin(ph + 1.3), 0)
    P["Neck2"] = (-3 + 1.5 * np.sin(ph + 2.0), 1.0 * np.sin(ph + 1.7), 0)
    P["Neck3"] = (1.0 * np.sin(ph + 2.4), 0, 0)
    stabilise(P, extra=1.0 * np.sin(ph + 2.8))
    P["Jaw"] = (-6 - 4 * (0.5 + 0.5 * np.sin(ph + 2.2)), 0, 0)              # halète
    ailes_repliees(P, 3 * np.sin(ph - 0.8) + 7 * susp, 2 * np.sin(ph - 1.4) + 6 * bump(s, 0.02, 0.08))
    tang = P["Root"][0]
    for i in range(6):                         # contrepoids du tangage (en retard) + vague latérale
        P[f"Tail{i + 1}"] = (-1.5 - 0.6 * tang * (i < 3) + 2.5 * np.sin(ph - 0.6 * i - 0.8)
                             + 0.6 * np.sin(2 * ph - 0.9 * i), (3 + 1.2 * i) * np.sin(ph - 0.75 * i - 0.5), 0)
    off = np.array([0, -0.30 - 0.10 * charge_ar - 0.12 * charge_av + 0.07 * susp, 0.14 * np.sin(ph - 1.2)])
    return P, off, 0.15


def corps_marche(s):
    ph = 2 * np.pi * s
    P = {}
    pose_av = bump(s, 0.3, 0.08) + bump(s, 0.8, 0.08)                       # une patte avant se pose
    P["Root"] = (0.8 * np.sin(2 * ph + 0.5), 3.0 * np.sin(ph), 2.2 * np.sin(ph - 0.3))   # roulis : le poids passe
    P["Spine"] = (-0.8 * np.sin(2 * ph + 1.0), -3.0 * np.sin(ph + 0.6), -0.8 * np.sin(ph))   # dos en S
    P["Chest"] = (-1.0 * pose_av, -2.5 * np.sin(ph + 1.2), -1.2 * np.sin(ph + 0.5))
    P["Neck1"] = (-6 - 2.0 * pose_av, 2.0 * np.sin(ph + 1.8), 0)
    P["Neck2"] = (-3 - 1.0 * pose_av, 1.5 * np.sin(ph + 2.2), 0)
    P["Neck3"] = (0.6 * np.sin(2 * ph + 2.0), 0, 0)
    stabilise(P, k=0.7, base=-6.0, extra=-1.5 * pose_av)                     # hoche la tête à chaque pas avant
    P["Jaw"] = (-2.5 - 0.5 * np.sin(ph), 0, 0)
    ailes_repliees(P, 1.5 * np.sin(ph - 0.8), 1.0 * np.sin(ph - 1.4))
    for i in range(6):
        P[f"Tail{i + 1}"] = (-1.0 + 1.0 * np.sin(2 * ph - 0.6 * i), (4 + 1.6 * i) * np.sin(ph - 0.7 * i - 0.6), 0)
    off = np.array([0, -0.08 - 0.05 * np.cos(2 * ph - 0.6), 0.06 * np.sin(2 * ph)])
    return P, off, 0.05


class Allure:
    def __init__(self, nom, duree, foulees, beta, pas, leve, phase, centre, talon, replie, corps):
        self.nom, self.duree, self.foulees, self.beta, self.pas = nom, duree, foulees, beta, pas
        self.leve, self.phase, self.centre, self.talon, self.replie, self.corps = leve, phase, centre, talon, replie, corps
        self.vitesse = pas / (beta * duree / foulees)          # studs/s pour que les pieds ne patinent pas
        self.bones, self.table = None, None

    def pied(self, u, kind):
        """Pied selon la phase u de la patte : (dz, dy) du pivot des griffes et levée du talon (degrés)."""
        B, S, c = self.beta, self.pas, self.centre[kind]
        if u < B:                                              # appui : recule à vitesse constante, à plat
            q = u / B
            return c - S / 2 + S * q, 0.0, self.talon * smooth((q - 0.7) / 0.3)
        q = (u - B) / (1 - B)                                  # lever : revient vers l'avant
        dz = c + S / 2 - S * smooth(q)
        dy = self.leve[kind] * np.sin(np.pi * smooth(q) ** 0.75)
        r, t0 = self.replie[kind], self.talon
        talon = t0 + (r - t0) * smooth(q / 0.35) - (r + 8) * smooth((q - 0.35) / 0.5) + 8 * smooth((q - 0.85) / 0.15)
        dy += 0.02 * max(0.0, -talon)                         # orteils relevés : le talon ne touche pas le sol
        return dz, dy, talon

    def bake(self):
        """Table (ECH, colonnes) : (ex, ey, ez) des os du corps, angles haut/bas des pattes, pied en quaternion,
        puis le décalage du bassin (x, y, z) et les paupières."""
        sk = _Os()
        rows, legs = [], []
        for k in range(ECH):
            s = k / ECH
            P, off, lid = self.corps(s)
            G = sk.matrices(P, off)
            row = []
            for kind in ("Front", "Back"):
                for sd in ("R", "L"):
                    u = (s - self.phase[kind + sd]) % 1
                    dz, dy, talon = self.pied(u, kind)
                    Wr = np.asarray(sk.bones[sk.index[kind + "Foot" + sd]][2], float)
                    piv = np.array([Wr[0], SOL, PIVOT_Z[kind]])
                    Rp = rendu.rot(-talon, 0, 0)               # talon qui monte = l'avant du pied qui descend
                    a1, a2, q = ik(sk, G, kind, sd, piv + [0, dy, dz] + Rp @ (Wr - piv), Rp)
                    row += [(a1 + 180) % 360 - 180, (a2 + 180) % 360 - 180, *q]
            legs.append(row)
            rows.append((P, off, lid))
        self.bones = [b[0] for b in sk.bones if b[0] in rows[0][0]]
        body = np.array([[c for n in self.bones for c in P[n]] + list(off) + [lid] for P, off, lid in rows])
        legs = np.array(legs)
        for k in range(1, ECH):                                # continuité : pas de saut de 360°, quaternions de même signe
            for c in range(0, legs.shape[1], 6):
                legs[k, c:c + 2] -= 360 * np.round((legs[k, c:c + 2] - legs[k - 1, c:c + 2]) / 360)
                if legs[k, c + 2:c + 6] @ legs[k - 1, c + 2:c + 6] < 0:
                    legs[k, c + 2:c + 6] *= -1

        self.table = arrondi(np.concatenate([body, legs], 1), 3 * len(self.bones), 4)
        return self

    def pose(self, t):
        """Pose complète à l'instant t de la boucle (0..1), décalage du bassin, paupières."""
        v = catmull(self.table, (t * self.foulees) % 1)
        P, c = {}, 0
        for n in self.bones:
            P[n] = tuple(v[c:c + 3]); c += 3
        off, lid = v[c:c + 3], v[c + 3]; c += 4
        for kind in ("Front", "Back"):
            for sd in ("R", "L"):
                P[kind + "UpperLeg" + sd] = (v[c], 0, 0)
                P[kind + "LowerLeg" + sd] = (v[c + 1], 0, 0)
                P[kind + "Foot" + sd] = mat(v[c + 2:c + 6])
                c += 6
        return P, off, lid


def arrondi(tab, nb_angles, nb_extra):
    """Angles au centième de degré, le reste (bassin, paupières, quaternions) au dix-millième : AnimDragon.lua
    contient exactement ces valeurs."""
    tab = np.round(tab, 4)
    tab[:, :nb_angles] = np.round(tab[:, :nb_angles], 2)
    for c in range(nb_angles + nb_extra, tab.shape[1], 6):
        tab[:, c:c + 2] = np.round(tab[:, c:c + 2], 2)
    return tab + 0.0                                         # pas de -0


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


def catmull(tab, s):
    """Interpolation Catmull-Rom périodique de la table à la phase s."""
    x = (s % 1) * len(tab)
    i = int(np.floor(x)) % len(tab)
    f = x - np.floor(x)
    p0, p1, p2, p3 = (tab[(i + j) % len(tab)] for j in (-1, 0, 1, 2))
    return 0.5 * (2 * p1 + (p2 - p0) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f
                  + (3 * p1 - p0 - 3 * p2 + p3) * f ** 3)



# galop transversal : arrière gauche, arrière droite, avant gauche, avant droite (fraction de foulée)
COURSE = Allure("Course", duree=2.2, foulees=2, beta=0.42, pas=4.0, leve={"Front": 1.5, "Back": 1.2},
                phase={"BackL": 0.0, "BackR": 0.11, "FrontL": 0.46, "FrontR": 0.57},
                centre={"Front": -0.45, "Back": 0.3}, talon=55, replie={"Front": 90, "Back": 62},
                corps=corps_course).bake()
# pas latéral à 4 temps
MARCHE = Allure("Marche", duree=1.7, foulees=1, beta=0.68, pas=2.8, leve={"Front": 0.9, "Back": 0.7},
                phase={"BackL": 0.0, "FrontL": 0.25, "BackR": 0.5, "FrontR": 0.75},
                centre={"Front": -0.2, "Back": 0.2}, talon=35, replie={"Front": 60, "Back": 40},
                corps=corps_marche).bake()
ALLURES = {"Course": COURSE, "Marche": MARCHE}
