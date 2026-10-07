# Dragon Lineage : série 4 (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé les `.glb` du dossier `objets/` du zip `dragon-lineage-serie4.zip`.

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est **le monde et la course** : la carte, la route, les dragons sauvages, les événements et l'ambiance. Le jeu est en **compétition** contre d'autres équipes : le rendu doit être soigné, sans rien casser.

Parle en **français**, simplement : Will débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) série 4 : crâne de dragon v3 (+ braseros et totems si besoin)`.
- Ne touche **qu'à la part de Will**.
- **Ne supprime rien** : l'ancien va dans `ServerStorage > MapBackup_<date>`.
- Fais d'abord **un seul exemplaire**, montre une capture à Will, attends son accord, puis fais le reste.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Ce qui change
Will a refait **la tête de dragon** une dernière fois. De face, celle de la série 3 (v2) ressemblait à un scarabée. Le nouveau crâne **v3** a :
- un museau plus court et plus haut ;
- des arcades au-dessus des yeux ;
- des cornes épaisses qui s'enroulent vers l'avant ;
- des **orbites en amande avec une pupille fendue orange qui brille** (partie `Eyes`, en Neon).

Le crâne v3 remplace l'ancien **partout** : le crâne seul, le squelette, les portes des repaires et l'arche de la route des œufs.

Ce prompt contient aussi ce qui venait de la série 3, au cas où elle n'aurait pas encore été appliquée dans Studio :
- **la flamme low-poly** des braseros et des portes (l'ancienne flamme montrait un « cylindre ») ;
- **les totems de l'autel** (`Altar_Pillar_A` et `Altar_Pillar_B`).

La porte `Gate_Lair_v3` a déjà la nouvelle flamme.

## Import (fait par Will)
**Avatar → Import 3D**, un `.glb` à la fois, avec l'unité **Stud** (compare la taille avec le tableau ; si c'est environ 3,5 fois trop grand ou trop petit, change l'unité), les parties séparées et **Anchored** coché. Range les modèles dans `ServerStorage > MapProps`.

| Nouveau modèle | Remplace | Parties | Taille (L × H × P, studs) |
|---|---|---|---|
| `Dragon_Skull_v3` | `Dragon_Skull_v2` (ou `Dragon_Skull`) | Bones, Horns, Sockets, **Eyes** | 12 × 10 × 10,6 |
| `Dragon_Skeleton_v3` | `Dragon_Skeleton_v2` (ou `Dragon_Skeleton`) | Bones, Horns, Sockets, **Eyes** | 27 × 18 × 65 (à enfoncer d'environ 1,5 stud) |
| `Gate_Lair_v3` | `Gate_Lair_v2` (ou `Gate_Lair`) | Stone, Bones, Horns, Sockets, **Eyes**, Sign, Flame, FlameCore | 21 × 20 × 8,4 |
| `Gate_EggRoad_v3` | `Gate_EggRoad_v2` (ou `Gate_EggRoad`) | Stone, StoneDark, Bones, Horns, Sockets, **Eyes**, Sign, Iron | 27 × 32 × 9 |
| `Brazier_DragonClaw_v2` | `Brazier_DragonClaw` (si pas déjà fait) | Stone, Claws, **Flame**, **FlameCore**, Coals, Embers | 4 × 6 × 4 |
| `Altar_Pillar_A` (grand), `Altar_Pillar_B` (moyen) | les piliers de l'autel (si pas déjà fait) | Stone, StoneDark, Claws, Runes, **Crystal** | 5,7 × 21 / 5,7 × 18 |

Les couleurs et matériaux de chaque partie sont dans `objets/manifest.json`. Points importants :
- `Eyes`, `Flame`, `FlameCore`, `Embers`, `Runes` et `Crystal` sont en **Neon**, avec `CastShadow = false`, `CanCollide = false` et `CanQuery = false`. Couleur des yeux : `#FF5418` (orange braise).
- `Bones` est ivoire (`#CFC8B4`), `Horns` plus sombre (`#5E5548`), `Sockets` presque noir (`#0E0E10`).
- **Le crâne seul n'a plus les mêmes proportions** : il est moins long (10,6 au lieu de 15,5 studs) mais beaucoup plus large à cause des cornes (12 au lieu de 5,5). Vérifie qu'aucune corne ne rentre dans un mur, un arbre ou la route ; sinon tourne-le un peu ou réduis-le légèrement.
- Les portes sont moins profondes qu'avant (le long crâne v2 dépassait derrière). Les Parts de collision invisibles restent valables.

## 0. Où en est la carte ?
Avant tout, regarde ce qui est placé sur la carte et dis-le à Will :
- les braseros sont-ils déjà des `Brazier_DragonClaw_v2` ?
- les piliers de l'autel sont-ils déjà des `Altar_Pillar_A` / `Altar_Pillar_B` ?
- les crânes, le squelette et les portes sont-ils en v1 ou en v2 ?

