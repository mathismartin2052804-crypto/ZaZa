# Planche des 4 lignées du dragon v6 : même squelette, ornements et palette propres à chaque lignée
# (lignees_v6.py) -> ../lignees-v6.png
# Ligne 1 : corps entier au repos ; ligne 2 : gros plan tête (rugissement) ; ligne 3 : en vol plané (style de la lignée) ;
# en bas : titre, souffle, passif, statistiques et affinités.
# Usage : python3 planche_lignees_v6.py
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rendu
import rig_v6 as RG
import corps_v6 as C6
import corps_v4 as V4
import palette_corps as PC
import demo_animations_v6 as D
import lignees_v6 as L6
from tete_v5 import FONT, FONT_B


def main():
    C = V4.C
    hc = RG.hl((0, 0.6, -1.4))
    w, h, ht = 460, 340, 330
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    im = Image.new("RGB", (w * 4, 50 + h * 3 + ht), (16, 19, 28))
    dr = ImageDraw.Draw(im)
    P_repos, off_r = D.repos(0.02)
    P_rug, off_g = D.rugit(0.6)
    for j, lin in enumerate(PC.LIGNEES):
        rig = RG.Rig(lignee=lin)
        pal = C6.palette(lin)
        P_vol, off_v = D.vol(0.88, L6.STYLE[lin]["vol"])                    # en vol plané
        vues = [(P_repos, off_r, C + [-24, 10, -22], C + [0, 2, 0], 42),
                (P_rug, off_g, hc + [-7, 1.5, -17], hc + [0.3, 0.9, 0.8], 42),
                (P_vol, off_v, C + [-18, 24, -24], C + [0, 4.5, 0.5], 56)]
        for k, (P, off, eye, tg, fov) in enumerate(vues):
            im.paste(rendu.render(rig.items(P, off, pal=pal), eye, tg, size=(w - 4, h - 4), fov=fov, ss=2),
                     (j * w, 50 + k * h))
        c = L6.CARAC[lin]
        col = tuple(int(255 * x) for x in rendu.hex_rgb(pal["eye"]))
        dr.text((j * w + 16, 10), f"{c['nom']} — {c['titre']}", font=f(24, True), fill=col)
        y = 50 + 3 * h + 10
        s = c["stats"]
        lignes = [(" ".join(L6.ORNEMENTS[lin].__doc__.split()), (200, 205, 220)),
                  (f"Passif : {c['passif']['nom']}", col),
                  (c["passif"]["texte"], (170, 178, 196)),
                  (f"Vie {s['vie']}  Att {s['attaque']}  Déf {s['defense']}  Vit {s['vitesse']}  Agi {s['agilite']}",
                   (220, 222, 230)),
                  (f"Bat : {PC.NOMS[c['fort_contre']]}   Craint : {PC.NOMS[c['faible_contre']]}", (220, 222, 230))]
        for txt, cl in lignes:
            words, line = txt.split(), ""
            for wd in words:                                   # retour à la ligne
                if dr.textlength(line + " " + wd, font=f(15)) > w - 30:
                    dr.text((j * w + 16, y), line.strip(), font=f(15), fill=cl)
                    y += 20
                    line = ""
                line += " " + wd
            dr.text((j * w + 16, y), line.strip(), font=f(15), fill=cl)
            y += 22
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lignees-v6.png")
    im.save(out)
    print(out)


if __name__ == "__main__":
    main()
