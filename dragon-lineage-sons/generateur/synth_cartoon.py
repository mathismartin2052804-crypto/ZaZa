"""Génère les sons cartoon de Dragon Lineage par synthèse (aucun échantillon externe).

v3 : sons ronds et musicaux (marimba, bulles, cloches FM, voix à formants),
notes accordées sur une gamme pentatonique, stéréo, réverbération douce
et volume homogène d'un son à l'autre.

Usage : python3 synth_cartoon.py [dossier_sortie]
Sortie : un .ogg stéréo par son + manifest.json.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from scipy import signal

SR = 44100
RNG = np.random.default_rng(11)

# Gamme de do majeur pentatonique : tout ce qui est « musical » tombe juste
# et s'accorde avec les autres sons du jeu.
PENTA = [261.63, 293.66, 329.63, 392.00, 440.00]


def note(degre, octave=0):
    """Degré dans la gamme pentatonique (peut dépasser 4) + décalage d'octave."""
    o, d = divmod(degre, 5)
    return PENTA[d] * 2 ** (o + octave)


# ---------------------------------------------------------------- briques

def n_of(dur):
    return int(round(dur * SR))


def t_axis(dur):
    return np.arange(n_of(dur)) / SR


def env_exp(n, decay):
    return np.exp(-np.arange(n) / SR / decay)


def env_ar(n, a=0.005, r=0.1, curve=2.0):
    """Attaque linéaire puis relâche courbe, sur toute la durée."""
    a = max(int(a * SR), 1)
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    rn = min(int(r * SR), n - a)
    if rn > 0:
        e[n - rn:] *= np.linspace(1, 0, rn) ** curve
    return e


def osc(freq, kind="sine", phase0=0.0):
    freq = np.atleast_1d(np.asarray(freq, dtype=float))
    ph = 2 * np.pi * np.cumsum(freq) / SR + phase0
    if kind == "sine":
        return np.sin(ph)
    if kind == "tri":
        return 2 / np.pi * np.arcsin(np.sin(ph))
    if kind == "soft_square":
        return np.tanh(2.5 * np.sin(ph)) / np.tanh(2.5)
    raise ValueError(kind)


def harmonic_voice(freq, n_harm=24, tilt=1.35):
    """Source « gorge » : somme d'harmoniques à pente douce (plus rond qu'une dent de scie)."""
    freq = np.atleast_1d(np.asarray(freq, dtype=float))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    out = np.zeros_like(ph)
    for k in range(1, n_harm + 1):
        band_ok = (freq * k) < SR * 0.45  # pas de repliement
        out += band_ok * np.sin(k * ph) / k ** tilt
    return out


def glide(f0, f1, dur_or_n, curve=1.0):
    n = dur_or_n if isinstance(dur_or_n, int) else n_of(dur_or_n)
    x = np.linspace(0, 1, n) ** curve
    return f0 * (f1 / f0) ** x


def white(n):
    return RNG.standard_normal(n) * 0.3


def pink(n):
    """Bruit rose (plus doux à l'oreille que le blanc)."""
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    return signal.lfilter(b, a, RNG.standard_normal(n)) * 0.6


