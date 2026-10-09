# Écrit le ModuleScript Luau « DragonCristalRig » : les pivots de repos du dragon de cristal v5
# (colonne, pattes, mâchoire, moustaches, yeux), dans le même repère que le GLB exporté par build.py
# (base à Y = 0). Le LocalScript DragonCristalVol s'en sert pour refaire l'animation de la démo (pose()).
# Usage : python3 rig5v5.py ../meshes-serie5-v5/DragonCristalRig.lua
import sys
import numpy as np
import assets5v5

a = assets5v5.all_assets()[0]
mn, _ = a.bounds()
dy = mn[1]                                  # même recalage que build.py et demo5.py
sh = lambda q: [float(q[0]), float(q[1] - dy), float(q[2])]


def center(name):
    v = np.array(a.parts[name]["v"], float)
    v[:, 1] -= dy
    return [float(x) for x in (v.min(0) + v.max(0)) / 2], [float(x) for x in v.max(0) - v.min(0)]


def v3(q):
    return "Vector3.new(%.4f, %.4f, %.4f)" % tuple(q)


m = a.meta
hc, hs = center("Head")
cc, _ = center("Seg20")
L = ["-- Généré par generateur/rig5v5.py : NE PAS MODIFIER À LA MAIN (relancer le script).",
     "-- Pivots de repos du dragon de cristal v5, repère du GLB (studs, Y vers le haut, tête vers -Z).",
     "return {",
     "\tHeadCenter = %s,  -- centre de la boîte de « Head » : sert à recaler le modèle importé" % v3(hc),
     "\tHeadSize = %s,    -- taille de « Head » : sert à trouver l'échelle si l'import l'a changée" % v3(hs),
     "\tCheckPart = \"Seg20\", CheckCenter = %s,  -- pour vérifier le recalage" % v3(cc),
     "\tJawHinge = %s," % v3(sh(m["jaw_hinge"])),
     "\tChain = {"]
L += ["\t\t%s," % v3(sh(q)) for q in m["chain"]]
L += ["\t},", "\tLegs = {"]
for nm, g in m["legs"].items():
    L.append("\t\t{ Name = \"%s\", Tag = \"%s\", Seg = %d, Front = %s, Hip = %s, Knee = %s, Ankle = %s },"
             % (nm, nm[-2:], g["seg"], "true" if g["front"] else "false", v3(sh(g["hip"])), v3(sh(g["knee"])),
                v3(sh(g["ankle"]))))
L += ["\t},", "\tWhiskers = {"]
for k, pts in m["whiskers"].items():
    L.append("\t\t%s = { %s }," % (k, ", ".join(v3(sh(q)) for q in pts)))
L += ["\t},", "\tEyes = {"]
for k, e in m["eyes"].items():
    L.append("\t\t%s = { C = %s, N = %s }," % (k, v3(sh(e["c"])), v3(e["n"])))
L += ["\t},", "}", ""]
open(sys.argv[1], "w").write("\n".join(L))
print("ok", sys.argv[1], len(m["chain"]), "points")
