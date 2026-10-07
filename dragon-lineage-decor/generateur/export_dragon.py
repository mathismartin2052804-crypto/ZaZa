# Exporte le dragon sauvage : GLB découpé + palettes de lignées + manifeste + scripts Roblox + aperçus.
# Usage : python3 generateur/export_dragon.py   (depuis dragon-lineage-decor/)
import json
import os
import sys
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dragon_sauvage as D
import rendu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dragon-sauvage")
CELL, GRID = 16, 4  # palette 64x64 : 4x4 cases de 16 px


def palette_image(colors):
    img = np.zeros((CELL * GRID, CELL * GRID, 3), np.uint8)
    for i, slot in enumerate(D.SLOTS):
        r, c = divmod(i, GRID)
        img[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = (rendu.hex_rgb(colors[slot]) * 255).round()
    return Image.fromarray(img)


def slot_uv(slot):
    r, c = divmod(D.SLOTS.index(slot), GRID)
    return (c + 0.5) / GRID, 1 - (r + 0.5) / GRID  # origine en bas à gauche (trimesh retourne pour le glTF)


def layer_slot(layer):
    return "skin" if layer == "skin" else layer


def segment_mesh(seg):
    meshes = []
    for layer, m in seg["layers"].items():
        m = m.copy()
        uv = np.tile(slot_uv(layer_slot(layer)), (len(m.vertices), 1))
        m.visual = trimesh.visual.TextureVisuals(uv=uv)
        meshes.append(m)
    return trimesh.util.concatenate(meshes)


def main():
    os.makedirs(os.path.join(OUT, "palettes"), exist_ok=True)
    model = D.build()
    feu = D.VARIANTS["Feu"]
    pal = palette_image(feu)
    for name, colors in D.VARIANTS.items():
        palette_image(colors).save(os.path.join(OUT, "palettes", f"Palette_{name}.png"))

    scene = trimesh.Scene()
    tex_mat = PBRMaterial(name="DragonPalette", baseColorTexture=pal, metallicFactor=0.0, roughnessFactor=0.75)
    report = []
    for name, seg in model.items():
        if name == "Eyes":
            m = seg["layers"]["eye"].copy()
            rgb = list(rendu.hex_rgb(feu["eye"]))
            m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
                name="DragonEyes", baseColorFactor=rgb + [1.0], emissiveFactor=rgb, metallicFactor=0.0))
        else:
            m = segment_mesh(seg)
            m.visual.material = tex_mat
        scene.add_geometry(m, node_name=name, geom_name=name)
        lo, hi = m.bounds
        report.append({"name": name, "parent": seg["parent"], "pivot": [round(x, 3) for x in seg["pivot"]],
                       "center": [round(float(x), 3) for x in (lo + hi) / 2],
                       "size": [round(float(x), 3) for x in hi - lo], "tris": int(len(m.faces))})
        print(f"{name:16s} {len(m.faces):5d} tris")
    with open(os.path.join(OUT, "Dragon_Sauvage.glb"), "wb") as fh:
        fh.write(scene.export(file_type="glb", include_normals=True))
    allv = np.concatenate([s.vertices for s in scene.geometry.values()])
    total = sum(r["tris"] for r in report)
    manifest = {"name": "Dragon_Sauvage", "tris": total,
                "size_studs": [round(float(x), 1) for x in allv.max(0) - allv.min(0)],
                "forward": "-Z", "segments": report, "variants": D.VARIANTS,
                "palette_slots": D.SLOTS}
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    write_luau(report)
    print("total", total, "tris, taille", manifest["size_studs"])
    previews(model)


def lua_vec(v):
    return "Vector3.new(%s)" % ", ".join(f"{x:.3f}" for x in v)


def write_luau(report):
    rows = "\n".join(f'\t{{"{r["name"]}", {("nil" if r["parent"] is None else chr(34) + r["parent"] + chr(34))}, '
                     f'{lua_vec(r["pivot"])}, {lua_vec(r["center"])}}},' for r in report)
    torso = next(r for r in report if r["name"] == "Torso")
    colors = "\n".join(f'\t{n} = {{ eye = Color3.fromHex("{c["eye"]}"), texture = "" }}, -- rbxassetid de Palette_{n}.png'
                       for n, c in D.VARIANTS.items())
    src = TEMPLATE.replace("{{ROWS}}", rows).replace("{{TORSO_X}}", f'{torso["size"][0]:.3f}').replace("{{VARIANTS}}", colors)
    with open(os.path.join(OUT, "RigDragon.lua"), "w") as fh:
        fh.write(src)


