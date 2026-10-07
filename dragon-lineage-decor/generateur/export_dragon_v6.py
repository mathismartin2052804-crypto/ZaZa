# Exporte le dragon v6 riggé : GLB avec squelette et poids (skinning) + palette + manifeste + script Luau d'animation.
#   Dragon_V6.glb : deux maillages qui partagent le même squelette (42 os)
#     - « Dragon »     : tout le corps, couleurs par face via une petite texture palette
#     - « DragonNeon » : yeux, narines, lame de queue, lueur de gorge (à passer en Neon dans Studio)
#   AnimDragon.lua : animations procédurales (course, vol, rugissement, repos) + yeux (clignement, regard,
#     plisser, pulsation de la lueur), en pilotant Bone.Transform — mêmes formules que demo_animations_v6.py
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
    Nn = Nn[first] / np.maximum(np.linalg.norm(Nn[first], axis=1, keepdims=True), 1e-9)
    return P[first], Nn, UV[first], J[first], W[first], inv[I]


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


def write_luau(rig, path):
    _, _, u, _ = T8.eye_frame(RG.A)
    axR = C6.HEAD_R @ u
    axL = C6.HEAD_R @ np.array([-u[0], u[1], u[2]])
    src = LUA.replace("{{AXE_R}}", lua_vec(axR)).replace("{{AXE_L}}", lua_vec(axL)).replace(
        "{{LID}}", f"{T8.LID_CLOSE:.1f}").replace("{{BONES}}", ", ".join(f'"{b[0]}"' for b in rig.bones))
    with open(path, "w") as fh:
        fh.write(src)


