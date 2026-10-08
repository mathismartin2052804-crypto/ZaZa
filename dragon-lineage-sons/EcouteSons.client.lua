--[[
	EcouteSons (LocalScript) : outil d'écoute temporaire, à NE PAS publier.
	À placer dans StarterPlayer > StarterPlayerScripts, puis lancer Play.

	Touches :
	  E : son suivant      Q : son précédent      R : rejouer
	La console (Output) affiche la catégorie, le nom et l'ID de chaque son.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local SoundService = game:GetService("SoundService")

local Sons = require(ReplicatedStorage:WaitForChild("SonsDragonLineage"))

-- Liste à plat, dans un ordre stable.
local liste = {}
local categories = {}
for categorie in Sons do
	table.insert(categories, categorie)
end
table.sort(categories)
for _, categorie in categories do
	local besoins = {}
	for besoin in Sons[categorie] do
		table.insert(besoins, besoin)
	end
	table.sort(besoins)
	for _, besoin in besoins do
		for i, son in Sons[categorie][besoin] do
			-- Les sons cartoon pas encore importés (id = nil) sont ignorés.
			if son.id then
				table.insert(liste, { titre = `{categorie} > {besoin} #{i}`, son = son })
			end
		end
	end
end

local courant = 0
local lecteur = Instance.new("Sound")
lecteur.Parent = SoundService

local function jouer(index)
	courant = (index - 1) % #liste + 1
	local entree = liste[courant]
	lecteur:Stop()
	lecteur.SoundId = entree.son.id
	lecteur.Looped = false
	lecteur:Play()
	print(`[{courant}/{#liste}] {entree.titre} : {entree.son.nom} ({entree.son.id})`)
end

UserInputService.InputBegan:Connect(function(input, traite)
	if traite then
		return
	end
	if input.KeyCode == Enum.KeyCode.E then
		jouer(courant + 1)
	elseif input.KeyCode == Enum.KeyCode.Q then
		jouer(courant - 1)
	elseif input.KeyCode == Enum.KeyCode.R and courant > 0 then
		jouer(courant)
	end
end)

print(`EcouteSons prêt : {#liste} sons. Appuie sur E pour commencer.`)
