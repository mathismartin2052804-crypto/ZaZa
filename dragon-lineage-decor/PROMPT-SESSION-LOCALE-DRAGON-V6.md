# Dragon Lineage : dragon v6, 4 lignées (instructions pour une nouvelle session locale)

> **Colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir
> dézippé `dragon-v6-lignees.zip` (ou récupéré le dossier `dragon-lineage-decor/dragon-v6/` du dépôt ZaZa, branche
> `claude/adoring-mccarthy-vim1gn`).

---

## Contexte
Tu aides sur le jeu Roblox **Dragon Lineage** (Team Create). Il faut **importer le dragon v6 dans ses 4 lignées**
(Feu, Glace, Forêt, Ombre), brancher ses scripts et **tout tester dans Studio** : rien n'a encore été vu dans Studio
à part une première version du Feu. Le jeu est en compétition : rendu soigné, rien de cassé.

Parle en **français**, simplement : l'utilisateur débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : (Claude) dragon v6 lignées`.
- **Ne supprime rien** : l'ancien `Dragon_V6` (Feu, première version) va dans `ServerStorage > MapBackup_<date>`.
- Fais d'abord **une seule lignée (Feu)** de bout en bout, montre une capture, attends l'accord, puis fais les 3 autres.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Les fichiers (dossier `dragon-v6/`)
- `Dragon_V6.glb` (Feu), `Dragon_V6_Glace.glb`, `Dragon_V6_Foret.glb`, `Dragon_V6_Ombre.glb` : même squelette
  (**42 os**), corps commun, ornements et couleurs propres à chaque lignée (Feu : cornes au bout incandescent et
  cheminées de lave ; Glace : cristaux ; Forêt : bois de cerf et feuilles ; Ombre : épines et runes).
  Chaque GLB contient **2 MeshParts skinnées** : `Dragon` (le corps, 15 776 à 18 248 triangles) et `DragonNeon`
  (yeux, lueurs et ornements lumineux).
