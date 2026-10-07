# Lignées du dragon v6 : ce qui différencie Feu, Glace, Forêt et Ombre, au-delà de la couleur.
#   1. Morphologie : ornements propres à chaque lignée, ajoutés sur le même maillage et le même squelette (les
#      animations restent communes) :
#        Feu   : cheminées d'obsidienne sur les épaules et les hanches, fissures de lave lumineuses le long du dos
#        Glace : grappes de cristaux de glace sur le dos, la queue et la nuque, givre sur les cornes
#        Forêt : cornes ramifiées en bois de cerf, feuilles le long du dos et de la queue
#        Ombre : longues épines recourbées sur le dos, runes lumineuses sur les flancs et la queue
#   2. Caractéristiques de jeu (CARAC) : statistiques, souffle (élément, effet, portée…), passif, affinités.
#      Exportées dans LigneesDragon.lua (ModuleScript de données pour les scripts du jeu).
#   3. Style d'animation (STYLE) : façon de voler (durée de la boucle, amplitude, part de vol plané, ondulation, lourdeur)
#      et particules du souffle ; exportés dans AnimDragon.lua.
# Usage : import lignees_v6 as L6 ; L6.orner(model, "Glace") ; L6.CARAC["Glace"] ; L6.STYLE["Glace"]
import numpy as np
import trimesh
from tete_v5 import loft, sweep, curve, blade, cone
import tete_v7 as T7

LIGNEES = ["Feu", "Glace", "Foret", "Ombre"]

# ---------- couleurs des ornements (s'ajoutent à corps_v6.palette) ----------
COULEURS = {
    "Feu": {"obsidienne": "#2A1414", "cristal": "#FFB35A", "bois": "#5A3420", "feuille": "#C8501E", "epine": "#3A1612"},
    "Glace": {"obsidienne": "#20364E", "cristal": "#CFF6FF", "bois": "#7FA8C8", "feuille": "#A8DCF4", "epine": "#E2FAFF"},
    "Foret": {"obsidienne": "#2E2418", "cristal": "#D8FF3A", "bois": "#6B4A2A", "feuille": "#5E9E2E", "epine": "#4A3420"},
    "Ombre": {"obsidienne": "#140E1E", "cristal": "#B48AE8", "bois": "#2A1C3A", "feuille": "#4A2E6E", "epine": "#1E1430"},
}
# cornes recolorées : obsidienne (Feu, bout incandescent), glace (Glace), bois (Forêt), nuit (Ombre)
CORNES = {"Feu": "#3A2622", "Glace": "#DDF4FF", "Foret": "#7A5432", "Ombre": "#2A2036"}
COULEURS_FEUILLE2 = {"Feu": "#E07A2A", "Glace": "#E2FAFF", "Foret": "#8CC23E", "Ombre": "#6A3E9A"}


def couleurs(lin):
    c = dict(COULEURS[lin])
    c["feuille2"] = COULEURS_FEUILLE2[lin]
    c["horn"] = CORNES[lin]
    return c


# ---------- morphologie ----------
def orner(model, lin):
    """Ajoute au modèle (corps_v6.build) les ornements de la lignée, en coordonnées monde, comme nouvelles couches
    des morceaux existants (couleur = nom de la couche) : chaque ornement est pondéré sur les os de son morceau."""
    for part, layers in ORNEMENTS[lin](model).items():
        seg = model[part]
        for layer, meshes in layers.items():
            meshes = [m for m in meshes if m is not None]
            if meshes:
                assert layer not in seg["layers"], (part, layer)
                seg["layers"][layer] = facettes(trimesh.util.concatenate(meshes))
    return model


def facettes(m):
    """Facettes plates, comme le reste du modèle (corps_v4.place)."""
    w = trimesh.Trimesh(np.asarray(m.vertices), np.asarray(m.faces), process=False)
    fn = T7.flat_quads(w)
    w.unmerge_vertices()
    w.vertex_normals = np.repeat(fn, 3, axis=0)
    return w


