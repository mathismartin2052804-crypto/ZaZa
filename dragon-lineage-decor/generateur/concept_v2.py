# Planche de concept v2 (2D, low-poly à facettes) : corps entier, 3 têtes au choix, traits par lignée.
# Sert à valider la direction avant de modifier dragon_lowpoly.py. Sortie : ../concept-dragon-v2.png
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.spatial import Delaunay
from matplotlib.path import Path

SS = 2                      # suréchantillonnage
W, H = 1900, 1320
rng = np.random.default_rng(7)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

LIGNEES = {
    "Feu":   dict(body="#c8281e", belly="#e0a030", dark="#7a1410", horn="#3a2a24", memb="#a8461c", neon="#ffb020", spike="#ff8a1c"),
    "Glace": dict(body="#3d78c0", belly="#c8d8e8", dark="#1f3f70", horn="#eef4fa", memb="#5a8fb8", neon="#8ff0ff", spike="#bff4ff"),
    "Forêt": dict(body="#3d8a32", belly="#8a6a3a", dark="#1f4a1a", horn="#6a4a2a", memb="#5f9a2a", neon="#d8ff40", spike="#a8d838"),
    "Ombre": dict(body="#2c2238", belly="#46365a", dark="#160f20", horn="#d8d0e0", memb="#3a2448", neon="#e040ff", spike="#b030e0"),
}


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


# ---------- moteur de facettes ----------
class Canvas:
    def __init__(self):
        self.img = Image.new("RGB", (W * SS, H * SS))
        self.d = ImageDraw.Draw(self.img)
        self.glow = Image.new("RGB", (W * SS, H * SS))
        self.gd = ImageDraw.Draw(self.glow)
        top, bot = hexc("#232838"), hexc("#10131c")
        for y in range(H * SS):
            t = y / (H * SS)
            self.d.line([(0, y), (W * SS, y)], fill=tuple((top * (1 - t) + bot * t).astype(int)))

    def facets(self, poly, color, n_in=None, shade=1.0, light=(-0.55, -0.85)):
        P = np.array(poly, float)
        if len(P) < 3:
            return
        c = hexc(color) * shade
        path = Path(P)
        # bord densifié + quelques points intérieurs = grandes facettes lisibles
        pts = []
        for a, b in zip(P, np.roll(P, -1, 0)):
            L = np.linalg.norm(b - a)
            k = max(1, int(L / 34))
            for i in range(k):
                pts.append(a + (b - a) * i / k)
        lo, hi = P.min(0), P.max(0)
        Q = np.roll(P, -1, 0)
        area = abs((P[:, 0] * Q[:, 1] - Q[:, 0] * P[:, 1]).sum()) / 2
        n_in = n_in if n_in is not None else int(np.clip(area / 1400, 0, 40))
        tries = 0
        while n_in > 0 and tries < 2000:
            q = lo + rng.random(2) * (hi - lo)
            tries += 1
            if path.contains_point(q, radius=-6):
                pts.append(q)
                n_in -= 1
        pts = np.array(pts)
        if len(pts) < 3:
            return
        try:
            tri = Delaunay(pts)
        except Exception:
            self.d.polygon([tuple(p * SS) for p in P], fill=tuple(c.astype(int)))
            return
        cen = P.mean(0)
        size = max(hi - lo) / 2 + 1e-6
        Lv = np.array(light) / np.linalg.norm(light)
        for s in tri.simplices:
            t = pts[s]
            g = t.mean(0)
            if not path.contains_point(g):
                continue
            v = (g - cen) / size
            k = 0.92 + 0.3 * float(np.dot(np.clip(v, -1, 1), Lv)) + rng.uniform(-0.06, 0.06)
            col = np.clip(c * np.clip(k, 0.55, 1.3), 0, 255).astype(int)
            self.d.polygon([tuple(p * SS) for p in t], fill=tuple(col))

    def flat(self, poly, color, shade=1.0):
        c = np.clip(hexc(color) * shade, 0, 255).astype(int)
        self.d.polygon([tuple(np.array(p) * SS) for p in poly], fill=tuple(c))

    def neon(self, poly, color, width=None):
        c = tuple(hexc(color).astype(int))
        pp = [tuple(np.array(p) * SS) for p in poly]
        if width:
            self.d.line(pp, fill=c, width=int(width * SS), joint="curve")
            self.gd.line(pp, fill=c, width=int(width * SS * 3), joint="curve")
        else:
            self.d.polygon(pp, fill=c)
            self.gd.polygon(pp, fill=c)

    def line(self, pts, color, width, shade=1.0):
        c = tuple(np.clip(hexc(color) * shade, 0, 255).astype(int))
        self.d.line([tuple(np.array(p) * SS) for p in pts], fill=c, width=int(width * SS), joint="curve")

    def text(self, xy, s, size=20, color="#d8dce8", bold=False, anchor="la"):
        f = ImageFont.truetype(FONT_B if bold else FONT, size * SS)
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=tuple(hexc(color).astype(int)), anchor=anchor)

    def finish(self, path):
        g = self.glow.filter(ImageFilter.GaussianBlur(9 * SS))
        out = np.clip(np.asarray(self.img, float) + np.asarray(g, float) * 0.9, 0, 255).astype(np.uint8)
        Image.fromarray(out).resize((W, H), Image.LANCZOS).save(path)


