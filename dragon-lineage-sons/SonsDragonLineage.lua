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
			{ id = nil, fichier = "rawr_gros.ogg", nom = "Gros RAWR grave", duree = 1.65 },
			{ id = nil, fichier = "rawr_moyen.ogg", nom = "RAWR moyen, plus vif", duree = 1.25 },
		},
		GrognementCalme = {
			{ id = nil, fichier = "grr_ronron.ogg", nom = "Ronronnement grave « grrr »", duree = 1.4 },
			{ id = nil, fichier = "grr_court.ogg", nom = "Petit grognement court", duree = 0.7 },
		},
		CriAttaque = {
			{ id = nil, fichier = "yip_aigu.ogg", nom = "Cri qui monte « yip ! »", duree = 0.5 },
			{ id = nil, fichier = "yip_vibre.ogg", nom = "Cri vibrant, plus rigolo", duree = 0.65 },
		},
		Sifflement = {
			{ id = nil, fichier = "pschh.ogg", nom = "Sifflement « pschhh »", duree = 0.8 },
		},
		BattementAiles = {
			{ id = nil, fichier = "flap_3.ogg", nom = "3 battements « fwup fwup fwup »", duree = 0.96 },
			{ id = nil, fichier = "flap_2_lent.ogg", nom = "2 battements lents", duree = 1.0 },
		},
		PasLourds = {
			{ id = nil, fichier = "bwomp.ogg", nom = "Pas lourd « bwomp »", duree = 0.75 },
			{ id = nil, fichier = "bwomp_rebond.ogg", nom = "Pas qui rebondit un peu", duree = 0.8 },
		},
	},
	Feu = {
		SouffleDeFeu = {
			{ id = nil, fichier = "fwoosh_long.ogg", nom = "Grand « FWOOSH » qui crépite", duree = 1.5 },
			{ id = nil, fichier = "fwoosh_court.ogg", nom = "Souffle court", duree = 0.9 },
		},
		BouleDeFeu = {
			{ id = nil, fichier = "fwip_pop.ogg", nom = "« Fwip » puis petit « pouf »", duree = 0.6 },
			{ id = nil, fichier = "fwip.ogg", nom = "« Fwip » seul, très court", duree = 0.25 },
		},
		Brasero = {
			{ id = nil, fichier = "brasero_boucle.ogg", nom = "Crépitement doux en boucle", duree = 7.6, boucle = true },
		},
	},
	Os = {
		Craquement = {
			{ id = nil, fichier = "krak.ogg", nom = "« Krak » sec, comme du bois", duree = 0.65 },
			{ id = nil, fichier = "krak_simple.ogg", nom = "Un seul « krak »", duree = 0.65 },
		},
		Cliquetis = {
			{ id = nil, fichier = "squelette_xylo.ogg", nom = "Squelette au xylophone (classique du cartoon)", duree = 1.07 },
		},
		ImpactPierre = {
			{ id = nil, fichier = "bonk.ogg", nom = "« Bonk » rebondissant", duree = 0.55 },
			{ id = nil, fichier = "bonk_grave.ogg", nom = "« Bonk » grave et lourd", duree = 0.65 },
		},
	},
	Oeufs = {
		Fissure = {
			{ id = nil, fichier = "tik_tik_tik.ogg", nom = "3 petits « tik » qui montent", duree = 0.83 },
			{ id = nil, fichier = "tik_tik.ogg", nom = "2 « tik » rapprochés", duree = 0.55 },
		},
		CoqueQuiCasse = {
			{ id = nil, fichier = "eclosion_pop.ogg", nom = "Crac + POP + étincelles", duree = 1.2 },
			{ id = nil, fichier = "pop_boing.ogg", nom = "POP + petit boing", duree = 0.65 },
		},
		CriBebeDragon = {
			{ id = nil, fichier = "bebe_miaou.ogg", nom = "Deux petits cris mignons", duree = 1.1 },
			{ id = nil, fichier = "bebe_rawr.ogg", nom = "Mini « rawr » de bébé", duree = 0.9 },
		},
	},
	Ambiance = {
		Repaire = {
			{ id = nil, fichier = "repaire_boucle.ogg", nom = "Nappe grave et douce + gouttes", duree = 9.0, boucle = true },
		},
		GouttesCaverne = {
			{ id = nil, fichier = "gouttes_boucle.ogg", nom = "« Plink » de gouttes en boucle", duree = 7.7, boucle = true },
		},
		VentMontagne = {
			{ id = nil, fichier = "vent_boucle.ogg", nom = "Vent doux qui siffle", duree = 9.0, boucle = true },
			{ id = nil, fichier = "vent_doux_boucle.ogg", nom = "Vent doux sans sifflement", duree = 9.0, boucle = true },
		},
		DragonQuiPasse = {
			{ id = nil, fichier = "swoosh.ogg", nom = "« Swoooosh » au passage", duree = 1.5 },
		},
	},
	Interface = {
		Clic = {
			{ id = nil, fichier = "clic_pop.ogg", nom = "Clic « pop » rond", duree = 0.05 },
			{ id = nil, fichier = "clic_bulle.ogg", nom = "Clic bulle, plus grave", duree = 0.08 },
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
			{ id = nil, fichier = "piece_bling.ogg", nom = "Pièce « bling » façon jeu vidéo", duree = 0.45 },
			{ id = nil, fichier = "piece_bling_grave.ogg", nom = "Pièce plus grave", duree = 0.45 },
		},
	},
}
