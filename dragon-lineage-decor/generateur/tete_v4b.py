# Étude de tête v4, 2e tour : on repart de la tête A (v3), jugée la meilleure, au lieu de la remplacer.
# Les têtes taillées en plans (B, C de tete_v4.py) ont perdu le côté organique de A : on ne touche donc
# qu'aux défauts, sans changer cornes, épines, yeux ni dents.
#   A  : v3 telle quelle (référence)
#   A1 : sans les boules — truffe et menton plus petits et rentrés dans le museau, fusions deux fois moins molles
#   A2 : A1 + gueule entrouverte (mâchoire baissée de 9°) : rictus et crocs lisibles
#   A3 : A1 + museau plus long et effilé vers l'avant, bosse nasale plus basse
# Usage : python3 tete_v4b.py  ->  ../concept-tete-v4b.png
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
from tete_v4 import wrap, FONT, FONT_B
from sdf import ellipsoid, sphere, cone_seg, smooth_chain, smin, smax, union, ellipsoid_r, look_basis

HB, HEAD_R, HS, _hq = V.HB, V.HEAD_R, V.HS, V._hq

BASE = dict(sn_r=(0.66, 0.5, 1.3), sn_c=-2.25, k_sn=0.45,
            nb_c=(0, 0.62, -2.85), nb_r=(0.4, 0.24, 0.55), k_nb=0.25,
            tr_c=(0, 0.24, -3.4), tr_r=(0.48, 0.42, 0.42), k_tr=0.3,
            k_pom=0.3, k_arc=0.12,
            jw_r=(0.56, 0.3, 1.2), k_jw=0.35, ch_c=(0, -0.3, -3.25), ch_r=(0.4, 0.26, 0.3), k_ch=0.2, open=0)
A1 = dict(BASE, tr_c=(0, 0.26, -3.3), tr_r=(0.4, 0.33, 0.3), k_tr=0.12, k_sn=0.25, k_nb=0.12, k_pom=0.18,
          k_arc=0.06, ch_c=(0, -0.3, -3.1), ch_r=(0.32, 0.2, 0.22), k_ch=0.08, k_jw=0.18)
VARIANTES = [
    ("A", "A — v3 (référence)", "inchangée", BASE),
    ("A1", "A1 — sans boules", "truffe et menton plus petits et rentrés, fusions deux fois moins molles", A1),
    ("A2", "A2 — gueule ouverte", "A1 + mâchoire baissée de 9° : rictus et crocs bien visibles", dict(A1, open=-9)),
    ("A3", "A3 — museau effilé", "A1 + museau plus long qui s'affine vers l'avant, bosse nasale plus basse",
     dict(A1, sn_r=(0.62, 0.46, 1.42), sn_c=-2.3, nb_c=(0, 0.56, -2.8), nb_r=(0.32, 0.18, 0.6),
          tr_c=(0, 0.24, -3.45), tr_r=(0.34, 0.3, 0.28))),
]


def head(lin, p):
    def f(P):
        q = _hq(P)
        d = ellipsoid(q, (0, 0.35, -0.55), (0.98, 0.88, 1.05))                                         # crâne
        d = smin(d, ellipsoid_r(q, (0, 0.28, p["sn_c"]), p["sn_r"], look_basis((0, -0.08, -1))), p["k_sn"])  # museau
        d = smin(d, ellipsoid(q, p["nb_c"], p["nb_r"]), p["k_nb"])                                    # bosse nasale
        d = smin(d, ellipsoid(q, p["tr_c"], p["tr_r"]), p["k_tr"])                                    # truffe
        for s in (-1, 1):
            d = smin(d, ellipsoid_r(q, (s * 0.55, 0.9, -1.35), (0.36, 0.24, 0.72), look_basis((s * 0.3, -0.5, -1))), p["k_arc"])
            d = smin(d, ellipsoid(q, (s * 0.8, 0.1, -0.85), (0.4, 0.42, 0.72)), p["k_pom"])         # pommette
            d = smax(d, -ellipsoid_r(q, (s * 0.74, 0.55, -1.55), (0.2, 0.15, 0.36), look_basis((s * 0.2, -0.3, -1))), 0.06)
            d = smax(d, -sphere(q, (s * 0.2, 0.42, p["tr_c"][2] - 0.35), 0.09), 0.04)              # narines
        mouth = -0.12 + 0.17 * np.clip(q[..., 2] + 3.6, 0, None)
        d = smax(d, np.where(q[..., 2] < -0.7, mouth - q[..., 1], -10.0), 0.05)
        L = V.head(lin)(P)   # cornes, épines, dents, yeux : identiques à la v3
        L["skin"] = d * HS
        return L
    return f


