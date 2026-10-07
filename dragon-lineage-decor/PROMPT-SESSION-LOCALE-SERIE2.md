# Dragon Lineage : refonte de la carte, série 2 (instructions pour une nouvelle session locale)

> **Will : colle tout ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP). Garde le dossier `meshes-serie2/` à portée de main.
> Tu dois avoir **importé toi-même** les modèles avant l'étape B (voir « Import »).

---

## Qui, quoi, pourquoi
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (tycoon de dragons, PlaceId 103674521990306, Team Create). Sa part est **le monde et la course** : `Workspace > Map`, `Workspace > Lairs`, `ServerStorage > LairTemplate`, `RoadService`, `WildService`, `EventService`, les sons et l'ambiance.

Le jeu est **en compétition** contre d'autres équipes. La carte doit être **la plus belle et la plus lisible possible**, sans casser le jeu et en restant fluide sur téléphone.

Will débute : parle en **français**, simplement, et explique ce que tu fais.

### Règles d'équipe (obligatoires)
1. Le jeu dans Studio (Team Create) est **la seule référence**. Ne régénère et ne réimporte jamais la carte depuis des fichiers.
2. **Avant de commencer**, lis `ServerStorage > DevJournal` et ajoute en haut : `EN COURS : Will (Claude) refonte de la carte, série 2`.
3. Ne touche **qu'à la part de Will**. Si un script d'Aidan (`LairService`…) ou de Lylian dépend d'un objet que tu veux changer, **ne le modifie pas** : écris `DEMANDE à <prénom> : …` dans le journal et préviens Will.
4. **Ne supprime rien.** Déplace l'ancien décor dans `ServerStorage > MapBackup_<date>`. On ne le supprime qu'après le test d'équipe.
5. **Zone test, capture d'écran, accord de Will, puis le reste de la carte**, pour chaque grande étape (B à F).
6. Fin de session : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## État actuel (d'après la dernière capture de Will)
- La série 1 est déjà en place : sapins, feuillus, arbres-repères avec nid, fougères, rochers moussus, braseros à serres, lanternes à cristal. Les modèles sont dans `ServerStorage > MapProps`.
- La carte, vue de haut : un autel central avec des piliers, un anneau de route (l'Egg Road), 8 chemins vers 8 repaires « Free Lair » en étoile, des montagnes enneigées tout autour et 3 îles flottantes en forme de cube et de pyramide.
- Ce qui reste à améliorer :
  - arbres répartis trop régulièrement, surtout dans l'anneau central (effet grille) ;
  - feuillus presque noirs dans la brume ;
  - sol vert uni et plat ;
  - portes « Free Lair » et arche « Egg Road » encore faites de blocs ;
  - limites des repaires qui ne sont que des bandes grises ;
  - îles flottantes en cube.

## Import (fait par Will, à la main)
1. **Avatar → Import 3D**, un `.glb` à la fois, avec l'unité **Stud** (vérifie la taille avec le tableau ; si c'est environ 3,5 fois trop grand ou trop petit, change l'unité, car le format .glb est prévu en mètres), les **parties séparées** (pas de fusion) et **Anchored** coché.
2. Ranger les modèles dans `ServerStorage > MapProps` (le même dossier que la série 1).
3. `Decal_Scorch.png` : l'importer avec le **Gestionnaire de ressources** (Asset Manager → Images). Will te donne ensuite l'**ID d'image** (`rbxassetid://…`).

Toi : vérifie que les 10 modèles sont là, avec les bonnes parties, puis applique l'étape A.

| Modèle | Parties | Taille (studs, L × H × P) | Remarques |
|---|---|---|---|
| `Dragon_Skeleton` | Bones, Sockets | 27 × 18 × 67 | Squelette géant à moitié enterré. **L'enfoncer d'environ 1,5 stud** : les côtes et l'aile doivent sortir du sol, pas flotter. Le crâne est au bout, côté +Z. |
| `Dragon_Skull` | Bones, Sockets | 4 × 7 × 15 | Crâne seul, à placer en décor. |
| `Gate_Lair` | Stone, Bones, Sign, Flame, Sockets | 21 × 19 × 9,5 | Porte de repaire : 2 piliers, des cornes, un crâne et un panneau. Passage d'environ 13 studs. |
| `Gate_EggRoad` | Stone, StoneDark, Bones, Sign, Iron, Sockets | 27 × 29 × 12 | Arche en pierre avec un crâne en clé de voûte et un panneau suspendu. Passage d'environ 18 studs. |
| `Wall_Straight_8`, `Wall_Straight_4` | Stone, StoneDark | 8 (ou 4) × 3 × 1,7 | Muret modulaire, aligné sur l'axe X. Mettre les modules bout à bout. |
| `Wall_Broken_8` | Stone, StoneDark | 8 × 3 × 3,7 | Muret écroulé, avec des pierres au sol. Environ 15 % des modules. |
| `Wall_Post` | Stone | 2,3 × 4,4 × 2,3 | Poteau pour les angles, les extrémités et environ tous les 16 studs. |
| `Island_Large`, `Island_Small` | Grass, Rock, Roots, Crystal | 28 × 27 / 14 × 13 | Îles flottantes. **Leur pivot est à la pointe du bas** : penses-y en les plaçant. |

Le panneau (`Sign`) est tourné vers +Z dans le fichier. Dans Studio, vérifie quelle face (`Front` ou `Back`) regarde la route avant d'y mettre le `SurfaceGui`.

---

## A. Réglages des modèles (dans `MapProps`)
- `Color` et `Material` de chaque partie : d'après `meshes-serie2/manifest.json`. `Flame` et `Crystal` sont en **Neon**, avec `CastShadow = false`.
- Pour tous : `Anchored = true` et `CanTouch = false`.
- **Collisions** (attention, une collision « Hull » remplit l'ouverture d'une arche) :
  - `Gate_Lair` et `Gate_EggRoad` :
    - parties en mesh : `CanCollide = false`, `CanQuery = false` ;
    - ajouter **2 Parts invisibles** (`Transparency = 1`, Anchored) qui couvrent uniquement les piliers, et les grouper dans le Model.
  - `Dragon_Skeleton` et `Dragon_Skull` : `CanCollide = false`, sauf le crâne du squelette, qu'on peut garder solide avec `CollisionFidelity = Hull`.
  - Murets et poteaux : `CanCollide = true`, `CollisionFidelity = Box`.
  - Îles : `CanCollide = false` (elles sont hors de portée des joueurs).
- Lumières, avec modération :
  - un `PointLight` orange dans chaque `Flame` des portes (Range 10) ;
  - **un seul** `PointLight` cyan par île (Range 16, Brightness 2), dans le plus gros cristal.
- Définir le `PrimaryPart` de chaque modèle sur une partie du bas.

## B. Portes des repaires et arche de l'Egg Road
1. **Commence par chercher** dans **tous** les scripts les noms des portes, des panneaux et de l'arche actuels : `Free Lair`, les noms des Parts, `SurfaceGui`, `TextLabel`. Il est **très probable** que `LairService` (Aidan) écrive le nom du propriétaire sur le panneau « Free Lair ».
   - **Si un script modifie ces objets** : garde **exactement les mêmes noms et la même hiérarchie** pour ce que le script utilise (par exemple le `SurfaceGui` et son `TextLabel`), et place-les dans le `Sign` du nouveau modèle. S'il n'y a aucun moyen de garder la même structure, **arrête-toi** et écris une `DEMANDE à Aidan` dans le journal.
2. Remplace **une seule** porte « Free Lair » :
   - même position, même orientation (le panneau face au chemin) ;
   - mets le `SurfaceGui` existant sur le nouveau `Sign` ;
   - vérifie en jeu que le texte s'affiche toujours et change quand un joueur prend le repaire.
3. Montre une capture à Will. **Avec son accord seulement**, fais les 7 autres portes, puis l'arche de l'Egg Road (avec le texte « EGG ROAD » sur son panneau).
4. Rien ne doit gêner le passage : un joueur doit traverser sans accrocher. Teste en marchant.

## C. Murets des repaires
1. Repère les bandes grises qui délimitent les 8 repaires. Fais la liste des segments (début et fin) **avant** de les remplacer.
2. Le long de chaque segment, à la place des bandes :
   - mets des `Wall_Straight_8` bout à bout, et un `Wall_Straight_4` pour finir quand il manque de la place ;
   - mets un `Wall_Post` à chaque angle, à chaque extrémité et environ tous les 16 studs ;
   - remplace environ 15 % des modules par un `Wall_Broken_8`, jamais deux à la suite ;
   - fais varier légèrement chaque module : rotation de ±1° et petite variation de hauteur, sans laisser de trou ;
   - suis la hauteur du sol (raycast vers le bas).
3. **Laisse une ouverture** au niveau de chaque porte « Free Lair » et de chaque chemin : au moins la largeur du passage, plus 2 studs.
4. Range tout dans `Workspace > Map > Decor > Walls > Lair1…Lair8`.

## D. Forêt plus naturelle (avec les modèles de la série 1)
1. **Couleurs des feuillus** : dans les modèles de `MapProps` *et* dans toutes les copies déjà placées, fais varier la couleur du `Foliage` entre `#3F5A32`, `#4A6436` et `#35502C`, au hasard. Ils doivent rester sombres sans paraître noirs dans la brume.
2. **Anneau central** : supprime l'effet grille. Garde 2 ou 3 **petits groupes** (3 à 5 arbres serrés, de tailles variées), séparés par des clairières. Quelques `Pine_Burnt` près de l'autel. Garde une vue dégagée sur l'autel depuis la route.
3. **Extérieur** : fais des **bosquets** de 5 à 12 arbres, serrés au pied des montagnes et des gros rochers, et plus rares en allant vers le centre. Ajoute des fougères et des rochers moussus au pied des bosquets.
4. Laisse **toujours libre** :
   - un couloir de 6 studs le long de la route et des chemins ;
   - l'entrée de chaque repaire ;
   - l'intérieur des terrains des repaires (c'est là que `LairService` pose les bâtiments).
