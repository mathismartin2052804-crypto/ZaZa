# Dragon v6 riggé : lignées Feu, Glace, Forêt, Ombre

Généré par `generateur/export_dragon_v6.py` (`--lignee Glace Ombre` pour n'en exporter que certaines).
Aperçus : `demo-animations-v6.gif` (vol v2 de profil et de face, rugissement, repos), `demo-animations-v6-nouvelles.gif`
(marche, décollage, atterrissage, souffle de feu), `demo-vol-lignees-v6.gif` (le vol des 4 lignées),
`lignees-v6.png` (les 4 lignées : ornements, vol plané, caractéristiques).

## Contenu
- `Dragon_V6.glb` (Feu), `Dragon_V6_Glace.glb`, `Dragon_V6_Foret.glb`, `Dragon_V6_Ombre.glb` : même squelette
  (42 os) et même corps ; chaque lignée a ses ornements et sa palette. Deux maillages skinnés par fichier :
  - `Dragon` : tout le corps (15 776 à 18 248 triangles selon la lignée, couleurs par face via la texture palette)
  - `DragonNeon` : yeux, narines, lame de queue, lueur de gorge, et pour Feu et Ombre leurs ornements lumineux
    (192 à 1 344 triangles, passé en Neon par le script)
- `Palette_<Lignée>.png` : les textures palette (déjà incluses dans les GLB)
- `AnimDragon.lua` : ModuleScript d'animation, commun aux 4 lignées (style de vol propre à chacune)
- `LigneesDragon.lua` : ModuleScript de données, caractéristiques de jeu des lignées (stats, vitesses, passif,
  affinités) et souffle commun
- `manifest.json` : os (nom, parent, position), lignées (triangles, cases de la palette, ornements, caractéristiques),
  animations, vitesses

## Lignées : ce qui les différencie
Source unique : `generateur/lignees_v6.py`. Valeurs de départ, à équilibrer en jeu.

| | Feu — Le Brasier | Glace — Le Givre éternel | Forêt — Le Gardien sylvestre | Ombre — Le Voile de nuit |
|---|---|---|---|---|
| Silhouette | cornes d'obsidienne au bout incandescent, cheminées d'obsidienne à cœur de lave (cou, queue), fissures de lave, fournaise au poitrail, ergots aux coudes | couronne de cristaux sur la nuque, givre sur les cornes, grappes de cristaux (cou, queue, coudes, genoux, poignets des ailes) | bois de cerf ramifiés, feuilles (nuque, cou, queue, coudes, poignets des ailes), touffe au bout de la queue | grandes épines de nuque, épines recourbées (cou, queue, coudes, ailes), runes lumineuses (cou, épaules, cuisses, queue) |
| Rôle | attaque | défense, planeur | endurance, zone | vitesse, embuscade |
| Vie / Att / Déf / Vit / Agi | 100 / 72 / 50 / 55 / 50 | 110 / 50 / 75 / 45 / 40 | 130 / 55 / 60 / 48 / 42 | 85 / 62 / 38 / 75 / 80 |
| Vol (studs/s) | 34 | 30 | 28 | 42 |
| Passif | Sang de lave : immunisé à la brûlure, +20 % d'attaque sous 30 % de vie | Carapace de givre : -15 % de dégâts, plane sans endurance | Racines : immobile au sol, +2 % de vie par seconde | Voile : immobile ou de nuit, presque invisible ; +30 % sur la première attaque |
| Vol (style) | boucle 3,6 s, plané 30 % | ample et lent, 4,4 s, plané 42 % | lourd, battements rapides, plané 20 % | rapide, corps qui ondule, ailes balayées en plané |
| Bat / craint | Glace / Ombre | Forêt / Feu | Ombre / Glace | Feu / Forêt |

Affinités : cycle Feu > Glace > Forêt > Ombre > Feu, dégâts x1,25 contre la lignée battue, x0,8 contre celle qui
vous bat (`Lignees.affinite(attaquant, defenseur)`). Le souffle est le même pour toutes les lignées
(`Lignees.SOUFFLE` : cône de 28 studs, 16 dégâts/s, brûlure) ; seule sa couleur suit celle des yeux. Les passifs et
la brûlure sont décrits dans les données : c'est au code de combat du jeu de les appliquer.

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
3. Mettre `AnimDragon.lua` et `LigneesDragon.lua` dans ReplicatedStorage (ModuleScripts), puis dans un LocalScript :
   ```lua
   local Anim = require(game.ReplicatedStorage.AnimDragon)
   local d = Anim.new(workspace.Dragon_V6_Glace)  -- lignée : 2e argument, sinon attribut « Lignee » du Model,
                                                  -- sinon son nom (Dragon_V6_Glace…), sinon Feu ; d.lignee

   d:play("Marche")         -- Repos, Marche, Vol, Rugissement, Decollage, Atterrissage, SouffleFeu
                            -- fondu de 0,25 s entre deux animations ; d:play("Vol", 0) pour couper net
   d:setSpeed(3)            -- au sol : Repos ou Marche selon la vitesse (studs/s), cadence calée sur v
   d:follow(humanoid)       -- la même chose, branchée sur Humanoid.Running
   d:decoller()             -- s'il est au sol : Decollage puis Vol (pas de course : pour aller vite, il vole)
   d:atterrir()             -- s'il vole : Atterrissage puis Repos ; d:enVol() dit s'il est en l'air
   d:setFlight(30, 8)       -- en vol : vitesse et vitesse verticale (studs/s) ; sans appel, mesurées sur le Model
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
- **Course** : retirée. Le dragon marche, ou décolle et vole.
- **Marche** : pas latéral à 4 temps (arrière G, avant G, arrière D, avant D), le poids passe d'un côté à
  l'autre, dos en S, la tête hoche à chaque pose d'une patte avant, la queue balaie.
- **Marche** : chaque pied reste à plat au sol pendant l'appui en reculant à vitesse constante, roule sur
  ses griffes au décollage, se replie en l'air puis tend les orteils avant de se reposer. Les pattes sont calculées
  par cinématique inverse (IK) dans `generateur/allures_v6.py`.
- **Décollage** (nouveau, 2 s) : s'accroupit en ouvrant les ailes, pousse sur les griffes, premier grand battement,
  monte à 4,5 studs et replie les pattes, puis enchaîne sur Vol.
- **Atterrissage** (nouveau, 1,8 s) : descend ailes en frein, pattes tendues, touche (arrière puis avant), encaisse
  (corps qui s'enfonce, pattes qui plient), replie les ailes, puis enchaîne sur Repos.
- **Souffle de feu** (2,8 s) : inspire en se cabrant (la gorge s'allume), puis crache gueule grande ouverte en
  balayant de droite à gauche. Le script ajoute sous l'os Head un os `Souffle` (sans poids) avec un ParticleEmitter
  `Feu` et une PointLight, communs à toutes les lignées et teintés de la couleur de leurs yeux. Il enchaîne sur Repos.
- **Vol** (v2, moins rigide) : une boucle = 4 battements puis du vol plané.
  - Battement asymétrique : descente rapide (42 % du temps), remontée lente. L'avant-bras et les doigts suivent avec
    retard, le bout de l'aile fouette. À la remontée, l'aile se replie et se balaie vers l'arrière ; à la descente,
    elle est tendue jusqu'au bout.
  - Le corps monte pendant la descente des ailes (avec retard) ; le dos, le cou et la queue ondulent en vagues
    décalées ; la tête reste stable comme celle d'un oiseau ; les pattes ballottent, la droite et la gauche décalées.
  - Vol plané : ailes tendues en léger dièdre, petites corrections de rafales (roulis), queue qui gouverne, regard
    qui balaie le sol.
  - Chaque lignée a son style (`lignees_v6.STYLE`) : Feu équilibré ; Glace ample, lent, grand planeur ; Forêt lourd,
    battements rapides, corps qui monte et descend ; Ombre rapide, corps serpentin, ailes balayées en faucon.
  - En jeu (`setFlight`, ou mesuré sur le Model) : en montée, il bat sans planer, plus vite, corps cabré ; en
    sur-place (moins de 35 % de sa vitesse de vol), il bat sans planer ; en croisière, il alterne ; en piqué,
    il plane ailes balayées vers l'arrière, nez baissé ; dans les virages il s'incline fort (24° contre 6° au sol).
- **Rugissement** : inchangé (enchaîne sur Repos).

### Déplacement en jeu
Le dragon marche sur place : c'est le jeu qui déplace le Model. Pour que les pieds ne patinent pas, la marche fait
`Anim.VITESSE_MARCHE` ≈ 2,4 studs/s à cadence normale ; `d:setSpeed(v)` ou `d:follow(humanoid)` accélèrent ou
ralentissent la cadence (×0,5 à ×2, soit jusqu'à ~4,8 studs/s), avec un seuil à hystérésis pour l'arrêt. Au-delà, le
jeu fait décoller le dragon (`d:decoller()`) et le déplace en vol (vitesses de vol par lignée dans `LigneesDragon`).
Ils n'agissent pas pendant le vol ni pendant une séquence (décollage, souffle…).

### Fonctions de jeu
- **Fondus** : chaque changement d'animation part de la pose affichée et la rejoint en 0,25 s (paupières et pupilles
  exceptées, pour garder les clignements nets).
- **Regard qui suit une cible** (`lookAt`) : les yeux visent tout de suite (±18° horizontal, ±9° vertical), la tête et
  le cou rattrapent plus lentement (jusqu'à 55°). Si la cible passe derrière lui, il laisse tomber en douceur.
- **Virages** : le dos et le cou se courbent vers l'intérieur, la tête mène, la queue part vers l'extérieur et le
  corps penche. Mesuré tout seul à partir de la rotation du Model, ou imposé par `setTurn`.
- **Pieds sur le relief** (`setGroundIK(true)`) : un rayon sous chaque patte. Le bassin descend de la moyenne des
  quatre hauteurs, puis chaque patte corrige le reste par IK, pied gardé à plat. C'est actif au repos, à la marche, au
  rugissement et au souffle, pas en vol. Limite : le corps ne s'incline pas encore dans les pentes
  fortes (seules les pattes compensent, jusqu'à ±2,5 studs).

## Déjà vérifié hors Studio
- Les 4 GLB passent le validateur glTF officiel (Khronos, gltf-validator 2.0.0-dev.3.10) sans erreur ni
  avertissement.
- `AnimDragon.lua` exécuté tel quel (Lune, faux Model) : ses `Bone.Transform` appliqués au GLB de chaque lignée à la
  manière de Roblox redonnent les poses du générateur, ornements compris (écart ≤ 0,0001 stud sur tous les sommets,
  19 instants couvrant les 7 animations, yeux compris, pour chacune des 4 lignées ; vol avec le style de la lignée).
  Relancer : `generateur/verif_anim_v6.luau` puis `generateur/verif_glb_v6.py ../dragon-v6 anim_v6.json`.
- Fonctions de jeu (`generateur/test_runtime_v6.luau`, 63 contrôles) : fondu sans à-coup, marche et hystérésis,
  plus de course, décoller / atterrir, enchaînements, vol v2 de chaque lignée (battements puis plané), montée
  (imposée et mesurée), sur-place, croisière et piqué, roulis en vol, virages imposés et mesurés, `lookAt`, choix de la lignée,
  particules et lumière du souffle (teinte de la lignée), `LigneesDragon` (affinités, souffle commun).
  Pieds sur le relief contrôlés dans le maillage (`generateur/test_runtime_v6.py`) : chaque patte monte ou descend de la hauteur du sol à
  0,004 stud près, pied gardé à plat.
- **Pas encore testé dans Studio** : les ornements des lignées (Feu compris : son GLB a changé, à réimporter), le
  vol v2, le contrôle du vol, les particules du souffle (réglages à ajuster à l'œil), les pieds sur le relief.
  Triangles par maillage sous la limite de 20 000 de Roblox (18 248 au plus, Glace).

## Import dans Studio : Feu testé le 2026-10-07, sans erreur, rendu convaincant
Points à garder en tête si on réimporte :
- Unité : le GLB est en studs (dragon ≈ 20 studs de long). Si l'importeur propose une unité, choisir « Stud » ;
  s'il arrive 3,57 fois trop grand ou trop petit, c'est cette conversion mètre/stud.
- Orientation : le modèle regarde vers -Z (l'avant de Roblox). S'il arrive tourné de 180°, le tourner au niveau du Model.
- Si l'importeur sépare les deux maillages en deux squelettes, garder un seul jeu d'os ou réexporter en un seul maillage
  (le Neon se ferait alors avec un SurfaceAppearance émissif).
- La pulsation de la lueur modifie `DragonNeon.Color` : si une texture est appliquée à cette pièce, la retirer
  pour que la couleur Neon s'affiche. La couleur du feu est lue sur `DragonNeon.Color` au lancement.
