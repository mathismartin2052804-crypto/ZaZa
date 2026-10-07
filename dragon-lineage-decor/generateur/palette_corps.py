# Palette de corps v7 : prolonge les couleurs de la tête v7 sur tout le dragon.
# Règles :
#   - 60 / 30 / 10 : peau + dos (60 %), bande ventrale + membranes (30 %), accents lumineux (10 %)
#   - la tête donne les teintes : la bande ventrale reprend les plaques de mâchoire (belly / belly2 alternées),
#     la crête dorsale reprend les collerettes (spike / tip), les griffes reprennent les cornes,
#     le motif lumineux du dos et le tranchant de la queue reprennent la couleur des yeux / runes
#   - une seule couleur lumineuse par lignée (yeux, narines, runes, motif dorsal, tranchant) pour qu'on
#     reconnaisse la lignée de loin
# Essai sur la maquette v3 (corps SDF) avec la tête v7 greffée, en attendant le corps polygonal v4.
# Usage : python3 palette_corps.py [dossier_cache]  ->  ../palette-corps-v7.png
#   (le dossier de cache contient model_<lignée>.pkl construits par dragon_v3.build, sinon ils sont reconstruits)
import os
import sys
import pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
import tete_v7 as T7

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LIGNEES = ["Feu", "Glace", "Foret", "Ombre"]
NOMS = {"Feu": "Feu", "Glace": "Glace", "Foret": "Forêt", "Ombre": "Ombre"}

# Couleurs ajoutées pour le corps (le reste vient de dragon_v3.VARIANTS, déjà utilisé par la tête)
CORPS = {
    "Feu":   {"belly2": "#D9862C", "crest": "#FF7A1A", "membrane": "#B8361A", "membrane2": "#FF8A2A",
              "wingbone": "#8E1C14", "tailblade": "#3A1612", "marking": "#FF9A1A"},
    "Glace": {"belly2": "#A6CBE6", "crest": "#BDF2FF", "membrane": "#4F88BC", "membrane2": "#A8DCF4",
              "wingbone": "#2A5890", "tailblade": "#E2FAFF", "marking": "#7FF4FF"},
    "Foret": {"belly2": "#A88F4C", "crest": "#A6D83A", "membrane": "#4E8A28", "membrane2": "#9CC84A",
              "wingbone": "#5E4126", "tailblade": "#7A5530", "marking": "#D8FF3A"},
    "Ombre": {"belly2": "#523E74", "crest": "#8E3AD0", "membrane": "#2E1E44", "membrane2": "#5A2E86",
              "wingbone": "#1C1428", "tailblade": "#140E1E", "marking": "#E840FF"},
}
# Retouches proposées sur la palette de tête (lisibilité)
RETOUCHES = {"Ombre": {"skin": "#45355F"}}     # peau un cran plus claire : la silhouette se perdait dans le fond

ROLES = [("skin", "peau"), ("back", "dos"), ("limb", "pattes"), ("belly", "ventre"), ("belly2", "ventre alt."),
         ("crest", "crête"), ("tip", "pointe"), ("membrane", "membrane"), ("membrane2", "bord d'aile"),
         ("wingbone", "os d'aile"), ("horn", "cornes"), ("claw", "griffes"), ("tailblade", "lame queue"),
         ("marking", "motif lum."), ("eye", "yeux")]


def palette(lin):
    p = dict(V.VARIANTS[lin])
    p.update(RETOUCHES.get(lin, {}))
    p.update(CORPS[lin])
    p["glow"] = p["eye"]
    return p


def body(lin, cache):
    path = os.path.join(cache, f"model_{lin}.pkl") if cache else None
    if path and os.path.exists(path):
        return pickle.load(open(path, "rb"))
    m = V.build(lin)
    if path:
        pickle.dump(m, open(path, "wb"))
    return m


