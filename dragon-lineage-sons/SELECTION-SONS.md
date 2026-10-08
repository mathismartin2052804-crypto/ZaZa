# Dragon Lineage : présélection de sons

49 sons pour 26 besoins (dragons, feu, os, œufs, ambiance, interface), avec 2 ou 3 candidats par besoin.

## D'où viennent les sons
Tous viennent de **ProSoundEffects**, une bibliothèque sous licence fournie par Roblox dans le Creator Store :
- gratuits, utilisables dans n'importe quel jeu ;
- rien à importer ni à faire modérer : on met l'ID dans un `Sound` et ça marche ;
- aucun risque de droits d'auteur.

J'ai écarté les sons mis en ligne par des joueurs. Beaucoup sont copiés d'autres jeux (*Skyrim*, *Elden Ring*…) et risquent d'être supprimés.

⚠️ **Je n'entends pas les sons.** J'ai choisi d'après les noms, les durées et les descriptions. C'est à toi d'écouter et de garder le meilleur de chaque besoin.

## Les fichiers
| Fichier | Où le mettre dans Studio | Rôle |
|---|---|---|
| `SonsDragonLineage.lua` | `ReplicatedStorage`, en **ModuleScript** nommé `SonsDragonLineage` | La liste des sons, par catégorie |
| `EcouteSons.client.lua` | `StarterPlayer > StarterPlayerScripts`, en **LocalScript** | Outil pour écouter les sons un par un (**à retirer avant de publier**) |
| `outils/recherche_sons.py` | (reste sur l'ordinateur) | Pour chercher d'autres sons plus tard |

## Comment écouter
1. Mets les deux scripts aux bons endroits, puis lance **Play**.
2. **E** : son suivant, **Q** : précédent, **R** : rejouer.
3. La console (Output) affiche le nom et l'ID du son en cours. Note ceux que tu gardes.

## La sélection
| Catégorie | Besoin | Candidats | Remarque |
|---|---|---|---|
| Dragons | Rugissement puissant | 3 | Pour l'apparition d'un dragon ou une attaque forte |
| | Grognement calme | 2 | Dragon au repos ou méfiant |
| | Cri d'attaque | 2 | Cris de ptérodactyle, aigus et rapides |
| | Sifflement | 2 | Menace avant une attaque |
| | Battement d'ailes | 3 | Le n° 3 est une boucle de 33 s pour le vol |
| | Pas lourds | 2 | |
| Feu | Souffle de feu | 3 | |
| | Boule de feu | 2 | Sons courts pour un projectile |
| | Brasero | 2 | Boucles pour les `Brazier_DragonClaw` |
| Os | Craquement | 3 | |
| | Cliquetis | 1 | Pas de vrai bruit de squelette : un treillis en bois qui s'en approche |
| | Impact de pierre | 2 | Pour les portes du repaire |
| Œufs | Fissure | 3 | Le n° 3 (6 s) craque petit à petit |
| | Coque qui casse | 1 | |
| | Cri de bébé dragon | 3 | À essayer avec `PlaybackSpeed` entre 1.2 et 1.5 |
| Ambiance | Repaire | 2 | Boucles inquiétantes |
| | Gouttes dans la caverne | 2 | |
| | Vent de montagne | 2 | Boucles |
| | Dragon qui passe | 1 | Souffle de vent au passage d'un dragon |
| Interface | Clic | 2 | |
| | Récompense | 3 | Carillons magiques |
| | Niveau supérieur | 1 | |
| | Pièces | 2 | |

## Conseils
- **Varier** : pour un son qui revient souvent (pas, clics, coups), joue-le avec un `PlaybackSpeed` un peu différent à chaque fois (entre 0.9 et 1.1). On ne l'entend plus comme une répétition.
- **Sons dans le monde** : mets le `Sound` dans une pièce (le brasero, le dragon) pour qu'on l'entende plus fort en s'approchant. Règle `RollOffMaxDistance`.
- **Volume** : commence vers 0.5 et monte si besoin. Les ambiances doivent rester discrètes (0.2 à 0.4).
- **Chercher d'autres sons** : `python3 outils/recherche_sons.py "mot anglais" "filtre"`, par exemple `python3 outils/recherche_sons.py "thunder" "thunder"`.
