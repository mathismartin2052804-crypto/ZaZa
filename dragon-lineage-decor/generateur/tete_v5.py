# Tête de dragon v5 : modélisée à la main en polygones (plus de SDF ni de lissage, qui arrondissaient tout).
# D'après la référence de l'utilisateur : arcade en V froncée, yeux enfoncés en fente, tête étroite en losange
# terminée par un bec crochu, cornes de bélier annelées, collerettes en lames sur les joues et la mâchoire.
# Repère local de la tête (le même que dragon_v3) : avant = -Z, Y vers le haut ; monde = HB + HS * HEAD_R @ q.
# Usage : python3 tete_v5.py  ->  ../concept-tete-v5.png
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu

HB, HEAD_R, HS = V.HB, V.HEAD_R, V.HS
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------- crâne + mâchoire du haut : sections (z, dessus, arcade, orbite, joue, lèvre, palais) ----------
# chaque point (x, y) est le côté droit ; le côté gauche est le miroir.
CRANE = [
    (0.45, 0.62, (0.42, 0.58), (0.58, 0.30), (0.62, 0.00), (0.50, -0.30), -0.36),
    (0.00, 1.00, (0.60, 0.92), (0.84, 0.52), (0.95, 0.05), (0.80, -0.32), -0.42),
    (-0.60, 1.02, (0.82, 1.12), (0.84, 0.55), (1.00, 0.10), (0.86, -0.14), -0.20),
    (-1.10, 0.88, (0.94, 1.2), (0.62, 0.52), (0.88, 0.10), (0.76, -0.04), -0.06),
    (-1.60, 0.74, (0.62, 0.86), (0.52, 0.42), (0.72, 0.12), (0.66, -0.06), -0.08),
    (-2.00, 0.64, (0.32, 0.62), (0.48, 0.38), (0.58, 0.12), (0.55, -0.08), -0.09),
    (-2.50, 0.57, (0.24, 0.52), (0.40, 0.30), (0.47, 0.08), (0.45, -0.10), -0.10),
    (-3.00, 0.46, (0.19, 0.40), (0.31, 0.20), (0.34, 0.00), (0.32, -0.13), -0.13),
    (-3.30, 0.22, (0.12, 0.17), (0.20, 0.03), (0.21, -0.12), (0.16, -0.26), -0.26),
]
BEC = (0.0, -0.50, -3.45)          # pointe du bec crochu, plus bas que la gueule
NUQUE = (0.0, 0.15, 0.62)

# mâchoire du bas : (z, dedans, lèvre, flanc, bas, quille) — dessous droit, angle marqué à l'arrière
MACHOIRE = [
    (0.15, -0.22, (0.74, -0.22), (0.84, -0.62), (0.52, -1.02), -1.08),
    (-0.60, -0.20, (0.78, -0.18), (0.84, -0.55), (0.48, -0.86), -0.93),
    (-1.40, -0.12, (0.64, -0.10), (0.64, -0.35), (0.40, -0.62), -0.68),
    (-2.25, -0.14, (0.48, -0.12), (0.48, -0.30), (0.30, -0.48), -0.53),
    (-2.90, -0.16, (0.30, -0.15), (0.29, -0.28), (0.18, -0.38), -0.42),
]
MENTON = (0.0, -0.30, -3.12)       # en retrait du bec : la mâchoire du haut déborde
ARRIERE_M = (0.0, -0.62, 0.40)


def section(z, top, pts, bottom):
    """Anneau : dessus, points droits de haut en bas, dessous, points gauches de bas en haut."""
    right = [(x, y, z) for x, y in pts]
    left = [(-x, y, z) for x, y in pts[::-1]]
    return [(0.0, top, z)] + right + [(0.0, bottom, z)] + left


