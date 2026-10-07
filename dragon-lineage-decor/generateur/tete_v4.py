# Étude de tête pour la v4 : la tête v3 (référence) face à deux têtes retaillées en plans.
# Constat v3 : truffe et menton en boules, fusions trop molles, masse à l'avant au lieu de l'arrière.
# Correctifs : museau taillé en coin par des plans (dessus plat, flancs qui convergent, face avant plate),
# masse reportée sur la mâchoire et les pommettes, arcade à dessous plat, crête nasale étroite,
# rayons de fusion divisés par deux, moins de pointes.
#   B « Coin »       : mâchoire du haut qui déborde (gueule de crocodile), dessous de mâchoire bien droit
#   C « Bouledogue » : museau plus court et plus large, mâchoire du bas en avant, crocs du bas en défenses
# Usage : python3 tete_v4.py  ->  ../concept-tete-v4.png
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
from sdf import ellipsoid, sphere, cone_seg, smooth_chain, smin, smax, union, ellipsoid_r, look_basis

HB, HEAD_R, HS = V.HB, V.HEAD_R, V.HS
_hq = V._hq

VARIANTES = {
    "B": dict(nom="B « Coin »", tip=-3.5, w_back=0.74, w_tip=0.44, top_back=0.66, top_tip=0.42,
              chin=-3.25, jw_back=0.68, jw_tip=0.38, jaw_bot=(-0.9, -0.52), jaw_w=0.95, tusk=False),
    "C": dict(nom="C « Bouledogue »", tip=-3.0, w_back=0.82, w_tip=0.6, top_back=0.66, top_tip=0.48,
              chin=-3.18, jw_back=0.8, jw_tip=0.6, jaw_bot=(-1.0, -0.66), jaw_w=1.05, tusk=True),
}


def plan(q, n, o):
    """Demi-espace : négatif du côté opposé à la normale n, passant par o."""
    n = np.asarray(n, np.float32) / np.linalg.norm(n)
    return (q - np.asarray(o, np.float32)) @ n


def lerp_z(z, z0, z1, v0, v1):
    t = np.clip((z - z0) / (z1 - z0), 0, 1)
    return v0 + (v1 - v0) * t


def mouth_line(q, tip):
    # rictus : la ligne de la gueule remonte vers la joue
    return -0.12 + 0.17 * np.clip(q[..., 2] - tip + 0.05, 0, None)


