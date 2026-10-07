-- Teste hors Studio (Lune) les fonctions de jeu de dragon-v6/AnimDragon.lua avec un faux Model :
-- fondus entre animations, setSpeed (repos / marche), décoller / atterrir, enchaînements automatiques, virages
-- (au sol et en vol), contrôle du vol (montée, piqué), lookAt, lignées et particules du souffle, pieds sur le
-- relief (sonde de sol remplacée par des hauteurs connues) ; et LigneesDragon.lua (s'il est passé en 2e argument).
-- Usage : lune run test_runtime_v6.luau ../dragon-v6/AnimDragon.lua ../dragon-v6/LigneesDragon.lua > runtime_v6.json
--         python3 test_runtime_v6.py runtime_v6.json   (contrôle des pieds sur le relief)
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

-- 1. fondus : passer du repos à la marche sans à-coup (et avec à-coup si fondu = 0)
local d = Anim.new(model)
run(d, 1.0)
d:play("Marche")
local doux = maxSaut(d, 0.5)
d = Anim.new(model); run(d, 1.0); d:play("Vol", 0)
local net = maxSaut(d, 0.05)
d = Anim.new(model); d:play("Marche", 0); run(d, 0.5)
local normal = maxSaut(d, 1.7)                  -- mouvement normal de la marche, image par image
check(doux <= 1.5 * normal and net > 3 * normal, ("fondu : saut max %.3f (marche seule %.3f, coupé net vers le vol %.3f)")
	:format(doux, normal, net))

-- 2. setSpeed : repos / marche + cadence ; plus de course
d = Anim.new(model)
d:setSpeed(0); check(d.current == "Repos", "setSpeed(0) -> Repos")
d:setSpeed(3); check(d.current == "Marche" and math.abs(d.rate - 3 / Anim.VITESSE_MARCHE) < 1e-6, "setSpeed(3) -> Marche")
d:setSpeed(12); check(d.current == "Marche" and d.rate == 2, "setSpeed(12) : reste en marche, cadence x2 au plus")
d:setSpeed(0.4); check(d.current == "Marche", "hystérésis : reste en marche à 0,4 stud/s")
d:setSpeed(0.2); check(d.current == "Repos", "s'arrête sous 0,3 stud/s")
check(Anim.VITESSE_COURSE == nil and not pcall(function() d:play("Course") end), "plus d'animation de course")
d:play("Vol"); d:setSpeed(10); check(d.current == "Vol", "setSpeed sans effet en vol")

-- 2b. décoller / atterrir
d = Anim.new(model); d:decoller(); check(d.current == "Decollage", "decoller() -> Decollage")
run(d, 2.1); check(d.current == "Vol" and d:enVol(), "Decollage -> Vol")
d:decoller(); check(d.current == "Vol", "decoller() sans effet en vol")
d:atterrir(); check(d.current == "Atterrissage", "atterrir() -> Atterrissage")
run(d, 1.9); check(d.current == "Repos" and not d:enVol(), "Atterrissage -> Repos")
d:atterrir(); check(d.current == "Repos", "atterrir() sans effet au sol")

-- 2c. vol v2 : la boucle de chaque lignée alterne battements et plané ; montée = bat sans planer, piqué = plane
local function envergure(dd)                   -- hauteur du bout de l'aile droite (rotation de l'épaule, degrés)
	local _, _, z = dd.bones.WingUpperR.Transform:ToEulerAnglesYXZ()
	return math.deg(z)
end
for _, lin in { "Feu", "Glace", "Foret", "Ombre" } do
	d = Anim.new(model, lin); d:play("Vol", 0)
	local dur, mn, mx, plane = d.style.vol.duree, 1e9, -1e9, 0
	for _ = 1, math.floor(dur / DT + 0.5) do
		cb(DT)
		local z = envergure(d)
		mn, mx = math.min(mn, z), math.max(mx, z)
		if d.t > 1 - d.style.vol.plane + 0.08 and d.t < 0.88 then plane = math.max(plane, math.abs(z + 30)) end
	end
	check(mx - mn > 55 and plane < 8, ("vol %s : battement %.0f° (min %.0f / max %.0f), écart au plané %.1f°")
		:format(lin, mx - mn, mn, mx, plane))
end
d = Anim.new(model); d:play("Vol", 0); d:setFlight(20, 12); run(d, 1.5)
check(d.volEffort > 0.6 and d.volPitch > 5, ("montée : effort %.2f, cabré %.1f°"):format(d.volEffort, d.volPitch))
local t0 = d.t; run(d, 1.0)
check((d.t - t0) % 1 > 1 / d.style.vol.duree * 1.2, "montée : il bat plus vite")
d:setFlight(30, -50); run(d, 2.0)
check(d.volForce > 0.8 and d.volPitch < -5, ("piqué : plané forcé %.2f, nez baissé %.1f°"):format(d.volForce, d.volPitch))
local _, yW = d.bones.WingUpperR.Transform:ToEulerAnglesYXZ()
check(math.deg(yW) < -20, ("piqué : ailes balayées vers l'arrière (%.0f°)"):format(math.deg(yW)))
d:setFlight(0, 0); run(d, 2.0)
check(d.volEffort > 0.8 and d.volForce < 0.05, ("sur place : bat sans planer (effort %.2f)"):format(d.volEffort))
d:setFlight(30, 0); run(d, 3.0)
check(d.volEffort < 0.05 and math.abs(d.volPitch) < 0.5, ("croisière : effort %.2f, tangage %.1f°"):format(d.volEffort, d.volPitch))
d:setFlight(nil, nil)
-- montée mesurée sur le Model
d = Anim.new(model); d:play("Vol", 0)
for _ = 1, 90 do pivot = pivot + roblox.Vector3.new(0, 10 * DT, -20 * DT); cb(DT) end
check(d.volEffort > 0.5, ("montée mesurée : effort %.2f"):format(d.volEffort))
pivot = roblox.CFrame.new()

