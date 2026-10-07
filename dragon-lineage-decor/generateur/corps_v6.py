# Corps de dragon v6 : corps v5 « Athlétique » (masse 0,5) + tête Prédateur v8, avec les corrections retenues
# sur le comparatif tête / corps et un corps « taillé » au lieu de « pâte à modeler » :
#   proportions : tête x1,45, cou raccourci de 20 %, queue raccourcie de 20 %, plus épaisse et un peu relevée
#   hiérarchie   : corps, crête et ailes un cran plus sombres que la tête ; la tête garde les couleurs vives
#   taillé       : muscles en prismes à facettes (plus de boules lisses), tronc à pans nets
#   os saillants : omoplates, côtes, bréchet, bassin, coudes, genoux, poignets, jarrets
#   contre-ombrage : dos sombre, flancs moyens, ventre clair (seuils par orientation des faces)
#   fusion       : peau + muscles de chaque morceau réunis par union booléenne (plus de faces superposées)
# Mêmes noms de morceaux que la v4/v5 (Torso, Neck, Head, Jaw, Tail1-4, pattes, ailes) pour export_dragon.py.
# Usage : python3 corps_v6.py  ->  ../concept-dragon-v6.png (avant / après, gros plans, silhouettes)
import os
from contextlib import contextmanager
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
import rendu
import tete_v7 as T7
import tete_v8 as T8
import palette_corps as PC
import corps_v4 as V4
import corps_v5 as C5
from corps_v4 import cat, place
from tete_v5 import loft, mesh, cone, both, FONT, FONT_B

K = 0.5                                    # masse « Athlétique »
TETE = "Prédateur"
HS = V4.HS * 1.45                          # tête x1,45
N0 = np.array(V4.NECK[0], float)
NECK = [tuple(N0 + (np.array(p) - N0) * 0.8) for p in V4.NECK]          # cou -20 %
HB = N0 + (V4.HB - N0) * 0.8
HEAD_R = V4.HEAD_R
TAIL = [(x, y + 0.05 * max(z - 5, 0), 5 + (z - 5) * 0.8 if z > 5 else z) for x, y, z in V4.TAIL]    # queue -20 %
TAIL_RAD = [r * f for r, f in zip(V4.TAIL_RAD, (1.2, 1.3, 1.35, 1.4, 1.4, 1.35, 1.3))]          # et plus épaisse
# tronc à pans nets (10 points au lieu de 14 arrondis) : dos plat, flanc droit, carène
SHAPE_TRONC = [(0, 1.0), (0.62, 0.9), (1.0, 0.35), (0.97, -0.28), (0.6, -0.82), (0, -1.0),
               (-0.6, -0.82), (-0.97, -0.28), (-1.0, 0.35), (-0.62, 0.9)]

# couleurs : la tête garde la palette Feu, le corps descend d'un cran
PAL = dict(PC.palette("Feu"))
PAL.update(head=PAL["skin"], headback=PAL["back"], headlimb=PAL["limb"],
           skin="#A8231A", back="#5E120C", limb="#86190F", crest="#D8601A", membrane="#6A1A10", membrane2="#9A3418", belly="#FFD27A", belly2="#F0A848",
           bone="#B8301E", eye="#FFE14A", glow="#FFE14A",
           mouth=T8.PAL["mouth"], tongue=T8.PAL["tongue"], throat=T8.PAL["throat"], cheek="#C42A1E")
EMISSIF = ("eye", "glow", "throat")


@contextmanager
def squelette():
    """Les fonctions v4/v5 lisent le squelette dans corps_v4 : on y met celui de la v6 le temps de construire."""
    old = {n: getattr(V4, n) for n in ("NECK", "HB", "HS", "TAIL", "TAIL_RAD", "SHAPE_TRONC")}
    old_muscle = C5.muscle
    V4.NECK, V4.HB, V4.HS, V4.TAIL, V4.TAIL_RAD, V4.SHAPE_TRONC = NECK, HB, HS, TAIL, TAIL_RAD, SHAPE_TRONC
    C5.muscle = muscle
    try:
        yield
    finally:
        for n, v in old.items():
            setattr(V4, n, v)
        C5.muscle = old_muscle


# ---------- formes taillées ----------
def muscle(c, d, r):
    """Muscle taillé : prisme hexagonal à trois anneaux tournés d'un demi-pas (facettes en losange), bouts pointus."""
    u = np.asarray(d, float); u /= np.linalg.norm(u)
    v = np.cross(u, [1.0, 0, 0])
    if np.linalg.norm(v) < 1e-6:
        v = np.array([0, 1.0, 0])
    v /= np.linalg.norm(v)
    w = np.cross(u, v)
    c = np.asarray(c, float)
    rings = []
    for t, s, rot in ((-0.7, 0.55, 0.0), (-0.3, 0.95, 0.5), (0.3, 0.95, 0.0), (0.7, 0.55, 0.5)):
        ang = (np.arange(6) + rot) * np.pi / 3
        rings.append([c + u * t * r[0] + s * (np.cos(a) * r[1] * v + np.sin(a) * r[2] * w) for a in ang])
    return loft(rings, c - u * r[0] * 0.88, c + u * r[0] * 0.88)


