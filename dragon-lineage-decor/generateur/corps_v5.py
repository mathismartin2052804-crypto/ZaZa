# Corps de dragon v5 : la v4 « musclée ». Même squelette et mêmes noms de morceaux, avec un paramètre de masse k
# (k = 0 redonne la v4) qui ajoute :
#   - tronc plus large et dos plat (dos de taureau), garrot relevé, carène plus profonde, taille moins pincée
#   - muscles en volumes séparés : pectoraux, trapèzes, masse dorsale des ailes, deltoïdes, avant-bras,
#     cuisses en pilon, fessiers, mollets
#   - pattes ×1,4 en épaisseur, grosses pattes griffues, posture écartée (coudes vers l'extérieur)
#   - cou et base de queue épaissis (la queue prolonge les hanches)
#   - ailes un peu moins grandes, os et doigts plus épais, muscle à la racine
#   - armure : plaques dorsales larges, plaques d'épaule et de cuisse, éperons plus gros ; bande ventrale plus large
# Usage : python3 corps_v5.py  ->  ../planche-masse-v5.png (Feu : v4 / athlétique / puissant / colosse)
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import rendu
import tete_v7 as T7
import palette_corps as PC
import corps_v4 as V4
from corps_v4 import tube, frame_rings, crest_piece, cat, place, slab
from tete_v5 import loft, mesh, sweep, cone, curve, both, FONT, FONT_B

NIVEAUX = [("v4", 0.0), ("Athlétique", 0.5), ("Puissant", 1.0), ("Colosse", 1.6)]


def bump(z, c, s):
    return float(np.exp(-((z - c) / s) ** 2))


def size(k):
    """Taille des muscles ajoutés selon la masse (0 à k = 0)."""
    return k ** 0.6


# ---------- squelette selon la masse ----------
def tronc(k):
    out = []
    for z, top, bot, w in V4.TRONC:
        top += 0.45 * k * bump(z, -3.2, 1.6)                       # garrot relevé (muscles des ailes)
        bot -= 0.55 * k * bump(z, -2.4, 1.9)                       # carène plus profonde
        w = w * (1 + 0.32 * k) + 0.22 * k * bump(z, 1.6, 1.6)      # taille moins pincée
        out.append((z, top, bot, w))
    return out


def legs(s, k):
    front = dict(shoulder=(s * (1.75 + 0.75 * k), 7.0, -3.1), elbow=(s * (2.45 + 1.1 * k), 4.35 - 0.2 * k, -2.2),
                 wrist=(s * (2.55 + 0.9 * k), 1.35, -3.15), paw=(s * (2.6 + 0.9 * k), 0.32, -3.75))
    back = dict(hip=(s * (1.65 + 0.6 * k), 7.1, 3.2), knee=(s * (2.15 + 0.9 * k), 4.7, 1.3),
                hock=(s * (2.1 + 0.8 * k), 2.2, 4.3), paw=(s * (2.1 + 0.8 * k), 0.32, 3.75))
    return front, back


def wing(s, k):
    W = V4.wing(s)
    root = np.array(W["root"]) + [s * 0.55 * k, 0.25 * k, 0]
    sp = 1 - 0.1 * k                                               # envergure un peu réduite
    far = lambda p: tuple(root + (np.array(p) - np.array(W["root"])) * sp)
    return dict(root=tuple(root), elbow=far(W["elbow"]), wrist=far(W["wrist"]), tips=[far(t) for t in W["tips"]],
                back=tuple(np.array(W["back"]) + [s * 0.55 * k, 0, 0]))


# ---------- outils ----------
def muscle(c, d, r):
    """Muscle : ellipsoïde polygonal ; d = sens de la longueur, r = (long, avant-arrière, côté)."""
    u = np.asarray(d, float); u /= np.linalg.norm(u)
    v = np.cross(u, [1.0, 0, 0])
    if np.linalg.norm(v) < 1e-6:
        v = np.array([0, 1.0, 0])
    v /= np.linalg.norm(v)
    w = np.cross(u, v)
    ico = trimesh.creation.icosphere(subdivisions=1)
    V = np.asarray(c, float) + (ico.vertices * r) @ np.array([u, v, w])
    return mesh(V, ico.faces)


def scute(c, u, n, w, l, th=0.14):
    return T7.plate(c, u, n, w, l, th)


