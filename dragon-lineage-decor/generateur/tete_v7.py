# Tête de dragon v7 : tête et cornes de la v6 (validées), avec
#   1) des détails de surface communs pour qu'on lise des écailles et des plaques, pas un tas de polygones :
#      plaques sur l'arête du nez, rangée d'écailles sur les joues, plaques sous la mâchoire, narines,
#      et un ombrage par quadrilatère (les deux triangles d'une face presque plane partagent la même normale)
#   2) des détails propres à chaque lignée :
#      Feu   : collerettes en langues de flamme (deux tons), petites cornes d'arcade, narines de braise
#      Glace : cristaux hexagonaux sur l'arcade et les joues, stalactites sous le menton
#      Forêt : collerettes en feuilles, barbe de mousse, plaques d'écorce sur le nez
#      Ombre : collerettes déchirées, couronne d'épines sur l'arcade, runes lumineuses, barbillons
# Usage : python3 tete_v7.py  ->  ../concept-tete-v7.png
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
from tete_v5 import section, loft, mesh, blade, sweep, cone, curve, both, FONT, FONT_B
import tete_v6 as T6

HB, HEAD_R, HS = V.HB, V.HEAD_R, V.HS
CRANE, MACHOIRE = T6.CRANE, T6.MACHOIRE
LIGNEES = ["Feu", "Glace", "Foret", "Ombre"]
NOMS = {"Feu": "Feu", "Glace": "Glace", "Foret": "Forêt", "Ombre": "Ombre"}


# ---------- outils ----------
def crane_at(z, idx):
    """Valeur d'une colonne de CRANE interpolée en z (idx : 1 = dessus, 4 = joue (x, y)…)."""
    zs = [-c[0] for c in CRANE]
    col = [c[idx] for c in CRANE]
    if np.ndim(col[0]) == 0:
        return float(np.interp(-z, zs, col))
    return tuple(float(np.interp(-z, zs, [c[k] for c in col])) for k in range(2))


def plate(c, u, n, w, l, th):
    """Plaque / écaille : hexagone allongé épais, posé à plat (u = sens de la longueur, n = normale)."""
    c, u, n = (np.asarray(x, float) for x in (c, u, n))
    n = n / np.linalg.norm(n); u = u - n * (u @ n); u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pts = [(0.5, 0), (0.22, 0.5), (-0.4, 0.5), (-0.5, 0), (-0.4, -0.5), (0.22, -0.5)]
    ring = lambda h: [c + u * a * l + v * b * w + n * h for a, b in pts]
    return loft([ring(-th * 0.4), ring(th)], c - n * th * 0.4, c + n * th * 1.1)


def leaf(a, b, t, th=0.04):
    """Feuille : losange arrondi de a-b (base) vers t, avec une nervure."""
    a, b, t = (np.asarray(p, float) for p in (a, b, t))
    base = (a + b) / 2
    side = (b - a) * 0.42
    m1, m2 = base + (t - base) * 0.4 + side, base + (t - base) * 0.4 - side
    n = np.cross(t - base, side); n = n / np.linalg.norm(n) * th / 2
    rim = [base, m1, t, m2]
    vs = [p + n for p in rim] + [p - n for p in rim] + [base + (t - base) * 0.45 + n * 2.5, base + (t - base) * 0.45 - n * 2.5]
    fs = [(0, 1, 8), (1, 2, 8), (2, 3, 8), (3, 0, 8), (5, 4, 9), (6, 5, 9), (7, 6, 9), (4, 7, 9)]
    return mesh(vs, fs)


def flame(a, b, t):
    """Langue de flamme : deux pointes larges de longueurs inégales, la grande relevée."""
    a, b, t = (np.asarray(p, float) for p in (a, b, t))
    out = []
    for f0, f1, k, lift in ((0.0, 0.65, 1.05, 0.3), (0.4, 1.0, 0.7, -0.15)):
        p0, p1 = a + (b - a) * f0, a + (b - a) * f1
        tip = (p0 + p1) / 2 + (t - (a + b) / 2) * k + np.array([0, lift, 0])
        out.append(blade(p0, p1, tip, th=0.07))
    return out


def torn(a, b, t):
    """Lame déchirée : deux pointes séparées par une encoche."""
    a, b, t = (np.asarray(p, float) for p in (a, b, t))
    mid = (a + b) / 2
    return [blade(a, mid, (a + mid) / 2 + (t - mid) * 1.0), blade(mid, b, (mid + b) / 2 + (t - mid) * 0.62)]