def loft(rings, start, end):
    """Relie des anneaux successifs et ferme chaque bout par un éventail vers un point."""
    rings = [np.asarray(r, float) for r in rings]
    n = len(rings[0])
    V_ = np.concatenate(rings + [np.asarray([start, end], float)])
    F = []
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            k = (j + 1) % n
            F += [(a + j, b + j, b + k), (a + j, b + k, a + k)]
    s, e = len(V_) - 2, len(V_) - 1
    last = (len(rings) - 1) * n
    for j in range(n):
        k = (j + 1) % n
        F += [(s, k, j), (e, last + j, last + k)]
    return mesh(V_, F)


def mesh(v, f):
    m = trimesh.Trimesh(np.asarray(v, float), np.asarray(f), process=True)
    trimesh.repair.fix_normals(m)
    if m.is_volume and m.volume < 0:
        m.invert()
    return m


def blade(a, b, t, th=0.05):
    """Lame plate (collerette, crête) : base a-b sur la peau, pointe t."""
    a, b, t = (np.asarray(p, float) for p in (a, b, t))
    n = np.cross(b - a, t - a); n = n / np.linalg.norm(n) * th / 2
    v = [a + n, b + n, t + n * 0.3, a - n, b - n, t - n * 0.3]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4), (0, 4, 1), (1, 4, 5), (1, 5, 2), (2, 5, 3), (2, 3, 0)]
    return mesh(v, f)


def sweep(path, radii, sides=6, rides=0.0):
    """Tube polygonal le long d'un chemin (repères transportés) ; rides : anneaux de corne."""
    P = np.asarray(path, float)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    nrm = np.cross(T[0], [0, 1, 0] if abs(T[0][1]) < 0.9 else [1, 0, 0]); nrm /= np.linalg.norm(nrm)
    rings = []
    for i, (p, t) in enumerate(zip(P, T)):
        nrm = nrm - t * (nrm @ t); nrm /= np.linalg.norm(nrm)
        bi = np.cross(t, nrm)
        r = radii[i] * (1 + rides if (rides and i % 2 == 1 and i < len(P) - 2) else 1)
        rings.append([p + r * (np.cos(a) * nrm + np.sin(a) * bi) for a in np.linspace(0, 2 * np.pi, sides, endpoint=False)])
    tip = P[-1] + T[-1] * radii[-1] * 2
    return loft(rings[:-1] + [rings[-1]], P[0] - T[0] * 0.05, tip)


def cone(a, b, r, sides=4):
    return sweep([a, (np.add(a, b)) / 2, b], [r, r * 0.55, r * 0.15], sides)


def curve(pts, n=3):
    from sdf import catmull
    return catmull(pts, n)


def mirror(m):
    m2 = m.copy(); m2.vertices[:, 0] *= -1; m2.invert(); return m2


def both(m):
    return [m, mirror(m)]