def head(lin, p):
    def f(P):
        q = _hq(P)
        x, y, z = q[..., 0], q[..., 1], q[..., 2]
        tip = p["tip"]
        d = ellipsoid(q, (0, 0.38, -0.45), (1.0, 0.9, 1.05))                                   # crâne
        for s in (-1, 1):
            d = smin(d, ellipsoid(q, (s * 0.86, 0.12, -0.8), (0.46, 0.46, 0.75)), 0.15)         # pommettes larges
        # museau : un volume taillé en coin par des plans
        sn = ellipsoid(q, (0, 0.2, (tip - 0.6) / 2), (0.85, 0.75, (-tip - 0.6) / 2 + 0.35))
        w = lerp_z(z, -1.2, tip, p["w_back"], p["w_tip"])
        sn = smax(sn, (np.abs(x) - w) * 0.97, 0.06)                                            # flancs qui convergent
        top = lerp_z(z, -1.2, tip, p["top_back"], p["top_tip"])
        sn = smax(sn, (y - top) * 0.99, 0.06)                                                  # dessus plat
        sn = smax(sn, plan(q, (0, 0.25, -1), (0, 0.3, tip)), 0.05)                              # face avant plate (truffe)
        d = smin(d, sn, 0.18)
        d = smin(d, cone_seg(q, (0, top_at(p, -1.4) + 0.02, -1.4), (0, p["top_tip"] + 0.06, tip + 0.45), 0.15, 0.08), 0.06)  # crête nasale
        for s in (-1, 1):
            brow = ellipsoid_r(q, (s * 0.6, 0.92, -1.4), (0.4, 0.2, 0.72), look_basis((s * 0.3, -0.45, -1)))
            brow = smax(brow, 0.8 - y, 0.03)                                                   # dessous plat : l'arcade surplombe l'œil
            d = smin(d, brow, 0.06)
            d = smax(d, -ellipsoid_r(q, (s * 0.74, 0.55, -1.55), (0.2, 0.15, 0.36), look_basis((s * 0.2, -0.3, -1))), 0.04)  # orbite
            d = smax(d, -ellipsoid(q, (s * 0.2, top_at(p, tip) - 0.12, tip - 0.02), (0.08, 0.06, 0.12)), 0.03)  # narines
        d = smax(d, np.where(z < -0.7, mouth_line(q, tip) - y, -10.0), 0.04)                   # gueule
        horn, spike, teeth = [], [], []
        for s in (-1, 1):
            horn.append(smooth_chain(q, [(s * 0.5, 0.9, -0.35), (s * 0.75, 1.3, 0.35), (s * 0.95, 1.95, 1.25), (s * 1.0, 2.55, 2.0)],
                                     [0.34, 0.25, 0.14, 0.02], 5, 0.03))                       # grandes cornes
            if lin == "Feu":   # cornes d'arcade (trait de lignée)
                horn.append(cone_seg(q, (s * 0.62, 1.0, -1.15), (s * 0.85, 1.45, -1.55), 0.14, 0.02))
            spike.append(cone_seg(q, (s * 0.92, -0.25, -0.5), (s * 1.5, -0.5, 0.3), 0.17, 0.02))   # une seule épine de joue
            zc = tip + 0.5
            teeth.append(cone_seg(q, (s * (p["w_tip"] - 0.06), -0.02, zc),
                                  (s * (p["w_tip"] - 0.03), -0.7, zc - 0.05), 0.11, 0.015))     # croc du haut
            for dz in (0.85, 1.2):
                zz, wz = tip + dz, width_at(p, tip + dz)
                teeth.append(cone_seg(q, (s * (wz - 0.06), 0.0, zz), (s * (wz - 0.05), -0.3, zz), 0.06, 0.01))
        horn.append(cone_seg(q, (0, p["top_tip"] + 0.05, tip + 0.6), (0, p["top_tip"] + 0.5, tip + 0.8), 0.12, 0.02))   # corne de nez
        eye = union(*[ellipsoid_r(q, (s * 0.7, 0.56, -1.55), (0.1, 0.11, 0.27), look_basis((s * 0.2, -0.35, -1)))
                      for s in (-1, 1)])
        pupil = union(*[ellipsoid(q, (s * 0.8, 0.56, -1.56), (0.03, 0.1, 0.035)) for s in (-1, 1)])
        back = ellipsoid(q, (0, 1.05, -0.9), (0.75, 0.38, 1.6))
        S = lambda v: v * HS
        return {"skin": S(d), "horn": S(union(*horn)), "spike": S(union(*spike)), "teeth": S(union(*teeth)),
                "eye": S(eye), "pupil": S(pupil), "back": S(back)}
    return f


def width_at(p, z):
    return float(lerp_z(np.float32(z), -1.2, p["tip"], p["w_back"], p["w_tip"]))


def top_at(p, z):
    return float(lerp_z(np.float32(z), -1.2, p["tip"], p["top_back"], p["top_tip"]))


def jaw(lin, p):
    def f(P):
        q = _hq(P)
        x, y, z = q[..., 0], q[..., 1], q[..., 2]
        tip, chin = p["tip"], p["chin"]
        d = ellipsoid(q, (0, -0.48, -0.9), (p["jaw_w"], 0.62, 0.8))                             # muscle de mâchoire
        for s in (-1, 1):
            d = smin(d, ellipsoid(q, (s * 0.72, -0.4, -0.85), (0.36, 0.48, 0.62)), 0.12)        # masséters
        jb = ellipsoid(q, (0, -0.35, (chin - 0.8) / 2), (0.8, 0.7, (-chin - 0.8) / 2 + 0.35))
        jb = smax(jb, (np.abs(x) - lerp_z(z, -1.2, chin, p["jw_back"], p["jw_tip"])) * 0.97, 0.05)
        bot = lerp_z(z, -1.2, chin, *p["jaw_bot"])
        jb = smax(jb, bot - y, 0.05)                                                           # dessous droit
        jb = smax(jb, plan(q, (0, -0.45, -1), (0, -0.3, chin)), 0.04)                           # menton qui fuit vers le bas
        d = smin(d, jb, 0.12)
        # angle de la mâchoire bien marqué à l'arrière
        d = smin(d, ellipsoid(q, (0, p["jaw_bot"][0] - 0.05, -0.75), (p["jaw_w"] * 0.85, 0.25, 0.45)), 0.08)
        d = smax(d, q[..., 1] - (mouth_line(q, tip) - 0.04), 0.03)
        teeth = []
        for s in (-1, 1):
            if p["tusk"]:   # défenses : crocs du bas qui passent devant la lèvre du haut
                teeth.append(cone_seg(q, (s * (p["jw_tip"] - 0.04), -0.25, chin + 0.2), (s * (p["jw_tip"] + 0.04), 0.55, chin + 0.12), 0.12, 0.02))
            else:
                teeth.append(cone_seg(q, (s * (p["jw_tip"] - 0.04), -0.2, chin + 0.15), (s * (p["jw_tip"] - 0.02), 0.35, chin + 0.1), 0.09, 0.015))
            zz = chin + 0.9
            teeth.append(cone_seg(q, (s * (p["jw_tip"] + 0.12), -0.15, zz), (s * (p["jw_tip"] + 0.13), 0.08, zz), 0.05, 0.01))
        belly = ellipsoid(q, (0, -0.85, -1.9), (0.52, 0.3, 1.7))
        S = lambda v: v * HS
        return {"skin": S(d), "teeth": S(union(*teeth)), "belly": S(belly)}
    return f