def paw(p, fwd, s, sc):
    """Patte : coussinet + 3 doigts griffus + ergot, à l'échelle sc."""
    p, fwd = np.asarray(p, float), np.asarray(fwd, float) / np.linalg.norm(fwd)
    side = np.array([s * 1.0, 0, 0])
    pad = tube([p - fwd * 0.45 * sc + [0, 0.15 * sc, 0], p, p + fwd * 0.4 * sc], [(0, 0.45 * sc), (1, 0.38 * sc)], 6)
    toes, claws = [pad], []
    for j in (-1, 0, 1):
        d = fwd + side * 0.38 * j; d /= np.linalg.norm(d)
        a = p + d * 0.25 * sc + side * 0.22 * j * sc
        b = a + d * 0.75 * sc - [0, 0.12 * sc, 0]
        toes.append(tube([a, b], [(0, 0.2 * sc), (1, 0.15 * sc)], 5))
        claws.append(cone(b, b + (d * 0.55 - [0, 0.32, 0]) * sc, 0.15 * sc, 5))
    e = p - fwd * 0.35 * sc + [0, 0.35 * sc, 0] - side * 0.3 * sc
    claws.append(cone(e, e + (-fwd * 0.4 - [0, 0.3, 0] - side * 0.05) * sc, 0.1 * sc, 4))
    return toes, claws


# ---------- pièces ----------
def torso(lin, k):
    T = tronc(k)
    flat = [(x * (1 + 0.12 * k * (y > 0.5)), y + 0.06 * k * (y > 0.5)) for x, y in V4.SHAPE_TRONC]   # dos plat
    rings = []
    for z, top, bot, w in T:
        cy, h = (top + bot) / 2, (top - bot) / 2
        rings.append([(sx * w, cy + sy * h, z) for sx, sy in flat])
    skin = [loft(rings, (0, 7.0, -5.6), (0, 6.7, 5.9))]
    bones, plates = [], []
    for x, y, z, ln in ((1.25, 8.55, -3.4, 1.6), (1.15, 8.0, 2.9, 1.3)):
        bones += both(T7.plate((x * (1 + 0.4 * k), y + 0.3 * k * (z < 0), z), (0.15, 0.2, 1), (0.5, 1, 0), 0.5, ln, 0.18))
    g = size(k)
    if k > 0:
        for s in (1, -1):
            skin += [muscle((s * (0.85 + 0.3 * k), 5.75 - 0.25 * k, -4.2), (0, -1, -0.35), (1.35 * g, 0.8 * g, 1.1 * g)),   # pectoraux
                     muscle((s * (1.2 + 0.45 * k), 8.75 + 0.3 * k, -2.7), (0, 0.05, 1), (2.0 * g, 0.75 * g, 0.95 * g)),   # masse des ailes
                     muscle((s * 0.85, 8.4 + 0.2 * k, -4.6), (s * 0.9, -0.4, 1.2), (1.6 * g, 0.55 * g, 0.85 * g))]        # trapèzes
    zs = [r[0] for r in T]
    crest = []
    for z in np.arange(-4.4, 5.2, 0.85):
        top = float(np.interp(z, zs, [r[1] for r in T]))
        top += 0.06 * k
        h = (0.75 - 0.25 * abs(z + 2.5) / 7) * (1 + 0.25 * k)
        crest += crest_piece(lin, np.array([0, top - 0.05, z]), np.array([0, 0, 1.0]), np.array([0, 1.0, 0.25]), h, 0.32)
        if k > 0:                                                   # plaques dorsales larges sous la crête
            w = float(np.interp(z, zs, [r[3] for r in T]))
            plates.append(scute((0, top - 0.02, z), (0, 0, 1), (0, 1, 0.08), 0.55 * w * g, 0.82, 0.12))
    return {"skin": cat(skin), "back": cat(bones + plates), "spike": cat(crest)}


def neck(lin, k):
    path = np.asarray(curve(V4.NECK, 2), float)
    rads = np.interp(np.linspace(0, 1, len(path)), [0, 0.35, 1], [1.55 + 0.6 * k, 1.05 + 0.3 * k, 0.88 + 0.08 * k])
    rings, T = frame_rings(path, rads, V4.SHAPE_COU)
    skin = loft(rings, path[0] - T[0] * 0.3, path[-1] + T[-1] * 0.1)
    crest = []
    for i in range(1, len(path) - 1):
        p, t, r = path[i], T[i], rads[i]
        up = np.cross(t, [1.0, 0, 0]); up /= np.linalg.norm(up); up = up if up[1] > 0 else -up
        crest += crest_piece(lin, p + up * r * 1.0, t, up, 0.35 * r + 0.15, 0.24)
    return {"skin": skin, "spike": cat(crest)}


