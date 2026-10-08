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
- **Regarde toute la vidéo avant de coder, y compris la fin.** Fais la planche sur toute la durée, puis zoome sur chaque passage (gros plan de la tête, profil, animation dans Blender, animation dans Studio). Erreur déjà faite : la v2 animait le dragon comme s'il **volait** (une vague qui court sur un corps en l'air), alors que la vidéo montre une **marche au sol**. Avant d'écrire une animation, décris-la à Will en une phrase (« il marche, le dos se bombe à chaque pas ») et attends son accord.
- **Compare les proportions, pas seulement les détails.** Mesure sur une image de profil : longueur de la tête / longueur totale, hauteur de la tête / hauteur du corps, position des pattes. Un modèle peut avoir toutes les bonnes pièces et rater quand même l'allure générale.
- **Droits** : un modèle posté sur ArtStation **n'est pas libre de droits**. Le dragon de cristal est reproduit avec l'accord de son auteur (un ami de Will). Si l'auteur a déjà le modèle dans Roblox Studio (c'est le cas sur la vidéo), le plus fidèle est de lui demander le fichier `.rbxm` (clic droit → Save to File) et son animation, plutôt que de tout refaire.

### 3.6 Communication avec Will
- Will peut changer d'avis en cours de route (« l'anime pas maintenant »). Adapte-toi tout de suite, mais **garde ce qui servira plus tard** (le découpage en morceaux est resté, pour l'animation).
- Montre toujours un aperçu (image ou démo) **avant** de préparer l'import dans Studio, puis propose une courte liste de choses à améliorer.
- Pas de pull request sauf si Will la demande. Commit et push sur la branche de la session.
- Dès le début, demande la vidéo ou les images de référence si elles ne sont pas jointes. Ne propose pas d'améliorations « à l'aveugle » sans le dire.

### 3.7 Donner du caractère à une créature
Ce qui manquait à la v2 du dragon (remarque de Will : « la tête n'est pas assez grosse, le dragon manque de caractère ») :
- **La tête est le point d'attention.** Pour un dragon « boss », elle doit être au moins aussi large que le corps avec sa crinière, et faire environ 1/6 à 1/5 de la longueur totale. Une petite tête sur un gros corps donne un serpent, pas un dragon.
- **L'expression vient de quelques formes fortes** : des arcades sourcilières épaisses qui descendent vers le museau (air méchant), une bouche ouverte avec de grands crocs visibles, des joues hérissées qui élargissent la silhouette de face, un ornement au milieu du front (crête, gemme).
- **La silhouette avant les détails** : vérifie la vue de face et de profil en ombre chinoise. Si on ne reconnaît pas la créature en silhouette, ajouter des lames n'y changera rien.

## 4. Le dragon de cristal (série 5) : ce qu'il faut savoir pour continuer
- Fichiers : `generateur/assets5.py` (modèle), `vue5.py` (aperçu), `demo5.py` + `demo5.tpl.html` (démo animée), `meshes-serie5/` (GLB + manifest), `PROMPT-SESSION-LOCALE-SERIE5.md` (import).
- **Noms des parties** (le script d'animation s'en sert, ne les change pas) :
  - `Head`, `Seg01` … `Seg30` : la chaîne qui ondule ;
  - `<Chaîne>_Blades` : les lames, collées à leur morceau ;
  - `Head_Jaw` : la mâchoire et la barbe (pivote autour de la charnière) ;
  - `Head_Eyes` : les yeux en Neon ;
  - `Seg10_LegFL/FR` et `Seg25_LegBL/BR` : les pattes (pivotent à la hanche).
- `a.meta` donne les pivots de repos : `chain` (un point par morceau), `jaw_hinge`, `legs[nom].hip`.
- **Animation voulue (d'après la vidéo, validée par Will) : une marche au sol, pas un vol.** Boucle de **1,32 s**. Les pieds se posent au sol et y restent pendant l'appui, puis se lèvent et repartent vers l'avant (grands pas, surtout les pattes avant). Le dos se **bombe** entre les pattes avant et arrière quand les pattes se rapprochent, et s'aplatit quand elles s'écartent (comme un furet). La tête reste basse et presque stable, la queue suit avec un peu de retard. Dans Blender, l'auteur utilise une chaîne d'os avec des contrôleurs en cercle le long du dos (on les voit en orange dans la vidéo).
- L'animation de la démo v2 (vague qui va de la tête à la queue, pattes qui balancent dans le vide) est **refusée** : elle donne l'impression que le dragon vole.
- Pour Roblox, l'animation devra être faite **côté client** (LocalScript), avec `workspace:BulkMoveTo`, des parties Anchored, et `ModelStreamingMode = Atomic` sur le modèle. Ne fais pas bouger 70 parties depuis le serveur à chaque image.
- **À faire pour la v3 (validé par Will)** :
  - corps plus touffu et plus haut : deux couches de lames (courtes et plaquées dessous, longues dessus), lames qui s'écartent aussi sur les côtés, longueurs variées ;
  - lames plus ondulées : 7 points, courbe en S, légère torsion, pointes en flamme. Sur la vidéo, elles sont **couchées le long du corps** comme des mèches, pas dressées comme des piquants ;
  - **tête beaucoup plus grosse** (environ 1,5 fois) et plus expressive : museau plus long, grands crocs en haut et en bas, bouche ouverte, arcades épaisses, joues hérissées, ornement au front, crinière rabattue vers l'arrière et les côtés, antennes courbées ;
  - pattes plus longues et fines avec de grandes griffes, touffe de queue plus fournie ;
  - pour rester dans le budget : lames à 3 faces au lieu de 4.
