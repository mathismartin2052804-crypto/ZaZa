"""Génère les sons cartoon de Dragon Lineage par synthèse (aucun échantillon externe).

Usage : python3 synth_cartoon.py [dossier_sortie]
Sortie : un .ogg par son + manifest.json (catégorie, besoin, nom, durée, boucle).
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- briques

def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a=0.005, d=0.05, s=0.7, r=0.1):
    """Enveloppe attaque / déclin / maintien / relâche, en secondes."""
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    s_len = max(n - a - d - r, 0)
    e = np.concatenate([
        np.linspace(0, 1, a, endpoint=False),
        np.linspace(1, s, d, endpoint=False),
        np.full(s_len, s),
        np.linspace(s, 0, r),
    ])
    return np.pad(e, (0, max(n - len(e), 0)))[:n]


def env_exp(n, decay):
    return np.exp(-np.arange(n) / SR / decay)


def osc(freq, kind="sine"):
    """Oscillateur à fréquence variable (freq = tableau ou nombre)."""
    freq = np.broadcast_to(np.asarray(freq, dtype=float), np.shape(freq) or (1,))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    if kind == "sine":
        return np.sin(phase)
    if kind == "tri":
        return 2 / np.pi * np.arcsin(np.sin(phase))
    if kind == "square":
        return np.tanh(4 * np.sin(phase))
    if kind == "saw":
        return 2 * ((phase / (2 * np.pi)) % 1) - 1
    raise ValueError(kind)


def sweep(f0, f1, n, curve=1.0):
    x = np.linspace(0, 1, n) ** curve
    return f0 * (f1 / f0) ** x  # glissement exponentiel


def noise(n):
    return RNG.uniform(-1, 1, n)


def lowpass(x, cutoff):
    """Passe-bas 1 pôle ; cutoff peut varier dans le temps."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def bandpass(x, center, q=4.0):
    """Passe-bande (biquad, centre éventuellement variable)."""
    center = np.broadcast_to(np.asarray(center, dtype=float), x.shape)
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        w = 2 * np.pi * center[i] / SR
        alpha = np.sin(w) / (2 * q)
        cw = np.cos(w)
        a0 = 1 + alpha
        b0, b2 = alpha / a0, -alpha / a0
        a1, a2 = -2 * cw / a0, (1 - alpha) / a0
        out = b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, x[i], y1, out
        y[i] = out
    return y


def reverb(x, size=0.25, mix=0.2):
    """Petite réverbération (réponse impulsionnelle de bruit qui décroît)."""
    n = int(size * SR)
    ir = noise(n) * env_exp(n, size / 5)
    ir[0] = 0
    wet = fit(np.convolve(x, ir), len(x) + n) * 0.08
    dry = np.pad(x, (0, n))
    return dry * (1 - mix) + wet * mix


def fit(x, length):
    return np.pad(x, (0, max(length - len(x), 0)))[:length]


def place(dst, src, at):
    i = int(at * SR)
    end = min(len(dst), i + len(src))
    dst[i:end] += src[: end - i]