- `AnimDragon.lua` : ModuleScript d'animation (commun aux 4 lignées).
- `LigneesDragon.lua` : ModuleScript de données (stats, vitesses, passifs, affinités, souffle commun).
- `LISEZMOI.md` : tout le détail (lis-le d'abord), `manifest.json`, `Palette_*.png` (déjà dans les GLB).

## A. Import (à faire par l'utilisateur, guide-le)
Pour chaque GLB : **Avatar → Import 3D** (ou Fichier → Importer 3D).
- Unité **Stud**. Le dragon fait environ 20 studs de long ; s'il arrive 3,57 fois trop grand ou trop petit, c'est
  l'unité.
- Garder le **rig / squelette** activé ; ne pas fusionner les maillages.
- Le dragon doit regarder vers **-Z**. S'il arrive tourné de 180°, tourner le **Model** entier, pas les pièces.

Ensuite, vérifie par MCP pour chaque Model (`Dragon_V6`, `Dragon_V6_Glace`, `Dragon_V6_Foret`, `Dragon_V6_Ombre`) :
1. 2 MeshParts `Dragon` et `DragonNeon`, et 42 `Bone` (Root, Spine, Chest, Neck1-3, Head, Jaw, Eyelid/Pupil R/L,
   Tail1-6, pattes, ailes ; liste exacte dans `manifest.json`).
2. Si l'importeur a créé **deux squelettes** (un par MeshPart), le signaler : il n'en faut qu'un.
3. Mets les MeshParts en `Anchored = true` et `CanCollide = false` pour les tests.
4. Si une texture est appliquée à `DragonNeon`, la retirer (sinon la couleur Neon ne s'affiche pas).
5. Mets un attribut texte `Lignee` sur chaque Model : `Feu`, `Glace`, `Foret`, `Ombre` (sans accent).
6. Pose les 4 dragons côte à côte, à 30 studs d'écart, sur un sol plat ; prévois à côté une **pente** et quelques
   **marches** (Parts) pour tester les pieds sur le relief.

## B. Scripts
1. `AnimDragon.lua` → **ModuleScript** `ReplicatedStorage > AnimDragon` (copier le contenu tel quel).
2. `LigneesDragon.lua` → **ModuleScript** `ReplicatedStorage > LigneesDragon`.
3. **LocalScript** `StarterPlayer > StarterPlayerScripts > TestDragon` (script de test, à retirer après) :

```lua
-- Test du dragon v6 : pilote un dragon au clavier.
-- N : lignée suivante   B : marcher / s'arrêter   T : décoller   G : atterrir
-- I / K : monter / descendre (en vol)   J / L : virer à gauche / à droite   F : souffle   R : rugir
-- O : le dragon te regarde (on/off)   P : pieds sur le relief (on/off)
local RS = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Anim = require(RS:WaitForChild("AnimDragon"))
local Lignees = require(RS:WaitForChild("LigneesDragon"))

local NOMS = { "Dragon_V6", "Dragon_V6_Glace", "Dragon_V6_Foret", "Dragon_V6_Ombre" }
local idx, d, model, sol = 0, nil, nil, 0
local marche, haut, virage, regard, relief, descente = false, 0, 0, false, false, false

local function suivant()
	if d then d:destroy() end
	idx = idx % #NOMS + 1
	model = workspace:WaitForChild(NOMS[idx])
	d = Anim.new(model)
	sol = model:GetPivot().Position.Y
	marche, haut, descente = false, 0, false
	local c = Lignees.get(d.lignee)
	print(("Lignée %s (%s) : vie %d, vol %d studs/s, passif %s"):format(d.lignee, c.titre, c.stats.vie,
		c.vitesses.vol, c.passif.nom))
end
suivant()

UIS.InputBegan:Connect(function(input, gp)
	if gp then return end
	local k = input.KeyCode
	if k == Enum.KeyCode.N then suivant()
	elseif k == Enum.KeyCode.B then marche = not marche
	elseif k == Enum.KeyCode.T then d:decoller()
	elseif k == Enum.KeyCode.G then descente = true          -- redescend jusqu'au sol, puis atterrit
	elseif k == Enum.KeyCode.I then haut = 1
	elseif k == Enum.KeyCode.K then haut = -1
	elseif k == Enum.KeyCode.J then virage = 1
	elseif k == Enum.KeyCode.L then virage = -1
	elseif k == Enum.KeyCode.F then if not d:enVol() then d:play("SouffleFeu") end
	elseif k == Enum.KeyCode.R then if not d:enVol() then d:play("Rugissement") end
	elseif k == Enum.KeyCode.O then
		regard = not regard
		d:lookAt(regard and Players.LocalPlayer.Character or nil)
	elseif k == Enum.KeyCode.P then
		relief = not relief
		d:setGroundIK(relief)
	end
end)
UIS.InputEnded:Connect(function(input)
	local k = input.KeyCode
	if k == Enum.KeyCode.I or k == Enum.KeyCode.K then haut = 0 end
	if k == Enum.KeyCode.J or k == Enum.KeyCode.L then virage = 0 end
end)

-- le jeu déplace le Model ; AnimDragon mesure la vitesse, la montée et le virage tout seul
RunService.Heartbeat:Connect(function(dt)
	if not d then return end
	local c = Lignees.get(d.lignee)
	local cf = model:GetPivot() * CFrame.Angles(0, virage * 1.2 * dt, 0)
	if d.current == "Vol" then
		local montee = haut * c.vitesses.montee
		if descente then
			montee = -c.vitesses.montee
			if cf.Position.Y <= sol + 0.05 then
				descente, montee = false, 0
				cf = cf - Vector3.new(0, cf.Position.Y - sol, 0)
				d:atterrir()
			end
		end
		cf = cf + cf.LookVector * (0.6 * c.vitesses.vol * dt) + Vector3.new(0, montee * dt, 0)
	elseif d.current == "Repos" or d.current == "Marche" then
		local v = marche and c.vitesses.marche or 0
		d:setSpeed(v)
		cf = cf + cf.LookVector * (v * dt)
	end
	model:PivotTo(cf)
end)
```

## C. Ce qu'il faut tester (Feu d'abord, puis les 3 autres)
Pour chaque point, fais une capture ou décris ce que tu vois ; note ce qui ne va pas.
1. **Rendu** : couleurs de la lignée, ornements bien collés au corps (rien qui flotte), `DragonNeon` lumineux
   (yeux, et pour Feu les bouts de cornes et les lueurs, pour Ombre les runes).
2. **Repos** : respiration, yeux qui sautent d'un point à l'autre, la tête suit du même côté, clignements.
3. **Marche** (B) : les pieds ne patinent pas, aucun ornement ne traverse le corps ni les ailes repliées.
   Il n'y a **plus de course** : `d:play("Course")` doit donner une erreur, c'est voulu.
4. **Décollage** (T) puis **vol** : 4 battements puis du vol plané ; l'aile se replie à la remontée, le corps et la
   queue ondulent, la tête reste stable. Chaque lignée vole à sa façon : Glace plane longtemps, Forêt bat lourdement,
   Ombre plane ailes balayées vers l'arrière.
5. **Contrôle du vol** : maintenir I (monter) → il bat sans planer et se cabre ; maintenir K (descendre vite) → il
   plane ailes repliées en arrière, nez baissé ; J / L → il s'incline fort dans le virage.
6. **Atterrissage** (G) : il redescend, se pose (arrière puis avant), replie les ailes, puis Repos.
7. **Souffle** (F) : particules et lumière qui sortent **de la gueule, vers l'avant**, teintées de la couleur des yeux
   de la lignée. Le souffle est le même pour toutes les lignées. Ajuster à l'œil si besoin (taille, vitesse, durée de
   vie) dans `generateur/AnimDragon_modele.lua` (fonction `_creerFeu`) puis régénérer, ou noter les valeurs pour moi.
8. **Rugissement** (R), **regard** (O : il te suit des yeux puis de la tête, lâche si tu passes derrière lui).
9. **Pieds sur le relief** (P) : amène le dragon sur les marches et la pente ; chaque patte doit se poser sur le sol.
   Limite connue : le corps ne s'incline pas dans les pentes fortes (seules les pattes compensent, jusqu'à ±2,5 studs).
10. **Console** : aucune erreur rouge, ni avertissement venant de `AnimDragon`.

## Si ça ne marche pas
- « Os introuvable : … » : l'importeur a renommé ou fusionné des os ; liste les `Bone` du Model et compare avec
  `manifest.json`.
- Dragon couché, retourné ou à la mauvaise taille : voir l'étape A (unité Stud, -Z vers l'avant).
- Maillage qui se déforme bizarrement : vérifier qu'il n'y a qu'un seul squelette et que les deux MeshParts sont
  dans le même Model que les os.
- Lueurs grises : retirer la texture de `DragonNeon` (la couleur Neon vient de `DragonNeon.Color`).
- Ne modifie pas `AnimDragon.lua` à la main pour corriger une pose : il est généré. Décris le problème (lignée,
  animation, moment, capture) pour qu'il soit corrigé dans le générateur.

## Fin
- Une capture de chaque lignée au repos et en vol.
- Liste de ce qui marche / ne marche pas pour chaque point de C.
- Console sans erreur rouge ; `TestDragon` retiré ou désactivé si on ne s'en sert plus.
- Entrée dans `DevJournal`, et retire la ligne `EN COURS`.
