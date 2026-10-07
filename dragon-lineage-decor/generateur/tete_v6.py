# Tête de dragon v6 : la v5 (polygones à la main) avec les retouches demandées.
#   - cornes plus épaisses et plus enroulées (en lyre : montent, s'écartent, puis reviennent vers l'intérieur)
#   - museau plus court et plus haut (moins « rapace »), mâchoire plus profonde
#   - cou refait en polygones (plus de cou lisse SDF qui jurait avec la tête)
#   - yeux retravaillés : amande plus grande, paupière du haut droite qui plonge vers le nez (regard froncé),
#     pupille en fente verticale, orbite sombre autour, œil orienté un peu vers l'avant pour être lu de face
# Usage : python3 tete_v6.py  ->  ../concept-tete-v6.png
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
from tete_v5 import section, loft, mesh, blade, sweep, cone, curve, both, FONT, FONT_B

HB, HEAD_R, HS = V.HB, V.HEAD_R, V.HS

# (z, dessus, arcade, orbite, joue, lèvre, palais) — côté droit, le gauche est le miroir
CRANE = [
    (0.45, 0.62, (0.42, 0.58), (0.58, 0.30), (0.62, 0.00), (0.50, -0.30), -0.36),
    (0.00, 1.00, (0.60, 0.92), (0.84, 0.52), (0.95, 0.05), (0.80, -0.32), -0.42),
    (-0.60, 1.02, (0.82, 1.12), (0.84, 0.55), (1.00, 0.10), (0.86, -0.14), -0.20),
    (-1.10, 0.90, (0.96, 1.22), (0.62, 0.50), (0.88, 0.10), (0.78, -0.04), -0.06),
    (-1.60, 0.80, (0.66, 0.90), (0.54, 0.42), (0.74, 0.12), (0.70, -0.06), -0.08),
    (-2.00, 0.74, (0.40, 0.72), (0.52, 0.40), (0.64, 0.12), (0.62, -0.08), -0.09),
    (-2.45, 0.67, (0.30, 0.62), (0.46, 0.34), (0.55, 0.08), (0.53, -0.10), -0.10),
    (-2.85, 0.55, (0.24, 0.50), (0.37, 0.24), (0.42, 0.00), (0.40, -0.14), -0.14),
    (-3.10, 0.30, (0.15, 0.25), (0.25, 0.06), (0.27, -0.12), (0.22, -0.27), -0.27),
]
BEC = (0.0, -0.52, -3.25)
NUQUE = (0.0, 0.15, 0.62)

# (z, dedans, lèvre, flanc, bas, quille) — plus profonde, plus courte
MACHOIRE = [
    (0.15, -0.22, (0.74, -0.22), (0.86, -0.64), (0.54, -1.06), -1.12),
    (-0.60, -0.20, (0.80, -0.18), (0.86, -0.58), (0.50, -0.92), -0.98),
    (-1.40, -0.12, (0.68, -0.10), (0.68, -0.38), (0.44, -0.70), -0.76),
    (-2.15, -0.14, (0.52, -0.12), (0.52, -0.34), (0.34, -0.58), -0.62),
    (-2.70, -0.16, (0.36, -0.15), (0.35, -0.32), (0.22, -0.48), -0.52),
]
MENTON = (0.0, -0.34, -2.92)
ARRIERE_M = (0.0, -0.64, 0.40)


def eye_meshes():
    """Œil en amande : paupière du haut droite et inclinée, bord du bas arrondi, bombé ; pupille en fente."""
    inner, outer = np.array([0.53, 0.43, -1.78]), np.array([0.86, 0.74, -0.86])
    n = np.array([1.0, 0.12, -0.55]); n /= np.linalg.norm(n)              # regarde un peu vers l'avant
    u = outer - inner; L = np.linalg.norm(u); u /= L
    v = np.cross(n, u); v /= np.linalg.norm(v)
    if v[1] < 0:
        v = -v
    rim = [inner]
    for t in (0.25, 0.5, 0.75):                                          # paupière du haut : presque droite
        rim.append(inner + u * L * t + v * (0.07 + 0.03 * t))
    rim.append(outer)
    for t in (0.75, 0.5, 0.25):                                          # bord du bas : arrondi
        rim.append(inner + u * L * t - v * 0.15 * np.sin(np.pi * t) ** 0.8)
    rim = [p + n * 0.03 for p in rim]
    c = inner + u * L * 0.5 - v * 0.03
    top, back = c + n * 0.09, c - n * 0.06
    k = len(rim)
    vs = rim + [top, back]
    fs = [(i, (i + 1) % k, k) for i in range(k)] + [((i + 1) % k, i, k + 1) for i in range(k)]
    eye = mesh(vs, fs)
    pc = c + n * 0.1
    h, w = 0.15, 0.06
    pv = [pc + v * h, pc + u * w, pc - v * h, pc - u * w, pc + n * 0.02, pc - n * 0.03]
    pf = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)]
    return both(eye), both(mesh(pv, pf))