# ---------- pièces ----------
def head_layers(lin="Feu"):
    rings = [section(z, top, [b, e, c, l], bot) for z, top, b, e, c, l, bot in CRANE]
    skin = loft(rings, NUQUE, BEC)
    horns, spikes, teeth, eyes, pupils = [], [], [], [], []
    # cornes de bélier : montent vers l'arrière, s'écartent puis reviennent vers l'intérieur
    path = curve([(0.5, 0.95, -0.3), (0.95, 1.55, 0.05), (1.55, 2.05, 0.5), (1.98, 2.6, 1.1), (1.95, 3.2, 1.6), (1.6, 3.45, 1.75)], 3)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, 0.4, 1], [0.38, 0.26, 0.04])
    horns += both(sweep(path, rad, 6, rides=0.12))
    # petites cornes de tempe, vers l'extérieur et l'arrière
    path = curve([(0.82, 0.62, -0.25), (1.35, 0.82, 0.25), (1.85, 0.92, 0.85)], 3)
    horns += both(sweep(path, np.interp(np.linspace(0, 1, len(path)), [0, 1], [0.15, 0.03]), 5))
    # collerettes en lames sur les joues (la mâchoire porte les siennes)
    for a, b, t in (((0.86, 0.42, -0.45), (0.9, 0.22, -0.95), (1.85, 0.75, 0.15)),
                    ((0.97, 0.12, -0.3), (0.97, -0.02, -0.85), (2.05, -0.05, 0.25)),
                    ((0.7, 0.75, 0.05), (0.8, 0.55, -0.35), (1.5, 1.35, 0.55))):
        spikes += both(blade(a, b, t))
    for a, b, t in (((0.9, 1.15, -0.85), (0.78, 1.1, -0.45), (1.45, 1.55, -0.05)),):   # épines d'arcade
        spikes += both(blade(a, b, t))
    # crête centrale : petites lames entre les cornes et sur l'arête du nez
    for z, h, l in ((-0.1, 0.42, 0.4), (0.3, 0.32, 0.35), (-1.8, 0.16, 0.3), (-2.3, 0.12, 0.25)):
        top = np.interp(-z, [-c[0] for c in CRANE], [c[1] for c in CRANE])
        spikes.append(blade((0, top - 0.02, z - l / 2), (0, top - 0.02, z + l / 2), (0, top + h, z + l * 0.6)))
    # crocs du haut
    for x, z, ln in ((0.3, -2.75, 0.5), (0.42, -2.35, 0.3), (0.5, -1.95, 0.22)):
        teeth += both(cone((x, -0.06, z), (x + 0.02, -0.06 - ln, z - 0.04), 0.09 if ln > 0.4 else 0.06))
    # yeux : fentes inclinées sous l'arcade, qui plongent vers le nez (regard froncé)
    for s in (1,):
        a, b = np.array([0.82, 0.7, -0.95]), np.array([0.56, 0.45, -1.75])
        mid, up = (a + b) / 2, np.array([0, 0.11, 0.03])
        out = np.array([0.09, 0.03, 0])
        ey = mesh([a, mid + up, b, mid - up, mid + out], [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2), (0, 2, 1)])
        eyes += both(ey)
        pc = mid + out * 1.02
        pu = mesh([pc + up * 0.95, pc + [0.012, 0, 0.03], pc - up * 0.95, pc + [0.012, 0, -0.03], pc + out * 0.3],
                  [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (0, 3, 2), (0, 2, 1)])
        pupils += both(pu)
    return {"skin": skin, "horn": trimesh.util.concatenate(horns), "spike": trimesh.util.concatenate(spikes),
            "teeth": trimesh.util.concatenate(teeth), "eye": trimesh.util.concatenate(eyes),
            "pupil": trimesh.util.concatenate(pupils)}


def jaw_layers(lin="Feu"):
    rings = [section(z, top, [l, s, b], k) for z, top, l, s, b, k in MACHOIRE]
    skin = loft(rings, ARRIERE_M, MENTON)
    spikes, teeth = [], []
    for a, b, t in (((0.84, -0.45, -0.25), (0.8, -0.62, -0.9), (1.85, -0.95, 0.35)),
                    ((0.56, -0.92, -0.15), (0.5, -0.86, -0.75), (1.3, -1.55, 0.3))):
        spikes += both(blade(a, b, t))
    for x, z, ln in ((0.22, -2.8, 0.42), (0.4, -2.15, 0.22)):
        teeth += both(cone((x, -0.2, z), (x + 0.01, -0.2 + ln, z + 0.03), 0.08 if ln > 0.3 else 0.055))
    return {"skin": skin, "spike": trimesh.util.concatenate(spikes), "teeth": trimesh.util.concatenate(teeth)}


def color_slots(layer_skin, which):
    """Couleur par face : arête sombre sur le dessus, orbites sombres, dessous de mâchoire en plaques claires."""
    c = layer_skin.triangles_center
    n = layer_skin.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if which == "head":
            if abs(x) < 0.3 and y > 0.45:
                out.append("back")
            elif 0.45 < abs(x) < 0.9 and 0.3 < y < 0.75 and -1.9 < z < -0.8:
                out.append("back")       # orbite enfoncée, plus sombre
            else:
                out.append("skin")
        else:
            out.append("belly" if ny < -0.55 else "skin")
    return out


def to_world(m, frame=True):
    m = m.copy()
    m.vertices = HB + HS * (m.vertices @ HEAD_R.T)
    return m