def ridge(a, b, out, h, w):
    """Os saillant : arête triangulaire de a à b qui sort de la peau selon out."""
    a, b, out = (np.asarray(p, float) for p in (a, b, out))
    t = b - a; t /= np.linalg.norm(t)
    out = out - t * (out @ t); out /= np.linalg.norm(out)
    side = np.cross(t, out)
    rings = []
    for p, k in ((a, 0.6), ((a + b) / 2, 1.0), (b, 0.55)):
        rings.append([p + out * h * k, p + side * w * k - out * 0.15, p - side * w * k - out * 0.15])
    return loft(rings, a - t * 0.25 * w, b + t * 0.3 * w)


def knob(p, out, r):
    """Bosse d'os à une articulation (pyramide à 5 pans)."""
    p, out = np.asarray(p, float), np.asarray(out, float) / np.linalg.norm(out)
    return cone(p - out * r * 0.4, p + out * r * 1.1, r, 5)


def snap(skin, pts, lift=0.0):
    """Ramène des points sur la peau (puis les écarte un peu selon la normale)."""
    pts = np.asarray(pts, float)
    _, tri = cKDTree(skin.triangles_center).query(pts)                 # face la plus proche (sans rtree)
    c, n = skin.triangles_center[tri], skin.face_normals[tri]
    q = pts - n * ((pts - c) * n).sum(1)[:, None]                      # projeté sur le plan de cette face
    return q + n * lift


def fuse(parts):
    """Union booléenne des volumes d'un morceau (repli : simple concaténation si un volume n'est pas fermé)."""
    parts = [p for p in parts if p is not None]
    if len(parts) == 1:
        return parts[0]
    try:
        u = trimesh.boolean.union(parts, engine="manifold")
        if len(u.faces):
            return u
    except Exception as e:                        # noqa: BLE001 — on garde le rendu même si un volume est ouvert
        print("union impossible, concaténation :", e)
    return cat(parts)


# ---------- pièces (v5 + os + fusion) ----------
def torso(lin):
    L = C5.torso(lin, K)
    skin = L["skin"]
    parts = skin.split(only_watertight=False) if hasattr(skin, "split") else [skin]
    skin = fuse(list(parts))
    bones = []
    for s in (1, -1):
        # omoplate : longue arête sur la masse des ailes ; bassin : arête au-dessus de la hanche
        a, b = snap(skin, [(s * 1.3, 9.6, -4.4), (s * 1.9, 9.2, -1.6)], 0.05)
        bones.append(ridge(a, b, (s, 0.8, 0), 0.45, 0.26))
        a, b = snap(skin, [(s * 1.5, 8.6, 2.0), (s * 1.9, 8.2, 4.2)], 0.05)
        bones.append(ridge(a, b, (s, 0.7, 0.1), 0.35, 0.22))
        # côtes : trois arêtes obliques sur le flanc
        for z in (-1.4, -0.3, 0.8):
            a, b = snap(skin, [(s * 3.0, 7.7, z - 0.2), (s * 3.0, 5.6, z + 0.55)], 0.02)
            bones.append(ridge(a, b, (s, -0.1, 0), 0.24, 0.22))
    a, b = snap(skin, [(0, 3.5, -5.0), (0, 3.8, -2.2)], 0.0)           # bréchet sous le poitrail
    bones.append(ridge(a, b, (0, -1, -0.3), 0.4, 0.2))
    L["skin"] = skin
    L["bone"] = cat(bones)
    return L


def leg_bones(s, front):
    F, B = C5.legs(s, K)
    if front:
        return [knob(np.add(F["elbow"], (s * 0.35, 0.1, 0.45)), (s * 0.5, 0.2, 1), 0.28),
                knob(np.add(F["wrist"], (s * 0.25, 0.1, 0.35)), (s * 0.4, 0, 1), 0.2)]
    return [knob(np.add(B["knee"], (s * 0.25, 0.1, -0.5)), (s * 0.3, 0.2, -1), 0.3),
            knob(np.add(B["hock"], (s * 0.2, 0.0, 0.35)), (s * 0.3, 0, 1), 0.22)]


