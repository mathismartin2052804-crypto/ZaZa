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
def dragon(cv, o, s, pal, headkind="A", trait=None):
    T = lambda pts: tf(pts, o, s)
    far = 0.62

    # aile éloignée (derrière)
    wing(cv, T, pal, shade=far, off=(-46, -26), trait=trait)
    # pattes éloignées
    leg_front(cv, T, pal, off=(28, -6), shade=far)
    leg_hind(cv, T, pal, off=(30, -8), shade=far)
    # queue
    tail_c = [(670, 350), (750, 378), (830, 410), (900, 455), (970, 480), (1030, 478)]
    poly, top, _ = tube(tail_c, [78, 58, 40, 26, 14, 6])
    cv.facets(T(poly), pal["body"])
    for i in range(1, 5):
        p = np.array(top[i])
        cv.facets(T([tuple(p + (-10, 2)), tuple(p + (4, -26 + 3 * i)), tuple(p + (12, 4))]), pal["spike"], n_in=0)
    cv.neon(T([(1024, 474), (1058, 458), (1074, 478), (1052, 494), (1026, 484)]), pal["neon"])
    # corps
    torso = [(395, 330), (392, 395), (430, 440), (520, 452), (610, 430), (684, 392), (700, 330),
             (650, 288), (560, 276), (470, 284), (420, 300)]
    cv.facets(T(torso), pal["body"])
    cv.facets(T([(398, 360), (405, 400), (440, 438), (520, 448), (560, 444), (500, 420), (440, 395)]), pal["belly"])
    # cou en S
    neck_c = [(450, 320), (390, 312), (345, 280), (322, 238), (312, 200), (288, 172)]
    poly, top, bot = tube(neck_c, [96, 84, 70, 62, 56, 54])
    neck_top = top
    cv.facets(T(poly), pal["body"])
    for i in range(1, 6):   # plaques ventrales
        a, b = np.array(bot[i - 1]), np.array(bot[i])
        cv.facets(T([tuple(a), tuple(b), tuple(b + (b - a) * 0 + (8, -4)), tuple(a + (10, -6))]), pal["belly"], n_in=0)
    # pattes proches
    leg_hind(cv, T, pal)
    leg_front(cv, T, pal)
    # piquants du dos (couleur d'accent)
    back = [tuple(np.array(top[i]) + (2, 4)) for i in (5, 4, 3, 2)] + [(470, 286), (530, 278), (590, 280), (645, 290)]
    for i, p in enumerate(back):
        p = np.array(p)
        h = [18, 22, 26, 30, 34, 30, 26, 22][i]
        if trait == "cristal":
            cv.facets(T([tuple(p + (-12, 6)), tuple(p + (-4, -h * 1.5)), tuple(p + (4, -h * 1.1)), tuple(p + (12, 6))]),
                      pal["spike"], n_in=0)
        elif trait == "feuilles" and i < 4:
            cv.facets(T([tuple(p + (-6, 4)), tuple(p + (14, -h * 1.2)), tuple(p + (34, -h * 0.5)), tuple(p + (18, 6))]),
                      pal["spike"], n_in=0)
        else:
            cv.facets(T([tuple(p + (-11, 4)), tuple(p + (6, -h)), tuple(p + (11, 4))]), pal["spike"], n_in=0)
    # tête
    head(cv, headkind, T([(300, 168)])[0], s * 0.92, pal, trait="bois" if trait == "feuilles" else None)
    # aile proche
    wing(cv, T, pal, trait=trait)
    # gemme
    cv.neon(T([(404, 352), (414, 340), (424, 352), (414, 368)]), pal["neon"])


def wing(cv, T, pal, shade=1.0, off=(0, 0), trait=None):
    ox, oy = off
    S = lambda pts: T([(x + ox, y + oy) for x, y in pts])
    root, elbow, wrist = (505, 296), (555, 175), (690, 112)
    tips = [(880, 70), (905, 190), (845, 285), (735, 305)]
    back = (615, 300)
    memb = [root, elbow, wrist]
    chain = [wrist] + tips
    w = np.array(wrist, float)
    pts = [tips[0]]
    for a, b in zip(tips[:-1], tips[1:]):
        a, b = np.array(a, float), np.array(b, float)
        m = (a + b) / 2
        if trait == "dechire":
            pts += [tuple(a + (b - a) * 0.3 + (w - m) * 0.25), tuple(m + (w - m) * 0.08),
                    tuple(a + (b - a) * 0.7 + (w - m) * 0.42)]
        else:
            pts.append(tuple(m + (w - m) * 0.32))   # feston
        pts.append(tuple(b))
    last = np.array(tips[-1], float)
    pts.append(tuple((last + np.array(back)) / 2 + (np.array(wrist) - (last + np.array(back)) / 2) * 0.2))
    memb = [root, elbow, wrist] + pts + [back]
    # membrane : éventail de facettes depuis le poignet
    cv.facets(S(memb), pal["memb"], shade=shade)
    # os
    cv.line(S([root, elbow, wrist]), pal["dark"], 15, shade=shade * 1.3)
    for t in tips:
        cv.line(S([wrist, t]), pal["dark"], 7, shade=shade * 1.3)
    cv.facets(S([(wrist[0] - 6, wrist[1] + 4), (wrist[0] - 30, wrist[1] - 24), (wrist[0] + 6, wrist[1] - 6)]),
              pal["horn"], n_in=0, shade=shade)   # griffe du pouce
    # bouts de doigts Neon (seulement le bout, pas tout le bord)
    for t in tips[:3]:
        t = np.array(t, float)
        d = (t - w) / np.linalg.norm(t - w)
        p0 = t - d * 34
        if shade >= 1:
            cv.neon(S([tuple(p0), tuple(t + d * 6)]), pal["neon"], width=6)
        else:
            cv.line(S([tuple(p0), tuple(t + d * 6)]), pal["neon"], 5, shade=0.55)