def build(lin="Feu"):
    jp = tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS)
    layers, slots = V.build_segment(V.neck(lin), 260)
    out = {"Neck": {"parent": None, "pivot": tuple(V.NECK[0]), "layers": layers, "slots": slots}}
    for name, fn, piv in (("Head", head_layers, tuple(HB)), ("Jaw", jaw_layers, jp)):
        L = fn(lin)
        sl = {"skin": color_slots(L["skin"], "head" if name == "Head" else "jaw")}
        lay = {}
        for k, m in L.items():
            w = to_world(m)
            if k == "skin":
                w = trimesh.Trimesh(w.vertices, w.faces, process=False)
            w.unmerge_vertices()
            lay[k] = w
        out[name] = {"parent": "Neck", "pivot": piv, "layers": lay, "slots": sl}
    return out


def head_tris(m):
    return sum(len(x.faces) for n in ("Head", "Jaw") for x in m[n]["layers"].values())


def main():
    hc = HB + HEAD_R @ np.array([0, 1.3, -1.0]) * HS
    vues = [("Face", np.array([0.0, 0.6, -15.0])), ("3/4", np.array([-10.0, 2.4, -11.0])),
            ("Profil", np.array([-15.5, 0.6, 0.0])), ("3/4 arrière", np.array([-11.0, 4.0, 8.0])),
            ("3/4 bas", np.array([-9.0, -6.0, -10.0]))]
    m = build("Feu")
    cw, ch = 372, 340
    W, H = cw * len(vues) + 20, 120 + 2 * ch + 150
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — tête v5, modélisée en polygones", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), f"D'après la référence : arcade en V, yeux en fente, bec crochu, cornes de bélier, collerettes. "
                      f"{head_tris(m)} triangles (tête + mâchoire).", font=f(17), fill=(150, 160, 184))
    pal = dict(V.VARIANTS["Feu"]); pal["glow"] = pal["eye"]
    it = rendu.gather(m, pal)
    for j, (t, off) in enumerate(vues):
        board.paste(rendu.render(it, hc + off, hc, size=(cw - 8, ch - 8), fov=31), (10 + j * cw, 100))
        dr.text((24 + j * cw, 108), t, font=f(17, True), fill=(255, 210, 122))
    # gueule ouverte + les 4 lignées (palettes seules : les traits de forme viendront ensuite)
    y1 = 110 + ch
    itg = rendu.gather(m, pal, pose={"Jaw": (-20, 0, 0)})
    board.paste(rendu.render(itg, hc + vues[2][1], hc, size=(cw - 8, ch - 8), fov=31), (10, y1))
    dr.text((24, y1 + 8), "Gueule ouverte (profil)", font=f(17, True), fill=(255, 210, 122))
    for j, lin in enumerate(["Feu", "Glace", "Foret", "Ombre"]):
        p = dict(V.VARIANTS[lin]); p["glow"] = p["eye"]
        board.paste(rendu.render(rendu.gather(m, p), hc + vues[1][1], hc, size=(cw - 8, ch - 8), fov=31), (10 + (j + 1) * cw, y1))
        dr.text((24 + (j + 1) * cw, y1 + 8), {"Foret": "Forêt"}.get(lin, lin), font=f(17, True), fill=(255, 210, 122))
    notes = ["Tête en coin étroit qui finit en bec crochu ; aucune truffe ronde, la mâchoire du haut déborde.",
             "Arcade en V : arêtes hautes à l'extérieur qui plongent vers le nez, orbites assombries, yeux en fente inclinés.",
             "Cornes de bélier annelées + petites cornes de tempe ; collerettes en lames sur les joues et la mâchoire.",
             "Mâchoire séparée (pivot inchangé) pour l'animation ; couleurs = mêmes emplacements de palette que la v3."]
    for k, t in enumerate(notes):
        dr.text((24, H - 120 + k * 27), "•  " + t, font=f(16), fill=(200, 206, 222))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-tete-v5.png"))
    print(head_tris(m))


if __name__ == "__main__":
    main()
