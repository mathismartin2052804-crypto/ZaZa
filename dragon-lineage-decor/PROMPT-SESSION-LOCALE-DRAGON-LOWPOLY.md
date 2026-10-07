# Dragon Lineage : dragon sauvage low-poly v1 (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé `objets/Dragon_LowPoly.glb` du zip `dragon-lowpoly-v1.zip`.

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est **le monde et la course**, dont **les dragons sauvages**. Le jeu est en **compétition** : le rendu doit être soigné, sans rien casser.

Parle en **français**, simplement : Will débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) dragon sauvage low-poly v1`.
- Ne touche **qu'à la part de Will**.
- **Ne supprime rien** : l'ancien dragon va dans `ServerStorage > MapBackup_<date>`.
- Fais d'abord **un seul dragon**, montre une capture à Will, attends son accord, puis fais le reste.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Le modèle
`Dragon_LowPoly` remplace l'ancien dragon généré sous Blender. Style **low-poly sculpté** : facettes visibles, silhouette exagérée (grosse tête, poitrail massif, taille fine), accents lumineux. Environ 25 × 12 × 21 studs (ailes ouvertes), **7 562 triangles** en tout : on peut en mettre beaucoup à l'écran.

Il est **découpé en 25 MeshParts** pour être animé : `Torso` (racine), `ChestGem`, `Neck1`, `Neck2`, `Head`, `Jaw`, `Eyes`, `Tail1` à `Tail4`, et pour chaque côté (`R`/`L`) `FrontUpperLeg`, `FrontLowerLeg`, `BackUpperLeg`, `BackLowerLeg`, `WingUpper`, `WingLower`, `WingGlow`. Le dragon regarde vers **-Z**.

Les couleurs viennent d'une **texture palette** 64 × 64 (une case par couleur). Changer de lignée = changer la texture. Les 4 palettes sont dans `objets/palettes/` : `Feu` (rouge et or, incluse dans le `.glb`), `Glace`, `Foret`, `Ombre`. Les morceaux lumineux (`Eyes`, `ChestGem`, `WingGlowR`, `WingGlowL`) sont en **Neon**, de la couleur de la lignée. Pour une rareté plus basse, on peut éteindre la gemme et le bout des ailes (`Transparency = 1`).

## Import (fait par Will)
**Avatar → Import 3D** de `Dragon_LowPoly.glb`, unité **Stud**, **parties séparées** (ne pas fusionner), textures importées. Si la taille est environ 3,5 fois trop grande ou trop petite, change l'unité. Si le dragon arrive couché ou tourné, redresse le modèle entier avant de continuer.

Importe aussi les 3 autres palettes (`Asset Manager → Import`) et note leurs `rbxassetid`.

## A. Rig
1. Mets `objets/RigDragon.lua` dans un **ModuleScript** `ReplicatedStorage > DragonRig`.
2. Lance une fois dans la barre de commande :
   ```lua
   require(game.ReplicatedStorage.DragonRig).build(workspace.Dragon_LowPoly)
   ```
   Le script crée un `Motor6D` à chaque articulation, met les morceaux lumineux en Neon, ancre seulement `Torso`, met les autres morceaux en `Massless` et `CanCollide = false`, puis ajoute un `AnimationController` avec un `Animator`.
3. Vérifie : bouge un `Motor6D` (par exemple `Transform` du `Jaw` ou de `WingUpperR`) et regarde si le morceau tourne autour de la bonne articulation. Aucun trou ne doit apparaître au pli.
4. Remplis `texture` dans `Rig.VARIANTS` avec les `rbxassetid` des palettes, puis teste :
   ```lua
   require(game.ReplicatedStorage.DragonRig).setVariant(workspace.Dragon_LowPoly, "Glace")
   ```

## B. Animations
Avec l'**Animation Editor**, crée au minimum `Idle` (respiration, battement lent des ailes, queue qui ondule), `Walk` et `Fly`. Publie-les et joue-les via l'`Animator`. Montre d'abord `Idle` à Will.

## C. Mise en jeu
Remplace l'ancien dragon sauvage au même endroit, avec la même logique (spawns, IA). Garde une Part de collision invisible et simple (une boîte pour le corps) : les MeshParts du dragon n'ont pas de collision.

## Fin
- Capture du dragon dans chaque lignée pour Will.
- Console sans erreur rouge.
- Entrée dans `DevJournal`, et retire la ligne `EN COURS`.
