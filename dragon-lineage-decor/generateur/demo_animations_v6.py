# Démo d'animations du dragon v6 sur le rig à os (rig_v6.py) : un seul maillage déformé, articulations sans trous.
#   Course : galop lourd refait (course_v6.py) : pieds posés au sol par IK (à plat pendant l'appui, roulent sur
#            les griffes au décollage), corps qui ne rebondit plus, tête stabilisée, cou et queue en retard
#   Vol    : battements avec le bout d'aile en retard ; pattes avant repliées sous le poitrail, pattes arrière
#            qui traînent vers l'arrière (moins relevées qu'en v5)
#   Rugissement : se cabre, ouvre la gueule (commissures étirées, lueur de gorge), plisse les yeux, ailes
#            déployées d'un seul tenant (la membrane se plie au coude au lieu de se couper)
#   Repos  : respiration ; les yeux sautent d'un point à l'autre (saccades, aussi en hauteur), la tête suit plus
#            lentement pendant que l'œil revient au centre ; micro-mouvements, double clignement, paupières lourdes
# Conventions de rendu.rot : +ex lève l'avant / balance vers l'avant ce qui pend sous l'os ; +ez lève l'aile droite.
# Usage : python3 demo_animations_v6.py  ->  ../demo-animations-v6.gif
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rendu
import rig_v6 as RG
import course_v6 as CO
import corps_v4 as V4
from tete_v5 import FONT_B

N = 40                                    # images par boucle (≈ 2,2 s)
C = V4.C
REPLI = {"WingUpper": (0, -38, -22), "WingLower": (0, -68, 0)}     # ailes repliées le long du corps


def sides(name, v):
    """Même rotation à droite et à gauche (miroir : ey et ez inversés à gauche)."""
    ex, ey, ez = v
    return {name + "R": (ex, ey, ez), name + "L": (ex, -ey, -ez)}


