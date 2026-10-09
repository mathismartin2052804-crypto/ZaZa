-- DragonCristalVol (LocalScript) : animation de VOL du dragon de cristal v5, côté client.
-- À mettre dans StarterPlayer > StarterPlayerScripts. Le ModuleScript « DragonCristalRig » (pivots de repos,
-- généré par generateur/rig5v5.py) va dans ReplicatedStorage. Chaque modèle de dragon placé dans le Workspace
-- doit avoir le tag « DragonCristal » (propriété Tags). Toutes ses parties sont Anchored.
--
-- C'est exactement le calcul de la démo (fonction pose() de demo5v5.tpl.html), boucle de 1,32 s :
--   - le corps ondule de haut en bas (vague de la tête vers la queue, plus faible près de la tête) ;
--   - la tête suit la direction moyenne du début du cou, avec un léger retard, et hoche un peu ;
--   - les quatre pattes pagaient (épaule/hanche, coude/genou, main/pied), en décalé ;
--   - la mâchoire (toutes les parties « Head_Jaw… ») se ferme un peu puis se rouvre ;
--   - les moustaches (3 morceaux) ondulent ; les yeux clignent (Head_Lids / Head_LidsHalf), les pupilles bougent.
-- Chaque morceau : CFrame = A × M × (A⁻¹ × CFrame de repos), avec M = T(nouveau pivot) × R × T(−pivot de repos)
-- calculé dans le repère du GLB, et A le passage du repère du GLB au monde (trouvé avec la partie « Head »).
-- Tout bouge en une fois avec workspace:BulkMoveTo, seulement près de la caméra.

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local RIG = require(ReplicatedStorage:WaitForChild("DragonCristalRig"))

local TAG = "DragonCristal"
local MAX_DIST = 600        -- au-delà (studs), on n'anime pas le dragon
-- @@MATH (début du calcul, testé hors de Roblox)
local T = 1.32              -- durée de la boucle (vidéo de référence)
local WAVE = 1.15           -- nombre de vagues le long du corps
local HEAD_LAG = 0.08       -- retard de la tête sur le cou (s)
local LEG_PH = { FL = 0, FR = 0.9, BL = math.pi, BR = math.pi + 0.9 }
local UP = Vector3.new(0, 1, 0)

local function basis(f: Vector3): CFrame -- rotation (droite, haut, arrière) d'un morceau qui regarde vers f
	local r = f:Cross(UP).Unit
	local u = r:Cross(f)
	return CFrame.fromMatrix(Vector3.new(0, 0, 0), r, u, -f)
end
local function moveMat(newP: Vector3, R: CFrame, restP: Vector3): CFrame
	return CFrame.new(newP) * R * CFrame.new(-restP)
end
local function about(p: Vector3, R: CFrame): CFrame -- rotation R autour du point de repos p
	return CFrame.new(p) * R * CFrame.new(-p)
end
local function rotX(a: number): CFrame
	return CFrame.Angles(a, 0, 0)
end
local function rotY(a: number): CFrame
	return CFrame.Angles(0, a, 0)
end
local function hash(n: number): number
	local x = math.sin(n * 127.1 + 311.7) * 43758.5453
	return x - math.floor(x)
end