def tail_rad(k):
    n = len(V4.TAIL_RAD)
    return [r * (1 + 0.55 * k * (1 - i / (n - 1)) ** 1.3) for i, r in enumerate(V4.TAIL_RAD)]


def tail(i, lin, k):
    TAIL, CUT, RAD = V4.TAIL, V4.TAIL_CUT, tail_rad(k)
    a, b = CUT[i], CUT[i + 1]
    pts = TAIL[max(a - 1, 0):b + 2] if i < 3 else TAIL[a - 1:]
    path = np.asarray(curve(pts, 3), float)
    za, zb = TAIL[a][2] - (0.35 if i else 0.6), TAIL[b][2] + (0.3 if i < 3 else 0)
    path = path[(path[:, 2] >= za) & (path[:, 2] <= zb)]
    rads = np.interp(path[:, 2], [p[2] for p in TAIL], RAD)
    rings, T = frame_rings(path, rads, V4.SHAPE_COU, 1.0)
    skin = loft(rings, path[0] - T[0] * 0.05, path[-1] + T[-1] * (0.05 if i < 3 else 0.3))
    crest = []
    for j in range(1, len(path) - (1 if i < 3 else 2), 2):
        p, t, r = path[j], T[j], rads[j]
        up = np.cross(t, [1.0, 0, 0]); up /= np.linalg.norm(up); up = up if up[1] > 0 else -up
        crest += crest_piece(lin, p + up * r * 0.95, t, up, 0.45 * r + 0.12, 0.2 + 0.1 * r)
    L = {"skin": skin, "spike": cat(crest)}
    if i == 3:
        L["tailblade"], L["glow"] = V4.tail_blade(lin, path[-1], T[-1])
    return L


def front_upper(s, lin, k):
    F, _ = legs(s, k)
    sh, el = np.array(F["shoulder"]), np.array(F["elbow"])
    lf, g = 1 + 0.4 * k, size(k)
    skin = [tube([sh + [0, 0.5, -0.2], (sh + el) / 2 + [0, 0, -0.35], el],
                 [(0, 1.3 * lf), (0.4, 1.1 * lf), (1, 0.7 * lf)], 7)]
    plates = []
    if k > 0:
        skin.append(muscle(sh + (el - sh) * 0.3 + [s * 0.35 * k, 0.25, -0.15], el - sh, (1.5 * g, 1.05 * g, 0.85 * g)))  # deltoïde
        plates.append(scute(sh + [s * (1.25 + 0.5 * k), 0.55, 0.05], el - sh, (s, 0.55, -0.1), 0.8 * g, 1.5 * g, 0.14))
    return {"skin": cat(skin), "back": cat(plates)}


def front_lower(s, lin, k):
    F, _ = legs(s, k)
    el, wr, pw = (np.array(F[n]) for n in ("elbow", "wrist", "paw"))
    lf, g = 1 + 0.4 * k, size(k)
    skin = [tube([el, (el + wr) / 2 + [0, 0, 0.1], wr, pw], [(0, 0.7 * lf), (0.6, 0.55 * lf), (1, 0.46 * lf)], 6)]
    if k > 0:
        skin.append(muscle(el + (wr - el) * 0.28 + [s * 0.1, 0, 0.15], wr - el, (1.15 * g, 0.62 * g, 0.55 * g)))       # avant-bras
    toes, claws = paw(pw, (0, 0, -1), s, 1 + 0.45 * k)
    spur = cone(el + [s * 0.1, 0.1, 0.3], el + [s * (0.25 + 0.2 * k), 0.25 + 0.15 * k, 1.05 + 0.4 * k], 0.16 * lf, 4)
    return {"skin": cat(skin + toes), "claw": cat(claws), "spike": spur}


