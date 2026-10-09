# Dragon Lineage : série 5, le dragon de cristal v5 qui VOLE (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé `objets/Dragon_Cristal_v5.glb` du zip `dragon-lineage-serie5.zip` (voir « Import » plus bas).
>
> Version précédente (v2, décor immobile, 68 parties) : remplacée. Si un ancien `Dragon_Cristal` est déjà sur la carte, **ne le supprime pas** : demande à Will ce qu'il veut en faire.

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est le monde et la course. Parle en **français**, simplement : Will débute.

**Règles d'équipe** :
- Lis `ServerStorage > DevJournal` et écris en haut : `EN COURS : Will (Claude) série 5 : dragon de cristal v5 (vol)`.
- Ne touche **qu'à la part de Will**. **Ne supprime rien.**
- Montre une capture à Will avant de placer le dragon sur la carte.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Le modèle
Un long dragon oriental de cristal bleu qui **vole** :
- crinière fluide sur la nuque ;
- gueule ouverte sombre avec des crocs blanc glacé ;
- yeux or à fente noire ;
- longues moustaches ;
- quatre pattes en serres.

Taille : environ **42 × 33 × 116 studs** (L × H × P), tête vers l'avant (-Z), 28 388 triangles.

Il est découpé en **117 parties** : un script les fait bouger pour l'animation de vol. **Ne renomme pas, ne fusionne pas (pas d'Union) et ne regroupe pas les parties** : le script les retrouve par leur nom exact.

## Import (fait par Will)
**Avatar → Import 3D**, fichier `objets/Dragon_Cristal_v5.glb`, unité **Stud**. Si le modèle est environ 3,5 fois trop grand ou trop petit, change l'unité : le script s'adapte à l'échelle tout seul. Garde les parties séparées et coche **Anchored**.

Après l'import, vérifie que les noms des parties sont exactement ceux de `objets/manifest.json` (`Head`, `Seg01`…`Seg38`, `Seg10_LegFL`, etc.). Si l'importeur a ajouté un préfixe ou un suffixe, renomme les parties pour retrouver les noms exacts.

## A. Réglages des parties (toi, par MCP)
Sur **toutes** les MeshParts : `Anchored = true`, `CanCollide = false`, `CanTouch = false`, `CanQuery = false`, `CastShadow = false` (sauf indication contraire ci-dessous).

Couleurs et matériaux (ils sont aussi dans `objets/manifest.json`, partie par partie) :

| Parties | Color | Material | Transparency |
|---|---|---|---|
| `Head`, `Seg01`…`Seg38`, `SegXX_LegYY`, `SegXX_LegYY_Shin`, `SegXX_LegYY_Foot` (corps) | `#24569F` | Glass | 0.25 |
| toutes les `…_Blades`, `Head_Jaw`, `Head_WhiskerL1..3`, `Head_WhiskerR1..3` (lames, mâchoire, moustaches) | `#4E8FE6` | Glass | 0.25 |
| `Head_Eyes` (iris or) | `#FFB22E` | Neon | 0 |
| `Head_Pupils_L`, `Head_Pupils_R` (pupilles) | `#120600` | Neon | 0 |
| `Head_Gem` (gemme du front) | `#7FD8FF` | Neon | 0 |
| `Head_Brows` (sourcils, orbites) | `#102A5C` | SmoothPlastic | 0 |
| `Head_Lids`, `Head_LidsHalf` (paupières : **cachées**, le script les montre quand il cligne) | `#102A5C` | SmoothPlastic | **1** |
| `Head_Teeth`, `Head_Jaw_Teeth` (crocs) | `#E6F4FF` | Ice | 0 |
| `Head_Mouth`, `Head_Jaw_Mouth` (intérieur de la gueule) | `#070B1C` | SmoothPlastic | 0 |
| `Head_Jaw_Tongue` (langue) | `#18224C` | SmoothPlastic | 0 |

Sur le **modèle** :
- `ModelStreamingMode = Atomic` (il arrive en entier chez le joueur, pas morceau par morceau) ;
- ajoute le tag **`DragonCristal`** (propriété Tags, ou `CollectionService:AddTag`) : c'est comme ça que le script le trouve ;
- ajoute un **`Highlight`** pour les contours lumineux : `FillTransparency = 1`, `OutlineColor = #9CC8FF`, `OutlineTransparency = 0.2`, `DepthMode = Occlusion`.

## B. Scripts de l'animation de vol (toi, par MCP)
Les deux fichiers sont dans le dossier `scripts/` du zip. Copie leur contenu **sans rien changer** :
1. `scripts/DragonCristalRig.lua` → un **ModuleScript** nommé `DragonCristalRig` dans **ReplicatedStorage**. Il contient les points de pivot du dragon et a été généré automatiquement, donc **on ne le modifie pas à la main**.
2. `scripts/DragonCristalVol.client.lua` → un **LocalScript** nommé `DragonCristalVol` dans **StarterPlayer > StarterPlayerScripts**.

Ce que fait le script : chaque joueur voit le dragon voler **sur place**, en boucle de 1,32 s :
- le corps ondule de haut en bas ;
- la tête reste posée ;
- les pattes pagaient dans le vide ;
- la gueule s'ouvre un peu ;
- les moustaches ondulent ;
- il cligne des yeux et regarde autour de lui.

C'est fait **côté client** : toutes les parties bougent en une seule fois avec `workspace:BulkMoveTo`, seulement quand la caméra est à moins de 600 studs. Le serveur ne fait rien, et ça reste léger pour le mobile. Si plusieurs dragons ont le tag, chacun a son propre rythme.

Le script recale l'animation sur la partie `Head` et vérifie avec `Seg20`. S'il affiche dans la sortie `le recalage ne colle pas`, c'est que des parties ont été déplacées ou renommées après l'import : remets-les comme à l'import.

## C. Placement
Range une copie de référence dans `ServerStorage > MapProps`, puis pose **un exemplaire** dans le Workspace, à un endroit visible (par exemple au-dessus du repaire). Mets-le **en l'air**, à environ 20 studs au-dessus du sol : il vole, rien ne doit toucher le sol, et son ombre doit être loin sous les griffes. Tu peux le tourner comme tu veux (tourne le modèle entier, pas les parties une par une).

Lance le jeu (**Play**) pour vérifier qu'il vole. Fais une capture, montre-la à Will, et attends son accord.

## D. Fin
Vérifie la console (aucune erreur rouge) et écris dans le DevJournal : `Will (Claude) série 5 : dragon de cristal v5 importé, placé, animation de vol côté client (DragonCristalVol + DragonCristalRig)`.
