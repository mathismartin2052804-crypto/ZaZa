# Démo d'animations du dragon v6 sur le rig à os (rig_v6.py) : un seul maillage déformé, articulations sans trous.
#   Marche : allures_v6.py (pieds posés au sol par IK, tête stabilisée) ; plus de course : il décolle et vole
#   Décollage, Atterrissage, Souffle de feu : sequences_v6.py
#   Vol v2 : battements asymétriques (aile repliée à la remontée, bout qui fouette), vol plané, corps qui ondule,
#            tête stabilisée, pattes et queue qui suivent avec retard ; style propre à chaque lignée (lignees_v6)
#   Rugissement : se cabre, ouvre la gueule (commissures étirées, lueur de gorge), plisse les yeux, ailes
#            déployées d'un seul tenant (la membrane se plie au coude au lieu de se couper)
#   Repos  : respiration ; les yeux sautent d'un point à l'autre (saccades, aussi en hauteur), la tête suit plus
#            lentement pendant que l'œil revient au centre ; micro-mouvements, double clignement, paupières lourdes
# Conventions de rendu.rot : +ex lève l'avant / balance vers l'avant ce qui pend sous l'os ; +ez lève l'aile droite ;
# +ey tourne vers la GAUCHE du dragon (regard « + = vers la droite » => lacet négatif).
# Usage : python3 demo_animations_v6.py  ->  ../demo-animations-v6.gif, ../demo-animations-v6-nouvelles.gif,
#                                             ../demo-vol-lignees-v6.gif
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rendu
import rig_v6 as RG
import allures_v6 as AL
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


def allure(A, t):
    P, off, lid = A.pose(t)
    P.update(eyes(lid, 0))
    return P, off


def marche(t):
    return allure(AL.MARCHE, t)


def sequence(nom, t):
    import sequences_v6 as SQ                                 # import tardif : sequences_v6 importe ce module
    P, off, lid, lueur, feu = SQ.SEQUENCES[nom].pose(t)
    P.update(eyes(lid, 0))
    return P, off


def decollage(t):
    return sequence("Decollage", t)


def atterrissage(t):
    return sequence("Atterrissage", t)


def souffle_feu(t):
    return sequence("SouffleFeu", t)


# ---------- vol v2 ----------
# Repère : au repos (pose de liaison) l'aile monte déjà de ~42° ; ez = -32 la met presque à l'horizontale.
# Une boucle = 4 battements puis du vol plané (part « plane » du style de la lignée) :
#   - battement asymétrique : descente rapide (42 % du temps), remontée lente ; l'avant-bras et les doigts suivent
#     avec retard (le bout de l'aile fouette) ; à la remontée l'aile se replie et se balaie vers l'arrière, à la
#     descente elle est tendue, bord d'attaque un peu en avant
#   - le corps monte pendant la descente des ailes (en retard) et pique légèrement du nez à la remontée
#   - le dos, le cou et la queue ondulent en vagues décalées (lacet lent + tangage au rythme des ailes), la tête
#     compense (stabilisée comme un oiseau), les pattes ballottent avec retard
#   - vol plané : ailes tendues en dièdre, petites corrections de rafales (roulis), queue qui gouverne, regard qui
#     balaie le sol ; effort (0..1, montée) le remplace par des battements, plane_force (0..1, piqué) l'impose
VOL_BATTEMENTS = 4
VOL_DESCENTE = 0.42


def style_vol(lin="Feu"):
    import lignees_v6 as L6
    return L6.STYLE[lin]["vol"]


def coup(u, d=VOL_DESCENTE):
    """Position de l'aile dans le battement (1 en haut, -1 en bas) et phase « angulaire » x (0..1)."""
    u = u % 1
    x = 0.5 * u / d if u < d else 0.5 + 0.5 * (u - d) / (1 - d)
    return np.cos(2 * np.pi * x), x


def plie(x):
    """Repli de l'aile pendant la remontée (0..1)."""
    return max(0.0, -np.sin(2 * np.pi * x)) ** 2


def appui(x):
    """Aile tendue pendant la descente (0..1)."""
    return max(0.0, np.sin(2 * np.pi * x)) ** 2