def surface(model, part, pts, lift=0.0):
    """Points ramenés sur la peau d'un morceau (face la plus proche), écartés de lift ; renvoie (points, normales)."""
    from scipy.spatial import cKDTree
    skin = model[part]["layers"]["skin"]
    pts = np.asarray(pts, float)
    _, tri = cKDTree(skin.triangles_center).query(pts)
    c, n = skin.triangles_center[tri], skin.face_normals[tri]
    q = pts - n * ((pts - c) * n).sum(1)[:, None]
    return q + n * lift, n


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def cristal(base, d, long, r, sides=6):
    """Cristal : prisme à 6 pans terminé en pointe, enfoncé un peu dans la peau."""
    d = unit(d)
    base = np.asarray(base, float) - d * 0.25 * r
    return sweep([base, base + d * long * 0.5, base + d * long], [r, r * 0.96, r * 0.82], sides)


def grappe(base, n, long, r, side, k=1.0):
    """Grappe de 3 cristaux : un grand au centre, deux plus petits penchés de part et d'autre."""
    n = unit(n)
    back = np.array([0, 0, 1.0])
    out = [cristal(base, n + 0.35 * back, long * k, r * k)]
    for s, f in ((1, 0.62), (-1, 0.5)):
        d = n + 0.55 * s * np.array([side, 0, 0]) + 0.2 * back - 0.15 * s * np.array([0, 0, 1.0])
        out.append(cristal(base + s * 0.28 * r * np.array([side, 0, 0.6]), d, long * k * f, r * k * 0.7))
    return out


def epine(base, n, long, r, courbe=0.6, back=(0, 0, 1.0), sides=5):
    """Épine recourbée vers l'arrière : tube effilé le long d'une courbe."""
    n, back = unit(n), unit(back)
    base = np.asarray(base, float) - n * 0.15 * r
    pts = [base, base + n * long * 0.4 + back * long * 0.1 * courbe,
           base + n * long * 0.75 + back * long * 0.38 * courbe, base + n * long * 0.95 + back * long * 0.8 * courbe]
    path = curve(pts, 2)
    return sweep(path, np.interp(np.linspace(0, 1, len(path)), [0, 0.5, 1], [r, r * 0.55, r * 0.08]), sides)


def plaque(c, u, n, w, l, th=0.05):
    return T7.plate(c, u, n, w, l, th)


def hl(p):
    import rig_v6 as RG
    return RG.hl(p)


def tete(pts):
    return np.array([hl(p) for p in pts])


def dos(model, part, zs, x=0.0, lift=0.0):
    """Points du dessus du dos (ou de la queue) aux z donnés, décalés de x sur le côté."""
    V = np.asarray(model[part]["layers"]["skin"].vertices)
    out = []
    for z in zs:
        d = np.abs(V[:, 2] - z)
        sl = V[d <= max(0.6, np.sort(d)[8])]
        out.append((x, sl[:, 1].max() + 0.5, z))
    return surface(model, part, out, lift)


# Le dos est couvert par les ailes repliées : les ornements vont sur la tête, le cou, la queue, les coudes et
# genoux, les poignets d'ailes et le poitrail (visibles au repos comme en vol, sans traverser les ailes).
def cou(f):
    """Point de l'axe du cou à la fraction f (0 = base, 1 = tête)."""
    import corps_v6 as C6
    N = np.asarray(C6.NECK, float)
    x = f * (len(N) - 1)
    i = min(int(x), len(N) - 2)
    return N[i] + (N[i + 1] - N[i]) * (x - i)


def queue(z):
    """Point de l'axe de la queue à la profondeur z, et le morceau de queue qui le porte."""
    import corps_v6 as C6
    T = np.asarray(C6.TAIL, float)
    y = np.interp(z, T[:, 2], T[:, 1])
    part = "Tail1" if z < 8.9 else ("Tail2" if z < 11.5 else ("Tail3" if z < 13.9 else "Tail4"))
    return np.array([0, y, z]), part


def peau(model, part, centre, d, lift=0.0):
    """Point de la peau d'un morceau dans la direction d depuis un point de son axe, et sa normale."""
    (p,), (n,) = surface(model, part, [np.asarray(centre, float) + unit(d) * 2.5], lift)
    return p, n


def pattes():
    import corps_v5 as C5, corps_v6 as C6
    return {s: C5.legs(s, C6.K) for s in (1, -1)}


def ailes():
    import corps_v5 as C5, corps_v6 as C6
    return {s: C5.wing(s, C6.K) for s in (1, -1)}


