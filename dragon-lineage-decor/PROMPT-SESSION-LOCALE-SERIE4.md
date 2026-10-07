# Dragon Lineage : série 4 (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé les `.glb` de `meshes-serie4/` (pas ceux du dossier `brouillons/`).

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est **le monde et la course** : la carte, la route, les dragons sauvages, les événements et l'ambiance. Le jeu est en **compétition** contre d'autres équipes : le rendu doit être soigné, sans rien casser.

Parle en **français**, simplement : Will débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) série 4 : crâne de dragon v3`.
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

Le crâne v3 remplace l'ancien **partout** : le crâne seul, le squelette, les portes des repaires et l'arche de la route des œufs. Le reste de la série 3 (braseros, piliers de l'autel) ne change pas.

## Import (fait par Will)
**Avatar → Import 3D**, un `.glb` à la fois, avec l'unité **Stud** (compare la taille avec le tableau ; si c'est environ 3,5 fois trop grand ou trop petit, change l'unité), les parties séparées et **Anchored** coché. Range les modèles dans `ServerStorage > MapProps`.

| Nouveau modèle | Remplace | Parties | Taille (L × H × P, studs) |
|---|---|---|---|
| `Dragon_Skull_v3` | `Dragon_Skull_v2` (ou `Dragon_Skull`) | Bones, Horns, Sockets, **Eyes** | 12 × 10 × 10,6 |
| `Dragon_Skeleton_v3` | `Dragon_Skeleton_v2` (ou `Dragon_Skeleton`) | Bones, Horns, Sockets, **Eyes** | 27 × 18 × 65 (à enfoncer d'environ 1,5 stud) |
| `Gate_Lair_v3` | `Gate_Lair_v2` (ou `Gate_Lair`) | Stone, Bones, Horns, Sockets, **Eyes**, Sign, Flame, FlameCore | 21 × 20 × 8,4 |
| `Gate_EggRoad_v3` | `Gate_EggRoad_v2` (ou `Gate_EggRoad`) | Stone, StoneDark, Bones, Horns, Sockets, **Eyes**, Sign, Iron | 27 × 32 × 9 |

Les couleurs et matériaux de chaque partie sont dans `meshes-serie4/manifest.json`. Points importants :
- `Eyes`, `Flame` et `FlameCore` sont en **Neon**, avec `CastShadow = false`, `CanCollide = false` et `CanQuery = false`. Couleur des yeux : `#FF5418` (orange braise).
- `Bones` est ivoire (`#CFC8B4`), `Horns` plus sombre (`#5E5548`), `Sockets` presque noir (`#0E0E10`).
- **Le crâne seul n'a plus les mêmes proportions** : il est moins long (10,6 au lieu de 15,5 studs) mais beaucoup plus large à cause des cornes (12 au lieu de 5,5). Vérifie qu'aucune corne ne rentre dans un mur, un arbre ou la route ; sinon tourne-le un peu ou réduis-le légèrement.
- Les portes sont moins profondes qu'avant (le long crâne v2 dépassait derrière). Les Parts de collision invisibles restent valables.

## A. Remplacer les anciens modèles par les v3 (au même endroit)
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

## B. Tests et journal
- Lance le jeu et lis la console : **aucune erreur rouge**.
- Vérifie que tout marche encore :
  - les panneaux des repaires : « Free Lair », puis le nom du joueur quand il prend le repaire ;
  - on peut passer sous les portes et sous l'arche ;
  - la route et l'achat d'un œuf.
- Simulateur **téléphone** : fluide.
- Retire la ligne `EN COURS` et ajoute en bas de `DevJournal`, avant `return {}` :
```lua
--[[ <date> · Will (Claude)
Fait : série 4 — crâne de dragon v3 (yeux braise) sur le crâne seul, le squelette, les portes des repaires et l'arche de la route des œufs.
Anciens modèles : ServerStorage > MapBackup_<date>.
Lumières ajoutées : <aucune / yeux du squelette et du crâne>.
Testé : <…>
Reste : <…>
]]
```
