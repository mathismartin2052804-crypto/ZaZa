# Dragon v6 riggé (Feu)

Généré par `generateur/export_dragon_v6.py` (aperçu des animations : `demo-animations-v6.gif`).

## Contenu
- `Dragon_V6.glb` : un seul squelette (42 os) et deux maillages skinnés qui le partagent
  - `Dragon` : tout le corps (couleurs par face via la petite texture palette)
  - `DragonNeon` : yeux, narines, lame de queue, lueur de gorge (passé en Neon par le script)
- `Palette_Feu.png` : la texture palette (déjà incluse dans le GLB)
- `AnimDragon.lua` : ModuleScript d'animation (course, vol, rugissement, repos) + contrôle des yeux
- `manifest.json` : liste des os (nom, parent, position), triangles, cases de la palette

## Os
Root → Spine → Chest (tronc souple) ; Neck1-3 → Head → Jaw, EyelidR/L, PupilR/L ; Tail1-6 ;
pattes : FrontUpperLeg / FrontLowerLeg / FrontFoot et BackUpperLeg / BackLowerLeg / BackFoot (R et L) ;
ailes : WingUpper / WingLower / WingFinger1-4 (R et L). 4 os maximum par sommet.

## Import dans Studio
1. Avatar > 3D Importer (ou Fichier > Importer 3D), choisir `Dragon_V6.glb`, garder « Rig » / squelette activé.
2. Vérifier que le Model contient les MeshParts `Dragon` et `DragonNeon` et les objets `Bone`.
3. Mettre `AnimDragon.lua` dans ReplicatedStorage (ModuleScript), puis dans un LocalScript :
   ```lua
   local Anim = require(game.ReplicatedStorage.AnimDragon)
   local d = Anim.new(workspace.Dragon_V6)
   d:play("Course")   -- "Vol", "Rugissement", "Repos"
   d:blink()          -- clignement (il cligne aussi tout seul toutes les 3 à 6 s)
   d:look(20)         -- regard (degrés, + = vers sa droite) ; d:look(nil) rend la main à l'animation
   d:squint(0.4)      -- plisser les yeux
   ```

## À vérifier au premier import (pas encore testé dans Studio)
- Orientation : le modèle regarde vers -Z (l'avant de Roblox). S'il arrive tourné de 180°, le tourner au niveau du Model.
- Si l'importeur sépare les deux maillages en deux squelettes, garder un seul jeu d'os ou réexporter en un seul maillage
  (le Neon se ferait alors avec un SurfaceAppearance émissif).
- La pulsation de la lueur modifie `DragonNeon.Color` : si une texture est appliquée à cette pièce, la retirer
  pour que la couleur Neon s'affiche.