SD = {1: "R", -1: "L"}
CORNE = [(0.48, 0.95, -0.35), (0.92, 1.55, -0.1), (1.45, 2.05, 0.3), (1.92, 2.55, 0.85),
         (1.98, 3.15, 1.2), (1.55, 3.62, 1.05), (1.05, 3.72, 0.75)]          # cornes en lyre (tete_v8, repère tête)


def corne(n=3):
    return curve(CORNE, n)


def ajoute(L, part, layer, m):
    L.setdefault(part, {}).setdefault(layer, [])
    L[part][layer] += m if isinstance(m, list) else [m]


def feu(model):
    """Cornes de braise, cheminées d'obsidienne à cœur de lave sur le cou et la queue, fissures de lave,
    fournaise lumineuse au poitrail, ergots d'obsidienne aux coudes."""
    L = {}
    # bout des cornes incandescent
    path = corne(4)
    k = int(0.8 * (len(path) - 1))
    for x in (1, -1):
        m = np.array([x, 1, 1])
        pts = tete(path[k:] * m)
        r = np.interp(np.linspace(0, 1, len(pts)), [0, 1], [0.2, 0.06]) * 1.45 * 1.05
        ajoute(L, "Head", "rune", sweep(pts, r, 6))
    for s in (1, -1):
        # cou : cheminées sur le haut des côtés, fissures entre elles
        for f, h in ((0.15, 1.2), (0.45, 1.0), (0.72, 0.75)):
            p, n = peau(model, "Neck", cou(f), (s * 0.8, 1, 0))
            ajoute(L, "Neck", "obsidienne", cristal(p, n + np.array([0, 0, 0.6]), h, 0.3, 5))
            ajoute(L, "Neck", "rune", cone(p + unit(n + np.array([0, 0, 0.6])) * h * 0.85,
                                           p + unit(n + np.array([0, 0, 0.6])) * h * 1.08, 0.18, 5))
        for f in (0.3, 0.58, 0.85):
            p, n = peau(model, "Neck", cou(f), (s * 1, 0.25, 0))
            ajoute(L, "Neck", "rune", plaque(p, (0, 0.6, -1), n, 0.12, 0.8, 0.05))
        # queue : cheminées en quinconce sur le dessus, fissures sur les flancs
        for j, z in enumerate((6.4, 8.6, 10.8, 13.0, 15.0)):
            c, part = queue(z + (0.5 if s < 0 else 0))
            p, n = peau(model, part, c, (s * 0.7, 1, 0))
            h = 1.25 - 0.15 * j
            d = unit(n + np.array([0, 0, 0.5]))
            ajoute(L, part, "obsidienne", cristal(p, d, h, 0.3 - 0.03 * j, 5))
            ajoute(L, part, "rune", cone(p + d * h * 0.85, p + d * h * 1.08, 0.18 - 0.02 * j, 5))
            c, part = queue(z + 1.0)
            p, n = peau(model, part, c, (s, -0.1, 0))
            ajoute(L, part, "rune", plaque(p, (0, -0.15, 1), n, 0.11, 0.9 - 0.08 * j, 0.05))
        # poitrail : plaques de fournaise entre les pattes avant
        for y, z in ((6.4, -5.6), (5.5, -5.3), (4.7, -4.7)):
            p, n = peau(model, "Torso", (0, y, -4.0), (s * 0.45, 0, -1))
            ajoute(L, "Torso", "rune", plaque(p, (0, 1, -0.3), n, 0.1, 0.55, 0.05))
        # ergots d'obsidienne aux coudes et aux jarrets
        F, B = pattes()[s]
        ajoute(L, "FrontLowerLeg" + SD[s], "obsidienne",
               cristal(np.add(F["elbow"], (s * 0.35, 0.0, 0.55)), (s * 0.3, 0.35, 1), 1.2, 0.26, 5))
        ajoute(L, "BackLowerLeg" + SD[s], "obsidienne",
               cristal(np.add(B["hock"], (s * 0.25, 0.1, 0.35)), (s * 0.3, 0.5, 1), 1.0, 0.24, 5))
    return L