# ---------- construction ----------
def build_head(var, lin="Feu"):
    jp = tuple(HB + HEAD_R @ np.array([0, -0.35, -0.8]) * HS)
    if var == "A":
        segs = [("Head", V.head(lin), 760), ("Jaw", V.jaw(lin), 220)]
    else:
        p = VARIANTES[var]
        segs = [("Head", head(lin, p), 640), ("Jaw", jaw(lin, p), 300)]
    layers, slots = V.build_segment(V.neck(lin), 260)
    out = {"Neck": {"parent": None, "pivot": tuple(V.NECK[0]), "layers": layers, "slots": slots}}
    for name, fn, budget in segs:
        layers, slots = V.build_segment(fn, budget, h=0.05)
        out[name] = {"parent": "Neck", "pivot": tuple(HB) if name == "Head" else jp, "layers": layers, "slots": slots}
    return out


def head_tris(m):
    return sum(len(x.faces) for n in ("Head", "Jaw") for x in m[n]["layers"].values())


# ---------- planche ----------
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main():
    hc = HB + HEAD_R @ np.array([0, 0.6, -1.1]) * HS        # centre de la tête
    vues = [("Profil", np.array([-14.0, 0.6, 0.0]), 30),
            ("Face", np.array([0.0, 1.2, -13.0]), 30),
            ("3/4", np.array([-9.5, 2.6, -9.5]), 30),
            ("Dessus", np.array([-0.5, 16.0, -2.0]), 32),
            ("3/4 bas", np.array([-10.0, -5.0, -8.0]), 30)]
    lignes = [("A", "A — v3 (référence)", "truffe et menton en boules, fusions molles"),
              ("B", VARIANTES["B"]["nom"], "museau en coin, mâchoire du haut qui déborde, dessous droit"),
              ("C", VARIANTES["C"]["nom"], "museau court et large, mâchoire du bas en avant, défenses")]
    cw, ch, lw = 330, 300, 250
    W, H = lw + cw * len(vues) + 20, 110 + ch * len(lignes) + 120
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 20), "Dragon — étude de tête v4", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 64), "Même pose et mêmes yeux qu'en v3 ; seules la tête et la mâchoire changent. Lignée Feu.",
            font=f(17), fill=(150, 160, 184))
    for j, (t, _, _) in enumerate(vues):
        dr.text((lw + j * cw + 14, 92), t, font=f(17, True), fill=(255, 210, 122))
    pal = dict(V.VARIANTS["Feu"]); pal["glow"] = pal["eye"]
    for i, (var, titre, desc) in enumerate(lignes):
        m = build_head(var)
        it = rendu.gather(m, pal)
        y0 = 118 + i * ch
        dr.text((20, y0 + 20), titre, font=f(20, True), fill=(230, 232, 240))
        yy = y0 + 56
        for line in wrap(desc, 24):
            dr.text((20, yy), line, font=f(15), fill=(180, 186, 204)); yy += 22
        dr.text((20, yy + 10), f"{head_tris(m)} triangles (tête + mâchoire)", font=f(14), fill=(140, 150, 172))
        for j, (_, off, fov) in enumerate(vues):
            board.paste(rendu.render(it, hc + off, hc, size=(cw - 8, ch - 8), fov=fov), (lw + j * cw, y0))
        print(var, head_tris(m), flush=True)
    notes = ["Cible : tête + mâchoire autour de 1 000 triangles (cornes et dents comprises).",
             "À choisir : B ou C (ou un mélange, ex. museau de B + défenses de C), puis intégration dans la maquette v4."]
    for k, t in enumerate(notes):
        dr.text((24, H - 90 + k * 28), "•  " + t, font=f(16), fill=(200, 206, 222))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "concept-tete-v4.png"))


def wrap(t, n):
    out, cur = [], ""
    for w in t.split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + [cur]


if __name__ == "__main__":
    main()
