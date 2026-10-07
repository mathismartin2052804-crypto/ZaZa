# Petite bibliothèque de génération de meshes low-poly à facettes (sans Blender).
# Repère Roblox : Y vers le haut, 1 unité = 1 stud.
import math
import numpy as np


class Asset:
    """Un objet 3D composé de plusieurs parties (une par couleur/matériau)."""

    def __init__(self, name):
        self.name = name
        self.parts = {}  # nom -> dict(color, material, verts list, faces list)

    def part(self, name, color, material="SmoothPlastic"):
        if name not in self.parts:
            self.parts[name] = {"color": color, "material": material, "v": [], "f": []}
        return self.parts[name]

    def add(self, part_name, verts, faces, color=None, material="SmoothPlastic"):
        p = self.part(part_name, color, material)
        base = len(p["v"])
        p["v"].extend([tuple(map(float, v)) for v in verts])
        p["f"].extend([tuple(i + base for i in f) for f in faces])

    def tri_count(self):
        return sum(len(p["f"]) for p in self.parts.values())

    def bounds(self):
        allv = np.array([v for p in self.parts.values() for v in p["v"]])
        return allv.min(0), allv.max(0)


# ---------- construction de base ----------

def loft(rings, cap_start=True, cap_end=True):
    """Relie une suite d'anneaux (listes de points 3D de même taille, ou un point seul = pointe)."""
    verts, faces, idx = [], [], []
    for r in rings:
        r = np.atleast_2d(r)
        idx.append(list(range(len(verts), len(verts) + len(r))))
        verts.extend(r.tolist())
    for a, b in zip(idx[:-1], idx[1:]):
        if len(a) > 1 and len(b) > 1:
            n = len(a)
            for i in range(n):
                j = (i + 1) % n
                faces.append((a[i], a[j], b[j]))
                faces.append((a[i], b[j], b[i]))
        elif len(b) == 1:  # pointe en haut
            n = len(a)
            for i in range(n):
                faces.append((a[i], a[(i + 1) % n], b[0]))
        else:  # pointe en bas
            n = len(b)
            for i in range(n):
                faces.append((a[0], b[(i + 1) % n], b[i]))
    if cap_start and len(idx[0]) > 2:
        r = idx[0]
        c = len(verts)
        verts.append(np.mean([verts[i] for i in r], 0).tolist())
        for i in range(len(r)):
            faces.append((c, r[(i + 1) % len(r)], r[i]))
    if cap_end and len(idx[-1]) > 2:
        r = idx[-1]
        c = len(verts)
        verts.append(np.mean([verts[i] for i in r], 0).tolist())
        for i in range(len(r)):
            faces.append((c, r[i], r[(i + 1) % len(r)]))
    return verts, faces


def ring(center, radius, sides, angle0=0.0, axis_u=(1, 0, 0), axis_v=(0, 0, 1), jitter=0.0, rng=None):
    """Anneau de points dans le plan (u, v). L'ordre suit le sens de u vers v."""
    center, u, v = map(np.asarray, (center, axis_u, axis_v))
    pts = []
    for i in range(sides):
        a = angle0 + 2 * math.pi * i / sides
        r = radius * (1 + (rng.uniform(-jitter, jitter) if jitter and rng is not None else 0))
        pts.append(center + r * (math.cos(a) * u + math.sin(a) * v))
    return np.array(pts)


def lathe(profile, sides, twist=0.0, jitter=0.0, rng=None, angle0=0.0):
    """Révolution d'un profil [(rayon, y)] autour de Y. Rayon 0 = pointe."""
    rings = []
    for k, (r, y) in enumerate(profile):
        if r <= 1e-6:
            rings.append(np.array([[0.0, y, 0.0]]))
        else:
            # u=X, v=-Z pour que les faces soient orientées vers l'extérieur
            rings.append(ring((0, y, 0), r, sides, angle0 + twist * k, (1, 0, 0), (0, 0, -1), jitter, rng))
    return loft(rings)


def _frame(d):
    d = d / np.linalg.norm(d)
    ref = np.array([0, 1, 0]) if abs(d[1]) < 0.9 else np.array([1, 0, 0])
    u = np.cross(d, ref)
    u /= np.linalg.norm(u)
    v = np.cross(u, d)
    return u, v


def tube(points, radii, sides, tip=False, jitter=0.0, rng=None, angle0=0.0):
    """Tube effilé le long d'une ligne brisée. tip=True : se termine en pointe."""
    points = [np.asarray(p, float) for p in points]
    rings = []
    n = len(points)
    for i, p in enumerate(points):
        if tip and i == n - 1:
            rings.append(p[None, :])
            continue
        d = points[min(i + 1, n - 1)] - points[max(i - 1, 0)]
        u, v = _frame(d)
        # ordre u -> -v pour garder les normales vers l'extérieur
        rings.append(ring(p, radii[i], sides, angle0, u, -v, jitter, rng))
    return loft(rings)