def vol_plane(t, st, effort=0.0, plane_force=0.0):
    """Poids du vol plané à l'instant t (0 : bat des ailes, 1 : plane)."""
    a = 1 - st["plane"] - 0.06
    env = ease(a, a + 0.1, t) * (1 - ease(0.9, 0.99, t)) if st["plane"] > 0 else 0.0
    return max((1 - effort) * env, plane_force)


def vol(t, st=None, effort=0.0, plane_force=0.0):
    st = st or style_vol()
    A, O, H, Bal = st["amplitude"], st["ondulation"], st["lourdeur"], st["balayage"]
    tau = 2 * np.pi
    b = VOL_BATTEMENTS * t
    g = vol_plane(t, st, effort, plane_force)
    fl = 1 - g
    raf = 0.6 * np.sin(tau * 7 * t) + 0.4 * np.sin(tau * 11 * t + 1)          # rafales (vol plané)
    lent = tau * 2 * t                                                      # ondulation lente : 2 par boucle
    P = {}
    # ailes : battement (fl) et pose de plané (g)
    s0, x0 = coup(b)
    s1, x1 = coup(b - 0.07)
    hautR = (fl * (-6 * appui(x0) + 8 * plie(x0)), fl * (5 * appui(x0) - 16 * plie(x0)) + g * (-4 - 14 * Bal),
             fl * (-8 + 38 * A * s0) + g * (-30 - 4 * Bal + 3 * raf))
    basR = (0, fl * (4 * appui(x1) - 22 * plie(x1)) + g * (4 - 24 * Bal),
            fl * (-2 + 18 * A * s1 - 30 * plie(x1)) + g * (8 + 1.5 * raf))
    roulis = 2.5 * raf * g                                                   # l'aile du côté qui tombe se relève
    P["WingUpperR"], P["WingUpperL"] = (hautR[0], hautR[1], hautR[2] + roulis), (hautR[0], -hautR[1], -(hautR[2] - roulis))
    P.update(sides("WingLower", basR))
    for j in range(4):
        sj, xj = coup(b - 0.13 - 0.03 * j)
        P.update(sides(f"WingFinger{j + 1}", (0, fl * (3 * j * (1 - 1.3 * plie(xj)) + 2 * appui(xj)) + g * (2.5 * j - 3 * Bal * j),
                                              fl * (12 * A * sj - 10 * plie(xj)) + g * (2 + 1.5 * raf))))
    # corps : monte pendant la descente des ailes, ondule ; plus à plat en vol plané
    lift = -coup(b - 0.18)[0]
    P["Root"] = (-4 + fl * 2.5 * A * -coup(b - 0.1)[0] + 1.5 * g, 2.5 * O * np.sin(lent + 0.3),
                 2 * O * np.sin(lent + 1.1) + 3 * raf * g)
    P["Spine"] = (fl * 2 * O * np.sin(tau * b + 1.0), -2 * O * np.sin(lent + 0.9), 0)
    P["Chest"] = (fl * 2 * O * np.sin(tau * b + 1.4), -1.5 * O * np.sin(lent + 1.5), -1.0 * O * np.sin(lent + 1.8))
    P["Neck1"] = (-8 + fl * 3 * O * np.sin(tau * b + 1.6), 2 * O * np.sin(lent + 1.9), 0)
    P["Neck2"] = (-4 + fl * 2 * O * np.sin(tau * b + 2.0), 1.5 * O * np.sin(lent + 2.3), 0)
    P["Neck3"] = (fl * 1.5 * O * np.sin(tau * b + 2.4), 1.0 * O * np.sin(lent + 2.7), 0)
    tang = sum(P[n][0] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3"))
    lac = sum(P[n][1] for n in ("Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3"))
    P["Head"] = (-0.9 * tang - 6.5, -0.8 * lac, -0.6 * (P["Root"][2] + P["Chest"][2]))      # tête stabilisée
    P["Jaw"] = (-4 - 2.5 * fl * appui(x0), 0, 0)
    # pattes : avant repliées, arrière qui traînent ; ballottent en retard (droite et gauche décalées)
    for sd, d in (("R", 0.0), ("L", 0.35)):
        ph = tau * b - d
        P["FrontUpperLeg" + sd] = (-22 + fl * 4 * H * np.sin(ph - 1.0), 0, 0)
        P["FrontLowerLeg" + sd] = (48 + fl * 5 * H * np.sin(ph - 1.5), 0, 0)
        P["FrontFoot" + sd] = (-35 + fl * 6 * H * np.sin(ph - 2.0), 0, 0)
        P["BackUpperLeg" + sd] = (-28 - 4 * g + fl * 4 * H * np.sin(ph - 1.2), 0, 0)
        P["BackLowerLeg" + sd] = (-12 + fl * 6 * H * np.sin(ph - 1.7), 0, 0)
        P["BackFoot" + sd] = (-35 + fl * 8 * H * np.sin(ph - 2.2), 0, 0)
    # queue : vague verticale au rythme des ailes (amplitude croissante vers le bout) + S lent (gouvernail)
    for i in range(6):
        P[f"Tail{i + 1}"] = ((3 if i == 0 else 0) + fl * (1.5 + 0.8 * i) * O * np.sin(tau * b - 0.7 * i - 0.5),
                             (2.5 + 1.6 * i) * O * np.sin(lent - 0.6 * i) + 4 * g * raf * (i + 1) / 6, 0)
    regard = 10 * np.sin(tau * t) + 12 * g * np.sin(tau * 2 * t)
    P.update(eyes(blink(t, 0.37), regard, -4 * g))
    return P, np.array([0, 4.5 + fl * 0.55 * H * A * lift - 0.25 * g + 0.15 * np.sin(tau * t),
                        fl * 0.1 * np.sin(tau * b)])


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
                "Neck1": (2 * br, -0.3 * tc, 0), "Neck2": (1 * br, -0.3 * tc, 0), "Neck3": (0.4 * th, -0.2 * tc, 0),
                "Head": (-2 * br + 0.6 * th, -0.2 * tc, 0), "Jaw": (-3 - 3 * max(0, br), 0, 0)})
    P.update(sides("WingUpper", (0, -38, -22 + 2 * br)))
    for i in range(6):
        P[f"Tail{i + 1}"] = (1.5 * np.sin(2 * np.pi * t - 0.5 * i), 6 * np.sin(2 * np.pi * t - 0.6 * i), 0)
    P.update(eyes(lid, cap, haut))
    return P, np.array([0, 0.05 * br, 0])


