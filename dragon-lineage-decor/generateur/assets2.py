# Série 2 : squelette de dragon, portes, murets, îles flottantes.
import math
import numpy as np
from meshlib import (Asset, lathe, tube, blob, box, loft, ring, transform,
                     rot_matrix_x, rot_matrix_y, rot_matrix_z)

C = {
    "bone": "#BDB39C", "bone_dark": "#9C927C", "socket": "#141416", "stone": "#4A4A51",
    "stone_dark": "#3A3A40", "sign": "#4A3426", "iron": "#26262A", "flame": "#FF7A1A",
    "grass": "#3C5A30", "rock": "#4E4A48", "root": "#3A2A22", "crystal": "#6FE3FF",
}


def add_mesh(a, part, vf, mat=None, offset=(0, 0, 0), flip=False, **kw):
    v, f = vf
    v = transform(v, mat, offset)
    if flip:
        f = [(x, z, y) for x, y, z in f]
    a.add(part, v, f, **kw)


def ellipse_ring(z, w, h, yc, sides=8, rng=None, jitter=0.0):
    pts = []
    for i in range(sides):
        t = 2 * math.pi * i / sides
        j = 1 + (rng.uniform(-jitter, jitter) if rng is not None and jitter else 0)
        pts.append([w / 2 * math.cos(t) * j, yc + h / 2 * math.sin(t) * j, z])
    return np.array(pts)


# ---------------- crâne de dragon (regarde vers +Z) ----------------
def skull_parts(rng, s=1.0):
    """Renvoie {partie: [(verts, faces), ...]} en coordonnées locales."""
    out = {"Bones": [], "Sockets": []}
    prof = [(-4.0, 2.0, 1.8, 2.2), (-2.6, 2.7, 2.5, 2.5), (-0.6, 2.4, 2.1, 2.4), (0.8, 1.7, 1.5, 2.1),
            (2.8, 1.3, 1.15, 1.8), (4.8, 1.05, 0.9, 1.55), (6.2, 0.7, 0.55, 1.35)]
    rings = [ellipse_ring(z, w, h, y, 8, rng, 0.06) for z, w, h, y in prof]
    v, f = loft(rings)
    out["Bones"].append((np.array(v) * s, f))
    # mâchoire inférieure, légèrement ouverte
    jprof = [(-2.4, 2.2, 0.6, 0.75), (0.0, 1.8, 0.55, 0.65), (2.8, 1.25, 0.45, 0.55), (5.6, 0.8, 0.35, 0.5)]
    v, f = loft([ellipse_ring(z, w, h, y, 6) for z, w, h, y in jprof])
    v = transform(np.array(v) - [0, 0.9, -2.4], rot_matrix_x(0.18), [0, 0.9, -2.4])
    out["Bones"].append((np.array(v) * s, f))
    for side in (-1, 1):
        # cornes vers l'arrière
        v, f = tube([[side * 0.9, 3.3, -2.4], [side * 1.7, 4.3, -4.6], [side * 1.9, 4.6, -6.8], [side * 1.4, 5.6, -8.6]],
                    [0.55, 0.45, 0.3, 0], 5, tip=True)
        out["Bones"].append((np.array(v) * s, f))
        # petite corne de joue
        v, f = tube([[side * 1.2, 2.0, -2.8], [side * 2.0, 2.2, -4.0]], [0.3, 0], 4, tip=True)
        out["Bones"].append((np.array(v) * s, f))
        # orbite sombre
        v, f = blob([side * 1.05, 2.75, -0.3], 0.5, (0.5, 0.75, 1.0), 0.1, rng, subdiv=0)
        out["Sockets"].append((np.array(v) * s, f))
        # narine
        v, f = blob([side * 0.32, 1.85, 5.4], 0.18, (0.6, 0.6, 1.0), 0.1, rng, subdiv=0)
        out["Sockets"].append((np.array(v) * s, f))
        # dents
        for k in range(5):
            z = 0.9 + k * 1.05
            w = np.interp(z, [p[0] for p in prof], [p[1] for p in prof])
            yb = np.interp(z, [p[0] for p in prof], [p[3] - p[2] / 2 for p in prof])
            x = side * w * 0.42
            v, f = tube([[x, yb + 0.1, z], [x, yb - 0.55, z + 0.1]], [0.16, 0], 3, tip=True)
            out["Bones"].append((np.array(v) * s, f))
    return out


def dragon_skull(name, seed, s=1.0):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    for part, items in skull_parts(rng, s).items():
        for v, f in items:
            col = C["bone"] if part == "Bones" else C["socket"]
            a.add(part, v, f, col, "Limestone" if part == "Bones" else "SmoothPlastic")
    return a