def crystal(base, d, r, ln):
    """Cristal hexagonal : prisme puis pointe."""
    base, d = np.asarray(base, float), np.asarray(d, float) / np.linalg.norm(d)
    return sweep([base, base + d * ln * 0.45, base + d * ln * 0.75], [r, r, r * 0.85], 6)


def flat_quads(m, max_angle=0.45):
    """Ombrage par quadrilatère : appaire les faces voisines presque coplanaires et moyenne leur normale."""
    adj, ang = m.face_adjacency, m.face_adjacency_angles
    order = np.argsort(ang)
    used = np.zeros(len(m.faces), bool)
    fn = m.face_normals.copy()
    for i in order:
        if ang[i] > max_angle:
            break
        f0, f1 = adj[i]
        if used[f0] or used[f1]:
            continue
        used[f0] = used[f1] = True
        nn = fn[f0] + fn[f1]; nn /= np.linalg.norm(nn)
        fn[f0] = fn[f1] = nn
    return fn


# ---------- collerettes par lignée ----------
JOUES = [((0.86, 0.42, -0.45), (0.9, 0.22, -0.95), (1.85, 0.75, 0.15)),
         ((0.97, 0.12, -0.3), (0.97, -0.02, -0.85), (2.05, -0.05, 0.25)),
         ((0.7, 0.75, 0.05), (0.8, 0.55, -0.35), (1.5, 1.35, 0.55))]
MACH = [((0.86, -0.45, -0.25), (0.82, -0.64, -0.9), (1.85, -0.98, 0.35)),
        ((0.58, -0.95, -0.15), (0.52, -0.9, -0.75), (1.3, -1.6, 0.3))]


def frills(lin, specs):
    L = {"spike": [], "tip": [], "membrane": []}
    for a, b, t in specs:
        if lin == "Feu":
            fl = flame(a, b, t)
            L["spike"] += sum((both(m) for m in fl), [])
            inner = blade(np.add(a, (0.02, 0, 0)), np.add(b, (0.02, 0, 0)), np.add(a, np.subtract(t, a) * 0.5))
            L["tip"] += both(inner)
        elif lin == "Glace":
            L["spike"] += both(blade(a, b, np.add(t, (0, 0.15, 0.1)), th=0.035))
        elif lin == "Foret":
            L["spike"] += both(leaf(a, b, t))
        else:
            L["spike"] += sum((both(m) for m in torn(a, b, t)), [])
    return L