def glace(model):
    """Couronne de cristaux sur la nuque, givre sur les cornes, grappes de cristaux le long du cou et de la queue,
    aux coudes, aux genoux et aux poignets des ailes."""
    L = {}
    for x, y, z, d, ln in ((0.0, 0.95, 0.35, (0, 0.8, 1), 1.0), (0.32, 0.85, 0.3, (0.4, 0.7, 1), 0.75),
                           (-0.32, 0.85, 0.3, (-0.4, 0.7, 1), 0.75), (0.55, 0.65, 0.45, (0.8, 0.4, 1), 0.55),
                           (-0.55, 0.65, 0.45, (-0.8, 0.4, 1), 0.55)):
        a, b = tete([(x, y, z), np.add((x, y, z), d)])
        ajoute(L, "Head", "cristal", cristal(a, b - a, ln * 1.6, 0.16, 6))
    path = corne(3)
    for f in (0.2, 0.36, 0.52, 0.68, 0.82):
        i = int(f * (len(path) - 1))
        for x in (1, -1):
            m = np.array([x, 1, 1])
            a = hl(path[i] * m)
            out = unit(hl(path[i] * m + np.array([x * 0.6, 0.35, 0.55])) - a)
            ajoute(L, "Head", "cristal", cristal(a, out, 0.7 - 0.25 * f, 0.1, 5))
    for s in (1, -1):
        for f, k in ((0.12, 1.0), (0.42, 0.85), (0.7, 0.7)):
            p, n = peau(model, "Neck", cou(f), (s * 0.75, 1, 0))
            ajoute(L, "Neck", "cristal", grappe(p, n + np.array([0, 0, 0.5]), 1.8, 0.27, s, k))
        for j, z in enumerate((6.2, 8.4, 10.6, 12.8, 15.0, 17.0)):
            c, part = queue(z + (0.55 if s < 0 else 0))
            p, n = peau(model, part, c, (s * 0.7, 1, 0))
            ajoute(L, part, "cristal", grappe(p, n + np.array([0, 0, 0.4]), 1.85, 0.27, s, 1 - 0.1 * j))
        F, B = pattes()[s]
        ajoute(L, "FrontLowerLeg" + SD[s], "cristal",
               grappe(np.add(F["elbow"], (s * 0.3, 0.05, 0.5)), (s * 0.35, 0.3, 1), 1.35, 0.22, s, 1.0))
        ajoute(L, "BackLowerLeg" + SD[s], "cristal",
               grappe(np.add(B["knee"], (s * 0.25, 0.15, -0.45)), (s * 0.4, 0.6, -0.6), 1.2, 0.21, s, 1.0))
        W = ailes()[s]
        w = np.asarray(W["wrist"], float)
        ajoute(L, "WingLower" + SD[s], "cristal", grappe(w + (0, 0.25, 0), (0.25 * s, 1, -0.5), 1.9, 0.26, s, 1.0))
    return L