def tube(center, widths):
    """Polygone épais le long d'une ligne (largeur variable)."""
    C = np.array(center, float)
    wd = np.array(widths, float)
    left, right = [], []
    for i, p in enumerate(C):
        a = C[max(i - 1, 0)]
        b = C[min(i + 1, len(C) - 1)]
        t = b - a
        t /= np.linalg.norm(t) + 1e-9
        n = np.array([-t[1], t[0]])
        left.append(p + n * wd[i] / 2)
        right.append(p - n * wd[i] / 2)
    return left + right[::-1], left, right


def tf(pts, o, s, flip=False):
    P = np.array(pts, float)
    if flip:
        P[:, 0] *= -1
    return [tuple(p) for p in (P * s + np.array(o))]


# ---------- têtes (profil, regard à gauche, base du crâne en 0,0) ----------
def head(cv, kind, o, s, pal, shade=1.0, trait=None):
    T = lambda pts: tf(pts, o, s)
    if kind == "A":   # Brute : arcade massive, mâchoire carrée, crocs qui dépassent
        horns = [[(5, -38), (40, -72), (95, -96), (140, -112), (112, -84), (60, -50), (20, -20)],
                 [(-28, -46), (-12, -84), (6, -52)]]
        skull = [(25, -28), (-15, -52), (-58, -50), (-104, -30), (-150, -20), (-182, -10), (-188, 8),
                 (-178, 16), (-120, 18), (-62, 20), (-15, 28), (22, 14)]
        jaw = [(-172, 17), (-112, 21), (-58, 22), (-4, 22), (8, 40), (-28, 54), (-86, 44), (-146, 33), (-170, 26)]
        brow = [(-14, -56), (-58, -58), (-108, -36), (-92, -26), (-70, -32), (-36, -38)]
        cheek = [(-30, 0), (-2, -12), (22, 6), (8, 24), (-24, 20)]
        eye = [(-86, -28), (-58, -33), (-52, -24), (-78, -20)]
        spikes = [[(16, 4), (66, -4), (22, 22)], [(6, 26), (52, 44), (8, 38)], [(-140, -16), (-128, -44), (-116, -20)]]
        fangs = [[(-150, 16), (-142, 40), (-134, 17)], [(-104, 19), (-98, 35), (-92, 20)],
                 [(-166, 23), (-160, 2), (-154, 21)]]
        nostril = [(-172, -6), (-160, -9), (-162, -2)]
    elif kind == "B":  # Prédateur : museau long et plat, crête d'épines, cornes parallèles
        horns = [[(0, -24), (55, -48), (150, -62), (60, -30), (20, -8)],
                 [(-20, -30), (30, -62), (120, -86), (40, -42), (0, -18)]]
        skull = [(22, -18), (-20, -36), (-70, -36), (-120, -22), (-190, -12), (-226, -4), (-230, 8),
                 (-200, 13), (-120, 15), (-50, 18), (0, 22), (24, 8)]
        jaw = [(-215, 14), (-140, 17), (-60, 19), (-6, 21), (4, 34), (-40, 40), (-120, 30), (-200, 22)]
        brow = [(-30, -40), (-72, -42), (-112, -24), (-98, -18), (-74, -26), (-44, -30)]
        cheek = [(-26, -4), (0, -14), (20, 4), (-4, 18)]
        eye = [(-96, -22), (-64, -27), (-60, -20), (-90, -16)]
        spikes = [[(-30, -36), (-14, -66), (-2, -40)], [(-56, -36), (-46, -60), (-34, -38)],
                  [(-84, -32), (-78, -50), (-66, -34)], [(12, 10), (54, 18), (14, 22)]]
        fangs = [[(-206, 13), (-200, 30), (-194, 14)], [(-176, 14), (-172, 26), (-167, 14)],
                 [(-146, 15), (-142, 27), (-137, 15)], [(-116, 16), (-112, 28), (-107, 16)],
                 [(-188, 20), (-184, 5), (-179, 20)], [(-158, 21), (-154, 7), (-149, 21)]]
        nostril = [(-216, -4), (-204, -7), (-206, 0)]
    else:              # C Ancien : couronne de cornes, collerette d'épines aux joues, barbe
        horns = [[(10, -36), (52, -70), (78, -120), (70, -64), (30, -22)],
                 [(-14, -46), (8, -96), (28, -112), (16, -78), (6, -44)],
                 [(-40, -48), (-36, -84), (-22, -50)], [(22, -20), (90, -40), (120, -30), (70, -18), (28, -2)]]
        skull = [(28, -26), (-10, -54), (-56, -54), (-98, -36), (-138, -22), (-162, -10), (-166, 8),
                 (-156, 16), (-100, 20), (-40, 24), (0, 28), (28, 10)]
        jaw = [(-150, 17), (-96, 22), (-40, 24), (0, 24), (10, 40), (-30, 50), (-90, 42), (-140, 30)]
        brow = [(-20, -58), (-62, -60), (-102, -38), (-88, -30), (-64, -36), (-36, -40)]
        cheek = [(-24, -2), (4, -16), (26, 8), (6, 26), (-20, 22)]
        eye = [(-80, -32), (-54, -36), (-48, -28), (-74, -24)]
        spikes = [[(20, -6), (84, -10), (28, 8)], [(24, 10), (90, 22), (26, 24)], [(14, 28), (70, 52), (10, 40)],
                  [(-30, 50), (-24, 82), (-14, 50)], [(-60, 46), (-56, 76), (-46, 46)], [(-92, 42), (-90, 66), (-80, 42)]]
        fangs = [[(-140, 17), (-133, 38), (-126, 18)], [(-152, 22), (-146, 4), (-140, 21)]]
        nostril = [(-152, -4), (-140, -7), (-142, 0)]
    if trait == "bois":   # Forêt : bois de cerf à la place des cornes
        horns = [[(0, -36), (30, -80), (40, -130), (48, -128), (40, -80), (60, -96), (78, -120), (84, -116),
                  (66, -84), (44, -50), (16, -20)],
                 [(-24, -46), (-20, -96), (-12, -96), (-14, -60), (-2, -76), (6, -74), (-6, -46)]]
    for h in horns[1:]:
        cv.facets(T(h), pal["horn"], shade=0.75 * shade)
    cv.facets(T(jaw), pal["body"], shade=0.82 * shade)
    for f in fangs:
        cv.flat(T(f), "#efe8d8", shade=shade)
    cv.facets(T(skull), pal["body"], shade=shade)
    cv.facets(T(cheek), pal["body"], shade=1.12 * shade, n_in=1)
    cv.facets(T(brow), pal["dark"], shade=shade, n_in=1)
    cv.facets(T(horns[0]), pal["horn"], shade=shade)
    for sp in spikes:
        cv.facets(T(sp), pal["spike"], shade=0.9 * shade, n_in=0)
    cv.flat(T([(-170, 17), (-60, 21), (-60, 24), (-170, 20)]), "#1a0c0c", shade=1)  # ligne de gueule
    E = np.array(eye, float)
    c = E.mean(0)
    cv.flat(T([tuple(c + (p - c) * 1.7 + (0, 2)) for p in E]), "#140808", shade=1)   # orbite
    cv.neon(T(eye), pal["neon"])
    cv.flat(T([tuple(c + (-1.5, -6)), tuple(c + (1, -6)), tuple(c + (1.5, 6)), tuple(c + (-1, 6))]), "#140808")
    cv.facets(T(brow), pal["dark"], shade=shade * 1.1, n_in=0)   # l'arcade repasse devant l'œil
    cv.flat(T(nostril), "#1a0c0c")


