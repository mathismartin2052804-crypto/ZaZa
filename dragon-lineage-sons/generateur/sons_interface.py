"""Sons d'interface de Dragon Lineage (tour 1 : catégorie par catégorie).

Courts, nets et « satisfaisants » : attaque très rapide, hauteur qui bouge un peu,
presque pas de réverbération, notes accordées sur la même gamme que le reste du jeu.

Usage : python3 sons_interface.py [dossier_sortie]
Sortie : un .ogg par son (à importer dans Roblox) + apercu/*.ogg (démo en série
pour le défilement et le survol) + manifest.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from synth_cartoon import (  # noqa: E402
    SR, RNG, bell, bp, bubble, env_ar, env_exp, fit, glide, hp, lp, marimba, n_of, note, osc, pink,
    place, soft_clip, stereo_reverb, sweep_lp, white, woodblock, write_wav,
)
import subprocess  # noqa: E402


# ---------------------------------------------------------------- briques d'interface

def tick(f=3000, dur=0.025, body=0.0):
    """Petit clic net : impulsion filtrée + (option) un peu de corps tonal."""
    n = n_of(dur)
    x = bp(white(n), f * 0.6, min(f * 1.8, 16000)) * env_exp(n, dur / 6) * 1.5
    if body:
        x += osc(np.full(n, f / 4)) * env_exp(n, dur / 3) * body
    return x * env_ar(n, 0.0003, 0.004)


def pluck(f, dur=0.18, bright=2.0):
    """Note pincée (FM) : courte, ronde, qui s'éteint vite."""
    n = n_of(dur)
    t = np.arange(n) / SR
    idx = bright * env_exp(n, dur / 8)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 2 * t)) * env_exp(n, dur / 4)
    return x * env_ar(n, 0.001, 0.02)


def thock(f=420):
    """« Thock » de clavier mécanique doux : corps grave + petit clic plastique."""
    n = n_of(0.07)
    x = osc(glide(f * 1.3, f, n, 0.2)) * env_exp(n, 0.012) * 0.9
    x += bp(white(n), 1200, 5000) * env_exp(n, 0.003) * 0.9
    x += osc(np.full(n, f * 2.7)) * env_exp(n, 0.006) * 0.3
    return x * env_ar(n, 0.0003, 0.008)


def swish(dur, f0, f1, gain=1.0):
    """Petit souffle « fwip » filtré qui glisse de f0 à f1."""
    n = n_of(dur)
    x = hp(sweep_lp(pink(n), f0, f1), 300) * env_ar(n, dur * 0.25, dur * 0.5) * gain
    return x


def finish(x, room=0.25, mix=0.07):
    x = np.concatenate([x, np.zeros(n_of(0.02))])  # marge : le fondu final ne touche pas au son
    return stereo_reverb(x, room, mix, damp=6000, predelay=0.004)


def seq(parts, total):
    """parts = [(son_mono, début_en_s, gain), ...]."""
    out = np.zeros(n_of(total))
    for s, at, g in parts:
        place(out, s, at, g)
    return out


# ---------------------------------------------------------------- les sons

def clic_bulle():
    return finish(seq([(bubble(520, 0.07, 2.4), 0, 1), (tick(4000, 0.01), 0, 0.25)], 0.1))


def clic_thock():
    return finish(thock(400))


def clic_pluck():
    return finish(seq([(pluck(note(4, 1), 0.14, 1.5), 0, 1), (tick(5000, 0.008), 0, 0.2)], 0.16))


def clic_verre():
    return finish(seq([(bell(note(2, 2), 0.12, 0.8, 3.0), 0, 0.8), (tick(6000, 0.006), 0, 0.3)], 0.14), 0.3, 0.09)


def survol_tick():
    return finish(tick(5500, 0.012, 0.0) * 0.8 + fit(osc(np.full(n_of(0.012), note(4, 3))) * env_exp(n_of(0.012), 0.004) * 0.3, n_of(0.012)))


def survol_bulle():
    return finish(bubble(note(3, 2), 0.04, 1.5) * 0.7)


