# Petit moteur de rendu logiciel (z-buffer, ombrage lisse, lueur Neon) pour les aperçus,
# + mise en pose des morceaux autour de leurs pivots (preuve que le découpage s'anime).
import numpy as np
from PIL import Image, ImageFilter


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def rot(ex=0, ey=0, ez=0):
    ex, ey, ez = np.radians([ex, ey, ez])
    cx, sx, cy, sy, cz, sz = np.cos(ex), np.sin(ex), np.cos(ey), np.sin(ey), np.cos(ez), np.sin(ez)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def pose_transforms(model, pose):
    """pose : {morceau: (rx, ry, rz) en degrés, autour de son pivot}. Renvoie {morceau: (R, t)}."""
    T = {}

    def get(name):
        if name in T:
            return T[name]
        seg = model[name]
        p = np.array(seg["pivot"])
        R = rot(*pose.get(name, (0, 0, 0)))
        local = (R, p - R @ p)
        if seg["parent"] is None:
            T[name] = local
        else:
            PR, Pt = get(seg["parent"])
            T[name] = (PR @ local[0], PR @ local[1] + Pt)
        return T[name]

    for n in model:
        get(n)
    return T


def gather(model, palette, pose=None):
    """Liste (sommets, normales, faces, couleur, émissif) pour tout le modèle posé."""
    T = pose_transforms(model, pose or {})
    out = []
    for name, seg in model.items():
        R, t = T[name]
        for layer, m in seg["layers"].items():
            v = m.vertices @ R.T + t
            n = m.vertex_normals @ R.T
            out.append((v, n, np.asarray(m.faces), hex_rgb(palette[layer if layer != "skin" else "skin"]),
                        layer == "eye"))
    return out


def render(items, eye, target, size=(900, 640), fov=32, ss=2, bg=("#1d2230", "#0c0e14")):
    W, H = size[0] * ss, size[1] * ss
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    foc = 0.5 * H / np.tan(np.radians(fov) / 2)
    zbuf = np.full((H, W), np.inf)
    nbuf = np.zeros((H, W, 3))
    cbuf = np.zeros((H, W, 3))
    ebuf = np.zeros((H, W), bool)
    pbuf = np.zeros((H, W, 3))
    for v, n, faces, col, emissive in items:
        rel = v - eye
        cx, cy, cz = rel @ r, rel @ u, rel @ f
        sx = W / 2 + foc * cx / cz
        sy = H / 2 - foc * cy / cz
        for a, b, c in faces:
            xs, ys = sx[[a, b, c]], sy[[a, b, c]]
            x0, x1 = int(max(xs.min(), 0)), int(min(np.ceil(xs.max()), W - 1))
            y0, y1 = int(max(ys.min(), 0)), int(min(np.ceil(ys.max()), H - 1))
            if x1 < x0 or y1 < y0:
                continue
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not m.any():
                continue
            iz = w0 / cz[a] + w1 / cz[b] + w2 / cz[c]
            z = 1 / iz
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            m &= z < zb
            if not m.any():
                continue
            zb[m] = z[m]
            nn = (w0[..., None] * n[a] / cz[a] + w1[..., None] * n[b] / cz[b] + w2[..., None] * n[c] / cz[c]) * z[..., None]
            pp = (w0[..., None] * v[a] / cz[a] + w1[..., None] * v[b] / cz[b] + w2[..., None] * v[c] / cz[c]) * z[..., None]
            nbuf[y0:y1 + 1, x0:x1 + 1][m] = nn[m]
            pbuf[y0:y1 + 1, x0:x1 + 1][m] = pp[m]
            cbuf[y0:y1 + 1, x0:x1 + 1][m] = col
            ebuf[y0:y1 + 1, x0:x1 + 1][m] = emissive
    hit = np.isfinite(zbuf)
    N = nbuf / np.maximum(np.linalg.norm(nbuf, axis=-1, keepdims=True), 1e-9)
    V = eye - pbuf
    V /= np.maximum(np.linalg.norm(V, axis=-1, keepdims=True), 1e-9)
    # éclairage façon jeu stylisé : soleil chaud + ciel froid + contour
    key = np.array([-0.45, 0.8, -0.4]); key /= np.linalg.norm(key)
    fill = np.array([0.6, 0.3, 0.7]); fill /= np.linalg.norm(fill)
    ndl = np.clip(N @ key, 0, 1)
    wrap = np.clip((N @ key + 0.35) / 1.35, 0, 1)
    diff = 0.82 * (0.55 * wrap + 0.45 * ndl)[..., None] * np.array([1.0, 0.95, 0.85])
    sky = 0.34 * (0.5 + 0.5 * N[..., 1])[..., None] * np.array([0.85, 0.9, 1.0])
    fl = 0.16 * np.clip(N @ fill, 0, 1)[..., None] * np.array([0.7, 0.8, 1.0])
    Hh = V + key; Hh /= np.maximum(np.linalg.norm(Hh, axis=-1, keepdims=True), 1e-9)
    spec = 0.22 * np.clip((N * Hh).sum(-1), 0, 1) ** 28
    rim = 0.35 * np.clip(1 - (N * V).sum(-1), 0, 1) ** 3
    # occlusion grossière : plus sombre près du sol et dans les creux bas
    ao = np.clip(0.6 + pbuf[..., 1] / 6, 0.6, 1.0)[..., None]
    shade = cbuf * (diff + sky + fl) * ao + spec[..., None] + rim[..., None] * np.array([1.0, 0.85, 0.7]) * cbuf * 1.5
    shade = np.where(ebuf[..., None], cbuf * 1.15, shade)
    # fond dégradé + sol
    t = np.linspace(0, 1, H)[:, None, None]
    img = hex_rgb(bg[0]) * (1 - t) + hex_rgb(bg[1]) * t
    img = np.broadcast_to(img, (H, W, 3)).copy()
    img[hit] = shade[hit]
    # lueur des parties Neon
    glow = np.zeros((H, W, 3))
    glow[ebuf] = cbuf[ebuf]
    gimg = Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6 * ss))
    img = img + np.asarray(gimg) / 255 * 0.9
    out = Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.1) * 255).astype(np.uint8))
    return out.resize(size, Image.LANCZOS)


def ground_shadow(items, eye, target, size, fov=32):
    """Ombre portée douce au sol (projection verticale) : renvoyée comme masque à multiplier."""
    pts = np.concatenate([v for v, *_ in items])
    pts = pts[::7].copy()
    pts[:, 1] = 0.0
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    W, H = size
    foc = 0.5 * H / np.tan(np.radians(fov) / 2)
    rel = pts - eye
    cz = rel @ f
    sx = (W / 2 + foc * (rel @ r) / cz).astype(int)
    sy = (H / 2 - foc * (rel @ u) / cz).astype(int)
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    mask = np.zeros((H, W), np.uint8)
    mask[sy[ok], sx[ok]] = 255
    m = Image.fromarray(mask).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
    return 1 - 0.55 * np.asarray(m) / 255
