# Série 3 : crâne de dragon détaillé, vraie flamme low-poly, piliers de l'autel.
import math
import numpy as np
from meshlib import Asset, lathe, tube, blob, box, loft, transform, rot_matrix_x, rot_matrix_y, rot_matrix_z
import assets
import assets2

C = {
    "bone": "#CFC8B4", "horn": "#5E5548", "socket": "#0E0E10", "flame_out": "#FF5418",
    "flame_in": "#FFC23A", "coals": "#2A1410", "ember": "#FF4A12", "stone": "#4A4A51",
    "stone_dark": "#3A3A40", "claw": "#2A2A2F", "crystal": "#6FE3FF", "rune": "#6FE3FF",
}
PART_STYLE = {
    "Bones": (C["bone"], "SmoothPlastic"), "Horns": (C["horn"], "SmoothPlastic"),
    "Sockets": (C["socket"], "SmoothPlastic"), "Flame": (C["flame_out"], "Neon"),
    "FlameCore": (C["flame_in"], "Neon"), "Coals": (C["coals"], "Basalt"), "Embers": (C["ember"], "Neon"),
}


# ---------------- crâne détaillé (regarde vers +Z) ----------------
def _section(z, w, top, bot, feats, sides=12):
    """Anneau autour de l'axe Z : superellipse + bosses (arcade, pommette, arête du museau)."""
    pts = []
    yc, h = (top + bot) / 2, (top - bot) / 2
    for i in range(sides):
        t = 2 * math.pi * i / sides
        c, s = math.cos(t), math.sin(t)
        k = 1.0
        for ang, amp, width in feats:  # bosse gaussienne autour de l'angle 'ang'
            d = math.atan2(math.sin(t - ang), math.cos(t - ang))
            k += amp * math.exp(-(d / width) ** 2)
        x = w * k * math.copysign(abs(c) ** 0.8, c)
        y = yc + h * k * math.copysign(abs(s) ** 0.8, s)
        pts.append([x, y, z])
    return np.array(pts)