def lp(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, fc, order=2):
    sos = signal.butter(order, fc, "high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def sweep_lp(x, f_start, f_end, steps=64):
    """Passe-bas dont la fréquence glisse (par blocs, avec état conservé)."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), steps + 1).astype(int)
    freqs = glide(f_start, f_end, steps)
    zi = None
    for i in range(steps):
        sos = signal.butter(2, min(freqs[i], SR * 0.45), "low", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[edges[i]:edges[i + 1]], zi = signal.sosfilt(sos, x[edges[i]:edges[i + 1]], zi=zi)
    return out


def formants(src, f_track, bw=(90, 110, 160), gains=(1.0, 0.6, 0.25), steps=48):
    """Filtre de voyelle : 3 résonances qui suivent f_track (tableau steps x 3)."""
    out = np.zeros_like(src)
    edges = np.linspace(0, len(src), steps + 1).astype(int)
    for j in range(3):
        zi = None
        for i in range(steps):
            fc = f_track[i][j]
            lo, hi = max(fc - bw[j] * 2, 40), fc + bw[j] * 2
            sos = signal.butter(2, [lo, hi], "band", fs=SR, output="sos")
            if zi is None:
                zi = np.zeros((sos.shape[0], 2))
            seg, zi = signal.sosfilt(sos, src[edges[i]:edges[i + 1]], zi=zi)
            out[edges[i]:edges[i + 1]] += seg * gains[j]
    return out


def vowel_track(points, steps=48):
    """points = [(position 0..1, (F1, F2, F3)), ...] → trajectoire interpolée."""
    pos = np.array([p for p, _ in points])
    vals = np.array([v for _, v in points], dtype=float)
    xs = np.linspace(0, 1, steps)
    return np.stack([np.interp(xs, pos, vals[:, j]) for j in range(3)], axis=1)


A = (750, 1200, 2600)
O = (450, 800, 2600)
U = (330, 700, 2400)
E = (500, 1700, 2500)
I = (300, 2200, 3000)
RR = (400, 1100, 1700)  # « r » roulé


def fit(x, n):
    return np.pad(x, (0, max(n - len(x), 0)))[:n]


def place(dst, src, at, gain=1.0):
    i = int(at * SR)
    end = min(len(dst), i + len(src))
    if end > i:
        dst[i:end] += src[: end - i] * gain


def soft_clip(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


# ---------------------------------------------------------------- instruments

def marimba(f, dur=0.5, bright=1.0):
    """Lame de marimba / xylophone : partiels 1, 3.93, 9.2 qui s'éteignent vite."""
    n = n_of(dur)
    x = osc(np.full(n, f)) * env_exp(n, dur / 3.5)
    x += 0.35 * bright * osc(np.full(n, f * 3.93)) * env_exp(n, dur / 10)
    x += 0.12 * bright * osc(np.full(n, f * 9.2)) * env_exp(n, dur / 25)
    return x * env_ar(n, 0.001, 0.02)


def woodblock(f=900, dur=0.12):
    n = n_of(dur)
    x = osc(np.full(n, f)) * env_exp(n, 0.025) + 0.5 * osc(np.full(n, f * 2.4)) * env_exp(n, 0.012)
    x += bp(white(n), f, min(f * 3, 7000)) * env_exp(n, 0.004) * 0.9
    return x * env_ar(n, 0.0005, 0.01)


def bell(f, dur=1.0, index=2.0, ratio=3.5):
    """Cloche FM : clair et « magique »."""
    n = n_of(dur)
    t = np.arange(n) / SR
    mod = index * env_exp(n, dur / 4) * np.sin(2 * np.pi * f * ratio * t)
    x = np.sin(2 * np.pi * f * t + mod) * env_exp(n, dur / 3)
    return x * env_ar(n, 0.002, 0.05)


def bubble(f=600, dur=0.12, rise=2.2):
    """« Bloup » : sinus dont la hauteur monte très vite (modèle de bulle)."""
    n = n_of(dur)
    x = osc(glide(f, f * rise, n, 0.5)) * env_exp(n, dur / 3.5)
    return x * env_ar(n, 0.001, 0.01)


def pop(f=500, dur=0.09):
    """Pop rond : bulle + petit clic de surface."""
    n = n_of(dur)
    x = bubble(f, dur, 2.6)
    x += fit(lp(hp(white(n_of(0.004)), 1500), 6000) * 0.6, n)
    return x


def boing(f=160, dur=0.6, depth=0.45, rate=13):
    """Ressort : la hauteur oscille et se calme."""
    t = t_axis(dur)
    p = f * (1 + depth * np.exp(-t * 5) * np.sin(2 * np.pi * rate * t))
    x = osc(p, "tri") * 0.8 + 0.3 * osc(p * 2)
    return x * env_exp(len(t), dur / 2.5) * env_ar(len(t), 0.002, 0.05)


def slide_whistle(f0, f1, dur=0.4, vib=0.015):
    t = t_axis(dur)
    p = glide(f0, f1, len(t), 0.8) * (1 + vib * np.sin(2 * np.pi * 6 * t))
    x = osc(p) + 0.08 * osc(p * 2)
    breath = bp(white(len(t)), 1500, 5000) * 0.15
    return (x + breath) * env_ar(len(t), 0.03, 0.08)


def voice(dur, pitch, vowels, roll=0.0, breath=0.12, sub=0.35, grit=0.0):
    """Voix cartoon : source harmonique + voyelles + « r » roulé optionnel."""
    n = n_of(dur)
    t = np.arange(n) / SR
    pitch = np.asarray(pitch, dtype=float)
    src = harmonic_voice(pitch, 28, 1.25)
    if roll:  # roulement « rrr » : modulation d'amplitude rapide
        src *= 1 - roll * 0.5 * (1 + np.sin(2 * np.pi * 26 * t))
    if grit:
        src = soft_clip(src * (1 + grit), 1 + grit * 2)
    x = formants(src, vowel_track(vowels))
    x += breath * formants(white(n), vowel_track(vowels))
    x += sub * osc(pitch / 2) * 0.5  # du poids dans le grave
    return x


# ---------------------------------------------------------------- finition

def stereo_reverb(x, size=1.2, mix=0.18, damp=3500, predelay=0.012):
    """Réverbération stéréo douce (réponse de bruit rose qui décroît, assombrie)."""
    x = x * env_ar(len(x), 0.0, 0.012)  # fin douce : pas de clic avant la queue de réverb
    n = n_of(size)
    out = []
    for seed in (0, 1):
        r = np.random.default_rng(100 + seed)
        ir = lp(r.standard_normal(n), damp) * env_exp(n, size / 6.5)
        ir = np.concatenate([np.zeros(n_of(predelay)), ir])
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        out.append(signal.fftconvolve(x, ir)[: len(x) + len(ir)])
    L = len(out[0])
    dry = fit(x, L)
    return np.stack([dry + mix * out[0], dry + mix * out[1]], axis=1)


def widen(x_st, ms=0.006):
    """Léger décalage gauche/droite pour plus de largeur."""
    d = n_of(ms)
    r = np.concatenate([np.zeros(d), x_st[:, 1]])[: len(x_st)]
    return np.stack([x_st[:, 0], 0.7 * x_st[:, 1] + 0.3 * r], axis=1)


def pan(x, p):
    """p de -1 (gauche) à 1 (droite)."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def master(x, rms_db=-17.0, peak=0.89, boucle=False):
    """Coupe le très grave, adoucit, met tous les sons au même volume ressenti."""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    x = np.stack([lp(hp(x[:, c], 35 if boucle else 70), 11000) for c in range(2)], axis=1)
    if not boucle:
        nz = np.where(np.max(np.abs(x), axis=1) > 1e-4 * np.max(np.abs(x)))[0]
        x = x[: nz[-1] + 1 + n_of(0.02)] if len(nz) else x
        f = min(n_of(0.015), len(x))
        x[-f:] *= np.linspace(1, 0, f)[:, None]
        x[: n_of(0.001)] *= np.linspace(0, 1, n_of(0.001))[:, None]
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    x = x * (10 ** (rms_db / 20) / rms)
    x = soft_clip(x / peak, 1.2) * peak  # limiteur doux
    m = np.max(np.abs(x))
    return x * (peak / m) if m > peak else x


def make_loop(x, xfade=0.8):
    """Boucle sans coupure (fondu enchaîné fin → début), mono ou stéréo."""
    n = n_of(xfade)
    ramp = np.linspace(0, 1, n)
    if x.ndim == 2:
        ramp = ramp[:, None]
    return np.concatenate([x[-n:] * (1 - ramp) + x[:n] * ramp, x[n:-n]])


# ---------------------------------------------------------------- sons du jeu

def rawr(dur=1.0, top=210, low=110, grit=0.4, cute=0.0):
    """« RRRAWRRR » : r roulé, voyelle A, fin en O/R, hauteur qui monte puis retombe."""
    n = n_of(dur)
    t = np.arange(n) / SR
    k = n // 4
    pitch = np.concatenate([glide(low * 1.1, top, k, 0.7), glide(top, low, n - k, 1.4)])
    pitch *= 1 + 0.03 * np.sin(2 * np.pi * 6.5 * t) * np.clip(t / 0.2, 0, 1)
    vowels = [(0, RR), (0.12, A), (0.6, A), (0.85, O), (1, RR)]
    x = voice(dur, pitch * (1 + cute), vowels, roll=0.55, breath=0.15, sub=0.15, grit=grit)
    x *= env_ar(n, 0.05, dur * 0.4, 1.5)
    return stereo_reverb(x, 1.0, 0.16)


def grr(dur=1.1, f=85):
    """Grognement « hmmmrrr » bouche fermée."""
    n = n_of(dur)
    t = np.arange(n) / SR
    pitch = f * (1 + 0.05 * np.sin(2 * np.pi * 1.3 * t))
    x = voice(dur, pitch, [(0, O), (0.5, A), (1, RR)], roll=0.7, breath=0.06, sub=0.12)
    return stereo_reverb(x * env_ar(n, 0.12, 0.35), 0.8, 0.12)


def hyah(dur=0.35, f=330):
    """Cri d'attaque « hya ! » qui monte."""
    n = n_of(dur)
    pitch = glide(f, f * 1.9, n, 0.6)
    x = voice(dur, pitch, [(0, E), (0.3, A), (1, A)], breath=0.2, sub=0.15, grit=0.2)
    return stereo_reverb(x * env_ar(n, 0.01, 0.12), 0.8, 0.15)


def whistle_attack():
    """Sifflet à coulisse qui monte « fwiiiip ! »."""
    return stereo_reverb(slide_whistle(500, 1600, 0.35), 0.8, 0.15)


def hiss(dur=0.7, tone=True):
    """« Pssshh » doux : bruit filtré + petite note glissante."""
    n = n_of(dur)
    x = lp(bp(pink(n), 1500, 6000), 5000) * 1.4 * env_ar(n, 0.04, dur * 0.6, 1.5)
    if tone:
        x += 0.25 * osc(glide(1400, 900, n)) * env_ar(n, 0.02, dur * 0.7)
    return stereo_reverb(x, 0.6, 0.12)


def flaps(beats=3, gap=0.24, f=180):
    out = np.zeros(n_of(beats * gap + 0.4))
    for i in range(beats):
        n = n_of(0.2)
        whoosh = hp(sweep_lp(pink(n), 3000, 500), 250) * env_ar(n, 0.03, 0.12) * 1.8
        thump = osc(glide(f * 2 * (1 + 0.15 * i), f * 1.2, n)) * env_exp(n, 0.04) * 0.25
        place(out, whoosh + thump, i * gap)
    return stereo_reverb(out, 0.7, 0.12)


def stomp(f=95, dur=0.55, bounce=0.0, marimba_note=None):
    """Pas cartoon « boum » : grave rond + petit choc + (option) note de marimba."""
    n = n_of(dur)
    t = np.arange(n) / SR
    p = glide(f * 1.8, f * 0.5, n, 0.35) * (1 + bounce * np.exp(-t * 8) * np.sin(2 * np.pi * 9 * t))
    x = osc(p) * env_exp(n, dur / 3.5) * 0.6
    x += osc(p * 2.0, "tri") * env_exp(n, dur / 5) * 0.5  # le « bwom » qu'on entend aussi sur téléphone
    x += bp(white(n), 150, 900) * env_exp(n, 0.02) * 1.5
    x += fit(woodblock(f * 3.2, 0.1), n) * 0.35
    if marimba_note:
        x += fit(marimba(marimba_note, 0.4), n) * 0.8
    return stereo_reverb(x, 0.8, 0.12)


def fwoom(dur=1.0, bright=4000, crackle=8):
    """Souffle de feu cartoon « FWOOOM » : grave qui gonfle + flamme filtrée + crépitements doux."""
    n = n_of(dur)
    flame = hp(sweep_lp(pink(n), 700, bright), 220) * 1.8
    flame *= env_ar(n, 0.08, dur * 0.55, 1.6)
    whump = osc(glide(110, 220, n, 0.5)) * env_ar(n, 0.06, dur * 0.6) * 0.2
    x = flame + whump
    for _ in range(crackle):
        place(x, bubble(RNG.choice([note(d, 1) for d in range(5)]), 0.05, 1.8), RNG.uniform(0.1, dur * 0.8), 0.18)
    return widen(stereo_reverb(x, 1.0, 0.15))


def fireball():
    out = np.zeros(n_of(0.7))
    n = n_of(0.22)
    swish = sweep_lp(pink(n), 800, 6000) * env_ar(n, 0.15, 0.05) * 1.3
    place(out, swish, 0)
    place(out, osc(glide(300, 900, n)) * env_ar(n, 0.15, 0.04) * 0.25, 0)
    place(out, pop(220, 0.16) * 1.1, 0.2)
    place(out, bubble(note(2, 1), 0.08, 2) * 0.3, 0.24)
    return stereo_reverb(out, 0.8, 0.15)


def fwip():
    n = n_of(0.25)
    x = sweep_lp(pink(n), 700, 7000) * env_ar(n, 0.12, 0.08) * 1.2
    x += osc(glide(400, 1300, n, 0.7)) * env_ar(n, 0.1, 0.08) * 0.35
    return stereo_reverb(x, 0.6, 0.12)


def brasero_loop(dur=10.0):
    """Feu de camp cartoon : souffle chaud + petits « pops » doux, accordés."""
    n = n_of(dur)
    t = np.arange(n) / SR
    base = lp(pink(n), 450) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * t)) * 1.2
    x = np.stack([base, lp(pink(n), 450) * 1.2], axis=1)
    for _ in range(int(dur * 7)):
        f = RNG.uniform(900, 2400)
        s = woodblock(f, 0.03) * RNG.uniform(0.05, 0.2)
        place(x, pan(s, RNG.uniform(-0.6, 0.6)), RNG.uniform(0, dur - 0.05))
    for _ in range(int(dur * 1.5)):
        s = bubble(RNG.choice([note(d) for d in range(5)]), 0.07, 1.6) * RNG.uniform(0.15, 0.3)
        place(x, pan(s, RNG.uniform(-0.5, 0.5)), RNG.uniform(0, dur - 0.1))
    return make_loop(x, 1.0)


