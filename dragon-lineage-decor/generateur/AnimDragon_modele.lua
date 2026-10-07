-- AnimDragon : anime le dragon v6 importé (Dragon_V6*.glb) en pilotant ses os (Bone.Transform).
-- Fichier généré par generateur/export_dragon_v6.py à partir de generateur/AnimDragon_modele.lua : modifier le modèle.
-- Placement : ModuleScript dans ReplicatedStorage ; à utiliser depuis un LocalScript (rendu fluide côté client)
-- ou un Script serveur. Les deux MeshParts (Dragon, DragonNeon) doivent être dans le même Model que les os.
--   local Anim = require(ReplicatedStorage.AnimDragon)
--   local d = Anim.new(workspace.Dragon_V6_Glace)   -- lignée lue sur l'attribut « Lignee » ou le nom du Model
--   d:play("Marche")            -- "Repos", "Marche", "Vol", "Rugissement", "Decollage", "Atterrissage",
--                               -- "SouffleFeu" (fondu de 0,25 s ; d:play(nom, 0) pour couper net)
--   d:setSpeed(v)               -- au sol : Repos ou Marche selon la vitesse (studs/s), cadence calée sur v
--   d:follow(humanoid)          -- pareil, branché sur Humanoid.Running
--   d:decoller() ; d:atterrir() -- pas de course : pour aller vite, il décolle et vole
--   d:setFlight(v, montee)      -- en vol : vitesse et vitesse verticale (studs/s) ; nil : mesurées sur le Model
--   d:lookAt(cible)             -- suit du regard un Vector3, une BasePart ou un Model (nil : rend la main)
--   d:setTurn(x)                -- virage de -1 (gauche) à 1 (droite) ; nil : mesuré tout seul sur le Model
--   d:setGroundIK(true)         -- pieds posés sur le relief (rayons sous chaque patte)
--   d:blink() ; d:squint(0.4) ; d:look(20, 5)   -- clignement, plisser les yeux, regard imposé (degrés)
-- Mêmes poses que les scripts Python du générateur (angles en degrés, ordre YXZ, autour de la tête de chaque os) ;
-- marche, décollage, atterrissage et souffle de feu sont copiés sous forme de tables (allures_v6.py,
-- sequences_v6.py : pattes calculées par cinématique inverse pour que les pieds restent au sol) ; le vol v2 est
-- calculé ici comme dans demo_animations_v6.vol, avec le style de vol de la lignée (lignees_v6.STYLE).
local RunService = game:GetService("RunService")

local Anim = {}
Anim.__index = Anim

local BONES = { {{BONES}} }
local LID_AXIS = { R = {{AXE_R}}, L = {{AXE_L}} }
local LID_CLOSE = math.rad({{LID}})
local PUPIL_AXIS = { R = {{PUP_R}}, L = {{PUP_L}} }
local rad, deg, sin, cos, max, min, abs, clamp = math.rad, math.deg, math.sin, math.cos, math.max, math.min, math.abs, math.clamp
local atan2, sqrt = math.atan2, math.sqrt
local TAU = 2 * math.pi

-- géométrie de repos utile au jeu (repère du modèle, studs)
local SOL_ROOT = {{SOL_ROOT}}                  -- hauteur du sol sous l'os Root (y, par rapport à sa tête)
local BOUCHE = {{BOUCHE}}                      -- sortie du feu : CFrame relative à l'os Head (-Z = direction)
-- pattes : épaule/hanche, coude/genou, poignet/jarret dans le plan (y, z) du parent, sens de pliure, bout des griffes
local PATTES = {
{{PATTES}}
}

-- regard au repos : { instant, cap, hauteur }
local SACCADES = { {{SACCADES}} }

-- poses en table (une ligne par échantillon) : os du corps (ex, ey, ez), bassin (x, y, z), paupières,
-- [lueur, feu pour les séquences], puis 4 pattes (haut, bas en degrés, pied en quaternion x, y, z, w)
local TABLES = {
{{TABLES}}
}

-- style de chaque lignée (lignees_v6.py) : vol (durée de la boucle, amplitude, part de plané, ondulation,
-- lourdeur, balayage), vitesses de référence (studs/s), couleur des yeux, particules et lumière du souffle
local LIGNEES = {
{{LIGNEES}}
}

Anim.VITESSE_MARCHE = TABLES.Marche.vitesse   -- studs/s où les pieds ne patinent pas, à cadence normale
Anim.LIGNEES = LIGNEES

local function ease(a, b, t)
	local x = clamp((t - a) / (b - a), 0, 1)
	return x * x * (3 - 2 * x)
