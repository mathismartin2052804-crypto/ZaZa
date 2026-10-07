-- LigneesDragon : caractéristiques de jeu des lignées du dragon v6 (Feu, Glace, Foret, Ombre).
-- Fichier généré par generateur/export_dragon_v6.py à partir de generateur/lignees_v6.py (CARAC) : modifier la source.
-- Placement : ModuleScript dans ReplicatedStorage, lu par les scripts du jeu (serveur pour les dégâts).
--   local Lignees = require(ReplicatedStorage.LigneesDragon)
--   local c = Lignees.get("Glace")          -- stats (sur 100), vitesses (studs/s), souffle, passif, affinités
--   local deg = c.souffle.degats * Lignees.affinite("Feu", "Glace")      -- x1,25 : le Feu bat la Glace
-- Cycle des affinités : Feu > Glace > Foret > Ombre > Feu (x1,25 contre la lignée battue,
-- x0,8 contre celle qui vous bat). Valeurs de départ : à équilibrer en jeu.
local Lignees = {}

Lignees.LISTE = { "Feu", "Glace", "Foret", "Ombre" }
Lignees.AFFINITE_FORT, Lignees.AFFINITE_FAIBLE = 1.25, 0.8

local DATA = {
	Feu = {
		nom = "Feu",
		element = "Feu",
		titre = "Le Brasier",
		description = "Dragon d'attaque : souffle de flammes qui brûle dans la durée, colère qui monte quand il est blessé.",
		stats = { vie = 100, attaque = 72, defense = 50, vitesse = 55, agilite = 50, endurance = 55 },
		vitesses = { marche = 4, vol = 34, montee = 12, pique = 60 },
		souffle = {
			nom = "Flammes",
			forme = "cone",
			portee = 28,
			angle = 25,
			degats = 18,
			duree = 2,
			recharge = 6,
			effet = "Brulure",
			effet_duree = 4,
			effet_valeur = 4,
			texte = "Brûlure : 4 dégâts par seconde pendant 4 s.",
		},
		passif = {
			nom = "Sang de lave",
			texte = "Immunisé contre la brûlure ; +20 % d'attaque sous 30 % de vie.",
			immunite = "Brulure",
			seuil_vie = 0.3,
			bonus_attaque = 0.2,
		},
		fort_contre = "Glace",
		faible_contre = "Ombre",
	},
	Glace = {
		nom = "Glace",
		element = "Glace",
		titre = "Le Givre éternel",
		description = "Dragon défensif : carapace de givre, souffle qui ralentit puis fige la cible, grand planeur.",
		stats = { vie = 110, attaque = 50, defense = 75, vitesse = 45, agilite = 40, endurance = 65 },
		vitesses = { marche = 3.5, vol = 30, montee = 9, pique = 55 },
		souffle = {
			nom = "Givre",
			forme = "rayon",
			portee = 34,
			angle = 10,
			degats = 12,
			duree = 2.4,
			recharge = 7,
			effet = "Gel",
			effet_duree = 3,
			effet_valeur = 0.4,
			texte = "Gel : ralentit de 40 % ; 2 s dans le souffle figent la cible 1,5 s.",
		},
		passif = {
			nom = "Carapace de givre",
			texte = "-15 % de dégâts subis ; plane sans perdre d'endurance.",
			reduction = 0.15,
			plane_gratuit = true,
		},
		fort_contre = "Foret",
		faible_contre = "Feu",
	},
	Foret = {
		nom = "Forêt",
		element = "Foret",
		titre = "Le Gardien sylvestre",
		description = "Dragon endurant : beaucoup de vie, se régénère au sol, souffle de spores qui empoisonne une zone.",
		stats = { vie = 130, attaque = 55, defense = 60, vitesse = 48, agilite = 42, endurance = 75 },
		vitesses = { marche = 3.8, vol = 28, montee = 8, pique = 50 },
		souffle = {
			nom = "Spores",
			forme = "nuage",
			portee = 18,
			angle = 40,
			degats = 8,
			duree = 2.6,
			recharge = 8,
			effet = "Poison",
			effet_duree = 6,
			effet_valeur = 3,
			zone_duree = 5,
			texte = "Poison : 3 dégâts par seconde pendant 6 s ; le nuage reste 5 s au sol.",
		},
		passif = {
			nom = "Racines",
			texte = "Au sol et immobile depuis 2 s : régénère 2 % de vie par seconde.",
			regen = 0.02,
			delai = 2,
		},
		fort_contre = "Ombre",
		faible_contre = "Glace",
	},
	Ombre = {
		nom = "Ombre",
		element = "Ombre",
		titre = "Le Voile de nuit",
		description = "Dragon rapide et fragile : vole vite, se fond dans l'ombre, souffle qui aveugle.",
		stats = { vie = 85, attaque = 62, defense = 38, vitesse = 75, agilite = 80, endurance = 50 },
		vitesses = { marche = 4.5, vol = 42, montee = 14, pique = 70 },
		souffle = {
			nom = "Ténèbres",
			forme = "cone",
			portee = 22,
			angle = 30,
			degats = 14,
			duree = 1.8,
			recharge = 5,
			effet = "Aveuglement",
			effet_duree = 3,
			effet_valeur = 0.7,
			texte = "Aveuglement : la vue de la cible se brouille (70 %) pendant 3 s.",
		},
		passif = {
			nom = "Voile",
			texte = "Immobile ou de nuit : presque invisible (transparence 0,7) ; première attaque depuis le voile +30 %.",
			transparence = 0.7,
			bonus_embuscade = 0.3,
		},
		fort_contre = "Feu",
		faible_contre = "Foret",
	},
}
Lignees.DATA = DATA

function Lignees.get(nom: string)
	return assert(DATA[nom], "Lignée inconnue : " .. tostring(nom))
end

-- multiplicateur de dégâts d'une lignée contre une autre
function Lignees.affinite(attaquant: string, defenseur: string): number
	local a = Lignees.get(attaquant)
	if a.fort_contre == defenseur then
		return Lignees.AFFINITE_FORT
	elseif a.faible_contre == defenseur then
		return Lignees.AFFINITE_FAIBLE
	end
	return 1
end

return Lignees