-- 3. enchaînements automatiques
d = Anim.new(model); d:play("SouffleFeu"); run(d, 1.4); check(d.fire > 0.9, "feu allumé au milieu du souffle")
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
-- en vol, il s'incline beaucoup plus dans le virage
local function roulis(anim)                    -- (les faux os sont partagés : on lit avant de créer le suivant)
	local dd = Anim.new(model); dd:play(anim, 0); dd:setTurn(1); run(dd, 1.0)
	local _, _, z1 = bones.Root.Transform:ToEulerAnglesYXZ()
	local dd0 = Anim.new(model); dd0:play(anim, 0); dd0:setTurn(0); run(dd0, 1.0)
	local _, _, z0 = bones.Root.Transform:ToEulerAnglesYXZ()
	return math.deg(z0 - z1)
end
local rv, rm = roulis("Vol"), roulis("Marche")
check(rv > 18 and rm < 8, ("roulis dans le virage : %.0f° en vol, %.0f° en marchant"):format(rv, rm))

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
-- 7. lignées : choix (argument, attribut, nom du Model) et particules du souffle propres à chacune
-- (vraies instances Roblox : Lune vérifie noms et types des propriétés)
check(Anim.new(model).lignee == "Feu", "lignée par défaut : Feu")
check(Anim.new(model, "Ombre").lignee == "Ombre", "lignée passée en argument")
local m2 = setmetatable({ Name = "Dragon_V6_Glace" }, { __index = model })
check(Anim.new(m2).lignee == "Glace", "lignée lue sur le nom du Model")
local m3 = setmetatable({ Name = "Dragon", GetAttribute = function(_, k) return k == "Lignee" and "Foret" or nil end },
	{ __index = model })
check(Anim.new(m3).lignee == "Foret", "lignée lue sur l'attribut Lignee")
local ATTENDU = { Feu = { "Feu", "Braises" }, Glace = { "Givre", "Eclats" }, Foret = { "Spores", "Pollen" },
	Ombre = { "Tenebres", "Volutes" } }
local couleurs = {}
for lin, noms in ATTENDU do
	local head = roblox.Instance.new("Bone"); head.Name = "Head"
	local f = setmetatable({ bones = { Head = head }, style = Anim.LIGNEES[lin] }, Anim)
	f:_creerFeu()
	local os_ = head:FindFirstChild("Souffle")
	local ok_ = os_ and os_.ClassName == "Bone" and os_:FindFirstChildOfClass("PointLight") ~= nil
	for _, n in noms do
		ok_ = ok_ and os_:FindFirstChild(n) ~= nil and os_:FindFirstChild(n).ClassName == "ParticleEmitter"
	end
	check(ok_, "souffle " .. lin .. " : os, émetteurs " .. table.concat(noms, " + ") .. " et lumière créés")
	check(os_.CFrame.LookVector.Z < -0.9 and os_.CFrame.LookVector.Y < 0, "souffle " .. lin .. " : part vers l'avant de la gueule")
	couleurs[lin] = os_:FindFirstChild(noms[1]).Color.Keypoints[2].Value
end
check(couleurs.Feu ~= couleurs.Glace and couleurs.Glace ~= couleurs.Ombre and couleurs.Foret ~= couleurs.Ombre,
	"souffle : couleur différente pour chaque lignée")
check(math.abs(out[2].bassin - 0.1) < 0.01, ("bassin abaissé de la moyenne : %.3f"):format(out[2].bassin))
-- 8. LigneesDragon.lua : caractéristiques et affinités
if process.args[2] then
	local L = luau.load(fs.readFile(process.args[2]), { environment = env })()
	check(#L.LISTE == 4, "LigneesDragon : 4 lignées")
	local cycle = { Feu = "Glace", Glace = "Foret", Foret = "Ombre", Ombre = "Feu" }
	for a, b in cycle do
		check(L.affinite(a, b) == L.AFFINITE_FORT and L.affinite(b, a) == L.AFFINITE_FAIBLE,
			"affinité : " .. a .. " bat " .. b)
	end
	check(L.affinite("Feu", "Foret") == 1 and L.affinite("Feu", "Feu") == 1, "affinité neutre")
	for _, n in L.LISTE do
		local c = L.get(n)
		check(c.stats.vie > 0 and c.souffle.portee > 0 and c.passif.nom and Anim.LIGNEES[n] ~= nil,
			"caractéristiques complètes : " .. n)
		check(c.vitesses.marche <= 2 * Anim.VITESSE_MARCHE + 0.01, ("%s : marche %.1f studs/s atteignable sans patiner")
			:format(n, c.vitesses.marche))
	end
	local sig = {}
	for _, n in L.LISTE do
		local s_ = L.get(n).stats
		sig[n] = ("%d/%d/%d/%d"):format(s_.vie, s_.attaque, s_.defense, s_.vitesse)
	end
	check(sig.Feu ~= sig.Glace and sig.Glace ~= sig.Foret and sig.Foret ~= sig.Ombre and sig.Ombre ~= sig.Feu,
		"stats différentes pour chaque lignée")
end
stdio.ewrite(("runtime : %d contrôles OK, %d échecs ; saut max fondu %.3f / marche seule %.3f / coupé net %.3f\n")
	:format(ok, fails, doux, normal, net))
print(serde.encode("json", out))
if fails > 0 then process.exit(1) end
