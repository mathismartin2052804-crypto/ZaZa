-- Exécute dragon-v6/AnimDragon.lua hors Studio (Lune, https://github.com/lune-org/lune) avec un faux Model
-- et imprime en JSON les Bone.Transform obtenus pour quelques instants de chaque animation.
-- Usage : lune run verif_anim_v6.luau ../dragon-v6/AnimDragon.lua > anim_v6.json  (puis verif_glb_v6.py)
-- Le faux Model n'a pas de Name ni d'attribut : la lignée est passée à Anim.new.
local roblox = require("@lune/roblox")
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")
local process = require("@lune/process")
local src = fs.readFile(process.args[1])
local cb
local game = { GetService = function(_, n) return { Heartbeat = { Connect = function(_, f) cb = f; return { Disconnect = function() end } end } } end }
local bones, list = {}, {}
local model = {}
function model:GetDescendants() return list end
function model:FindFirstChild() return nil end
local env = setmetatable({ game = game, CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Color3 = roblox.Color3,
	Instance = roblox.Instance,
	Enum = roblox.Enum, typeof = roblox.typeof or typeof,
	math = setmetatable({ random = function() return 1 end }, { __index = math }) }, { __index = getfenv and getfenv() or _G })
local Anim = luau.load(src, { environment = env })()
-- crée les os à partir de la liste BONES lue dans la source
for name in string.gmatch(string.match(src, "local BONES = {(.-)}"), '"(%w+)"') do
	local b = { Name = name, Transform = nil }
	function b:IsA(c) return c == "Bone" end
	table.insert(list, b); bones[name] = b
end
local out = {}
local DUREES = { Marche = 1.7, Rugissement = 2.2, Repos = 4.0, Decollage = 2.0, Atterrissage = 1.8, SouffleFeu = 2.8 }
local CAS = { { "Marche", 0.21 }, { "Marche", 0.77 }, { "Vol", 0.125 }, { "Vol", 0.41 }, { "Vol", 0.62 }, { "Vol", 0.83 },
	{ "Rugissement", 0.12 }, { "Rugissement", 0.6 }, { "Repos", 0.0625 }, { "Repos", 0.45 }, { "Repos", 0.66 },
	{ "Repos", 0.887 }, { "Decollage", 0.3 }, { "Decollage", 0.55 }, { "Decollage", 0.93 }, { "Atterrissage", 0.2 },
	{ "Atterrissage", 0.6 }, { "SouffleFeu", 0.25 }, { "SouffleFeu", 0.6 } }
-- toutes les animations pour chaque lignée (le vol dépend du style de la lignée ; les maillages diffèrent)
for _, lin in { "Feu", "Glace", "Foret", "Ombre" } do
	for _, case in CAS do
		local d = Anim.new(model, lin)
		d:play(case[1])
		d.blinkT = 10
		cb(case[2] * (case[1] == "Vol" and d.style.vol.duree or DUREES[case[1]]))
		local T = {}
		for n, b in bones do T[n] = { b.Transform:GetComponents() } end
		table.insert(out, { lignee = lin, anim = case[1], t = case[2], T = T })
	end
end
print(serde.encode("json", out))
