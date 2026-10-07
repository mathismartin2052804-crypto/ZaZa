# Planche de concept v3, rendue depuis la maquette 3D (dragon_v3.py) : 3/4 héros, profil, face,
# gros plan de la tête, les 4 lignées et le test de silhouette. Sortie : ../concept-dragon-v3.png
# Usage : python3 concept_v3.py [dossier_cache]  (les modèles déjà construits y sont relus en .pkl)
import os
import sys
import pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LIGNEES = ["Feu", "Glace", "Foret", "Ombre"]
NOMS = {"Feu": "Feu", "Glace": "Glace", "Foret": "Forêt", "Ombre": "Ombre"}
TRAITS = {"Feu": "crête en flammes, cornes d'arcade", "Glace": "crête en cristaux",
          "Foret": "bois de cerf, collerette de feuilles", "Ombre": "cornes droites, ailes déchirées"}
CENTER = np.array([0, 6.0, 1.5])


def model(lin, cache):
    p = os.path.join(cache, f"model_{lin}.pkl") if cache else None
    if p and os.path.exists(p):
        return pickle.load(open(p, "rb"))
    m = V.build(lin)
    if p:
        pickle.dump(m, open(p, "wb"))
    return m


def items(m, lin, black=False):
    pal = dict(V.VARIANTS[lin])
    pal["glow"] = pal["eye"]
    if black:
        pal = {k: "#000000" for k in pal}
    return rendu.gather(m, pal)


def view(it, eye, target=CENTER, size=(600, 420), fov=32, bg=("#1d2230", "#0c0e14")):
    return rendu.render(it, eye, target, size=size, fov=fov, bg=bg)


def silhouette(m, lin, size):
    im = view(items(m, lin, black=True), (-22, 10, -20), size=size, bg=("#e8e4da", "#e8e4da"))
    a = np.asarray(im.convert("L"))
    return Image.fromarray(np.where(a < 200, 24, 232).astype(np.uint8)).convert("RGB")


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else None
    W, H = 1900, 1500
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)

    def label(xy, txt, s=18, col=(200, 206, 222), b=False):
        dr.text(xy, txt, font=f(s, b), fill=col)

    M = {l: model(l, cache) for l in LIGNEES}
    feu = items(M["Feu"], "Feu")

    label((40, 26), "Dragon low-poly — concept v3", 34, (230, 232, 240), True)
    label((40, 72), f"Maquette 3D ({V.tri_count(M['Feu'])} triangles) : pose d'attaque, tête A affinée, "
                    "ailes asymétriques, queue lame, 3 points Neon (œil, gemme, lame).", 18, (150, 160, 184))

    # héros 3/4
    board.paste(view(feu, (-21, 9.5, -19), size=(1150, 760), fov=30), (20, 110))
    label((40, 120), "3/4 avant", 18, (255, 210, 122), True)
    # profil, face, tête
    board.paste(view(feu, (-36, 6.5, 2), (0, 6, 2), size=(700, 380), fov=34), (1180, 110))
    label((1196, 120), "Profil", 18, (255, 210, 122), True)
    board.paste(view(feu, (0, 6.8, -32), (0, 6.2, 0), size=(350, 380), fov=34), (1180, 500))
    label((1196, 510), "Face", 18, (255, 210, 122), True)
    hb = V.HB + V.HEAD_R @ np.array([0, 0.2, -1.6]) * V.HS
    board.paste(view(feu, hb + np.array([-5.5, 1.6, -5.0]), hb, size=(350, 380), fov=34), (1530, 500))
    label((1546, 510), "Tête", 18, (255, 210, 122), True)

    notes = ["Ligne d'action : épaules plus hautes que les hanches, tête baissée vers l'avant, une patte avant en avant",
             "Tête : bosse nasale, rictus qui remonte vers la joue, gros crocs, œil en amande sous l'arcade, cornes claires",
             "Ailes : aile proche levée, aile éloignée repliée, doigts de longueurs inégales, bord d'attaque courbe",
             "Valeurs : dos plus sombre, pattes un cran plus sombres, ventre en plaques, griffes et cornes claires"]
    for i, t in enumerate(notes):
        label((40, 885 + i * 26), "•  " + t, 16)

    # lignées : couleur puis silhouette
    label((40, 1000), "Les 4 lignées (en haut) et test de silhouette à petite taille (en bas)", 22, (230, 232, 240), True)
    cw = 465
    for i, l in enumerate(LIGNEES):
        x = 20 + i * cw
        board.paste(view(items(M[l], l), (-22, 10, -20), size=(cw - 10, 300), fov=34), (x, 1040))
        label((x + 16, 1048), f"{NOMS[l]} — {TRAITS[l]}", 16, (220, 224, 236))
        board.paste(silhouette(M[l], l, (150, 100)), (x + (cw - 160) // 2, 1360))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-dragon-v3.png"))


if __name__ == "__main__":
    main()