# ---------- pièces ----------
def head_layers(lin):
    rings = [section(z, top, [b, e, c, l], bot) for z, top, b, e, c, l, bot in CRANE]
    L = {"skin": [loft(rings, T6.NUQUE, T6.BEC)], "horn": [], "spike": [], "teeth": [], "eye": [], "pupil": [],
         "back": [], "limb": [], "tip": [], "membrane": [], "glow": []}
    # cornes v6 (inchangées)
    path = curve([(0.48, 0.95, -0.35), (0.92, 1.55, -0.1), (1.45, 2.05, 0.3), (1.92, 2.55, 0.85),
                  (1.98, 3.15, 1.2), (1.55, 3.62, 1.05), (1.05, 3.72, 0.75)], 3)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, 0.35, 0.75, 1], [0.5, 0.36, 0.2, 0.04])
    L["horn"] += both(sweep(path, rad, 6, rides=0.14))
    path = curve([(0.82, 0.62, -0.25), (1.35, 0.8, 0.25), (1.8, 0.85, 0.8)], 3)
    L["horn"] += both(sweep(path, np.interp(np.linspace(0, 1, len(path)), [0, 1], [0.17, 0.03]), 5))
    # collerettes de joue + épine d'arcade
    for k, v in frills(lin, JOUES).items():
        L[k] += v
    if lin != "Ombre":
        L["spike"] += both(blade((0.92, 1.17, -0.85), (0.8, 1.12, -0.45), (1.45, 1.55, -0.05)))
    # crête centrale
    for z, h, l in ((-0.1, 0.42, 0.4), (0.3, 0.32, 0.35)):
        top = crane_at(z, 1)
        L["spike"].append(blade((0, top - 0.02, z - l / 2), (0, top - 0.02, z + l / 2), (0, top + h, z + l * 0.6)))
    # plaques sur l'arête du nez (écorce pour la Forêt)
    for i, z in enumerate((-1.62, -1.95, -2.28, -2.6, -2.88)):
        top, slope = crane_at(z, 1), (crane_at(z - 0.05, 1) - crane_at(z + 0.05, 1)) / -0.1
        n = np.array([0, 1, -slope])
        w = 0.42 - i * 0.05
        L["horn" if lin == "Foret" else "back"].append(plate((0, top + 0.01, z), (0, slope * -1, -1), n, w, 0.42, 0.06))
    # rangée d'écailles sur les joues
    for z, y in ((-0.45, 0.22), (-0.8, 0.2), (-1.15, 0.16), (-1.5, 0.15)):
        cx, _ = crane_at(z, 4)
        L["limb"] += both(plate((cx - 0.02, y, z), (0, -0.15, -1), (1, 0.1, 0), 0.22, 0.34, 0.05))
    # narines (de braise pour le Feu)
    for s in (1,):
        z = -2.95
        top = crane_at(z, 1)
        nos = plate((0.17, top - 0.04, z), (0.3, 0, -1), (0.4, 1, -0.4), 0.08, 0.2, 0.04)
        L["glow" if lin == "Feu" else "pupil"] += both(nos)
    # crocs du haut
    for x, z, ln in ((0.24, -2.62, 0.52), (0.44, -2.2, 0.3), (0.55, -1.85, 0.22)):
        L["teeth"] += both(cone((x, -0.06, z), (x + 0.02, -0.06 - ln, z - 0.04), 0.1 if ln > 0.4 else 0.065))
    eyes, pupils = T6.eye_meshes()
    L["eye"] += eyes
    L["pupil"] += pupils
    # ---- traits de lignée ----
    if lin == "Feu":     # petites cornes d'arcade vers l'avant
        L["horn"] += both(sweep(curve([(0.78, 1.1, -1.0), (0.98, 1.4, -1.35), (1.05, 1.62, -1.75)], 2), [0.13, 0.1, 0.07, 0.04, 0.02], 5))
    elif lin == "Glace":  # cristaux sur l'arcade et les joues
        for base, d, r, ln in (((0.85, 1.12, -0.75), (0.5, 1, 0.5), 0.12, 0.9), ((0.7, 1.08, -0.45), (0.2, 1, 0.7), 0.09, 0.65),
                               ((0.95, 0.35, -0.6), (1, 0.4, 0.5), 0.1, 0.7), ((0.92, -0.05, -0.5), (1, -0.2, 0.6), 0.08, 0.55)):
            L["spike"] += both(crystal(base, d, r, ln))
    elif lin == "Ombre":  # couronne d'épines + runes lumineuses
        for z, x, y in ((-0.6, 0.82, 1.12), (-0.9, 0.9, 1.18), (-1.2, 0.86, 1.14), (-1.5, 0.7, 0.96)):
            L["spike"] += both(cone((x, y - 0.05, z), (x + 0.22, y + 0.4, z + 0.18), 0.07, 4))
        for a, b in (((0.97, 0.05, -0.6), (0.93, -0.02, -1.0)), ((0.9, 0.0, -1.1), (0.78, 0.0, -1.45)),
                     ((0.85, 0.32, -0.55), (0.92, 0.12, -0.75))):
            a, b = np.array(a), np.array(b)
            L["glow"] += both(plate((a + b) / 2 + [0.04, 0, 0], b - a, (1, 0.1, 0), 0.05, np.linalg.norm(b - a), 0.02))
    return L


def jaw_layers(lin):
    rings = [section(z, top, [l, s, b], k) for z, top, l, s, b, k in MACHOIRE]
    L = {"skin": [loft(rings, T6.ARRIERE_M, T6.MENTON)], "spike": [], "teeth": [], "tip": [], "membrane": []}
    for k, v in frills(lin, MACH).items():
        L[k] += v
    for x, z, ln in ((0.2, -2.6, 0.45), (0.42, -2.0, 0.24)):
        L["teeth"] += both(cone((x, -0.2, z), (x + 0.01, -0.2 + ln, z + 0.03), 0.085 if ln > 0.3 else 0.06))
    if lin == "Glace":    # stalactites sous le menton
        for x, z, ln in ((0.0, -2.5, 0.55), (0.18, -2.15, 0.4), (0.3, -1.7, 0.3)):
            ms = [cone((x, -0.5, z), (x, -0.5 - ln, z + 0.08), 0.07, 5)]
            L["spike"] += ms if x == 0 else both(ms[0])
    elif lin == "Foret":  # barbe de mousse
        for x, z, ln in ((0.0, -2.35, 0.5), (0.16, -2.05, 0.45), (0.28, -1.65, 0.4), (0.1, -1.7, 0.55)):
            ms = [blade((x - 0.08, -0.55, z), (x + 0.08, -0.55, z + 0.15), (x, -0.55 - ln, z + 0.35), th=0.04)]
            L["membrane"] += ms if x == 0 else both(ms[0])
    elif lin == "Ombre":  # barbillons
        for s in (1, -1):
            p = curve([(s * 0.18, -0.4, -2.6), (s * 0.25, -0.9, -2.3), (s * 0.3, -1.4, -1.7), (s * 0.4, -1.65, -1.1)], 3)
            L["spike"].append(sweep(p, np.interp(np.linspace(0, 1, len(p)), [0, 1], [0.06, 0.015]), 4))
    return L


