# Vérifie l'export hors Studio : déforme Dragon_V6.glb comme Roblox (Bone.CFrame de repos * Bone.Transform,
# Transform venant du vrai AnimDragon.lua exécuté par verif_anim_v6.luau) et compare chaque sommet au générateur.
# Usage : lune run verif_anim_v6.luau ../dragon-v6/AnimDragon.lua > anim_v6.json
#         python3 verif_glb_v6.py ../dragon-v6/Dragon_V6.glb anim_v6.json   (écart attendu : 0.0000 stud)
import sys, json, struct, numpy as np
sys.path.insert(0, ".")
from scipy.spatial import cKDTree
import rig_v6 as RG, demo_animations_v6 as D, rendu

def load_glb(p):
    b = open(p, "rb").read()
    jl = struct.unpack_from("<I", b, 12)[0]
    g = json.loads(b[20:20 + jl]); binb = b[20 + jl + 8:]
    def acc(i):
        a = g["accessors"][i]; v = g["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5121: np.uint8, 5125: np.uint32}[a["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        return np.frombuffer(binb, dt, a["count"] * n, v["byteOffset"]).reshape(a["count"], n)
    return g, acc

g, acc = load_glb(sys.argv[1])
lua = json.load(open(sys.argv[2]))
skin = g["skins"][0]; joints = skin["joints"]
IBM = acc(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
nodes = g["nodes"]
parent = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
names = [nodes[j]["name"] for j in joints]
rig = RG.Rig()
FN = {"Course": D.course, "Marche": D.marche, "Vol": D.vol, "Rugissement": D.rugit, "Repos": D.repos,
      "Decollage": D.decollage, "Atterrissage": D.atterrissage, "SouffleFeu": D.souffle_feu}

def cf(c):
    M = np.eye(4); M[:3, 3] = c[:3]; M[:3, :3] = np.array(c[3:]).reshape(3, 3); return M


ref_rest = np.concatenate([L[2] for L in rig.layers])
tree = cKDTree(ref_rest)
for case in lua:
    T = {n: cf(c) for n, c in case["T"].items()}
    W = {}
    def world(j):
        if j in W: return W[j]
        L = np.eye(4); L[:3, 3] = nodes[j].get("translation", [0, 0, 0])
        M = L @ T[nodes[j]["name"]]
        W[j] = (world(parent[j]) if j in parent else np.eye(4)) @ M
        return W[j]
    Mj = np.stack([world(j) @ IBM[k] for k, j in enumerate(joints)])
    # poses du générateur, yeux compris (clignements, saccades et regard sont les mêmes des deux côtés)
    P, off = FN[case["anim"]](case["t"])
    ref = np.concatenate([it[0] for it in rig.items(P, off)])
    err = 0
    for m in g["meshes"]:
        a = m["primitives"][0]["attributes"]
        V = acc(a["POSITION"]).astype(float); J = acc(a["JOINTS_0"]).astype(int); Wt = acc(a["WEIGHTS_0"]).astype(float)
        M = np.einsum("nk,nkij->nij", Wt, Mj[J])
        v = np.einsum("nij,nj->ni", M[:, :3, :3], V) + M[:, :3, 3]
        cand = tree.query_ball_point(V, 1e-3)
        e = np.array([min(np.linalg.norm(ref[c] - x, axis=1).min() for c in [cc]) if cc else np.inf for cc, x in zip(cand, v)])
        err = max(err, e.max())
        assert np.allclose(Wt.sum(1), 1, atol=1e-4)
    print(f'{case["anim"]:12s} t={case["t"]:.3f}  écart max GLB+Luau vs générateur = {err:.4f} studs')