def survol_souffle():
    return finish(swish(0.06, 2500, 7000, 0.7))


def scroll_bois():
    return finish(woodblock(note(4, 2), 0.035) * 0.9, 0.15, 0.05)


def scroll_plastique():
    return finish(tick(3500, 0.012, 0.5), 0.15, 0.05)


def scroll_cran():
    """Cran de molette : deux micro-clics très rapprochés."""
    return finish(seq([(tick(2800, 0.008, 0.3), 0, 1), (tick(4200, 0.006), 0.009, 0.6)], 0.03), 0.15, 0.05)


def ouvrir_bulles():
    return finish(seq([(bubble(note(2, 1), 0.06, 1.8), 0, 0.8), (bubble(note(4, 1), 0.07, 1.8), 0.06, 1.0),
                       (pluck(note(7, 1), 0.2, 1.0), 0.06, 0.25)], 0.3))


def ouvrir_fwip():
    return finish(seq([(tick(4000, 0.008), 0, 0.3), (swish(0.1, 900, 6000), 0, 1), (pluck(note(5, 1), 0.15, 1.2), 0.05, 0.6)], 0.22))


def ouvrir_pop():
    return finish(seq([(swish(0.05, 1200, 5000, 0.6), 0, 1), (bubble(440, 0.09, 2.6), 0.025, 1.0)], 0.14))


def fermer_bulles():
    return finish(seq([(bubble(note(4, 1), 0.06, 0.6), 0, 0.9), (bubble(note(2, 1), 0.07, 0.6), 0.06, 0.8)], 0.16))


def fermer_fwip():
    return finish(seq([(tick(3500, 0.008), 0, 0.3), (swish(0.09, 6000, 800), 0, 1), (pluck(note(2, 1), 0.12, 1.0), 0.05, 0.45)], 0.2))


def fermer_pop():
    """Le menu se « rentre » : petite aspiration puis clic."""
    return finish(seq([(swish(0.035, 4000, 1200, 0.6), 0, 1), (thock(330), 0.022, 0.9)], 0.11))


def onglet_page():
    """Changer d'onglet : petit « tchk » de carte."""
    return finish(seq([(tick(3000, 0.012, 0.4), 0, 1), (swish(0.04, 2500, 8000, 0.6), 0.004, 1)], 0.06))


def onglet_double():
    return finish(seq([(pluck(note(3, 1), 0.08, 1.2), 0, 0.7), (pluck(note(5, 1), 0.1, 1.2), 0.045, 0.8)], 0.16))


def activer_monte():
    return finish(seq([(thock(380), 0, 0.7), (pluck(note(2, 1), 0.08), 0.02, 0.5), (pluck(note(4, 1), 0.12), 0.07, 0.6)], 0.2))


def activer_bulle():
    return finish(seq([(bubble(note(2, 1), 0.05, 1.6), 0, 0.8), (bubble(note(5, 1), 0.07, 2.0), 0.05, 1.0)], 0.13))


def desactiver_descend():
    return finish(seq([(thock(360), 0, 0.7), (pluck(note(4, 1), 0.08), 0.02, 0.5), (pluck(note(1, 1), 0.12), 0.07, 0.55)], 0.2))


def desactiver_bulle():
    return finish(seq([(bubble(note(5, 1), 0.05, 0.7), 0, 0.8), (bubble(note(2, 1), 0.07, 0.6), 0.05, 0.9)], 0.13))


def valider_pluck():
    return finish(seq([(pluck(note(5, 1), 0.15), 0, 0.8), (pluck(note(7, 1), 0.25), 0.08, 0.9)], 0.35), 0.4, 0.1)


def valider_marimba():
    return finish(seq([(marimba(note(d, 1), 0.3), i * 0.05, 0.6) for i, d in enumerate((5, 7, 10))], 0.45), 0.45, 0.1)


def valider_ding():
    return finish(seq([(thock(420), 0, 0.5), (bell(note(9, 1), 0.6, 1.4, 2.0), 0.02, 0.8)], 0.65), 0.6, 0.12)


