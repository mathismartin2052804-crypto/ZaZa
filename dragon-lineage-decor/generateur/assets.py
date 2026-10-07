# Définition des éléments de décor « terre de dragons » (sombre, low-poly à facettes).
import math
import numpy as np
from meshlib import (Asset, lathe, tube, blob, box, loft, ring, transform,
                     rot_matrix_x, rot_matrix_y, rot_matrix_z)

# Palette sombre (modifiable ensuite dans Studio : chaque partie est une MeshPart séparée)
C = {
    "pine": "#1E3529", "pine_alt": "#24402F", "bark": "#3A2A22", "charred": "#1C1917",
    "ember": "#FF5A1F", "leaf": "#33482B", "leaf_alt": "#3D4F2A", "rock": "#4E4E55",
    "moss": "#36502C", "fern": "#2C4A2C", "stone": "#45454C", "claw": "#2A2A2F",
    "flame": "#FF7A1A", "iron": "#26262A", "crystal": "#6FE3FF", "rune": "#6FE3FF",
    "nest": "#5A4632", "wood": "#4A3426",
}


# ---------------- 1. Sapins à étages ----------------
def pine(name, height, seed, lean=0.0, tiers=4):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    trunk_h = height * 0.32
    tv, tf = lathe([(height * 0.045, 0), (height * 0.035, trunk_h * 0.6), (height * 0.025, trunk_h + height * 0.2)],
                   6, jitter=0.08, rng=rng)
    a.add("Trunk", tv, tf, C["bark"], "Wood")
    y = trunk_h
    span = height - trunk_h
    for t in range(tiers):
        frac = t / tiers
        R = height * 0.3 * (1 - frac * 0.62)
        h = span / tiers * 1.55
        n = 8
        pts = []
        for i in range(n):
            ang = 2 * math.pi * i / n + rng.uniform(-0.12, 0.12)
            r = R * (1.0 if i % 2 == 0 else 0.78) * rng.uniform(0.92, 1.06)
            droop = -R * 0.18 if i % 2 == 0 else -R * 0.05
            pts.append([r * math.cos(ang), y + droop, -r * math.sin(ang)])
        apex = [rng.uniform(-0.2, 0.2), y + h, rng.uniform(-0.2, 0.2)]
        under = [0, y + h * 0.18, 0]
        verts, faces = loft([np.array(pts), np.array([apex])], cap_start=False, cap_end=False)
        # dessous légèrement creusé (visible depuis le bas)
        c = len(verts)
        verts.append(under)
        for i in range(n):
            faces.append((c, (i + 1) % n, i))
        verts = transform(verts, rot_matrix_y(rng.uniform(0, math.pi)))
        a.add("Foliage", verts, faces, C["pine"] if t % 2 == 0 else C["pine_alt"], "Grass")
        y += span / tiers * 0.82
    if lean:
        rot = rot_matrix_z(lean) @ rot_matrix_x(lean * 0.4)
        for p in a.parts.values():
            p["v"] = transform(p["v"], rot)
    return a


def burnt_pine(name, height, seed):
    """Sapin calciné par un dragon : tronc noir et branches cassées, braises sur la cassure."""
    rng = np.random.default_rng(seed)
    a = Asset(name)
    pts = [[0, 0, 0], [0.2, height * 0.35, 0.1], [-0.1, height * 0.7, 0], [0.3, height, -0.2]]
    v, f = tube(pts, [height * 0.075, height * 0.055, height * 0.035, height * 0.015], 6, tip=True, jitter=0.1, rng=rng)
    a.add("Wood", v, f, C["charred"], "Slate")
    for k in range(6):
        y = height * rng.uniform(0.3, 0.85)
        ang = rng.uniform(0, 2 * math.pi)
        L = height * rng.uniform(0.22, 0.35) * (1.2 - y / height)
        d = np.array([math.cos(ang), rng.uniform(-0.35, 0.1), math.sin(ang)])
        start = np.array([0, y, 0])
        v, f = tube([start, start + d * L * 0.6, start + d * L + [0, -L * 0.15, 0]],
                    [height * 0.022, height * 0.015, 0], 4, tip=True, rng=rng)
        a.add("Wood", v, f)
    # braises au sommet cassé
    v, f = blob([0.3, height * 0.98, -0.2], height * 0.03, (1, 0.6, 1), 0.3, rng, subdiv=0)
    a.add("Embers", v, f, C["ember"], "Neon")
    return a