def slots(m, which):
    c, n = m.triangles_center, m.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if which == "head":
            if abs(x) < 0.3 and y > 0.5:
                out.append("back")
            elif 0.42 < abs(x) < 0.95 and 0.3 < y < 0.8 and -2.0 < z < -0.6:
                out.append("back")
            else:
                out.append("skin")
        elif which == "jaw":   # plaques ventrales : bandes alternées
            out.append(("belly" if int(np.floor(-z / 0.38)) % 2 == 0 else "limb") if ny < -0.55 else "skin")
        else:
            out.append("back" if ny > 0.75 else ("belly" if ny < -0.6 else "skin"))
    return out


def finish(m, local=True):
    """Passe en repère monde, sépare les sommets et applique l'ombrage par quadrilatère."""
    w = m.copy()
    if local:
        w.vertices = HB + HS * (w.vertices @ HEAD_R.T)
    w = trimesh.Trimesh(w.vertices, w.faces, process=False)
    fn = flat_quads(w)
    w.unmerge_vertices()
    w.vertex_normals = np.repeat(fn, 3, axis=0)
    return w


def build(lin):
    jp = tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS)
    N = T6.neck_layers(lin)
    out = {"Neck": {"parent": None, "pivot": tuple(V.NECK[0]),
                    "layers": {k: finish(m, False) for k, m in N.items()}, "slots": {"skin": slots(N["skin"], "neck")}}}
    for name, fn, piv, which in (("Head", head_layers, tuple(HB), "head"), ("Jaw", jaw_layers, jp, "jaw")):
        L = {k: trimesh.util.concatenate(v) for k, v in fn(lin).items() if v}
        out[name] = {"parent": "Neck", "pivot": piv, "layers": {k: finish(m) for k, m in L.items()},
                     "slots": {"skin": slots(L["skin"], which)}}
    return out


def main():
    hc = HB + HEAD_R @ np.array([0, 1.3, -1.0]) * HS
    vues = [("Face", np.array([0.0, 0.6, -15.0])), ("3/4", np.array([-10.0, 2.4, -11.0])),
            ("Profil", np.array([-15.5, 0.6, 0.0])), ("3/4 bas", np.array([-9.0, -6.0, -10.0]))]
    cw, ch, lw = 400, 330, 230
    W, H = lw + cw * len(vues) + 10, 110 + ch * len(LIGNEES) + 60
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — tête v7 : détails et lignées", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Tête et cornes v6 ; plaques sur le nez, écailles de joue, plaques de mâchoire, narines, ombrage par face ; "
                      "un jeu de détails par lignée.", font=f(17), fill=(150, 160, 184))
    traits = {"Feu": "collerettes en flammes (2 tons), cornes d'arcade, narines de braise",
              "Glace": "cristaux sur l'arcade et les joues, stalactites sous le menton",
              "Foret": "collerettes en feuilles, barbe de mousse, nez en écorce",
              "Ombre": "collerettes déchirées, couronne d'épines, runes lumineuses, barbillons"}
    for i, lin in enumerate(LIGNEES):
        m = build(lin)
        pal = dict(V.VARIANTS[lin]); pal["glow"] = pal["eye"]
        it = rendu.gather(m, pal)
        y0 = 100 + i * ch
        n_tris = sum(len(x.faces) for k in ("Head", "Jaw") for x in m[k]["layers"].values())
        dr.text((20, y0 + 20), NOMS[lin], font=f(22, True), fill=(230, 232, 240))
        yy = y0 + 56
        words, cur = traits[lin].split(), ""
        for w in words:
            if len(cur) + len(w) > 24:
                dr.text((20, yy), cur, font=f(15), fill=(180, 186, 204)); yy += 21; cur = w
            else:
                cur = (cur + " " + w).strip()
        dr.text((20, yy), cur, font=f(15), fill=(180, 186, 204))
        dr.text((20, yy + 34), f"{n_tris} triangles", font=f(14), fill=(140, 150, 172))
        for j, (t, off) in enumerate(vues):
            board.paste(rendu.render(it, hc + off, hc, size=(cw - 8, ch - 8), fov=31), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        print(lin, n_tris, flush=True)
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-tete-v7.png"))


if __name__ == "__main__":
    main()