Si les braseros et les piliers sont déjà en v2, **saute les parties B et C**.

## A. Remplacer les crânes, le squelette et les portes par les v3 (au même endroit)
Commence par lister ce qui est placé sur la carte : selon ce que Will a déjà fait, ce sont des versions v2 (série 3) ou encore v1 (série 2). Remplace la version présente, quelle qu'elle soit.

Pour **chaque** exemplaire placé de crâne, squelette, porte de repaire et arche de la route des œufs :
1. Clone le modèle v3 depuis `MapProps`.
2. Donne-lui **la même position et la même taille** que l'ancien : `nouveau:PivotTo(ancien:GetPivot())` et `nouveau:ScaleTo(ancien:GetScale())`. Le pivot est à la base dans toutes les versions ; vérifie à l'œil qu'il est bien posé.
3. **Transfère tout ce qui a été ajouté** sur l'ancien modèle dans le nouveau :
   - les `PointLight` et les `ParticleEmitter` d'étincelles (dans la `Flame` des portes) ;
   - le `SurfaceGui` du panneau (`Sign`), **avec exactement les mêmes noms**, parce que `LairService` écrit le nom du propriétaire dessus ;
   - les Parts de collision invisibles ;
   - les attributs, les tags (`CollectionService`) et le nom de l'instance.
4. Déplace l'ancien dans `ServerStorage > MapBackup_<date>`.

**Ordre conseillé** : une **porte de repaire** d'abord (c'est la plus délicate à cause du panneau), capture pour Will, puis son accord, puis le reste.

**Option, avec l'accord de Will** : un tout petit `PointLight` orange (Range 6, Brightness 0,6) dans la partie `Eyes` du **squelette** et du **crâne seul** uniquement, pour que le regard brille la nuit. Pas sur les portes, qui ont déjà la lumière des flammes. Respecte la limite de 30 lumières sur la carte.

## B. Braseros (seulement si la série 3 n'est pas en place)
Pour chaque `Brazier_DragonClaw` placé, fais la même chose qu'en A (même position, même taille, transfert des lumières, des tags et des attributs, ancien dans `MapBackup_<date>`). Un seul d'abord, avec une capture pour Will.

**Flamme :** s'il reste un ancien effet `Fire` dans les braseros ou les portes, **retire-le** : c'est lui qui donnait l'effet « cylindre ». Ajoute plutôt, dans la partie `Flame`, un petit `ParticleEmitter` d'étincelles :
- Rate 6, Lifetime 0,8 à 1,4, Speed 3 à 5, SpreadAngle (20, 20) ;
- Size de 0,25 à 0 ;
- couleur orange vers jaune ;
- LightEmission 1.

## C. Totems de l'autel (seulement si la série 3 n'est pas en place)
1. **Avant tout**, cherche dans **tous** les scripts ce qui utilise l'autel, ses piliers et ses cristaux : noms des Parts, `Altar`, `Pillar`, `Crystal`, tags. `WildService` (la part de Will) les utilise très probablement pour faire apparaître le dragon sauvage, faire briller ou tourner les cristaux, etc. Note précisément ce que chaque script utilise.
2. Remplace **un seul** pilier :
   - même position, rotation Y au hasard ;
   - alterne `Altar_Pillar_A` (grand) et `Altar_Pillar_B` (moyen) ;
   - ajuste la taille avec `ScaleTo` pour que le cristal soit à peu près à la hauteur de l'ancien.
3. **Si un script utilise les anciens piliers ou cristaux**, garde **les mêmes noms et la même hiérarchie** pour ce que le script vise. Si ce n'est pas possible proprement, **arrête-toi** et explique à Will.
4. Lance le jeu : le dragon sauvage doit toujours apparaître au centre, et le mini-jeu de capture doit marcher. Montre une capture à Will, puis fais les autres piliers.
5. Un `PointLight` cyan pour 2 piliers seulement (Range 14), pour rester sous la limite de lumières.

## D. Tests et journal
- Lance le jeu et lis la console : **aucune erreur rouge**.
- Vérifie que tout marche encore :
  - les panneaux des repaires : « Free Lair », puis le nom du joueur quand il prend le repaire ;
  - on peut passer sous les portes et sous l'arche ;
  - la route et l'achat d'un œuf ;
  - si les totems ont été changés : le dragon sauvage apparaît et la capture marche.
- Simulateur **téléphone** : fluide.
- Retire la ligne `EN COURS` et ajoute en bas de `DevJournal`, avant `return {}` :
```lua
--[[ <date> · Will (Claude)
Fait : série 4 — crâne de dragon v3 (yeux braise) sur le crâne seul, le squelette, les portes des repaires et l'arche de la route des œufs. <+ braseros flamme v2 et totems de l'autel, si pas déjà faits>.
Anciens modèles : ServerStorage > MapBackup_<date>.
Lumières ajoutées : <aucune / yeux du squelette et du crâne>.
Testé : <…>
Reste : <…>
]]
```
