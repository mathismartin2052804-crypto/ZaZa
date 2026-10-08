# Dragon Lineage : série 5, le dragon de cristal (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé `objets/Dragon_Cristal.glb` du zip `dragon-lineage-serie5.zip`.

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est le monde et la course. Parle en **français**, simplement : Will débute.

**Règles d'équipe** :
- Lis `ServerStorage > DevJournal` et écris en haut : `EN COURS : Will (Claude) série 5 : dragon de cristal`.
- Ne touche **qu'à la part de Will**. **Ne supprime rien.**
- Montre une capture à Will avant de le placer sur la carte.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Le modèle
Un long dragon oriental bleu, transparent comme de la glace, couvert de lames de cristal (crinière aux épaules, touffe au bout de la queue). Taille : environ **10,5 × 24 × 67 studs** (L × H × P), tête vers l'avant (-Z). **Pas d'animation pour l'instant** : on le pose comme décor.

Il est découpé en **68 parties** pour qu'on puisse l'animer plus tard. **Ne renomme pas et ne fusionne pas les parties** (pas d'Union) :
- `Head`, `Seg01` … `Seg30` : la tête et le corps, couleur `#2C63B8` ;
- `Head_Blades`, `SegXX_Blades` et `Head_Jaw` (mâchoire) : les lames, couleur `#6FA8F0` ;
- `Head_Eyes` : les yeux, couleur `#C8ECFF`, en **Neon** ;
- `Seg06_LegFL/FR` (pattes avant) et `Seg21_LegBL/BR` (pattes arrière), couleur `#2C63B8`.

## Import (fait par Will)
**Avatar → Import 3D**, unité **Stud** (si c'est environ 3,5 fois trop grand ou petit, change l'unité), parties séparées, **Anchored** coché. Range le modèle dans `ServerStorage > MapProps`.

## A. Réglages du modèle (toi, par MCP)
Sur toutes les MeshParts du modèle :
- `Anchored = true`, `CanCollide = false`, `CanTouch = false`, `CanQuery = false` ;
- corps et lames : `Material = Glass`, `Transparency = 0.25`, `CastShadow = false` ;
- yeux : `Material = Neon`, `Transparency = 0`.
Ajoute dans le modèle un **`Highlight`** pour les contours lumineux (l'effet « hologramme » de l'image) :
`FillTransparency = 1`, `OutlineColor = #9CC8FF`, `OutlineTransparency = 0.2`, `DepthMode = Occlusion`.
Mets `ModelStreamingMode = Atomic` sur le modèle (il apparaît en entier, pas morceau par morceau).

## B. Placement
Pose **un exemplaire** dans un endroit visible de la carte (par exemple au-dessus du repaire), avec les pattes arrière posées au sol ou sur un rocher. Fais une capture, montre-la à Will, et attends son accord.

## C. Fin
Vérifie la console (aucune erreur rouge) et écris dans le DevJournal : `Will (Claude) série 5 : dragon de cristal importé et placé (décor, sans animation)`.
