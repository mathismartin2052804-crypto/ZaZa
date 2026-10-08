# Dragon Lineage : sons cartoon

Les sons réalistes de la v1 sont abandonnés. On garde seulement les sons Roblox de **récompense** et de **niveau supérieur**.

Tous les autres sons sont des **sons cartoon fabriqués pour le jeu** par synthèse (`generateur/synth_cartoon.py`) : pop, boing, « RAWR », « fwoosh », squelette au xylophone… Comme ils ne viennent d'aucun autre jeu ni d'aucun site, il n'y a aucun problème de droits.

## Écouter et choisir
Ouvre `ecouter-les-sons.html` ou la page publiée. Le bouton ▶︎ joue chaque son directement dans la page. Coche ton préféré pour chaque besoin, puis clique sur « Copier mes choix » et colle le texte à Claude.

## La liste (36 sons, 21 besoins)
| Catégorie | Besoins |
|---|---|
| Dragons | Rugissement « RAWR », grognement, cri d'attaque, sifflement, battement d'ailes, pas lourds |
| Feu | Souffle « FWOOSH », boule de feu, brasero (boucle) |
| Os et pierre | Craquement « krak », squelette au xylophone, « bonk » |
| Œufs | Fissure « tik tik », éclosion « POP », cri de bébé dragon |
| Ambiance | Repaire, gouttes, vent (boucles), dragon qui passe |
| Interface | Clic, pièces (+ récompense et niveau supérieur gardés de Roblox) |

## Mettre les sons dans le jeu
Les sons fabriqués doivent être **importés dans Roblox** avant d'avoir un ID :
1. Dans Studio : **View → Asset Manager**, puis le bouton **Bulk Import**. Choisis les `.ogg` que tu as gardés dans `sons-cartoon/`.
2. Roblox les vérifie (modération), ce qui prend en général quelques minutes.
3. Clic droit sur chaque son → **Copy Asset ID**.
4. Dans `SonsDragonLineage`, remplace `id = nil` par `id(<le numéro>)`.

Roblox limite le nombre de sons importés par mois. N'importe donc que ceux que tu gardes : un par besoin, soit 21 au maximum.

## Les fichiers
| Fichier | Rôle |
|---|---|
| `sons-cartoon/*.ogg` | Les 36 sons cartoon, prêts à importer |
| `sons-cartoon/manifest.json` | Liste des sons (catégorie, besoin, durée, boucle) |
| `SonsDragonLineage.lua` | ModuleScript à mettre dans `ReplicatedStorage` |
| `EcouteSons.client.lua` | Outil d'écoute dans Studio (seulement les sons qui ont un ID ; à retirer avant de publier) |
| `ecouter-les-sons.html` | La page pour écouter et cocher |
| `generateur/synth_cartoon.py` | Le générateur : change les réglages et relance-le pour refaire un son |
| `outils/recherche_sons.py` | Recherche dans la bibliothèque Roblox |

## Conseils
- Pour un son qui revient souvent (pas, clics, pièces), change un peu le `PlaybackSpeed` à chaque fois (entre 0.9 et 1.1). La répétition s'entend beaucoup moins.
- Les boucles (brasero, repaire, gouttes, vent) vont dans un `Sound` avec `Looped = true`, placé dans l'objet concerné, avec un volume bas (0.2 à 0.4).
- Un son pas tout à fait comme tu veux (plus grave, plus long, plus mignon) ? Dis-le à Claude : il change les réglages du générateur et refait le son.
