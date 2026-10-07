-- Teste hors Studio (Lune) les fonctions de jeu de dragon-v6/AnimDragon.lua avec un faux Model :
-- fondus entre animations, setSpeed (choix de l'allure), enchaînements automatiques, virages, lookAt,
-- pieds sur le relief (sonde de sol remplacée par des hauteurs connues).
-- Usage : lune run test_runtime_v6.luau ../dragon-v6/AnimDragon.lua > runtime_v6.json
--         python3 test_runtime_v6.py ../dragon-v6/Dragon_V6.glb runtime_v6.json   (contrôle des pieds sur le relief)
local roblox = require("@lune/roblox")
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")
local process = require("@lune/process")
local stdio = require("@lune/stdio")
local src = fs.readFile(process.args[1])
local cb
local game = { GetService = function(_, n) return { Heartbeat = { Connect = function(_, f) cb = f; return { Disconnect = function() end } end } } end }
local list, pivot = {}, roblox.CFrame.new()
local model = {}
function model:GetDescendants() return list end
function model:FindFirstChild() return nil end
function model:GetPivot() return pivot end
local env = setmetatable({ game = game, CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Color3 = roblox.Color3,
	Enum = roblox.Enum, typeof = roblox.typeof or typeof, Instance = roblox.Instance, Vector2 = roblox.Vector2,
	NumberRange = roblox.NumberRange, NumberSequence = roblox.NumberSequence,
	NumberSequenceKeypoint = roblox.NumberSequenceKeypoint, ColorSequence = roblox.ColorSequence,
	ColorSequenceKeypoint = roblox.ColorSequenceKeypoint,
	math = setmetatable({ random = function() return 1 end }, { __index = math }) }, { __index = getfenv and getfenv() or _G })
local Anim = luau.load(src, { environment = env })()
local bones = {}
for name in string.gmatch(string.match(src, "local BONES = {(.-)}"), '"(%w+)"') do
	local b = { Name = name, Transform = roblox.CFrame.new() }
	function b:IsA(c) return c == "Bone" end
	table.insert(list, b); bones[name] = b
end

local ok, fails = 0, 0
local function check(cond, msg)
	if cond then ok += 1 else fails += 1; stdio.ewrite("ÉCHEC : " .. msg .. "\n") end
end
local DT = 1 / 60
local function run(d, sec) for _ = 1, math.floor(sec / DT + 0.5) do cb(DT) end end
local function snapshot() local T = {} for n, b in bones do T[n] = { b.Transform:GetComponents() } end return T end
local function saut()                          -- plus grand déplacement d'un sommet d'os d'une image à l'autre
	local m = 0
	for _, b in bones do
		local p0 = b.Transform
		b._p = b._p or p0
		m = math.max(m, (b._p.Position - p0.Position).Magnitude, (b._p.LookVector - p0.LookVector).Magnitude * 3,
			(b._p.UpVector - p0.UpVector).Magnitude * 3)
		b._p = p0
	end
	return m
end
local function maxSaut(d, sec)
	saut()
	local m = 0
	for _ = 1, math.floor(sec / DT + 0.5) do cb(DT); m = math.max(m, saut()) end
	return m
end

-- 1. fondus : passer du repos à la course sans à-coup (et avec à-coup si fondu = 0)
local d = Anim.new(model)
run(d, 1.0)
d:play("Course")
local doux = maxSaut(d, 0.5)
d = Anim.new(model); run(d, 1.0); d:play("Course", 0)
local net = maxSaut(d, 0.05)
d = Anim.new(model); d:play("Course", 0); run(d, 0.5)
local normal = maxSaut(d, 2.2)                  -- mouvement normal de la course, image par image
check(doux <= 1.15 * normal and net > 3 * normal, ("fondu : saut max %.3f (course seule %.3f, coupé net %.3f)")
	:format(doux, normal, net))

-- 2. setSpeed : repos / marche / course + cadence
d = Anim.new(model)
d:setSpeed(0); check(d.current == "Repos", "setSpeed(0) -> Repos")
d:setSpeed(3); check(d.current == "Marche" and math.abs(d.rate - 3 / Anim.VITESSE_MARCHE) < 1e-6, "setSpeed(3) -> Marche")
d:setSpeed(12); check(d.current == "Course" and d.rate <= 1.6, "setSpeed(12) -> Course")
local seuil = (Anim.VITESSE_MARCHE + Anim.VITESSE_COURSE) / 2
d:setSpeed(seuil); check(d.current == "Course", "hystérésis : reste en course au seuil")
d:setSpeed(seuil - 1); check(d.current == "Marche", "repasse à la marche sous le seuil")
d:play("Vol"); d:setSpeed(10); check(d.current == "Vol", "setSpeed sans effet en vol")

-- 3. enchaînements automatiques
d = Anim.new(model); d:play("Decollage"); run(d, 2.1); check(d.current == "Vol", "Decollage -> Vol")
d:play("Atterrissage"); run(d, 1.9); check(d.current == "Repos", "Atterrissage -> Repos")
d:play("SouffleFeu"); run(d, 1.4); check(d.fire > 0.9, "feu allumé au milieu du souffle")
run(d, 1.5); check(d.current == "Repos" and d.fire == 0, "SouffleFeu -> Repos, feu éteint")
d:play("Rugissement"); run(d, 2.3); check(d.current == "Repos", "Rugissement -> Repos")

-- 4. virage imposé à droite : le dos se courbe vers la droite (lacet négatif), la queue part à gauche
d = Anim.new(model); d:play("Marche", 0); d:setTurn(1); run(d, 1.0)
local _, yS1 = bones.Spine.Transform:ToEulerAnglesYXZ()
d = Anim.new(model); d:play("Marche", 0); d:setTurn(0); run(d, 1.0)
local _, yS0 = bones.Spine.Transform:ToEulerAnglesYXZ()
check(yS1 < yS0 - math.rad(3), ("virage : lacet du dos %.1f° contre %.1f° sans virage"):format(math.deg(yS1), math.deg(yS0)))
-- virage mesuré : le Model tourne à droite à 1,5 rad/s
d = Anim.new(model); d:play("Marche", 0)
for _ = 1, 60 do pivot = pivot * roblox.CFrame.Angles(0, -1.5 * DT, 0); cb(DT) end
check(d.turn > 0.4, ("virage mesuré : %.2f"):format(d.turn))
pivot = roblox.CFrame.new()

-- 5. lookAt : cible devant à droite et un peu en haut -> yeux et tête vers la droite et le haut
d = Anim.new(model); d:play("Repos", 0); d:lookAt(roblox.Vector3.new(12, 6, -14)); run(d, 1.5)
check(d.eyeYaw > 0 or d.headYaw > 20, ("lookAt : cap tête %.1f°, yeux %.1f°"):format(d.headYaw, d.eyeYaw))
check(d.headPitch > 0, "lookAt : la tête se lève")
d:lookAt(roblox.Vector3.new(0, 0, 30)); run(d, 2.0)   -- derrière lui : il laisse tomber
check(d.lookW < 0.05, "lookAt : cible derrière -> lâche")
d:lookAt(nil)

-- 6. pieds sur le relief : sol connu sous chaque patte (patte avant droite sur une marche de 0,6 stud)
local SOL = { FrontFootR = 0.6, FrontFootL = 0, BackFootR = -0.2, BackFootL = 0 }
local out = {}
for _, on in { false, true } do
	d = Anim.new(model); d:play("Repos", 0)
	d._sondeSol = function(_, leg) return SOL[leg.foot] end
	d:setGroundIK(on)
	run(d, 1.0)
	d.t = 0.25; d.rate = 0; cb(DT)                     -- même instant pour les deux cas
	table.insert(out, { anim = "Repos", t = d.t, sol = on, T = snapshot(), attendu = SOL, bassin = d.groundShift })
end
-- 7. particules du souffle : vraies instances Roblox (Lune vérifie noms et types des propriétés)
local head = roblox.Instance.new("Bone"); head.Name = "Head"
local feu = setmetatable({ bones = { Head = head }, baseColor = roblox.Color3.fromRGB(127, 244, 255) }, Anim)
feu:_creerFeu()
local os_ = head:FindFirstChild("Souffle")
check(os_ and os_.ClassName == "Bone" and os_:FindFirstChild("Feu") and os_:FindFirstChildOfClass("PointLight"),
	"souffle : os, ParticleEmitter et PointLight créés")
check(os_.CFrame.LookVector.Z < -0.9 and os_.CFrame.LookVector.Y < 0, "souffle : le feu part vers l'avant de la gueule")
check(math.abs(out[2].bassin - 0.1) < 0.01, ("bassin abaissé de la moyenne : %.3f"):format(out[2].bassin))
stdio.ewrite(("runtime : %d contrôles OK, %d échecs ; saut max fondu %.3f / course seule %.3f / coupé net %.3f\n")
	:format(ok, fails, doux, normal, net))
print(serde.encode("json", out))
if fails > 0 then process.exit(1) end