def claws(cv, T, pal, pts, shade):
    for x, y in pts:
        cv.flat(T([(x, y - 6), (x - 16, y + 4), (x, y + 4)]), pal["horn"], shade=shade)


def leg_front(cv, T, pal, off=(0, 0), shade=1.0):
    ox, oy = off
    c = [(445 + ox, 355 + oy), (470 + ox, 440 + oy), (440 + ox, 520 + oy), (436 + ox, 562 + oy)]
    poly, _, _ = tube(c, [64, 44, 30, 28])
    cv.facets(T(poly), pal["body"], shade=shade * 0.95)
    cv.facets(T([(400 + ox, 556 + oy), (450 + ox, 552 + oy), (458 + ox, 576 + oy), (396 + ox, 578 + oy)]),
              pal["body"], shade=shade * 0.85, n_in=0)
    claws(cv, T, pal, [(400 + ox, 574 + oy), (416 + ox, 576 + oy), (432 + ox, 577 + oy)], shade)


def leg_hind(cv, T, pal, off=(0, 0), shade=1.0):
    ox, oy = off
    # cuisse massive puis patte digitigrade (talon relevé)
    cv.facets(T([(590 + ox, 330 + oy), (660 + ox, 318 + oy), (708 + ox, 370 + oy), (690 + ox, 440 + oy),
                 (630 + ox, 470 + oy), (590 + ox, 420 + oy)]), pal["body"], shade=shade * 1.02)
    c = [(632 + ox, 445 + oy), (612 + ox, 478 + oy), (664 + ox, 520 + oy), (640 + ox, 566 + oy)]
    poly, _, _ = tube(c, [50, 38, 26, 24])
    cv.facets(T(poly), pal["body"], shade=shade * 0.92)
    cv.facets(T([(600 + ox, 560 + oy), (656 + ox, 556 + oy), (662 + ox, 578 + oy), (594 + ox, 580 + oy)]),
              pal["body"], shade=shade * 0.85, n_in=0)
    claws(cv, T, pal, [(598 + ox, 576 + oy), (614 + ox, 578 + oy), (630 + ox, 579 + oy)], shade)


# ---------- planche ----------
def main():
    cv = Canvas()
    F = LIGNEES["Feu"]
    cv.text((40, 30), "Dragon low-poly — concept v2", 34, bold=True)
    cv.text((40, 76), "À valider avant de toucher au générateur. Tête : choisir A, B ou C.", 19, "#9aa3b8")

    # corps entier
    dragon(cv, (-40, 110), 0.98, F, "A")
    notes = [
        ((60, 790), "1  Tête plus grosse : arcade qui écrase l'œil, crocs qui dépassent, cornes vers l'arrière"),
        ((60, 818), "2  Cou en S, plaques ventrales"),
        ((60, 846), "3  Aile à 4 doigts, membrane festonnée, Neon seulement au bout des doigts"),
        ((60, 874), "4  Pattes arrière digitigrades (talon relevé), cuisses massives, griffes visibles"),
        ((60, 902), "5  Piquants dans la couleur d'accent, facettes plus grandes (~5 000 triangles)"),
    ]
    for xy, t in notes:
        cv.text(xy, t, 17, "#c8cede")

    # têtes
    cv.text((1180, 120), "Têtes proposées", 24, bold=True)
    for i, (k, nom, desc) in enumerate([
        ("A", "A · Brute", "arcade massive, mâchoire carrée, crocs"),
        ("B", "B · Prédateur", "museau long, crête d'épines, regard plissé"),
        ("C", "C · Ancien", "couronne de cornes, collerette, barbe"),
    ]):
        y = 160 + i * 270
        cv.text((1180, y), nom, 20, "#ffd27a", bold=True)
        cv.text((1180, y + 26), desc, 16, "#9aa3b8")
        head(cv, k, (1520, y + 180), 1.45, F)

    # lignées
    cv.text((40, 985), "Une forme par lignée (pas seulement la couleur)", 22, bold=True)
    for i, (nom, trait, desc) in enumerate([
        ("Feu", None, "grandes cornes, braises"),
        ("Glace", "cristal", "crête en cristaux"),
        ("Forêt", "feuilles", "bois de cerf, crête en feuilles"),
        ("Ombre", "dechire", "ailes déchirées"),
    ]):
        x = 40 + i * 465
        dragon(cv, (x - 10, 995), 0.38, LIGNEES[nom], "A", trait)
        cv.text((x + 50, 1232), f"{nom} — {desc}", 16, "#c8cede")

    cv.finish("../concept-dragon-v2.png")


if __name__ == "__main__":
    main()
