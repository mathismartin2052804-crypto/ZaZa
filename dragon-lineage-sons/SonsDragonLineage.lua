--[[
	SonsDragonLineage (ModuleScript) : sons de Dragon Lineage.
	À placer dans ReplicatedStorage.

	Deux sortes de sons :
	- les sons cartoon fabriqués pour le jeu (dossier sons-cartoon/) :
	  `id = nil` tant qu'ils ne sont pas importés dans Roblox. Après l'import,
	  remplace nil par id(<numéro donné par Roblox>) ;
	- les sons de récompense et de niveau supérieur, gardés de la bibliothèque
	  Roblox : déjà prêts.
	`boucle = true` : son fait pour tourner en continu (Looped).
]]

local function id(n)
	return "rbxassetid://" .. n
end

return {
	Dragons = {
		RugissementPuissant = {
			{ id = nil, fichier = "rawr_gros.ogg", nom = "« RRRAWR » grave avec r roulé", duree = 1.96 },
			{ id = nil, fichier = "rawr_vif.ogg", nom = "« RAWR ! » plus court et plus vif", duree = 1.67 },
		},
		GrognementCalme = {
			{ id = nil, fichier = "hmmrrr.ogg", nom = "« Hmmmrrr » bouche fermée", duree = 1.73 },
			{ id = nil, fichier = "hmmrrr_court.ogg", nom = "Petit « mrrr » méfiant", duree = 1.24 },
		},
		CriAttaque = {
			{ id = nil, fichier = "hya.ogg", nom = "Cri « hya ! » qui monte", duree = 1.11 },
			{ id = nil, fichier = "sifflet_monte.ogg", nom = "Sifflet à coulisse « fwiiip ! »", duree = 1.12 },
		},
		Sifflement = {
			{ id = nil, fichier = "psshh.ogg", nom = "« Pssshh » doux avec une note qui descend", duree = 1.15 },
			{ id = nil, fichier = "psshh_court.ogg", nom = "« Tss » court, sans note", duree = 0.91 },
		},
		BattementAiles = {
			{ id = nil, fichier = "ailes_3.ogg", nom = "3 battements « fwoump »", duree = 1.31 },
			{ id = nil, fichier = "ailes_2.ogg", nom = "2 battements lents et graves", duree = 1.19 },
		},
		PasLourds = {
			{ id = nil, fichier = "boum.ogg", nom = "Pas « boum » rond", duree = 1.11 },
			{ id = nil, fichier = "boum_marimba.ogg", nom = "Pas « boum » + note de marimba (très cartoon)", duree = 1.08 },
		},
	},
	Feu = {
		SouffleDeFeu = {
			{ id = nil, fichier = "fwooom.ogg", nom = "« FWOOOM » qui gonfle", duree = 1.84 },
			{ id = nil, fichier = "fwoom_court.ogg", nom = "« Fwoom » court et vif", duree = 1.45 },
		},
		BouleDeFeu = {
			{ id = nil, fichier = "fwip_pouf.ogg", nom = "« Fwip » puis « pouf »", duree = 1.1 },
			{ id = nil, fichier = "fwip.ogg", nom = "« Fwip » seul", duree = 0.82 },
		},
		Brasero = {
			{ id = nil, fichier = "brasero_boucle.ogg", nom = "Feu de camp doux qui crépite (boucle)", duree = 9.0, boucle = true },
		},
	},
	Os = {
		Craquement = {
			{ id = nil, fichier = "clac_clac.ogg", nom = "« Clac-clac » de bois sec", duree = 0.73 },
			{ id = nil, fichier = "clac.ogg", nom = "Un seul « clac »", duree = 0.66 },
		},
		Cliquetis = {
			{ id = nil, fichier = "squelette_xylo.ogg", nom = "Squelette au xylophone", duree = 1.45 },
			{ id = nil, fichier = "squelette_xylo_descend.ogg", nom = "Squelette au xylophone, qui descend", duree = 1.53 },
		},
		ImpactPierre = {
			{ id = nil, fichier = "bonk.ogg", nom = "« Bonk ! » qui rebondit", duree = 0.75 },
			{ id = nil, fichier = "bonk_grave.ogg", nom = "« Bonk » grave", duree = 0.74 },
		},
	},
	Oeufs = {
		Fissure = {
			{ id = nil, fichier = "tic_tic_tic.ogg", nom = "3 « tic » cristallins qui montent", duree = 1.13 },
			{ id = nil, fichier = "tic.ogg", nom = "Un seul « tic »", duree = 0.77 },
		},
		CoqueQuiCasse = {
			{ id = nil, fichier = "eclosion_tada.ogg", nom = "Crac + POP + « ta-daa » de clochettes", duree = 2.37 },
			{ id = nil, fichier = "eclosion_boing.ogg", nom = "POP + boing + ding", duree = 2.12 },
		},
		CriBebeDragon = {
			{ id = nil, fichier = "bebe_miou.ogg", nom = "Deux petits « miii-ou »", duree = 1.39 },
			{ id = nil, fichier = "bebe_rawr.ogg", nom = "Mini « rawr » de bébé", duree = 1.47 },
		},
	},
	Ambiance = {
		Repaire = {
			{ id = nil, fichier = "repaire_boucle.ogg", nom = "Nappe douce + gouttes accordées (boucle)", duree = 10.5, boucle = true },
		},
		GouttesCaverne = {
			{ id = nil, fichier = "gouttes_boucle.ogg", nom = "« Plip » de gouttes à gauche et à droite (boucle)", duree = 7.5, boucle = true },
		},
		VentMontagne = {
			{ id = nil, fichier = "vent_boucle.ogg", nom = "Vent doux qui chante un peu (boucle)", duree = 10.5, boucle = true },
			{ id = nil, fichier = "vent_doux_boucle.ogg", nom = "Vent doux seul (boucle)", duree = 10.5, boucle = true },
		},
		DragonQuiPasse = {
			{ id = nil, fichier = "passage.ogg", nom = "Souffle qui passe de gauche à droite", duree = 1.3 },
		},
	},
	Interface = {
		Clic = {
			{ id = nil, fichier = "clic_bulle.ogg", nom = "Clic « bloup » rond", duree = 0.35 },
			{ id = nil, fichier = "clic_bois.ogg", nom = "Clic « toc » de bois", duree = 0.33 },
		},
		Recompense = {
			{ id = id(9116394545), nom = "Magic Glows Soft Clusters Of Chiming Hits 1", duree = 1 },
			{ id = id(9116395085), nom = "Magic Glows Soft Clusters Of Chiming Hits 5", duree = 4 },
			{ id = id(9119447936), nom = "Sparkle Bell Tree Wind Chimes 1", duree = 5 },
		},
		NiveauSuperieur = {
			{ id = id(9125644775), nom = "Magic Twirling Small High Pitch Spinning", duree = 3 },
		},
		Pieces = {
			{ id = nil, fichier = "piece_bling.ogg", nom = "Pièce « bling » (deux notes)", duree = 1.27 },
			{ id = nil, fichier = "piece_etincelles.ogg", nom = "Pièce + petites étincelles", duree = 1.35 },
		},
	},
}