# ---------- dragon complet (profil) ----------
# Proportions v2b : corps trapu en tonneau, tête ~1/4 de la longueur du corps, cou court et épais,
# pattes épaisses et courtes, ailes un peu réduites, queue épaisse à la base et relevée.
def frame(a, b):
    a, b = np.array(a, float), np.array(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    v = np.array([-u[1], u[0]])
    return lambda pts: [tuple(b + u * x + v * y) for x, y in pts]


def tail(cv, T, pal, kind, shade=1.0):
    c = [(640, 380), (720, 422), (800, 448), (870, 446), (928, 418), (972, 376)]
    poly, l, r = tube(c, [112, 84, 62, 44, 30, 18])
    dors = l if np.mean([p[1] for p in l]) < np.mean([p[1] for p in r]) else r
    cv.facets(T(poly), pal["body"], shade=shade)
    ventre = r if dors is l else l
    for i in range(1, 4):   # plaques ventrales
        a, b = np.array(ventre[i - 1]), np.array(ventre[i])
        cv.facets(T([tuple(a), tuple(b), tuple(b + (0, -10)), tuple(a + (0, -12))]), pal["belly"], n_in=0, shade=shade)
    F = frame(c[-2], c[-1])
    if kind == "nageoire":   # voile membraneuse sur le dernier tiers
        a, b, cc, d = (np.array(dors[i]) for i in (2, 3, 4, 5))
        tips = [a + (0, -80), b + (12, -104), cc + (34, -96), d + (60, -50)]
        memb = [tuple(a)] + sum([[tuple(t), tuple((t + n) / 2 + (6, 12))] for t, n in zip(tips[:-1], tips[1:])], []) \
            + [tuple(tips[-1]), tuple(d)]
        cv.facets(T(memb), pal["memb"], shade=shade)
        for base, t in zip((a, b, cc, d), tips):
            cv.line(T([tuple(base), tuple(t)]), pal["dark"], 5, shade=shade * 1.3)
            cv.neon(T([tuple(t + (base - t) * 0.25), tuple(t)]), pal["neon"], width=4)
        cv.facets(T(F([(-8, 10), (34, 0), (-8, -10)])), pal["horn"], n_in=0, shade=shade)
        return
    for i, h in zip(range(1, 5), (34, 28, 22, 16)):   # plaques dorsales
        p = np.array(dors[i])
        cv.facets(T([tuple(p + (-14, 6)), tuple(p + (2, -h)), tuple(p + (14, 6))]), pal["spike"], n_in=0, shade=shade)
    if kind == "lame":       # fer de lance, Neon seulement sur le tranchant
        blade = F([(-14, 12), (20, 34), (96, 0), (20, -34), (-14, -12), (6, 0)])
        cv.facets(T(blade), pal["spike"], shade=shade, n_in=2)
        cv.facets(T(F([(6, 0), (20, 34), (96, 0)])), pal["spike"], shade=shade * 0.72, n_in=0)
        cv.neon(T(F([(30, 28), (92, 0), (30, -28)])), pal["neon"], width=4)
    else:                    # massue hérissée
        ring = [(26 + 34 * np.cos(t), 30 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 9)[:-1]]
        for ang in (-80, -40, 0, 40, 80, 125, -125):
            t = np.radians(ang)
            cx, cy = 26 + 30 * np.cos(t), 26 * np.sin(t)
            cv.facets(T(F([(cx - 9 * np.sin(t), cy + 9 * np.cos(t)), (26 + 62 * np.cos(t), 56 * np.sin(t)),
                           (cx + 9 * np.sin(t), cy - 9 * np.cos(t))])), pal["horn"], n_in=0, shade=shade)
        cv.facets(T(F(ring)), pal["dark"], shade=shade * 1.4, n_in=3)
        cv.neon(T(F([(14, 0), (26, -10), (38, 0), (26, 10)])), pal["neon"])


def dragon(cv, o, s, pal, headkind="A", trait=None, queue="lame"):
    T = lambda pts: tf(pts, o, s)
    far = 0.62
    wing(cv, T, pal, shade=far, off=(-40, -22), trait=trait)
    leg_front(cv, T, pal, off=(30, -6), shade=far)
    leg_hind(cv, T, pal, off=(32, -8), shade=far)
    tail(cv, T, pal, queue)
    torso = [(382, 318), (372, 392), (408, 452), (500, 472), (590, 456), (652, 414), (672, 352),
             (634, 302), (545, 282), (452, 286), (404, 298)]
    cv.facets(T(torso), pal["body"])
    cv.facets(T([(378, 360), (386, 410), (420, 452), (500, 468), (548, 462), (480, 434), (420, 400)]), pal["belly"])
    neck_c = [(440, 330), (378, 306), (338, 262), (322, 222)]
    poly, top, bot = tube(neck_c, [124, 108, 92, 84])
    cv.facets(T(poly), pal["body"])
    for i in range(1, 4):
        a, b = np.array(bot[i - 1]), np.array(bot[i])
        cv.facets(T([tuple(a), tuple(b), tuple(b + (10, -4)), tuple(a + (12, -6))]), pal["belly"], n_in=0)
    leg_hind(cv, T, pal)
    leg_front(cv, T, pal)
    back = [tuple(np.array(top[i]) + (2, 4)) for i in (3, 2, 1)] + [(470, 288), (530, 282), (590, 288), (636, 304)]
    for i, p in enumerate(back):
        p = np.array(p)
        h = [22, 26, 30, 34, 36, 32, 26][i]
        if trait == "cristal":
            cv.facets(T([tuple(p + (-12, 6)), tuple(p + (-4, -h * 1.5)), tuple(p + (4, -h * 1.1)), tuple(p + (12, 6))]),
                      pal["spike"], n_in=0)
        elif trait == "feuilles" and i < 4:
            cv.facets(T([tuple(p + (-6, 4)), tuple(p + (14, -h * 1.2)), tuple(p + (34, -h * 0.5)), tuple(p + (18, 6))]),
                      pal["spike"], n_in=0)
        else:
            cv.facets(T([tuple(p + (-12, 4)), tuple(p + (6, -h)), tuple(p + (12, 4))]), pal["spike"], n_in=0)
    head(cv, headkind, T([(334, 206)])[0], s * 1.12, pal, trait="bois" if trait == "feuilles" else None)
    wing(cv, T, pal, trait=trait)
    cv.neon(T([(384, 356), (396, 340), (408, 356), (396, 374)]), pal["neon"])


def wing(cv, T, pal, shade=1.0, off=(0, 0), trait=None):
    ox, oy = off
    S = lambda pts: T([(x + ox, y + oy) for x, y in pts])
    root, elbow, wrist = (500, 298), (540, 196), (650, 140)
    tips = [(810, 100), (842, 200), (790, 278), (694, 302)]
    back = (604, 304)
    w = np.array(wrist, float)
    pts = [tips[0]]
    for a, b in zip(tips[:-1], tips[1:]):
        a, b = np.array(a, float), np.array(b, float)
        m = (a + b) / 2
        if trait == "dechire":
            pts += [tuple(a + (b - a) * 0.3 + (w - m) * 0.25), tuple(m + (w - m) * 0.08),
                    tuple(a + (b - a) * 0.7 + (w - m) * 0.42)]
        else:
            pts.append(tuple(m + (w - m) * 0.32))
        pts.append(tuple(b))
    last = np.array(tips[-1], float)
    pts.append(tuple((last + np.array(back)) / 2 + (w - (last + np.array(back)) / 2) * 0.2))
    memb = [root, elbow, wrist] + pts + [back]
    cv.facets(S(memb), pal["memb"], shade=shade)
    cv.line(S([root, elbow, wrist]), pal["dark"], 16, shade=shade * 1.3)
    for t in tips:
        cv.line(S([wrist, t]), pal["dark"], 7, shade=shade * 1.3)
    cv.facets(S([(wrist[0] - 6, wrist[1] + 4), (wrist[0] - 30, wrist[1] - 24), (wrist[0] + 6, wrist[1] - 6)]),
              pal["horn"], n_in=0, shade=shade)
    for t in tips[:3]:
        t = np.array(t, float)
        d = (t - w) / np.linalg.norm(t - w)
        p0 = t - d * 30
        if shade >= 1:
            cv.neon(S([tuple(p0), tuple(t + d * 6)]), pal["neon"], width=6)
        else:
            cv.line(S([tuple(p0), tuple(t + d * 6)]), pal["neon"], 5, shade=0.55)


def claws(cv, T, pal, pts, shade):
    for x, y in pts:
        cv.flat(T([(x, y - 7), (x - 18, y + 4), (x, y + 4)]), pal["horn"], shade=shade)


def leg_front(cv, T, pal, off=(0, 0), shade=1.0):
    ox, oy = off
    c = [(440 + ox, 372 + oy), (466 + ox, 448 + oy), (444 + ox, 518 + oy), (440 + ox, 552 + oy)]
    poly, _, _ = tube(c, [86, 60, 42, 40])
    cv.facets(T(poly), pal["body"], shade=shade * 0.95)
    cv.facets(T([(398 + ox, 548 + oy), (462 + ox, 544 + oy), (470 + ox, 578 + oy), (392 + ox, 580 + oy)]),
              pal["body"], shade=shade * 0.85, n_in=0)
    claws(cv, T, pal, [(396 + ox, 576 + oy), (416 + ox, 578 + oy), (436 + ox, 579 + oy)], shade)


def leg_hind(cv, T, pal, off=(0, 0), shade=1.0):
    ox, oy = off
    cv.facets(T([(556 + ox, 330 + oy), (646 + ox, 310 + oy), (702 + ox, 366 + oy), (690 + ox, 446 + oy),
                 (624 + ox, 482 + oy), (566 + ox, 432 + oy)]), pal["body"], shade=shade * 1.02)
    c = [(626 + ox, 456 + oy), (602 + ox, 490 + oy), (652 + ox, 526 + oy), (636 + ox, 556 + oy)]
    poly, _, _ = tube(c, [66, 50, 38, 36])
    cv.facets(T(poly), pal["body"], shade=shade * 0.92)
    cv.facets(T([(592 + ox, 550 + oy), (660 + ox, 546 + oy), (668 + ox, 578 + oy), (586 + ox, 580 + oy)]),
              pal["body"], shade=shade * 0.85, n_in=0)
    claws(cv, T, pal, [(590 + ox, 576 + oy), (610 + ox, 578 + oy), (630 + ox, 579 + oy)], shade)


# ---------- planche ----------
def main():
    cv = Canvas()
    F = LIGNEES["Feu"]
    cv.text((40, 30), "Dragon low-poly — concept v2b", 34, bold=True)
    cv.text((40, 76), "Proportions revues + 3 queues au choix (tête A).", 19, "#9aa3b8")
    dragon(cv, (-70, 120), 1.0, F, "A", queue="lame")
    notes = [
        "1  Corps en tonneau plus court, poitrail profond",
        "2  Tête plus grosse (~1/4 du corps), cou court et épais",
        "3  Pattes plus épaisses et plus courtes, grosses pattes au sol",
        "4  Ailes réduites d'environ 15 % : le corps reste le centre",
        "5  Queue épaisse à la base, relevée au bout, plaques dorsales",
    ]
    for i, t in enumerate(notes):
        cv.text((60, 790 + i * 28), t, 17, "#c8cede")

    cv.text((1180, 120), "Queues proposées", 24, bold=True)
    for i, (k, nom, desc) in enumerate([
        ("lame", "1 · Lame", "fer de lance Neon"),
        ("massue", "2 · Massue", "boule hérissée"),
        ("nageoire", "3 · Nageoire", "voile, pointes Neon"),
    ]):
        y = 160 + i * 270
        cv.text((1180, y + 100), nom, 20, "#ffd27a", bold=True)
        cv.text((1180, y + 126), desc, 16, "#9aa3b8")
        dragon(cv, (1375, y + 40), 0.42, F, "A", queue=k)

    cv.text((40, 985), "Une forme par lignée (pas seulement la couleur)", 22, bold=True)
    for i, (nom, trait, desc) in enumerate([
        ("Feu", None, "grandes cornes, braises"),
        ("Glace", "cristal", "crête en cristaux"),
        ("Forêt", "feuilles", "bois de cerf, crête en feuilles"),
        ("Ombre", "dechire", "ailes déchirées"),
    ]):
        x = 40 + i * 465
        dragon(cv, (x - 60, 990), 0.42, LIGNEES[nom], "A", trait)
        cv.text((x + 50, 1250), f"{nom} — {desc}", 16, "#c8cede")

    cv.finish("../concept-dragon-v2b.png")


if __name__ == "__main__":
    main()
