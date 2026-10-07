# Tête de dragon v8 : planche de recherche de caractère (5 archétypes), de profil et gueule ouverte.
# Pistes tirées des références (familiers Roblox) : grosse arcade lourde au-dessus d'yeux lumineux, grandes formes
# simples, contraste fort, bouche lisible (intérieur sombre, langue, crocs, lueur de gorge).
# Base commune : crâne et mâchoire v6/v7 déformés par archétype ; cornes en lyre v6 inchangées.
#   Gardien    : noble et calme, museau haut et carré, arcade horizontale, gros yeux
#   Prédateur  : museau long et bas, arcade froncée, rangée de crocs, collerettes rabattues
#   Bouledogue : museau court et large, mâchoire énorme en avant, défenses qui remontent
#   Rusé       : museau fin et retroussé, grands yeux, arcade légère, moustaches
#   Ancien     : arcade massive qui couvre les yeux, corne de nez, barbe d'épines
# Usage : python3 tete_v8.py  ->  ../recherche-tetes-v8.png
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import dragon_v3 as V
import rendu
from tete_v5 import section, loft, mesh, blade, sweep, cone, curve, both, mirror, FONT, FONT_B
import tete_v6 as T6
import tete_v7 as T7

HB, HEAD_R, HS = V.HB, V.HEAD_R, V.HS
CRANE, MACHOIRE = T6.CRANE, T6.MACHOIRE
PIVOT_M = np.array([0.0, -0.25, 0.15])        # charnière de la mâchoire (sous l'oreille)

ARCHETYPES = {
    "Gardien": dict(L=1.0, H=1.12, W=1.12, brow=1.0, tilt=0.05, eye=1.15, jl=1.0, jd=1.15, jw=1.08, ub=0.0,
                    nose_up=0.0, frill=1.0,
                    up=[(-2.6, 0.55, 0.11), (-2.15, 0.3, 0.07)], low=[(-2.45, 0.38, 0.08)],
                    texte="noble et calme : museau haut et carré, arcade droite, gros yeux, deux crocs nets"),
    "Prédateur": dict(L=1.35, H=0.86, W=0.84, brow=0.95, tilt=0.38, eye=0.95, jl=1.35, jd=0.9, jw=0.86, ub=0.0,
                      nose_up=-0.08, frill=1.35,
                      up=[(-2.75, 0.5, 0.09), (-2.45, 0.3, 0.06), (-2.2, 0.36, 0.065), (-1.95, 0.24, 0.05), (-1.7, 0.2, 0.05)],
                      low=[(-2.6, 0.34, 0.07), (-2.3, 0.22, 0.05), (-2.0, 0.26, 0.055), (-1.75, 0.18, 0.045)],
                      texte="museau long et bas, arcade froncée, rangée de crocs, collerettes rabattues"),
    "Bouledogue": dict(L=0.6, H=1.25, W=1.45, brow=1.3, tilt=0.15, eye=1.0, jl=0.78, jd=1.7, jw=1.55, ub=0.6,
                       nose_up=0.0, frill=0.85,
                       up=[(-2.55, 0.22, 0.07)], low=[(-2.6, 1.0, 0.15), (-2.15, 0.38, 0.08)],
                       texte="museau court et large, mâchoire énorme en avant, défenses qui remontent"),
    "Rusé": dict(L=1.18, H=0.78, W=0.8, brow=0.6, tilt=-0.18, eye=1.4, jl=1.1, jd=0.8, jw=0.8, ub=-0.05,
                 nose_up=0.32, frill=1.1,
                 up=[(-2.4, 0.4, 0.07)], low=[(-2.5, 0.2, 0.05)],
                 texte="museau fin et retroussé, grands yeux, arcade légère, longues moustaches"),
    "Ancien": dict(L=1.1, H=1.0, W=1.05, brow=2.0, tilt=0.22, eye=0.85, jl=1.15, jd=1.1, jw=1.0, ub=0.0,
                   nose_up=0.0, frill=1.25,
                   up=[(-2.6, 0.5, 0.1), (-2.15, 0.28, 0.07)], low=[(-2.4, 0.3, 0.07)],
                   texte="arcade massive qui ombre les yeux, corne de nez, barbe d'épines"),
}
PAL = dict(V.VARIANTS["Feu"], mouth="#3C0A12", tongue="#D2465A", throat="#FF6A18", glow="#FFC21A")
EMISSIF = ("eye", "glow", "throat")


