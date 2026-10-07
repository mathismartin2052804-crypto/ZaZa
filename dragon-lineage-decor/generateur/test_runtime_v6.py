# Contrôle des pieds sur le relief (sortie de test_runtime_v6.luau) : avec les mêmes Bone.Transform qu'en jeu,
# le bout des griffes de chaque patte doit monter ou descendre de la hauteur de sol donnée, pied gardé à plat.
# Usage : lune run test_runtime_v6.luau ../dragon-v6/AnimDragon.lua > runtime_v6.json
#         python3 test_runtime_v6.py runtime_v6.json
import sys, json, numpy as np
sys.path.insert(0, ".")
import allures_v6 as AL

sk = AL._Os()
rest = {b[0]: (b[1], np.asarray(b[2], float)) for b in sk.bones}


def cf(c):
    M = np.eye(4); M[:3, 3] = c[:3]; M[:3, :3] = np.array(c[3:]).reshape(3, 3); return M


def monde(T):
    W = {}
    def get(n):
        if n not in W:
            par, h = rest[n]
            L = np.eye(4); L[:3, 3] = h - (rest[par][1] if par else 0)
            W[n] = (get(par) if par else np.eye(4)) @ L @ T[n]
        return W[n]
    for n in rest:
        get(n)
    return W


cases = json.load(open(sys.argv[1]))
off, on = (monde({n: cf(c) for n, c in k["T"].items()}) for k in cases)
pire = 0
for kind in ("Front", "Back"):
    for sd in ("R", "L"):
        foot = kind + "Foot" + sd
        h = rest[foot][1]
        griffe = np.array([h[0], AL.SOL, AL.PIVOT_Z[kind]]) - h
        p0, p1 = (W[foot][:3, :3] @ griffe + W[foot][:3, 3] for W in (off, on))
        dy = cases[1]["attendu"][foot]
        rot = np.degrees(np.arccos(np.clip((np.trace(off[foot][:3, :3].T @ on[foot][:3, :3]) - 1) / 2, -1, 1)))
        e = max(abs(p1[1] - p0[1] - dy), np.linalg.norm((p1 - p0)[[0, 2]]))
        pire = max(pire, e)
        print(f"{foot:11s} sol {dy:+.2f}  griffes {p1[1] - p0[1]:+.3f} (dérive horizontale "
              f"{np.linalg.norm((p1 - p0)[[0, 2]]):.3f})  pied tourné de {rot:.2f}°")
print(f"écart max {pire:.3f} stud")
sys.exit(0 if pire < 0.05 else 1)
