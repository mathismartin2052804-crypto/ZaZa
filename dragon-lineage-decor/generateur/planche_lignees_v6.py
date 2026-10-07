# Planche des 4 lignées du dragon v6 (même maillage, palette corps plus sombre que la tête) -> ../lignees-v6.png
# Ligne du haut : corps entier (pose de repos, ailes repliées) ; ligne du bas : gros plan tête et rugissement.
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
from tete_v5 import FONT_B


def main():
    rig = RG.Rig()
    C = V4.C
    hc = RG.hl((0, 0.6, -1.4))
    w, h = 460, 360
    font = ImageFont.truetype(FONT_B, 22)
    im = Image.new("RGB", (w * 4, h * 2 + 40), (16, 19, 28))
    dr = ImageDraw.Draw(im)
    P_repos, off_r = D.repos(0.02)
    P_rug, off_g = D.rugit(0.6)
    for j, lin in enumerate(PC.LIGNEES):
        pal = C6.palette(lin)
        im.paste(rendu.render(rig.items(P_repos, off_r, pal=pal), C + [-28, 9, -26], C + [0, 1.5, -1.5],
                              size=(w - 4, h - 4), fov=44, ss=2), (j * w, 40))
        im.paste(rendu.render(rig.items(P_rug, off_g, pal=pal), hc + [-15, 4, -17], hc + [0.3, 0.6, 0.8],
                              size=(w - 4, h - 4), fov=36, ss=2), (j * w, 40 + h))
        dr.text((j * w + 16, 8), PC.NOMS[lin], font=font, fill=tuple(int(255 * x) for x in rendu.hex_rgb(pal["eye"])))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lignees-v6.png")
    im.save(out)
    print(out)


if __name__ == "__main__":
    main()
