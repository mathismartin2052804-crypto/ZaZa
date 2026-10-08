"""Cherche des sons dans le Creator Store de Roblox et garde ceux des
bibliothèques officielles sous licence (ProSoundEffects, APMOfficial).

Usage : python3 recherche_sons.py "dragon roar" [motif-regex]
"""
import json, re, sys, urllib.parse, urllib.request

OFFICIELS = {"ProSoundEffects", "APMOfficial"}
API = "https://apis.roblox.com/toolbox-service/v1"


def get(url):
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.load(r)


def chercher(mot_cle, pages=2):
    ids, curseur = [], ""
    for _ in range(pages):
        url = f"{API}/marketplace/3?limit=100&keyword={urllib.parse.quote(mot_cle)}"  # 3 = Audio
        if curseur:
            url += f"&cursor={curseur}"
        d = get(url)
        ids += [x["id"] for x in d["data"]]
        curseur = d.get("nextPageCursor")
        if not curseur:
            break
    details = []
    for i in range(0, len(ids), 50):
        lot = ",".join(map(str, ids[i:i + 50]))
        details += get(f"{API}/items/details?assetIds={lot}")["data"]
    return details


if __name__ == "__main__":
    mot_cle = sys.argv[1]
    motif = sys.argv[2] if len(sys.argv) > 2 else "."
    vus = set()
    for x in chercher(mot_cle):
        a = x["asset"]
        if x["creator"]["name"] in OFFICIELS and re.search(motif, a["name"], re.I) and a["name"] not in vus:
            vus.add(a["name"])
            print(f'{a["id"]} | {a["name"]} | {a.get("duration")}s | {x["creator"]["name"]}')