def icosphere(subdiv=1):
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
         (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11),
         (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    v = [np.array(p, float) / np.linalg.norm(p) for p in v]
    for _ in range(subdiv):
        cache, nf = {}, []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = v[a] + v[b]
                v.append(m / np.linalg.norm(m))
                cache[k] = len(v) - 1
            return cache[k]

        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    return np.array(v), f


def blob(center, radius, scale=(1, 1, 1), jitter=0.15, rng=None, subdiv=1, flat_bottom=None):
    v, f = icosphere(subdiv)
    out = []
    for p in v:
        r = 1 + (rng.uniform(-jitter, jitter) if rng is not None else 0)
        q = p * r
        if flat_bottom is not None:
            q[1] = max(q[1], flat_bottom)
        out.append(np.asarray(center) + q * radius * np.asarray(scale))
    return out, f


def box(center, size, rot_y=0.0):
    sx, sy, sz = np.asarray(size) / 2
    corners = np.array([[x, y, z] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)])
    faces = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
             (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return (np.asarray(corners) @ rot_matrix_y(rot_y).T + np.asarray(center)).tolist(), faces


# ---------- transformations ----------

def rot_matrix_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_matrix_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_matrix_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def transform(verts, mat=None, offset=(0, 0, 0), shear_xy=0.0):
    v = np.asarray(verts, float)
    if shear_xy:
        v = v.copy()
        v[:, 0] += shear_xy * v[:, 1] ** 2
    if mat is not None:
        v = v @ np.asarray(mat).T
    return (v + np.asarray(offset)).tolist()


# ---------- export ----------

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def export_obj(asset, path_obj):
    """OBJ + MTL, normales par face (rendu à facettes), une 'o' par partie."""
    import os
    base = os.path.splitext(os.path.basename(path_obj))[0]
    mtl_path = os.path.splitext(path_obj)[0] + ".mtl"
    lines = [f"# {asset.name} - Dragon Lineage (decor de Will)", "# Y vers le haut, 1 unite = 1 stud",
             f"mtllib {base}.mtl"]
    mtl = []
    vo = no = 0
    for pname, p in asset.parts.items():
        v = np.array(p["v"])
        lines.append(f"o {pname}")
        lines.append(f"usemtl {asset.name}_{pname}")
        lines += [f"v {x:.4f} {y:.4f} {z:.4f}" for x, y, z in v]
        normals = []
        for a, b, c in p["f"]:
            n = np.cross(v[b] - v[a], v[c] - v[a])
            ln = np.linalg.norm(n)
            normals.append(n / ln if ln > 1e-12 else np.array([0, 1, 0]))
        lines += [f"vn {x:.4f} {y:.4f} {z:.4f}" for x, y, z in normals]
        for k, (a, b, c) in enumerate(p["f"]):
            ni = no + k + 1
            lines.append(f"f {a + vo + 1}//{ni} {b + vo + 1}//{ni} {c + vo + 1}//{ni}")
        vo += len(v)
        no += len(normals)
        r, g, b_ = hex_to_rgb(p["color"])
        mtl += [f"newmtl {asset.name}_{pname}", f"Kd {r:.4f} {g:.4f} {b_:.4f}", "Ka 0 0 0", "Ks 0 0 0", "d 1", ""]
    with open(path_obj, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(mtl_path, "w") as fh:
        fh.write("\n".join(mtl))


def export_glb(asset, path_glb):
    """GLB : un nœud par partie (nommé), couleur en matériau PBR, sommets non partagés = rendu à facettes."""
    import trimesh
    from trimesh.visual.material import PBRMaterial
    scene = trimesh.Scene()
    for pname, p in asset.parts.items():
        v = np.array(p["v"], float)
        f = np.array(p["f"], int)
        fv = v[f].reshape(-1, 3)
        faces = np.arange(len(fv)).reshape(-1, 3)
        rgb = list(hex_to_rgb(p["color"]))
        neon = p["material"] == "Neon"
        mat = PBRMaterial(name=f"{asset.name}_{pname}", baseColorFactor=rgb + [1.0], metallicFactor=0.0,
                          roughnessFactor=0.9, emissiveFactor=rgb if neon else None)
        m = trimesh.Trimesh(fv, faces, process=False)
        m.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(m, node_name=pname, geom_name=pname)
    with open(path_glb, "wb") as fh:
        fh.write(scene.export(file_type="glb", include_normals=True))