def vol_face(t):
    return vol(t)


ANIMS = [("Vol v2 (Feu) : battements puis plané", vol, C + [-34, 2, -26], C + [0, 4.0, -1.0], 50),
         ("Vol v2, de face", vol_face, C + [0, 9, -40], C + [0, 4.5, -1.0], 50),
         ("Rugissement", rugit, C + [-26, 4, -32], C + [0, 2.0, -2.5], 44),
         ("Repos : regard, saccades et clignements", repos, None, None, 34)]
# deuxième GIF : nouvelles animations (les séquences jouent une fois par boucle du GIF)
ANIMS2 = [("Marche (pas à 4 temps)", marche, C + [-30, 7, -30], C + [0, 0.5, -1.5], 42),
          ("Décollage", decollage, C + [-36, 6, -30], C + [0, 3.0, -1.5], 50),
          ("Atterrissage", atterrissage, C + [-36, 6, -30], C + [0, 3.0, -1.5], 50),
          ("Souffle de feu", souffle_feu, C + [-34, 9, -22], C + [0, 1.0, -8.0], 54)]


def sol_items():
    """Sol (dessous des pattes au repos) pour voir les appuis et la hauteur."""
    y = AL.SOL - 0.005
    v = np.array([[-16, y, -22], [16, y, -22], [16, y, 16], [-16, y, 16]], float) + [C[0], 0, C[2]]
    return [(v, np.tile([0, 1, 0], (4, 1)), np.array([[0, 2, 1], [0, 3, 2]]), rendu.hex_rgb("#2A3040"), False)]