def ease(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def eyes(close=0.0, look=0.0, up=0.0):
    """Paupières (0 ouvertes, 1 fermées) et regard (degrés, + = vers la droite du dragon / vers le haut)."""
    close = float(np.clip(close, 0, 1))
    P = {"EyelidR": RG.lid_pose(close, "R"), "EyelidL": RG.lid_pose(close, "L")}
    P["PupilR"], P["PupilL"] = RG.pupil_pose(look, up, "R"), RG.pupil_pose(look, up, "L")
    return P


def blink(t, at, d=0.06):
    return float(np.clip(1 - abs(t - at) / d, 0, 1)) ** 0.7


def folded(P):
    for k, v in REPLI.items():
        P.update(sides(k, v))
    return P


def course(t):
    P, off = CO.pose(t)
    P.update(eyes(0.15, 0))
    return P, off


def vol(t):
    p = 2 * np.pi * 2 * t                                      # 2 battements par boucle
    P = {"Root": (-4 + 3 * np.sin(p + 0.6), 0, 0), "Spine": (2 * np.sin(p + 1.0), 0, 0),
         "Chest": (2 * np.sin(p + 1.4), 0, 0),
         "Neck1": (-8 + 3 * np.sin(p + 1.4), 0, 0), "Neck2": (-4 + 2 * np.sin(p + 1.8), 0, 0),
         "Head": (8 - 3 * np.sin(p + 2.2), 0, 0), "Jaw": (-4, 0, 0)}
    P.update(sides("WingUpper", (0, 4 * np.cos(p), 38 * np.sin(p) + 8)))
    P.update(sides("WingLower", (0, 6 * np.cos(p), 30 * np.sin(p - 0.7) - 4)))
    for j in range(4):                                         # doigts : le bout de l'aile fouette
        P.update(sides(f"WingFinger{j + 1}", (0, 3 * j * np.cos(p - 1.2), 10 * np.sin(p - 1.3 - 0.2 * j))))
    # pattes : avant repliées sous le poitrail, arrière qui traînent (moins relevées qu'en v5)
    P.update(sides("FrontUpperLeg", (-22, 0, 0)))
    P.update(sides("FrontLowerLeg", (48, 0, 0)))
    P.update(sides("FrontFoot", (-35, 0, 0)))
    P.update(sides("BackUpperLeg", (-28 + 3 * np.sin(p), 0, 0)))
    P.update(sides("BackLowerLeg", (-12, 0, 0)))
    P.update(sides("BackFoot", (-35, 0, 0)))
    for i in range(6):
        P[f"Tail{i + 1}"] = (3 * np.sin(p - 0.8 * i) + (3 if i == 0 else 0), 5 * np.sin(0.5 * p - 0.6 * i), 0)
    P.update(eyes(blink(t, 0.62), 8 * np.sin(2 * np.pi * t)))
    return P, np.array([0, 4.5 - 0.7 * np.sin(p), 0])


def rugit(t):
    a = ease(0.0, 0.22, t) * (1 - ease(0.3, 0.42, t))        # prise d'élan : se cabre
    r = ease(0.3, 0.42, t) * (1 - ease(0.82, 0.98, t))       # rugissement
    sh = r * np.sin(2 * np.pi * t * 14)                       # tremblement pendant le cri
    P = {"Root": (6 * a - 3 * r, 0, 0), "Spine": (3 * a, 0, 0), "Chest": (3 * a - 2 * r, 0, 0)}
    for i in range(3):
        P[f"Neck{i + 1}"] = (7 * a - 4 * r, 0, 0)
    P["Head"] = (12 * a + 8 * r + 2 * sh, 2 * sh, 0)
    P["Jaw"] = (-6 * a - 34 * r, 0, 0)
    P.update(sides("WingUpper", (0, -38 * (1 - a - r) - 10 * r, -22 * (1 - a - r) + 25 * a + 45 * r)))
    P.update(sides("WingLower", (0, -68 * (1 - a - r) + 8 * r, 10 * a + 25 * r)))
    for j in range(4):
        P.update(sides(f"WingFinger{j + 1}", (0, (j - 1.5) * 6 * r, 4 * r * np.sin(2 * np.pi * t * 7 + j))))
    P.update(sides("FrontUpperLeg", (-14 * a + 10 * r, 0, 0)))
    P.update(sides("FrontLowerLeg", (10 * a - 8 * r, 0, 0)))
    P.update(sides("FrontFoot", (6 * a, 0, 0)))
    P.update(sides("BackUpperLeg", (-6 * a - 6 * r, 0, 0)))       # garde les pattes arrière au sol
    P.update(sides("BackLowerLeg", (4 * a, 0, 0)))
    P.update(sides("BackFoot", (2 * a + 6 * r, 0, 0)))
    for i in range(6):
        P[f"Tail{i + 1}"] = (4 * a + 3 * r, 12 * r * np.sin(2 * np.pi * t * 3 - 0.8 * i), 0)
    P.update(eyes(0.4 * r + blink(t, 0.12), 0))              # plisse les yeux en rugissant
    return P, np.array([0, 0.45 * a - 0.15 * r, 0])


# regard au repos : (instant, cap, hauteur) en degrés ; l'œil y saute en ~50 ms, la tête suit en ~0,4 s
SACCADES = [(0.06, 18, 4), (0.20, 25, -3), (0.34, -3, 1), (0.45, -22, 5), (0.58, -27, -4), (0.72, -6, 7),
            (0.84, 3, -1)]


def cible(t, k, dur, delai=0.0):
    """Valeur k (1 cap, 2 hauteur) du regard à l'instant t, transitions de durée dur (boucle sans à-coup)."""
    v = SACCADES[-1][k]
    for i, s in enumerate(SACCADES):
        v += (s[k] - SACCADES[i - 1][k]) * ease(s[0] + delai, s[0] + delai + dur, t)
    return v


def regard_repos(t):
    """(cap de la tête, hauteur de la tête, cap de l'œil, hauteur de l'œil, paupières) au repos."""
    tete_cap, tete_haut = 0.65 * cible(t, 1, 0.1, 0.02), 0.5 * cible(t, 2, 0.1, 0.02)
    tau = 2 * np.pi * t
    cap = np.clip(cible(t, 1, 0.012) - tete_cap, -18, 18) + 0.7 * np.sin(19 * tau) + 0.4 * np.sin(31 * tau + 1)
    haut = np.clip(cible(t, 2, 0.012) - tete_haut, -9, 9) + 0.5 * np.sin(23 * tau + 2)
    lourd = 0.35 * ease(0.58, 0.62, t) * (1 - ease(0.70, 0.73, t))          # paupières lourdes un instant
    lid = 0.08 + lourd - 0.02 * haut + max(blink(t, 0.45, 0.03), blink(t, 0.83, 0.03), blink(t, 0.89, 0.03))
    return tete_cap, tete_haut, cap, haut, lid


def repos(t):
    br = np.sin(2 * np.pi * t)                                # une respiration par boucle
    tc, th, cap, haut, lid = regard_repos(t)
    P = folded({"Chest": (1.5 * br, 0, 0), "Spine": (-1 * br, 0, 0),
                "Neck1": (2 * br, 0.3 * tc, 0), "Neck2": (1 * br, 0.3 * tc, 0), "Neck3": (0.4 * th, 0.2 * tc, 0),
                "Head": (-2 * br + 0.6 * th, 0.2 * tc, 0), "Jaw": (-3 - 3 * max(0, br), 0, 0)})
    P.update(sides("WingUpper", (0, -38, -22 + 2 * br)))
    for i in range(6):
        P[f"Tail{i + 1}"] = (1.5 * np.sin(2 * np.pi * t - 0.5 * i), 6 * np.sin(2 * np.pi * t - 0.6 * i), 0)
    P.update(eyes(lid, cap, haut))
    return P, np.array([0, 0.05 * br, 0])


ANIMS = [("Course (galop)", course, C + [-30, 7, -30], C + [0, 0.5, -1.5], 42),
         ("Vol", vol, C + [-34, 2, -26], C + [0, 4.0, -1.0], 50),
         ("Rugissement", rugit, C + [-26, 4, -32], C + [0, 2.0, -2.5], 44),
         ("Repos : regard, saccades et clignements", repos, None, None, 34)]


def main():
    rig = RG.Rig()
    hc = RG.hl((0, 0.6, -1.4))
    cw, ch = 470, 380
    font = ImageFont.truetype(FONT_B, 18)
    frames = []
    for i in range(N):
        t = i / N
        im = Image.new("RGB", (cw * 2, ch * 2), (16, 19, 28))
        dr = ImageDraw.Draw(im)
        for j, (nom, fn, eye, tg, fov) in enumerate(ANIMS):
            pose, off = fn(t)
            if eye is None:                                   # gros plan sur la tête pour le repos
                eye, tg = hc + [-17, 4, -19], hc + [0.3, 0.4, 0.8]
            x0, y0 = (j % 2) * cw, (j // 2) * ch
            im.paste(rendu.render(rig.items(pose, off), eye, tg, size=(cw - 6, ch - 6), fov=fov, ss=1), (x0, y0))
            dr.text((x0 + 14, y0 + 10), nom, font=font, fill=(255, 210, 122))
        frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=160))
        print(i, flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo-animations-v6.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=55, loop=0, optimize=True)


if __name__ == "__main__":
    main()
