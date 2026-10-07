# Dragon Lineage : série 3 (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé les `.glb` de `meshes-serie3/`.

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est **le monde et la course** : la carte, la route, les dragons sauvages, les événements et l'ambiance. Le jeu est en **compétition** contre d'autres équipes : le rendu doit être soigné, sans rien casser.

Parle en **français**, simplement : Will débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) série 3 : flammes, crânes, piliers de l'autel`.
- Ne touche **qu'à la part de Will**.
- **Ne supprime rien** : l'ancien va dans `ServerStorage > MapBackup_<date>`.
- Fais d'abord **un seul exemplaire**, montre une capture à Will, attends son accord, puis fais le reste.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Ce qui change
Les séries 1 et 2 sont en place. Will a demandé trois corrections :
1. **La flamme des braseros et des portes** : on voyait clairement le cône (« le cylindre ») dans la flamme.
2. **La tête de dragon**, sur le squelette, les crânes, les portes et l'arche : elle manquait de détail et faisait bâclée.
3. **Les piliers du centre (l'autel)** : ce sont encore les piliers d'origine.

## Import (fait par Will)
**Avatar → Import 3D**, un `.glb` à la fois, avec l'unité **Stud** (compare la taille avec le tableau ; si c'est environ 3,5 fois trop grand ou trop petit, change l'unité), les parties séparées et **Anchored** coché. Range les modèles dans `ServerStorage > MapProps`.

| Nouveau modèle | Remplace | Parties | Taille (L × H × P, studs) |
|---|---|---|---|
| `Brazier_DragonClaw_v2` | `Brazier_DragonClaw` | Stone, Claws, **Flame**, **FlameCore**, Coals, Embers | 4 × 6 × 4 |
| `Dragon_Skull_v2` | `Dragon_Skull` | Bones, **Horns**, Sockets | 5,5 × 9 × 15,5 |
| `Dragon_Skeleton_v2` | `Dragon_Skeleton` | Bones, Horns, Sockets | 27 × 18 × 67 (à enfoncer d'environ 1,5 stud) |
| `Gate_Lair_v2` | `Gate_Lair` | Stone, Bones, Horns, Sockets, Sign, Flame, FlameCore | 21 × 19 × 15 |
| `Gate_EggRoad_v2` | `Gate_EggRoad` | Stone, StoneDark, Bones, Horns, Sockets, Sign, Iron | 27 × 29 × 13 |
| `Altar_Pillar_A` (grand), `Altar_Pillar_B` (moyen) | les piliers de l'autel | Stone, StoneDark, Claws, Runes, **Crystal** | 5,7 × 21 / 5,7 × 18 |

Les couleurs et matériaux de chaque partie sont dans `meshes-serie3/manifest.json`. Points importants :
- `Flame`, `FlameCore`, `Embers`, `Runes` et `Crystal` sont en **Neon**, avec `CastShadow = false`, `CanCollide = false` et `CanQuery = false`.
- `Bones` et `Horns` sont en `SmoothPlastic`. Sur les captures, l'os paraissait rosé : garde la couleur du manifeste (`#CFC8B4`, ivoire) et les cornes plus sombres (`#5E5548`).

## A. Remplacer les modèles v1 par les v2 (au même endroit)
Pour **chaque** exemplaire placé de `Brazier_DragonClaw`, `Dragon_Skull`, `Dragon_Skeleton`, `Gate_Lair` et `Gate_EggRoad` :
1. Clone le modèle v2 depuis `MapProps`.
2. Donne-lui **la même position et la même taille** que l'ancien : `nouveau:PivotTo(ancien:GetPivot())` et `nouveau:ScaleTo(ancien:GetScale())`. Vérifie à l'œil qu'il est bien posé : le pivot des deux versions est à la base, mais les tailles diffèrent un peu.
3. **Transfère tout ce qui a été ajouté** sur l'ancien modèle dans le nouveau :
   - les `PointLight` (dans la `Flame` du brasero ou des portes) ;
   - le `SurfaceGui` du panneau (`Sign`), **avec exactement les mêmes noms**, parce que `LairService` écrit le nom du propriétaire dessus ;
   - les Parts de collision invisibles ;
   - les attributs, les tags (`CollectionService`) et le nom de l'instance.
4. Déplace l'ancien dans `ServerStorage > MapBackup_<date>`.
5. Pour les **portes** : vérifie en jeu que le panneau affiche toujours « Free Lair » puis le nom du joueur quand il prend le repaire.

**Flamme :** s'il reste un ancien effet `Fire` dans les braseros ou les portes, **retire-le** : c'est lui qui donnait l'effet « cylindre ». Ajoute plutôt, dans la partie `Flame`, un petit `ParticleEmitter` d'étincelles :
- Rate 6, Lifetime 0,8 à 1,4, Speed 3 à 5, SpreadAngle (20, 20) ;
- Size de 0,25 à 0 ;
- couleur orange vers jaune ;
- LightEmission 1.

Ajoute aussi, en option, une fumée très légère (Transparency 0,85 vers 1). C'est léger pour le téléphone.

## B. Piliers de l'autel
1. **Avant tout**, cherche dans **tous** les scripts ce qui utilise l'autel, ses piliers et ses cristaux : noms des Parts, `Altar`, `Pillar`, `Crystal`, tags. `WildService` (la part de Will) les utilise très probablement pour faire apparaître le dragon sauvage, faire briller ou tourner les cristaux, etc. Note précisément ce que chaque script utilise.
2. Remplace **un seul** pilier :
   - même position, rotation Y au hasard ;
   - alterne `Altar_Pillar_A` (grand) et `Altar_Pillar_B` (moyen) ;
   - ajuste la taille avec `ScaleTo` pour que le cristal soit à peu près à la hauteur de l'ancien.
3. **Si un script utilise les anciens piliers ou cristaux**, garde **les mêmes noms et la même hiérarchie** pour ce que le script vise. Par exemple, si le script fait tourner une Part `Crystal`, la nouvelle partie `Crystal` doit avoir le même nom et se trouver au même endroit dans l'arborescence. Si ce n'est pas possible proprement, **arrête-toi** et explique à Will. Comme c'est son propre script (`WildService`), il peut décider de l'adapter.
4. Lance le jeu : le dragon sauvage doit toujours apparaître au centre, et le mini-jeu de capture doit marcher. Montre une capture à Will, puis fais les autres piliers.
5. *Option, avec l'accord de Will* : dans un LocalScript `MapAmbience` (`StarterPlayerScripts`), fais tourner lentement le `Crystal` de chaque pilier (un tour en 12 s) et monter et descendre de ±0,4 stud, **côté joueur uniquement**. Si un script existant anime déjà les cristaux, ne fais rien.
6. Un `PointLight` cyan pour 2 piliers seulement (Range 14), pour rester sous la limite de lumières.

## C. Lumière (à proposer à Will)
Sur la dernière vue de haut, la **brume est trop épaisse** : tout devient gris-vert, on ne lit plus bien les repaires et les montagnes. Propose :
- `Atmosphere.Density` : baisser d'environ un tiers (par exemple 0,35 vers 0,25), et `Haze` vers 0,8 ;
- garder un léger `Bloom` pour les flammes et les cristaux.

Montre une capture **avant** et une capture **après**, prises sous le même angle, et n'applique que si Will valide.

## D. Tests et journal
- Lance le jeu et lis la console : **aucune erreur rouge**.
- Vérifie que tout marche encore :
  - la route et l'achat d'un œuf ;
  - le dragon sauvage et la capture ;
  - les panneaux des repaires ;
  - on peut passer sous les portes et l'arche.
- Simulateur **téléphone** : fluide. Au total, 30 lumières au maximum sur la carte.
- Retire la ligne `EN COURS` et ajoute en bas de `DevJournal`, avant `return {}` :
```lua
--[[ <date> · Will (Claude)
Fait : série 3 — braseros/portes avec flamme low-poly (v2), crânes de dragon détaillés (crâne, squelette, portes, arche v2), nouveaux piliers de l'autel (Altar_Pillar_A/B).
Anciens modèles : ServerStorage > MapBackup_<date>.
Scripts : <aucun / MapAmbience (cristaux qui tournent)>. Noms gardés pour WildService : <…>.
Testé : <…>
Reste : <…>
]]
```