def back_upper(s, lin, k):
    _, B = legs(s, k)
    hp, kn = np.array(B["hip"]), np.array(B["knee"])
    lf, g = 1 + 0.4 * k, size(k)
    skin = [tube([hp + [0, 0.4, 0.4], (hp + kn) / 2 + [0, 0, 0.35], kn], [(0, 1.7 * lf), (0.45, 1.4 * lf), (1, 0.75 * lf)], 7)]
    plates = []
    if k > 0:
        skin += [muscle(hp + (kn - hp) * 0.38 + [s * 0.3 * k, 0.15, 0.25], kn - hp, (2.0 * g, 1.5 * g, 1.05 * g)),          # cuisse
                 muscle(hp + [s * 0.1, 0.55, 0.65], (0, -0.3, 1), (1.35 * g, 1.15 * g, 1.0 * g))]                          # fessier
        plates.append(scute(hp + (kn - hp) * 0.3 + [s * (1.35 + 0.55 * k), 0.2, 0.3], kn - hp, (s, 0.35, 0.1),
                            0.8 * g, 1.45 * g, 0.14))
    return {"skin": cat(skin), "back": cat(plates)}


def back_lower(s, lin, k):
    _, B = legs(s, k)
    kn, hk, pw = (np.array(B[n]) for n in ("knee", "hock", "paw"))
    lf, g = 1 + 0.4 * k, size(k)
    skin = [tube([kn, (kn + hk) / 2 + [0, 0, -0.15], hk, pw + [0, 0.25, 0.1], pw],
                 [(0, 0.75 * lf), (0.45, 0.6 * lf), (0.7, 0.47 * lf), (1, 0.44 * lf)], 6)]
    if k > 0:
        skin.append(muscle(kn + (hk - kn) * 0.32 + [0, 0.05, 0.22], hk - kn, (1.3 * g, 0.75 * g, 0.6 * g)))               # mollet
    toes, claws = paw(pw, (0, 0, -1), s, 1 + 0.45 * k)
    spur = cone(hk + [0, 0.1, 0.15], hk + [s * 0.1, 0.4 + 0.15 * k, 0.95 + 0.4 * k], 0.15 * lf, 4)
    return {"skin": cat(skin + toes), "claw": cat(claws), "spike": spur}


def wing_parts(s, lin, k):
    W = wing(s, k)
    old = V4.wing
    V4.wing = lambda s_: W            # wing_parts de la v4 lit le squelette de l'aile par cette fonction
    try:
        up, lo = V4.wing_parts(s, lin)
    finally:
        V4.wing = old
    if k > 0:                          # os et doigts plus épais, muscle à la racine
        root, elbow, wrist = (np.array(W[n], float) for n in ("root", "elbow", "wrist"))
        bf, g = 1 + 0.5 * k, size(k)
        up["wingbone"] = cat([up["wingbone"], tube([root, (root + elbow) / 2 + [0, 0.3, 0], elbow], [(0, 0.6 * bf), (1, 0.4 * bf)], 6),
                              muscle(root + (elbow - root) * 0.3, elbow - root, (1.5 * g, 0.75 * g, 0.65 * g))])
        bones = [lo["wingbone"], tube([elbow, (elbow + wrist) / 2 + [0, 0.25, 0], wrist], [(0, 0.4 * bf), (1, 0.32 * bf)], 6)]
        for t in W["tips"]:
            t = np.array(t, float)
            bones.append(tube([wrist, wrist + (t - wrist) * 0.3], [(0, 0.24 * bf), (1, 0.13 * bf)], 5))
        lo["wingbone"] = cat(bones)
    return up, lo


def body_slots(m, kind):
    """Comme la v4, avec une bande ventrale plus large (seuil de normale abaissé)."""
    c, n = m.triangles_center, m.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if kind == "leg":
            out.append("limb" if y < 3.0 else "skin")
            continue
        band = int(np.floor((z - 0.4 * y) / 0.75)) % 2
        if ny < -0.38:
            out.append("belly2" if band else "belly")
        elif ny > 0.72:
            out.append("marking" if (kind != "neck" and abs(x) < 0.7 and ((z / 1.3) % 1) < 0.22) else "back")
        else:
            out.append("skin")
    return out


