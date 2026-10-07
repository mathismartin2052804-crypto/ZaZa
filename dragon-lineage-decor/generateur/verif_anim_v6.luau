-- Exécute dragon-v6/AnimDragon.lua hors Studio (Lune, https://github.com/lune-org/lune) avec un faux Model
-- et imprime en JSON les Bone.Transform obtenus pour quelques instants de chaque animation.
-- Usage : lune run verif_anim_v6.luau ../dragon-v6/AnimDragon.lua > anim_v6.json  (puis verif_glb_v6.py)
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
for _, case in { { "Course", 0.1 }, { "Course", 0.37 }, { "Course", 0.8113 }, { "Vol", 0.125 }, { "Vol", 0.62 },
	{ "Rugissement", 0.12 }, { "Rugissement", 0.6 }, { "Repos", 0.0625 }, { "Repos", 0.45 }, { "Repos", 0.66 },
	{ "Repos", 0.887 } } do
	local d = Anim.new(model)
	d:play(case[1])
	d.blinkT = 10
	cb(case[2] * ({ Course = 2.2, Vol = 2.2, Rugissement = 2.2, Repos = 4.0 })[case[1]])
	local T = {}
	for n, b in bones do T[n] = { b.Transform:GetComponents() } end
	table.insert(out, { anim = case[1], t = case[2], T = T })
end
print(serde.encode("json", out))