def crack(hits=2, base=1300):
    """Craquement cartoon : clacs de bois secs, chaque coup un peu plus aigu."""
    out = np.zeros(n_of(0.15 * hits + 0.3))
    for i in range(hits):
        place(out, woodblock(base * (1 + 0.18 * i), 0.1), i * 0.07)
        place(out, bp(white(n_of(0.012)), 2000, 6500) * env_exp(n_of(0.012), 0.003) * 0.8, i * 0.07)
    return stereo_reverb(out, 0.6, 0.12)


def skeleton_xylo(run=(7, 6, 8, 5, 9, 7, 10), gap=0.065):
    """Squelette au xylophone : petite course de notes + cliquetis de bois."""
    out = np.zeros(n_of(len(run) * gap + 0.6))
    for i, d in enumerate(run):
        place(out, marimba(note(d), 0.35, 1.3), i * gap + RNG.uniform(0, 0.008), 0.7)
        place(out, woodblock(RNG.uniform(1800, 2600), 0.04), i * gap + 0.01, 0.15)
    return stereo_reverb(out, 0.9, 0.18)


def bonk(f=260, dur=0.4):
    """« Bonk ! » : bloc de bois grave + petit rebond de hauteur."""
    n = n_of(dur)
    x = osc(glide(f * 1.6, f, n, 0.15)) * env_exp(n, 0.07)
    x += fit(woodblock(f * 2.5, 0.1), n) * 0.6
    x += fit(boing(f * 0.75, 0.3, 0.25, 16), n) * 0.35
    return stereo_reverb(x, 0.6, 0.12)


