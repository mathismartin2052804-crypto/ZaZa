# Exporte le dragon v6 riggé : GLB avec squelette et poids (skinning) + palette + manifeste + script Luau d'animation.
#   Dragon_V6.glb : deux maillages qui partagent le même squelette (42 os)
#     - « Dragon »     : tout le corps, couleurs par face via une petite texture palette
#     - « DragonNeon » : yeux, narines, lame de queue, lueur de gorge (à passer en Neon dans Studio)
#   AnimDragon.lua : animations procédurales (course, vol, rugissement, repos) + yeux (clignement, regard,
#     plisser, pulsation de la lueur), en pilotant Bone.Transform — mêmes formules que demo_animations_v6.py ;
#     la course y est copiée sous forme de table (angles des pattes calculés par IK dans course_v6.py)
# Le glTF est écrit à la main (pas de dépendance) ; repères de repos des os alignés sur le modèle (-Z = avant).
# Usage (depuis dragon-lineage-decor/) : python3 generateur/export_dragon_v6.py  ->  dragon-v6/
import json
import os
import struct
import sys
import io
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rendu
import rig_v6 as RG
import corps_v6 as C6
import tete_v8 as T8
import allures_v6 as AL
import demo_animations_v6 as D
import sequences_v6 as SQ

NAME = "Dragon_V6"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dragon-v6")
NEON = set(C6.EMISSIF)
CELL = 16


# ---------- palette ----------
def slots_used(rig):
    used = []
    for part, layer, V, Nn, F, slots, idx, w in rig.layers:
        for s in (slots if slots is not None else [layer]):
            if s not in used:
                used.append(s)
    return used


