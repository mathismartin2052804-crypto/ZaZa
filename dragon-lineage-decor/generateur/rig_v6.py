# Rig du dragon v6 : un seul maillage déformé par un squelette (skinning), au lieu de 20 morceaux rigides.
#   - squelette : bassin / dos / poitrail (tronc souple), 3 os de cou, tête, mâchoire, paupières et pupilles,
#     6 os de queue, pattes en 3 os (avant : bras, avant-bras, main ; arrière : cuisse, jambe, pied = 3 morceaux),
#     ailes en 3 os + 4 doigts ; membrane redécoupée et pondérée en douceur sur les mêmes os pour les deux
#     morceaux de l'aile (elle se courbe et reste attachée au flanc au lieu de se casser en se déployant)
#   - poids : par distance aux os autorisés pour chaque morceau d'origine (4 os max par sommet), ce qui adoucit
#     les articulations ; commissures de la gueule partagées entre tête et mâchoire (elles s'étirent à l'ouverture)
#   - pose : rotations locales autour de la tête de chaque os (repères de repos alignés sur le monde),
#     mélange linéaire des transformations (LBS), comme Roblox
#   - lignée : Rig(lignee="Glace") ajoute les ornements de la lignée (lignees_v6.py) sur le même squelette
# Usage : import rig_v6 ; R = rig_v6.Rig(lignee="Feu") ; items = R.items(pose)  (voir demo_animations_v6.py)
import numpy as np
import trimesh
import rendu
import corps_v6 as C6
import corps_v5 as C5
import corps_v4 as V4
import tete_v8 as T8

A = T8.ARCHETYPES[C6.TETE]


def hl(p):
    """Repère tête (déformé) -> monde."""
    return C6.HB + C6.HS * (C6.HEAD_R @ np.asarray(p, float))


def wl(p):
    """Monde -> repère tête."""
    return (np.asarray(p, float) - C6.HB) @ C6.HEAD_R / C6.HS


# ---------- squelette ----------
def skeleton():
    """[(os, parent, tête, bout)] en coordonnées monde au repos."""
    N, T = C6.NECK, C6.TAIL
    B = [("Root", None, (0, 7.0, 2.6), (0, 6.9, 5.0)),
         ("Spine", "Root", (0, 7.2, -0.4), (0, 7.0, 2.6)),
         ("Chest", "Spine", (0, 7.4, -3.2), (0, 7.5, -5.4)),
         ("Neck1", "Chest", N[0], N[2]), ("Neck2", "Neck1", N[2], N[3]), ("Neck3", "Neck2", N[3], tuple(C6.HB)),
         ("Head", "Neck3", tuple(C6.HB), tuple(hl((0, 0.3, -2.6)))),
         ("Jaw", "Head", tuple(hl(T8.PIVOT_M)), tuple(hl((0, -0.45, -2.6))))]
    c, n, u, s = T8.eye_frame(A)
    for sd, x in (("R", 1), ("L", -1)):
        m = np.array([x, 1, 1])
        B.append(("Eyelid" + sd, "Head", tuple(hl(T8.lid_axis(c, n) * m)), tuple(hl((c + n * 0.2) * m))))
        B.append(("Pupil" + sd, "Head", tuple(hl((c - n * 0.3) * m)), tuple(hl((c + n * 0.12) * m))))
    prev = "Root"
    for i in range(6):
        B.append((f"Tail{i + 1}", prev, T[i], T[i + 1])); prev = f"Tail{i + 1}"
    for sd, x in (("R", 1), ("L", -1)):
        F, Bk = C5.legs(x, C6.K)
        W = C5.wing(x, C6.K)
        B += [("FrontUpperLeg" + sd, "Chest", F["shoulder"], F["elbow"]),
              ("FrontLowerLeg" + sd, "FrontUpperLeg" + sd, F["elbow"], F["wrist"]),
              ("FrontFoot" + sd, "FrontLowerLeg" + sd, F["wrist"], tuple(np.add(F["paw"], (0, 0, -1.2)))),
              ("BackUpperLeg" + sd, "Root", Bk["hip"], Bk["knee"]),
              ("BackLowerLeg" + sd, "BackUpperLeg" + sd, Bk["knee"], Bk["hock"]),
              ("BackFoot" + sd, "BackLowerLeg" + sd, Bk["hock"], tuple(np.add(Bk["paw"], (0, 0, -1.2)))),
              ("WingUpper" + sd, "Chest", W["root"], W["elbow"]),
              ("WingLower" + sd, "WingUpper" + sd, W["elbow"], W["wrist"])]
        for j, t in enumerate(W["tips"]):
            B.append((f"WingFinger{j + 1}" + sd, "WingLower" + sd, W["wrist"], t))
    return B