def skull_v2(rng, s=1.0):
    out = {"Bones": [], "Horns": [], "Sockets": []}
    up = math.pi / 2
    brow = [(up - 0.75, 0.32, 0.28), (up + 0.75, 0.32, 0.28)]       # arcades sourcilières
    cheek = [(0.0, 0.2, 0.35), (math.pi, 0.2, 0.35)]                # pommettes
    ridge = [(up, 0.14, 0.25)]                                      # arête du museau
    #         z     demi-larg  haut  bas   bosses
    prof = [(-4.2, 1.15, 3.1, 1.3, []),
            (-3.4, 1.55, 3.7, 1.0, cheek),
            (-2.2, 1.6, 3.9, 0.9, cheek),
            (-1.0, 1.45, 3.75, 1.0, brow + cheek),
            (0.0, 1.3, 3.45, 1.05, brow),
            (1.0, 1.0, 2.9, 1.1, ridge),
            (2.4, 0.85, 2.55, 1.1, ridge),
            (3.8, 0.75, 2.3, 1.1, ridge),
            (5.0, 0.7, 2.15, 1.15, ridge + [(0.0, 0.12, 0.3), (math.pi, 0.12, 0.3)]),
            (5.9, 0.55, 1.95, 1.2, []),
            (6.4, 0.3, 1.7, 1.3, [])]
    rings = [_section(z, w, t, b, f) for z, w, t, b, f in prof]
    rings = [r * (1 + rng.uniform(-0.02, 0.02, r.shape) * [1, 1, 0]) for r in rings]
    v, f = loft(rings)
    out["Bones"].append((v, f))

    # mâchoire inférieure (mandibule en U), entrouverte
    jprof = [(-3.0, 1.35, 1.2, 0.55), (-1.8, 1.3, 1.05, 0.45), (0.5, 1.0, 0.95, 0.4),
             (3.0, 0.78, 0.9, 0.42), (5.2, 0.6, 0.9, 0.45), (6.0, 0.35, 0.95, 0.6)]
    jr = [_section(z, w, t, b, [], sides=8) for z, w, t, b in jprof]
    v, f = loft(jr)
    v = transform(np.array(v) - [0, 1.1, -3.0], rot_matrix_x(0.22), [0, 1.1, -3.0])
    out["Bones"].append((v, f))

    for side in (-1, 1):
        # cornes principales : partent vers l'arrière puis remontent, avec des anneaux
        path = [[side * 1.0, 3.6, -2.6], [side * 1.6, 4.3, -4.3], [side * 2.1, 4.6, -6.0],
                [side * 2.4, 5.4, -7.6], [side * 2.2, 6.6, -8.7], [side * 1.7, 7.8, -9.1]]
        radii = [0.62, 0.62 * 0.8, 0.5, 0.36, 0.22, 0]
        # anneaux : on insère un léger renflement entre chaque segment
        p2, r2 = [], []
        for i in range(len(path) - 1):
            a, b = np.array(path[i]), np.array(path[i + 1])
            p2 += [a, (a + b) / 2]
            r2 += [radii[i], (radii[i] + radii[i + 1]) / 2 * 0.86]
        p2.append(np.array(path[-1])); r2.append(0)
        v, f = tube(p2, r2, 6, tip=True)
        out["Horns"].append((v, f))
        # collerette : 3 épines vers l'arrière
        for k, (y, z, L) in enumerate([(3.0, -3.8, 2.0), (2.3, -4.0, 1.7), (1.6, -3.8, 1.3)]):
            base = np.array([side * 1.3, y, z])
            tip = base + [side * 0.8, -0.2 * k, -L]
            v, f = tube([base, (base + tip) / 2 + [side * 0.15, 0.15, 0], tip], [0.32, 0.2, 0], 4, tip=True)
            out["Horns"].append((v, f))
        # épine de pommette
        v, f = tube([[side * 1.5, 1.6, -1.0], [side * 2.1, 1.1, -2.3]], [0.25, 0], 4, tip=True)
        out["Horns"].append((v, f))
        # orbite : creux sombre en amande, incliné (regard menaçant)
        v, f = blob([0, 0, 0], 1.0, (0.28, 0.42, 0.75), 0.05, rng, subdiv=1)
        v = transform(v, rot_matrix_y(side * 0.35) @ rot_matrix_z(side * 0.35), [side * 1.28, 2.95, -0.4])
        out["Sockets"].append((v, f))
        # fenêtre temporale (ouverture derrière l'œil, typique des crânes de reptiles)
        v, f = blob([0, 0, 0], 1.0, (0.2, 0.38, 0.6), 0.05, rng, subdiv=0)
        v = transform(v, rot_matrix_y(side * 0.2), [side * 1.55, 2.5, -2.4])
        out["Sockets"].append((v, f))
        # narine allongée
        v, f = blob([0, 0, 0], 1.0, (0.16, 0.13, 0.45), 0.05, rng, subdiv=0)
        v = transform(v, rot_matrix_y(side * 0.3), [side * 0.42, 2.0, 5.5])
        out["Sockets"].append((v, f))
        # dents du haut : un gros croc + une rangée qui diminue
        for k in range(6):
            z = 5.3 - k * 0.85
            x = side * (0.55 + k * 0.1)
            L = 0.95 if k == 1 else 0.5 - k * 0.03
            r = 0.2 if k == 1 else 0.13
            v, f = tube([[x, 1.25, z], [x, 1.25 - L * 0.6, z - 0.05], [x * 0.97, 1.25 - L, z - 0.2]], [r, r * 0.6, 0], 4, tip=True)
            out["Bones"].append((v, f))
        # dents du bas (sur la mâchoire ouverte)
        for k in range(5):
            z = 4.9 - k * 0.95
            x = side * (0.45 + k * 0.1)
            p = np.array([x, 1.3, z])
            p = (rot_matrix_x(0.22) @ (p - [0, 1.1, -3.0])) + [0, 1.1, -3.0]
            L = 0.75 if k == 0 else 0.4
            v, f = tube([p, p + [0, L, 0.08]], [0.14, 0], 4, tip=True)
            out["Bones"].append((v, f))
    # crête : 3 petites épines sur le dessus
    for k, z in enumerate([-1.6, -2.6, -3.5]):
        v, f = tube([[0, 3.8, z], [0, 4.5 - k * 0.1, z - 0.6]], [0.22, 0], 4, tip=True)
        out["Horns"].append((v, f))
    return {p: [(np.array(v) * s, f) for v, f in items] for p, items in out.items()}