def foret(model):
    """Cornes ramifiées en bois de cerf, feuilles derrière la nuque, le long du cou et de la queue, aux coudes et
    aux poignets des ailes, touffe de feuilles au bout de la queue."""
    L = {}
    path = corne(3)
    for f, d, ln in ((0.22, (0.15, 1.0, -0.55), 1.3), (0.45, (0.35, 1.0, -0.35), 1.45), (0.66, (0.55, 1.0, 0.1), 1.15),
                     (0.85, (0.2, 0.6, 0.9), 0.9)):
        i = int(f * (len(path) - 1))
        for x in (1, -1):
            m = np.array([x, 1, 1])
            p0 = path[i] * m
            dd = unit(np.array(d) * m)
            mid = p0 + dd * ln * 0.55 + np.array([0, 0.1, 0])
            tip = p0 + dd * ln + np.array([x * 0.15, 0.15, 0])
            pts = tete(curve([p0, mid, tip], 2))
            ajoute(L, "Head", "bois", sweep(pts, np.interp(np.linspace(0, 1, len(pts)), [0, 1], [0.16, 0.04]), 5))
            fourche = tete([mid, mid + unit(dd + np.array([x * 0.4, 0, -0.9])) * ln * 0.45])
            ajoute(L, "Head", "bois", sweep(fourche, [0.09, 0.055, 0.02], 5))
    for x in (0.45, -0.45, 0.0):
        a, b, t = tete([(x - 0.18, 0.85, 0.15), (x + 0.18, 0.85, 0.15), (x * 2.4, 1.7, 1.5)])
        ajoute(L, "Head", "feuille" if x else "feuille2", T7.leaf(a, b, t, 0.05))

    def feuille(part, p, n, d, ln, w, layer):
        t = p + unit(d) * ln
        side = unit(np.cross(t - p, n)) * w
        ajoute(L, part, layer, T7.leaf(p - side, p + side, t, 0.05))

    for s in (1, -1):
        for i, f in enumerate((0.08, 0.3, 0.52, 0.74)):
            p, n = peau(model, "Neck", cou(f), (s * 0.7, 1, 0))
            feuille("Neck", p, n, n + np.array([s * 0.8, 0, 0.9]), 1.6 - 0.14 * i, 0.34, "feuille" if i % 2 else "feuille2")
        for j, z in enumerate(np.arange(6.0, 17.0, 1.1)):
            c, part = queue(z + (0.55 if s < 0 else 0))
            p, n = peau(model, part, c, (s * 0.7, 1, 0))
            k = 1 - 0.05 * j
            feuille(part, p, n, n + np.array([s * 1.0, 0, 1.0]), 1.5 * k, 0.3 * k, "feuille" if j % 2 else "feuille2")
        F, B = pattes()[s]
        for d, lay in (((s * 0.6, 0.5, 1), "feuille"), ((s * 1, 0.2, 0.6), "feuille2")):
            p = np.add(F["elbow"], (s * 0.35, 0.0, 0.45))
            feuille("FrontLowerLeg" + SD[s], p, np.array([s, 0, 0.4]), d, 1.0, 0.22, lay)
            p = np.add(B["hock"], (s * 0.25, 0.1, 0.3))
            feuille("BackLowerLeg" + SD[s], p, np.array([s, 0, 0.4]), d, 0.85, 0.2, lay)
        W = ailes()[s]
        w = np.asarray(W["wrist"], float)
        for d, lay in (((0.3 * s, 1, -0.3), "feuille"), ((0.5 * s, 0.8, 0.5), "feuille2"), ((-0.2 * s, 1, 0.3), "feuille")):
            feuille("WingLower" + SD[s], w + (0, 0.2, 0), np.array([0, 0.3, 1.0]), d, 1.3, 0.25, lay)
    # touffe au bout de la queue
    V = np.asarray(model["Tail4"]["layers"]["skin"].vertices)
    bout = V[np.argmax(V[:, 2])] - np.array([0, 0, 1.0])
    for i, a in enumerate(np.linspace(0, 2 * np.pi, 7, endpoint=False)):
        d = unit(np.array([np.cos(a), np.sin(a) * 0.8 + 0.4, 1.2]))
        side = unit(np.cross(d, (0, 1, 0.01))) * 0.22
        ajoute(L, "Tail4", "feuille" if i % 2 else "feuille2", T7.leaf(bout - side, bout + side, bout + d * 1.7, 0.05))
    return L