def flammes(pose, off, feu, t):
    """Aperçu du souffle (dans Roblox ce sont des particules) : chapelet de flammes lumineuses depuis la gueule."""
    if feu < 0.05:
        return []
    import trimesh
    sk = AL._Os()
    G = sk.matrices(pose, off)
    Gh = G[sk.index["Head"]]
    a, b = RG.hl((0, -0.15, -2.75)), RG.hl((0, -0.15, -3.75))
    p0 = Gh[:3, :3] @ a + Gh[:3, 3]
    d = Gh[:3, :3] @ (b - a); d /= np.linalg.norm(d)
    out = []
    rng = np.random.default_rng(int(t * 1000))
    for k in range(14):
        x = (k + rng.random()) / 14 * 10 * feu
        r = 0.3 + 0.16 * x
        c = p0 + d * x + rng.normal(0, 0.12 * x, 3)
        m = trimesh.creation.icosphere(1, r)
        m.apply_translation(c)
        col = "#FFF4C0" if x < 2.5 else ("#FFC21A" if x < 7 else "#FF6A18")
        out.append((np.asarray(m.vertices), np.asarray(m.vertex_normals), np.asarray(m.faces), rendu.hex_rgb(col), True))
    return out


def main():
    rig = RG.Rig()
    hc = RG.hl((0, 0.6, -1.4))
    cw, ch = 470, 380
    font = ImageFont.truetype(FONT_B, 18)
    for anims, nom, nb in ((ANIMS, "demo-animations-v6.gif", 64), (ANIMS2, "demo-animations-v6-nouvelles.gif", N)):
        frames = []
        for i in range(nb):
            t = i / nb
            im = Image.new("RGB", (cw * 2, ch * 2), (16, 19, 28))
            dr = ImageDraw.Draw(im)
            for j, (titre, fn, eye, tg, fov) in enumerate(anims):
                pose, off = fn(t)
                extra = sol_items()
                if fn is souffle_feu:
                    import sequences_v6 as SQ
                    extra += flammes(pose, off, SQ.SOUFFLE.pose(t)[4], t)
                if eye is None:                               # gros plan sur la tête pour le repos
                    eye, tg = hc + [-17, 4, -19], hc + [0.3, 0.4, 0.8]
                x0, y0 = (j % 2) * cw, (j // 2) * ch
                im.paste(rendu.render(rig.items(pose, off) + extra, eye, tg, size=(cw - 6, ch - 6), fov=fov, ss=1),
                         (x0, y0))
                dr.text((x0 + 14, y0 + 10), titre, font=font, fill=(255, 210, 122))
            frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=160))
            print(nom, i, flush=True)
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", nom)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=55, loop=0, optimize=True)
    vol_lignees(cw, ch, font)


def vol_lignees(cw, ch, font, n=64):
    """Les 4 lignées en vol, chacune avec son style (boucles ramenées à la même longueur dans le GIF)."""
    import lignees_v6 as L6
    import palette_corps as PC
    rigs = {lin: RG.Rig(lignee=lin) for lin in PC.LIGNEES}
    frames = []
    for i in range(n):
        t = i / n
        im = Image.new("RGB", (cw * 2, ch * 2), (16, 19, 28))
        dr = ImageDraw.Draw(im)
        for j, lin in enumerate(PC.LIGNEES):
            st = L6.STYLE[lin]["vol"]
            pose, off = vol(t, st)
            x0, y0 = (j % 2) * cw, (j // 2) * ch
            im.paste(rendu.render(rigs[lin].items(pose, off), C + [-30, 10, -28], C + [0, 4.0, -0.5],
                                  size=(cw - 6, ch - 6), fov=52, ss=1), (x0, y0))
            dr.text((x0 + 14, y0 + 10), f"{PC.NOMS[lin]} : boucle de {st['duree']:.1f} s, plané {st['plane']:.0%}".replace(".", ","),
                    font=font, fill=(255, 210, 122))
        frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=200))
        print("vol lignées", i, flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo-vol-lignees-v6.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=60, loop=0, optimize=True)


if __name__ == "__main__":
    main()
