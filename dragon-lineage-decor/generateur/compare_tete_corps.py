# Pourquoi les têtes v8 « rendent mal » sur le corps v5 : comparatif à vues égales.
#   ligne 1 : tête actuelle (x1) ; ligne 2 : tête x1,45 ; ligne 3 : tête x1,45 + queue raccourcie + ailes et corps
#   un cran plus sombres que la tête (la tête devient le point le plus clair et le plus contrasté).
# Usage : python3 compare_tete_corps.py [Archétype]  ->  ../comparaison-tete-corps-v8.png
import os
import sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import rendu
import corps_v5 as C5
import corps_v4 as V4
import palette_corps as PC
import tete_v7 as T7
import tete_v8 as T8


def head_on_body(nm, hs, k=0.5, open_deg=0):
    m = C5.build("Feu", k)
    a = T8.ARCHETYPES[nm]
    hp, hsl = T8.head_parts(nm, a)
    for kk, v in T8.mouth_web(a, open_deg).items():
        hp.setdefault(kk if kk != "skin" else "cheek", []).extend(v)
    jp, jsl = T8.jaw_parts(nm, a, open_deg)
    for part, layers, sl in (("Head", hp, hsl), ("Jaw", jp, jsl)):
        lay = {}
        for kk, v in layers.items():
            w = trimesh.util.concatenate(v).copy()
            w.vertices = V4.HB + hs * (w.vertices @ V4.HEAD_R.T)
            lay[kk] = T7.finish(w, False)
        m[part] = {"parent": None, "pivot": tuple(V4.HB), "layers": lay, "slots": sl}
    return m


pal = dict(PC.palette("Feu")); pal.update(mouth=T8.PAL["mouth"], tongue=T8.PAL["tongue"], throat=T8.PAL["throat"], cheek=pal["skin"], glow=pal["eye"])
nm = sys.argv[1] if len(sys.argv) > 1 else "Gardien"


def variant(hs, fix):
    m = head_on_body(nm, hs)
    if fix:   # queue raccourcie (on comprime tout ce qui est derrière la croupe)
        for n, seg in m.items():
            if n.startswith("Tail"):
                for lay in seg["layers"].values():
                    v = lay.vertices.copy(); z = v[:, 2]
                    v[:, 2] = np.where(z > 5, 5 + (z - 5) * 0.62, z); v[:, 1] = np.where(z > 5, v[:, 1] + (z - 5) * 0.06, v[:, 1])
                    lay.vertices = v
    tete = {k: m.pop(k) for k in ("Head", "Jaw")}
    pb = dict(pal)
    if fix:   # ailes et corps un cran plus sombres que la tête : la tête devient le point focal
        pb.update(membrane="#7E1E12", membrane2="#B8401C", skin="#A8231A", limb="#86190F", spike="#D8601A", crest="#D8601A")
    ph = dict(pal, eye="#FFE14A", glow="#FFE14A")
    return rendu.gather(m, pb, emissive=T8.EMISSIF) + rendu.gather(tete, ph, emissive=T8.EMISSIF)


rows = [(1.1, False, "actuel : tête x1"), (1.6, False, "tête x1,45 seule"),
        (1.6, True, "tête x1,45 + queue -38 % + ailes et corps plus sombres")]
VUES = V4.VUES[:3]
cw, ch = 470, 380
W = Image.new("RGB", (cw*len(VUES), ch*len(rows)), (16,19,28))
dr = ImageDraw.Draw(W); f = ImageFont.truetype(T8.FONT_B, 18)
for i,(s,fix,lab) in enumerate(rows):
    it = variant(s, fix)
    for j,(t,eye,tg,fov) in enumerate(VUES):
        W.paste(rendu.render(it, eye, tg, size=(cw-8,ch-8), fov=fov), (j*cw, i*ch))
    dr.text((12, i*ch+8), lab, font=f, fill=(255,210,122))
W.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comparaison-tete-corps-v8.png"))
