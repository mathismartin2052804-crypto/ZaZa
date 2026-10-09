# Guide pour créer des meshes Dragon Lineage (à lire en début de conversation)

> **Will : colle ce fichier (ou donne son chemin) au début de chaque nouvelle conversation cloud qui crée des meshes.** Il résume comment le projet marche et tous les pièges déjà rencontrés, pour ne pas les refaire.

## 1. Le contexte en bref
- Jeu Roblox **Dragon Lineage** (Team Create). La part de **Will** : la carte, la route, les dragons sauvages, l'ambiance.
- Parle **français**, simplement : Will débute. Phrases courtes, pas de jargon sans explication.
- Le travail se fait en **deux sessions** :
  1. **Session cloud** (celle-ci) : elle génère les `.glb` en Python, fait des aperçus, écrit un fichier `PROMPT-SESSION-LOCALE-SERIEx.md` et un zip `dragon-lineage-seriex.zip`, puis pousse sur la branche git.
  2. **Session locale** (connectée à Roblox Studio par MCP) : Will importe les `.glb`, puis colle le prompt. Cette session règle les matériaux et place les objets.
- Règles d'équipe à recopier dans chaque prompt local : lire `ServerStorage > DevJournal`, écrire `EN COURS : …` en haut ; ne toucher qu'à la part de Will ; **ne rien supprimer** (l'ancien va dans `ServerStorage > MapBackup_<date>`) ; un seul exemplaire d'abord, une capture, attendre l'accord ; à la fin, aucune erreur rouge et une entrée dans le journal.

## 2. Démarrage rapide (copier-coller)
```bash
pip install trimesh matplotlib numpy scipy        # scipy est OBLIGATOIRE (voir piège 3.1)
cd dragon-lineage-decor/generateur
python3 build.py assets5 meshes-serie5 apercu-serie5.png    # module, dossier de sortie, aperçu
python3 vue5.py ../vue-dragon-cristal.png                    # aperçu multi-angles d'un objet long
python3 demo5.py demo5.tpl.html /chemin/scratchpad/demo.html # démo 3D animée (navigateur)
# v5 du dragon de cristal (serpentin, pose de vol) — version actuelle :
python3 demo5.py demo5v5.tpl.html /chemin/scratchpad/dragon-cristal-demo.html assets5v5
python3 vue5.py /chemin/scratchpad/vue-v5.png assets5v5
# v3 du dragon de cristal (ancienne marche au sol, abandonnée) :
python3 build.py assets5v3 meshes-serie5-v3 /chemin/scratchpad/apercu-v3.png
python3 vue5.py ../vue-dragon-cristal-v3.png assets5v3
python3 demo5.py demo5v3.tpl.html /chemin/scratchpad/dragon-cristal-demo.html assets5v3
```
- `meshlib.py` : la boîte à outils (`loft`, `ring`, `tube`, `lathe`, `blob`, `box`, `transform`, `rot_matrix_*`, `export_glb`).
- `assetsN.py` : une série d'objets. Chaque module expose `all_assets()` et renvoie une liste d'`Asset`.
- `build.py` : exporte un `.glb` par objet, écrit `manifest.json` (triangles, taille, couleurs, matériaux) et une planche d'aperçu.
- Les anciennes séries sont gardées telles quelles. Une nouvelle version d'un objet porte un nouveau nom (`_v2`, `_v3`) et n'écrase jamais l'ancienne.

## 3. Les pièges rencontrés (et la solution)

### 3.1 Environnement
- **`trimesh` n'est pas installé au départ.** Il faut installer `trimesh matplotlib numpy scipy`. **Sans `scipy`**, chaque calcul de volume ou de normales affiche une énorme trace « No module named 'scipy' ». Les fichiers sortent quand même, mais la sortie devient illisible.
- Le chemin de travail du shell change parfois tout seul. **Utilise toujours des chemins absolus.**
- **Après un `sed` sur un fichier**, l'outil Write refuse d'écrire (« modified since read ») : il faut d'abord relire le fichier avec Read.
- Les fichiers temporaires (démo HTML, captures, images de la vidéo) vont dans le **scratchpad**, pas dans le dépôt.

### 3.2 Repère, échelle, pivot
- Repère : **Y vers le haut, 1 unité = 1 stud.** L'avant de Roblox est **-Z**. Attention, les crânes v2/v3 regardent vers **+Z**. Le dragon de cristal regarde vers **-Z**. Choisis une convention et écris-la en tête du module.
- `build.py` **recale chaque objet pour que sa base soit à Y = 0**. Si tu exportes aussi des pivots (pour une animation), applique le même décalage (voir `demo5.py`).
- À l'import, Roblox peut appliquer un facteur d'environ **3,5** si l'unité n'est pas « Stud ». Mets toujours le tableau des tailles attendues dans le prompt local.
- Un nœud du GLB devient **une MeshPart**, avec **une seule couleur et un seul matériau**. Pour deux couleurs, il faut deux parties (ex. `Seg01` et `Seg01_Blades`).
- Les sommets sont exportés en coordonnées monde. Dans Roblox, le **pivot de chaque MeshPart est donc au centre de sa boîte englobante**, pas à l'endroit logique (hanche, charnière). Un script d'animation doit calculer ses décalages à partir de la pose de repos.
- **Mobile** : 20 000 triangles pour un gros dragon, ça passe. Ce qui coûte vraiment sur téléphone : beaucoup de morceaux **transparents** (Glass/Transparency) qui se superposent, le nombre de morceaux (environ 1 appel de dessin chacun) et une animation qui tourne même quand le joueur est loin. Garde `RenderFidelity = Automatic`, coupe l'animation au-delà d'une certaine distance et évite d'avoir beaucoup de gros dragons à l'écran en même temps.
- Limite Roblox : environ **20 000 triangles par MeshPart**. Vise moins de 3 000 pour un décor, et environ 15 000 au total pour un gros dragon.

### 3.3 Géométrie
- **Normales inversées** : `build.py` affiche `ATTENTION normales inversées` quand un volume est négatif. Dans `assets5.py`, la fonction `_oriented(v, f)` retourne les faces automatiquement : utilise-la pour chaque nouveau morceau.
- Avec `loft`, l'ordre des points de l'anneau décide du sens des faces. Dans un `ring`, l'ordre suit le sens `axis_u → axis_v`.
- Les lames plates « cristal » : `blade()` (section en losange) et `sabre()` (lame couchée vers l'arrière, pointe relevée). Ce qui a marché pour ressembler à la référence : des lames **larges** (environ 0,6 × le rayon du corps), **longues**, **peu relevées** (`hook` faible). Des lames fines et dressées donnent un hérisson.
- Pour une pièce animée par morceaux, fais **chevaucher** les morceaux (longueur d'environ 1,3 à 1,5 fois l'écart), sinon des trous apparaissent quand ça plie.

### 3.4 Aperçus
- **matplotlib** : avec `set_box_aspect((1,1,1))`, un objet long (dragon de 78 studs) devient minuscule. `vue5.py` règle l'aspect sur les vraies dimensions. Le rendu matplotlib reste approximatif : il sert à vérifier les formes, pas le style.
- **Pour juger le style, utilise la démo three.js** (`demo5.tpl.html` + `demo5.py`). Elle intègre le GLB en base64 et offre le rendu cristal (transparent + arêtes lumineuses), les couleurs Roblox, une couleur par morceau, des angles prédéfinis et l'animation.
- **Capture de la démo** : `capture_demo.js`, lancé depuis le dossier qui contient `dragon-cristal-demo.html` :
  `NODE_PATH=$(npm root -g) node capture_demo.js`
  Il faut les options `--use-gl=swiftshader --ignore-gpu-blocklist` (déjà dans le script) pour le WebGL. **Ne lance jamais `playwright install`** : Chromium est déjà installé.
- Bugs déjà corrigés dans la démo : (1) la boîte englobante doit être calculée **avant** de déplacer les meshes dans les groupes d'animation, sinon on obtient « 0 × 0 × 0 » et un écran vide ; (2) modifie le **gabarit** (`demo5.tpl.html`) et pas le HTML généré, qui est écrasé à chaque génération ; (3) la barre d'outils a besoin de `width:max-content`, sinon elle passe sur deux lignes.
- three.js : `three@0.128.0` sur jsDelivr, avec `examples/js/loaders/GLTFLoader.js` et `examples/js/controls/OrbitControls.js` (versions non-module, qui marchent dans un artifact).
- Publie la démo comme artifact, **toujours depuis le même fichier**, pour garder le même lien (`https://claude.ai/artifact/2ZhRnWaw8UKQeyF9NuVvFW` pour le dragon de cristal).

### 3.5 Références (images, vidéos, sites)
- **ArtStation bloque l'accès (403)**, même avec l'API `.json`. Demande directement des captures ou une vidéo à Will.
- Pour une vidéo, fais une planche d'images :
  ```bash
  ffmpeg -v error -i video.mp4 -vf "fps=2,scale=640:-1,tile=4x6" -frames:v 1 planche.png
  ffmpeg -v error -ss 1.6 -i video.mp4 -frames:v 1 -vf scale=1280:-1 image.png   # une image précise
  ```
  Recadre (`crop=`) les vidéos de Roblox Studio : on y lit la **durée de l'animation** dans la timeline de l'Animation Editor (1,32 s pour le dragon de cristal).
- **Regarde toute la vidéo avant de coder, y compris la fin.** Fais la planche sur toute la durée, puis zoome sur chaque passage (gros plan de la tête, profil, animation dans Blender, animation dans Studio). Erreur déjà faite (deux fois) : la v3 a été animée en **marche au sol**, alors que la vidéo montre un dragon qui **VOLE**. Les indices : **l'ombre est détachée des griffes** (rien ne touche le sol), les pattes **pagaient dans le vide**, le corps ondule de haut en bas. Regarde toujours où est l'ombre. Avant d'écrire une animation, décris-la à Will en une phrase (« il vole, le corps ondule, les pattes pagaient ») et attends son accord.
- **Compare les proportions, pas seulement les détails.** Mesure sur une image de profil : longueur de la tête / longueur totale, hauteur de la tête / hauteur du corps, position des pattes. Un modèle peut avoir toutes les bonnes pièces et rater quand même l'allure générale.
- **Droits** : un modèle posté sur ArtStation **n'est pas libre de droits**. Le dragon de cristal est reproduit avec l'accord de son auteur (un ami de Will). Si l'auteur a déjà le modèle dans Roblox Studio (c'est le cas sur la vidéo), le plus fidèle est de lui demander le fichier `.rbxm` (clic droit → Save to File) et son animation, plutôt que de tout refaire.

### 3.6 Communication avec Will
- Will peut changer d'avis en cours de route (« l'anime pas maintenant »). Adapte-toi tout de suite, mais **garde ce qui servira plus tard** (le découpage en morceaux est resté, pour l'animation).
- Montre toujours un aperçu (image ou démo) **avant** de préparer l'import dans Studio, puis propose une courte liste de choses à améliorer.
- Pas de pull request sauf si Will la demande. Commit et push sur la branche de la session.
- Dès le début, demande la vidéo ou les images de référence si elles ne sont pas jointes. Ne propose pas d'améliorations « à l'aveugle » sans le dire.

### 3.7 Animer une créature (marche ou vol)
> **Le dragon de cristal VOLE** (voir 3.5 et 4). Ce qui suit sur l'appui au sol servait à la marche v3, abandonnée ; la formule des matrices et l'IK à deux os restent valables pour le vol (pattes qui pagaient, morceaux qui ondulent).
- **Une patte rigide ne peut pas garder le pied au sol** pendant que le corps bouge. Il faut au moins **trois morceaux par patte** (cuisse, tibia, pied) et un calcul « IK à deux os » : on donne la hanche et la cheville, la fonction trouve le genou (`ik_knee` dans `assets5v3.py`, `ikKnee` dans la démo).
- **Construis la pose de repos avec la même IK** : on place la hanche et le point d'appui au sol, et le genou est calculé. Comme ça, les griffes touchent exactement Y = 0 au repos.
- **Cycle d'un pied** : pendant l'appui (60 % du temps), le pied recule à la vitesse du sol (`STRIDE / (DUTY × durée)`). Pendant le vol, il se lève (sinus) et revient devant. Si la vitesse du sol et celle des pieds en appui ne sont pas les mêmes, les pieds glissent.
- **Une seule formule pour tous les morceaux** : `M = Translation(nouveau pivot) × Rotation × Translation(-pivot de repos)`. Elle marche telle quelle en three.js (matrices) et en Luau (`CFrame.new(p) * R * CFrame.new(-p0)`). Le script Roblox reprend le même calcul que la démo.
- Dans la démo, ajoute un **sol qui défile et des ombres** : sans eux, impossible de voir si les pieds glissent ou flottent.
- Pour capturer une pose précise, mets la démo en pause depuis Playwright : `p.evaluate(() => { playing = false; tAnim = 0.66; })`, puis prends la capture.

### 3.8 Donner du caractère à une créature (et ne pas faire « chien »)
Remarque de Will sur la v4 : « il fait trop chien ou renard ». Ce qui donne l'allure d'un quadrupède, et la correction faite en v5 :
- **proportions** : un corps 4 fois plus long que haut, posé haut sur ses pattes = un chien. Un dragon oriental est **environ 8 à 10 fois plus long que haut** ; les pattes sont courtes par rapport au corps ;
- **dos droit et horizontal** = un chien. Le corps doit faire **une grande arche** (tête basse, dos au plus haut vers les 3/5, queue qui redescend) ;
- **pattes en zigzag avec un talon relevé** = des pattes de chien. Il faut des **bras fins presque droits** qui pendent sous le ventre et de **grandes mains en serres** (doigts écartés, griffes recourbées) ;
- **grosse touffe au bout d'une queue courte** = une queue de renard ;
- calcule le « dos de la main » pareil des deux côtés (`np.cross(x, main)`), sinon une main se plie à l'envers.

Ce qui manquait à la v2 du dragon (remarque de Will : « la tête n'est pas assez grosse, le dragon manque de caractère ») :
- **La tête est le point d'attention.** Pour un dragon « boss », elle doit être au moins aussi large que le corps avec sa crinière, et faire environ 1/6 à 1/5 de la longueur totale. Une petite tête sur un gros corps donne un serpent, pas un dragon.
- **L'expression vient de quelques formes fortes** : des arcades sourcilières épaisses qui descendent vers le museau (air méchant), une bouche ouverte avec de grands crocs visibles, des joues hérissées qui élargissent la silhouette de face, un ornement au milieu du front (crête, gemme).
- **La silhouette avant les détails** : vérifie la vue de face et de profil en ombre chinoise. Si on ne reconnaît pas la créature en silhouette, ajouter des lames n'y changera rien.

## 4. Le dragon de cristal (série 5) : ce qu'il faut savoir pour continuer
> **Version actuelle : v5** (`assets5v5.py`, `demo5v5.tpl.html`, planche `comparaison-silhouette-dragon-v5.png`). La démo publiée (même lien) montre la v5. Les anciennes versions sont gardées telles quelles.
>
> **v5 (silhouette « pas chien ») :** tête v4 reprise à l'identique (validée par Will) ; 38 morceaux de 2,6 studs (environ 118 studs de long, queue de 10 morceaux qui s'affine jusqu'à 0,8) ; cou en S (creux derrière la nuque, tête relevée) ; corps plus large que haut et **collerette** de grandes lames sur `Seg01`–`Seg03` qui partent sur les côtés (de face, sans elle, le dragon fait « colonne ») ; colonne en grande arche (`spine()`) ; bras en `Seg10`, pattes arrière en `Seg28` ; pattes de vol en 3 morceaux (bras, avant-bras, main en serres), épaisses et couvertes de plaques de cristal (`_plates`) ; **patte arrière : genou en avant, talon en arrière, orteils vers l'AVANT** (le pied tourné vers la queue faisait une patte « à l'envers ») ; antennes écartées sur les côtés (`v4.ANTENNA` remplacé dans la v5) ; les plaques des pattes sont dans des morceaux à part, `SegXX_LegYY_Blades` et `SegXX_LegYY_Shin_Blades` (couleur des lames) : **dans le script, ils suivent la cuisse et le tibia, pas le morceau `SegXX`** ; `a.meta["legs"]` donne `hip`, `knee`, `ankle`, `hand` (direction des doigts), `l1`, `l2`, `bend` ; le dragon est à environ `FLY_H = 24` studs du sol ; environ 22 500 triangles et 103 morceaux avant les retouches ci-dessous (Will accepte un peu plus de 20 000, mais il faut que ça tourne sur mobile). **Pas encore d'animation** : Will veut d'abord un dragon satisfaisant.
>
> **Retouches v5 (demandées par Will, planche `comparaison-gueule-meches-dragon-v5.png`) :** (1) **gueule** : avant, elle était du même bleu que le reste. `head5()` reprend `v4.head()` à l'identique mais sort les dents dans `Head_Teeth` (haut) et `Head_Jaw_Teeth` (bas), en blanc glacé (`#E6F4FF`, Ice), et ajoute un intérieur sombre : `Head_Mouth` (palais et joues, `#070B1C`), `Head_Jaw_Mouth` (plancher) et `Head_Jaw_Tongue` (langue bleu nuit). **Règle pour le script : tout ce qui commence par `Head_Jaw` pivote avec la mâchoire.** Les membranes des joues relient le palais à la mâchoire ouverte : si la mâchoire se ferme, elles traversent un peu, ça ne se voit pas. (2) **mèches hérissées** : `flame()` restait à moins de 15° du corps, ce qui donnait des mèches « plaquées ». La couche du dessus utilise maintenant `bristle()` : base couchée, puis la mèche se relève jusqu'à `rise` (environ 20 à 50°, plus sur le dos et sur l'arrière du corps) et la pointe se redresse encore (`hook`) ; 15 % de très longues mèches. La couche courte du dessous reste plaquée (elle cache le cœur foncé). (3) **yeux C** (iris or `#FFB22E`, fente noire), choisis par Will à la place des yeux B ; la démo les met par défaut. Total : 22 844 triangles, 108 morceaux (Will optimisera le budget plus tard). Dans la démo, tester `Teeth`/`Mouth`/`Tongue` **avant** `Jaw`, sinon ces parties passent en cristal bleu.
>
> **Mèches en flammes (remarque de Will : « trop angulaire, linéaire, comme s'il s'était fait électrocuter ») :** la première `bristle()` avait 5 points et un angle qui montait régulièrement : des pics droits, fins et tous dans le même sens. Version actuelle (planche `comparaison-meches-flammes-dragon-v5.png`) : 7 points, angle `0,06 + rise·u^1,6 + hook·u^3` (couchée au départ puis une **courbe** qui se relève), S sur le côté (13 % de la longueur), base **1,5 fois plus large** (flammes, pas aiguilles), `rise` très variable (×0,55 à ×1,45) et fort surtout sur le haut du dos et l'arrière, flancs plus couchés, `lean` qui penche certaines mèches sur le côté. Animer le bout des mèches a été écarté : il faudrait environ 40 morceaux de plus (ou un mesh avec os), trop lourd pour mobile ; la vague du corps suffit. Longueur des mèches plafonnée à `14 × rs` studs (une mèche de 21 studs « sortait de l'ordinaire ») et lames de la collerette plus courtes sous le cou (une longue lame pendait sous la tête). Total : 27 004 triangles (Will optimisera plus tard).
>
> **Import dans Roblox (fait) :** `python3 build.py assets5v5 meshes-serie5-v5 vue-dragon-cristal-v5.png` (GLB + manifest ; l'aperçu matplotlib est illisible pour un dragon si long : `vue-dragon-cristal-v5.png` a été remplacé par des captures de la démo), puis `python3 rig5v5.py ../meshes-serie5-v5/DragonCristalRig.lua` (ModuleScript des pivots de repos, **à régénérer à chaque changement du modèle**). Le LocalScript `meshes-serie5-v5/DragonCristalVol.client.lua` reprend `pose()` à l'identique ; il recale le repère du GLB sur la partie `Head` (centre + échelle via `HeadSize`) et vérifie avec `Seg20`. Il a été **testé hors de Roblox** : Luau CLI (`luau`, release GitHub 0.650) + un faux `Vector3`/`CFrame`, on extrait la partie entre `-- @@MATH` et `-- @@FIN`, et on compare les matrices avec celles de la démo (Playwright, `pose(t)` puis `o.matrix`) : écart max 0,0005. Prompt : `PROMPT-SESSION-LOCALE-SERIE5.md` (réécrit pour la v5) ; zip : `dragon-lineage-serie5.zip` (prompt, `objets/`, `scripts/`, aperçu).
>
> **Plumage choisi : C « Fluides »** (`PLUMAGE = "C"` par défaut ; la démo se construit avec `... assets5v5 C`, un seul style = pas de boutons).
>
> **Liaison tête–cou–corps (Will : « rigide et un peu brouillon », planche `comparaison-cou-dragon-v5.png`) :** (1) il n'y avait pas de vrai cou : le crâne s'arrêtait net, un vide le séparait de `Seg01`, déjà presque aussi gros que le corps. Maintenant : **nuque** (le crâne se prolonge et s'affine, sections `nape` dans `head5`) et **cou** de `Seg01` à `Seg06` (`NECK_SEGS`) qui passe de 2,5 à 4,1 de rayon, avec des anneaux réguliers (sans torsion ni jitter) qui se chevauchent. (2) trois crinières se superposaient (crinière + collerette de la v4 dans `Head_Blades`, collerette des `Seg01`–`03`) : elles sont retirées et remplacées par **une seule crinière** (`mane()`, 30 lames en 3 rangs sur la nuque, larges et peu ondulées pour couler ensemble ; lames des côtés plus longues = allure « lion » de face). (3) **tête plus souple** dans `pose()` : la vague est plus faible près de la tête (×0,3 à la tête, normale à partir de s = 0,18), la tête suit la direction moyenne des 3 premiers morceaux (`headDir`) avec un retard de 0,08 s (`HEAD_LAG`), plus un petit hochement (0,05 rad). Pas de morceau en plus. Total : 28 388 triangles, 117 morceaux.
>
> **Styles de plumage (Will : « plus fluide, pas piquant », il choisit dans la démo) :** `PLUMAGE` dans `assets5v5.py` = `"0"` flammes courbes (précédent), `"A"` flammes douces (couchées, pointe arrondie), `"B"` plumes (courtes, larges, en feuille, qui se chevauchent), `"C"` mèches fluides (longues, ondulées de côté et de haut en bas). Les tirages aléatoires sont identiques pour tous les styles. La démo les embarque tous : `python3 demo5.py demo5v5.tpl.html sortie.html assets5v5 0,A,B,C` (boutons Flammes / Douces / Plumes / Fluides ; environ 11 Mo, sous la limite de 16 Mo). Planche : `comparaison-plumages-dragon-v5.png`. **Une fois le style choisi**, mettre `PLUMAGE` à ce style et ne garder que lui dans la démo. Pattes arrière : même mouvement que les pattes avant (avant, amplitude réduite et genou en sens inverse).
>
> **Vol (démo, `demo5v5.tpl.html`, fonction `pose(t)` à reprendre telle quelle dans le LocalScript) :** boucle `T = 1,32 s`. (1) Colonne : chaque point monte et descend de `(0,9 + 2,1·s)·sin(w − 2π·1,15·s)` (s = 0 à la tête, 1 au bout de la queue : une vague qui part de la tête), plus un petit balancement de côté `0,5·s·sin(w − 2π·0,6·s + 1,2)` ; le repère de chaque morceau suit la nouvelle direction (`basis(f) × restInv`). (2) Pattes : rotation autour de l'axe X (latéral) à l'épaule/hanche (0,5 rad), puis au coude/genou (0,45, retard 0,9, sens inversé à l'arrière) et au poignet/cheville (0,5, retard 1,7), en chaîne (`thigh → shin → foot`) ; déphasage FL 0, FR 0,9, BL π, BR π + 0,9. (3) Mâchoire (tout `Head_Jaw*`) : se ferme de 0 à 0,13 rad autour de `jaw_hinge`. (4) Moustaches `Head_WhiskerL1..3` / `R1..3` : chaîne de 3 morceaux, pivots dans `meta["whiskers"]`, rotation X de 0,1 à 0,24 rad avec un retard de 1 rad par morceau. (5) Yeux : `Head_Lids` (fermée) et `Head_LidsHalf` (mi-close) sont **cachées** au repos (Transparency 1 dans Studio) ; toutes les 3,7 s : mi-close 0,05 s → fermée 0,09 s → mi-close 0,06 s. Pupilles `Head_Pupils_L/R` : toutes les 2,3 s, nouveau regard (lacet ±0,16 rad, tangage ±0,08) par rotation autour d'un point 0,9 stud derrière le centre de l'œil (`meta["eyes"]`). (6) Sol qui défile à 14 studs/s ; rien ne touche le sol (ombre loin dessous). **Menton** : les 7 mèches de la barbe de la v4 partaient jusqu'à 0,9 stud sous la mâchoire (vide visible, remarque de Will) ; `_beard_fix()` les remonte. Total : 23 068 triangles, 117 morceaux.
>
> **v4 :** nouvelle tête (yeux B, regard froncé `Head_Brows`, gemme à anneaux `Head_Gem`, pupilles `Head_Pupils`, museau court et carré, crocs irréguliers), validée par Will.
>
> **v3** (`assets5v3.py`, `demo5v3.tpl.html`, `meshes-serie5-v3/`) :
>
> Ce que la v3 a changé et qui a marché :
> - **tête** : `HEAD_SCALE = 1.4`, puis un étirement `HEAD_WIDEN = diag(1.4, 1.2, 1.0)` (plus large et plus haute, sans allonger encore). Le museau est relevé de 0,2 rad (`HEAD_PITCH`) pour regarder devant et pas le sol. Une **collerette** de 16 lames qui rayonnent autour de la nuque donne la silhouette « lion » de la vidéo vue de face. Pour l'expression : arcades en V, gueule ouverte (0,5 rad), deux grands crocs en haut et en bas, gemme Neon au front ;
> - **corps** : cœur ovale (1,22 fois plus haut que large), une couche de 8 lames courtes plaquées et une couche de 10 longues lames en S (`flame()`), avec de temps en temps une très longue mèche ;
> - **pattes** : 3 morceaux (`SegXX_LegYY`, `_Shin`, `_Foot`). `a.meta["legs"]` donne `hip`, `knee`, `ankle`, `contact` (point d'appui au sol), `l1`, `l2` (longueurs des os) et `bend` (de quel côté plie le genou) ;
> - **budget** : 19 172 triangles au total (Will a validé environ 20 000). Le plus gros morceau, la tête avec ses lames, fait environ 2 700 triangles.
> - **Animation v3 (démo, ABANDONNÉE : c'était une marche, la vidéo montre un vol)** : boucle de 1,32 s, `DUTY = 0,6`, `STRIDE = 5` studs, déphasage des pattes FL 0 / FR 0,1 / BL 0,5 / BR 0,6. Le dos se bombe (jusqu'à 2,2 studs entre les pattes) au moment où les pattes arrière se posent. Petit rebond de 0,2 stud deux fois par cycle ; la tête hoche ; la queue ondule avec du retard ; la mâchoire se ferme un peu puis se rouvre.
>
> Ce qui suit décrit la v2 ; les noms des morceaux restent valables pour la v3, à part les pattes.

- Fichiers : `generateur/assets5.py` (modèle), `vue5.py` (aperçu), `demo5.py` + `demo5.tpl.html` (démo animée), `meshes-serie5/` (GLB + manifest), `PROMPT-SESSION-LOCALE-SERIE5.md` (import).
- **Noms des parties** (le script d'animation s'en sert, ne les change pas) :
  - `Head`, `Seg01` … `Seg30` : la chaîne qui ondule ;
  - `<Chaîne>_Blades` : les lames, collées à leur morceau ;
  - `Head_Jaw` : la mâchoire et la barbe (pivote autour de la charnière) ;
  - `Head_Eyes` : les yeux en Neon ;
  - `Seg10_LegFL/FR` et `Seg25_LegBL/BR` : les pattes (pivotent à la hanche).
- `a.meta` donne les pivots de repos : `chain` (un point par morceau), `jaw_hinge`, `legs[nom].hip`.
- **Animation voulue (d'après la vidéo) : un VOL, pas une marche.** Boucle de **1,32 s**. L'ombre est loin sous les griffes : rien ne touche le sol. Le corps **ondule de haut en bas** (une vague qui part de la tête et va vers la queue), les pattes **pagaient dans le vide** avec un décalage entre elles, la tête reste dans l'axe du cou. (Ancienne note fausse, corrigée : « une marche au sol ».) À faire seulement quand Will aura validé la forme. Dans Blender, l'auteur utilise une chaîne d'os avec des contrôleurs en cercle le long du dos (on les voit en orange dans la vidéo).
- La démo v2 avait déjà une vague de la tête à la queue avec des pattes qui balancent : c'était **la bonne idée** (un vol). Elle avait été refusée à tort, en croyant que la vidéo montrait une marche.
- Pour Roblox, l'animation devra être faite **côté client** (LocalScript), avec `workspace:BulkMoveTo`, des parties Anchored, et `ModelStreamingMode = Atomic` sur le modèle. Ne fais pas bouger 70 parties depuis le serveur à chaque image.
- **À faire pour la v3 (validé par Will)** :
  - corps plus touffu et plus haut : deux couches de lames (courtes et plaquées dessous, longues dessus), lames qui s'écartent aussi sur les côtés, longueurs variées ;
  - lames plus ondulées : 7 points, courbe en S, légère torsion, pointes en flamme. Sur la vidéo, elles sont **couchées le long du corps** comme des mèches, pas dressées comme des piquants ;
  - **tête beaucoup plus grosse** (environ 1,5 fois) et plus expressive : museau plus long, grands crocs en haut et en bas, bouche ouverte, arcades épaisses, joues hérissées, ornement au front, crinière rabattue vers l'arrière et les côtés, antennes courbées ;
  - pattes plus longues et fines avec de grandes griffes, touffe de queue plus fournie ;
  - pour rester dans le budget : lames à 3 faces au lieu de 4.
