# Dragon Lineage : dragon sauvage v1 (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), après avoir importé `objets/Dragon_Sauvage.glb` du zip `dragon-sauvage-v1.zip`.

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Sa part est **le monde et la course**, dont **les dragons sauvages**. Le jeu est en **compétition** : le rendu doit être soigné, sans rien casser.

Parle en **français**, simplement : Will débute.

**Règles d'équipe** (obligatoires) :
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) dragon sauvage v1`.
- Ne touche **qu'à la part de Will**.
- **Ne supprime rien** : l'ancien dragon va dans `ServerStorage > MapBackup_<date>`.
- Fais d'abord **un seul dragon**, montre une capture à Will, attends son accord, puis fais le reste.
- À la fin : **aucune erreur rouge** dans la console, et une entrée en bas du journal.

## Le modèle
`Dragon_Sauvage` remplace l'ancien dragon généré sous Blender. Style lisse et stylisé, environ 24 × 11 × 20,5 studs (ailes ouvertes), 40 400 triangles en tout, aucun morceau au-dessus de 8 200.

Il est **découpé en 22 MeshParts** pour être animé : `Torso` (racine), `Neck1`, `Neck2`, `Head`, `Jaw`, `Eyes`, `Tail1` à `Tail4`, et pour chaque côté (`R`/`L`) `FrontUpperLeg`, `FrontLowerLeg`, `BackUpperLeg`, `BackLowerLeg`, `WingUpper`, `WingLower`. Le dragon regarde vers **-Z**.

Les couleurs viennent d'une **texture palette** 64 × 64 (une case par couleur). Changer de lignée = changer la texture. Les 4 palettes sont dans `objets/palettes/` : `Feu` (rouge et or, incluse dans le `.glb`), `Glace`, `Foret`, `Ombre`. Les yeux sont une MeshPart à part, en **Neon**.

## Import (fait par Will)
**Avatar → Import 3D** de `Dragon_Sauvage.glb`, unité **Stud**, **parties séparées** (ne pas fusionner), textures importées. Si la taille est environ 3,5 fois trop grande ou trop petite, change l'unité. Si le dragon arrive couché ou tourné, redresse le modèle entier avant de continuer.

Importe aussi les 3 autres palettes (`Asset Manager → Import`) et note leurs `rbxassetid`.

## A. Rig
1. Mets `objets/RigDragon.lua` dans un **ModuleScript** `ReplicatedStorage > DragonRig`.
2. Lance une fois dans la barre de commande :
   ```lua
   require(game.ReplicatedStorage.DragonRig).build(workspace.Dragon_Sauvage)
   ```
   Le script crée un `Motor6D` à chaque articulation, ancre seulement `Torso`, met les autres morceaux en `Massless` et `CanCollide = false`, puis ajoute un `AnimationController` avec un `Animator`.
3. Vérifie : bouge un `Motor6D` (par exemple `Transform` du `Jaw` ou de `WingUpperR`) et regarde si le morceau tourne autour de la bonne articulation. Aucun trou ne doit apparaître au pli.
4. Remplis `texture` dans `Rig.VARIANTS` avec les `rbxassetid` des palettes, puis teste :
   ```lua
   require(game.ReplicatedStorage.DragonRig).setVariant(workspace.Dragon_Sauvage, "Glace")
   ```

## B. Animations
Avec l'**Animation Editor**, crée au minimum `Idle` (respiration, battement lent des ailes, queue qui ondule), `Walk` et `Fly`. Publie-les et joue-les via l'`Animator`. Montre d'abord `Idle` à Will.

## C. Mise en jeu
Remplace l'ancien dragon sauvage au même endroit, avec la même logique (spawns, IA). Garde une Part de collision invisible et simple (une boîte pour le corps) : les MeshParts du dragon n'ont pas de collision.

## Fin
- Capture du dragon dans chaque lignée pour Will.
- Console sans erreur rouge.
- Entrée dans `DevJournal`, et retire la ligne `EN COURS`.
