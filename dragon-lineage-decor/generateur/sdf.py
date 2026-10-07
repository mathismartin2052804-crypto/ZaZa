# Sculpture par champs de distance (SDF) : formes organiques lisses, sans Blender.
# On combine des primitives (ellipsoïdes, tubes effilés) par union douce, puis
# marching cubes -> lissage -> décimation -> mesh à normales lisses.
import numpy as np


# ---------- primitives (P : tableau (..., 3)) ----------

def ellipsoid(P, c, r):
    p = (P - np.asarray(c, np.float32)) / np.asarray(r, np.float32)
    k0 = np.linalg.norm(p, axis=-1)
    k1 = np.linalg.norm(p / np.asarray(r, np.float32), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def sphere(P, c, r):
    return np.linalg.norm(P - np.asarray(c, np.float32), axis=-1) - r


def cone_seg(P, a, b, ra, rb):
    """Segment à rayon variable (ra en a, rb en b)."""
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    ba = b - a
    pa = P - a
    h = np.clip((pa @ ba) / (ba @ ba), 0.0, 1.0)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - (ra + (rb - ra) * h)


def chain(P, pts, radii, k=0.08):
    """Tube effilé le long d'une ligne brisée (segments unis en douceur)."""
    d = None
    for i in range(len(pts) - 1):
        s = cone_seg(P, pts[i], pts[i + 1], radii[i], radii[i + 1])
        d = s if d is None else smin(d, s, k)
    return d


def catmull(pts, n=6):
    """Courbe lisse passant par les points (pour cornes, queue, os d'aile)."""
    pts = [np.asarray(p, float) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def smooth_chain(P, pts, radii, n=5, k=0.05):
    """Tube courbe : points de contrôle + rayons interpolés."""
    curve = catmull(pts, n)
    r = np.interp(np.linspace(0, 1, len(curve)), np.linspace(0, 1, len(radii)), radii)
    return chain(P, curve, r, k)


# ---------- opérations ----------

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def union(*ds):
    d = ds[0]
    for x in ds[1:]:
        d = np.minimum(d, x)
    return d


# ---------- grille et maillage ----------

class Grid:
    def __init__(self, lo, hi, h):
        self.lo, self.h = np.asarray(lo, np.float32), float(h)
        n = np.ceil((np.asarray(hi) - self.lo) / h).astype(int) + 1
        axes = [self.lo[i] + np.arange(n[i], dtype=np.float32) * h for i in range(3)]
        X, Y, Z = np.meshgrid(*axes, indexing="ij")
        self.P = np.stack([X, Y, Z], -1)
        self.shape = tuple(n)


def to_mesh(grid, d, target_tris=None, smooth_iter=8, strict=True):
    """Champ de distance -> trimesh lissé et décimé, normales vers l'extérieur."""
    import trimesh
    from skimage.measure import marching_cubes
    import fast_simplification
    d = np.pad(d, 1, constant_values=1.0)  # ferme le maillage au bord de la grille
    v, f, _, _ = marching_cubes(d, 0.0, spacing=(grid.h,) * 3)
    v = v + grid.lo - grid.h
    m = trimesh.Trimesh(v, f, process=True)
    if m.volume < 0:
        m.invert()
    if smooth_iter:
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=smooth_iter)
    if target_tris and len(m.faces) > target_tris:
        full = m
        # la décimation crée parfois des « aiguilles » (triangles très longs) : on réessaie plus doucement
        for tgt in (target_tris, target_tris * 1.2, target_tris * 1.45, target_tris * 1.8, None):
            if tgt is None:
                m = full
                break
            v2, f2 = fast_simplification.simplify(full.vertices, full.faces, 1 - min(1.0, tgt / len(full.faces)))
            m = trimesh.Trimesh(v2, f2, process=True)
            # triangles isolés qui « volent » : on les retire
            m = trimesh.util.concatenate([c for c in m.split(only_watertight=False) if len(c.faces) >= (12 if strict else 4)])
            e = m.edges_unique_length
            if not strict or e.max() < 6 * np.median(e) + 0.15:
                break
        if m.volume < 0:
            m.invert()
    return m


def ellipsoid_r(P, c, r, R):
    """Ellipsoïde tourné : R = matrice 3x3 (colonnes = axes locaux)."""
    q = (P - np.asarray(c, np.float32)) @ np.asarray(R, np.float32)
    return ellipsoid(q, (0, 0, 0), r)


def look_basis(fwd, up=(0, 1, 0)):
    """Base dont l'axe Z local suit fwd (pour orienter une ellipsoïde)."""
    z = np.asarray(fwd, float); z /= np.linalg.norm(z)
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)