LUA = r'''-- AnimDragon : anime le dragon v6 importé (Dragon_V6.glb) en pilotant ses os (Bone.Transform).
-- Placement : ModuleScript dans ReplicatedStorage ; à utiliser depuis un LocalScript (rendu fluide côté client)
-- ou un Script serveur. Les deux MeshParts (Dragon, DragonNeon) doivent être dans le même Model que les os.
--   local Anim = require(ReplicatedStorage.AnimDragon)
--   local d = Anim.new(workspace.Dragon_V6)
--   d:play("Course")            -- "Course", "Vol", "Rugissement", "Repos"
--   d:blink()                   -- clignement
--   d:look(20)                  -- regard en degrés (+ = vers la droite du dragon)
--   d:squint(0.4)               -- plisser les yeux (0 ouverts, 1 fermés)
-- Mêmes formules que generateur/demo_animations_v6.py (angles en degrés, ordre YXZ, autour de la tête de chaque os).
local RunService = game:GetService("RunService")

local Anim = {}
Anim.__index = Anim

local BONES = { {{BONES}} }
local LID_AXIS = { R = {{AXE_R}}, L = {{AXE_L}} }
local LID_CLOSE = math.rad({{LID}})
local rad, sin, cos, max, abs, clamp = math.rad, math.sin, math.cos, math.max, math.abs, math.clamp
local TAU = 2 * math.pi

local function ease(a, b, t)
	local x = clamp((t - a) / (b - a), 0, 1)
	return x * x * (3 - 2 * x)
end

local function rot(v)
	return CFrame.fromEulerAnglesYXZ(rad(v[1]), rad(v[2]), rad(v[3]))
end

local function sides(P, name, ex, ey, ez)
	P[name .. "R"] = { ex, ey, ez }
	P[name .. "L"] = { ex, -ey, -ez }
end

local function folded(P)
	sides(P, "WingUpper", 0, -38, -22)
	sides(P, "WingLower", 0, -68, 0)
	return P
end

local ANIMS = {}
ANIMS.Course = { duree = 2.2, fn = function(t)
	local w = TAU * 2 * t
	local P = folded({})
	P.Root = { 3 * sin(2 * w), 4 * sin(w), 0 }
	P.Spine = { -5 * sin(2 * w + 0.6), -5 * sin(w + 0.4), 0 }
	P.Chest = { -4 * sin(2 * w + 1.2), -4 * sin(w + 0.8), 0 }
	P.Neck1 = { -6 + 5 * sin(2 * w + 1.8), 3 * sin(w + 1.2), 0 }
	P.Neck2 = { -3 + 3 * sin(2 * w + 2.2), 0, 0 }
	P.Head = { 6 - 6 * sin(2 * w + 2.6), 0, 0 }
	P.Jaw = { -5 - 6 * max(0, sin(2 * w)), 0, 0 }
	for _, s in { { "R", 0, math.pi }, { "L", 0.6, math.pi + 0.6 } } do
		local f, b = w + s[2], w + s[3]
		local sf, sb = max(0, cos(f)), max(0, cos(b))
		P["FrontUpperLeg" .. s[1]] = { 36 * sin(f), 0, 0 }
		P["FrontLowerLeg" .. s[1]] = { 30 * sf, 0, 0 }
		P["FrontFoot" .. s[1]] = { -75 * sf, 0, 0 }
		P["BackUpperLeg" .. s[1]] = { 32 * sin(b) + 4, 0, 0 }
		P["BackLowerLeg" .. s[1]] = { -45 * sb, 0, 0 }
		P["BackFoot" .. s[1]] = { 60 * sb - 10 * (1 - sb), 0, 0 }
	end
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 2 * sin(2 * w - 0.5 * i), 7 * sin(w - 0.7 * i), 0 }
	end
	return P, Vector3.new(0, 0.5 * abs(sin(2 * w)) - 0.25, 0), 0.15
end }

ANIMS.Vol = { duree = 2.2, fn = function(t)
	local p = TAU * 2 * t
	local P = { Root = { -4 + 3 * sin(p + 0.6), 0, 0 }, Spine = { 2 * sin(p + 1.0), 0, 0 }, Chest = { 2 * sin(p + 1.4), 0, 0 },
		Neck1 = { -8 + 3 * sin(p + 1.4), 0, 0 }, Neck2 = { -4 + 2 * sin(p + 1.8), 0, 0 },
		Head = { 8 - 3 * sin(p + 2.2), 0, 0 }, Jaw = { -4, 0, 0 } }
	sides(P, "WingUpper", 0, 4 * cos(p), 38 * sin(p) + 8)
	sides(P, "WingLower", 0, 6 * cos(p), 30 * sin(p - 0.7) - 4)
	for j = 0, 3 do
		sides(P, "WingFinger" .. (j + 1), 0, 3 * j * cos(p - 1.2), 10 * sin(p - 1.3 - 0.2 * j))
	end
	sides(P, "FrontUpperLeg", -22, 0, 0)
	sides(P, "FrontLowerLeg", 48, 0, 0)
	sides(P, "FrontFoot", -35, 0, 0)
	sides(P, "BackUpperLeg", -28 + 3 * sin(p), 0, 0)
	sides(P, "BackLowerLeg", -12, 0, 0)
	sides(P, "BackFoot", -35, 0, 0)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 3 * sin(p - 0.8 * i) + (i == 0 and 3 or 0), 5 * sin(0.5 * p - 0.6 * i), 0 }
	end
	return P, Vector3.new(0, 4.5 - 0.7 * sin(p), 0), 0
end }

ANIMS.Rugissement = { duree = 2.2, boucle = false, fn = function(t)
	local a = ease(0, 0.22, t) * (1 - ease(0.3, 0.42, t))
	local r = ease(0.3, 0.42, t) * (1 - ease(0.82, 0.98, t))
	local sh = r * sin(TAU * t * 14)
	local P = { Root = { 6 * a - 3 * r, 0, 0 }, Spine = { 3 * a, 0, 0 }, Chest = { 3 * a - 2 * r, 0, 0 } }
	for i = 1, 3 do
		P["Neck" .. i] = { 7 * a - 4 * r, 0, 0 }
	end
	P.Head = { 12 * a + 8 * r + 2 * sh, 2 * sh, 0 }
	P.Jaw = { -6 * a - 34 * r, 0, 0 }
	local f = 1 - a - r
	sides(P, "WingUpper", 0, -38 * f - 10 * r, -22 * f + 25 * a + 45 * r)
	sides(P, "WingLower", 0, -68 * f + 8 * r, 10 * a + 25 * r)
	for j = 0, 3 do
		sides(P, "WingFinger" .. (j + 1), 0, (j - 1.5) * 6 * r, 4 * r * sin(TAU * t * 7 + j))
	end
	sides(P, "FrontUpperLeg", -14 * a + 10 * r, 0, 0)
	sides(P, "FrontLowerLeg", 10 * a - 8 * r, 0, 0)
	sides(P, "FrontFoot", 6 * a, 0, 0)
	sides(P, "BackUpperLeg", -6 * a - 6 * r, 0, 0)
	sides(P, "BackLowerLeg", 4 * a, 0, 0)
	sides(P, "BackFoot", 2 * a + 6 * r, 0, 0)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 4 * a + 3 * r, 12 * r * sin(TAU * t * 3 - 0.8 * i), 0 }
	end
	return P, Vector3.new(0, 0.45 * a - 0.15 * r, 0), 0.4 * r, r
end }

ANIMS.Repos = { duree = 4.0, fn = function(t)
	local br = sin(TAU * t)
	local look = 22 * sin(TAU * t + 0.5)
	local P = folded({ Chest = { 1.5 * br, 0, 0 }, Spine = { -br, 0, 0 },
		Neck1 = { 2 * br, 0.3 * look, 0 }, Neck2 = { br, 0.3 * look, 0 }, Neck3 = { 0, 0.2 * look, 0 },
		Head = { -2 * br, 0.2 * look, 0 }, Jaw = { -3 - 3 * max(0, br), 0, 0 } })
	sides(P, "WingUpper", 0, -38, -22 + 2 * br)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 1.5 * sin(TAU * t - 0.5 * i), 6 * sin(TAU * t - 0.6 * i), 0 }
	end
	return P, Vector3.new(0, 0.05 * br, 0), 0, 0, 0.6 * look
end }

function Anim.new(model: Model)
	local self = setmetatable({}, Anim)
	self.model = model
	self.bones = {}
	for _, b in model:GetDescendants() do
		if b:IsA("Bone") then
			self.bones[b.Name] = b
		end
	end
	for _, n in BONES do
		assert(self.bones[n], "Os introuvable : " .. n)
	end
	self.neon = model:FindFirstChild("DragonNeon", true)
	if self.neon then
		self.neon.Material = Enum.Material.Neon
		self.baseColor = self.neon.Color
	end
	self.current, self.t = "Repos", 0
	self.blinkT, self.squintV, self.lookV = math.huge, 0, nil
	self.conn = RunService.Heartbeat:Connect(function(dt)
		self:step(dt)
	end)
	return self
end

function Anim:play(name: string)
	assert(ANIMS[name], "Animation inconnue : " .. tostring(name))
	self.current, self.t = name, 0
end

function Anim:blink()
	self.blinkT = 0
end

function Anim:look(deg: number?)
	self.lookV = deg -- nil : le regard suit l'animation
end

function Anim:squint(v: number)
	self.squintV = clamp(v, 0, 1)
end

function Anim:step(dt)
	local A = ANIMS[self.current]
	self.t += dt / A.duree
	if self.t >= 1 then
		if A.boucle == false then
			self.current, self.t = "Repos", 0
			A = ANIMS.Repos
		else
			self.t %= 1
		end
	end
	local P, off, squint, roar, look = A.fn(self.t)
	-- clignement : à la demande + un au hasard toutes les 3 à 6 s
	self.blinkT += dt
	if self.blinkT > 0.25 and math.random() < dt / 4.5 then
		self.blinkT = 0
	end
	local bl = clamp(1 - abs(self.blinkT - 0.08) / 0.08, 0, 1)
	local lid = max(bl, squint or 0, self.squintV)
	look = self.lookV or look or 0
	for _, s in { "R", "L" } do
		P["Eyelid" .. s] = CFrame.fromAxisAngle(LID_AXIS[s], -LID_CLOSE * lid * (s == "R" and 1 or -1))
		P["Pupil" .. s] = { 0, -look, 0 }
	end
	for _, n in BONES do
		local v = P[n]
		local cf = typeof(v) == "CFrame" and v or (v and rot(v) or CFrame.identity)
		if n == "Root" then
			cf = CFrame.new(off) * cf
		end
		self.bones[n].Transform = cf
	end
	-- lueur des yeux : pulsation lente, plus vive pendant le rugissement
	if self.neon then
		local k = 0.85 + 0.15 * sin(os.clock() * 2.5) + 0.3 * (roar or 0)
		self.neon.Color = Color3.new(math.min(self.baseColor.R * k, 1), math.min(self.baseColor.G * k, 1),
			math.min(self.baseColor.B * k, 1))
	end
end

function Anim:destroy()
	self.conn:Disconnect()
end

return Anim
'''


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
