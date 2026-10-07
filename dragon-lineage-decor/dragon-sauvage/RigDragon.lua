-- RigDragon : transforme le dragon importé (Dragon_Sauvage.glb) en modèle animable.
-- À mettre dans un Script (ServerScriptService) ou à lancer une fois dans la barre de commande.
-- Il relie les 21 morceaux par des Motor6D placés aux articulations, puis crée un AnimationController.
-- Le modèle peut avoir été agrandi ou réduit : l'échelle est retrouvée à partir de la largeur du Torso.

local Rig = {}

-- { morceau, parent, pivot (studs, repère d'origine), centre du morceau (repère d'origine) }
local SEGMENTS = {
	{"Torso", nil, Vector3.new(0.000, 5.300, 0.000), Vector3.new(0.000, 5.742, -0.480)},
	{"Neck1", "Torso", Vector3.new(0.000, 6.900, -4.000), Vector3.new(0.001, 7.496, -4.381)},
	{"Neck2", "Neck1", Vector3.new(0.000, 8.300, -5.000), Vector3.new(0.004, 8.837, -5.230)},
	{"Head", "Neck2", Vector3.new(0.000, 9.550, -5.600), Vector3.new(0.003, 10.056, -5.965)},
	{"Jaw", "Head", Vector3.new(0.000, 9.500, -6.000), Vector3.new(-0.001, 9.209, -6.913)},
	{"Eyes", "Head", Vector3.new(0.000, 9.550, -5.600), Vector3.new(-0.001, 10.122, -6.723)},
	{"Tail1", "Torso", Vector3.new(0.000, 5.350, 3.100), Vector3.new(-0.002, 5.097, 4.038)},
	{"Tail2", "Tail1", Vector3.new(0.000, 4.550, 5.200), Vector3.new(0.000, 4.281, 6.088)},
	{"Tail3", "Tail2", Vector3.new(0.000, 3.750, 7.200), Vector3.new(0.001, 3.551, 8.048)},
	{"Tail4", "Tail3", Vector3.new(0.000, 3.150, 9.100), Vector3.new(0.005, 3.124, 10.339)},
	{"FrontUpperLegR", "Torso", Vector3.new(1.620, 4.500, -2.400), Vector3.new(1.671, 3.339, -2.216)},
	{"FrontLowerLegR", "FrontUpperLegR", Vector3.new(1.780, 2.750, -1.850), Vector3.new(1.749, 1.649, -2.686)},
	{"BackUpperLegR", "Torso", Vector3.new(1.420, 4.600, 1.500), Vector3.new(1.509, 3.812, 1.382)},
	{"BackLowerLegR", "BackUpperLegR", Vector3.new(1.620, 2.750, 0.750), Vector3.new(1.622, 1.656, 1.221)},
	{"WingUpperR", "Torso", Vector3.new(1.150, 6.850, -1.850), Vector3.new(3.152, 6.556, 0.509)},
	{"WingLowerR", "WingUpperR", Vector3.new(4.000, 8.150, -0.950), Vector3.new(7.859, 6.980, 1.017)},
	{"FrontUpperLegL", "Torso", Vector3.new(-1.620, 4.500, -2.400), Vector3.new(-1.668, 3.739, -2.246)},
	{"FrontLowerLegL", "FrontUpperLegL", Vector3.new(-1.780, 2.750, -1.850), Vector3.new(-1.749, 1.648, -2.685)},
	{"BackUpperLegL", "Torso", Vector3.new(-1.420, 4.600, 1.500), Vector3.new(-1.507, 3.806, 1.382)},
	{"BackLowerLegL", "BackUpperLegL", Vector3.new(-1.620, 2.750, 0.750), Vector3.new(-1.621, 1.653, 1.219)},
	{"WingUpperL", "Torso", Vector3.new(-1.150, 6.850, -1.850), Vector3.new(-3.156, 6.546, 0.510)},
	{"WingLowerL", "WingUpperL", Vector3.new(-4.000, 8.150, -0.950), Vector3.new(-7.862, 6.978, 1.017)},
}
local TORSO_WIDTH = 4.388

-- Couleur des yeux par lignée ; mets dans texture l'ID de la palette importée (ex. "rbxassetid://123").
Rig.VARIANTS = {
	Feu = { eye = Color3.fromHex("#FFB21C"), texture = "" }, -- rbxassetid de Palette_Feu.png
	Glace = { eye = Color3.fromHex("#8CF4FF"), texture = "" }, -- rbxassetid de Palette_Glace.png
	Foret = { eye = Color3.fromHex("#E2FF57"), texture = "" }, -- rbxassetid de Palette_Foret.png
	Ombre = { eye = Color3.fromHex("#C34BFF"), texture = "" }, -- rbxassetid de Palette_Ombre.png
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