# ---------------- flamme low-poly en langues ----------------
def flame_tongue(H, W, rng, lean, sway, twist, sides=7):
    ts = [0.0, 0.12, 0.3, 0.5, 0.68, 0.84, 1.0]
    rprof = [0.8, 1.0, 0.92, 0.7, 0.45, 0.22, 0.0]
    rings = []
    for t, rp in zip(ts, rprof):
        cx = lean[0] * t * t * H + sway * math.sin(t * math.pi * 1.4) * W
        cz = lean[1] * t * t * H + sway * 0.6 * math.cos(t * math.pi * 1.2) * W - sway * 0.6 * W
        y = t * H
        if rp == 0:
            rings.append(np.array([[cx, y, cz]]))
            continue
        a, b = W * rp, W * rp * 0.6
        R = rot_matrix_y(twist * t)
        pts = [np.array([cx, y, cz]) + R @ [a * math.cos(2 * math.pi * i / sides), 0, -b * math.sin(2 * math.pi * i / sides)]
               for i in range(sides)]
        rings.append(np.array(pts))
    return loft(rings, cap_start=True, cap_end=False)


def flame_cluster(a, center, H, R, seed, outer=6, coals=True):
    """Ajoute à l'asset un feu complet : lit de braises, langues orange, cœur jaune."""
    rng = np.random.default_rng(seed)
    cx, cy, cz = center
    for part in ("Flame", "FlameCore") + (("Coals", "Embers") if coals else ()):
        a.part(part, *PART_STYLE[part])
    # grande langue centrale
    v, f = flame_tongue(H, R * 0.62, rng, (0.05, 0.0), 0.25, 1.2)
    a.add("Flame", transform(v, None, center), f)
    for k in range(outer):
        ang = 2 * math.pi * k / outer + rng.uniform(-0.3, 0.3)
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        h = H * rng.uniform(0.5, 0.82)
        v, f = flame_tongue(h, R * rng.uniform(0.32, 0.42), rng, (d[0] * 0.18, d[2] * 0.18), rng.uniform(-0.4, 0.4), rng.uniform(-1.5, 1.5))
        a.add("Flame", transform(v, rot_matrix_y(-ang), np.array(center) + d * R * 0.55), f)
    for k in range(3):
        ang = 2 * math.pi * k / 3 + 0.5
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        v, f = flame_tongue(H * rng.uniform(0.45, 0.6), R * 0.3, rng, (0, 0), rng.uniform(-0.3, 0.3), 0.8)
        a.add("FlameCore", transform(v, rot_matrix_y(ang), np.array(center) + d * R * 0.32 + [0, 0.02, 0]), f)
    if coals:
        v, f = blob([cx, cy, cz], R * 1.05, (1, 0.28, 1), 0.2, rng, subdiv=1)
        a.add("Coals", v, f)
        for k in range(9):
            ang = rng.uniform(0, 2 * math.pi)
            dist = R * rng.uniform(0.55, 0.95)
            v, f = blob([cx + dist * math.cos(ang), cy + R * 0.2, cz + dist * math.sin(ang)], R * rng.uniform(0.1, 0.17),
                        (1, 0.7, 1), 0.3, rng, subdiv=0)
            a.add("Embers", v, f)


def brazier_v2(name, seed):
    a = assets.brazier(name, seed)
    del a.parts["Flame"]
    flame_cluster(a, (0, 3.05, 0), 2.9, 1.25, seed)
    return a


# ---------------- crâne / squelette / portes avec le nouveau crâne ----------------
def _with_new_skull(builder, *args, skull_scale=1.0):
    old = assets2.skull_parts
    assets2.skull_parts = lambda rng, s=1.0: skull_v2(rng, s * skull_scale)
    try:
        a = builder(*args)
    finally:
        assets2.skull_parts = old
    for pname, p in a.parts.items():  # parties créées sans couleur (ex. Horns)
        if p["color"] is None or pname in PART_STYLE:
            p["color"], p["material"] = PART_STYLE.get(pname, (C["bone"], "SmoothPlastic"))
    return a


def gate_lair_v2(name, seed):
    a = _with_new_skull(assets2.lair_gate, name, seed, skull_scale=1.45)
    del a.parts["Flame"]
    for side in (-1, 1):
        flame_cluster(a, (side * 8.0, 12.6, 0.9), 3.0, 0.95, seed + side, outer=5, coals=False)
    return a


