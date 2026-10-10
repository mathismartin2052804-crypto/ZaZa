# Dragon Lineage : icônes du HUD (instructions pour une nouvelle session locale)

> **Will : colle ce fichier dans une NOUVELLE conversation Claude locale** (connectée à Roblox Studio par MCP), avec le jeu ouvert dans Studio.

---

## Contexte
Tu aides **Will** sur le jeu Roblox **Dragon Lineage** (Team Create). Le jeu est en **compétition** contre d'autres équipes : le rendu doit être soigné.

Parle en **français**, simplement : Will débute.

Dans le **HUD** (l'interface affichée en jeu), certaines icônes ne sont que des **emoji** (🔥, 🥚, 💰, ⚙️…). Will veut les remplacer par de vraies images, dessinées dans **le même style que la boutique** du jeu.

Will fera générer les images par **Gemini (modèle Nano Banana)**. **Gemini ne voit pas le jeu et on ne lui envoie aucune image** : il ne reçoit que du texte. Ton travail est donc d'écrire **un prompt par icône** qui décrit tout en mots : le style de la boutique, l'objet à dessiner et le cadrage.

## Règles (obligatoires)
- Lis `ServerStorage > DevJournal` avant de commencer et écris en haut : `EN COURS : Will (Claude) inventaire des icônes emoji du HUD (lecture seule)`.
- **Tu ne modifies rien dans le jeu.** C'est une session **en lecture seule** : tu regardes, tu lis les propriétés, tu fais des captures. Le HUD et la boutique ne font peut-être pas partie de la part de Will. Regarde dans le DevJournal qui s'en occupe et dis-le à Will.
- **N'invente rien.** Si tu ne peux pas voir une couleur ou un style (aucune capture possible, image introuvable), demande à Will de t'envoyer une capture plutôt que de deviner.
- À la fin, ajoute une entrée en bas du journal (« inventaire des icônes du HUD fait, prompts Gemini donnés à Will ») et retire la ligne `EN COURS`.

---

## Étape 1 : trouver toutes les icônes emoji
Lance ce script dans la **barre de commande** de Studio (ou avec l'outil MCP d'exécution de code). Il **ne modifie rien** : il cherche les emoji dans les textes de l'interface **et** dans les scripts, car beaucoup d'interfaces sont créées par script au lancement du jeu.

```lua
local function emojisIn(s)
	if typeof(s) ~= "string" or s == "" then return nil end
	local found = {}
	local ok = pcall(function()
		for _, cp in utf8.codes(s) do
			if (cp >= 0x1F000 and cp <= 0x1FAFF) -- emoji, objets, animaux, symboles
				or (cp >= 0x2190 and cp <= 0x2BFF) -- flèches, ☀ ⚔ ⚙ ★ ✨ ❤ ⬆…
				or cp == 0x3030 or cp == 0x303D or cp == 0x3297 or cp == 0x3299 then
				table.insert(found, utf8.char(cp))
			end
		end
	end)
	return (ok and #found > 0) and table.concat(found, " ") or nil
end

local roots = {
	game:GetService("StarterGui"),
	game:GetService("StarterPlayer"),
	game:GetService("ReplicatedFirst"),
	game:GetService("ReplicatedStorage"),
	game:GetService("ServerScriptService"),
	game:GetService("ServerStorage"),
	workspace,
}

for _, root in roots do
	for _, inst in root:GetDescendants() do
		if inst:IsA("TextLabel") or inst:IsA("TextButton") or inst:IsA("TextBox") then
			local e = emojisIn(inst.Text)
			if e then
				print(("[UI] %s | %s | texte=%q | taille=%s"):format(inst:GetFullName(), e, inst.Text, tostring(inst.Size)))
			end
		elseif inst:IsA("LuaSourceContainer") then
			local ok, src = pcall(function() return inst.Source end)
			if ok then
				for n, line in string.split(src, "\n") do
					local e = emojisIn(line)
					if e then
						print(("[SCRIPT] %s | ligne %d | %s | %s"):format(inst:GetFullName(), n, e, line:sub(1, 140)))
					end
				end
			end
		end
	end
end
print("Recherche des emoji terminée")
```

Ensuite :
1. **Ignore** ce qui est dans `ServerStorage > MapBackup_*` (ce sont des sauvegardes).
2. Pour chaque résultat `[SCRIPT]`, lis le script pour comprendre **où l'emoji s'affiche** : dans quel bouton, quel compteur, quelle notification.
3. Lance le jeu (**Play**), ouvre l'**Explorer** dans `Players > (joueur) > PlayerGui` et vérifie que tu n'as rien raté. Fais une **capture du HUD en jeu** si ton MCP le permet.
4. Garde seulement ce qui est **vraiment une icône du HUD** : un emoji seul ou à côté d'un chiffre (monnaie, œufs, boutons de menu…). Un emoji au milieu d'une phrase de dialogue ou de notification n'est pas une icône : liste-le à part, Will décidera.

Montre à Will un **tableau** avant d'aller plus loin :

| # | Emoji | Où (chemin) | Rôle (ce que ça représente) | Taille à l'écran (px environ) | Bouton cliquable ? |
|---|---|---|---|---|---|

Demande à Will de confirmer ou corriger les **rôles** (par exemple « 🥚 = incubateur » ou « 🥚 = nombre d'œufs ? »). **Attends sa réponse.**

---

## Étape 2 : décrire le style (la « DA ») de la boutique
Trouve la boutique (cherche un `ScreenGui` ou un `Frame` qui contient `Shop`, `Boutique` ou `Store`). Ouvre-la en jeu et **fais une capture** si possible.

Relève **précisément**, sans deviner :
- **Les icônes d'objets existantes de la boutique** (ce sont les **vraies références**) : les `ImageLabel` et `ImageButton` avec un `Image` en `rbxassetid://…`. Regarde-les (capture, ou aperçu dans l'Explorer) et décris :
  - le **type de rendu** : 3D cartoon type Roblox, peinture, illustration plate (flat), pixel art, low-poly…
  - le **contour** : pas de contour, contour noir épais, contour coloré, épaisseur relative ;
  - les **ombres** : en aplats (cel shading), dégradés doux, ombre portée ;
  - la **lumière** : d'où elle vient, reflets brillants ou matière mate, halo/lueur autour ;
  - le **niveau de détail** et les **proportions** (formes arrondies et exagérées, ou réalistes) ;
  - le **cadrage** : objet de face ou de 3/4, combien de place il prend dans le carré ;
  - le **fond** de l'icône : transparent, cercle, carte colorée…
- **Le cadre de la boutique** : `BackgroundColor3` (donne le code **hex**), `UIGradient` (couleurs et angle), `UIStroke` (couleur, épaisseur), `UICorner` (arrondi), polices (`FontFace`), couleurs des textes et des prix, couleurs par **rareté** s'il y en a.
- **La palette** : les **6 à 10 couleurs principales** en hex, avec leur usage (fond, bordure, accent, or, texte…).

Si une icône de la boutique est introuvable ou ne s'affiche pas pour toi, **demande une capture à Will**.

Écris ensuite une **« fiche de style »** en anglais (Gemini comprend mieux l'anglais pour les images), courte et précise, en 6 à 10 lignes. Exemple de forme (**à remplacer par ce que tu as vraiment observé**) :

```
STYLE: <type de rendu>, <contour>, <ombres>, <lumière>, <matières>.
PROPORTIONS: <formes>, <niveau de détail>.
PALETTE: <hex + usage>, ...
FRAMING: single object, centered, <angle de vue>, fills about 80% of the square, 10% empty margin on each side.
BACKGROUND: plain flat solid <couleur> background, no gradient, no ground shadow, no frame.
```

Montre la fiche à Will et **attends son accord**.

---

## Étape 3 : écrire un prompt Gemini par icône
Pour chaque icône validée, écris **un prompt complet et autonome** : Will va les coller un par un et Gemini ne se souvient pas forcément des précédents. Chaque prompt répète donc **toute** la fiche de style.

Modèle (en anglais) :

```
Create a square 1:1 game UI icon, 1024x1024, for a Roblox game called Dragon Lineage (fantasy dragons, eggs, lairs).

SUBJECT: <l'objet, décrit concrètement : forme, couleurs (hex), matière, détails importants. Ex : "a single dragon egg, tall oval shape, deep orange shell #E8641B with darker scale pattern, three thin glowing cracks of light yellow #FFD25A">.
MEANING: this icon represents <le rôle : "the egg incubator button">, it must be instantly recognizable at very small size.

<FICHE DE STYLE COMPLÈTE>

READABILITY: will be displayed at about <taille> pixels, so use a bold simple silhouette, strong contrast, few large shapes, no tiny details.
DO NOT: no text, no letters, no numbers, no emoji style, no watermark, no border or frame around the icon, no multiple objects, no realistic photo.
```

Règles pour les prompts :
- **Le sujet ne copie pas l'emoji** : il décrit un objet du **monde de Dragon Lineage** (une pièce d'or gravée d'une tête de dragon plutôt qu'un 💰 générique, si ça colle au jeu). Si tu n'es pas sûr, propose 2 idées à Will.
- **Le fond** : Nano Banana ne sait pas faire de vrai fond transparent. Demande un **fond uni** d'une couleur **absente de l'icône** (blanc `#FFFFFF` par défaut ; magenta `#FF00FF` si l'objet est blanc ou très clair). Will enlèvera le fond ensuite (outil de suppression de fond) pour avoir un **PNG transparent**.
- **Même famille** : même angle de vue, même épaisseur de contour, même lumière et même marge pour toutes les icônes. Elles doivent aller ensemble dans la même barre.
- Garde l'ordre du tableau de l'étape 1 et donne à chaque prompt un **nom de fichier** (`icon_incubateur.png`, `icon_or.png`…).

---

## Ce que tu rends à Will
Un seul message final avec :
1. le **tableau** des icônes (étape 1, corrigé par Will) ;
2. la **fiche de style** validée ;
3. **un bloc de code par icône** avec son prompt complet (facile à copier) et le nom du fichier ;
4. un **mode d'emploi** très court :
   - coller les prompts un par un dans Gemini (Nano Banana) ;
   - **commencer par l'icône la plus proche des objets de la boutique** : si elle est réussie, garder la même conversation Gemini pour les suivantes (le style reste plus régulier) ;
   - enlever le fond pour obtenir un PNG transparent, puis le **réduire à 512×512** ;
   - importer les PNG dans Studio avec le **Gestionnaire de ressources** (Asset Manager) et noter les `rbxassetid` ;
5. le **plan de remplacement** pour plus tard : pour chaque emoji, quel objet de l'interface ou quelle ligne de script il faudra changer pour mettre un `ImageLabel` à la place.

**Ne fais pas le remplacement dans cette session.** Il se fera plus tard, une fois les images prêtes, avec l'accord de la personne qui s'occupe du HUD.