def egg_ticks(count=3, base=note(5, 1), gap=0.18):
    """Fissure : petits « tic » cristallins qui montent (on sent que ça va éclore)."""
    out = np.zeros(n_of(count * gap + 0.4))
    for i in range(count):
        f = note(i * 2 + 5, 1)
        place(out, woodblock(f, 0.06), i * gap, 0.7)
        place(out, bell(f * 2, 0.25, 1.0, 2.0), i * gap, 0.12)
    return stereo_reverb(out, 0.7, 0.15)


def hatch_tada():
    """Éclosion : crac + POP + arpège de cloches qui monte (« ta-daa »)."""
    out = np.zeros(n_of(1.6))
    place(out, crack(2, 1500)[:, 0], 0, 0.7)
    place(out, pop(420, 0.14), 0.13, 1.1)
    for i, d in enumerate([0, 2, 4, 5, 7]):
        place(out, bell(note(d, 1), 0.9, 1.5, 2.0), 0.2 + i * 0.06, 0.32)
    return widen(stereo_reverb(out, 1.3, 0.2))


def hatch_boing():
    """Éclosion : POP + boing + ding."""
    out = np.zeros(n_of(1.3))
    place(out, pop(380, 0.13), 0, 1.0)
    place(out, boing(230, 0.55, 0.35, 12), 0.08, 0.6)
    place(out, bell(note(7, 1), 1.0, 1.2, 2.0), 0.35, 0.35)
    return stereo_reverb(out, 1.0, 0.18)