# ---------- déformations ----------
def _smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def warp_head(P, a):
    """Allonge / élargit / rehausse le museau devant les yeux ; l'arrière du crâne (cornes) ne bouge pas."""
    P = np.array(P, float, ndmin=2).copy()
    x, y, z = P.T
    d = np.clip(-1.0 - z, 0, None)
    f = _smooth(d / 1.0)
    P[:, 0] = x * (1 + f * (a["W"] - 1))
    P[:, 1] = 0.15 + (y - 0.15) * (1 + f * (a["H"] - 1)) + a["nose_up"] * (d / 2.3) ** 2
    P[:, 2] = z - d * (a["L"] - 1)
    return P


def warp_jaw(P, a):
    P = np.array(P, float, ndmin=2).copy()
    x, y, z = P.T
    d = np.clip(-1.0 - z, 0, None)
    f = _smooth(d / 1.0)
    P[:, 0] = x * (1 + (a["jw"] - 1) * (0.45 + 0.55 * f))
    P[:, 1] = np.where(y < -0.2, -0.2 + (y + 0.2) * a["jd"], y)
    P[:, 2] = z - d * (a["jl"] - 1) - a["ub"] * f
    return P


def warped(meshes, fn, a):
    out = []
    for m in meshes:
        m = m.copy()
        m.vertices = fn(m.vertices, a)
        out.append(m)
    return out


def jaw_rot(deg):
    R = rendu.rot(ex=-deg)
    return lambda P: (np.asarray(P, float) - PIVOT_M) @ R.T + PIVOT_M


# ---------- pièces ----------
def eye(c, s, n=(1.0, 0.12, -0.55)):
    """Œil en amande (v6) centré en c, échelle s ; renvoie (œil, pupille) côté droit."""
    n = np.asarray(n, float); n /= np.linalg.norm(n)
    u = np.array([0.33, 0.31, 0.92]); u -= n * (u @ n); u /= np.linalg.norm(u)
    L = 0.98 * s
    v = np.cross(n, u); v /= np.linalg.norm(v)
    v = v if v[1] > 0 else -v
    inner = c - u * L / 2
    rim = [inner] + [inner + u * L * t + v * (0.07 + 0.03 * t) * s for t in (0.25, 0.5, 0.75)] + [inner + u * L]
    rim += [inner + u * L * t - v * 0.17 * s * np.sin(np.pi * t) ** 0.8 for t in (0.75, 0.5, 0.25)]
    rim = [p + n * 0.03 for p in rim]
    cc = c - v * 0.03 * s
    k = len(rim)
    vs = rim + [cc + n * 0.1, cc - n * 0.06]
    fs = [(i, (i + 1) % k, k) for i in range(k)] + [((i + 1) % k, i, k + 1) for i in range(k)]
    pc = cc + n * 0.11
    h, w = 0.15 * s, 0.05 * s
    pv = [pc + v * h, pc + u * w, pc - v * h, pc - u * w, pc + n * 0.02, pc - n * 0.03]
    pf = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)]
    return mesh(vs, fs), mesh(pv, pf), (inner, inner + u * L, n, u)


