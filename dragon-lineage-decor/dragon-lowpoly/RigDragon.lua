-- RigDragon : transforme le dragon importé (Dragon_LowPoly.glb) en modèle animable.
-- À mettre dans un Script (ServerScriptService) ou à lancer une fois dans la barre de commande.
-- Il relie tous les morceaux par des Motor6D placés aux articulations, puis crée un AnimationController.
-- Le modèle peut avoir été agrandi ou réduit : l'échelle est retrouvée à partir de la largeur du Torso.

local Rig = {}

-- { morceau, parent, pivot (studs, repère d'origine), centre du morceau (repère d'origine) }
local SEGMENTS = {
	{"Torso", nil, Vector3.new(0.000, 5.300, 0.000), Vector3.new(-0.002, 6.034, -0.509)},
	{"ChestGem", "Torso", Vector3.new(0.000, 5.750, -4.500), Vector3.new(0.006, 5.748, -4.644)},
	{"Neck1", "Torso", Vector3.new(0.000, 6.900, -4.000), Vector3.new(-0.002, 7.571, -4.404)},
	{"Neck2", "Neck1", Vector3.new(0.000, 8.300, -5.000), Vector3.new(0.002, 8.900, -5.275)},
	{"Head", "Neck2", Vector3.new(0.000, 9.550, -5.600), Vector3.new(0.009, 10.220, -6.096)},
	{"Jaw", "Head", Vector3.new(0.000, 9.485, -6.120), Vector3.new(0.008, 9.168, -7.317)},
	{"Eyes", "Head", Vector3.new(0.000, 9.550, -5.600), Vector3.new(-0.011, 10.291, -7.037)},
	{"Tail1", "Torso", Vector3.new(0.000, 5.350, 3.100), Vector3.new(0.004, 5.138, 4.039)},
	{"Tail2", "Tail1", Vector3.new(0.000, 4.550, 5.200), Vector3.new(-0.000, 4.284, 6.091)},
	{"Tail3", "Tail2", Vector3.new(0.000, 3.750, 7.200), Vector3.new(-0.000, 3.575, 8.047)},
	{"Tail4", "Tail3", Vector3.new(0.000, 3.150, 9.100), Vector3.new(0.007, 3.132, 10.345)},
	{"FrontUpperLegR", "Torso", Vector3.new(1.620, 4.500, -2.400), Vector3.new(1.661, 3.736, -2.240)},
	{"FrontLowerLegR", "FrontUpperLegR", Vector3.new(1.780, 2.750, -1.850), Vector3.new(1.748, 1.646, -2.643)},
	{"BackUpperLegR", "Torso", Vector3.new(1.420, 4.600, 1.500), Vector3.new(1.525, 3.826, 1.360)},
	{"BackLowerLegR", "BackUpperLegR", Vector3.new(1.620, 2.750, 0.750), Vector3.new(1.622, 1.660, 1.199)},
	{"WingUpperR", "Torso", Vector3.new(1.150, 6.850, -1.850), Vector3.new(3.716, 6.438, 0.783)},
	{"WingLowerR", "WingUpperR", Vector3.new(4.000, 8.150, -0.950), Vector3.new(8.144, 7.010, 0.968)},
	{"WingGlowR", "WingLowerR", Vector3.new(6.800, 8.950, -1.550), Vector3.new(9.465, 6.765, 1.602)},
	{"FrontUpperLegL", "Torso", Vector3.new(-1.620, 4.500, -2.400), Vector3.new(-1.675, 3.723, -2.251)},
	{"FrontLowerLegL", "FrontUpperLegL", Vector3.new(-1.780, 2.750, -1.850), Vector3.new(-1.752, 1.651, -2.653)},
	{"BackUpperLegL", "Torso", Vector3.new(-1.420, 4.600, 1.500), Vector3.new(-1.515, 3.810, 1.371)},
	{"BackLowerLegL", "BackUpperLegL", Vector3.new(-1.620, 2.750, 0.750), Vector3.new(-1.618, 1.660, 1.219)},
	{"WingUpperL", "Torso", Vector3.new(-1.150, 6.850, -1.850), Vector3.new(-3.715, 6.431, 0.796)},
	{"WingLowerL", "WingUpperL", Vector3.new(-4.000, 8.150, -0.950), Vector3.new(-8.127, 7.011, 0.973)},
	{"WingGlowL", "WingLowerL", Vector3.new(-6.800, 8.950, -1.550), Vector3.new(-9.465, 6.769, 1.633)},
}
local TORSO_WIDTH = 5.013
-- Morceaux lumineux (yeux, gemme, bout des ailes) : Neon, couleur de la lignée.
local NEON = { "ChestGem", "Eyes", "WingGlowR", "WingGlowL" }

-- Couleur des yeux par lignée ; mets dans texture l'ID de la palette importée (ex. "rbxassetid://123").
Rig.VARIANTS = {
	Feu = { eye = Color3.fromHex("#FF7A1A"), texture = "" }, -- rbxassetid de Palette_Feu.png
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
	for _, n in NEON do
		parts[n].Material = Enum.Material.Neon
		parts[n].CastShadow = false
	end
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
			if table.find(NEON, p.Name) then
				p.Color = v.eye
			elseif v.texture ~= "" then
				p.TextureID = v.texture
			end
		end
	end
end

return Rig