def allowed(part, layer, sd):
    """Os qui peuvent tirer les sommets d'un morceau d'origine."""
    if part == "Torso":
        return ["Root", "Spine", "Chest", "Neck1", "Tail1"]
    if part == "Neck":
        return ["Chest", "Neck1", "Neck2", "Neck3", "Head"]
    if part == "Head":
        if layer == "lid":
            return ["EyelidR", "EyelidL"]
        if layer in ("pupil", "eye"):
            return ["PupilR", "PupilL"] if layer == "pupil" else ["Head"]
        return ["Head"]
    if part == "Jaw":
        return ["Jaw"]
    if part.startswith("Tail"):
        return ["Root"] + [f"Tail{i + 1}" for i in range(6)]
    if part.startswith("Front"):
        return ["Chest"] + [n + sd for n in ("FrontUpperLeg", "FrontLowerLeg", "FrontFoot")]
    if part.startswith("Back"):
        return ["Root"] + [n + sd for n in ("BackUpperLeg", "BackLowerLeg", "BackFoot")]
    if part.startswith("Wing"):                # mêmes os pour les deux morceaux : la membrane reste d'un seul tenant
        return (["Chest", "Spine", "Root"] + [n + sd for n in ("WingUpper", "WingLower")]
                + [f"WingFinger{j + 1}" + sd for j in range(4)])
    raise KeyError(part)


MEMBRANE = ("membrane", "membrane2")
MEMBRANE_SIZE = 0.9        # longueur max d'arête de la membrane avant skinning (studs)
MEMBRANE_POWER = 3.5       # poids plus doux que les os : la membrane s'étire au lieu de se plier net


def soft(m):
    """Membrane redécoupée en petits triangles pour qu'elle se courbe au lieu de casser le long d'une diagonale."""
    V, F = trimesh.remesh.subdivide_to_size(np.asarray(m.vertices), np.asarray(m.faces), MEMBRANE_SIZE)
    out = trimesh.Trimesh(V, F, process=False)
    out.unmerge_vertices()                     # facettes plates, comme le reste du modèle
    return out


def seg_dist(P, a, b):
    ab = np.subtract(b, a)
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