def head_layers(lin="Feu"):
    rings = [section(z, top, [b, e, c, l], bot) for z, top, b, e, c, l, bot in CRANE]
    skin = loft(rings, NUQUE, BEC)
    horns, spikes, teeth = [], [], []
    # cornes en lyre, épaisses et annelées
    path = curve([(0.48, 0.95, -0.35), (0.92, 1.55, -0.1), (1.45, 2.05, 0.3), (1.92, 2.55, 0.85),
                  (1.98, 3.15, 1.2), (1.55, 3.62, 1.05), (1.05, 3.72, 0.75)], 3)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, 0.35, 0.75, 1], [0.5, 0.36, 0.2, 0.04])
    horns += both(sweep(path, rad, 6, rides=0.14))
    # petites cornes de tempe
    path = curve([(0.82, 0.62, -0.25), (1.35, 0.8, 0.25), (1.8, 0.85, 0.8)], 3)
    horns += both(sweep(path, np.interp(np.linspace(0, 1, len(path)), [0, 1], [0.17, 0.03]), 5))
    # collerettes en lames + épine d'arcade
    for a, b, t in (((0.86, 0.42, -0.45), (0.9, 0.22, -0.95), (1.85, 0.75, 0.15)),
                    ((0.97, 0.12, -0.3), (0.97, -0.02, -0.85), (2.05, -0.05, 0.25)),
                    ((0.7, 0.75, 0.05), (0.8, 0.55, -0.35), (1.5, 1.35, 0.55)),
                    ((0.92, 1.17, -0.85), (0.8, 1.12, -0.45), (1.45, 1.55, -0.05))):
        spikes += both(blade(a, b, t))
    # crête centrale
    for z, h, l in ((-0.1, 0.42, 0.4), (0.3, 0.32, 0.35), (-1.8, 0.16, 0.3), (-2.25, 0.12, 0.25)):
        top = np.interp(-z, [-c[0] for c in CRANE], [c[1] for c in CRANE])
        spikes.append(blade((0, top - 0.02, z - l / 2), (0, top - 0.02, z + l / 2), (0, top + h, z + l * 0.6)))
    for x, z, ln in ((0.24, -2.62, 0.52), (0.44, -2.2, 0.3), (0.55, -1.85, 0.22)):
        teeth += both(cone((x, -0.06, z), (x + 0.02, -0.06 - ln, z - 0.04), 0.1 if ln > 0.4 else 0.065))
    eyes, pupils = eye_meshes()
    cat = trimesh.util.concatenate
    return {"skin": skin, "horn": cat(horns), "spike": cat(spikes), "teeth": cat(teeth), "eye": cat(eyes), "pupil": cat(pupils)}


def jaw_layers(lin="Feu"):
    rings = [section(z, top, [l, s, b], k) for z, top, l, s, b, k in MACHOIRE]
    skin = loft(rings, ARRIERE_M, MENTON)
    spikes, teeth = [], []
    for a, b, t in (((0.86, -0.45, -0.25), (0.82, -0.64, -0.9), (1.85, -0.98, 0.35)),
                    ((0.58, -0.95, -0.15), (0.52, -0.9, -0.75), (1.3, -1.6, 0.3))):
        spikes += both(blade(a, b, t))
    for x, z, ln in ((0.2, -2.6, 0.45), (0.42, -2.0, 0.24)):
        teeth += both(cone((x, -0.2, z), (x + 0.01, -0.2 + ln, z + 0.03), 0.085 if ln > 0.3 else 0.06))
    cat = trimesh.util.concatenate
    return {"skin": skin, "spike": cat(spikes), "teeth": cat(teeth)}