def brow_ridge(inner, outer, n, size, tilt):
    """Arcade lourde : prisme qui déborde au-dessus de l'œil, vers l'extérieur et l'avant."""
    up = np.array([0.0, 1.0, 0.0])
    a = inner + np.array([-0.04, 0.2 - tilt * 0.3, -0.16])
    b = outer + np.array([0.06, 0.2 + tilt * 0.12, 0.2])
    out = n + np.array([0, 0.25, 0]); out /= np.linalg.norm(out)
    rings = []
    for t in (0.0, 0.35, 0.7, 1.0):
        c = a + (b - a) * t
        bulge = 0.75 + 0.35 * np.sin(np.pi * min(t * 1.2, 1))
        th, ov = 0.16 * size * bulge, 0.3 * size * bulge
        rings.append([c + up * th + out * 0.05, c + out * ov + up * 0.02, c + out * ov * 0.8 - up * th * 0.55,
                      c - out * 0.22 - up * th * 0.3, c - out * 0.25 + up * th * 0.6])
    tip = b + (b - a) / np.linalg.norm(b - a) * 0.35 * size + out * 0.15 + up * 0.08
    return loft(rings, a - (b - a) * 0.08, tip)


def tooth(base, tip, r):
    return cone(base, tip, r, 4)


def tongue(a, fork=False):
    zs = np.array([0.0, -0.6, -1.2, -1.75, -2.1]) * (0.5 + 0.5 * a["jl"])
    ys = [-0.3, -0.27, -0.24, -0.21, -0.15]
    path = curve([(0, y, z) for y, z in zip(ys, zs)], 2)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, 0.7, 1], [0.17, 0.15, 0.06]) * (0.6 + 0.4 * a["jw"])
    m = sweep(path, rad, 6)
    v = m.vertices.copy()
    yc = np.interp(-v[:, 2], -zs, ys)
    v[:, 1] = yc + (v[:, 1] - yc) * 0.35
    v[:, 0] *= 1.25
    m.vertices = v
    out = [m]
    if fork:
        tip = np.array([0, ys[-1], zs[-1]])
        for s in (1, -1):
            out.append(cone(tip, tip + (s * 0.16, 0.04, -0.32), 0.05, 4))
    return out