-- Données de repos d'un dragon, dans le repère du GLB mis à l'échelle s (si l'import a changé la taille)
local function makeRig(s: number)
	local D = { s = s, P = {}, restInv = {}, legs = {}, whisk = {}, eyes = {} }
	local n = 0
	for i, p in ipairs(RIG.Chain) do
		D.P[i - 1] = p * s
		n = i - 1
	end
	D.N = n
	for i = 0, n do
		local f = (i == 0) and (D.P[0] - D.P[1]) or (D.P[i - 1] - D.P[i])
		D.restInv[i] = basis(f.Unit):Inverse()
	end
	D.restHeadInv = basis((D.P[0] - D.P[3]).Unit):Inverse()
	D.jawHinge = RIG.JawHinge * s
	for _, L in ipairs(RIG.Legs) do
		D.legs[L.Name] = { tag = L.Tag, seg = L.Seg, hip = L.Hip * s, knee = L.Knee * s, ankle = L.Ankle * s }
	end
	for k, pts in pairs(RIG.Whiskers) do
		local t = {}
		for j, p in ipairs(pts) do
			t[j] = p * s
		end
		D.whisk[k] = t
	end
	for k, e in pairs(RIG.Eyes) do
		D.eyes[k] = { c = e.C * s, n = e.N }
	end
	return D
end

local function chainAt(D, t: number)
	local w = 2 * math.pi * ((t / T) % 1)
	local Q = {}
	for i = 0, D.N do
		local sN = i / D.N
		local near = 0.3 + 0.7 * math.min(1, sN / 0.18)
		local dy = (0.9 + 2.1 * sN) * near * math.sin(w - 2 * math.pi * WAVE * sN)
		local dx = 0.5 * sN * math.sin(w - 2 * math.pi * 0.6 * sN + 1.2)
		Q[i] = D.P[i] + Vector3.new(dx, dy, 0) * D.s
	end
	return Q
end

-- Calcule toutes les matrices M de l'instant t (repère du GLB). Renvoie une table : clé de pilotage → CFrame,
-- et l'état des paupières (« full », « half » ou nil).
local function pose(D, t: number)
	local w = 2 * math.pi * ((t / T) % 1)
	local out = {}
	-- 1. colonne
	local Q = chainAt(D, t)
	for i = 0, D.N do
		local f = (i == 0) and (Q[0] - Q[1]) or (Q[i - 1] - Q[i])
		out["seg" .. i] = moveMat(Q[i], basis(f.Unit) * D.restInv[i], D.P[i])
	end
	-- tête : direction moyenne des 3 premiers morceaux, avec un léger retard, plus un petit hochement
	local Ql = chainAt(D, t - HEAD_LAG)
	local fh = (Ql[0] - Ql[3]).Unit
	local headM = moveMat(Q[0], basis(fh) * D.restHeadInv * rotX(0.05 * math.sin(w - 1.3)), D.P[0])
	out.seg0 = headM
	-- 2. mâchoire
	out.jaw = headM * about(D.jawHinge, rotX(0.13 * (0.5 + 0.5 * math.sin(w + 2.0))))
	-- 3. pattes : elles pagaient (les quatre de la même façon, en décalé)
	for name, L in pairs(D.legs) do
		local ph = w + LEG_PH[L.tag]
		local thigh = out["seg" .. L.seg] * about(L.hip, rotX(0.5 * math.sin(ph)))
		local shin = thigh * about(L.knee, rotX(0.45 * math.sin(ph - 0.9)))
		out[name .. "/thigh"] = thigh
		out[name .. "/shin"] = shin
		out[name .. "/foot"] = shin * about(L.ankle, rotX(0.5 * math.sin(ph - 1.7)))
	end
	-- 4. moustaches : trois morceaux en chaîne, vague qui part du museau
	for k, piv in pairs(D.whisk) do
		local m = headM
		local sd = (k == "L") and 0 or 0.7
		local sg = (k == "L") and -1 or 1
		for j, p in ipairs(piv) do
			local jj = j - 1
			local R = rotX((0.1 + 0.07 * jj) * math.sin(w - 1.0 * jj + sd)) * rotY(sg * 0.06 * math.sin(w - 1.0 * jj + 1.3))
			m = m * about(p, R)
			out["whisker" .. k .. j] = m
		end
	end
	-- 5. yeux : clignement toutes les 3,7 s, regard qui change toutes les 2,3 s
	local bt = t % 3.7
	local lids = nil
	if bt > 0.05 and bt < 0.14 then
		lids = "full"
	elseif bt < 0.05 or (bt >= 0.14 and bt < 0.2) then
		lids = "half"
	end
	local look = math.floor(t / 2.3)
	local yaw = 0.16 * (hash(look) - 0.5) * 2
	local pitch = 0.08 * (hash(look + 7) - 0.5) * 2
	for k, e in pairs(D.eyes) do
		local pivot = e.c - e.n * (0.9 * D.s)
		out["pupil" .. k] = headM * about(pivot, rotY(yaw) * rotX(pitch))
	end
	return out, lids
end

-- Quelle matrice pilote chaque partie (même règle que la démo)
local function driveKey(name: string, D): string
	if string.sub(name, 1, 8) == "Head_Jaw" then
		return "jaw"
	end
	local side, j = string.match(name, "^Head_Whisker([LR])(%d)$")
	if side then
		return "whisker" .. side .. j
	end
	local ps = string.match(name, "^Head_Pupils_([LR])$")
	if ps then
		return "pupil" .. ps
	end
	for legName in pairs(D.legs) do
		if string.sub(name, 1, #legName) == legName then
			if string.find(name, "_Shin", 1, true) then
				return legName .. "/shin"
			elseif string.sub(name, -5) == "_Foot" then
				return legName .. "/foot"
			end
			return legName .. "/thigh"
		end
	end
	local key = string.match(name, "^([^_]+)")
	if key == "Head" then
		return "seg0"
	end
	return "seg" .. tostring(tonumber(string.sub(key, 4)))
end
-- @@FIN (fin du calcul)

-- ---------------- dans le jeu ----------------
local dragons = {}

local function setup(model: Model)
	local parts = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			parts[d.Name] = d
		end
	end
	local head = parts.Head
	if not head then
		warn("[DragonCristalVol] pas de partie « Head » dans", model:GetFullName())
		return
	end
	local s = head.Size.Magnitude / RIG.HeadSize.Magnitude
	local A = head.CFrame * CFrame.new(-(RIG.HeadCenter * s)) -- repère du GLB → monde
	local check = parts[RIG.CheckPart]
	if check and (A * (RIG.CheckCenter * s) - check.Position).Magnitude > 2 * s then
		warn("[DragonCristalVol] le recalage ne colle pas (", RIG.CheckPart, ") : le modèle a été modifié ou mal importé")
	end
	local D = makeRig(s)
	local Ainv = A:Inverse()
	local list, keys, rel = {}, {}, {}
	for name, p in pairs(parts) do
		list[#list + 1] = p
		keys[#keys + 1] = driveKey(name, D)
		rel[#rel + 1] = Ainv * p.CFrame -- position de repos dans le repère du GLB
	end
	if parts.Head_Lids then
		parts.Head_Lids.Transparency = 1
	end
	if parts.Head_LidsHalf then
		parts.Head_LidsHalf.Transparency = 1
	end
	dragons[model] = {
		D = D, A = A, list = list, keys = keys, rel = rel, cf = table.create(#list),
		lidFull = parts.Head_Lids, lidHalf = parts.Head_LidsHalf, lidState = nil,
		center = head, offset = math.random() * 10, -- chaque dragon a son propre rythme
	}
end

local function onAdded(inst: Instance)
	if inst:IsA("Model") then
		task.defer(setup, inst)
	end
end
for _, m in ipairs(CollectionService:GetTagged(TAG)) do
	onAdded(m)
end
CollectionService:GetInstanceAddedSignal(TAG):Connect(onAdded)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(m)
	dragons[m] = nil
end)

local clock = 0
RunService.RenderStepped:Connect(function(dt)
	clock += dt
	local cam = Workspace.CurrentCamera
	for model, G in pairs(dragons) do
		if not model.Parent then
			dragons[model] = nil
			continue
		end
		if cam and (G.center.Position - cam.CFrame.Position).Magnitude > MAX_DIST then
			continue
		end
		local M, lids = pose(G.D, clock + G.offset)
		for i, p in ipairs(G.list) do
			G.cf[i] = G.A * M[G.keys[i]] * G.rel[i]
		end
		Workspace:BulkMoveTo(G.list, G.cf, Enum.BulkMoveMode.FireCFrameChanged)
		if lids ~= G.lidState then
			G.lidState = lids
			if G.lidFull then
				G.lidFull.Transparency = (lids == "full") and 0 or 1
			end
			if G.lidHalf then
				G.lidHalf.Transparency = (lids == "half") and 0 or 1
			end
		end
	end
end)