def ombre(model):
    """Grandes épines de nuque couchées vers l'arrière, épines recourbées le long du cou et de la queue, aux coudes
    et aux poignets des ailes ; runes lumineuses sur le cou, les épaules, les cuisses et la queue."""
    L = {}
    for x in (1, -1):
        a = (x * 0.35, 0.9, 0.2)
        p = tete([a])[0]
        n = unit(tete([np.add(a, (x * 0.35, 1.0, 0.25))])[0] - p)
        ajoute(L, "Head", "epine", epine(p, n, 3.4, 0.24, 1.3, back=(x * 0.2, -0.2, 1.0)))
        a = (x * 0.75, 0.55, 0.3)
        p = tete([a])[0]
        n = unit(tete([np.add(a, (x * 0.8, 0.5, 0.3))])[0] - p)
        ajoute(L, "Head", "epine", epine(p, n, 2.2, 0.17, 1.3, back=(x * 0.3, -0.3, 1.0)))
    for s in (1, -1):
        for f, h in ((0.1, 2.5), (0.38, 2.2), (0.66, 1.9)):
            p, n = peau(model, "Neck", cou(f), (s * 0.6, 1, 0))
            ajoute(L, "Neck", "epine", epine(p, n + np.array([s * 0.4, 0, 0]), h, 0.22, 1.0))
        for f in (0.22, 0.5, 0.78):
            pts, nn = surface(model, "Neck", [cou(f) + (s * 2.5, 0.4, 0), cou(f) + (s * 2.5, -0.3, 0.35)])
            for p, n, u in zip(pts, nn, ((0, 1, -0.6), (0, -1, -0.6))):
                ajoute(L, "Neck", "rune", plaque(p, u, n, 0.1, 0.65, 0.05))
        for j, z in enumerate((6.0, 8.2, 10.4, 12.6, 14.8, 16.8)):
            c, part = queue(z + (0.55 if s < 0 else 0))
            p, n = peau(model, part, c, (s * 0.6, 1, 0))
            ajoute(L, part, "epine", epine(p, n + np.array([s * 0.5, 0, 0]), 2.2 - 0.22 * j, 0.21 - 0.015 * j, 1.0))
            c, part = queue(z + 1.0)
            pts, nn = surface(model, part, [c + (s * 2.5, 0.35, 0), c + (s * 2.5, -0.25, 0.4)])
            for p, n, u in zip(pts, nn, ((0, 1, -0.7), (0, -1, -0.7))):
                ajoute(L, part, "rune", plaque(p, u, n, 0.1, 0.7 - 0.06 * j, 0.05))
        F, B = pattes()[s]
        ajoute(L, "FrontLowerLeg" + SD[s], "epine",
               epine(np.add(F["elbow"], (s * 0.3, 0.1, 0.45)), (s * 0.3, 0.3, 1), 1.5, 0.15, 1.0, back=(0, -1, 0.3)))
        ajoute(L, "BackLowerLeg" + SD[s], "epine",
               epine(np.add(B["hock"], (s * 0.2, 0.1, 0.3)), (s * 0.3, 0.6, 1), 1.2, 0.14, 1.0, back=(0, -1, 0.3)))
        for part, a, b in (("FrontUpperLeg", F["shoulder"], F["elbow"]), ("BackUpperLeg", B["hip"], B["knee"])):
            for f in (0.35, 0.6):
                c = np.add(a, np.subtract(b, a) * f)
                pts, nn = surface(model, part + SD[s], [c + (s * 2.0, 0, 0)])
                ajoute(L, part + SD[s], "rune", plaque(pts[0], np.subtract(b, a), nn[0], 0.08, 0.6, 0.05))
        W = ailes()[s]
        w = np.asarray(W["wrist"], float)
        ajoute(L, "WingLower" + SD[s], "epine", epine(w + (0, 0.2, 0), (0.2 * s, 1, -0.4), 2.0, 0.17, 1.2,
                                                      back=(s * 0.4, 0, 1)))
    return L


ORNEMENTS = {"Feu": feu, "Glace": glace, "Foret": foret, "Ombre": ombre}


