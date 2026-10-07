# Série 4 : crâne de dragon v3 — plus massif et menaçant (le v2 est conservé tel quel).
# Changements par rapport au v2 :
#  - museau plus court et plus haut (moins « crocodile / cheval ») ;
#  - arcades sourcilières en surplomb au-dessus d'orbites plus grandes et creuses ;
#  - cornes épaisses qui partent sur les côtés puis s'enroulent vers l'avant (lisibles de face) ;
#  - collerette réduite à 2 grosses épines par côté, plus d'épine de pommette
#    (de face, le v2 ressemblait à un scarabée).
import math
import numpy as np
from meshlib import Asset, tube, blob, loft, transform, rot_matrix_x, rot_matrix_y, rot_matrix_z
import assets2
from assets3 import C, PART_STYLE, _section


def skull_v3(rng, s=1.0, eyes="sombre"):
    # eyes : "v3" (première proposition), "sombre", "braise" (lueur orange) ou "cyan" (comme les runes)
    out = {"Bones": [], "Horns": [], "Sockets": []}
    up = math.pi / 2
    brow = [(up - 0.7, 0.42, 0.26), (up + 0.7, 0.42, 0.26)]
    cheek = [(0.0, 0.18, 0.4), (math.pi, 0.18, 0.4)]
    ridge = [(up, 0.12, 0.28)]
    #         z     demi-larg  haut  bas   bosses
    prof = [(-3.8, 1.3, 3.4, 1.4, []),
            (-3.0, 1.75, 4.1, 1.0, cheek),
            (-1.9, 1.85, 4.35, 0.85, cheek),
            (-0.8, 1.7, 4.2, 0.9, brow + cheek),
            (0.2, 1.5, 3.9, 0.95, brow),
            (1.2, 1.2, 3.35, 1.0, ridge),
            (2.3, 1.05, 3.0, 1.0, ridge),
            (3.3, 0.98, 2.8, 1.05, ridge + [(0.0, 0.14, 0.3), (math.pi, 0.14, 0.3)]),
            (4.1, 0.8, 2.55, 1.1, []),
            (4.6, 0.45, 2.2, 1.25, [])]
    rings = [_section(z, w, t, b, f) for z, w, t, b, f in prof]
    rings = [r * (1 + rng.uniform(-0.02, 0.02, r.shape) * [1, 1, 0]) for r in rings]
    v, f = loft(rings)
    out["Bones"].append((v, f))

    # mâchoire inférieure, plus épaisse et plus ouverte (gueule menaçante)
    jprof = [(-2.8, 1.55, 1.3, 0.5), (-1.6, 1.5, 1.15, 0.35), (0.6, 1.2, 1.05, 0.3),
             (2.6, 0.95, 1.0, 0.32), (3.9, 0.7, 1.0, 0.4), (4.5, 0.4, 1.05, 0.6)]
    jr = [_section(z, w, t, b, [], sides=8) for z, w, t, b in jprof]
    v, f = loft(jr)
    PIV, OPEN = np.array([0, 1.15, -2.8]), 0.34
    v = transform(np.array(v) - PIV, rot_matrix_x(OPEN), PIV)
    out["Bones"].append((v, f))

    for side in (-1, 1):
        # arcade sourcilière en surplomb (os qui fait « froncer » le regard)
        bp = [[side * 0.45, 4.05, 1.0], [side * 1.25, 4.15, 0.0], [side * 1.85, 3.85, -1.0], [side * 2.05, 3.5, -1.7]]
        v, f = tube(bp, [0.32, 0.42, 0.36, 0.0], 5, tip=True)
        out["Bones"].append((v, f))
        # cornes : épaisses, partent sur le côté et vers l'arrière puis s'enroulent vers l'avant
        path = [[side * 1.3, 3.9, -2.0], [side * 2.4, 4.6, -3.3], [side * 3.7, 5.0, -4.0],
                [side * 4.9, 5.6, -3.6], [side * 5.6, 6.6, -2.6], [side * 5.6, 7.6, -1.3], [side * 5.1, 8.3, -0.3]]
        radii = [0.9, 0.82, 0.7, 0.55, 0.4, 0.24, 0]
        p2, r2 = [], []
        for i in range(len(path) - 1):
            a, b = np.array(path[i]), np.array(path[i + 1])
            p2 += [a, (a + b) / 2]
            r2 += [radii[i], (radii[i] + radii[i + 1]) / 2 * 0.86]   # anneaux de la corne
        p2.append(np.array(path[-1])); r2.append(0)
        v, f = tube(p2, r2, 6, tip=True)
        out["Horns"].append((v, f))
        # petite corne secondaire, droite vers l'arrière (silhouette de profil)
        v, f = tube([[side * 1.1, 3.4, -3.2], [side * 1.6, 3.6, -4.8], [side * 1.9, 3.5, -6.0]], [0.45, 0.28, 0], 5, tip=True)
        out["Horns"].append((v, f))
        # collerette : 2 grosses épines vers l'arrière et le haut (au lieu de 3 + pommette)
        for y, z, L in [(2.6, -3.4, 2.0), (1.7, -3.2, 1.5)]:
            base = np.array([side * 1.5, y, z])
            tip = base + [side * 0.9, 0.35, -L]
            v, f = tube([base, (base + tip) / 2, tip], [0.38, 0.24, 0], 4, tip=True)
            out["Horns"].append((v, f))
        # orbite : amande anguleuse inclinée (coin avant bas, coin arrière haut = regard méchant),
        # sortie un peu de la surface et sous l'arcade pour être lisible de face et de profil
        if eyes != "v3":
            ex = side * 1.66
            path = [[ex - side * 0.08, 2.9, 0.75], [ex + side * 0.1, 3.12, 0.1], [ex + side * 0.14, 3.42, -0.6], [ex, 3.8, -1.35]]
            v, f = tube(path, [0.0, 0.58, 0.5, 0.0], 6, tip=True)
            v = np.array(v)
            v[:, 0] = ex + (v[:, 0] - ex) * 0.6           # aplatie contre le crâne
            out["Sockets"].append((v.tolist(), f))
            if eyes in ("braise", "cyan"):
                # petite lueur au fond de l'orbite (pupille fendue)
                v, f = tube([[ex + side * 0.2, 3.0, 0.3], [ex + side * 0.3, 3.28, -0.3], [ex + side * 0.22, 3.6, -0.85]],
                            [0.0, 0.24, 0.0], 4, tip=True)
                out.setdefault("Eyes", []).append((v, f))
        else:
            v, f = blob([0, 0, 0], 1.0, (0.36, 0.5, 0.78), 0.05, rng, subdiv=1)
            v = transform(v, rot_matrix_y(side * 0.45) @ rot_matrix_z(side * 0.4), [side * 1.5, 3.3, -0.35])
            out["Sockets"].append((v, f))
        # fenêtre temporale
        ts = (0.22, 0.42, 0.55) if eyes == "v3" else (0.18, 0.26, 0.38)   # plus discrète : ne doit pas passer pour un 2e œil
        v, f = blob([0, 0, 0], 1.0, ts, 0.05, rng, subdiv=0)
        v = transform(v, rot_matrix_y(side * 0.2), [side * 1.85, 2.5 if eyes == "v3" else 2.2, -2.4])
        out["Sockets"].append((v, f))
        # narine
        v, f = blob([0, 0, 0], 1.0, (0.2, 0.17, 0.4), 0.05, rng, subdiv=0)
        v = transform(v, rot_matrix_y(side * 0.3), [side * 0.55, 2.55, 3.9])
        out["Sockets"].append((v, f))
        # dents du haut : un énorme croc + rangée
        for k in range(5):
            z = 3.9 - k * 0.9
            x = side * (0.72 + k * 0.12)
            L = 1.35 if k == 1 else 0.6 - k * 0.04
            r = 0.26 if k == 1 else 0.16
            v, f = tube([[x, 1.2, z], [x, 1.2 - L * 0.6, z - 0.05], [x * 0.96, 1.2 - L, z - 0.25]], [r, r * 0.6, 0], 4, tip=True)
            out["Bones"].append((v, f))
        # dents du bas, avec un croc qui remonte
        for k in range(4):
            z = 3.7 - k * 1.0
            x = side * (0.6 + k * 0.12)
            p = (rot_matrix_x(OPEN) @ (np.array([x, 1.35, z]) - PIV)) + PIV
            L = 1.0 if k == 0 else 0.5
            v, f = tube([p, p + [0, L, 0.12]], [0.18, 0], 4, tip=True)
            out["Bones"].append((v, f))
    # crête : 3 épines plus marquées sur le dessus
    for k, z in enumerate([-1.3, -2.3, -3.2]):
        v, f = tube([[0, 4.3, z], [0, 5.1 - k * 0.15, z - 0.7]], [0.26, 0], 4, tip=True)
        out["Horns"].append((v, f))
    return {p: [(np.array(v) * s, f) for v, f in items] for p, items in out.items()}


EYE_COLORS = {"braise": "#FF5418", "cyan": "#6FE3FF"}


def dragon_skull_v3(name, seed, eyes="sombre"):
    old = assets2.skull_parts
    assets2.skull_parts = lambda rng, s=1.0: skull_v3(rng, s, eyes)
    try:
        a = assets2.dragon_skull(name, seed, 1.0)
    finally:
        assets2.skull_parts = old
    for pname, p in a.parts.items():
        p["color"], p["material"] = PART_STYLE.get(pname, (C["bone"], "SmoothPlastic"))
        if pname == "Eyes":
            p["color"], p["material"] = EYE_COLORS[eyes], "Neon"
    return a


def all_assets():
    return [dragon_skull_v3("Dragon_Skull_v3_YeuxSombres", 22, "sombre"),
            dragon_skull_v3("Dragon_Skull_v3_YeuxBraise", 22, "braise"),
            dragon_skull_v3("Dragon_Skull_v3_YeuxCyan", 22, "cyan")]
