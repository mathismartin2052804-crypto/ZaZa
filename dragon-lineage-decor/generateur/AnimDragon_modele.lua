-- AnimDragon : anime le dragon v6 importé (Dragon_V6*.glb) en pilotant ses os (Bone.Transform).
-- Fichier généré par generateur/export_dragon_v6.py à partir de generateur/AnimDragon_modele.lua : modifier le modèle.
-- Placement : ModuleScript dans ReplicatedStorage ; à utiliser depuis un LocalScript (rendu fluide côté client)
-- ou un Script serveur. Les deux MeshParts (Dragon, DragonNeon) doivent être dans le même Model que les os.
--   local Anim = require(ReplicatedStorage.AnimDragon)
--   local d = Anim.new(workspace.Dragon_V6)
--   d:play("Course")            -- "Repos", "Marche", "Course", "Vol", "Rugissement", "Decollage", "Atterrissage",
--                               -- "SouffleFeu" (fondu de 0,25 s ; d:play(nom, 0) pour couper net)
--   d:setSpeed(v)               -- choisit Repos / Marche / Course selon la vitesse (studs/s) et cale la foulée
--   d:follow(humanoid)          -- pareil, branché sur Humanoid.Running
--   d:lookAt(cible)             -- suit du regard un Vector3, une BasePart ou un Model (nil : rend la main)
--   d:setTurn(x)                -- virage de -1 (gauche) à 1 (droite) ; nil : mesuré tout seul sur le Model
--   d:setGroundIK(true)         -- pieds posés sur le relief (rayons sous chaque patte)
--   d:blink() ; d:squint(0.4) ; d:look(20, 5)   -- clignement, plisser les yeux, regard imposé (degrés)
-- Mêmes poses que les scripts Python du générateur (angles en degrés, ordre YXZ, autour de la tête de chaque os) ;
-- marche, course, décollage, atterrissage et souffle de feu sont copiés sous forme de tables (allures_v6.py,
-- sequences_v6.py : pattes calculées par cinématique inverse pour que les pieds restent au sol).
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

Anim.VITESSE_MARCHE = TABLES.Marche.vitesse   -- studs/s où les pieds ne patinent pas, à cadence normale
Anim.VITESSE_COURSE = TABLES.Course.vitesse

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
	return P, Vector3.new(0, 4.5 - 0.7 * sin(p), 0), blink(t, 0.62), 0, 8 * sin(TAU * t)
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
	self.current, self.t, self.rate = "Repos", 0, 1
	self.blinkT, self.squintV, self.lookV, self.lookUpV = math.huge, 0, nil, nil
	self.last, self.from, self.fadeT, self.fadeDur = {}, nil, 0, 0.25
	self.turn, self.turnV, self.lastYaw = 0, nil, nil
	self.lookTarget, self.lookW, self.headYaw, self.headPitch, self.eyeYaw, self.eyePitch = nil, 0, 0, 0, 0, 0
	self.groundIK, self.groundDy, self.groundShift = false, {}, 0
	self.fire = 0
	self:_creerFeu()
	self.conns = { RunService.Heartbeat:Connect(function(dt)
		self:step(dt)
	end) }
	return self
end

-- particules et lumière du souffle de feu, attachées à l'os Head (couleur prise sur DragonNeon)
function Anim:_creerFeu()
	local head = self.bones.Head
	if typeof(head) ~= "Instance" then
		return
	end
	local c = self.baseColor or Color3.fromRGB(255, 200, 60)
	local att = Instance.new("Attachment")
	att.Name = "Souffle"
	att.CFrame = BOUCHE
	att.Parent = head
	local pe = Instance.new("ParticleEmitter")
	pe.Name = "Feu"
	pe.Enabled = false
	pe.EmissionDirection = Enum.NormalId.Front
	pe.Rate = 160
	pe.Lifetime = NumberRange.new(0.35, 0.6)
	pe.Speed = NumberRange.new(28, 38)
	pe.SpreadAngle = Vector2.new(9, 9)
	pe.Drag = 2
	pe.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(0.4, 2.6),
		NumberSequenceKeypoint.new(1, 4.5) })
	pe.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.7, 0.4),
		NumberSequenceKeypoint.new(1, 1) })
	pe.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.new(1, 1, 0.9)), ColorSequenceKeypoint.new(0.25, c),
		ColorSequenceKeypoint.new(1, c:Lerp(Color3.new(0.1, 0.05, 0.05), 0.7)) })
	pe.LightEmission = 1
	pe.Parent = att
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = c, 16, 0
	light.Parent = att
	self.feu, self.feuLight, self.feuAtt = pe, light, att
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

-- choisit l'allure selon la vitesse au sol (studs/s) et cale la cadence ; sans effet en vol ou pendant une séquence
function Anim:setSpeed(v: number)
	local cur = self.current
	if cur ~= "Repos" and cur ~= "Marche" and cur ~= "Course" then
		return
	end
	local vm, vc = Anim.VITESSE_MARCHE, Anim.VITESSE_COURSE
	local seuil = (vm + vc) / 2 + (cur == "Course" and -0.6 or 0.6)      -- hystérésis
	local arret = cur == "Repos" and 0.6 or 0.3
	local nom = v < arret and "Repos" or (v < seuil and "Marche" or "Course")
	if nom ~= cur then
		self:play(nom, 0.3)
	end
	if nom == "Marche" then
		self.rate = clamp(v / vm, 0.5, 1.8)
	elseif nom == "Course" then
		self.rate = clamp(v / vc, 0.6, 1.6)
	else
		self.rate = 1
	end
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

-- virage : le corps se courbe vers l'intérieur, la tête mène, la queue part vers l'extérieur, roulis
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
	P.Root = CFrame.fromEulerAnglesYXZ(0, 0, rad(-6 * k)) * P.Root          -- penche dans le virage
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
	local A = ANIMS[self.current]
	self.t += dt * self.rate / A.duree
	if self.t >= 1 then
		if A.boucle == false then
			self:play(A.suite or "Repos")
			A = ANIMS[self.current]
		else
			self.t %= 1
		end
	end
	local P, off, squint, glow, look, lookUp, fire = A.fn(self.t)
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
	if self.feu then
		self.feu.Enabled = self.fire > 0.5
		self.feuLight.Brightness = 4 * self.fire
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