TEMPLATE = '''-- RigDragon : transforme le dragon importé (Dragon_Sauvage.glb) en modèle animable.
-- À mettre dans un Script (ServerScriptService) ou à lancer une fois dans la barre de commande.
-- Il relie les 21 morceaux par des Motor6D placés aux articulations, puis crée un AnimationController.
-- Le modèle peut avoir été agrandi ou réduit : l'échelle est retrouvée à partir de la largeur du Torso.

local Rig = {}

-- { morceau, parent, pivot (studs, repère d'origine), centre du morceau (repère d'origine) }
local SEGMENTS = {
{{ROWS}}
}
local TORSO_WIDTH = {{TORSO_X}}

-- Couleur des yeux par lignée ; mets dans texture l'ID de la palette importée (ex. "rbxassetid://123").
Rig.VARIANTS = {
{{VARIANTS}}
}

function Rig.build(model: Model)
	local parts, centers = {}, {}
	for _, row in SEGMENTS do
		local p = model:FindFirstChild(row[1], true)
		assert(p and p:IsA("BasePart"), "Morceau introuvable : " .. row[1])
		parts[row[1]] = p
		centers[row[1]] = row[4]
	end
	local scale = parts.Torso.Size.X / TORSO_WIDTH
	for _, row in SEGMENTS do
		local name, parentName, pivot = row[1], row[2], row[3]
		local part = parts[name]
		part.Anchored = parentName == nil -- seul le Torso est ancré ; on le déplace avec PivotTo
		part.CanCollide = false
		part.Massless = parentName ~= nil
		if parentName then
			local parent = parts[parentName]
			local pivotWorld = parent.CFrame * CFrame.new((pivot - centers[parentName]) * scale)
			local m = Instance.new("Motor6D")
			m.Name = name
			m.Part0 = parent
			m.Part1 = part
			m.C0 = parent.CFrame:Inverse() * pivotWorld
			m.C1 = part.CFrame:Inverse() * pivotWorld
			m.Parent = parent
		end
	end
	parts.Eyes.Material = Enum.Material.Neon
	parts.Eyes.CastShadow = false
	model.PrimaryPart = parts.Torso
	if not model:FindFirstChildOfClass("AnimationController") then
		local ac = Instance.new("AnimationController")
		Instance.new("Animator").Parent = ac
		ac.Parent = model
	end
	return parts
end

-- Change la lignée (Feu, Glace, Foret, Ombre) : texture palette + couleur des yeux.
function Rig.setVariant(model: Model, variant: string)
	local v = Rig.VARIANTS[variant]
	assert(v, "Lignée inconnue : " .. tostring(variant))
	for _, p in model:GetDescendants() do
		if p:IsA("MeshPart") then
			if p.Name == "Eyes" then
				p.Color = v.eye
			elseif v.texture ~= "" then
				p.TextureID = v.texture
			end
		end
	end
end

return Rig
'''


def previews(model):
    pose = {"WingUpperR": (0, 0, 28), "WingUpperL": (0, 0, -28), "WingLowerR": (0, 0, -18),
            "WingLowerL": (0, 0, 18), "Neck1": (-12, 8, 0), "Neck2": (8, 10, 0), "Head": (12, 8, 0),
            "Jaw": (-22, 0, 0), "Tail1": (6, -10, 0), "Tail2": (0, -16, 0), "Tail3": (-4, -20, 0),
            "Tail4": (-6, -22, 0), "FrontUpperLegL": (-30, 0, 0), "FrontLowerLegL": (55, 0, 0)}
    W, H = 640, 460
    sheet = Image.new("RGB", (W * 3, H * 2))
    cells = [("Feu", None, (-22, 12, -22)), ("Feu", pose, (-23, 13, -22)), ("Feu", None, (-32, 8, 1)),
             ("Glace", None, (-22, 12, -22)), ("Foret", pose, (-23, 13, -22)), ("Ombre", None, (0, 10, -32))]
    for k, (var, p, eye) in enumerate(cells):
        img = rendu.render(rendu.gather(model, D.VARIANTS[var], p), eye, (1.5, 5.8, 1), size=(W, H), ss=2)
        sheet.paste(img, ((k % 3) * W, (k // 3) * H))
        print("aperçu", k + 1, "/", len(cells), flush=True)
    sheet.save(os.path.join(OUT, "apercu-dragon-sauvage.png"))


if __name__ == "__main__":
    main()