5. Pour chaque arbre : rotation Y au hasard, taille au hasard entre ×0,85 et ×1,2.

## E. Sol et traces de dragons
1. Regarde si le sol est du **Terrain** ou des **Parts**.
   - **Si c'est du Terrain** : peins des zones de `Ground` ou `Mud` le long des chemins et au pied des bosquets, des zones de `LeafyGrass` sous les arbres, et du `Rock` autour des gros rochers. Ajoute de **légères** bosses en dehors des chemins et des repaires.
   - **Si ce sont des Parts** : ajoute quelques plaques (Parts fines, matériau `Ground` ou `Mud`, de couleurs proches) à peine au-dessus du sol, aux mêmes endroits.
2. **Traces de brûlure** (`Decal_Scorch`, avec l'ID donné par Will) : mets le décalque sur la face du dessus de Parts invisibles et très fines (`Transparency = 1`, CanCollide/CanQuery/CanTouch à false). Fais varier la taille (8 à 20 studs) et la rotation. En placer environ 10 :
   - autour de l'autel ;
   - sous les `Pine_Burnt` ;
   - autour du squelette.

## F. Squelette, crânes et îles flottantes
1. **`Dragon_Skeleton`** (un seul exemplaire) :
   - dans un coin **bien visible depuis le point d'arrivée des joueurs**, par exemple entre deux repaires au pied des montagnes, **jamais** sur un chemin ni dans un terrain de repaire ;
   - enfonce-le d'environ 1,5 stud et tourne-le pour qu'on voie le crâne et les côtes de profil ;
   - autour : 2 ou 3 `Pine_Burnt`, 2 traces de brûlure, quelques rochers moussus. Il doit raconter « un dragon est tombé ici ».
   - Taille possible : ×1 à ×1,4 avec `Model:ScaleTo`.
2. **`Dragon_Skull`** : 2 ou 3 exemplaires à demi enfouis dans l'herbe ou contre un rocher, loin des chemins. **Pas** près de l'autel, pour garder la vue dégagée sur le dragon sauvage.
3. **Îles flottantes** :
   - vérifie d'abord qu'**aucun script** n'utilise les 3 îles actuelles (`WildService`, `EventService`…) ;
   - si aucun ne les utilise : remplace-les aux mêmes positions (2 `Island_Large` et 1 `Island_Small`, ou l'inverse), et ajoute 1 ou 2 petites îles en plus pour la profondeur ;
   - tu peux poser un `Pine_Small` sur une grande île ;
   - **Option (avec l'accord de Will)** : un LocalScript `MapAmbience` dans `StarterPlayer > StarterPlayerScripts` qui fait monter et descendre doucement les îles côté joueur (±1,5 stud, 6 à 9 s, `TweenService` en boucle, décalage différent par île). C'est un effet visuel uniquement, rien côté serveur.

## G. Lumière (à proposer, pas à imposer)
Fais une capture **avant**, puis propose à Will :
- `Atmosphere` : Density environ 0,35, Haze environ 1,5, Glare 0, couleur légèrement bleu-gris. Les montagnes doivent rester lisibles.
- `ColorCorrection` : Saturation −0,05, Contrast +0,08, TintColor légèrement chaud (255, 245, 235).
- `Bloom` léger (Intensity 0,4, Threshold 0,95) pour faire briller les cristaux et les flammes.

Applique seulement ce que Will valide, et montre une capture **après**, prise sous le même angle.

## H. Performance et test final
- Nombre de lumières dans toute la carte : **30 au maximum**. S'il y en a plus, retire celles des lanternes les plus éloignées.
- Pour les feuillages, crânes, îles et décalques : `CanQuery = false` et `CanTouch = false` (moins de calculs).
- Lance le jeu (`start_stop_play`) et lis la console (`get_console_output`) : **aucune erreur rouge**.
- Vérifie que tout marche encore :
  - un œuf passe sur la route et on peut l'acheter ;
  - un dragon sauvage apparaît à l'autel ;
  - les repaires sont bien attribués et leurs panneaux affichent le bon nom ;
  - on peut marcher partout où il faut passer.
- Simulateur d'appareil **téléphone** : la scène reste fluide et lisible.
- Fais une **capture vue de haut** sous le même angle que la capture de départ de Will, pour comparer.

## Journal (fin de session)
Retire la ligne `EN COURS` et ajoute en bas de `DevJournal`, avant `return {}` :
```lua
--[[ <date> · Will (Claude)
Fait : refonte carte série 2 — portes Free Lair + arche Egg Road (modèles Gate_*), murets des repaires (Wall_*),
forêt en bosquets + couleurs des feuillus, sol peint + traces de brûlure, squelette de dragon, crânes, îles flottantes.
Modèles : ServerStorage > MapProps. Ancien décor : ServerStorage > MapBackup_<date> (à supprimer après le test d'équipe).
Scripts : <aucun, ou MapAmbience (LocalScript, îles qui flottent)>.
Testé : <ce qui a été vérifié>.
Reste / DEMANDES : <…>
]]
```