def head_parts(name, a):
    L = {k: [] for k in ("skin", "horn", "spike", "teeth", "eye", "pupil", "back", "limb", "tip", "glow")}
    rings = [section(z, top, [b, e, c, l], bot) for z, top, b, e, c, l, bot in CRANE]
    skull = loft(rings, T6.NUQUE, T6.BEC)
    slots = T7.slots(skull, "head")
    for i, (cy, ny) in enumerate(zip(skull.triangles_center[:, 1], skull.face_normals[:, 1])):
        if ny < -0.5 and cy < 0.0:
            slots[i] = "mouth"                                    # palais
    L["skin"].append(skull)
    # cornes en lyre v6 + petites cornes de tempe (inchangées)
    path = curve([(0.48, 0.95, -0.35), (0.92, 1.55, -0.1), (1.45, 2.05, 0.3), (1.92, 2.55, 0.85),
                  (1.98, 3.15, 1.2), (1.55, 3.62, 1.05), (1.05, 3.72, 0.75)], 3)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, 0.35, 0.75, 1], [0.5, 0.36, 0.2, 0.04])
    L["horn"] += both(sweep(path, rad, 6, rides=0.14))
    path = curve([(0.82, 0.62, -0.25), (1.35, 0.8, 0.25), (1.8, 0.85, 0.8)], 3)
    L["horn"] += both(sweep(path, np.interp(np.linspace(0, 1, len(path)), [0, 1], [0.17, 0.03]), 5))
    # collerettes de joue (flammes), plus ou moins longues
    specs = [(p, q, tuple(np.add(p, np.subtract(t, p) * a["frill"]))) for p, q, t in T7.JOUES]
    for k, v in T7.frills("Feu", specs).items():
        L.setdefault(k, []).extend(v)
    # crête entre les cornes
    for z, h, l in ((-0.1, 0.42, 0.4), (0.3, 0.32, 0.35)):
        top = T7.crane_at(z, 1)
        L["spike"].append(blade((0, top - 0.02, z - l / 2), (0, top - 0.02, z + l / 2), (0, top + h, z + l * 0.6)))
    # plaques du nez, écailles de joue, narines de braise
    for i, z in enumerate((-1.62, -1.95, -2.28, -2.6, -2.88)):
        top, slope = T7.crane_at(z, 1), (T7.crane_at(z - 0.05, 1) - T7.crane_at(z + 0.05, 1)) / -0.1
        L["back"].append(T7.plate((0, top + 0.01, z), (0, -slope, -1), (0, 1, -slope), 0.42 - i * 0.05, 0.42, 0.06))
    for z, y in ((-0.45, 0.22), (-0.8, 0.2), (-1.15, 0.16), (-1.5, 0.15)):
        cx, _ = T7.crane_at(z, 4)
        L["limb"] += both(T7.plate((cx - 0.02, y, z), (0, -0.15, -1), (1, 0.1, 0), 0.22, 0.34, 0.05))
    top = T7.crane_at(-2.95, 1)
    L["glow"] += both(T7.plate((0.17, top - 0.04, -2.95), (0.3, 0, -1), (0.4, 1, -0.4), 0.08, 0.2, 0.04))
    # crocs du haut, placés sur la lèvre
    for z, ln, r in a["up"]:
        x = T7.crane_at(z, 5)[0] * 0.78
        L["teeth"] += both(tooth((x, -0.06, z), (x + 0.02, -0.06 - ln, z - 0.04), r))
    # traits propres à l'archétype (repère non déformé)
    if name == "Prédateur":       # petites lames le long de l'arête du nez
        for z in (-1.75, -2.1, -2.45):
            t = T7.crane_at(z, 1)
            L["spike"].append(blade((0, t + 0.04, z - 0.12), (0, t + 0.04, z + 0.12), (0, t + 0.3, z + 0.22)))
    elif name == "Ancien":        # corne de nez
        t = T7.crane_at(-2.55, 1)
        L["horn"].append(sweep(curve([(0, t, -2.55), (0, t + 0.35, -2.7), (0, t + 0.75, -2.62)], 2), [0.2, 0.15, 0.1, 0.05, 0.02], 5))
    elif name == "Rusé":          # moustaches qui partent du museau et retombent
        for s in (1, -1):
            p = curve([(s * 0.36, 0.0, -2.75), (s * 0.85, -0.2, -2.55), (s * 1.35, -0.7, -2.1), (s * 1.6, -1.35, -1.55)], 3)
            L["tip"].append(sweep(p, np.interp(np.linspace(0, 1, len(p)), [0, 1], [0.06, 0.015]), 4))
    out = {k: warped(v, warp_head, a) for k, v in L.items() if v}
    # yeux et arcades : placés après la déformation (taille propre à l'archétype)
    c = warp_head((0.70, 0.56, -1.32), a)[0] + np.array([0.04 * (a["eye"] - 1), 0, 0])
    e, p, (inner, outer, n, _) = eye(c, a["eye"])
    out["eye"] = both(e)
    out["pupil"] = both(p)
    out["back"] = out.get("back", []) + both(brow_ridge(inner, outer, n, a["brow"], a["tilt"]))
    return out, {"skin": slots}


def jaw_parts(name, a, open_deg):
    L = {k: [] for k in ("skin", "spike", "teeth", "tip", "tongue", "horn")}
    rings = [section(z, top, [l, s, b], k) for z, top, l, s, b, k in MACHOIRE]
    jaw = loft(rings, T6.ARRIERE_M, T6.MENTON)
    slots = T7.slots(jaw, "jaw")
    for i, ny in enumerate(jaw.face_normals[:, 1]):
        if ny > 0.5:
            slots[i] = "mouth"                                    # plancher de la gueule
    L["skin"].append(jaw)
    specs = [(p, q, tuple(np.add(p, np.subtract(t, p) * a["frill"]))) for p, q, t in T7.MACH]
    for k, v in T7.frills("Feu", specs).items():
        L.setdefault(k, []).extend(v)
    for z, ln, r in a["low"]:
        x = float(np.interp(-z, [-m[0] for m in MACHOIRE], [m[2][0] for m in MACHOIRE])) * 0.78
        L["teeth"] += both(tooth((x, -0.2, z), (x + 0.01, -0.2 + ln, z + 0.03 + 0.1 * (ln > 0.5)), r))
    L["tongue"] += tongue(a, fork=name == "Rusé")
    if name == "Ancien":          # barbe d'épines sous le menton
        for x, z, ln in ((0.0, -2.55, 0.85), (0.2, -2.25, 0.7), (0.32, -1.85, 0.55), (0.0, -2.0, 0.6)):
            b = [blade((x - 0.1, -0.45, z), (x + 0.1, -0.5, z + 0.25), (x * 1.2, -0.45 - ln, z + 0.45), th=0.06)]
            L["horn"] += b if x == 0 else both(b[0])
    out = {k: warped(v, warp_jaw, a) for k, v in L.items() if v}
    J = jaw_rot(open_deg)
    for ms in out.values():
        for m in ms:
            m.vertices = J(m.vertices)
    return out, {"skin": slots}