class Rig:
    def __init__(self, model=None, power=6.0, lignee="Feu"):
        import lignees_v6 as L6
        self.lignee = lignee
        self.model = model or L6.orner(C6.build(web=True), lignee)       # ornements propres à la lignée
        self.bones = skeleton()
        self.index = {b[0]: i for i, b in enumerate(self.bones)}
        self.layers = []       # (part, layer, verts, normals, faces, couleurs (slots), émissif, idx (n,4), poids (n,4))
        for part, seg in self.model.items():
            sd = "L" if part.endswith("L") else "R"
            for layer, m in seg["layers"].items():
                slots = seg.get("slots", {}).get(layer)
                pw = power
                if part.startswith("Wing") and layer in MEMBRANE and slots is None:
                    m = soft(m)
                    pw = MEMBRANE_POWER
                V = np.asarray(m.vertices, float)
                idx, w = self.weights(part, layer, sd, V, pw)
                self.layers.append((part, layer, V, np.asarray(m.vertex_normals, float), np.asarray(m.faces),
                                    slots, idx, w))

    def weights(self, part, layer, sd, V, power):
        names = allowed(part, layer, sd)
        if layer in ("lid", "pupil"):          # côté par le signe de x (dans le repère tête)
            side = np.where(wl(V)[:, 0] >= 0, 0, 1)
            idx = np.zeros((len(V), 4), int)
            idx[:, 0] = [self.index[names[s]] for s in side]
            w = np.zeros((len(V), 4)); w[:, 0] = 1
            return idx, w
        D = np.stack([seg_dist(V, self.bones[self.index[n]][2], self.bones[self.index[n]][3]) for n in names], 1)
        W = 1.0 / (D + 0.08) ** power
        if part == "Head" and layer in ("cheek", "mouth", "throat"):
            W = self.mouth_weights(V, layer)
            names = ["Head", "Jaw"]
        k = min(4, W.shape[1])
        top = np.argsort(-W, axis=1)[:, :k]
        tw = np.take_along_axis(W, top, 1)
        tw /= tw.sum(1, keepdims=True)
        idx = np.zeros((len(V), 4), int); w = np.zeros((len(V), 4))
        idx[:, :k] = np.vectorize(lambda j: self.index[names[j]])(top)
        w[:, :k] = tw
        return idx, w

    def mouth_weights(self, V, layer):
        """Commissures : bord du haut sur la tête, bord du bas partagé avec la mâchoire (plus près du fond = plus mâchoire)."""
        L = wl(V)
        if layer == "throat":
            return np.tile([0.45, 0.55], (len(V), 1))
        z = L[:, 2]
        up_y = np.array([T8.T7.crane_at(zz, 5)[1] for zz in z])
        lower = L[:, 1] < up_y - 0.06
        zc = -0.75 * (0.6 + 0.4 * A["L"])
        f = np.clip((z - zc) / (0.25 - zc), 0, 1) ** 0.8          # 1 au fond, 0 au coin de la gueule
        wj = np.where(lower, f, 0.0)
        return np.stack([1 - wj + 1e-9, wj + 1e-9], 1)

    # ---------- pose ----------
    def matrices(self, pose, offset=(0, 0, 0)):
        """pose : {os: matrice 3x3 ou (rx, ry, rz) degrés} autour de la tête de l'os. Renvoie (n, 4, 4)."""
        G = np.zeros((len(self.bones), 4, 4))
        for i, (name, parent, head, _) in enumerate(self.bones):
            R = pose.get(name, np.eye(3))
            R = rendu.rot(*R) if np.shape(R) == (3,) else np.asarray(R)
            h = np.asarray(head, float)
            L = np.eye(4); L[:3, :3] = R; L[:3, 3] = h - R @ h
            if parent is None:
                L[:3, 3] += offset
                G[i] = L
            else:
                G[i] = G[self.index[parent]] @ L
        return G

    def items(self, pose=None, offset=(0, 0, 0), pal=None, black=False):
        pal = pal or C6.palette(self.lignee)
        if black:
            pal = {k: "#000000" for k in pal}
        G = self.matrices(pose or {}, offset)
        out = []
        for part, layer, V, Nn, F, slots, idx, w in self.layers:
            M = np.einsum("nk,nkij->nij", w, G[idx])                 # matrice mélangée par sommet
            v = np.einsum("nij,nj->ni", M[:, :3, :3], V) + M[:, :3, 3]
            n = np.einsum("nij,nj->ni", M[:, :3, :3], Nn)
            col = (np.array([rendu.hex_rgb(pal[s]) for s in slots]) if slots is not None
                   else rendu.hex_rgb(pal.get(layer) or pal["eye"]))
            out.append((v, n, F, col, (layer in C6.EMISSIF) and not black))
        return out


def lid_pose(close, side="R"):
    """Rotation de la paupière (0 = ouverte, 1 = fermée) autour de l'axe de l'œil, en repère monde."""
    _, _, u, _ = T8.eye_frame(A)
    if side == "L":                                # miroir : axe symétrique, sens de rotation inversé
        u = np.array([-u[0], u[1], u[2]])
    ang = -np.radians(T8.LID_CLOSE * close) * (1 if side == "R" else -1)
    return axis_angle(C6.HEAD_R @ u, ang)


def axis_angle(ax, ang):
    ax = np.asarray(ax, float) / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def pupil_axis(side="R"):
    """Axe (monde) pour lever/baisser le regard : perpendiculaire à l'axe de l'œil et à la verticale."""
    sk = {b[0]: b for b in skeleton()}
    _, _, h, t = sk["Pupil" + side]
    ax = np.cross(np.subtract(t, h), (0, 1, 0))           # + = vers le haut, des deux côtés
    return ax / np.linalg.norm(ax)


def pupil_pose(look, up, side="R"):
    """Pupille : regard horizontal (degrés, + = vers la droite du dragon) puis vertical (+ = vers le haut)."""
    return rendu.rot(0, -look, 0) @ axis_angle(pupil_axis(side), np.radians(up))