# ---------- caractéristiques de jeu ----------
# Statistiques sur 100 (le dragon de référence a 50 partout) ; vitesses en studs/s (marche : la cadence de
# AnimDragon suit jusqu'à ~4,8 studs/s sans que les pieds patinent ; au-delà, le dragon décolle). Cycle des affinités :
# Feu > Glace > Forêt > Ombre > Feu (dégâts x1,25 contre la lignée battue, x0,8 contre celle qui vous bat).
# souffle : degats = dégâts par seconde passée dans le souffle, duree et recharge en s, portee en studs, angle en
# degrés (demi-ouverture du cône) ; effet appliqué à la cible (effet_duree en s, effet_valeur selon l'effet).
# Ce sont des valeurs de départ pour l'équilibrage : le jeu les lit dans LigneesDragon.lua.
CARAC = {
    "Feu": dict(
        nom="Feu", element="Feu", titre="Le Brasier",
        description="Dragon d'attaque : souffle de flammes qui brûle dans la durée, colère qui monte quand il est blessé.",
        stats=dict(vie=100, attaque=72, defense=50, vitesse=55, agilite=50, endurance=55),
        vitesses=dict(marche=4.0, vol=34, montee=12, pique=60),
        souffle=dict(nom="Flammes", forme="cone", portee=28, angle=25, degats=18, duree=2.0,
                     recharge=6, effet="Brulure", effet_duree=4, effet_valeur=4,
                     texte="Brûlure : 4 dégâts par seconde pendant 4 s."),
        passif=dict(nom="Sang de lave", texte="Immunisé contre la brûlure ; +20 % d'attaque sous 30 % de vie.",
                    immunite="Brulure", seuil_vie=0.3, bonus_attaque=0.2),
        fort_contre="Glace", faible_contre="Ombre"),
    "Glace": dict(
        nom="Glace", element="Glace", titre="Le Givre éternel",
        description="Dragon défensif : carapace de givre, souffle qui ralentit puis fige la cible, grand planeur.",
        stats=dict(vie=110, attaque=50, defense=75, vitesse=45, agilite=40, endurance=65),
        vitesses=dict(marche=3.5, vol=30, montee=9, pique=55),
        souffle=dict(nom="Givre", forme="rayon", portee=34, angle=10, degats=12, duree=2.4,
                     recharge=7, effet="Gel", effet_duree=3, effet_valeur=0.4,
                     texte="Gel : ralentit de 40 % ; 2 s dans le souffle figent la cible 1,5 s."),
        passif=dict(nom="Carapace de givre", texte="-15 % de dégâts subis ; plane sans perdre d'endurance.",
                    reduction=0.15, plane_gratuit=True),
        fort_contre="Foret", faible_contre="Feu"),
    "Foret": dict(
        nom="Forêt", element="Foret", titre="Le Gardien sylvestre",
        description="Dragon endurant : beaucoup de vie, se régénère au sol, souffle de spores qui empoisonne une zone.",
        stats=dict(vie=130, attaque=55, defense=60, vitesse=48, agilite=42, endurance=75),
        vitesses=dict(marche=3.8, vol=28, montee=8, pique=50),
        souffle=dict(nom="Spores", forme="nuage", portee=18, angle=40, degats=8, duree=2.6,
                     recharge=8, effet="Poison", effet_duree=6, effet_valeur=3, zone_duree=5,
                     texte="Poison : 3 dégâts par seconde pendant 6 s ; le nuage reste 5 s au sol."),
        passif=dict(nom="Racines", texte="Au sol et immobile depuis 2 s : régénère 2 % de vie par seconde.",
                    regen=0.02, delai=2),
        fort_contre="Ombre", faible_contre="Glace"),
    "Ombre": dict(
        nom="Ombre", element="Ombre", titre="Le Voile de nuit",
        description="Dragon rapide et fragile : vole vite, se fond dans l'ombre, souffle qui aveugle.",
        stats=dict(vie=85, attaque=62, defense=38, vitesse=75, agilite=80, endurance=50),
        vitesses=dict(marche=4.5, vol=42, montee=14, pique=70),
        souffle=dict(nom="Ténèbres", forme="cone", portee=22, angle=30, degats=14, duree=1.8,
                     recharge=5, effet="Aveuglement", effet_duree=3, effet_valeur=0.7,
                     texte="Aveuglement : la vue de la cible se brouille (70 %) pendant 3 s."),
        passif=dict(nom="Voile", texte="Immobile ou de nuit : presque invisible (transparence 0,7) ; "
                                       "première attaque depuis le voile +30 %.",
                    transparence=0.7, bonus_embuscade=0.3),
        fort_contre="Feu", faible_contre="Foret"),
}
AFFINITE_FORT, AFFINITE_FAIBLE = 1.25, 0.8


def affinite(attaquant, defenseur):
    """Multiplicateur de dégâts d'une lignée contre une autre."""
    if CARAC[attaquant]["fort_contre"] == defenseur:
        return AFFINITE_FORT
    if CARAC[attaquant]["faible_contre"] == defenseur:
        return AFFINITE_FAIBLE
    return 1.0