def jaw(lin, p):
    def f(P):
        q = _hq(P)
        d = ellipsoid(q, (0, -0.4, -0.95), (0.82, 0.55, 0.75))
        d = smin(d, ellipsoid_r(q, (0, -0.32, -2.35), p["jw_r"], look_basis((0, 0.12, -1))), p["k_jw"])
        d = smin(d, ellipsoid(q, p["ch_c"], p["ch_r"]), p["k_ch"])                                    # menton
        mouth = -0.12 + 0.17 * np.clip(q[..., 2] + 3.6, 0, None)
        d = smax(d, q[..., 1] - (mouth - 0.04), 0.04)
        L = V.jaw(lin)(P)
        L["skin"] = d * HS
        return L
    return f


def build_head(p, lin="Feu"):
    jp = tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS)
    out = {}
    layers, slots = V.build_segment(V.neck(lin), 260)
    out["Neck"] = {"parent": None, "pivot": tuple(V.NECK[0]), "layers": layers, "slots": slots}
    for name, fn, budget, piv in (("Head", head(lin, p), 760, tuple(HB)), ("Jaw", jaw(lin, p), 220, jp)):
        layers, slots = V.build_segment(fn, budget, h=0.05)
        out[name] = {"parent": "Neck", "pivot": piv, "layers": layers, "slots": slots}
    return out


def main():
    hc = HB + HEAD_R @ np.array([0, 0.6, -1.1]) * HS
    vues = [("Profil", np.array([-14.0, 0.6, 0.0])), ("Face", np.array([0.0, 1.2, -13.0])),
            ("3/4", np.array([-9.5, 2.6, -9.5])), ("Dessus", np.array([-0.5, 16.0, -2.0])),
            ("3/4 bas", np.array([-10.0, -5.0, -8.0]))]
    cw, ch, lw = 330, 300, 250
    W, H = lw + cw * len(vues) + 20, 118 + ch * len(VARIANTES) + 70
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — étude de tête v4, 2e tour (à partir de A)", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Cornes, épines, yeux et dents identiques à la v3 : seule la forme du museau et de la mâchoire change.",
            font=f(17), fill=(150, 160, 184))
    for j, (t, _) in enumerate(vues):
        dr.text((lw + j * cw + 14, 92), t, font=f(17, True), fill=(255, 210, 122))
    pal = dict(V.VARIANTS["Feu"]); pal["glow"] = pal["eye"]
    for i, (key, titre, desc, p) in enumerate(VARIANTES):
        m = build_head(p)
        it = rendu.gather(m, pal, pose={"Jaw": (p["open"], 0, 0)})
        y0 = 118 + i * ch
        dr.text((20, y0 + 20), titre, font=f(19, True), fill=(230, 232, 240))
        yy = y0 + 54
        for line in wrap(desc, 26):
            dr.text((20, yy), line, font=f(15), fill=(180, 186, 204)); yy += 22
        for j, (_, off) in enumerate(vues):
            board.paste(rendu.render(it, hc + off, hc, size=(cw - 8, ch - 8), fov=30), (lw + j * cw, y0))
        print(key, flush=True)
    dr.text((24, H - 50), "•  Dis-moi laquelle s'approche le plus, et surtout ce qui te gêne encore (forme, expression, cornes…).",
            font=f(16), fill=(200, 206, 222))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-tete-v4b.png"))


if __name__ == "__main__":
    main()
