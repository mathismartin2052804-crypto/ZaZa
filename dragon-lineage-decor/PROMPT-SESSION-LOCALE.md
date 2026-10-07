# Intégration du nouveau décor « terre de dragons » : instructions pour l'IA locale

> **Will : copie tout ce fichier dans ta session Claude locale** (celle qui est connectée à Roblox Studio par MCP), avec le dossier `meshes/` à côté.

---

Tu aides **Will** sur le jeu Roblox **Dragon Lineage**. Sa part est **le monde et la course** (`Workspace > Map`, etc.). Les règles de l'équipe (`GUIDE-IA.md`, `REPARTITION.md`) s'appliquent. Les plus importantes ici :
- Le jeu dans Studio (Team Create) est la seule référence. Ne régénère jamais la carte à partir de fichiers.
- Lis `ServerStorage > DevJournal` avant de commencer. Ajoute en haut : `EN COURS : Will remplace le décor de la carte (arbres, buissons, braseros, lanternes)`.
- Ne touche qu'à `Workspace > Map` et aux nouveaux dossiers décrits ci-dessous. Rien dans les scripts des autres.
- Explique simplement et en français. Will débute.

## Ce qu'on intègre
Le dossier `meshes/` contient 14 modèles low-poly à facettes, de style sombre « terre de dragons ». Chacun est un `.glb` découpé en parties, une par couleur. `meshes/manifest.json` donne pour chaque partie la couleur et le matériau à appliquer.

| Modèle | Rôle | Hauteur (studs) |
|---|---|---|
| `Pine_Small`, `Pine_Medium`, `Pine_Tall`, `Pine_Leaning` | Sapins à étages (environ 60 % des arbres) | 16 / 24 / 33 / 24 |
| `Pine_Burnt` | Sapin calciné par un dragon, avec des braises (quelques-uns près du centre) | 20 |
| `Tree_Leafy_A`, `Tree_Leafy_B` | Feuillus au feuillage en un seul bloc (environ 40 % des arbres) | 18 / 15 |
| `Tree_Landmark_Nest` | Vieil arbre mort avec un nid de dragon, 3 ou 4 sur toute la carte pour se repérer | 35 |
| `Fern`, `Bush_Spiky`, `Rock_Mossy` | Remplacent les buissons en boules | 3 à 4 |
| `Brazier_DragonClaw` | Brasero sur serres de dragon, avec une flamme low-poly | 5 |
| `Lantern_Road` | Lanterne à cristal, remplace les poteaux à cube jaune de l'Egg Road | 9 |
| `Pillar_Runic` | Pilier à runes avec un cristal, *optionnel*, pour l'autel | 17 |

Le pivot de chaque modèle est à la base (Y = 0), au pied de l'objet : il se pose donc directement sur le sol.

## Étape 1 : import (fait par Will à la main, c'est le plus fiable)
1. Dans Studio : **Avatar → Import 3D** (ou **Fichier → Import 3D**), puis choisir un `.glb`.
2. Réglages de l'importeur :
   - **Unité / échelle** : *Stud*. Vérifie la taille obtenue avec le tableau : si l'objet est environ 3,5 fois trop grand ou trop petit, change l'unité (le format .glb est prévu en mètres) ;
   - garder les parties **séparées** (ne pas fusionner), pour obtenir un Model avec une MeshPart par partie (`Trunk`, `Foliage`…) ;
   - cocher **Anchored**.
3. Répéter pour les 14 fichiers, puis ranger les modèles dans un nouveau dossier **`ServerStorage > MapProps`**. Ce sont les modèles de référence, qui ne s'affichent pas en jeu.