def palette_image(slots, pal, grid):
    img = np.zeros((CELL * grid, CELL * grid, 3), np.uint8)
    for i, s in enumerate(slots):
        r, c = divmod(i, grid)
        img[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = (rendu.hex_rgb(pal.get(s) or pal["eye"]) * 255).round()
    return Image.fromarray(img)


# ---------- maillages ----------
def gather(rig, neon, slots, grid):
    """Sommets (position, normale, uv, os, poids) dédoublonnés + indices, pour les couches lumineuses ou non."""
    P, Nn, UV, J, W, I = [], [], [], [], [], []
    base = 0
    for part, layer, V, N_, F, sl, idx, w in rig.layers:
        if (layer in NEON) != neon:
            continue
        fs = np.asarray(F)
        uv = np.zeros((len(V), 2))
        names = sl if sl is not None else [layer] * len(fs)
        for fi, f in enumerate(fs):
            r, c = divmod(slots.index(names[fi]), grid)
            uv[f] = ((c + 0.5) / grid, (r + 0.5) / grid)          # glTF : origine des UV en haut à gauche
        P.append(V); Nn.append(N_); UV.append(uv); J.append(idx); W.append(w); I.append(fs + base)
        base += len(V)
    P, Nn, UV, J, W, I = (np.concatenate(x) for x in (P, Nn, UV, J, W, I))
    key = np.concatenate([P.round(4), Nn.round(3), UV.round(4)], 1)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    P, I = P[first], inv[I]
    T = P[I]
    area = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    I = I[area > 1e-8]                                             # triangles plats : refusés par le validateur glTF
    Nn = Nn[first]
    ln = np.linalg.norm(Nn, axis=1)
    Nn[ln < 1e-6] = (0, 1, 0)                                      # normale nulle (sommet isolé) : valeur par défaut
    Nn = Nn / np.linalg.norm(Nn, axis=1, keepdims=True)
    return P, Nn, UV[first], J[first], W[first], I


class Glb:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors = [], []

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin += data
        self.views.append(v)
        return len(self.views) - 1

    def accessor(self, arr, ctype, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        a = {"bufferView": self.view(arr.tobytes(), target), "componentType": ctype, "count": len(arr), "type": typ}
        if minmax:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        self.accessors.append(a)
        return len(self.accessors) - 1


def build_glb(rig, pal):
    slots = slots_used(rig)
    grid = int(np.ceil(np.sqrt(len(slots))))
    tex = palette_image(slots, pal, grid)
    g = Glb()
    bones = rig.bones
    # nœuds : os (translation relative au parent), puis les deux maillages
    nodes = []
    for name, parent, head, _ in bones:
        ph = np.zeros(3) if parent is None else np.asarray(bones[rig.index[parent]][2], float)
        nodes.append({"name": name, "translation": (np.asarray(head, float) - ph).tolist()})
    for i, (name, parent, *_rest) in enumerate(bones):
        if parent is not None:
            nodes[rig.index[parent]].setdefault("children", []).append(i)
    ibm = np.stack([np.eye(4) for _ in bones])
    for i, (_, _, head, _) in enumerate(bones):
        ibm[i, :3, 3] = -np.asarray(head, float)
    ibm_acc = g.accessor(ibm.transpose(0, 2, 1).reshape(-1, 16).astype(np.float32), 5126, "MAT4")
    buf = io.BytesIO(); tex.save(buf, "PNG")
    img_view = g.view(buf.getvalue())
    eye = list(rendu.hex_rgb(pal["eye"]))
    materials = [{"name": "DragonPalette", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0,
                                                                     "roughnessFactor": 0.75}},
                 {"name": "DragonNeon", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0},
                  "emissiveFactor": eye}]
    meshes, report = [], {}
    for mi, (mname, neon) in enumerate((("Dragon", False), ("DragonNeon", True))):
        P, Nn, UV, J, W, I = gather(rig, neon, slots, grid)
        attrs = {"POSITION": g.accessor(P.astype(np.float32), 5126, "VEC3", 34962, True),
                 "NORMAL": g.accessor(Nn.astype(np.float32), 5126, "VEC3", 34962),
                 "TEXCOORD_0": g.accessor(UV.astype(np.float32), 5126, "VEC2", 34962),
                 "JOINTS_0": g.accessor(J.astype(np.uint8), 5121, "VEC4", 34962),
                 "WEIGHTS_0": g.accessor(W.astype(np.float32), 5126, "VEC4", 34962)}
        meshes.append({"name": mname, "primitives": [{"attributes": attrs, "material": mi,
                                                      "indices": g.accessor(I.ravel().astype(np.uint32), 5125, "SCALAR", 34963)}]})
        nodes.append({"name": mname, "mesh": mi, "skin": 0})
        report[mname] = {"vertices": int(len(P)), "triangles": int(len(I))}
    gltf = {"asset": {"version": "2.0", "generator": "dragon-lineage export_dragon_v6.py"},
            "scene": 0, "scenes": [{"nodes": [rig.index["Root"], len(bones), len(bones) + 1]}],
            "nodes": nodes, "meshes": meshes, "materials": materials,
            "skins": [{"name": "DragonSkeleton", "joints": list(range(len(bones))), "skeleton": rig.index["Root"],
                       "inverseBindMatrices": ibm_acc}],
            "images": [{"bufferView": img_view, "mimeType": "image/png"}],
            "samplers": [{"magFilter": 9728, "minFilter": 9728}], "textures": [{"sampler": 0, "source": 0}],
            "accessors": g.accessors, "bufferViews": g.views, "buffers": [{"byteLength": len(g.bin)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binb = bytes(g.bin) + b"\0" * (-len(g.bin) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binb), 0x004E4942) + binb
    return out, slots, grid, tex, report


# ---------- script Luau ----------
def lua_vec(v):
    return "Vector3.new(%s)" % ", ".join(f"{x:.4f}" for x in v)


def lua_table(nom, A, periodique):
    rows = ",\n".join("\t\t{ " + ", ".join(np.format_float_positional(x, trim="-") for x in r) + " }"
                      for r in A.table)
    head = f'\t{nom} = {{ duree = {A.duree}, periodique = {str(periodique).lower()}, '
    if periodique:
        head += f"foulees = {A.foulees}, vitesse = {A.vitesse:.3f}, sol = true, "
    else:
        head += f'suite = "{A.suite}", sol = {str(A.sol).lower()}, '
    bones = ", ".join(f'"{b}"' for b in A.bones)
    return head + f"bones = {{ {bones} }},\n\t\trows = {{\n{rows}\n\t\t}} }},"


def lua_pattes(sk):
    rest = {b[0]: np.asarray(b[2], float) for b in sk.bones}
    out = []
    for kind in ("Front", "Back"):
        for sd in ("R", "L"):
            up, low, foot = (kind + n + sd for n in ("UpperLeg", "LowerLeg", "Foot"))
            S, E, W = rest[up], rest[low], rest[foot]
            a, b = (E - S)[1:], (W - E)[1:]
            sens = np.sign(a[0] * (W - S)[2] - a[1] * (W - S)[1])
            griffe = np.array([W[0], AL.SOL, AL.PIVOT_Z[kind]]) - W
            out.append(f'\t{kind}{sd} = {{ up = "{up}", low = "{low}", foot = "{foot}", l1y = {a[0]:.4f}, l1z = {a[1]:.4f}, '
                       f"l2y = {b[0]:.4f}, l2z = {b[1]:.4f}, l1 = {np.linalg.norm(a):.4f}, l2 = {np.linalg.norm(b):.4f}, "
                       f"sens = {int(sens)}, griffe = {lua_vec(griffe)} }},")
    return "\n".join(out)


def write_luau(rig, path):
    _, _, u, _ = T8.eye_frame(RG.A)
    axR = C6.HEAD_R @ u
    axL = C6.HEAD_R @ np.array([-u[0], u[1], u[2]])
    sk = AL._Os()
    root = np.asarray(sk.bones[sk.index["Root"]][2], float)
    hb = np.asarray(C6.HB, float)
    bouche = RG.hl((0, -0.15, -2.75)) - hb                          # entre les mâchoires, relatif à l'os Head
    dirb = RG.hl((0, -0.15, -3.75)) - RG.hl((0, -0.15, -2.75))
    tables = [lua_table(n, A, True) for n, A in AL.ALLURES.items()]
    tables += [lua_table(n, S, False) for n, S in SQ.SEQUENCES.items()]
    sac = ", ".join("{ %g, %g, %g }" % s for s in D.SACCADES)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "AnimDragon_modele.lua")).read()
    for k, v in {"AXE_R": lua_vec(axR), "AXE_L": lua_vec(axL),
                 "PUP_R": lua_vec(RG.pupil_axis("R")), "PUP_L": lua_vec(RG.pupil_axis("L")),
                 "LID": f"{T8.LID_CLOSE:.1f}", "BONES": ", ".join(f'"{b[0]}"' for b in rig.bones),
                 "SACCADES": sac, "SOL_ROOT": f"{AL.SOL - root[1]:.4f}",
                 "BOUCHE": f"CFrame.lookAt({lua_vec(bouche)}, {lua_vec(bouche + dirb / np.linalg.norm(dirb))})",
                 "PATTES": lua_pattes(sk), "TABLES": "\n".join(tables)}.items():
        assert "{{" + k + "}}" in src, k
        src = src.replace("{{" + k + "}}", v)
    assert "{{" not in src
    with open(path, "w") as fh:
        fh.write(src)


def main():
    os.makedirs(OUT, exist_ok=True)
    rig = RG.Rig()
    data, slots, grid, tex, report = build_glb(rig, C6.PAL)
    with open(os.path.join(OUT, NAME + ".glb"), "wb") as fh:
        fh.write(data)
    tex.save(os.path.join(OUT, "Palette_Feu.png"))
    write_luau(rig, os.path.join(OUT, "AnimDragon.lua"))
    manifest = {"name": NAME, "forward": "-Z", "up": "+Y", "units": "studs",
                "bones": [{"name": b[0], "parent": b[1], "head": [round(float(x), 3) for x in b[2]]} for b in rig.bones],
                "meshes": report, "palette_slots": slots, "palette_grid": grid,
                "neon_layers": sorted(NEON), "max_influences": 4}
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    print(json.dumps(report), len(rig.bones), "os", len(data) // 1024, "Ko")


if __name__ == "__main__":
    main()