# ---------- style d'animation ----------
# vol : duree (s, boucle de 4 battements + plané : plus court = bat plus vite), amplitude (x angle des ailes), plane (part de vol plané dans la boucle,
# 0 = bat tout le temps), ondulation (x mouvements du corps, du cou et de la queue), lourdeur (x montée et
# descente du corps, x balancement des pattes), balayage (ailes repliées vers l'arrière en vol plané, faucon)
# souffle : particules (liste d'émetteurs), lumière ; « oeil » = couleur des yeux de la lignée (DragonNeon)
STYLE = {
    "Feu": dict(
        vol=dict(duree=3.6, amplitude=1.0, plane=0.3, ondulation=1.0, lourdeur=1.0, balayage=0.2),
        souffle=dict(lumiere=dict(portee=16, eclat=4), particules=[
            dict(nom="Feu", taux=160, vie=(0.35, 0.6), vitesse=(28, 38), angle=9, frein=2,
                 taille=[(0, 0.6), (0.4, 2.6), (1, 4.5)], transparence=[(0, 0.1), (0.7, 0.4), (1, 1)],
                 couleurs=[(0, "#FFFFE6"), (0.25, "oeil"), (1, "#3A140C")], lumineux=1),
            dict(nom="Braises", taux=40, vie=(0.6, 1.1), vitesse=(18, 30), angle=18, frein=1,
                 taille=[(0, 0.25), (1, 0.05)], transparence=[(0, 0), (1, 1)],
                 couleurs=[(0, "#FFE14A"), (1, "#FF5A10")], lumineux=1, acceleration=(0, 6, 0))]),
    ),
    "Glace": dict(
        vol=dict(duree=4.4, amplitude=1.1, plane=0.42, ondulation=0.7, lourdeur=0.8, balayage=0.1),
        souffle=dict(lumiere=dict(portee=14, eclat=2.5), particules=[
            dict(nom="Givre", taux=140, vie=(0.5, 0.8), vitesse=(30, 40), angle=5, frein=1.5,
                 taille=[(0, 0.4), (0.5, 1.8), (1, 3.2)], transparence=[(0, 0.2), (0.6, 0.5), (1, 1)],
                 couleurs=[(0, "#FFFFFF"), (0.3, "oeil"), (1, "#DDF4FF")], lumineux=0.6),
            dict(nom="Eclats", taux=60, vie=(0.4, 0.7), vitesse=(35, 45), angle=8, frein=0.5,
                 taille=[(0, 0.35), (1, 0.15)], transparence=[(0, 0), (1, 0.6)],
                 couleurs=[(0, "#FFFFFF"), (1, "oeil")], lumineux=0.8, rotation=(-180, 180),
                 vitesse_rotation=(-360, 360))]),
    ),
    "Foret": dict(
        vol=dict(duree=3.2, amplitude=1.15, plane=0.2, ondulation=0.9, lourdeur=1.35, balayage=0.0),
        souffle=dict(lumiere=dict(portee=12, eclat=1.5), particules=[
            dict(nom="Spores", taux=90, vie=(1.2, 2.0), vitesse=(12, 18), angle=22, frein=1.2,
                 taille=[(0, 0.8), (0.5, 3.0), (1, 4.5)], transparence=[(0, 0.3), (0.7, 0.6), (1, 1)],
                 couleurs=[(0, "oeil"), (0.5, "#8CC23E"), (1, "#3A5A1E")], lumineux=0.3,
                 acceleration=(0, -1.5, 0)),
            dict(nom="Pollen", taux=50, vie=(1.5, 2.5), vitesse=(8, 14), angle=30, frein=0.8,
                 taille=[(0, 0.2), (1, 0.12)], transparence=[(0, 0), (1, 1)],
                 couleurs=[(0, "oeil"), (1, "#FFF6A0")], lumineux=1, acceleration=(0, 1.0, 0))]),
    ),
    "Ombre": dict(
        vol=dict(duree=3.0, amplitude=0.85, plane=0.36, ondulation=1.5, lourdeur=0.7, balayage=1.0),
        souffle=dict(lumiere=dict(portee=10, eclat=1.2), particules=[
            dict(nom="Tenebres", taux=150, vie=(0.4, 0.7), vitesse=(24, 32), angle=12, frein=2,
                 taille=[(0, 0.8), (0.5, 3.0), (1, 5.0)], transparence=[(0, 0.15), (0.6, 0.45), (1, 1)],
                 couleurs=[(0, "oeil"), (0.35, "#2A1440"), (1, "#05030A")], lumineux=0),
            dict(nom="Volutes", taux=45, vie=(0.8, 1.3), vitesse=(14, 22), angle=20, frein=1.5,
                 taille=[(0, 0.3), (0.5, 0.6), (1, 0.1)], transparence=[(0, 0), (1, 1)],
                 couleurs=[(0, "oeil"), (1, "#6A3E9A")], lumineux=1, acceleration=(0, 2.5, 0))]),
    ),
}