def erreur_bonk():
    """« Bonk-bonk » doux, grave : non, mais gentiment."""
    return finish(seq([(marimba(note(1, 0), 0.18, 0.8), 0, 0.9), (marimba(note(0, 0), 0.22, 0.8), 0.11, 0.9)], 0.38), 0.3, 0.08)


def erreur_descend():
    return finish(seq([(pluck(note(3, 0), 0.12, 2.5), 0, 0.8), (pluck(note(1, 0), 0.2, 2.5), 0.09, 0.8)], 0.32))


def erreur_nonnon():
    """« Nuh-uh » : deux petites notes carrées douces qui descendent."""
    out = []
    for f, at in ((note(2, 0), 0), (note(0, 0), 0.1)):
        n = n_of(0.08)
        out.append((lp(soft_clip(osc(np.full(n, f)) * 3, 2), 2500) * env_ar(n, 0.003, 0.03), at, 0.6))
    return finish(seq(out, 0.22))


def notif_cloche():
    return finish(seq([(bell(note(7, 1), 0.5, 1.2, 2.0), 0, 0.7), (bell(note(9, 1), 0.7, 1.2, 2.0), 0.11, 0.8)], 0.85), 0.6, 0.12)


def notif_bulles():
    return finish(seq([(bubble(note(d, 1), 0.08, 1.8), i * 0.07, 0.8) for i, d in enumerate((2, 4, 7))]
                      + [(pluck(note(9, 1), 0.3, 0.8), 0.2, 0.3)], 0.5), 0.4, 0.1)


def piece_bling():
    return finish(seq([(bell(note(8, 1), 0.08, 1.0, 1.0), 0, 0.6), (bell(note(11, 1), 0.45, 1.3, 1.0), 0.06, 0.8)], 0.55), 0.45, 0.1)


def piece_tintement():
    """Plusieurs pièces qui tombent : petits tintements rapides et aigus."""
    parts = [(bell(note(d, 2), 0.18, 0.7, 2.76), i * 0.045 + RNG.uniform(0, 0.01), 0.45 - i * 0.05)
             for i, d in enumerate((2, 4, 3, 5, 4))]
    return finish(seq(parts, 0.5), 0.35, 0.1)


# ---------------------------------------------------------------- catalogue

# (besoin, fichier, description, fonction, volume dB RMS, démo en série ?)
SONS = [
    ("Clic", "clic_bulle", "« Bloup » rond", clic_bulle, -16, None),
    ("Clic", "clic_thock", "« Thock » de clavier doux", clic_thock, -16, None),
    ("Clic", "clic_pluck", "Petite note pincée", clic_pluck, -17, None),
    ("Clic", "clic_verre", "« Tink » de verre", clic_verre, -18, None),
    ("Survol", "survol_tick", "Tick très léger", survol_tick, -26, (5, 0.11, 0.0)),
    ("Survol", "survol_bulle", "Micro-bulle", survol_bulle, -25, (5, 0.11, 0.0)),
    ("Survol", "survol_souffle", "Petit souffle « fft »", survol_souffle, -26, (5, 0.11, 0.0)),
    ("Defilement", "defil_bois", "Tick de bois", scroll_bois, -22, (10, 0.06, 0.02)),
    ("Defilement", "defil_plastique", "Clic plastique", scroll_plastique, -22, (10, 0.06, 0.02)),
    ("Defilement", "defil_cran", "Cran de molette (double clic)", scroll_cran, -22, (10, 0.06, 0.02)),
    ("OuvrirMenu", "ouvrir_bulles", "Deux bulles qui montent", ouvrir_bulles, -17, None),
    ("OuvrirMenu", "ouvrir_fwip", "« Fwip » + note", ouvrir_fwip, -18, None),
    ("OuvrirMenu", "ouvrir_pop", "Souffle + « pop »", ouvrir_pop, -17, None),
    ("FermerMenu", "fermer_bulles", "Deux bulles qui descendent", fermer_bulles, -18, None),
    ("FermerMenu", "fermer_fwip", "« Fwip » à l'envers", fermer_fwip, -19, None),
    ("FermerMenu", "fermer_pop", "Aspiration + clic", fermer_pop, -18, None),
    ("Onglet", "onglet_page", "« Tchk » de carte", onglet_page, -19, None),
    ("Onglet", "onglet_double", "Deux petites notes", onglet_double, -18, None),
    ("Activer", "activer_monte", "Clic + deux notes qui montent", activer_monte, -17, None),
    ("Activer", "activer_bulle", "Deux bulles qui montent", activer_bulle, -17, None),
    ("Desactiver", "desactiver_descend", "Clic + deux notes qui descendent", desactiver_descend, -17, None),
    ("Desactiver", "desactiver_bulle", "Deux bulles qui descendent", desactiver_bulle, -17, None),
    ("Valider", "valider_pluck", "Deux notes pincées « ti-ding »", valider_pluck, -17, None),
    ("Valider", "valider_marimba", "Accord de marimba qui monte", valider_marimba, -17, None),
    ("Valider", "valider_ding", "Clic + « ding » de clochette", valider_ding, -18, None),
    ("Erreur", "erreur_bonk", "« Bonk-bonk » doux", erreur_bonk, -17, None),
    ("Erreur", "erreur_descend", "Deux notes qui descendent", erreur_descend, -17, None),
    ("Erreur", "erreur_nonnon", "« Nuh-uh » rétro", erreur_nonnon, -19, None),
    ("Notification", "notif_cloche", "Deux clochettes", notif_cloche, -18, None),
    ("Notification", "notif_bulles", "Trois bulles + note", notif_bulles, -18, None),
    ("Pieces", "piece_bling", "« Bling » deux notes", piece_bling, -17, None),
    ("Pieces", "piece_tintement", "Pièces qui tintent", piece_tintement, -18, None),
]