def mouth_web(a, open_deg):
    """Commissures : membrane de joue entre les lèvres quand la gueule s'ouvre (peau dehors, gueule dedans)
    + lueur au fond de la gorge."""
    J = jaw_rot(open_deg)
    zc = -0.75 * (0.6 + 0.4 * a["L"])
    zs = np.linspace(0.25, zc, 6)
    up, lo = [], []
    for z in zs:
        x, y = T7.crane_at(z, 5)
        up.append(warp_head((x * 0.97, y - 0.02, z), a)[0])
        xj = float(np.interp(-z, [-m[0] for m in MACHOIRE], [m[2][0] for m in MACHOIRE]))
        yj = float(np.interp(-z, [-m[0] for m in MACHOIRE], [m[2][1] for m in MACHOIRE]))
        lo.append(J(warp_jaw((xj * 0.97, yj + 0.02, z), a))[0])
    w = np.linspace(1, 0, len(zs)) ** 0.8
    lo = [u + (l - u) * k for u, l, k in zip(up, lo, w)]
    out = {"skin": [], "mouth": [], "throat": []}
    for off, layer, flip in ((0.0, "skin", False), (-0.05, "mouth", True)):
        vs, fs = [], []
        for u, l in zip(up, lo):
            vs += [u + (off, 0, 0), l + (off, 0, 0)]
        for i in range(len(zs) - 1):
            q = (2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2)
            fs += [(q[0], q[2], q[1]), (q[0], q[3], q[2])] if not flip else [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
        m = trimesh.Trimesh(np.asarray(vs), np.asarray(fs), process=False)
        out[layer] += [m, mirror(m)]
    if open_deg > 0:
        g = trimesh.creation.icosphere(1, 0.3)
        g.vertices *= (1.0, 0.6, 0.9)
        g.vertices += warp_head((0, -0.42, -0.15), a)[0] + (0, -0.1 * open_deg / 30, 0)
        out["throat"].append(g)
    return {k: v for k, v in out.items() if v}


# ---------- assemblage ----------
def build(name, open_deg=0.0):
    a = ARCHETYPES[name]
    N = T6.neck_layers("Feu")
    model = {"Neck": {"parent": None, "pivot": tuple(V.NECK[0]),
                      "layers": {k: T7.finish(m, False) for k, m in N.items()}, "slots": {"skin": T7.slots(N["skin"], "neck")}}}
    hp, hs = head_parts(name, a)
    web = mouth_web(a, open_deg)
    for k, v in web.items():
        hp.setdefault(k if k != "skin" else "cheek", []).extend(v)
    jp, js = jaw_parts(name, a, open_deg)
    for part, layers, sl in (("Head", hp, hs), ("Jaw", jp, js)):
        model[part] = {"parent": None, "pivot": tuple(HB),
                       "layers": {k: T7.finish(trimesh.util.concatenate(v)) for k, v in layers.items()}, "slots": sl}
    return model


def silhouette(model, eye, target, size):
    noir = {k: "#000000" for k in list(PAL) + ["cheek", "glow"]}
    img = rendu.render(rendu.gather(model, noir, emissive=()), eye, target, size=size, fov=31,
                       bg=("#ffffff", "#ffffff"))
    m = np.asarray(img).min(axis=-1) < 235
    out = np.full(m.shape + (3,), 236, np.uint8)
    out[m] = (18, 18, 22)
    return Image.fromarray(out)


def main():
    pal = dict(PAL, cheek=PAL["skin"])
    hc = HB + HEAD_R @ np.array([0, 1.25, -1.0]) * HS
    vues = [("Profil", np.array([-17.0, 0.6, 0.0]), 0), ("Profil, gueule ouverte", np.array([-17.0, 0.6, 0.0]), 32),
            ("3/4 avant, gueule ouverte", np.array([-10.0, 0.8, -13.0]), 32), ("Face", np.array([0.0, 1.2, -16.5]), 0)]
    noms = list(ARCHETYPES)
    cw, ch, lw = 380, 320, 250
    sh = 230
    W, H = lw + cw * len(vues) + 10, 104 + ch * len(noms) + 50 + sh + 110
    board = Image.new("RGB", (W, H), (16, 19, 28))
    dr = ImageDraw.Draw(board)
    f = lambda s, b=False: ImageFont.truetype(FONT_B if b else FONT, s)
    dr.text((24, 18), "Dragon — tête v8 : recherche de caractère (Feu)", font=f(32, True), fill=(230, 232, 240))
    dr.text((24, 62), "Même crâne v7 déformé par archétype, cornes en lyre conservées ; arcade lourde au-dessus d'yeux "
                      "lumineux ; gueule ouverte : palais sombre, langue, crocs, lueur de gorge.", font=f(17), fill=(150, 160, 184))
    sils = []
    for i, nm in enumerate(noms):
        y0 = 100 + i * ch
        models = {d: build(nm, d) for d in sorted({v[2] for v in vues})}
        dr.text((20, y0 + 18), nm, font=f(24, True), fill=(230, 232, 240))
        yy, cur = y0 + 58, ""
        for w in ARCHETYPES[nm]["texte"].split():
            if len(cur) + len(w) > 26:
                dr.text((20, yy), cur, font=f(15), fill=(180, 186, 204)); yy += 21; cur = w
            else:
                cur = (cur + " " + w).strip()
        dr.text((20, yy), cur, font=f(15), fill=(180, 186, 204))
        n_tris = sum(len(x.faces) for k in ("Head", "Jaw") for x in models[0][k]["layers"].values())
        dr.text((20, yy + 32), f"{n_tris} triangles (tête + mâchoire)", font=f(13), fill=(140, 150, 172))
        for j, (t, off, d) in enumerate(vues):
            it = rendu.gather(models[d], pal, emissive=EMISSIF)
            tg = hc - (0, 0.7, 0) if j == 2 else hc
            board.paste(rendu.render(it, tg + off, tg, size=(cw - 8, ch - 8), fov=30), (lw + j * cw, y0))
            if i == 0:
                dr.text((lw + j * cw + 12, y0 + 8), t, font=f(16, True), fill=(255, 210, 122))
        sils.append(silhouette(models[0], hc + vues[0][1], hc, ((W - 40) // len(noms) - 10, sh - 10)))
        print(nm, n_tris, flush=True)
    ys = 100 + ch * len(noms) + 20
    dr.text((24, ys), "Silhouettes de profil (même échelle) — chaque tête doit se reconnaître en noir", font=f(18, True),
            fill=(230, 232, 240))
    sw = (W - 40) // len(noms)
    for k, (nm, s) in enumerate(zip(noms, sils)):
        board.paste(s, (20 + k * sw, ys + 34))
        ImageDraw.Draw(board).text((30 + k * sw, ys + 40), nm, font=f(15, True), fill=(200, 60, 40))
    notes = ["Prochaine étape : choisir 1 archétype (ou en mélanger 2) ; puis corps taillé (facettes, os saillants, contre-ombrage).",
             "Les pièces de la tête sont encore posées les unes sur les autres : la fusion booléenne se fera sur la version retenue."]
    for k, t in enumerate(notes):
        dr.text((24, H - 80 + k * 27), "•  " + t, font=f(16), fill=(200, 206, 222))
    board.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recherche-tetes-v8.png"))


if __name__ == "__main__":
    main()
