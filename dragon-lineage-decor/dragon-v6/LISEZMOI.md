# Dragon v6 riggé : lignées Feu, Glace, Forêt, Ombre

Généré par `generateur/export_dragon_v6.py` (`--lignee Glace Ombre` pour n'en exporter que certaines).
Aperçus : `demo-animations-v6.gif` (course, vol, rugissement, repos), `demo-animations-v6-nouvelles.gif`
(marche, décollage, atterrissage, souffle de feu), `lignees-v6.png` (les 4 lignées).

## Contenu
- `Dragon_V6.glb` (Feu), `Dragon_V6_Glace.glb`, `Dragon_V6_Foret.glb`, `Dragon_V6_Ombre.glb` : même maillage, même
  squelette (42 os), seule la texture palette change. Deux maillages skinnés par fichier :
  - `Dragon` : tout le corps (15 176 triangles, couleurs par face via la petite texture palette)
  - `DragonNeon` : yeux, narines, lame de queue, lueur de gorge (192 triangles, passé en Neon par le script)
- `Palette_<Lignée>.png` : les textures palette (déjà incluses dans les GLB)
- `AnimDragon.lua` : ModuleScript d'animation, commun aux 4 lignées
- `manifest.json` : os (nom, parent, position), lignées et triangles, cases de la palette, animations, vitesses

Couleurs : pour chaque lignée, le corps est un cran plus sombre que la tête. La règle reprend les écarts réglés à la
main pour Feu (saturation et luminosité, teinte gardée), avec un plancher de luminosité pour que l'Ombre ne tourne pas
au noir (`corps_v6.palette`).

## Os
Root → Spine → Chest (tronc souple) ; Neck1-3 → Head → Jaw, EyelidR/L, PupilR/L ; Tail1-6 ;
pattes : FrontUpperLeg / FrontLowerLeg / FrontFoot et BackUpperLeg / BackLowerLeg / BackFoot (R et L) ;
ailes : WingUpper / WingLower / WingFinger1-4 (R et L). 4 os maximum par sommet.

## Import dans Studio
1. Avatar > 3D Importer (ou Fichier > Importer 3D), choisir le GLB de la lignée, garder « Rig » / squelette activé.
2. Vérifier que le Model contient les MeshParts `Dragon` et `DragonNeon` et les objets `Bone`.
3. Mettre `AnimDragon.lua` dans ReplicatedStorage (ModuleScript), puis dans un LocalScript :
   ```lua
   local Anim = require(game.ReplicatedStorage.AnimDragon)
   local d = Anim.new(workspace.Dragon_V6)

   d:play("Course")         -- Repos, Marche, Course, Vol, Rugissement, Decollage, Atterrissage, SouffleFeu
                            -- fondu de 0,25 s entre deux animations ; d:play("Vol", 0) pour couper net
   d:setSpeed(6)            -- choisit Repos / Marche / Course selon la vitesse (studs/s) et cale la foulée
   d:follow(humanoid)       -- la même chose, branchée sur Humanoid.Running
   d:lookAt(joueur.Character)   -- suit du regard (Vector3, BasePart ou Model) ; d:lookAt(nil) pour arrêter
   d:setTurn(0.5)           -- virage (-1 gauche … 1 droite) ; par défaut il est mesuré sur la rotation du Model
   d:setGroundIK(true)      -- pieds posés sur le relief (désactivé par défaut)
   d:blink() ; d:squint(0.4) ; d:look(20, 5)   -- clignement, plisser les yeux, regard imposé (degrés)
   d:destroy()              -- arrête tout et retire les particules
   ```

## Animations
- **Repos** : respiration ; les yeux sautent d'un point à l'autre en ~50 ms (gauche, droite, haut, bas), la tête suit
  plus lentement, du même côté (corrigé : avant, elle tournait à l'opposé du regard), pendant que l'œil revient au
  centre ; micro-mouvements des pupilles, paupières lourdes un instant, un clignement et un double clignement par
  boucle, plus les clignements au hasard.
- **Marche** (nouvelle) : pas latéral à 4 temps (arrière G, avant G, arrière D, avant D), le poids passe d'un côté à
  l'autre, dos en S, la tête hoche à chaque pose d'une patte avant, la queue balaie.
- **Course** (v2) : galop lourd. Le corps s'enfonce un peu à chaque réception (arrière puis avant) et s'allège pendant
  la suspension, au lieu d'osciller en sinus. Le dos se ramasse et s'étend, la foulée est plus longue, les ailes
  repliées s'entrouvrent pendant la suspension, la queue fait contrepoids au tangage et la tête reste stable.
- **Marche et course** : chaque pied reste à plat au sol pendant l'appui en reculant à vitesse constante, roule sur
  ses griffes au décollage, se replie en l'air puis tend les orteils avant de se reposer. Les pattes sont calculées
  par cinématique inverse (IK) dans `generateur/allures_v6.py`.
- **Décollage** (nouveau, 2 s) : s'accroupit en ouvrant les ailes, pousse sur les griffes, premier grand battement,
  monte à 4,5 studs et replie les pattes, puis enchaîne sur Vol.
- **Atterrissage** (nouveau, 1,8 s) : descend ailes en frein, pattes tendues, touche (arrière puis avant), encaisse
  (corps qui s'enfonce, pattes qui plient), replie les ailes, puis enchaîne sur Repos.
- **Souffle de feu** (nouveau, 2,8 s) : inspire en se cabrant (la gorge s'allume), puis crache gueule grande ouverte en
  balayant de droite à gauche. Le script ajoute sous l'os Head un os `Souffle` (sans poids) avec un ParticleEmitter `Feu` et
  une PointLight, de la couleur des yeux de la lignée (flammes bleu glacé pour la Glace, violettes pour l'Ombre…).
  Il enchaîne sur Repos.
- **Vol**, **Rugissement** : inchangés (le rugissement enchaîne sur Repos).

### Déplacement en jeu
Le dragon marche et court sur place : c'est le jeu qui déplace le Model. Pour que les pieds ne patinent pas :
- marche : `Anim.VITESSE_MARCHE` ≈ 2,4 studs/s à cadence normale ;
- course : `Anim.VITESSE_COURSE` ≈ 8,7 studs/s à cadence normale.

`d:setSpeed(v)` ou `d:follow(humanoid)` choisissent l'allure et accélèrent ou ralentissent la cadence
(×0,5 à ×1,8 pour la marche, ×0,6 à ×1,6 pour la course), avec un seuil à hystérésis pour ne pas hésiter entre
les deux. Ils n'agissent pas pendant le vol ni pendant une séquence (décollage, souffle…).

### Fonctions de jeu
- **Fondus** : chaque changement d'animation part de la pose affichée et la rejoint en 0,25 s (paupières et pupilles
  exceptées, pour garder les clignements nets).
- **Regard qui suit une cible** (`lookAt`) : les yeux visent tout de suite (±18° horizontal, ±9° vertical), la tête et
  le cou rattrapent plus lentement (jusqu'à 55°). Si la cible passe derrière lui, il laisse tomber en douceur.
- **Virages** : le dos et le cou se courbent vers l'intérieur, la tête mène, la queue part vers l'extérieur et le
  corps penche. Mesuré tout seul à partir de la rotation du Model, ou imposé par `setTurn`.
- **Pieds sur le relief** (`setGroundIK(true)`) : un rayon sous chaque patte. Le bassin descend de la moyenne des
  quatre hauteurs, puis chaque patte corrige le reste par IK, pied gardé à plat. C'est actif au repos, à la marche, à
  la course, au rugissement et au souffle, pas en vol. Limite : le corps ne s'incline pas encore dans les pentes
  fortes (seules les pattes compensent, jusqu'à ±2,5 studs).

## Déjà vérifié hors Studio
- Les 4 GLB passent le validateur glTF officiel (Khronos) sans erreur ni avertissement ; `Dragon_V6.glb` (Feu) est
  identique octet pour octet à celui déjà importé et testé dans Studio.
- `AnimDragon.lua` exécuté tel quel (Lune, faux Model) : ses `Bone.Transform` appliqués au GLB à la manière de Roblox
  redonnent les poses du générateur (écart ≤ 0,0001 stud sur tous les sommets, 20 instants couvrant les
  8 animations, yeux compris). Relancer : `generateur/verif_anim_v6.luau` puis `generateur/verif_glb_v6.py`.
- Fonctions de jeu (`generateur/test_runtime_v6.luau`, 20 contrôles) : fondu sans à-coup, choix de l'allure et
  hystérésis, enchaînements, virages imposés et mesurés, `lookAt`, création et direction des particules de feu.
  Pieds sur le relief contrôlés dans le maillage (`generateur/test_runtime_v6.py`) : chaque patte monte ou descend de la hauteur du sol à
  0,004 stud près, pied gardé à plat.
- **Pas encore testé dans Studio** : les nouvelles animations et fonctions, les particules de feu (réglages à ajuster
  à l'œil) et les 3 nouvelles lignées.

## Import dans Studio : Feu testé le 2026-10-07, sans erreur, rendu convaincant
Points à garder en tête si on réimporte :
- Unité : le GLB est en studs (dragon ≈ 20 studs de long). Si l'importeur propose une unité, choisir « Stud » ;
  s'il arrive 3,57 fois trop grand ou trop petit, c'est cette conversion mètre/stud.
- Orientation : le modèle regarde vers -Z (l'avant de Roblox). S'il arrive tourné de 180°, le tourner au niveau du Model.
- Si l'importeur sépare les deux maillages en deux squelettes, garder un seul jeu d'os ou réexporter en un seul maillage
  (le Neon se ferait alors avec un SurfaceAppearance émissif).
- La pulsation de la lueur modifie `DragonNeon.Color` : si une texture est appliquée à cette pièce, la retirer
  pour que la couleur Neon s'affiche. La couleur du feu est lue sur `DragonNeon.Color` au lancement.