def recolor(m, lin):
    """Corps v3 + tête v7, avec les nouveaux emplacements de couleur répartis par face."""
    m = {k: dict(v, slots=dict(v["slots"])) for k, v in m.items()}
    for k, seg in T7.build(lin).items():           # tête, mâchoire et cou v7
        m[k] = dict(seg, parent=seg["parent"] or "Torso")
    for name, seg in m.items():
        L, S = seg["layers"], seg["slots"]
        body_seg = name == "Torso" or name.startswith("Tail")
        if body_seg and "skin" in L:
            c, nrm = L["skin"].triangles_center, L["skin"].face_normals
            out = []
            for s, (x, y, z), ny in zip(S["skin"], c, nrm[:, 1]):
                if s == "skin" and ny > 0.7:
                    s = "back"                                      # bande dorsale prolongée sur la queue
                if s == "belly" and int(np.floor(z / 0.8)) % 2:
                    s = "belly2"                                    # plaques ventrales alternées, comme la mâchoire
                elif s == "back" and abs(x) < 0.9 and (z / 1.1) % 1 < 0.35:
                    s = "marking"                                   # bandes du motif dorsal
                out.append(s)
            S["skin"] = out
        if (body_seg or name == "Neck" or "Leg" in name) and "spike" in L:
            if name == "Tail4":                                     # lame de queue
                c = L["spike"].triangles_center
                S["spike"] = ["tailblade" if z > 11.2 else "crest" for _, _, z in c]
            elif name != "Neck":
                S["spike"] = ["crest"] * len(L["spike"].faces)
        if name == "Tail4" and "glow" in L:
            S["glow"] = ["marking"] * len(L["glow"].faces)
        if name.startswith("Wing"):
            S["skin"] = ["wingbone"] * len(L["skin"].faces)
            if "membrane" in L:                                     # dégradé : sombre au corps, clair au bord
                c = L["membrane"].triangles_center
                d = np.abs(c[:, 0]) + 0.25 * c[:, 1]
                t = (d - d.min()) / (np.ptp(d) + 1e-9)
                edge = t > 0.45 if name.startswith("WingLower") else np.zeros(len(t), bool)
                S["membrane"] = ["membrane2" if e else "membrane" for e in edge]
    return m


def gather(m, pal):
    """Comme rendu.gather, mais les tables de couleurs par face valent pour toutes les couches."""
    T = rendu.pose_transforms(m, {})
    out = []
    for name, seg in m.items():
        R, t = T[name]
        for layer, mesh in seg["layers"].items():
            slots = seg.get("slots", {}).get(layer)
            col = (np.array([rendu.hex_rgb(pal[s]) for s in slots]) if slots is not None
                   else rendu.hex_rgb(pal["eye" if layer == "glow" else layer]))
            out.append((mesh.vertices @ R.T + t, mesh.vertex_normals @ R.T, np.asarray(mesh.faces), col,
                        layer in ("eye", "glow")))
    return out


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else None
    cw, ch, lw, sw = 520, 400, 170, 570
    vues = [("3/4", (-21, 9.5, -19), (0, 6.0, 1.5), 31), ("Profil", (-36, 6.5, 2), (0, 6, 2), 27),
            ("3/4 bas (ventre)", (-20, -3.5, -17), (0, 5.0, 1.5), 33)]
    W, H = lw + cw * len(vues) + sw + 20, 120 + ch * len(LIGNEES) + 20
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — palette de corps d'après la tête v7", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Corps v3 (SDF, provisoire) + tête v7 ; ventre en plaques alternées comme la mâchoire, crête = "
                      "collerettes, aile en dégradé, une seule couleur lumineuse par lignée.",
            font=f(17), fill=(150, 160, 184))
    for i, lin in enumerate(LIGNEES):
        pal = palette(lin)
        it = gather(recolor(body(lin, cache), lin), pal)
        y0 = 100 + i * ch
        dr.text((20, y0 + 20), NOMS[lin], font=f(24, True), fill=(230, 232, 240))
        for j, (t, eye, target, fov) in enumerate(vues):
            board.paste(rendu.render(it, eye, target, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        x0 = lw + len(vues) * cw + 8
        for j, (k, nom) in enumerate(ROLES):
            x, y = x0 + (j % 3) * 188, y0 + 14 + (j // 3) * 76
            dr.rectangle((x, y, x + 52, y + 52), fill=pal[k], outline=(60, 66, 84))
            dr.text((x + 60, y + 6), nom, font=f(15, True), fill=(220, 224, 236))
            dr.text((x + 60, y + 28), pal[k].upper(), font=f(14), fill=(150, 160, 184))
        print(lin, flush=True)
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "palette-corps-v7.png"))


if __name__ == "__main__":
    main()