# ---------------- squelette complet, à moitié enterré ----------------
def dragon_skeleton(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Bones", C["bone"], "Limestone")
    a.part("Sockets", C["socket"])

    def spine_y(z):
        return 9.0 * math.exp(-((z + 8) / 13) ** 2) + 0.4

    # colonne : du cou (z=+11) au bout de la queue (z=-46), la queue serpente
    zs = np.linspace(11, -46, 34)
    pts = [np.array([math.sin(z * 0.09) * (3 if z < -14 else 0.6), spine_y(z) if z < 2 else np.interp(z, [2, 11], [spine_y(2), 1.6]), z])
           for z in zs]
    for i, p in enumerate(pts):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        size = np.interp(p[2], [-46, -20, -8, 11], [0.35, 0.8, 1.1, 0.7])
        v, f = tube([p - d * 0.55 * size, p + d * 0.55 * size], [size, size], 6, angle0=i)
        a.add("Bones", v, f)
        # épine dorsale
        v, f = tube([p, p + [0, 1.7 * size, -0.4 * size]], [0.35 * size, 0], 4, tip=True)
        a.add("Bones", v, f)
    # côtes : arcs qui plongent dans le sol
    for k, z in enumerate(np.arange(-1.5, -16, -1.8)):
        Y = spine_y(z)
        sc = np.interp(z, [-16, -8, -1.5], [0.65, 1.0, 0.8])
        for side in (-1, 1):
            if rng.random() < 0.12:  # quelques côtes cassées
                rib = [[side * 0.8, Y - 0.2, z], [side * 4.2 * sc, Y - 0.6, z - 0.4], [side * 5.8 * sc, Y - 3.0 * sc, z - 0.7]]
                v, f = tube(rib, [0.42, 0.35, 0], 5, tip=True)
            else:
                rib = [[side * 0.8, Y - 0.2, z], [side * 4.2 * sc, Y - 0.6, z - 0.4], [side * 6.4 * sc, Y - 3.8 * sc, z - 0.8],
                       [side * 6.4 * sc, Y - 7.4 * sc, z - 1.0], [side * 5.2 * sc, -1.5, z - 1.1]]
                v, f = tube(rib, [0.45, 0.42, 0.38, 0.32, 0.28], 5)
            a.add("Bones", v, f)
    # aile enterrée : os qui sortent du sol en éventail
    base = np.array([10.5, -1.0, -6.0])
    elbow = base + [1.5, 7.0, 1.0]
    v, f = tube([base, elbow], [0.8, 0.65], 6)
    a.add("Bones", v, f)
    for k, (dx, dy, dz) in enumerate([(-1.5, 9, -4), (2.5, 10, -6), (6, 7, -7)]):
        tip = elbow + [dx, dy, dz]
        mid = (elbow + tip) / 2 + [0.6, 0.4, 0]
        v, f = tube([elbow, mid, tip], [0.45, 0.32, 0], 5, tip=True)
        a.add("Bones", v, f)
    # patte avant griffue qui sort du sol
    for k in range(3):
        ang = -0.5 + k * 0.5
        s0 = np.array([-7.5, 0.2, 3.0])
        d = np.array([math.sin(ang), 0, math.cos(ang)])
        v, f = tube([s0, s0 + d * 1.5 + [0, 1.2, 0], s0 + d * 3.2 + [0, 0.9, 0], s0 + d * 3.9 + [0, -0.4, 0]],
                    [0.4, 0.35, 0.25, 0], 5, tip=True)
        a.add("Bones", v, f)
    # crâne posé au sol au bout du cou
    parts = skull_parts(rng, 1.25)
    mat = rot_matrix_y(0.35) @ rot_matrix_z(0.18)
    for part, items in parts.items():
        for v, f in items:
            a.add(part, transform(v, mat, [1.0, -0.2, 13.0]), f)
    return a


# ---------------- porte de repaire ----------------
def stone_pillar(rng, h, w):
    return lathe([(w * 0.75, 0), (w * 0.75, 1.0), (w * 0.62, 1.3), (w * 0.56, h - 1.2), (w * 0.72, h - 0.9),
                  (w * 0.72, h), (0, h)], 4, angle0=math.pi / 4, jitter=0.04, rng=rng)


def lair_gate(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Stone", C["stone"], "Slate")
    a.part("Bones", C["bone"], "Limestone")
    a.part("Sign", C["sign"], "Wood")
    a.part("Flame", C["flame"], "Neon")
    a.part("Sockets", C["socket"])
    half = 8.0
    for side in (-1, 1):
        add_mesh(a, "Stone", stone_pillar(rng, 12.0, 2.6), offset=[side * half, 0, 0])
        # corne qui s'enroule au-dessus du pilier
        v, f = tube([[side * half, 11.6, 0], [side * (half + 1.6), 14.0, -0.3], [side * (half + 1.9), 16.6, -0.8],
                     [side * (half + 0.9), 18.6, -1.2], [side * (half - 0.4), 19.2, -0.9]],
                    [0.95, 0.8, 0.6, 0.35, 0], 6, tip=True)
        a.add("Bones", v, f)
        # coupe et flamme sur le pilier, devant la corne
        add_mesh(a, "Stone", lathe([(0.5, 0), (0.95, 0.6), (0.85, 0.8), (0, 0.6)], 6), offset=[side * half, 12.0, 0.9])
        for k, (h, r) in enumerate([(2.4, 0.75), (1.6, 0.5)]):
            v, f = lathe([(r, 0), (r * 0.6, h * 0.55), (0, h)], 5, twist=0.5, angle0=k)
            a.add("Flame", transform(v, None, [side * half + k * 0.3, 12.55, 0.9 - k * 0.2]), f)
    # linteau en deux pierres
    for side in (-1, 1):
        v, f = box([side * 4.6, 12.75, 0], [9.6, 1.5, 2.2])
        a.add("Stone", v, f)
    # panneau (mettre le SurfaceGui sur la face avant, +Z)
    v, f = box([0, 10.4, 0.85], [8.5, 2.4, 0.35])
    a.add("Sign", v, f)
    for side in (-1, 1):
        v, f = box([side * 3.6, 11.75, 0.85], [0.18, 0.6, 0.18])
        a.add("Sign", v, f)
    # petit crâne de dragon au centre du linteau
    for part, items in skull_parts(rng, 0.62).items():
        for v, f in items:
            a.add(part, transform(v, rot_matrix_x(-0.15), [0, 13.4, -0.6]), f)
    return a


def egg_road_arch(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Stone", C["stone"], "Slate")
    a.part("StoneDark", C["stone_dark"], "Slate")
    a.part("Bones", C["bone"], "Limestone")
    a.part("Sign", C["sign"], "Wood")
    a.part("Iron", C["iron"], "Metal")
    a.part("Sockets", C["socket"])
    half, ph = 11.0, 13.0
    for side in (-1, 1):
        add_mesh(a, "Stone", stone_pillar(rng, ph, 3.4), offset=[side * half, 0, 0])
    # arc en claveaux
    R, n = half, 11
    for k in range(n):
        t0, t1 = math.pi * k / n, math.pi * (k + 1) / n
        tm = (t0 + t1) / 2
        L = 2 * (R + 1.2) * math.sin((t1 - t0) / 2) * 0.96
        v, f = box([0, 0, 0], [L, 2.6, 3.0 if k != n // 2 else 3.4])
        c = [math.cos(tm) * (R + 1.2), ph + math.sin(tm) * (R + 1.2), 0]
        v = transform(v, rot_matrix_z(tm - math.pi / 2), c)
        a.add("Stone" if k % 2 == 0 else "StoneDark", v, f)
    # crâne de dragon en clé de voûte, qui regarde la route
    top = ph + R + 1.2
    for part, items in skull_parts(rng, 0.75).items():
        for v, f in items:
            a.add(part, transform(v, rot_matrix_x(-0.35), [0, top + 0.2, 0.6]), f)
    # cornes en défense sur les côtés de l'arc
    for side in (-1, 1):
        v, f = tube([[side * 3.5, top - 1.0, 0.5], [side * 6.5, top + 1.2, 1.4], [side * 8.5, top + 4.0, 1.0]],
                    [0.7, 0.45, 0], 5, tip=True)
        a.add("Bones", v, f)
    # panneau suspendu par des chaînes
    v, f = box([0, ph + 3.0, 0.2], [13.0, 3.0, 0.45])
    a.add("Sign", v, f)
    for side in (-1, 1):
        x = side * 5.2
        y_arc = ph + math.sqrt(max(0.0, (R - 0.2) ** 2 - x ** 2))
        v, f = box([x, (ph + 4.5 + y_arc) / 2, 0.2], [0.2, y_arc - (ph + 4.5), 0.2])
        a.add("Iron", v, f)
    return a


# ---------------- murets de pierre modulaires ----------------
def wall(name, length, seed, broken=False):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Stone", C["stone"], "Slate")
    a.part("StoneDark", C["stone_dark"], "Slate")
    courses = [(0.0, 1.2, 1.6), (1.2, 2.2, 1.45), (2.2, 2.9, 1.7)]  # (bas, haut, épaisseur)
    for ci, (y0, y1, th) in enumerate(courses):
        x = -length / 2
        first = True
        while x < length / 2 - 0.01:
            w = rng.uniform(1.3, 2.4) if not (first and ci % 2) else rng.uniform(0.7, 1.1)
            first = False
            w = min(w, length / 2 - x)
            if length / 2 - x - w < 0.6:
                w = length / 2 - x
            gap = 0.06
            skip = broken and ci > 0 and (x > -0.5 and (ci == 2 or x < 1.5))
            if not skip:
                ins = rng.uniform(0.02, 0.12)
                v, f = box([x + w / 2, (y0 + y1) / 2, 0], [w - gap, y1 - y0 - gap, th - ins])
                v = np.array(v)
                v[:, 1] += rng.uniform(-0.05, 0.05, len(v)) * (v[:, 1] > y0 + 0.1)
                a.add("Stone" if rng.random() < 0.6 else "StoneDark", v.tolist(), f)
            x += w
    if broken:
        for k in range(4):
            v, f = blob([rng.uniform(-0.5, 2.0), 0.25, rng.choice([-1, 1]) * rng.uniform(1.1, 1.8)],
                        rng.uniform(0.35, 0.6), (1.2, 0.7, 1.0), 0.25, rng, subdiv=0)
            a.add("StoneDark", v, f)
    return a


def wall_post(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Stone", C["stone"], "Slate")
    v, f = lathe([(1.45, 0), (1.45, 3.2), (1.6, 3.4), (1.6, 3.8), (0.9, 4.3), (0, 4.4)], 4,
                 angle0=math.pi / 4, jitter=0.03, rng=rng)
    a.add("Stone", v, f)
    return a


# ---------------- îles flottantes ----------------
def floating_island(name, R, seed, crystals=4):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    n = 11
    angs = [2 * math.pi * i / n + rng.uniform(-0.15, 0.15) for i in range(n)]
    rad = [R * rng.uniform(0.82, 1.1) for _ in range(n)]

    def r_at(scale, y, jit=0.0, off=(0, 0)):
        return np.array([[off[0] + rad[i] * scale * (1 + rng.uniform(-jit, jit)) * math.cos(angs[i]), y,
                          off[1] - rad[i] * scale * (1 + rng.uniform(-jit, jit)) * math.sin(angs[i])] for i in range(n)])

    top = r_at(1.0, 0.0)
    v, f = loft([r_at(1.03, -0.9), top + [0, 0.35, 0]], cap_start=False, cap_end=True)
    a.add("Grass", v, f, C["grass"], "Grass")
    rings = [r_at(1.0, -0.9), r_at(0.82, -R * 0.35, 0.12), r_at(0.55, -R * 0.75, 0.15, (R * 0.05, 0)),
             r_at(0.28, -R * 1.1, 0.2, (R * 0.12, R * 0.05)), np.array([[R * 0.18, -R * 1.45, R * 0.1]])]
    v, f = loft(rings, cap_start=False, cap_end=False)
    f = [(x, z, y) for x, y, z in f]  # le profil descend : on inverse l'ordre pour garder les faces vers l'extérieur
    a.add("Rock", v, f, C["rock"], "Slate")
    for k in range(6):  # racines qui pendent
        i = rng.integers(n)
        p = r_at(0.75, -R * 0.35)[i] * [1, 1, 1]
        L = R * rng.uniform(0.5, 0.9)
        v, f = tube([p, p + [rng.uniform(-1, 1), -L * 0.5, rng.uniform(-1, 1)], p + [rng.uniform(-1.5, 1.5), -L, rng.uniform(-1.5, 1.5)]],
                    [R * 0.035, R * 0.025, 0], 4, tip=True)
        a.add("Roots", v, f, C["root"], "Wood")
    for k in range(crystals):  # amas de cristaux
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(0, R * 0.35)
        h = R * rng.uniform(0.25, 0.5)
        v, f = lathe([(0, -0.4), (h * 0.18, h * 0.25), (h * 0.15, h * 0.75), (0, h)], 6, angle0=rng.uniform(0, 1))
        v = transform(v, rot_matrix_z(rng.uniform(-0.35, 0.35)) @ rot_matrix_x(rng.uniform(-0.35, 0.35)),
                      [R * 0.1 + dist * math.cos(ang), 0.35, dist * math.sin(ang)])
        a.add("Crystal", v, f, C["crystal"], "Neon")
    return a


def all_assets():
    return [
        dragon_skeleton("Dragon_Skeleton", 21),
        dragon_skull("Dragon_Skull", 22, 1.0),
        lair_gate("Gate_Lair", 23),
        egg_road_arch("Gate_EggRoad", 24),
        wall("Wall_Straight_8", 8.0, 25),
        wall("Wall_Straight_4", 4.0, 26),
        wall("Wall_Broken_8", 8.0, 27, broken=True),
        wall_post("Wall_Post", 28),
        floating_island("Island_Large", 14.0, 29, crystals=5),
        floating_island("Island_Small", 7.0, 30, crystals=3),
    ]