# ---------------- piliers de l'autel ----------------
def altar_pillar(name, h, seed, glyph_rows=4):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    a.part("Stone", C["stone"], "Slate")
    a.part("StoneDark", C["stone_dark"], "Slate")
    a.part("Claws", C["claw"], "Basalt")
    a.part("Runes", C["rune"], "Neon")
    a.part("Crystal", C["crystal"], "Neon")
    # socle à deux marches
    v, f = lathe([(3.0, 0), (3.0, 0.6), (2.5, 0.6), (2.5, 1.2), (0, 1.2)], 8, angle0=math.pi / 8, jitter=0.03, rng=rng)
    a.add("StoneDark", v, f)
    r0, r1 = 1.75, 1.35
    top = h - 2.2
    prof = [(2.05, 1.2), (2.05, 1.7), (r0, 2.0), (r1, top - 0.6), (1.85, top - 0.3), (1.85, top + 0.3), (1.45, top + 0.6), (0, top + 0.6)]
    v, f = lathe(prof, 8, angle0=math.pi / 8, jitter=0.02, rng=rng)
    a.add("Stone", v, f)
    # bandeau sombre au milieu
    ym = 2.0 + (top - 2.6) * 0.45
    rm = r0 + (r1 - r0) * (ym - 2.0) / (top - 0.6 - 2.0)
    v, f = lathe([(rm + 0.12, ym - 0.35), (rm + 0.12, ym + 0.35), (0, ym + 0.35)], 8, angle0=math.pi / 8)
    a.add("StoneDark", v, f)
    # runes lumineuses sur les 4 faces principales, colonne de glyphes
    shapes = [[(0, 0, 0.14, 1.1, 0), (0.25, 0.2, 0.12, 0.55, 0.7)],
              [(-0.2, 0, 0.12, 1.0, 0.3), (0.2, 0, 0.12, 1.0, -0.3)],
              [(0, 0, 0.14, 1.1, 0), (0, 0.3, 0.12, 0.6, 1.57), (0, -0.3, 0.12, 0.4, 1.57)],
              [(0, 0.15, 0.12, 0.8, 0.8), (0, -0.25, 0.12, 0.7, -0.8)]]
    for face in range(4):
        ang = face * math.pi / 2
        n = np.array([math.cos(ang), 0, -math.sin(ang)])
        side = np.array([n[2], 0, -n[0]])
        for row in range(glyph_rows):
            yc = 3.2 + row * (top - 4.4) / max(glyph_rows - 1, 1)
            if abs(yc - ym) < 0.7:
                continue
            r = r0 + (r1 - r0) * (yc - 2.0) / (top - 0.6 - 2.0)
            dist = r * math.cos(math.pi / 8)
            for dx, dy, w, hh, rot in shapes[(face + row) % 4]:
                bv, bf = box([0, 0, 0], [w, hh, 0.16])
                bv = transform(bv, rot_matrix_z(rot))
                basis = np.stack([side, [0, 1, 0], n], 1)
                bv = (np.array(bv) @ basis.T + n * dist + side * dx + [0, yc + dy, 0]).tolist()
                a.add("Runes", bv, bf)
    # 4 serres de dragon en pierre qui tiennent le cristal
    for k in range(4):
        ang = math.pi / 4 + k * math.pi / 2
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        y0 = top + 0.5
        pts = [d * 1.2 + [0, y0, 0], d * 1.85 + [0, y0 + 1.0, 0], d * 1.7 + [0, y0 + 2.3, 0],
               d * 1.05 + [0, y0 + 3.2, 0], d * 0.55 + [0, y0 + 3.4, 0]]
        v, f = tube(pts, [0.42, 0.38, 0.3, 0.18, 0], 5, tip=True)
        a.add("Claws", v, f)
        # articulation
        v, f = blob(list(d * 1.85 + [0, y0 + 1.0, 0]), 0.42, (1, 1, 1), 0.15, rng, subdiv=0)
        a.add("Claws", v, f)
    # cristal tenu par les serres (pièce séparée : on peut le faire tourner/flotter)
    v, f = lathe([(0, 0), (1.05, 1.5), (0.95, 3.8), (0, 5.6)], 6, angle0=0.2)
    v = transform(v, rot_matrix_z(0.08), [0, top + 1.0, 0])
    a.add("Crystal", v, f)
    # léger penchant : pierre ancienne
    lean = rot_matrix_z(rng.uniform(-0.03, 0.03)) @ rot_matrix_x(rng.uniform(-0.03, 0.03))
    for p in a.parts.values():
        p["v"] = transform(p["v"], lean)
    return a


def all_assets():
    return [
        brazier_v2("Brazier_DragonClaw_v2", 12),
        _with_new_skull(assets2.dragon_skull, "Dragon_Skull_v2", 22, 1.0),
        _with_new_skull(assets2.dragon_skeleton, "Dragon_Skeleton_v2", 21),
        gate_lair_v2("Gate_Lair_v2", 23),
        _with_new_skull(assets2.egg_road_arch, "Gate_EggRoad_v2", 24),
        altar_pillar("Altar_Pillar_A", 17.0, 41, 4),
        altar_pillar("Altar_Pillar_B", 14.0, 42, 3),
    ]