# ---------- cou en polygones ----------
def neck_layers(lin="Feu"):
    ctrl = [(0, 5.0, -1.9), (0, 5.75, -2.95), (0, 6.85, -3.95), (0, 7.55, -4.75), (0, 7.75, -5.1)]
    path = np.asarray(curve(ctrl, 2), float)
    rads = np.interp(np.linspace(0, 1, len(path)), [0, 0.4, 1], [1.45, 1.12, 0.9])
    T = np.gradient(path, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    shape = [(0, 1.08), (0.62, 0.82), (1.0, 0.18), (0.9, -0.5), (0.45, -0.92), (0, -0.98),
             (-0.45, -0.92), (-0.9, -0.5), (-1.0, 0.18), (-0.62, 0.82)]
    rings = []
    for p, t, r in zip(path, T, rads):
        x = np.array([1.0, 0, 0])
        up = np.cross(t, x); up /= np.linalg.norm(up)
        if up[1] < 0:
            up = -up
        rings.append([p + r * (sx * x + sy * up) for sx, sy in shape])
    skin = loft(rings, path[0] - T[0] * 0.1, path[-1] + T[-1] * 0.1)
    spikes = []
    for i in range(1, len(path) - 1, 2):     # crête dorsale en lames, plus petites vers la tête
        p, t, r = path[i], T[i], rads[i]
        x = np.array([1.0, 0, 0]); up = np.cross(t, x); up /= np.linalg.norm(up)
        up = up if up[1] > 0 else -up
        base = p + up * r * 1.02
        h = 0.55 * r + 0.1
        spikes.append(blade(base - t * 0.3, base + t * 0.3, base + up * h + t * 0.45))
    return {"skin": skin, "spike": trimesh.util.concatenate(spikes)}


def slots(m, which):
    c, n = m.triangles_center, m.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if which == "head":
            if abs(x) < 0.3 and y > 0.5:
                out.append("back")
            elif 0.42 < abs(x) < 0.95 and 0.3 < y < 0.8 and -2.0 < z < -0.6:
                out.append("back")                 # orbite sombre : l'œil ressort
            else:
                out.append("skin")
        elif which == "jaw":
            out.append("belly" if ny < -0.55 else "skin")
        else:   # cou (coordonnées monde) : dos sombre, gorge en plaques
            out.append("back" if ny > 0.75 else ("belly" if ny < -0.6 else "skin"))
    return out


def build(lin="Feu"):
    jp = tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS)
    out = {}
    N = neck_layers(lin)
    nl = {}
    for k, m in N.items():
        m = m.copy(); m.unmerge_vertices(); nl[k] = m
    out["Neck"] = {"parent": None, "pivot": tuple(V.NECK[0]), "layers": nl, "slots": {"skin": slots(N["skin"], "neck")}}
    for name, fn, piv, which in (("Head", head_layers, tuple(HB), "head"), ("Jaw", jaw_layers, jp, "jaw")):
        L = fn(lin)
        lay = {}
        for k, m in L.items():
            w = m.copy()
            w.vertices = HB + HS * (w.vertices @ HEAD_R.T)
            w = trimesh.Trimesh(w.vertices, w.faces, process=False)
            w.unmerge_vertices()
            lay[k] = w
        out[name] = {"parent": "Neck", "pivot": piv, "layers": lay, "slots": {"skin": slots(L["skin"], which)}}
    return out


def tris(m, names=("Head", "Jaw")):
    return sum(len(x.faces) for n in names for x in m[n]["layers"].values())


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
    dr.text((24, 20), "Dragon — tête v6", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), f"Cornes en lyre plus épaisses, museau plus court et plus haut, cou en polygones, yeux retravaillés. "
                      f"{tris(m)} triangles (tête + mâchoire), cou {tris(m, ('Neck',))}.", font=f(17), fill=(150, 160, 184))
    pal = dict(V.VARIANTS["Feu"]); pal["glow"] = pal["eye"]
    it = rendu.gather(m, pal)
    for j, (t, off) in enumerate(vues):
        board.paste(rendu.render(it, hc + off, hc, size=(cw - 8, ch - 8), fov=31), (10 + j * cw, 100))
        dr.text((24 + j * cw, 108), t, font=f(17, True), fill=(255, 210, 122))
    y1 = 110 + ch
    itg = rendu.gather(m, pal, pose={"Jaw": (-20, 0, 0)})
    board.paste(rendu.render(itg, hc + vues[2][1], hc, size=(cw - 8, ch - 8), fov=31), (10, y1))
    dr.text((24, y1 + 8), "Gueule ouverte", font=f(17, True), fill=(255, 210, 122))
    eye_c = HB + HEAD_R @ np.array([0.7, 0.6, -1.3]) * HS
    board.paste(rendu.render(it, eye_c + np.array([-5.5, 1.2, -4.5]), eye_c, size=(cw - 8, ch - 8), fov=24), (10 + cw, y1))
    dr.text((24 + cw, y1 + 8), "Gros plan œil", font=f(17, True), fill=(255, 210, 122))
    for j, lin in enumerate(["Glace", "Foret", "Ombre"]):
        p = dict(V.VARIANTS[lin]); p["glow"] = p["eye"]
        board.paste(rendu.render(rendu.gather(m, p), hc + vues[1][1], hc, size=(cw - 8, ch - 8), fov=31), (10 + (j + 2) * cw, y1))
        dr.text((24 + (j + 2) * cw, y1 + 8), {"Foret": "Forêt"}.get(lin, lin), font=f(17, True), fill=(255, 210, 122))
    notes = ["Yeux : amande plus grande, paupière du haut droite qui plonge vers le nez, fente verticale, orbite sombre.",
             "Cornes en lyre : plus épaisses à la base, annelées, pointes qui reviennent vers l'intérieur.",
             "Museau raccourci et rehaussé, mâchoire plus profonde ; cou en polygones avec crête dorsale en lames."]
    for k, t in enumerate(notes):
        dr.text((24, H - 100 + k * 27), "•  " + t, font=f(16), fill=(200, 206, 222))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-tete-v6.png"))
    print(tris(m), tris(m, ("Neck",)))


if __name__ == "__main__":
    main()