def fade(x, fin=0.003, fout=0.01):
    a, b = int(fin * SR), int(fout * SR)
    x = x.copy()
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def normalize(x, peak=0.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def make_loop(x, xfade=0.5):
    """Boucle sans coupure : fondu enchaîné de la fin sur le début."""
    n = int(xfade * SR)
    head, body, tail = x[:n], x[n:-n], x[-n:]
    ramp = np.linspace(0, 1, n)
    return np.concatenate([tail * (1 - ramp) + head * ramp, body])


# ---------------------------------------------------------------- sons

def rawr(dur=1.1, f_hi=260, f_lo=110, grit=0.6, cute=0.0):
    """Rugissement cartoon : voix « RAWR » (dents de scie + formants + vibrato)."""
    t = t_axis(dur)
    n = len(t)
    pitch = np.concatenate([sweep(f_lo * 1.3, f_hi, n // 5, 0.6), sweep(f_hi, f_lo, n - n // 5, 1.6)])
    pitch *= 1 + 0.035 * np.sin(2 * np.pi * 7 * t)  # vibrato
    voice = osc(pitch, "saw") * (1 + grit * 0.5 * osc(np.full(n, 34), "sine"))  # grain « grr »
    vowel_a = bandpass(voice, sweep(500, 800, n), 3) + 0.7 * bandpass(voice, sweep(1000, 1250, n), 4)
    body = lowpass(voice, 900) * 0.6
    breath = bandpass(noise(n), 1800, 1.5) * 0.15
    x = (vowel_a + body + breath) * env_adsr(n, 0.04, 0.15, 0.8, dur * 0.45)
    if cute:
        x = x + cute * osc(pitch * 2, "tri") * env_adsr(n, 0.02, 0.1, 0.5, dur * 0.4) * 0.3
    return reverb(x, 0.35, 0.18)


def purr(dur=1.4, f=75):
    t = t_axis(dur)
    n = len(t)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 22 * t) ** 2
    x = lowpass(osc(np.full(n, f) * (1 + 0.02 * np.sin(2 * np.pi * 2 * t)), "saw"), 500) * am
    x += bandpass(noise(n), 300, 1.2) * 0.2 * am
    return x * env_adsr(n, 0.12, 0.1, 0.9, 0.35)


def yip(dur=0.32, f0=500, f1=1500, wobble=0.0):
    t = t_axis(dur)
    n = len(t)
    p = np.concatenate([sweep(f0, f1, n * 2 // 3, 0.7), sweep(f1, f1 * 0.8, n - n * 2 // 3)])
    p *= 1 + wobble * np.sin(2 * np.pi * 18 * t)
    x = osc(p, "tri") * 0.8 + osc(p * 2, "sine") * 0.25
    return reverb(x * env_adsr(n, 0.01, 0.05, 0.8, 0.08), 0.2, 0.15)


def hiss(dur=0.9):
    n = int(dur * SR)
    x = bandpass(noise(n), sweep(3500, 6000, n), 1.2) + 0.4 * lowpass(noise(n), 3000)
    return x * env_adsr(n, 0.06, 0.1, 0.7, dur * 0.5)


def flap(beats=3, gap=0.22):
    out = np.zeros(int((beats * gap + 0.3) * SR))
    for i in range(beats):
        n = int(0.16 * SR)
        f = sweep(1200, 250, n)
        b = lowpass(noise(n), f) * env_adsr(n, 0.02, 0.04, 0.5, 0.08) * 1.6
        b += osc(sweep(140, 70, n)) * env_exp(n, 0.05) * 0.4
        place(out, b, i * gap)
    return out


def bwomp(f0=130, f1=38, dur=0.45, wobble=0.0):
    t = t_axis(dur)
    n = len(t)
    p = sweep(f0, f1, n, 0.5) * (1 + wobble * np.sin(2 * np.pi * 12 * t))
    x = osc(p) * env_exp(n, dur / 3) + 0.3 * lowpass(noise(n), 400) * env_exp(n, 0.03)
    return reverb(x, 0.3, 0.15)


def fwoosh(dur=1.0, rise=True, crackle=0.5):
    n = int(dur * SR)
    center = np.concatenate([sweep(400, 2200, n // 3), sweep(2200, 500, n - n // 3)]) if rise else sweep(1800, 400, n)
    x = bandpass(noise(n), center, 1.4) * 1.4 + lowpass(noise(n), 300) * 0.5
    x *= env_adsr(n, 0.05, 0.15, 0.75, dur * 0.5)
    for _ in range(int(crackle * 25 * dur)):
        place(x, pop_click(RNG.uniform(1500, 4000)) * RNG.uniform(0.2, 0.5), RNG.uniform(0.05, dur * 0.8))
    return reverb(x, 0.3, 0.15)


def pop_click(f=2500, dur=0.012):
    n = int(dur * SR)
    return osc(np.full(n, f)) * env_exp(n, dur / 4)


def fwip(dur=0.28):
    n = int(dur * SR)
    x = bandpass(noise(n), sweep(600, 4000, n, 0.6), 2.5) * 1.8
    x += osc(sweep(300, 1200, n)) * 0.25
    return x * env_adsr(n, 0.01, 0.05, 0.8, 0.08)


def fireball(dur=0.6):
    out = np.zeros(int(dur * SR))
    place(out, fwip(0.25), 0)
    place(out, pop(220, 0.18) * 0.9, 0.2)
    place(out, fwoosh(0.35, False, 0.8) * 0.6, 0.2)
    return out


def pop(f=600, dur=0.12, bend=2.2):
    n = int(dur * SR)
    x = osc(sweep(f * bend, f, n, 0.3)) * env_exp(n, dur / 4)
    return x + fit(pop_click(3000), n) * 0.3


def boing(dur=0.6, f=180):
    t = t_axis(dur)
    n = len(t)
    p = f * (1 + 0.5 * np.exp(-t * 6) * np.sin(2 * np.pi * 14 * t))
    return osc(p, "tri") * env_exp(n, dur / 3)


def crackle_loop(dur=8.0, density=14):
    n = int(dur * SR)
    x = lowpass(noise(n), 250) * 0.25  # souffle du feu
    x += bandpass(noise(n), 900, 0.8) * 0.06 * (1 + 0.5 * np.sin(2 * np.pi * 0.4 * t_axis(dur)))
    for _ in range(int(dur * density)):
        f = RNG.uniform(900, 3500)
        place(x, pop_click(f, RNG.uniform(0.006, 0.02)) * RNG.uniform(0.15, 0.6), RNG.uniform(0, dur - 0.03))
    for _ in range(int(dur * 1.2)):
        place(x, pop(RNG.uniform(250, 500), 0.07, 1.6) * 0.35, RNG.uniform(0, dur - 0.1))
    return make_loop(x, 0.4)


def wood(f=900, dur=0.09):
    n = int(dur * SR)
    return (osc(np.full(n, f)) + 0.5 * osc(np.full(n, f * 2.76))) * env_exp(n, dur / 5)


def krak(hits=3):
    out = np.zeros(int(0.45 * SR))
    for i in range(hits):
        place(out, noise(int(0.02 * SR)) * env_exp(int(0.02 * SR), 0.004) * 0.9, i * 0.05)
        place(out, wood(RNG.uniform(700, 1100)) * 0.6, i * 0.05)
    return reverb(out, 0.2, 0.15)


def xylo_rattle(notes=(1046, 880, 1174, 988, 1318, 1046), gap=0.07):
    out = np.zeros(int((len(notes) * gap + 0.4) * SR))
    for i, f in enumerate(notes):
        n = int(0.3 * SR)
        tone = (osc(np.full(n, f)) + 0.35 * osc(np.full(n, f * 3.9))) * env_exp(n, 0.07)
        place(out, tone * 0.7, i * gap + RNG.uniform(0, 0.01))
    return reverb(out, 0.25, 0.2)


def bonk(f=320, dur=0.35):
    n = int(dur * SR)
    x = osc(sweep(f * 1.3, f, n, 0.2)) * env_exp(n, 0.08) + 0.6 * osc(np.full(n, f * 2.3)) * env_exp(n, 0.04)
    x += lowpass(noise(n), 1500) * env_exp(n, 0.01)
    return reverb(x, 0.2, 0.15)


def tiks(count=3, base=2200, gap=0.16):
    out = np.zeros(int((count * gap + 0.2) * SR))
    for i in range(count):
        place(out, fit(pop_click(base * (1 + 0.15 * i), 0.02), int(0.05 * SR)) + wood(base / 2 * (1 + 0.1 * i), 0.05) * 0.5, i * gap)
    return reverb(out, 0.15, 0.1)


def sparkle(count=6, dur=0.6, base=1568):
    scale = [1, 1.25, 1.5, 2, 2.5, 3]
    out = np.zeros(int((dur + 0.5) * SR))
    for i in range(count):
        f = base * scale[i % len(scale)]
        n = int(0.35 * SR)
        place(out, osc(np.full(n, f)) * env_exp(n, 0.08) * 0.4, i * dur / count)
    return reverb(out, 0.4, 0.3)


def hatch():
    out = np.zeros(int(1.2 * SR))
    place(out, krak(2) * 0.6, 0)
    place(out, pop(500, 0.18, 2.8), 0.12)
    place(out, sparkle(5, 0.4, 1318) * 0.8, 0.18)
    return out


def chirp(f=900, up=1.8, dur=0.22, trill=0.0):
    t = t_axis(dur)
    n = len(t)
    p = np.concatenate([sweep(f, f * up, n // 2), sweep(f * up, f * 1.2, n - n // 2)])
    p *= 1 + trill * np.sin(2 * np.pi * 30 * t)
    return osc(p, "sine") * env_adsr(n, 0.01, 0.03, 0.85, 0.05)


def baby_mew():
    out = np.zeros(int(0.9 * SR))
    place(out, chirp(700, 1.7, 0.2), 0)
    place(out, chirp(850, 1.5, 0.28, 0.03), 0.25)
    return reverb(out, 0.2, 0.15)


def baby_rawr():
    return rawr(0.55, 620, 380, grit=0.3, cute=1.0) * 0.9


def drone_loop(dur=10.0, f=55):
    t = t_axis(dur)
    n = len(t)
    x = sum(osc(np.full(n, f * k) * (1 + 0.004 * np.sin(2 * np.pi * (0.13 * k) * t)), "tri") / k for k in (1, 1.5, 2, 3))
    x = lowpass(x, 600) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))
    x += lowpass(noise(n), 200) * 0.3
    for _ in range(int(dur * 0.6)):
        place(x, plink(RNG.uniform(700, 1400)) * 0.35, RNG.uniform(0, dur - 0.5))
    return make_loop(reverb(x, 0.6, 0.3)[:n], 1.0)


def plink(f=1000):
    n = int(0.25 * SR)
    return osc(sweep(f * 0.6, f, n, 0.15)) * env_exp(n, 0.05)


def drips_loop(dur=8.0):
    x = np.zeros(int(dur * SR))
    for _ in range(int(dur * 1.5)):
        place(x, plink(RNG.uniform(800, 1800)) * RNG.uniform(0.4, 0.9), RNG.uniform(0, dur - 0.3))
    return make_loop(reverb(x, 0.8, 0.4)[: len(x)], 0.3)


def wind_loop(dur=10.0, whistle=True):
    t = t_axis(dur)
    n = len(t)
    center = 700 + 400 * np.sin(2 * np.pi * 0.11 * t) + 200 * np.sin(2 * np.pi * 0.27 * t)
    x = bandpass(noise(n), center, 1.0) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t))
    if whistle:
        x += osc(1100 + 150 * np.sin(2 * np.pi * 0.2 * t)) * 0.06 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t))
    return make_loop(x, 1.0)


def swoosh_by(dur=1.2):
    n = int(dur * SR)
    center = np.concatenate([sweep(300, 2500, n // 2), sweep(2500, 250, n - n // 2)])
    x = bandpass(noise(n), center, 2.0) * 1.6 * env_adsr(n, dur * 0.4, 0.05, 0.9, dur * 0.45)
    return reverb(x, 0.3, 0.2)


def click(f=1800):
    return pop(f, 0.05, 1.5) + fit(pop_click(4000, 0.006), int(0.05 * SR)) * 0.4


def coin(f1=988, f2=1318):
    out = np.zeros(int(0.45 * SR))
    n1, n2 = int(0.07 * SR), int(0.35 * SR)
    place(out, osc(np.full(n1, f1), "square") * env_adsr(n1, 0.002, 0.01, 0.9, 0.01) * 0.5, 0)
    place(out, osc(np.full(n2, f2), "square") * env_exp(n2, 0.1) * 0.5, 0.07)
    return out


# ---------------------------------------------------------------- catalogue

SONS = [
    # (catégorie, besoin, fichier, description, fonction, boucle)
    ("Dragons", "RugissementPuissant", "rawr_gros", "Gros RAWR grave", lambda: rawr(1.3, 230, 90, 0.8), False),
    ("Dragons", "RugissementPuissant", "rawr_moyen", "RAWR moyen, plus vif", lambda: rawr(0.9, 340, 150, 0.5), False),
    ("Dragons", "GrognementCalme", "grr_ronron", "Ronronnement grave « grrr »", lambda: purr(1.4, 70), False),
    ("Dragons", "GrognementCalme", "grr_court", "Petit grognement court", lambda: purr(0.7, 95), False),
    ("Dragons", "CriAttaque", "yip_aigu", "Cri qui monte « yip ! »", lambda: yip(0.3, 500, 1500), False),
    ("Dragons", "CriAttaque", "yip_vibre", "Cri vibrant, plus rigolo", lambda: yip(0.45, 400, 1200, 0.06), False),
    ("Dragons", "Sifflement", "pschh", "Sifflement « pschhh »", lambda: hiss(0.8), False),
    ("Dragons", "BattementAiles", "flap_3", "3 battements « fwup fwup fwup »", lambda: flap(3, 0.22), False),
    ("Dragons", "BattementAiles", "flap_2_lent", "2 battements lents", lambda: flap(2, 0.35), False),
    ("Dragons", "PasLourds", "bwomp", "Pas lourd « bwomp »", lambda: bwomp(130, 38, 0.45), False),
    ("Dragons", "PasLourds", "bwomp_rebond", "Pas qui rebondit un peu", lambda: bwomp(160, 45, 0.5, 0.08), False),
    ("Feu", "SouffleDeFeu", "fwoosh_long", "Grand « FWOOSH » qui crépite", lambda: fwoosh(1.2, True, 0.6), False),
    ("Feu", "SouffleDeFeu", "fwoosh_court", "Souffle court", lambda: fwoosh(0.6, True, 0.4), False),
    ("Feu", "BouleDeFeu", "fwip_pop", "« Fwip » puis petit « pouf »", fireball, False),
    ("Feu", "BouleDeFeu", "fwip", "« Fwip » seul, très court", lambda: fwip(0.25), False),
    ("Feu", "Brasero", "brasero_boucle", "Crépitement doux en boucle", lambda: crackle_loop(8, 14), True),
    ("Os", "Craquement", "krak", "« Krak » sec, comme du bois", lambda: krak(3), False),
    ("Os", "Craquement", "krak_simple", "Un seul « krak »", lambda: krak(1), False),
    ("Os", "Cliquetis", "squelette_xylo", "Squelette au xylophone (classique du cartoon)", xylo_rattle, False),
    ("Os", "ImpactPierre", "bonk", "« Bonk » rebondissant", lambda: bonk(320), False),
    ("Os", "ImpactPierre", "bonk_grave", "« Bonk » grave et lourd", lambda: bonk(160, 0.45), False),
    ("Oeufs", "Fissure", "tik_tik_tik", "3 petits « tik » qui montent", lambda: tiks(3), False),
    ("Oeufs", "Fissure", "tik_tik", "2 « tik » rapprochés", lambda: tiks(2, 2600, 0.1), False),
    ("Oeufs", "CoqueQuiCasse", "eclosion_pop", "Crac + POP + étincelles", hatch, False),
    ("Oeufs", "CoqueQuiCasse", "pop_boing", "POP + petit boing", lambda: np.concatenate([pop(450, 0.15, 3), boing(0.5, 220) * 0.6]), False),
    ("Oeufs", "CriBebeDragon", "bebe_miaou", "Deux petits cris mignons", baby_mew, False),
    ("Oeufs", "CriBebeDragon", "bebe_rawr", "Mini « rawr » de bébé", baby_rawr, False),
    ("Ambiance", "Repaire", "repaire_boucle", "Nappe grave et douce + gouttes", lambda: drone_loop(10, 55), True),
    ("Ambiance", "GouttesCaverne", "gouttes_boucle", "« Plink » de gouttes en boucle", lambda: drips_loop(8), True),
    ("Ambiance", "VentMontagne", "vent_boucle", "Vent doux qui siffle", lambda: wind_loop(10, True), True),
    ("Ambiance", "VentMontagne", "vent_doux_boucle", "Vent doux sans sifflement", lambda: wind_loop(10, False), True),
    ("Ambiance", "DragonQuiPasse", "swoosh", "« Swoooosh » au passage", lambda: swoosh_by(1.2), False),
    ("Interface", "Clic", "clic_pop", "Clic « pop » rond", lambda: click(1800), False),
    ("Interface", "Clic", "clic_bulle", "Clic bulle, plus grave", lambda: pop(700, 0.08, 1.8), False),
    ("Interface", "Pieces", "piece_bling", "Pièce « bling » façon jeu vidéo", coin, False),
    ("Interface", "Pieces", "piece_bling_grave", "Pièce plus grave", lambda: coin(659, 988), False),
]


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for cat, besoin, fichier, desc, fn, boucle in SONS:
        x = fn()
        x = normalize(x if boucle else fade(x), 0.7 if boucle else 0.89)
        wav = os.path.join(out_dir, fichier + ".wav")
        ogg = os.path.join(out_dir, fichier + ".ogg")
        write_wav(wav, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "4", ogg], check=True)
        os.remove(wav)
        manifest.append({"categorie": cat, "besoin": besoin, "fichier": fichier + ".ogg", "description": desc,
                         "duree": round(len(x) / SR, 2), "boucle": boucle})
        print(f"{fichier:22s} {len(x) / SR:5.2f}s")
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "sons-cartoon"))