def baby_mew():
    """Bébé dragon : deux petits « miii-ou » à la voix aiguë."""
    out = np.zeros(n_of(0.9))
    for start, f, dur in ((0, 520, 0.25), (0.3, 600, 0.32)):
        n = n_of(dur)
        p = np.concatenate([glide(f, f * 1.35, n // 3), glide(f * 1.35, f * 1.05, n - n // 3)])
        p *= 1 + 0.025 * np.sin(2 * np.pi * 9 * np.arange(n) / SR)
        v = voice(dur, p, [(0, I), (0.5, E), (1, U)], breath=0.08, sub=0.0)
        place(out, v * env_ar(n, 0.015, 0.08), start)
    return stereo_reverb(out, 0.8, 0.15)


def baby_rawr():
    return rawr(0.55, 560, 380, grit=0.0, cute=0.0)


def lair_loop(dur=12.0):
    """Repaire : nappe douce (accord grave qui respire) + gouttes accordées."""
    n = n_of(dur)
    t = np.arange(n) / SR
    pad = np.zeros(n)
    for f, ph in ((note(0, -1), 0), (note(3, -1), 1.3), (note(0, 0), 2.1), (note(2, 0), 0.7)):
        for det in (-0.6, 0.6):
            pad += osc(np.full(n, f + det), "tri", ph) * 0.18
    pad = lp(pad, 1200) * (0.75 + 0.25 * np.sin(2 * np.pi * t / dur * 2))
    x = np.stack([pad, np.roll(pad, n_of(0.011))], axis=1)
    x = x + 0.25 * np.stack([lp(pink(n), 250)] * 2, axis=1)
    for _ in range(int(dur * 0.5)):
        s = bubble(RNG.choice([note(d, 1) for d in range(5)]), 0.12, 1.5) * 0.3
        place(x, pan(s, RNG.uniform(-0.8, 0.8)), RNG.uniform(0, dur - 0.3))
    wet = np.stack([stereo_reverb(x[:, c], 2.0, 0.35)[:n, c] for c in range(2)], axis=1)
    return make_loop(wet, 1.5)


def drips_loop(dur=8.0):
    """Gouttes « plip » accordées, réparties à gauche et à droite."""
    n = n_of(dur)
    x = np.zeros((n, 2))
    for _ in range(int(dur * 1.8)):
        s = bubble(RNG.choice([note(d, 1) for d in range(5)]), 0.1, 1.7) * RNG.uniform(0.4, 0.9)
        place(x, pan(s, RNG.uniform(-0.9, 0.9)), RNG.uniform(0, dur - 0.2))
    wet = np.stack([stereo_reverb(x[:, c], 1.6, 0.45)[:n, c] for c in range(2)], axis=1)
    return make_loop(wet, 0.5)


def wind_loop(dur=12.0, whistle=True):
    n = n_of(dur)
    t = np.arange(n) / SR
    chans = []
    for c in range(2):
        x = pink(n)
        lfo = 600 + 350 * np.sin(2 * np.pi * (0.09 + 0.02 * c) * t) + 150 * np.sin(2 * np.pi * 0.23 * t)
        # passe-bande glissant, appliqué par blocs
        out = np.zeros(n)
        edges = np.linspace(0, n, 121).astype(int)
        zi = None
        for i in range(120):
            fc = lfo[edges[i]]
            sos = signal.butter(2, [fc * 0.6, fc * 1.6], "band", fs=SR, output="sos")
            if zi is None:
                zi = np.zeros((sos.shape[0], 2))
            out[edges[i]:edges[i + 1]], zi = signal.sosfilt(sos, x[edges[i]:edges[i + 1]], zi=zi)
        out *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t + c)
        if whistle:
            out += 0.05 * osc(note(4, 1) * (1 + 0.03 * np.sin(2 * np.pi * 0.17 * t + c))) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
        chans.append(out)
    return make_loop(np.stack(chans, axis=1), 1.5)


def fly_by(dur=1.3):
    """Dragon qui passe : souffle qui arrive de gauche et part à droite + battement."""
    n = n_of(dur)
    t = np.arange(n) / SR
    shape = np.exp(-((t - dur * 0.45) / (dur * 0.22)) ** 2)
    x = hp(sweep_lp(pink(n), 900, 4000), 250) * shape * 1.8
    x += osc(glide(260, 170, n)) * shape * 0.25  # petit effet Doppler
    p = np.linspace(-0.9, 0.9, n)
    st = np.stack([x * np.cos((p + 1) * np.pi / 4), x * np.sin((p + 1) * np.pi / 4)], axis=1) * np.sqrt(2)
    place(st, pan(flaps(1)[:, 0], 0) * 0.5, dur * 0.42)
    return st


def click_pop():
    return stereo_reverb(pop(650, 0.06), 0.3, 0.06)


def click_wood():
    return stereo_reverb(woodblock(note(4, 2), 0.06), 0.3, 0.06)


def coin(d1=8, d2=11):
    """Pièce : deux notes de cloche qui montent (« bling ! »)."""
    out = np.zeros(n_of(0.7))
    place(out, bell(note(d1, 1), 0.12, 1.2, 1.0), 0, 0.6)
    place(out, bell(note(d2, 1), 0.6, 1.4, 1.0), 0.07, 0.8)
    return stereo_reverb(out, 0.7, 0.15)


def coin_sparkle():
    out = np.zeros(n_of(1.0))
    place(out, coin(6, 9)[:, 0], 0)
    for i, d in enumerate([12, 14, 16]):
        place(out, bell(note(d, 1), 0.35, 0.8, 2.0), 0.14 + i * 0.045, 0.15)
    return widen(stereo_reverb(out, 0.9, 0.18))


# ---------------------------------------------------------------- catalogue

SONS = [
    # (catégorie, besoin, fichier, description, fonction, boucle)
    ("Dragons", "RugissementPuissant", "rawr_gros", "« RRRAWR » grave avec r roulé", lambda: rawr(1.1, 190, 95, 0.45), False),
    ("Dragons", "RugissementPuissant", "rawr_vif", "« RAWR ! » plus court et plus vif", lambda: rawr(0.75, 280, 150, 0.3), False),
    ("Dragons", "GrognementCalme", "hmmrrr", "« Hmmmrrr » bouche fermée", lambda: grr(1.1, 85), False),
    ("Dragons", "GrognementCalme", "hmmrrr_court", "Petit « mrrr » méfiant", lambda: grr(0.6, 110), False),
    ("Dragons", "CriAttaque", "hya", "Cri « hya ! » qui monte", lambda: hyah(0.35, 330), False),
    ("Dragons", "CriAttaque", "sifflet_monte", "Sifflet à coulisse « fwiiip ! »", whistle_attack, False),
    ("Dragons", "Sifflement", "psshh", "« Pssshh » doux avec une note qui descend", lambda: hiss(0.7, True), False),
    ("Dragons", "Sifflement", "psshh_court", "« Tss » court, sans note", lambda: hiss(0.4, False), False),
    ("Dragons", "BattementAiles", "ailes_3", "3 battements « fwoump »", lambda: flaps(3, 0.24), False),
    ("Dragons", "BattementAiles", "ailes_2", "2 battements lents et graves", lambda: flaps(2, 0.36, 140), False),
    ("Dragons", "PasLourds", "boum", "Pas « boum » rond", lambda: stomp(150), False),
    ("Dragons", "PasLourds", "boum_marimba", "Pas « boum » + note de marimba (très cartoon)", lambda: stomp(150, 0.55, 0.1, note(0)), False),
    ("Feu", "SouffleDeFeu", "fwooom", "« FWOOOM » qui gonfle", lambda: fwoom(1.0), False),
    ("Feu", "SouffleDeFeu", "fwoom_court", "« Fwoom » court et vif", lambda: fwoom(0.55, 5500, 4), False),
    ("Feu", "BouleDeFeu", "fwip_pouf", "« Fwip » puis « pouf »", fireball, False),
    ("Feu", "BouleDeFeu", "fwip", "« Fwip » seul", fwip, False),
    ("Feu", "Brasero", "brasero_boucle", "Feu de camp doux qui crépite (boucle)", lambda: brasero_loop(10), True),
    ("Os", "Craquement", "clac_clac", "« Clac-clac » de bois sec", lambda: crack(2), False),
    ("Os", "Craquement", "clac", "Un seul « clac »", lambda: crack(1, 1100), False),
    ("Os", "Cliquetis", "squelette_xylo", "Squelette au xylophone", skeleton_xylo, False),
    ("Os", "Cliquetis", "squelette_xylo_descend", "Squelette au xylophone, qui descend", lambda: skeleton_xylo((12, 10, 11, 8, 9, 6, 5)), False),
    ("Os", "ImpactPierre", "bonk", "« Bonk ! » qui rebondit", lambda: bonk(260), False),
    ("Os", "ImpactPierre", "bonk_grave", "« Bonk » grave", lambda: bonk(150, 0.5), False),
    ("Oeufs", "Fissure", "tic_tic_tic", "3 « tic » cristallins qui montent", lambda: egg_ticks(3), False),
    ("Oeufs", "Fissure", "tic", "Un seul « tic »", lambda: egg_ticks(1), False),
    ("Oeufs", "CoqueQuiCasse", "eclosion_tada", "Crac + POP + « ta-daa » de clochettes", hatch_tada, False),
    ("Oeufs", "CoqueQuiCasse", "eclosion_boing", "POP + boing + ding", hatch_boing, False),
    ("Oeufs", "CriBebeDragon", "bebe_miou", "Deux petits « miii-ou »", baby_mew, False),
    ("Oeufs", "CriBebeDragon", "bebe_rawr", "Mini « rawr » de bébé", baby_rawr, False),
    ("Ambiance", "Repaire", "repaire_boucle", "Nappe douce + gouttes accordées (boucle)", lambda: lair_loop(12), True),
    ("Ambiance", "GouttesCaverne", "gouttes_boucle", "« Plip » de gouttes à gauche et à droite (boucle)", lambda: drips_loop(8), True),
    ("Ambiance", "VentMontagne", "vent_boucle", "Vent doux qui chante un peu (boucle)", lambda: wind_loop(12, True), True),
    ("Ambiance", "VentMontagne", "vent_doux_boucle", "Vent doux seul (boucle)", lambda: wind_loop(12, False), True),
    ("Ambiance", "DragonQuiPasse", "passage", "Souffle qui passe de gauche à droite", fly_by, False),
    ("Interface", "Clic", "clic_bulle", "Clic « bloup » rond", click_pop, False),
    ("Interface", "Clic", "clic_bois", "Clic « toc » de bois", click_wood, False),
    ("Interface", "Pieces", "piece_bling", "Pièce « bling » (deux notes)", lambda: coin(8, 11), False),
    ("Interface", "Pieces", "piece_etincelles", "Pièce + petites étincelles", coin_sparkle, False),
]

# Volume ressenti visé (dB RMS) : les boucles restent discrètes.
VOLUME = {"boucle": -24.0, "court": -16.0}


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main(out_dir, seulement=None):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for cat, besoin, fichier, desc, fn, boucle in SONS:
        if seulement and fichier not in seulement:
            continue
        x = master(fn(), VOLUME["boucle" if boucle else "court"], boucle=boucle)
        wav = os.path.join(out_dir, fichier + ".wav")
        ogg = os.path.join(out_dir, fichier + ".ogg")
        write_wav(wav, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "5", ogg], check=True)
        os.remove(wav)
        manifest.append({"categorie": cat, "besoin": besoin, "fichier": fichier + ".ogg", "description": desc,
                         "duree": round(len(x) / SR, 2), "boucle": boucle})
        print(f"{fichier:24s} {len(x) / SR:5.2f}s")
    if not seulement:
        with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "sons-cartoon")
    main(dossier, set(sys.argv[2:]) or None)