# ---------------- 2. Arbres feuillus en nuage ----------------
def leafy(name, height, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    H = height * 0.55
    bend = rng.uniform(0.6, 1.2) * height * 0.06
    pts = [[0, 0, 0], [bend * 0.3, H * 0.33, 0], [-bend * 0.2, H * 0.66, bend * 0.3], [bend, H, 0]]
    r0 = height * 0.06
    v, f = tube(pts, [r0, r0 * 0.75, r0 * 0.62, r0 * 0.5], 6, jitter=0.08, rng=rng)
    a.add("Trunk", v, f, C["bark"], "Wood")
    for k in range(3):  # racines
        ang = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        v, f = tube([d * r0 * 0.3 + [0, r0 * 1.6, 0], d * r0 * 1.6 + [0, r0 * 0.5, 0], d * r0 * 2.6 + [0, -0.1, 0]],
                    [r0 * 0.5, r0 * 0.35, 0], 4, tip=True)
        a.add("Trunk", v, f)
    for k in range(2):  # deux grosses branches qui partent dans le feuillage
        ang = rng.uniform(0, 2 * math.pi)
        d = np.array([math.cos(ang), 0.9, math.sin(ang)])
        s = np.array([bend * 0.5, H * 0.75, 0])
        v, f = tube([s, s + d * height * 0.15], [r0 * 0.4, r0 * 0.15], 5)
        a.add("Trunk", v, f)
    R = height * 0.3
    v, f = blob([bend, H + R * 0.45, 0], R, (1.15, 0.72, 1.0), 0.22, rng, subdiv=1, flat_bottom=-0.45)
    v = transform(np.array(v) - [bend, H, 0], rot_matrix_y(rng.uniform(0, 6.28)), [bend, H, 0])
    a.add("Foliage", v, f, C["leaf"], "Grass")
    return a


# ---------------- 3. Arbre-repère : vieil arbre mort avec nid de dragon ----------------
def landmark(name, height, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    pts, radii = [], []
    for k in range(7):
        t = k / 6
        pts.append([math.sin(t * 3.0) * height * 0.06, t * height * 0.75, math.cos(t * 2.2) * height * 0.04 - height * 0.04])
        radii.append(height * (0.075 * (1 - t) + 0.025))
    v, f = tube(pts, radii, 7, jitter=0.1, rng=rng)
    a.add("Wood", v, f, C["wood"], "Wood")
    top = np.array(pts[-1])
    for k in range(5):  # racines
        ang = 2 * math.pi * k / 5 + rng.uniform(-0.2, 0.2)
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        v, f = tube([d * height * 0.03 + [0, height * 0.08, 0], d * height * 0.1 + [0, height * 0.02, 0],
                     d * height * 0.17 + [0, -0.2, 0]], [height * 0.035, height * 0.022, 0], 5, tip=True)
        a.add("Wood", v, f)
    branch_tips = []
    for k in range(5):  # grosses branches tordues
        t = rng.uniform(0.45, 0.95)
        i = int(t * 6)
        s = np.array(pts[i])
        ang = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
        d = np.array([math.cos(ang), rng.uniform(0.3, 0.8), math.sin(ang)])
        d /= np.linalg.norm(d)
        L = height * rng.uniform(0.32, 0.45)
        mid = s + d * L * 0.5 + [0, -L * 0.1, 0]
        end = s + d * L + [0, L * 0.15, 0]
        v, f = tube([s, mid, end], [radii[i] * 0.55, radii[i] * 0.35, 0], 5, tip=True)
        a.add("Wood", v, f)
        # petite branche secondaire
        d2 = d + [rng.uniform(-0.6, 0.6), 0.5, rng.uniform(-0.6, 0.6)]
        d2 /= np.linalg.norm(d2)
        v, f = tube([mid, mid + d2 * L * 0.4], [radii[i] * 0.22, 0], 4, tip=True)
        a.add("Wood", v, f)
        branch_tips.append(end)
    # nid de dragon au sommet : anneau de branchages
    nest_c = top + [0, height * 0.02, 0]
    R, rr = height * 0.13, height * 0.04
    rings = []
    for i in range(10):
        ang = 2 * math.pi * i / 10
        cdir = np.array([math.cos(ang), 0, -math.sin(ang)])
        c = nest_c + cdir * R
        rings.append(ring(c, rr * rng.uniform(0.85, 1.2), 5, rng.uniform(0, 1), cdir, (0, 1, 0)))
    verts, faces, idx = [], [], []
    for r in rings:
        idx.append(list(range(len(verts), len(verts) + 5)))
        verts += r.tolist()
    for k in range(10):
        A, B = idx[k], idx[(k + 1) % 10]
        for i in range(5):
            j = (i + 1) % 5
            faces += [(A[i], B[j], A[j]), (A[i], B[i], B[j])]
    verts = (np.array(verts) * [1, 1, 1]).tolist()
    a.add("Nest", verts, faces, C["nest"], "Wood")
    v, f = lathe([(R * 0.95, nest_c[1] - rr * 0.6), (0, nest_c[1] - rr * 0.8)], 8)
    v = transform(v, None, [nest_c[0], 0, nest_c[2]])
    a.add("Nest", v, [(x, z, y) for x, y, z in f])  # fond du nid, vu du dessus
    return a


# ---------------- 4. Buissons, fougères, rochers moussus ----------------
def fern(name, size, seed, blades=9):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    for k in range(blades):
        ang = 2 * math.pi * k / blades + rng.uniform(-0.25, 0.25)
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        side = np.array([-d[2], 0, d[0]])
        L = size * rng.uniform(0.8, 1.1)
        up = rng.uniform(0.7, 1.1)
        rings = []
        for s in range(5):
            t = s / 4
            c = d * L * t + np.array([0, L * up * math.sin(t * math.pi * 0.75), 0])
            w = size * 0.16 * math.sin(math.pi * min(t * 1.15, 1)) + 0.02
            th = size * 0.035
            if s == 4:
                rings.append(np.array([c]))
            else:
                rings.append(np.array([c + side * w, c + [0, th, 0], c - side * w, c - [0, th, 0]]))
        v, f = loft(rings, cap_start=True, cap_end=False)
        f = [(x, z, y) for x, y, z in f]  # ordre inversé : faces vers l'extérieur
        a.add("Leaves", v, f, C["fern"], "Grass")
    return a


def spiky_bush(name, size, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    v, f = blob([0, size * 0.25, 0], size * 0.4, (1.2, 0.7, 1.2), 0.25, rng, subdiv=0, flat_bottom=-0.3)
    a.add("Leaves", v, f, C["leaf_alt"], "Grass")
    for k in range(14):
        ang = rng.uniform(0, 2 * math.pi)
        el = rng.uniform(0.25, 1.3)
        d = np.array([math.cos(ang) * math.cos(el), math.sin(el), math.sin(ang) * math.cos(el)])
        base = np.array([0, size * 0.25, 0]) + d * size * 0.2
        L = size * rng.uniform(0.55, 0.8)
        v, f = tube([base, base + d * L], [size * 0.09, 0], 4, tip=True, angle0=rng.uniform(0, 1))
        a.add("Leaves", v, f, C["leaf_alt"] if k % 2 else C["leaf"])
    return a


def mossy_rock(name, size, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    v, f = blob([0, size * 0.32, 0], size * 0.55, (1.2, 0.65, 0.95), 0.25, rng, subdiv=1, flat_bottom=-0.55)
    a.add("Rock", v, f, C["rock"], "Slate")
    # mousse : couche posée sur le dessus (on garde les sommets hauts du rocher et on la gonfle un peu)
    vv = np.array(v)
    top = vv[:, 1] > size * 0.42
    keep = [tri for tri in f if all(top[i] for i in tri)]
    used = sorted({i for tri in keep for i in tri})
    remap = {o: n for n, o in enumerate(used)}
    c = vv[used].mean(0)
    mv = [(c + (vv[i] - c) * 1.04 + [0, size * 0.03, 0]).tolist() for i in used]
    mf = [tuple(remap[i] for i in tri) for tri in keep]
    # bord de la mousse fermé vers le bas pour éviter qu'elle paraisse en papier
    a.add("Moss", mv, mf, C["moss"], "Grass")
    return a


# ---------------- 5. Brasero en pierre sur serres de dragon ----------------
def brazier(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    prof = [(1.25, 0), (1.25, 0.35), (0.85, 0.55), (0.55, 1.1), (0.5, 2.1), (0.75, 2.35),
            (1.7, 2.95), (1.95, 3.35), (1.75, 3.45), (1.35, 3.15), (0, 3.0)]
    v, f = lathe(prof, 8, jitter=0.03, rng=rng)
    a.add("Stone", v, f, C["stone"], "Slate")
    for k in range(4):  # serres de dragon qui agrippent le socle
        ang = 2 * math.pi * k / 4 + math.pi / 4
        d = np.array([math.cos(ang), 0, math.sin(ang)])
        pts = [d * 0.7 + [0, 1.0, 0], d * 1.25 + [0, 0.7, 0], d * 1.65 + [0, 0.25, 0], d * 1.8 + [0, -0.05, 0]]
        v, f = tube(pts, [0.28, 0.24, 0.15, 0], 5, tip=True)
        a.add("Claws", v, f, C["claw"], "Basalt")
    # flamme low-poly : 3 pointes torsadées
    for k, (h, r, off) in enumerate([(2.4, 0.8, (0, 0)), (1.7, 0.55, (0.55, 0.3)), (1.5, 0.5, (-0.45, -0.4))]):
        pv = [(r, 0), (r * 0.85, h * 0.3), (r * 0.5, h * 0.65), (0, h)]
        v, f = lathe(pv, 5, twist=0.45, angle0=k)
        v = transform(v, rot_matrix_y(k * 2.1), [off[0], 2.95, off[1]], shear_xy=0.03 * (1 if k % 2 else -1))
        a.add("Flame", v, f, C["flame"], "Neon")
    return a


# ---------------- 6. Lanterne de route ----------------
def lantern(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    v, f = lathe([(0.5, 0), (0.42, 4.5), (0.34, 9.2)], 4, angle0=math.pi / 4, jitter=0.04, rng=rng)
    a.add("Post", v, f, C["wood"], "Wood")
    v, f = box([1.0, 8.75, 0], [2.6, 0.38, 0.38])
    a.add("Post", v, f)
    v, f = box([0.55, 8.15, 0], [0.25, 1.3, 0.25], 0)  # jambe de force
    v = transform(np.array(v) - [0.55, 8.15, 0], rot_matrix_z(-0.75), [0.75, 8.15, 0])
    a.add("Post", v, f)
    # cage en fer suspendue
    cx, top = 2.0, 8.55
    v, f = box([cx, top - 0.25, 0], [0.1, 0.5, 0.1])
    a.add("Iron", v, f, C["iron"], "Metal")
    v, f = lathe([(0.75, top - 1.05), (0.75, top - 0.95), (0, top - 0.45)], 4, angle0=math.pi / 4)
    a.add("Iron", transform(v, None, [cx, 0, 0]), f)
    v, f = lathe([(0.7, top - 2.85), (0.7, top - 2.7), (0, top - 2.7)], 4, angle0=math.pi / 4)
    a.add("Iron", transform(v, None, [cx, 0, 0]), f)
    for k in range(4):
        ang = math.pi / 4 + k * math.pi / 2
        v, f = box([cx + 0.6 * math.cos(ang), top - 1.85, 0.6 * math.sin(ang)], [0.1, 1.75, 0.1])
        a.add("Iron", v, f)
    v, f = lathe([(0, top - 2.6), (0.32, top - 2.0), (0.26, top - 1.6), (0, top - 1.1)], 6)
    a.add("Crystal", transform(v, None, [cx, 0, 0]), f, C["crystal"], "Neon")
    return a


# ---------------- 7. Pilier runique de l'autel ----------------
def pillar(name, seed):
    rng = np.random.default_rng(seed)
    a = Asset(name)
    prof = [(2.2, 0), (2.2, 1.0), (1.7, 1.35), (1.5, 1.35), (1.3, 12.0), (1.85, 12.5), (1.85, 13.3), (1.1, 13.7)]
    v, f = lathe(prof, 8, angle0=math.pi / 8)
    a.add("Stone", v, f, C["stone"], "Slate")
    # runes en relief sur 4 faces (petites barres lumineuses)
    glyphs = [
        [(0, 0, 0.12, 1.6, 0), (0.3, 0.4, 0.1, 0.8, 0.6), (-0.3, -0.3, 0.1, 0.7, -0.6)],
        [(0, 0, 0.12, 1.6, 0), (0, 0.5, 0.1, 0.8, 1.57)],
        [(-0.25, 0, 0.1, 1.4, 0.35), (0.25, 0, 0.1, 1.4, -0.35), (0, -0.2, 0.1, 0.6, 1.57)],
        [(0, 0.3, 0.1, 1.0, 0), (0, -0.4, 0.1, 0.9, 0.8)],
    ]
    for k, glyph in enumerate(glyphs):
        for row, yc in enumerate((4.0, 8.0)):
            ang = k * math.pi / 2 + (math.pi / 4 if row else 0)
            r = 1.5 + (1.3 - 1.5) * (yc - 1.35) / (12.0 - 1.35)
            dist = r * math.cos(math.pi / 8)
            n = np.array([math.cos(ang), 0, -math.sin(ang)])
            side = np.array([n[2], 0, -n[0]])
            for (dx, dy, w, h, rot) in glyphs[(k + row) % 4]:
                bv, bf = box([0, 0, 0], [w, h, 0.18])
                bv = transform(bv, rot_matrix_z(rot))
                basis = np.stack([side, [0, 1, 0], n], 1)
                bv = (np.array(bv) @ basis.T + n * dist + side * dx + [0, yc + dy, 0]).tolist()
                a.add("Runes", bv, bf, C["rune"], "Neon")
    v, f = lathe([(0, 0), (0.75, 1.3), (0.6, 2.8), (0, 4.2)], 6, angle0=0.3)
    v = transform(v, rot_matrix_z(0.12) @ rot_matrix_x(-0.08), [0, 13.0, 0])
    a.add("Crystal", v, f, C["crystal"], "Neon")
    return a


def all_assets():
    return [
        pine("Pine_Small", 16, 1),
        pine("Pine_Medium", 24, 2),
        pine("Pine_Tall", 34, 3, tiers=5),
        pine("Pine_Leaning", 24, 4, lean=0.14),
        burnt_pine("Pine_Burnt", 20, 5),
        leafy("Tree_Leafy_A", 20, 6),
        leafy("Tree_Leafy_B", 17, 7),
        landmark("Tree_Landmark_Nest", 42, 8),
        fern("Fern", 3.2, 9),
        spiky_bush("Bush_Spiky", 4.0, 10),
        mossy_rock("Rock_Mossy", 5.0, 11),
        brazier("Brazier_DragonClaw", 12),
        lantern("Lantern_Road", 13),
        pillar("Pillar_Runic", 14),
    ]