def master_ui(x, rms_db):
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    x = np.stack([lp(hp(x[:, c], 90), 15000) for c in range(2)], axis=1)
    nz = np.where(np.max(np.abs(x), axis=1) > 3e-4 * np.max(np.abs(x)))[0]
    x = x[: nz[-1] + 1 + n_of(0.005)]
    f = min(n_of(0.006), len(x))
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    # volume mesuré sur la partie « active » du son (pas sur la queue)
    loud = np.sqrt(np.mean(x[: max(n_of(0.05), int(len(x) * 0.4))] ** 2)) + 1e-9
    x = x * (10 ** (rms_db / 20) / loud)
    m = np.max(np.abs(x))
    return x * (0.89 / m) if m > 0.89 else x


def demo(x, count, gap, rise):
    """Série pour l'aperçu (défilement, survol) avec une légère variation de hauteur."""
    out = np.zeros((n_of(count * gap + 0.3), 2))
    for i in range(count):
        speed = 1 + rise * (i % 5) + RNG.uniform(-0.015, 0.015)
        idx = np.arange(0, len(x), speed)
        y = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1)
        place(out, y, i * gap)
    return out


def to_ogg(path_no_ext, x):
    write_wav(path_no_ext + ".wav", x)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path_no_ext + ".wav", "-c:a", "libvorbis", "-q:a", "6",
                    path_no_ext + ".ogg"], check=True)
    os.remove(path_no_ext + ".wav")


def main(out_dir):
    os.makedirs(os.path.join(out_dir, "apercu"), exist_ok=True)
    manifest = []
    for besoin, fichier, desc, fn, vol, serie in SONS:
        x = master_ui(fn(), vol)
        to_ogg(os.path.join(out_dir, fichier), x)
        entry = {"categorie": "Interface", "besoin": besoin, "fichier": fichier + ".ogg", "description": desc,
                 "duree": round(len(x) / SR, 3), "boucle": False}
        if serie:
            to_ogg(os.path.join(out_dir, "apercu", fichier + "_serie"), demo(x, *serie))
            entry["apercu"] = "apercu/" + fichier + "_serie.ogg"
        manifest.append(entry)
        print(f"{fichier:22s} {len(x) / SR * 1000:5.0f} ms")
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "sons-interface"))