def leg(fn, s, front, upper):
    L = fn(s, "Feu", K)
    L["skin"] = fuse(list(L["skin"].split(only_watertight=False)))
    if upper and L.get("back") is not None and not front:              # plaque de cuisse v5 réduite (faisait aileron)
        pl = L["back"]
        c = pl.vertices.mean(0)
        pl.vertices = c + (pl.vertices - c) * 0.6
    if upper:
        F, B = C5.legs(s, K)
        a, b = (F["shoulder"], F["elbow"]) if front else (B["hip"], B["knee"])
        a, b = np.add(a, (s * 0.6, -0.4, 0)), np.add(b, (s * 0.15, 0.6, 0))
        p, q = snap(L["skin"], [a, b], 0.03)
        L["bone"] = ridge(p, q, (s, 0.2, 0.2 if front else -0.2), 0.22, 0.14)        # arête d'humérus / de fémur
    else:
        L["bone"] = cat(leg_bones(s, front))
    return L


def head_model(open_deg=0.0, web=False):
    """Tête Prédateur v8 posée au bout du cou v6 ; mâchoire articulée sous l'oreille."""
    a = T8.ARCHETYPES[TETE]
    hp, hsl = T8.head_parts(TETE, a)
    if open_deg > 0 or web:                      # web : commissures au repos (rig), qui s'étirent avec la mâchoire
        for k, v in T8.mouth_web(a, open_deg, throat=True).items():
            hp.setdefault(k if k != "skin" else "cheek", []).extend(v)
    jp, jsl = T8.jaw_parts(TETE, a, open_deg)
    remap = {"skin": "head", "back": "headback"}
    out = {}
    for part, layers, sl in (("Head", hp, hsl), ("Jaw", jp, jsl)):
        lay = {}
        for k, v in layers.items():
            w = trimesh.util.concatenate(v).copy()
            w.vertices = HB + HS * (w.vertices @ HEAD_R.T)
            lay[k] = T7.finish(w, False)
        slots = {"skin": [remap.get(x, x) for x in sl["skin"]]}
        for k, name in (("back", "headback"), ("limb", "headlimb"), ("lid", "head")):
            if k in lay:
                slots[k] = [name] * len(lay[k].faces)
        out[part] = {"layers": lay, "slots": slots}
    out["Head"].update(parent="Neck", pivot=tuple(HB))
    out["Jaw"].update(parent="Head", pivot=tuple(HB + HS * (HEAD_R @ T8.PIVOT_M)))
    return out


def body_slots(m, kind):
    """Contre-ombrage : dos sombre (ny > 0,4), flancs moyens, ventre clair en plaques alternées (ny < -0,3)."""
    c, n = m.triangles_center, m.face_normals
    out = []
    for (x, y, z), (nx, ny, nz) in zip(c, n):
        if kind == "leg":
            out.append("limb" if (y < 3.0 or ny < -0.3) else ("back" if ny > 0.55 else "skin"))
            continue
        band = int(np.floor((z - 0.4 * y) / 0.75)) % 2
        if ny < -0.3:
            out.append("belly2" if band else "belly")
        elif ny > 0.4:
            out.append("marking" if (kind != "neck" and abs(x) < 0.6 and ((z / 1.3) % 1) < 0.2) else "back")
        else:
            out.append("skin")
    return out


def build(open_deg=0.0, web=False):
    out = {}

    def add(name, parent, pivot, L, kind=None):
        L = {n: v for n, v in L.items() if v is not None}
        layers = {n: place(v, False, n.startswith("membrane")) for n, v in L.items()}
        slots = {}
        if kind and "skin" in layers:
            slots["skin"] = body_slots(L["skin"], kind)
        if "spike" in layers:
            slots["spike"] = ["crest"] * len(layers["spike"].faces)                 # crête du corps plus sombre
        for n in ("membrane2", "wingbone", "tailblade", "belly", "limb", "marking", "bone"):
            if n in layers:
                slots[n] = [n] * len(layers[n].faces)
        out[name] = {"parent": parent, "pivot": tuple(float(v) for v in pivot), "layers": layers, "slots": slots}

    with squelette():
        add("Torso", None, (0, 7.0, 0), torso("Feu"), "body")
        nk = C5.neck("Feu", K)
        add("Neck", "Torso", NECK[0], nk, "neck")
        out.update(head_model(open_deg, web))
        for i in range(4):
            add(f"Tail{i + 1}", "Torso" if i == 0 else f"Tail{i}", TAIL[V4.TAIL_CUT[i]], C5.tail(i, "Feu", K), "body")
        for s, n in ((1, "R"), (-1, "L")):
            F, B = C5.legs(s, K)
            W = C5.wing(s, K)
            add("FrontUpperLeg" + n, "Torso", F["shoulder"], leg(C5.front_upper, s, True, True), "leg")
            add("FrontLowerLeg" + n, "FrontUpperLeg" + n, F["elbow"], leg(C5.front_lower, s, True, False), "leg")
            add("BackUpperLeg" + n, "Torso", B["hip"], leg(C5.back_upper, s, False, True), "leg")
            add("BackLowerLeg" + n, "BackUpperLeg" + n, B["knee"], leg(C5.back_lower, s, False, False), "leg")
            up, lo = C5.wing_parts(s, "Feu", K)
            add("WingUpper" + n, "Torso", W["root"], up)
            add("WingLower" + n, "WingUpper" + n, W["elbow"], lo)
    return out


