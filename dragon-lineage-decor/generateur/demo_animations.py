# Démo d'animations du corps v5 (masse athlétique) : course, vol, rugissement, en tournant les 20 morceaux
# autour de leurs pivots (les mêmes articulations que les Motor6D de RigDragon.lua).
# Conventions de rendu.rot : +ex lève l'avant d'un morceau / balance vers l'avant ce qui pend sous le pivot ;
# +ez lève l'aile droite (x > 0), -ez lève l'aile gauche.
# Usage : python3 demo_animations.py [lignée] [masse]  ->  ../demo-animations-v5.gif
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rendu
import palette_corps as PC
import corps_v4 as V4
import corps_v5 as C5
from tete_v5 import FONT_B

N = 36                                    # images par boucle (≈ 2 s)
C = V4.C


def sides(name, v, mirror_z=True):
    """Même rotation pour R et L ; la rotation autour de z (et y) est inversée côté gauche."""
    ex, ey, ez = v
    return {name + "R": (ex, ey, ez), name + "L": (ex, -ey, -ez) if mirror_z else (ex, ey, ez)}


def course(t):
    p = 2 * np.pi * 3 * t                 # 3 foulées par boucle
    P = {"Torso": (3 * np.sin(2 * p), 0, 0),
         "Neck": (-8 + 6 * np.sin(2 * p + 0.8), 0, 0), "Head": (4 - 5 * np.sin(2 * p + 1.4), 0, 0),
         "Jaw": (-6 - 4 * max(0, np.sin(2 * p)), 0, 0)}
    for n, ph in (("R", 0.0), ("L", 0.55)):           # galop : pattes avant puis arrière, côtés décalés
        f, b = p + ph, p + ph + np.pi
        P["FrontUpperLeg" + n] = (38 * np.sin(f), 0, 0)
        P["FrontLowerLeg" + n] = (-45 * (0.5 + 0.5 * np.cos(f)), 0, 0)
        P["BackUpperLeg" + n] = (34 * np.sin(b), 0, 0)
        P["BackLowerLeg" + n] = (30 * (0.5 + 0.5 * np.cos(b)), 0, 0)
    P.update(sides("WingUpper", (5 * np.sin(2 * p), -38, -22 + 4 * np.sin(2 * p))))
    P.update(sides("WingLower", (0, -68, 0)))
    for i in range(4):
        P[f"Tail{i + 1}"] = (2 + 3 * np.sin(2 * p - i), 9 * np.sin(p - 0.7 * i), 0)
    return P, np.array([0, 0.45 * abs(np.sin(2 * p)) - 0.2, 0])


def vol(t):
    p = 2 * np.pi * 2 * t                 # 2 battements par boucle
    P = {"Torso": (-4 + 3 * np.sin(p + 0.6), 0, 0), "Neck": (-14 + 4 * np.sin(p + 1.2), 0, 0),
         "Head": (10 - 4 * np.sin(p + 1.6), 0, 0), "Jaw": (-4, 0, 0)}
    P.update(sides("WingUpper", (0, 4 * np.cos(p), 38 * np.sin(p) + 8)))
    P.update(sides("WingLower", (0, 6 * np.cos(p), 28 * np.sin(p - 0.7) - 4)))
    P.update(sides("FrontUpperLeg", (-55, 0, 0)))
    P.update(sides("FrontLowerLeg", (70, 0, 0)))
    P.update(sides("BackUpperLeg", (-50, 0, 0)))
    P.update(sides("BackLowerLeg", (-35, 0, 0)))
    for i in range(4):
        P[f"Tail{i + 1}"] = (4 * np.sin(p - 0.8 * i) + (3 if i == 0 else 0), 6 * np.sin(0.5 * p - 0.6 * i), 0)
    return P, np.array([0, 4.5 - 0.7 * np.sin(p), 0])


def ease(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def rugit(t):
    a = ease(0.0, 0.22, t) * (1 - ease(0.3, 0.42, t))        # prise d'élan : se cabre
    r = ease(0.3, 0.42, t) * (1 - ease(0.8, 0.98, t))        # rugissement
    sh = r * np.sin(2 * np.pi * t * 14)                      # tremblement pendant le cri
    P = {"Torso": (7 * a - 3 * r, 0, 0),
         "Neck": (22 * a - 12 * r, 0, 0), "Head": (14 * a + 6 * r + 2 * sh, 2 * sh, 0),
         "Jaw": (-8 * a - 38 * r, 0, 0)}
    P.update(sides("WingUpper", (0, -10 * r, 25 * a + 50 * r)))
    P.update(sides("WingLower", (0, 8 * r, 10 * a + 30 * r)))
    P.update(sides("FrontUpperLeg", (-10 * a + 14 * r, 0, 0)))
    P.update(sides("FrontLowerLeg", (8 * a - 10 * r, 0, 0)))
    P.update(sides("BackUpperLeg", (-8 * r, 0, 0)))
    for i in range(4):
        P[f"Tail{i + 1}"] = (6 * a + 4 * r, 14 * r * np.sin(2 * np.pi * t * 3 - 0.8 * i), 0)
    return P, np.array([0, 0.5 * a - 0.15 * r, 0])


def items(model, pal, pose, off):
    T = rendu.pose_transforms(model, pose)
    out = []
    for name, seg in model.items():
        R, t = T[name]
        for layer, mesh in seg["layers"].items():
            sl = seg.get("slots", {}).get(layer)
            col = (np.array([rendu.hex_rgb(pal[s]) for s in sl]) if sl is not None
                   else rendu.hex_rgb(pal["eye" if layer == "glow" else layer]))
            out.append((mesh.vertices @ R.T + t + off, mesh.vertex_normals @ R.T, np.asarray(mesh.faces), col,
                        layer in ("eye", "glow")))
    return out


ANIMS = [("Course", course, C + [-30, 7, -30], C + [0, 0.5, -1.5], 42),
         ("Vol", vol, C + [-34, 2, -26], C + [0, 4.0, -1.0], 50),
         ("Rugissement", rugit, C + [-26, 4, -32], C + [0, 2.0, -2.5], 44)]


def main():
    lin = sys.argv[1] if len(sys.argv) > 1 else "Feu"
    k = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    model, pal = C5.build(lin, k), PC.palette(lin)
    cw, ch = 520, 420
    font = ImageFont.truetype(FONT_B, 20)
    frames = []
    for i in range(N):
        t = i / N
        im = Image.new("RGB", (cw * len(ANIMS), ch), (16, 19, 28))
        dr = ImageDraw.Draw(im)
        for j, (nom, fn, eye, tg, fov) in enumerate(ANIMS):
            pose, off = fn(t)
            im.paste(rendu.render(items(model, pal, pose, off), eye, tg, size=(cw - 6, ch - 6), fov=fov, ss=1), (j * cw, 0))
            dr.text((j * cw + 14, 10), nom, font=font, fill=(255, 210, 122))
        frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=128))
        print(i, flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo-animations-v5.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=55, loop=0, optimize=True)


if __name__ == "__main__":
    main()