Toi (l'IA), tu vérifies ensuite par MCP que `ServerStorage > MapProps` contient bien les 14 modèles, avec les bonnes parties et à peu près la bonne hauteur.

## Étape 2 : réglages des modèles (par script MCP, dans `MapProps`)
Pour chaque MeshPart, d'après `manifest.json` :
- `Color` et `Material` : ceux du manifeste. Les parties `Flame`, `Crystal`, `Runes` et `Embers` sont en **Neon**.
- `Anchored = true`, `CanTouch = false`, `CastShadow = true` (sauf les parties Neon : `false`).
- **Collisions** :
  - troncs, pierre, poteaux, rochers : `CanCollide = true`, `CollisionFidelity = Hull` ;
  - feuillages, fougères, buissons, flammes, cristaux, runes, nid : `CanCollide = false`, `CanQuery = false`, `CollisionFidelity = Box`.
- Lumières, à ajouter avec modération pour le mobile :
  - un `PointLight` dans le `Crystal` de chaque lanterne (Range 12, Brightness 1.5, couleur cyan `#6FE3FF`) ;
  - un `PointLight` orange dans la `Flame` des braseros.
- Définir le `PrimaryPart` de chaque modèle sur la partie du bas (tronc, pierre ou poteau).

## Étape 3 : remplacer l'ancien décor, **une zone test d'abord**
1. **Repérer l'ancien décor** dans `Workspace > Map` :
   - arbres : un cylindre marron + des sphères vertes (`Shape = Ball`) ;
   - buissons : des sphères vertes seules ;
   - braseros : un cylindre sombre + une boule jaune ;
   - lanternes : un poteau + un cube jaune.

   Liste ce que tu trouves (combien, où) **avant** de toucher à quoi que ce soit.
2. **Vérifier qu'aucun script n'utilise ces objets.** Cherche leurs noms dans tous les scripts. Le plus probable, ce sont les piliers et braseros de l'autel, que `WildService` peut viser. Si un script les utilise, **ne pas les remplacer** et prévenir Will.
3. **Sauvegarde** : déplace l'ancien décor dans `ServerStorage > MapBackup_<date>` au lieu de le supprimer. On ne le supprime qu'après le test d'équipe.
4. **Zone test** : remplace d'abord une petite zone, par exemple une vingtaine d'arbres autour d'un seul repaire.
   - Chaque nouvel objet prend **la position de l'ancien**, une **rotation Y aléatoire** et une **taille variée** (`Model:ScaleTo` entre 0,85 et 1,15), adaptée pour garder à peu près la hauteur de l'ancien objet.
   - Mélange des arbres : environ 60 % de sapins (avec 1 sur 4 penché) et 40 % de feuillus. Quelques `Pine_Burnt` seulement, plutôt vers le centre.
   - Buissons : environ 50 % `Fern`, 30 % `Bush_Spiky`, 20 % `Rock_Mossy`.
   - Braseros : place le nouveau modèle au même endroit. S'il y avait un effet de feu (`Fire`/`ParticleEmitter`) sur l'ancienne boule jaune, **déplace-le dans la nouvelle `Flame`**.
   - Lanternes : même position que l'ancien poteau, avec le bras tourné vers la route.
   - Range les nouveaux objets dans `Workspace > Map > Decor` (sous-dossiers `Trees`, `Bushes`, `Braziers`, `Lanterns`).
5. **Montre le résultat à Will** (capture d'écran via MCP) et **attends son accord** avant de faire toute la carte.
6. Avec son accord : remplace le reste. Place ensuite les 3 ou 4 `Tree_Landmark_Nest` à des endroits bien visibles, **sans gêner la route ni les repaires**.
7. `Pillar_Runic` : seulement si Will le demande, et seulement si l'étape 2 a confirmé qu'aucun script n'utilise les piliers actuels.

## Étape 4 : tester
- Lancer le jeu (`start_stop_play`), lire la console (`get_console_output`) : **aucune erreur rouge**.
- Vérifier que la route, les œufs, le dragon sauvage et les repaires marchent toujours.
- Vérifier la fluidité dans le simulateur d'appareil **téléphone**. S'il y a trop de lumières, retirer les `PointLight` des lanternes les plus éloignées.
- Proposer à Will (sans l'appliquer d'office) une ambiance plus sombre dans `Lighting` :
  - `Atmosphere` un peu plus dense, légèrement brumeuse ;
  - `ColorCorrection` avec une saturation légèrement plus basse et un contraste légèrement plus haut.

## Étape 5 : journal
Retire la ligne « EN COURS » et ajoute une entrée en bas de `DevJournal`, avant `return {}` :
```lua
--[[ <date> · Will (Claude)
Fait : nouveau décor low-poly « terre de dragons » (14 modèles dans ServerStorage > MapProps), arbres/buissons/braseros/lanternes remplacés dans Workspace > Map > Decor.
Ancien décor sauvegardé dans ServerStorage > MapBackup_<date> (à supprimer après le test d'équipe).
Scripts : aucun.
Testé : …
Reste : …
]]
```