def gather(model, pal, black=False):
    """Comme palette_corps.gather, avec la lueur de gorge parmi les couches lumineuses."""
    if black:
        pal = {k: "#000000" for k in pal}
    T = rendu.pose_transforms(model, {})
    out = []
    for name, seg in model.items():
        R, t = T[name]
        for layer, m in seg["layers"].items():
            slots = seg.get("slots", {}).get(layer)
            col = (np.array([rendu.hex_rgb(pal[s]) for s in slots]) if slots is not None
                   else rendu.hex_rgb(pal.get(layer) or pal["eye"]))
            out.append((m.vertices @ R.T + t, m.vertex_normals @ R.T, np.asarray(m.faces), col,
                        (layer in EMISSIF) and not black))
    return out


def tris(model):
    return sum(len(m.faces) for seg in model.values() for m in seg["layers"].values())


# ---------- planche ----------
def main():
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    VUES = V4.VUES
    cw, ch, lw = 470, 380, 190
    W, H = lw + cw * len(VUES) + 10, 104 + ch * 4 + 30
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    dr.text((24, 18), "Dragon — corps v6 : tête Prédateur, proportions corrigées, corps taillé (Feu)", font=f(30, True),
            fill=(230, 232, 240))
    dr.text((24, 60), "Tête x1,45, cou -20 %, queue -20 % et plus épaisse ; corps et ailes plus sombres que la tête ; muscles à facettes, "
                      "os saillants, contre-ombrage ; peau et muscles fusionnés.", font=f(17), fill=(150, 160, 184))
    v5 = C5.build("Feu", K)
    v6 = build()
    rows = [("v5", "Athlétique", v5, PC.gather(v5, PC.palette("Feu"))), ("v6", "", v6, gather(v6, PAL))]
    for i, (nom, sous, m, it) in enumerate(rows):
        y0 = 96 + i * ch
        dr.text((20, y0 + 20), nom, font=f(26, True), fill=(230, 232, 240))
        dr.text((20, y0 + 56), sous or "Prédateur", font=f(15), fill=(255, 210, 122))
        dr.text((20, y0 + 80), f"{tris(m)} triangles", font=f(14), fill=(140, 150, 172))
        for j, (t, eye, tg, fov) in enumerate(VUES):
            board.paste(rendu.render(it, eye, tg, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        print(nom, tris(m), flush=True)
    # gros plans v6 : tête 3/4, rugissement, profil serré, dessous (contre-ombrage)
    y0 = 96 + 2 * ch
    dr.text((20, y0 + 20), "v6", font=f(26, True), fill=(230, 232, 240))
    dr.text((20, y0 + 56), "gros plans", font=f(15), fill=(255, 210, 122))
    hc = HB + HEAD_R @ np.array([0, 0.8, -1.4]) * HS
    it_open = gather(build(32), PAL)
    it6 = rows[1][3]
    C = V4.C
    plans = [("Tête 3/4", it6, hc + [-9, 3.5, -10], hc, 36), ("Rugissement", it_open, hc + [-10, 1.0, -9], hc - [0, 0.8, 0], 38),
             ("Profil serré", it6, C + [-38, 2.0, -2.0], C + [0, 1.0, -2.0], 34),
             ("3/4 bas (contre-ombrage)", it6, C + [-22, -6, -16], C + [0, 1.5, 0], 40)]
    for j, (t, it, eye, tg, fov) in enumerate(plans):
        board.paste(rendu.render(it, eye, tg, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
        dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
    # silhouettes de profil v5 / v6 à la même échelle
    y0 = 96 + 3 * ch
    dr.text((20, y0 + 20), "Silhouettes", font=f(22, True), fill=(230, 232, 240))
    dr.text((20, y0 + 52), "profil, même échelle", font=f(14), fill=(140, 150, 172))
    eye, tg = C + [-56, 1.5, 2.5], C + [0, 0, 2.5]
    for j, (nom, _, m, _) in enumerate(rows):
        it = gather(m, PAL, True) if nom == "v6" else PC.gather(m, {k: "#000000" for k in PC.palette("Feu")})
        board.paste(V4.silhouette(it, eye, tg, (cw * 2 - 8, ch - 8), 34), (lw + j * cw * 2, y0))
        dr.text((lw + j * cw * 2 + 12, y0 + 8), nom, font=f(16, True), fill=(200, 60, 40))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-dragon-v6.png"))


if __name__ == "__main__":
    main()
