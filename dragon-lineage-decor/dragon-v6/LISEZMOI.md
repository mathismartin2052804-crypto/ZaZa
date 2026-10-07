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
   d:look(20, 5)      -- regard (degrés : + = vers sa droite, + = vers le haut) ; d:look(nil) rend la main à l'animation
   d:squint(0.4)      -- plisser les yeux
   d:setRate(vitesse / Anim.VITESSE_COURSE)   -- course : cale la foulée sur la vitesse de déplacement réelle
   ```

## Animations
- **Course** (refaite) : galop lourd où chaque pied reste posé à plat au sol pendant l'appui et recule à vitesse
  constante, roule sur ses griffes au décollage, se replie en l'air puis tend les orteils avant de se reposer.
  Les angles des pattes sont calculés par cinématique inverse dans `generateur/course_v6.py` et copiés dans
  `AnimDragon.lua` (table `COURSE`). Le corps ne rebondit plus (0,1 stud de balancement), la tête reste stable,
  le cou, la queue et les ailes repliées suivent avec du retard.
  Le dragon court sur place : en jeu, le déplacer à `Anim.VITESSE_COURSE` (≈ 7,3 studs/s) ou appeler
  `d:setRate(vitesse / Anim.VITESSE_COURSE)` pour que ses pieds ne patinent pas.
- **Vol**, **Rugissement** : inchangés.
- **Repos** : respiration ; les yeux sautent d'un point à l'autre en ~50 ms (à gauche, à droite, en haut, en bas),
  puis la tête suit plus lentement pendant que l'œil revient au centre ; micro-mouvements des pupilles, paupières
  lourdes un instant, un clignement et un double clignement par boucle (en plus des clignements au hasard).

## Déjà vérifié hors Studio
- `Dragon_V6.glb` passe le validateur glTF officiel (Khronos) sans erreur ni avertissement.
- `AnimDragon.lua` exécuté tel quel (Lune, faux Model) : ses `Bone.Transform` appliqués au GLB à la manière de Roblox
  redonnent exactement les poses du générateur (écart ≤ 0,0001 stud sur tous les sommets ; course, vol, rugissement,
  repos, yeux compris : clignements, saccades et regard vertical).
  Relancer : `generateur/verif_anim_v6.luau` puis `generateur/verif_glb_v6.py` (instructions en tête des fichiers).

## Import dans Studio : testé le 2026-10-07, sans erreur, rendu convaincant
Points à garder en tête si on réimporte :
- Unité : le GLB est en studs (dragon ≈ 20 studs de long). Si l'importeur propose une unité, choisir « Stud » ;
  s'il arrive 3,57 fois trop grand ou trop petit, c'est cette conversion mètre/stud.
- Orientation : le modèle regarde vers -Z (l'avant de Roblox). S'il arrive tourné de 180°, le tourner au niveau du Model.
- Si l'importeur sépare les deux maillages en deux squelettes, garder un seul jeu d'os ou réexporter en un seul maillage
  (le Neon se ferait alors avec un SurfaceAppearance émissif).
- La pulsation de la lueur modifie `DragonNeon.Color` : si une texture est appliquée à cette pièce, la retirer
  pour que la couleur Neon s'affiche.