def build(lin="Feu", k=1.0):
    out = {}

    def add(name, parent, pivot, L, kind=None):
        L = {n: v for n, v in L.items() if v is not None}
        layers = {n: place(v, False, n.startswith("membrane")) for n, v in L.items()}
        slots = {}
        if kind and "skin" in layers:
            slots["skin"] = body_slots(L["skin"], kind)
        for n in ("membrane2", "wingbone", "tailblade", "belly", "limb", "marking"):
            if n in layers:
                slots[n] = [n] * len(layers[n].faces)
        out[name] = {"parent": parent, "pivot": tuple(float(v) for v in pivot), "layers": layers, "slots": slots}

    add("Torso", None, (0, 7.0, 0), torso(lin, k), "body")
    add("Neck", "Torso", V4.NECK[0], neck(lin, k), "neck")
    HB, HS, HEAD_R = V4.HB, V4.HS, V4.HEAD_R
    for name, fn, piv, which in (("Head", T7.head_layers, HB, "head"),
                                 ("Jaw", T7.jaw_layers, HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS, "jaw")):
        L = {n: trimesh.util.concatenate(v) for n, v in fn(lin).items() if v}
        out[name] = {"parent": "Neck" if name == "Head" else "Head", "pivot": tuple(float(v) for v in piv),
                     "layers": {n: place(m) for n, m in L.items()}, "slots": {"skin": T7.slots(L["skin"], which)}}
    for i in range(4):
        add(f"Tail{i + 1}", "Torso" if i == 0 else f"Tail{i}", V4.TAIL[V4.TAIL_CUT[i]], tail(i, lin, k), "body")
    for s, n in ((1, "R"), (-1, "L")):
        F, B = legs(s, k)
        W = wing(s, k)
        add("FrontUpperLeg" + n, "Torso", F["shoulder"], front_upper(s, lin, k), "leg")
        add("FrontLowerLeg" + n, "FrontUpperLeg" + n, F["elbow"], front_lower(s, lin, k), "leg")
        add("BackUpperLeg" + n, "Torso", B["hip"], back_upper(s, lin, k), "leg")
        add("BackLowerLeg" + n, "BackUpperLeg" + n, B["knee"], back_lower(s, lin, k), "leg")
        up, lo = wing_parts(s, lin, k)
        add("WingUpper" + n, "Torso", W["root"], up)
        add("WingLower" + n, "WingUpper" + n, W["elbow"], lo)
    return out


# ---------- planche : niveaux de masse ----------
def main():
    lin = "Feu"
    cw, ch, lw = 470, 380, 190
    VUES = V4.VUES
    rows = len(NIVEAUX) + 1
    W, H = lw + cw * len(VUES) + 10, 110 + ch * rows + 20
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — corps v5 : niveaux de masse (Feu)", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Tronc élargi, pectoraux, masse des ailes, cuisses en pilon, grosses pattes, posture écartée, "
                      "cou et queue épaissis, os d'ailes renforcés, plaques d'armure.", font=f(17), fill=(150, 160, 184))
    sil = []
    for i, (nom, k) in enumerate(NIVEAUX):
        m = build(lin, k)
        it = V4.gather(m, PC.palette(lin))
        y0 = 100 + i * ch
        dr.text((20, y0 + 20), nom, font=f(24, True), fill=(230, 232, 240))
        dr.text((20, y0 + 56), f"masse {k:g}", font=f(15), fill=(255, 210, 122))
        dr.text((20, y0 + 80), f"{V4.tris(m)} triangles", font=f(14), fill=(140, 150, 172))
        for j, (t, eye, tg, fov) in enumerate(VUES):
            board.paste(rendu.render(it, eye, tg, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        sil.append((nom, V4.gather(m, PC.palette(lin), True)))
        print(nom, V4.tris(m), flush=True)
    # dernière ligne : silhouettes de profil à la même échelle
    y0 = 100 + len(NIVEAUX) * ch
    dr.text((20, y0 + 20), "Silhouettes", font=f(22, True), fill=(230, 232, 240))
    dr.text((20, y0 + 52), "profil, même échelle", font=f(14), fill=(140, 150, 172))
    C = V4.C
    for j, (nom, it) in enumerate(sil):
        board.paste(V4.silhouette(it, C + [-56, 1.5, 2.5], C + [0, 0, 2.5], (cw - 8, ch - 8), 34), (lw + j * cw, y0))
        dr.text((lw + j * cw + 12, y0 + 8), nom, font=f(16, True), fill=(200, 60, 40))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planche-masse-v5.png"))


if __name__ == "__main__":
    main()