end

local function rot(v)
	return CFrame.fromEulerAnglesYXZ(rad(v[1]), rad(v[2]), rad(v[3]))
end

local function blink(t, at, d)
	return clamp(1 - abs(t - at) / (d or 0.06), 0, 1) ^ 0.7
end

local function spline(p0, p1, p2, p3, f)
	local out = table.create(#p1)
	for k = 1, #p1 do
		out[k] = 0.5 * (2 * p1[k] + (p2[k] - p0[k]) * f + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f * f
			+ (3 * p1[k] - p0[k] - 3 * p2[k] + p3[k]) * f * f * f)
	end
	return out
end

-- Catmull-Rom périodique (allures_v6.catmull)
local function catmull(tab, s)
	local n = #tab
	local x = (s % 1) * n
	local i = math.floor(x)
	local f = x - i
	return spline(tab[(i - 1) % n + 1], tab[i % n + 1], tab[(i + 1) % n + 1], tab[(i + 2) % n + 1], f)
end

-- Catmull-Rom aux bouts bloqués (sequences_v6.interp)
local function interp(tab, t)
	local n = #tab
	local x = clamp(t, 0, 1) * (n - 1)
	local i = min(math.floor(x), n - 2)
	local f = x - i
	local function at(j)
		return tab[clamp(i + j, 0, n - 1) + 1]
	end
	return spline(at(-1), at(0), at(1), at(2), f)
end

local function quat(x, y, z, w)
	local n = sqrt(x * x + y * y + z * z + w * w)
	return CFrame.new(0, 0, 0, x / n, y / n, z / n, w / n)
end

-- valeur k (2 = cap, 3 = hauteur) du regard au repos, transitions de durée dur
local function cible(t, k, dur, delai)
	delai = delai or 0
	local v = SACCADES[#SACCADES][k]
	for i, s in SACCADES do
		local prev = SACCADES[i == 1 and #SACCADES or i - 1]
		v += (s[k] - prev[k]) * ease(s[1] + delai, s[1] + delai + dur, t)
	end
	return v
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

-- pose d'une table : renvoie P, décalage, paupières, lueur, regard, regard vertical, feu
local function poseTable(def, t)
	local v = def.periodique and catmull(def.rows, (t * def.foulees) % 1) or interp(def.rows, t)
	local P, c = {}, 0
	for _, n in def.bones do
		P[n] = { v[c + 1], v[c + 2], v[c + 3] }
		c += 3
	end
	local off, lid = Vector3.new(v[c + 1], v[c + 2], v[c + 3]), v[c + 4]
	c += 4
	local glow, fire = 0, 0
	if not def.periodique then
		glow, fire = v[c + 1], v[c + 2]
		c += 2
	end
	for _, kind in { "Front", "Back" } do
		for _, sd in { "R", "L" } do
			P[kind .. "UpperLeg" .. sd] = { v[c + 1], 0, 0 }
			P[kind .. "LowerLeg" .. sd] = { v[c + 2], 0, 0 }
			P[kind .. "Foot" .. sd] = quat(v[c + 3], v[c + 4], v[c + 5], v[c + 6])
			c += 6
		end
	end
	return P, off, lid, glow, nil, nil, fire
end

local ANIMS = {}
for name, def in TABLES do
	ANIMS[name] = { duree = def.duree, boucle = def.periodique, suite = def.suite, allure = def.periodique,
		sol = def.sol, fn = function(t)
			return poseTable(def, t)
		end }
end

-- vol v2 (demo_animations_v6.vol) : 4 battements asymétriques puis du vol plané ; effort (montée) remplace le
-- plané par des battements, force (piqué) impose le plané
local VOL_BATTEMENTS, VOL_DESCENTE = 4, 0.42

local function coup(u)                         -- 1 aile en haut, -1 en bas ; descente rapide, remontée lente
	u %= 1
	local x = u < VOL_DESCENTE and 0.5 * u / VOL_DESCENTE or 0.5 + 0.5 * (u - VOL_DESCENTE) / (1 - VOL_DESCENTE)
	return cos(TAU * x), x
end

local function plie(x)                         -- repli de l'aile à la remontée
	return max(0, -sin(TAU * x)) ^ 2
end

local function appui(x)                        -- aile tendue à la descente
	return max(0, sin(TAU * x)) ^ 2
end

local function volPlane(t, st, effort, force)
	local env = 0
	if st.plane > 0 then
		local a = 1 - st.plane - 0.06
		env = ease(a, a + 0.1, t) * (1 - ease(0.9, 0.99, t))
	end
	return max((1 - effort) * env, force)
end

ANIMS.Vol = { vol = true, fn = function(t, self)             -- durée : style de la lignée (vol.duree)
	local st = self.style.vol
	local A, O, H, Bal = st.amplitude, st.ondulation, st.lourdeur, st.balayage
	local b = VOL_BATTEMENTS * t
	local g = volPlane(t, st, self.volEffort, self.volForce)
	local fl = 1 - g
	local raf = 0.6 * sin(TAU * 7 * t) + 0.4 * sin(TAU * 11 * t + 1)
	local lent = TAU * 2 * t
	local P = {}
	local s0, x0 = coup(b)
	local s1, x1 = coup(b - 0.07)
	local hx = fl * (-6 * appui(x0) + 8 * plie(x0))
	local hy = fl * (5 * appui(x0) - 16 * plie(x0)) + g * (-4 - 14 * Bal)
	local hz = fl * (-8 + 38 * A * s0) + g * (-30 - 4 * Bal + 3 * raf)
	local roulis = 2.5 * raf * g
	P.WingUpperR, P.WingUpperL = { hx, hy, hz + roulis }, { hx, -hy, -(hz - roulis) }
	sides(P, "WingLower", 0, fl * (4 * appui(x1) - 22 * plie(x1)) + g * (4 - 24 * Bal),
		fl * (-2 + 18 * A * s1 - 30 * plie(x1)) + g * (8 + 1.5 * raf))
	for j = 0, 3 do
		local sj, xj = coup(b - 0.13 - 0.03 * j)
		sides(P, "WingFinger" .. (j + 1), 0, fl * (3 * j * (1 - 1.3 * plie(xj)) + 2 * appui(xj)) + g * (2.5 * j - 3 * Bal * j),
			fl * (12 * A * sj - 10 * plie(xj)) + g * (2 + 1.5 * raf))
	end
	local lift = -(coup(b - 0.18))
	P.Root = { -4 + fl * 2.5 * A * -(coup(b - 0.1)) + 1.5 * g, 2.5 * O * sin(lent + 0.3), 2 * O * sin(lent + 1.1) + 3 * raf * g }
	P.Spine = { fl * 2 * O * sin(TAU * b + 1.0), -2 * O * sin(lent + 0.9), 0 }
	P.Chest = { fl * 2 * O * sin(TAU * b + 1.4), -1.5 * O * sin(lent + 1.5), -1.0 * O * sin(lent + 1.8) }
	P.Neck1 = { -8 + fl * 3 * O * sin(TAU * b + 1.6), 2 * O * sin(lent + 1.9), 0 }
	P.Neck2 = { -4 + fl * 2 * O * sin(TAU * b + 2.0), 1.5 * O * sin(lent + 2.3), 0 }
	P.Neck3 = { fl * 1.5 * O * sin(TAU * b + 2.4), 1.0 * O * sin(lent + 2.7), 0 }
	local tang, lac = 0, 0
	for _, n in { "Root", "Spine", "Chest", "Neck1", "Neck2", "Neck3" } do
		tang += P[n][1]
		lac += P[n][2]
	end
	P.Head = { -0.9 * tang - 6.5, -0.8 * lac, -0.6 * (P.Root[3] + P.Chest[3]) }       -- tête stabilisée
	P.Jaw = { -4 - 2.5 * fl * appui(x0), 0, 0 }
	for sd, d in { R = 0, L = 0.35 } do
		local ph = TAU * b - d
		P["FrontUpperLeg" .. sd] = { -22 + fl * 4 * H * sin(ph - 1.0), 0, 0 }
		P["FrontLowerLeg" .. sd] = { 48 + fl * 5 * H * sin(ph - 1.5), 0, 0 }
		P["FrontFoot" .. sd] = { -35 + fl * 6 * H * sin(ph - 2.0), 0, 0 }
		P["BackUpperLeg" .. sd] = { -28 - 4 * g + fl * 4 * H * sin(ph - 1.2), 0, 0 }
		P["BackLowerLeg" .. sd] = { -12 + fl * 6 * H * sin(ph - 1.7), 0, 0 }
		P["BackFoot" .. sd] = { -35 + fl * 8 * H * sin(ph - 2.2), 0, 0 }
	end
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { (i == 0 and 3 or 0) + fl * (1.5 + 0.8 * i) * O * sin(TAU * b - 0.7 * i - 0.5),
			(2.5 + 1.6 * i) * O * sin(lent - 0.6 * i) + 4 * g * raf * (i + 1) / 6, 0 }
	end
	local regard = 10 * sin(TAU * t) + 12 * g * sin(TAU * 2 * t)
	return P, Vector3.new(0, 4.5 + fl * 0.55 * H * A * lift - 0.25 * g + 0.15 * sin(TAU * t), fl * 0.1 * sin(TAU * b)),
		blink(t, 0.37), 0, regard, -4 * g
end }

ANIMS.Rugissement = { duree = 2.2, boucle = false, suite = "Repos", sol = true, fn = function(t)
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
	return P, Vector3.new(0, 0.45 * a - 0.15 * r, 0), 0.4 * r + blink(t, 0.12), r
end }

-- repos : l'œil saute vers un point (~50 ms), la tête suit plus lentement pendant que l'œil revient au centre
ANIMS.Repos = { duree = 4.0, sol = true, fn = function(t)
	local br = sin(TAU * t)
	local tc, th = 0.65 * cible(t, 2, 0.1, 0.02), 0.5 * cible(t, 3, 0.1, 0.02)
	local cap = clamp(cible(t, 2, 0.012) - tc, -18, 18) + 0.7 * sin(19 * TAU * t) + 0.4 * sin(31 * TAU * t + 1)
	local haut = clamp(cible(t, 3, 0.012) - th, -9, 9) + 0.5 * sin(23 * TAU * t + 2)
	local lourd = 0.35 * ease(0.58, 0.62, t) * (1 - ease(0.70, 0.73, t))
	local lid = 0.08 + lourd - 0.02 * haut + max(blink(t, 0.45, 0.03), blink(t, 0.83, 0.03), blink(t, 0.89, 0.03))
	local P = folded({ Chest = { 1.5 * br, 0, 0 }, Spine = { -br, 0, 0 },
		Neck1 = { 2 * br, -0.3 * tc, 0 }, Neck2 = { br, -0.3 * tc, 0 }, Neck3 = { 0.4 * th, -0.2 * tc, 0 },
		Head = { -2 * br + 0.6 * th, -0.2 * tc, 0 }, Jaw = { -3 - 3 * max(0, br), 0, 0 } })
	sides(P, "WingUpper", 0, -38, -22 + 2 * br)
	for i = 0, 5 do
		P["Tail" .. (i + 1)] = { 1.5 * sin(TAU * t - 0.5 * i), 6 * sin(TAU * t - 0.6 * i), 0 }
	end
	return P, Vector3.new(0, 0.05 * br, 0), lid, 0, cap, haut
end }

-- rapproche v de cible sans à-coup (vitesse k par seconde)
local function suivre(v, cible_, k, dt)
	return v + (cible_ - v) * (1 - math.exp(-k * dt))
end

local function enCF(v)
	if typeof(v) == "CFrame" then
		return v
	end
	return v and rot(v) or CFrame.identity
end

-- lignée : argument, sinon attribut « Lignee » du Model, sinon son nom (Dragon_V6_Glace…), sinon Feu
local function lignee(model, nom)
	if not nom then
		local ok, a = pcall(function()
			return model:GetAttribute("Lignee")
		end)
		nom = ok and a or nil
	end
	if not nom then
		local ok, n = pcall(function()
			return model.Name
		end)
		if ok and type(n) == "string" then
			for k in LIGNEES do
				if n:find(k) then
					nom = k
				end
			end
		end
	end
	return LIGNEES[nom] and nom or "Feu"
end

function Anim.new(model: Model, nomLignee: string?)
	local self = setmetatable({}, Anim)
	self.model = model
	self.lignee = lignee(model, nomLignee)
	self.style = LIGNEES[self.lignee]
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
	self.current, self.t, self.rate = "Repos", 0, 1
	self.blinkT, self.squintV, self.lookV, self.lookUpV = math.huge, 0, nil, nil
	self.last, self.from, self.fadeT, self.fadeDur = {}, nil, 0, 0.25
	self.turn, self.turnV, self.lastYaw = 0, nil, nil
	self.lookTarget, self.lookW, self.headYaw, self.headPitch, self.eyeYaw, self.eyePitch = nil, 0, 0, 0, 0, 0
	self.groundIK, self.groundDy, self.groundShift = false, {}, 0
	self.fire = 0
	self.volEffort, self.volForce, self.volPitch, self.flightV, self.flightM, self.lastPos = 0, 0, 0, nil, nil, nil
	self:_creerFeu()
	self.conns = { RunService.Heartbeat:Connect(function(dt)
		self:step(dt)
	end) }
	return self
end

local function seqN(pts)
	local k = {}
	for _, p in pts do
		table.insert(k, NumberSequenceKeypoint.new(p[1], p[2]))
	end
	return NumberSequence.new(k)
end

-- particules et lumière du souffle, sur un os « Souffle » ajouté sous Head ; réglages et couleurs propres à la
-- lignée (flammes et braises, givre et éclats, spores et pollen, ténèbres et volutes) ; « oeil » = couleur des yeux
function Anim:_creerFeu()
	local head = self.bones.Head
	if typeof(head) ~= "Instance" then
		return
	end
	local st = self.style or LIGNEES.Feu
	local oeil = Color3.fromHex(st.oeil)
	local att = Instance.new("Bone")                      -- os enfant sans poids : ne déforme rien, sert de point
	att.Name = "Souffle"                                  -- d'émission (un Bone est un Attachment)
	att.CFrame = BOUCHE
	att.Parent = head
	self.feux = {}
	for _, p in st.souffle.particules do
		local pe = Instance.new("ParticleEmitter")
		pe.Name = p.nom
		pe.Enabled = false
		pe.EmissionDirection = Enum.NormalId.Front
		pe.Rate = p.taux
		pe.Lifetime = NumberRange.new(p.vie[1], p.vie[2])
		pe.Speed = NumberRange.new(p.vitesse[1], p.vitesse[2])
		pe.SpreadAngle = Vector2.new(p.angle, p.angle)
		pe.Drag = p.frein
		pe.Size = seqN(p.taille)
		pe.Transparency = seqN(p.transparence)
		local k = {}
		for _, c in p.couleurs do
			table.insert(k, ColorSequenceKeypoint.new(c[1], c[2] == "oeil" and oeil or Color3.fromHex(c[2])))
		end
		pe.Color = ColorSequence.new(k)
		pe.LightEmission = p.lumineux
		if p.acceleration then
			pe.Acceleration = Vector3.new(p.acceleration[1], p.acceleration[2], p.acceleration[3])
		end
		if p.rotation then
			pe.Rotation = NumberRange.new(p.rotation[1], p.rotation[2])
			pe.RotSpeed = NumberRange.new(p.vitesse_rotation[1], p.vitesse_rotation[2])
		end
		pe.Parent = att
		table.insert(self.feux, pe)
	end
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = oeil, st.souffle.lumiere.portee, 0
	light.Parent = att
	self.feu, self.feuLight, self.feuAtt = self.feux[1], light, att
end

function Anim:play(name: string, fondu: number?)
	assert(ANIMS[name], "Animation inconnue : " .. tostring(name))
	if next(self.last) and (fondu or 0.25) > 0 then
		self.from = table.clone(self.last)
		self.fadeT, self.fadeDur = 0, fondu or 0.25
	end
	self.current, self.t = name, 0
	if not ANIMS[name].allure then
		self.rate = 1
	end
end

function Anim:blink()
	self.blinkT = 0
end

function Anim:look(degres: number?, up: number?)
	self.lookV, self.lookUpV = degres, up -- nil : le regard suit l'animation
end

function Anim:lookAt(target)
	self.lookTarget = target -- Vector3, BasePart, Model ou nil
end

function Anim:setTurn(x: number?)
	self.turnV = x and clamp(x, -1, 1) or nil -- nil : mesuré sur la rotation du Model
end

function Anim:setGroundIK(on: boolean)
	self.groundIK = on
end

function Anim:setRate(r: number)
	self.rate = max(r, 0) -- vitesse de lecture (1 = normale)
end

function Anim:squint(v: number)
	self.squintV = clamp(v, 0, 1)
end

-- au sol : Repos ou Marche selon la vitesse (studs/s), cadence calée sur v pour que les pieds ne patinent pas
-- (x0,5 à x2) ; pas de course : au-delà, le jeu fait décoller le dragon. Sans effet en vol ou pendant une séquence.
function Anim:setSpeed(v: number)
	local cur = self.current
	if cur ~= "Repos" and cur ~= "Marche" then
		return
	end
	local nom = v < (cur == "Repos" and 0.6 or 0.3) and "Repos" or "Marche"       -- hystérésis
	if nom ~= cur then
		self:play(nom, 0.3)
	end
	self.rate = nom == "Marche" and clamp(v / Anim.VITESSE_MARCHE, 0.5, 2) or 1
end

function Anim:enVol(): boolean
	return self.current == "Vol" or self.current == "Decollage"
end

-- décolle (s'il est au sol) puis enchaîne sur Vol
function Anim:decoller()
	if not self:enVol() and self.current ~= "Atterrissage" then
		self:play("Decollage")
	end
end

-- se pose (s'il vole) puis enchaîne sur Repos
function Anim:atterrir()
	if self.current == "Vol" then
		self:play("Atterrissage")
	end
end

-- en vol : vitesse horizontale et verticale (studs/s) ; nil : mesurées sur les déplacements du Model.
-- Monter ou faire du sur-place fait battre des ailes sans planer (monter cabre le corps) ; piquer replie les ailes
-- en arrière et baisse le nez ; en croisière il alterne battements et plané.
function Anim:setFlight(vitesse: number?, montee: number?)
	self.flightV, self.flightM = vitesse, montee
end

function Anim:follow(humanoid: Humanoid)
	table.insert(self.conns, humanoid.Running:Connect(function(speed)
		self:setSpeed(speed)
	end))
end

function Anim:_pivot()
	local ok, cf = pcall(function()
		return self.model:GetPivot()
	end)
	return ok and cf or CFrame.identity
end

-- regard qui suit une cible : les yeux visent tout de suite, la tête rattrape plus lentement
function Anim:_lookAt(dt, P)
	local tgt = self.lookTarget
	if typeof(tgt) == "Instance" then
		tgt = tgt:IsA("Model") and tgt:GetPivot().Position or (tgt:IsA("BasePart") and tgt.Position or nil)
	end
	local yaw, pitch, on = 0, 0, false
	if typeof(tgt) == "Vector3" then
		local head = self.bones.Head
		local hp = typeof(head) == "Instance" and head.TransformedWorldCFrame.Position or self:_pivot().Position
		local rel = self:_pivot():VectorToObjectSpace(tgt - hp)
		yaw = deg(atan2(rel.X, -rel.Z))
		pitch = deg(atan2(rel.Y, sqrt(rel.X * rel.X + rel.Z * rel.Z)))
		on = abs(yaw) < 120                                 -- derrière lui : il laisse tomber
	end
	self.lookW = suivre(self.lookW, on and 1 or 0, 5, dt)
	self.headYaw = suivre(self.headYaw, on and clamp(0.75 * yaw, -55, 55) or 0, 4, dt)
	self.headPitch = suivre(self.headPitch, on and clamp(0.6 * pitch, -25, 30) or 0, 4, dt)
	self.eyeYaw = suivre(self.eyeYaw, on and clamp(yaw - self.headYaw, -18, 18) or 0, 30, dt)
	self.eyePitch = suivre(self.eyePitch, on and clamp(pitch - self.headPitch, -9, 9) or 0, 30, dt)
	if self.lookW < 0.01 then
		return nil
	end
	local w = self.lookW
	for n, k in { Neck1 = 0.3, Neck2 = 0.3, Neck3 = 0.2, Head = 0.2 } do
		local up = (n == "Head" and 0.6 or (n == "Neck3" and 0.4 or 0)) * self.headPitch
		P[n] = CFrame.fromEulerAnglesYXZ(rad(up * w), rad(-k * self.headYaw * w), 0) * P[n]
	end
	return self.eyeYaw * w, self.eyePitch * w, w
end

-- vol : effort (montée ou sur-place), plané forcé (piqué), tangage, d'après setFlight ou les déplacements du Model
function Anim:_volCtrl(dt)
	local v, m = self.flightV, self.flightM
	local p = self:_pivot().Position
	if self.lastPos and dt > 0 then
		local d = (p - self.lastPos) / dt
		v = v or Vector3.new(d.X, 0, d.Z).Magnitude
		m = m or d.Y
	end
	self.lastPos = p
	self.bouge = self.bouge or (v or 0) > 1
	local connu = self.flightV ~= nil or self.bouge         -- Model immobile depuis le début : pas de sur-place
	v, m = v or 0, m or 0
	local vit = self.style.vitesses
	local enVol = ANIMS[self.current].vol
	local surPlace = connu and clamp(1 - v / (0.35 * vit.vol), 0, 1) or 0          -- lent : il bat pour se tenir
	local effort = enVol and max(clamp(m / vit.montee, 0, 1), surPlace) or 0
	local force = enVol and clamp((-m - 0.25 * vit.pique) / (0.5 * vit.pique), 0, 1) or 0
	local pitch = enVol and (clamp(m / vit.montee, -1, 1) * 12 - 10 * force) or 0
	self.volEffort = suivre(self.volEffort, effort, 3, dt)
	self.volForce = suivre(self.volForce, force, 3, dt)
	self.volPitch = suivre(self.volPitch, pitch, 3, dt)
end

-- calque du vol : tangage (montée / piqué) et ailes balayées vers l'arrière en piqué
function Anim:_vol(P)
	if abs(self.volPitch) > 1e-4 then
		P.Root = CFrame.fromEulerAnglesYXZ(rad(self.volPitch), 0, 0) * P.Root
	end
	local f = self.volForce
	if f > 1e-4 then
		for _, sd in { "R", "L" } do
			local k = sd == "R" and 1 or -1
			P["WingUpper" .. sd] = CFrame.fromEulerAnglesYXZ(0, rad(-25 * f * k), rad(-10 * f * k)) * P["WingUpper" .. sd]
			P["WingLower" .. sd] = CFrame.fromEulerAnglesYXZ(0, rad(-30 * f * k), 0) * P["WingLower" .. sd]
		end
	end
end

-- virage : le corps se courbe vers l'intérieur, la tête mène, la queue part vers l'extérieur, roulis
-- (en vol : grand roulis, le dragon s'incline sur l'aile intérieure)
function Anim:_turn(dt, P)
	local x = self.turnV
	if x == nil then
		local look = self:_pivot().LookVector
		local yawNow = atan2(-look.X, -look.Z)
		local rate = 0
		if self.lastYaw and dt > 0 then
			rate = ((yawNow - self.lastYaw + math.pi) % TAU - math.pi) / dt
		end
		self.lastYaw = yawNow
		x = clamp(-rate / 2.2, -1, 1)                       -- ≈ 2,2 rad/s = virage complet
	end
	self.turn = suivre(self.turn, x, 6, dt)
	local k = self.turn
	if abs(k) < 1e-3 then
		return
	end
	for n, a in { Spine = 5, Chest = 6, Neck1 = 7, Neck2 = 6, Neck3 = 4, Head = 4 } do
		P[n] = CFrame.fromEulerAnglesYXZ(0, rad(-a * k), 0) * P[n]
	end
	for i = 1, 6 do
		P["Tail" .. i] = CFrame.fromEulerAnglesYXZ(0, rad(4 * k), 0) * P["Tail" .. i]
	end
	local roulis = ANIMS[self.current].vol and 24 or 6
	P.Root = CFrame.fromEulerAnglesYXZ(0, 0, rad(-roulis * k)) * P.Root     -- penche dans le virage
end

-- hauteur du sol sous une patte par rapport au plan du modèle (rayon) ; remplaçable pour les tests
function Anim:_sondeSol(leg)
	local foot = self.bones[leg.foot]
	if typeof(foot) ~= "Instance" then
		return 0
	end
	local root = self.bones.Root
	local plan = root.WorldCFrame:PointToWorldSpace(Vector3.new(0, SOL_ROOT, 0)).Y
	local p = foot.TransformedWorldCFrame:PointToWorldSpace(leg.griffe)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { self.model }
	local hit = workspace:Raycast(Vector3.new(p.X, plan + 4, p.Z), Vector3.new(0, -9, 0), params)
	return hit and clamp(hit.Position.Y - plan, -2.5, 2.5) or 0
end

local function rot2(y, z, a)
	return y * cos(a) - z * sin(a), y * sin(a) + z * cos(a)
end

-- pieds sur le relief : le bassin descend de la moyenne, chaque patte corrige le reste par IK (pied gardé à plat)
function Anim:_ground(dt, cf)
	local on = self.groundIK and ANIMS[self.current].sol
	local dys, somme = {}, 0
	for name, leg in PATTES do
		local d = on and self:_sondeSol(leg) or 0
		self.groundDy[name] = suivre(self.groundDy[name] or 0, d, 12, dt)
		dys[name] = self.groundDy[name]
		somme += dys[name]
	end
	self.groundShift = suivre(self.groundShift, on and clamp(somme / 4, -1.5, 0.5) or 0, 8, dt)
	local shift = self.groundShift
	local actif = abs(shift) > 1e-4
	for _, d in dys do
		actif = actif or abs(d) > 1e-4
	end
	if not actif then
		return
	end
	cf.Root = CFrame.new(0, shift, 0) * cf.Root
	local piv = self:_pivot()
	for name, leg in PATTES do
		local a1 = cf[leg.up]:ToEulerAnglesYXZ()            -- les pattes ne tournent qu'autour de X
		local a2 = cf[leg.low]:ToEulerAnglesYXZ()
		local foot = cf[leg.foot]
		-- poignet actuel dans le plan du parent
		local ey, ez = rot2(leg.l2y, leg.l2z, a2)
		ey, ez = rot2(leg.l1y + ey, leg.l1z + ez, a1)
		local d = piv:VectorToObjectSpace(Vector3.new(0, dys[name] - shift, 0))
		local ty, tz = ey + d.Y, ez + d.Z
		local l1, l2 = leg.l1, leg.l2
		local dist = clamp(sqrt(ty * ty + tz * tz), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
		local alpha = math.acos(clamp((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1))
		local b1 = atan2(tz, ty) - leg.sens * alpha - atan2(leg.l1z, leg.l1y)
		local my, mz = rot2(leg.l1y, leg.l1z, b1)           -- coude/genou après correction
		local wy, wz = rot2(leg.l2y, leg.l2z, b1)
		local b2 = atan2(tz - mz, ty - my) - atan2(wz, wy)
		cf[leg.up] = CFrame.Angles(b1, 0, 0)
		cf[leg.low] = CFrame.Angles(b2, 0, 0)
		-- pied : même orientation qu'avant la correction
		cf[leg.foot] = CFrame.Angles(-(b1 + b2), 0, 0) * CFrame.Angles(a1 + a2, 0, 0) * foot
	end
end

function Anim:step(dt)
	self:_volCtrl(dt)
	local A = ANIMS[self.current]
	local duree = A.vol and self.style.vol.duree or A.duree
	self.t += dt * self.rate * (A.vol and 1 + 0.4 * self.volEffort or 1) / duree   -- en montée, il bat plus vite
	if self.t >= 1 then
		if A.boucle == false then
			self:play(A.suite or "Repos")
			A = ANIMS[self.current]
		else
			self.t %= 1
		end
	end
	local P, off, squint, glow, look, lookUp, fire = A.fn(self.t, self)
	-- clignement : à la demande + un au hasard toutes les 3 à 6 s
	self.blinkT += dt
	if self.blinkT > 0.25 and math.random() < dt / 4.5 then
		self.blinkT = 0
	end
	local bl = clamp(1 - abs(self.blinkT - 0.08) / 0.08, 0, 1)
	local lid = clamp(max(bl, squint or 0, self.squintV), 0, 1)
	-- calques ajoutés à l'animation : virage, regard vers une cible
	local cf = {}
	for _, n in BONES do
		cf[n] = enCF(P[n])
	end
	self:_turn(dt, cf)
	self:_vol(cf)
	local eyeYaw, eyePitch, w = self:_lookAt(dt, cf)
	look = self.lookV or look or 0
	lookUp = self.lookUpV or lookUp or 0
	if eyeYaw then
		look, lookUp = look * (1 - w) + eyeYaw, lookUp * (1 - w) + eyePitch
	end
	for _, s in { "R", "L" } do
		cf["Eyelid" .. s] = CFrame.fromAxisAngle(LID_AXIS[s], -LID_CLOSE * lid * (s == "R" and 1 or -1))
		cf["Pupil" .. s] = CFrame.fromEulerAnglesYXZ(0, rad(-look), 0) * CFrame.fromAxisAngle(PUPIL_AXIS[s], rad(lookUp))
	end
	cf.Root = CFrame.new(off) * cf.Root
	-- fondu depuis la pose affichée au moment du changement d'animation (sauf paupières et pupilles)
	if self.from then
		self.fadeT += dt
		local k = ease(0, 1, self.fadeT / self.fadeDur)
		for _, n in BONES do
			if self.from[n] and not (n:sub(1, 6) == "Eyelid" or n:sub(1, 5) == "Pupil") then
				cf[n] = self.from[n]:Lerp(cf[n], k)
			end
		end
		if self.fadeT >= self.fadeDur then
			self.from = nil
		end
	end
	self:_ground(dt, cf)
	for _, n in BONES do
		self.bones[n].Transform = cf[n]
	end
	self.last = cf
	-- feu : particules et lumière pendant le souffle
	self.fire = fire or 0
	if self.feux then
		for _, pe in self.feux do
			pe.Enabled = self.fire > 0.5
		end
		self.feuLight.Brightness = self.style.souffle.lumiere.eclat * self.fire
	end
	-- lueur des yeux : pulsation lente, plus vive pendant le rugissement et le souffle
	if self.neon then
		local k = 0.85 + 0.15 * sin(os.clock() * 2.5) + 0.3 * (glow or 0)
		self.neon.Color = Color3.new(min(self.baseColor.R * k, 1), min(self.baseColor.G * k, 1), min(self.baseColor.B * k, 1))
	end
end

function Anim:destroy()
	for _, c in self.conns do
		c:Disconnect()
	end
	if self.feuAtt then
		self.feuAtt:Destroy()
	end
end

return Anim
