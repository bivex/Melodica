# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
album_tonality_vl.py — Tonality-integration album demo, two profiles side by side.

Pipeline per movement:
  CoupledHMMEngine.harmonize(melody)           -> list[ChordLabel]
  ChordGenerator + ExactVoiceLeadingModifier   -> smooth pad (exact mts VL)
  BassGenerator / ArpeggiatorGenerator         -> bass + arp
  export_multitrack_midi                        -> MIDI
Also runs verify_progression (Tonality oracle) over each movement's chords.

Profiles:
  moody  — sparse 1-note/bar melody, default coupling (chromatic/minor-leaning).
  bright — dense 4-note/bar chord-tone outline + key_coupling_weight=3.0
           (forces bright diatonic I-IV-V-I harmony).

Run:  .venv_dd/bin/python scripts/album_tonality_vl.py
Out:  output/tonality_album/album_moody.mid , album_bright.mid
"""

from __future__ import annotations

from pathlib import Path

from melodica.engines.coupled_hmm_engine import CoupledHMMEngine
from melodica.generators import ArpeggiatorGenerator, BassGenerator, ChordGenerator
from melodica.harmonize.coupled_hmm import HMMConfig
from melodica.harmonize import harmonizer_profile
from melodica.midi import export_multitrack_midi
from melodica.modifiers import ExactVoiceLeadingModifier, HumanizeModifier, LimitNoteRangeModifier
from melodica.theory import name_chord_label, verify_progression, voice_lead_progression
from melodica.types import HarmonizationRequest, Mode, Note, PhraseInstance, Scale

BEATS = 16.0

# Each profile: key, bpm, HMMConfig kwargs, movements[(name, [(pitch,start,dur)])].
PROFILES = {
    "moody": {
        "key": Scale(root=0, mode=Mode.MAJOR), "bpm": 92,
        "config": {},  # supervised weights — no runtime color penalty needed
        "movements": [
            ("I-Morning",  [(60, 0, 4), (64, 4, 4), (67, 8, 4), (72, 12, 4)]),
            ("II-Wander",  [(57, 0, 4), (60, 4, 4), (64, 8, 4), (67, 12, 4)]),
            ("III-Home",   [(67, 0, 4), (64, 4, 4), (60, 8, 4), (55, 12, 4)]),
        ],
    },
    "bright": {
        "key": Scale(root=0, mode=Mode.MAJOR), "bpm": 96,
        "config": {"key_coupling_weight": 3.0},  # supervised weights — no color penalty
        # Dense 4-note/bar chord-tone outlines: C-F-G-C / Am-F-G-C / C-G-G-C.
        "movements": [
            ("I-Morning", [(60,0,1),(64,1,1),(67,2,1),(72,3,1),
                           (60,4,1),(65,5,1),(69,6,1),(72,7,1),
                           (59,8,1),(62,9,1),(67,10,1),(71,11,1),
                           (72,12,1),(67,13,1),(64,14,1),(60,15,1)]),
            ("II-Wander", [(57,0,1),(60,1,1),(64,2,1),(69,3,1),
                           (62,4,1),(65,5,1),(69,6,1),(74,7,1),
                           (55,8,1),(59,9,1),(62,10,1),(67,11,1),
                           (60,12,1),(64,13,1),(67,14,1),(72,15,1)]),
            ("III-Home",  [(60,0,1),(64,1,1),(67,2,1),(72,3,1),
                           (55,4,1),(59,5,1),(62,6,1),(67,7,1),
                           (62,8,1),(67,9,1),(71,10,1),(74,11,1),
                           (60,12,1),(64,13,1),(67,14,1),(72,15,1)]),
        ],
    },
    "jazz": {
        "key": Scale(root=0, mode=Mode.MAJOR), "bpm": 100,
        "profile": "jazz",  # harmonizer_profile("jazz") -> completion_bonus=5 (7th retention)
        "config": {},
        # Dense 4-note/bar 7th-arp outlines so the set-completion term fires:
        # I-vi-ii-V / ii-V-I / secondary-dominant turnarounds.
        "movements": [
            ("I-Turnaround", [(60,0,1),(64,1,1),(67,2,1),(71,3,1),    # Cmaj7
                              (57,4,1),(60,5,1),(64,6,1),(67,7,1),    # Am7
                              (62,8,1),(65,9,1),(69,10,1),(72,11,1),  # Dm7
                              (67,12,1),(71,13,1),(74,14,1),(77,15,1)]),  # G7
            ("II-IiViI",     [(62,0,1),(65,1,1),(69,2,1),(72,3,1),    # Dm7
                              (67,4,1),(71,5,1),(74,6,1),(77,7,1),    # G7
                              (60,8,1),(64,9,1),(67,10,1),(71,11,1),  # Cmaj7
                              (60,12,1),(64,13,1),(67,14,1),(71,15,1)]),  # Cmaj7
            ("III-SecDom",   [(60,0,1),(64,1,1),(67,2,1),(71,3,1),    # Cmaj7
                              (57,4,1),(61,5,1),(64,6,1),(67,7,1),    # A7 (V/vi)
                              (62,8,1),(65,9,1),(69,10,1),(72,11,1),  # Dm7
                              (67,12,1),(71,13,1),(74,14,1),(77,15,1)]),  # G7
        ],
    },
}


def _shift(notes: list, offset: float) -> list:
    out = []
    for n in notes:
        out.append(type(n)(pitch=n.pitch, start=n.start + offset,
                           duration=n.duration, velocity=n.velocity,
                           absolute=getattr(n, "absolute", True)))
    return out


def _chord_names(chords: list) -> list[str]:
    names = []
    for c in chords:
        nm = name_chord_label(c)
        if nm and nm.chosen:
            ri = nm.chosen.interpretation
            names.append(f"{ri.root_pc}:{ri.quality}")
        else:
            names.append("?")
    return names


def generate(profile: dict, out_path: Path) -> None:
    key = profile["key"]
    engine = CoupledHMMEngine(config=harmonizer_profile(profile.get("profile", "pop"), **profile.get("config", {})))
    pad_track: list = []
    bass_track: list = []
    arp_track: list = []
    offset = 0.0

    print(f"\n### {out_path.stem} | key=root{key.root} {key.mode.value} | "
          f"BPM {profile['bpm']} | profile={profile.get('profile','pop')} +{profile['config']}")
    for name, mel in profile["movements"]:
        notes = [Note(p, s, d) for (p, s, d) in mel]
        chords = engine.harmonize(HarmonizationRequest(notes, key, chord_rhythm=4.0))

        rep = verify_progression(chords)
        print(f"  {name:10} chords={_chord_names(chords)}  "
              f"verify: parse={rep['parseable']}/{rep['n']} amb={rep['ambiguous']} VL={rep['total_voice_leading']}")

        pad = PhraseInstance(generator=ChordGenerator(voicing="closed"),
                             modifiers=[ExactVoiceLeadingModifier(), LimitNoteRangeModifier(low=60, high=83)])
        bass = PhraseInstance(generator=BassGenerator(), modifiers=[HumanizeModifier(), LimitNoteRangeModifier(low=36, high=47)])
        arp = PhraseInstance(generator=ArpeggiatorGenerator(), modifiers=[LimitNoteRangeModifier(low=72, high=95)])
        pad_track += _shift(pad.render(chords, key, BEATS), offset)
        bass_track += _shift(bass.render(chords, key, BEATS), offset)
        arp_track += _shift(arp.render(chords, key, BEATS), offset)
        offset += BEATS

    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_multitrack_midi(
        {"Pad-ExactVL": pad_track, "Bass": bass_track, "Arp": arp_track},
        out_path, bpm=profile["bpm"], key=key, time_sig=(4, 4),
    )
    print(f"  -> {out_path}  ({int(offset)} beats, "
          f"{len(pad_track)}/{len(bass_track)}/{len(arp_track)} notes)")


def main() -> None:
    out_dir = Path("output/tonality_album")
    for name, profile in PROFILES.items():
        generate(profile, out_dir / f"album_{name}.mid")


if __name__ == "__main__":
    main()
