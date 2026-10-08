--[[
	SonsDragonLineage (ModuleScript) : présélection de sons pour Dragon Lineage.
	À placer dans ReplicatedStorage.

	Tous les sons viennent des bibliothèques sous licence du Creator Store
	(ProSoundEffects), utilisables gratuitement dans n'importe quel jeu.

	Chaque besoin a 2 ou 3 candidats : Will écoute avec EcouteSons et garde
	le meilleur. Les autres pourront être supprimés ensuite.
	`boucle = true` : son fait pour tourner en continu (Looped).
]]

local function id(n)
	return "rbxassetid://" .. n
end

return {
	Dragons = {
		RugissementPuissant = {
			{ id = id(9113987603), nom = "Giant Crab Monster Roars 1", duree = 6 },
			{ id = id(9120025244), nom = "Thunder With Lion Roar Searing Blast 16", duree = 3 },
			{ id = id(9113985451), nom = "Roar Constant Deep Throaty Growls 1", duree = 16 },
		},
		GrognementCalme = {
			{ id = id(9125467848), nom = "Lion Deep Guttural Rumbling", duree = 2 },
			{ id = id(9113985445), nom = "Roar Constant Deep Throaty Growls 2", duree = 3 },
		},
		CriAttaque = {
			{ id = id(9125474505), nom = "Pterodactyl Screech Vocals Screams", duree = 1 },
			{ id = id(9113981940), nom = "Pterodactyl Dressed Screams 18", duree = 2 },
		},
		Sifflement = {
			{ id = id(9113991406), nom = "Spider Long Hiss Spray 2", duree = 5 },
			{ id = id(9113990020), nom = "Spider Hiss Exhale 3", duree = 3 },
		},
		BattementAiles = {
			{ id = id(9120781361), nom = "Wings Pterodactyl 2", duree = 5 },
			{ id = id(9125472053), nom = "Pterodactyl Attack Wing Flaps 1", duree = 2 },
			{ id = id(9120782165), nom = "Wings Pterodactyl 1", duree = 33, boucle = true },
		},
		PasLourds = {
			{ id = id(9114080709), nom = "Dinosaur Footsteps Boomy Thumps 16", duree = 2 },
			{ id = id(9125404769), nom = "Boomy Footsteps Giant Thumpy Dinosaur", duree = 3 },
		},
	},

	Feu = {
		SouffleDeFeu = {
			{ id = id(9114439216), nom = "Fire Whoosh 4", duree = 6 },
			{ id = id(9114446277), nom = "Fire Whoosh 6", duree = 2 },
			{ id = id(9114443037), nom = "Fire Whoosh 7", duree = 2 },
		},
		BouleDeFeu = {
			{ id = id(9114446852), nom = "Fire Whoosh 15", duree = 1 },
			{ id = id(9114444008), nom = "Fire Whoosh 3", duree = 1 },
		},
		Brasero = {
			{ id = id(9112780462), nom = "Fireplace Constant Burning Flame 4", duree = 43, boucle = true },
			{ id = id(9112780193), nom = "Fireplace Constant Burning Flame 1", duree = 36, boucle = true },
		},
	},

	Os = {
		Craquement = {
			{ id = id(9113542363), nom = "Bone Cracks 10", duree = 1 },
			{ id = id(9113540599), nom = "Bone Cracks 33", duree = 3 },
			{ id = id(9113546617), nom = "Bone Cracks 30", duree = 2 },
		},
		-- Pas de vrai « cliquetis de squelette » dans la bibliothèque :
		-- un treillis en bois qui s'entrechoque s'en rapproche.
		Cliquetis = {
			{ id = id(9120927210), nom = "Wood Lattice Light Rattle 7", duree = 4 },
		},
		ImpactPierre = {
			{ id = id(9125391808), nom = "Big Rocks Drop Interior Muffled", duree = 11 },
			{ id = id(9118587701), nom = "Rock Drop On Concrete Drops Breaks 4", duree = 2 },
		},
	},

	Oeufs = {
		Fissure = {
			{ id = id(9113958649), nom = "Crack Egg Crunchy 2", duree = 2 },
			{ id = id(9113959106), nom = "Crack Egg Crunchy 7", duree = 4 },
			{ id = id(9113958660), nom = "Crack Egg Crunchy 1", duree = 6 },
		},
		CoqueQuiCasse = {
			{ id = id(9120490359), nom = "Walnuts Crunch Shell Crack Break 2", duree = 5 },
		},
		-- À essayer avec PlaybackSpeed entre 1.2 et 1.5 pour un son plus « bébé ».
		CriBebeDragon = {
			{ id = id(9125596197), nom = "Growls Tiny Creature Cartoon", duree = 1 },
			{ id = id(9125596336), nom = "Growls Tiny Creature Cartoon", duree = 4 },
			{ id = id(9125473997), nom = "Pterodactyl Squawks Wing Flaps", duree = 4 },
		},
	},

	Ambiance = {
		Repaire = {
			{ id = id(9113731969), nom = "Cave Presence Constant Eerie Musical Hum 4", duree = 57, boucle = true },
			{ id = id(9113732233), nom = "Cavernous Winds Empty Eerie Gusts Tonal 3", duree = 43, boucle = true },
		},
		GouttesCaverne = {
			{ id = id(9120505513), nom = "Water Cave Trickle Very Thin 3", duree = 27, boucle = true },
			{ id = id(9126190654), nom = "Water Drips Into Filled Bowl Cave Water Drop", duree = 8 },
		},
		VentMontagne = {
			{ id = id(9114625414), nom = "Gods Wind Spooky Eerie 1", duree = 36, boucle = true },
			{ id = id(9114057104), nom = "Desert Wind Whistley Light Gusts 1", duree = 37, boucle = true },
		},
		DragonQuiPasse = {
			{ id = id(9120697823), nom = "Whoosh By Howling Wind Light Rumbling 1", duree = 7 },
		},
	},

	Interface = {
		Clic = {
			{ id = id(9119717529), nom = "Switch Click On Or Off Toggle Button 1", duree = 0 },
			{ id = id(9113649171), nom = "Button Click And Ring 1", duree = 1 },
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
			{ id = id(9113849492), nom = "Coins Or Keys Jingle 6", duree = 1 },
			{ id = id(9113848469), nom = "Coin Bounce 3", duree = 1 },
		},
	},
}
