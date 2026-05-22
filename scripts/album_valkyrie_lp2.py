# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
album_valkyrie_lp2.py — "VALKYRIE LP2".

A stunning 10-track cinematic jazz-noir and modern jazz album combining
Scandinavian mythology, jazz fusion, and dark ambient textures.
Enhanced with section-by-section dynamic orchestration, voice-led chords,
dynamic jazz drums, and expressive CC automation.
"""

import math
import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.composer.transformers import spiceup, serialize_canon, OneToThree
from melodica.harmonize.predictive import PredictiveHarmonizer
from melodica.rhythm.groove_template import SWING_60, LAID_BACK
from melodica.theory.chords import Quality
from melodica.theory.voicing import voice_lead, chord_to_notes

# Keys Config
KEY_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)       # D minor (Aeolian)
KEY_D_DORIAN = Scale(root=2, mode=Mode.DORIAN)       # D Dorian
KEY_F_SHARP_DORIAN = Scale(root=6, mode=Mode.DORIAN) # F# Dorian
KEY_F_SHARP_PHRYGIAN = Scale(root=6, mode=Mode.PHRYGIAN) # F# Phrygian
KEY_F_SHARP_MINOR = Scale(root=6, mode=Mode.AEOLIAN) # F# minor (Aeolian)
KEY_B_FLAT_DORIAN = Scale(root=10, mode=Mode.DORIAN) # Bb Dorian
KEY_B_FLAT_MINOR = Scale(root=10, mode=Mode.AEOLIAN)  # Bb minor (Aeolian)


def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    """Parse Roman numeral progression into ChordLabels."""
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords


def generate_voice_led_comping(chords, base_octave=4, velocity=70, duration_ratio=0.8, offset=0.0, prev_voicing=None):
    """
    Generate voice-led comping chords with dynamic extensions.
    """
    notes = []
    for c in chords:
        orig_ext = list(c.extensions)
        
        # Add rich jazz extensions
        if c.quality in [Quality.MINOR, Quality.MINOR7]:
            if 10 not in c.extensions:
                c.extensions.append(10)
            if 14 not in c.extensions:
                c.extensions.append(14)
        elif c.quality in [Quality.MAJOR, Quality.MAJOR7]:
            if 11 not in c.extensions:
                c.extensions.append(11)
            if 14 not in c.extensions:
                c.extensions.append(14)
        elif c.quality == Quality.DOMINANT7:
            if 14 not in c.extensions:
                c.extensions.append(14)
        
        # Voicing calculation
        try:
            if prev_voicing is None:
                voicing = chord_to_notes(c, base_octave=base_octave)
            else:
                voicing = voice_lead(prev_voicing, c)
        except Exception:
            voicing = [12 * (base_octave + 1) + c.root, 12 * (base_octave + 1) + c.root + 4, 12 * (base_octave + 1) + c.root + 7]
            
        # Add notes
        for p in voicing:
            notes.append(NoteInfo(
                pitch=p,
                start=c.start + offset,
                duration=c.duration * duration_ratio,
                velocity=velocity
            ))
        prev_voicing = voicing
        # Restore extensions
        c.extensions = orig_ext
        
    return notes, prev_voicing


def generate_drum_pattern(style: str, duration: float, velocity_scale: float = 1.0) -> list[NoteInfo]:
    """
    Generate rich dynamic drum patterns for different styles.
    """
    drums = []
    
    if style == "ambient_brushed":
        for i in range(int(duration)):
            drums.append(NoteInfo(pitch=38, start=i + 0.0, duration=0.4, velocity=int(32 * velocity_scale)))
            if i % 4 in [0, 2]:
                drums.append(NoteInfo(pitch=36, start=i + 0.0, duration=0.3, velocity=int(30 * velocity_scale)))
            if i % 4 in [1, 3]:
                drums.append(NoteInfo(pitch=42, start=i + 0.0, duration=0.1, velocity=int(40 * velocity_scale)))
                
    elif style == "swing_brushed":
        for bar in range(int(duration / 4.0)):
            bar_start = bar * 4.0
            drums.append(NoteInfo(pitch=36, start=bar_start + 0.0, duration=0.2, velocity=int(45 * velocity_scale)))
            drums.append(NoteInfo(pitch=36, start=bar_start + 2.0, duration=0.2, velocity=int(40 * velocity_scale)))
            drums.append(NoteInfo(pitch=42, start=bar_start + 1.0, duration=0.1, velocity=int(50 * velocity_scale)))
            drums.append(NoteInfo(pitch=42, start=bar_start + 3.0, duration=0.1, velocity=int(50 * velocity_scale)))
            snare_offsets = [0.0, 1.0, 1.66, 2.0, 3.0, 3.66]
            for off in snare_offsets:
                vel = 35 if off in [1.66, 3.66] else 42
                drums.append(NoteInfo(pitch=38, start=bar_start + off, duration=0.2, velocity=int(vel * velocity_scale)))
                
    elif style == "funk_broken":
        for bar in range(int(duration / 4.0)):
            bar_start = bar * 4.0
            kick_offs = [0.0, 0.75, 2.0, 2.5]
            for off in kick_offs:
                drums.append(NoteInfo(pitch=36, start=bar_start + off, duration=0.2, velocity=int(85 * velocity_scale)))
            snare_events = [(1.0, 95), (1.75, 40), (3.0, 105), (3.5, 45)]
            for off, vel in snare_events:
                drums.append(NoteInfo(pitch=38, start=bar_start + off, duration=0.15, velocity=int(vel * velocity_scale)))
            for i in range(8):
                off = i * 0.5
                vel = 65 if i % 2 == 0 else 45
                drums.append(NoteInfo(pitch=42, start=bar_start + off, duration=0.1, velocity=int(vel * velocity_scale)))
                
    elif style == "hard_bop":
        for bar in range(int(duration / 4.0)):
            bar_start = bar * 4.0
            for beat in range(4):
                drums.append(NoteInfo(pitch=36, start=bar_start + beat, duration=0.15, velocity=int(35 * velocity_scale)))
            if random.random() < 0.3:
                drums.append(NoteInfo(pitch=36, start=bar_start + 2.5, duration=0.2, velocity=int(95 * velocity_scale)))
            drums.append(NoteInfo(pitch=42, start=bar_start + 1.0, duration=0.1, velocity=int(75 * velocity_scale)))
            drums.append(NoteInfo(pitch=42, start=bar_start + 3.0, duration=0.1, velocity=int(75 * velocity_scale)))
            ride_offs = [0.0, 1.0, 1.66, 2.0, 3.0, 3.66]
            for off in ride_offs:
                vel = 85 if off not in [1.66, 3.66] else 65
                drums.append(NoteInfo(pitch=51, start=bar_start + off, duration=0.25, velocity=int(vel * velocity_scale)))
            snare_offs = [1.0, 2.33, 3.5]
            for off in snare_offs:
                if random.random() < 0.7:
                    vel = random.choice([40, 85])
                    drums.append(NoteInfo(pitch=38, start=bar_start + off, duration=0.15, velocity=int(vel * velocity_scale)))
                    
    return drums


# ---------------------------------------------------------------------------
# SIDE A — "Ascent" (Восхождение)
# ---------------------------------------------------------------------------

# 01. Iron Wings (Intro)
def produce_track_1():
    """Cold awakening. Single Rhodes pedal line, low Upright E pedal, brushed snare."""
    print("Producing 01. Iron Wings (Intro / Cold D minor Awakening)...")
    total_duration = 200.0  # 3:20 at 60 BPM
    piano_notes = []
    bass_notes = []
    drums_notes = []
    
    # A. Morning Mist (Beats 0.0 - 64.0)
    chords_1 = _build_chords("i v i v " * 4, 64.0, KEY_D_MINOR)
    solo_params_1 = GeneratorParams(density=0.15, key_range_low=55, key_range_high=74)
    solo_gen_1 = SoloMelodyGenerator(solo_params_1, style="modal_ambient", vibrato_depth=0.5)
    melody_1 = solo_gen_1.render(chords_1, KEY_D_MINOR, 64.0)
    for n in melody_1:
        n.duration *= 2.0
        n.velocity = random.randint(40, 48)  # ppp
        piano_notes.append(n)
    for i in range(int(64.0 / 8.0)):
        bass_notes.append(NoteInfo(pitch=16, start=i * 8.0, duration=7.5, velocity=40))
        
    # B. Cold Wind (Beats 64.0 - 144.0)
    chords_2 = _build_chords("i iv v i " * 5, 80.0, KEY_D_MINOR)
    solo_params_2 = GeneratorParams(density=0.25, key_range_low=55, key_range_high=74)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="modal_ambient", vibrato_depth=0.6)
    melody_2 = solo_gen_2.render(chords_2, KEY_D_MINOR, 80.0)
    for n in melody_2:
        n.duration *= 1.5
        n.velocity = random.randint(45, 53)  # pp
        n.start += 64.0
        piano_notes.append(n)
    for c in chords_2:
        bass_notes.append(NoteInfo(pitch=c.root + 16, start=c.start + 64.0, duration=c.duration * 0.95, velocity=46))
    drums_notes.extend([
        NoteInfo(pitch=38, start=i * 2.0 + 1.0 + 64.0, duration=0.2, velocity=30)
        for i in range(int(80.0 / 2.0))
    ])
        
    # C. Iron Silhouette (Beats 144.0 - 200.0)
    chords_3 = _build_chords("i v bVI v " * 3 + "i i ", 56.0, KEY_D_MINOR)
    comp_notes, _ = generate_voice_led_comping(chords_3, base_octave=4, velocity=48, duration_ratio=0.85)
    for n in comp_notes:
        n.start += 144.0
    piano_notes.extend(comp_notes)
    
    bass_params_3 = GeneratorParams(density=0.45, key_range_low=28, key_range_high=48)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="walking")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_D_MINOR, 56.0)
    for n in melody_bass_3:
        n.velocity = random.randint(50, 58)
        n.start += 144.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=38, start=i * 2.0 + 144.0, duration=0.25, velocity=34)
        for i in range(int(56.0 / 2.0))
    ])
    
    return {"piano": piano_notes, "bass": bass_notes, "drums": drums_notes}, 60.0


# 02. Chooser of the Slain
def produce_track_2():
    """Aggressive Coltrane-style Tenor Sax + Broken Funk Slap Bass."""
    print("Producing 02. Chooser of the Slain (Coltrane Sax + Slap Broken Funk)...")
    total_duration = 660.0
    lead_notes = []
    piano_notes = []
    bass_notes = []
    drums_notes = []
    prev_voicing = None
    
    # A. Anticipation (0.0 - 48.0)
    chords_1 = _build_chords("i iv VII i " * 3, 48.0, KEY_D_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_1, base_octave=4, velocity=68, prev_voicing=prev_voicing)
    piano_notes.extend(comp_notes)
    
    bass_params_1 = GeneratorParams(density=0.45, key_range_low=32, key_range_high=52)
    bass_gen_1 = ModernBass2025Generator(bass_params_1, style="ghost_note")
    melody_bass_1 = bass_gen_1.render(chords_1, KEY_D_DORIAN, 48.0)
    bass_notes.extend(melody_bass_1)
    
    drums_notes.extend(generate_drum_pattern("funk_broken", 48.0, velocity_scale=0.75))
    
    # B. Flight of the Valkyrie (48.0 - 192.0)
    chords_2 = _build_chords("i iv VII i " * 9, 144.0, KEY_D_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_2, base_octave=4, velocity=78, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 48.0
    piano_notes.extend(comp_notes)
    
    solo_params_2 = GeneratorParams(density=0.55, key_range_low=50, key_range_high=78)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="jazz_fusion", vibrato_depth=0.7)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_D_DORIAN, 144.0)
    for n in melody_lead_2:
        n.start += 48.0
        n.velocity = min(110, n.velocity + 10)
        lead_notes.append(n)
        
    bass_params_2 = GeneratorParams(density=0.72, key_range_low=32, key_range_high=52)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="slap")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_D_DORIAN, 144.0)
    for n in melody_bass_2:
        n.start += 48.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 48.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("funk_broken", 144.0, velocity_scale=1.0)
    ])
    
    # C. The Hunt (192.0 - 320.0)
    chords_3 = _build_chords("i iv VII i " * 8, 128.0, KEY_D_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_3, base_octave=4, velocity=85, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 192.0
    piano_notes.extend(comp_notes)
    
    solo_params_3 = GeneratorParams(density=0.70, key_range_low=50, key_range_high=78)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="jazz_fusion", vibrato_depth=0.75)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_D_DORIAN, 128.0)
    for n in melody_lead_3:
        n.start += 192.0
        n.velocity = min(115, n.velocity + 15)
        lead_notes.append(n)
        
    bass_params_3 = GeneratorParams(density=0.8, key_range_low=32, key_range_high=52)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="hybrid_slap")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_D_DORIAN, 128.0)
    for n in melody_bass_3:
        n.start += 192.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 192.0, duration=d.duration, velocity=min(127, d.velocity + 10))
        for d in generate_drum_pattern("funk_broken", 128.0, velocity_scale=1.1)
    ])
    
    # D. The Shield Wall - Bridge (320.0 - 416.0)
    # Modulate to Phrygian tension chords
    chords_4 = _build_chords("bII bII i i " * 6, 96.0, KEY_D_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_4, base_octave=4, velocity=60, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 320.0
    piano_notes.extend(comp_notes)
    
    solo_params_4 = GeneratorParams(density=0.35, key_range_low=50, key_range_high=78)
    solo_gen_4 = SoloMelodyGenerator(solo_params_4, style="vocal_mimic", vibrato_depth=0.85)
    melody_lead_4 = solo_gen_4.render(chords_4, KEY_D_DORIAN, 96.0)
    for n in melody_lead_4:
        n.start += 320.0
        n.velocity = int(n.velocity * 0.8)
        lead_notes.append(n)
        
    bass_params_4 = GeneratorParams(density=0.45, key_range_low=28, key_range_high=48)
    bass_gen_4 = ModernBass2025Generator(bass_params_4, style="self_modifying")
    melody_bass_4 = bass_gen_4.render(chords_4, KEY_D_DORIAN, 96.0)
    for n in melody_bass_4:
        n.start += 320.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=42, start=i * 1.0 + 320.0, duration=0.1, velocity=45)
        for i in range(96)
    ])
    
    # E. Ultimate Ascent (416.0 - 592.0)
    chords_5 = _build_chords("i iv VII i " * 11, 176.0, KEY_D_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_5, base_octave=4, velocity=90, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 416.0
    piano_notes.extend(comp_notes)
    
    solo_params_5 = GeneratorParams(density=0.78, key_range_low=50, key_range_high=78)
    solo_gen_5 = SoloMelodyGenerator(solo_params_5, style="shred_guitar", vibrato_depth=0.9)
    melody_lead_5 = solo_gen_5.render(chords_5, KEY_D_DORIAN, 176.0)
    for n in melody_lead_5:
        n.start += 416.0
        n.velocity = min(120, n.velocity + 20)
        lead_notes.append(n)
        
    bass_params_5 = GeneratorParams(density=0.85, key_range_low=32, key_range_high=52)
    bass_gen_5 = ModernBass2025Generator(bass_params_5, style="slap")
    melody_bass_5 = bass_gen_5.render(chords_5, KEY_D_DORIAN, 176.0)
    for n in melody_bass_5:
        n.start += 416.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 416.0, duration=d.duration, velocity=min(127, d.velocity + 15))
        for d in generate_drum_pattern("funk_broken", 176.0, velocity_scale=1.15)
    ])
    
    # F. Descent to Valhalla (592.0 - 660.0)
    chords_6 = _build_chords("i i i i " * 4 + "i i ", 68.0, KEY_D_DORIAN)
    comp_notes, _ = generate_voice_led_comping(chords_6, base_octave=4, velocity=45, duration_ratio=0.9, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 592.0
    piano_notes.extend(comp_notes)
    
    solo_params_6 = GeneratorParams(density=0.2, key_range_low=50, key_range_high=70)
    solo_gen_6 = SoloMelodyGenerator(solo_params_6, style="blues_lick", vibrato_depth=0.8)
    melody_lead_6 = solo_gen_6.render(chords_6, KEY_D_DORIAN, 68.0)
    for n in melody_lead_6:
        n.start += 592.0
        n.velocity = 50
        lead_notes.append(n)
        
    for i in range(int(68.0 / 4.0)):
        bass_notes.append(NoteInfo(pitch=14, start=i * 4.0 + 592.0, duration=3.8, velocity=40))
        
    return {"lead": lead_notes, "piano": piano_notes, "bass": bass_notes, "drums": drums_notes}, 115.0


# 03. Mist & Armor
def produce_track_3():
    """Lyrical swing Flugelhorn, Vibraphone echo, Acoustic bass walking."""
    print("Producing 03. Mist & Armor (Flugelhorn Swing / Vibraphone echo)...")
    total_duration = 468.0
    lead_notes = []
    pad_notes = []
    bass_notes = []
    drums_notes = []
    
    # A. Shrouded Path (0.0 - 64.0)
    chords_1 = _build_chords("i ii V i " * 4, 64.0, KEY_F_SHARP_DORIAN)
    solo_params_1 = GeneratorParams(density=0.3, key_range_low=52, key_range_high=74)
    solo_gen_1 = SoloMelodyGenerator(solo_params_1, style="modal_ambient", vibrato_depth=0.8)
    melody_lead_1 = solo_gen_1.render(chords_1, KEY_F_SHARP_DORIAN, 64.0)
    for n in melody_lead_1:
        n.velocity = random.randint(48, 56)
        lead_notes.append(n)
    for c in chords_1:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 60, start=c.start, duration=c.duration * 0.9, velocity=42),
            NoteInfo(pitch=c.root + 64, start=c.start, duration=c.duration * 0.9, velocity=42),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start, duration=c.duration * 0.95, velocity=48))
        
    # B. Gentle Swing (64.0 - 224.0)
    chords_2 = _build_chords("i ii V i " * 10, 160.0, KEY_F_SHARP_DORIAN)
    solo_params_2 = GeneratorParams(density=0.45, key_range_low=52, key_range_high=74)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="vocal_mimic", vibrato_depth=0.8)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_F_SHARP_DORIAN, 160.0)
    for n in melody_lead_2:
        n.start += 64.0
        lead_notes.append(n)
        
    for c in chords_2:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 60, start=c.start + 1.5 + 64.0, duration=1.5, velocity=52),
            NoteInfo(pitch=c.root + 64, start=c.start + 1.5 + 64.0, duration=1.5, velocity=52),
        ])
        
    bass_params_2 = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="walking")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_F_SHARP_DORIAN, 160.0)
    for n in melody_bass_2:
        n.start += 64.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 64.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 160.0, velocity_scale=0.85)
    ])
    
    # C. Solitude's Voice (224.0 - 352.0)
    chords_3 = _build_chords("i ii V i " * 8, 128.0, KEY_F_SHARP_DORIAN)
    solo_params_3 = GeneratorParams(density=0.58, key_range_low=52, key_range_high=74)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="vocal_mimic", vibrato_depth=0.85)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_F_SHARP_DORIAN, 128.0)
    for n in melody_lead_3:
        n.start += 224.0
        n.velocity = min(110, n.velocity + 8)
        lead_notes.append(n)
        
    for c in chords_3:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 60, start=c.start + 1.0 + 224.0, duration=2.0, velocity=58),
            NoteInfo(pitch=c.root + 64, start=c.start + 1.0 + 224.0, duration=2.0, velocity=58),
        ])
        
    bass_params_3 = GeneratorParams(density=0.58, key_range_low=28, key_range_high=48)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="walking")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_F_SHARP_DORIAN, 128.0)
    for n in melody_bass_3:
        n.start += 224.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 224.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 128.0, velocity_scale=0.95)
    ])
    
    # D. Armor Fades (352.0 - 468.0)
    chords_4 = _build_chords("i ii V i " * 7 + "i ", 116.0, KEY_F_SHARP_DORIAN)
    solo_params_4 = GeneratorParams(density=0.25, key_range_low=52, key_range_high=70)
    solo_gen_4 = SoloMelodyGenerator(solo_params_4, style="modal_ambient", vibrato_depth=0.8)
    melody_lead_4 = solo_gen_4.render(chords_4, KEY_F_SHARP_DORIAN, 116.0)
    for n in melody_lead_4:
        n.start += 352.0
        n.velocity = 45
        lead_notes.append(n)
        
    for c in chords_4:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 60, start=c.start + 352.0, duration=c.duration * 0.95, velocity=38),
            NoteInfo(pitch=c.root + 64, start=c.start + 352.0, duration=c.duration * 0.95, velocity=38),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start + 352.0, duration=c.duration * 0.95, velocity=40))
        
    drums_notes.extend([
        NoteInfo(pitch=42, start=i * 2.0 + 352.0, duration=0.2, velocity=35)
        for i in range(int(116.0 / 2.0))
    ])
    
    return {"lead": lead_notes, "pad": pad_notes, "bass": bass_notes, "drums": drums_notes}, 76.0


# 04. Raven Protocol
def produce_track_4():
    """Alto & Soprano Sax counterpoint, Prepared Piano, Sliding Fretless Bass."""
    print("Producing 04. Raven Protocol (Alto + Soprano counterpoint / Fretless Bass)...")
    total_duration = 580.0
    lead_notes = []
    canon_lead_notes = []
    piano_notes = []
    bass_notes = []
    pad_notes = []
    
    # A. Surveillance (0.0 - 96.0)
    chords_1 = _build_chords("i i iv iv bII bII i i " * 3, 96.0, KEY_F_SHARP_PHRYGIAN)
    solo_params_1 = GeneratorParams(density=0.38, key_range_low=52, key_range_high=76)
    solo_gen_1 = SoloMelodyGenerator(solo_params_1, style="jazz_fusion", vibrato_depth=0.7)
    melody_lead_1 = solo_gen_1.render(chords_1, KEY_F_SHARP_PHRYGIAN, 96.0)
    lead_notes.extend(melody_lead_1)
    
    for c in chords_1:
        piano_notes.extend([
            NoteInfo(pitch=c.root + 36, start=c.start + 0.5, duration=0.2, velocity=62),
            NoteInfo(pitch=c.root + 43, start=c.start + 1.5, duration=0.2, velocity=62),
        ])
        
    bass_params_1 = GeneratorParams(density=0.45, key_range_low=26, key_range_high=46)
    bass_gen_1 = ModernBass2025Generator(bass_params_1, style="self_modifying")
    melody_bass_1 = bass_gen_1.render(chords_1, KEY_F_SHARP_PHRYGIAN, 96.0)
    bass_notes.extend(melody_bass_1)
    
    for c in chords_1:
        pad_notes.append(NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.02, velocity=32))
        
    # B. Eerie Duet (96.0 - 288.0)
    chords_2 = _build_chords("i i iv iv bII bII i i " * 6, 192.0, KEY_F_SHARP_PHRYGIAN)
    solo_params_2 = GeneratorParams(density=0.45, key_range_low=52, key_range_high=76)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="jazz_fusion", vibrato_depth=0.75)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_F_SHARP_PHRYGIAN, 192.0)
    
    # Generate counterpoint soprano sax from alto sax in local coordinates
    alto_for_canon = [NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=n.velocity) for n in melody_lead_2]
    canon_melody = serialize_canon(
        voices=[alto_for_canon, alto_for_canon],
        delay_beats=8.0,
        transpositions=[0, 12],
        duration_beats=192.0,
    )
    for n in melody_lead_2:
        n.start += 96.0
        lead_notes.append(n)
        
    for n in canon_melody:
        n.start += 96.0
        canon_lead_notes.append(n)
        
    for c in chords_2:
        piano_notes.extend([
            NoteInfo(pitch=c.root + 36, start=c.start + 0.5 + 96.0, duration=0.25, velocity=68),
            NoteInfo(pitch=c.root + 43, start=c.start + 1.5 + 96.0, duration=0.25, velocity=68),
        ])
        
    bass_params_2 = GeneratorParams(density=0.58, key_range_low=26, key_range_high=46)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="self_modifying")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_F_SHARP_PHRYGIAN, 192.0)
    for n in melody_bass_2:
        n.start += 96.0
        bass_notes.append(n)
        
    for c in chords_2:
        pad_notes.append(NoteInfo(pitch=c.root + 48, start=c.start + 96.0, duration=c.duration * 1.02, velocity=36))
        
    # C. Granular Swarm (288.0 - 480.0)
    chords_3 = _build_chords("i i iv iv bII bII i i " * 6, 192.0, KEY_F_SHARP_PHRYGIAN)
    solo_params_3 = GeneratorParams(density=0.55, key_range_low=52, key_range_high=78)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="jazz_fusion", vibrato_depth=0.8)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_F_SHARP_PHRYGIAN, 192.0)
    
    alto_for_canon_3 = [NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=n.velocity) for n in melody_lead_3]
    canon_melody_3 = serialize_canon(
        voices=[alto_for_canon_3, alto_for_canon_3],
        delay_beats=6.0,
        transpositions=[0, 12],
        duration_beats=192.0,
    )
    for n in melody_lead_3:
        n.start += 288.0
        lead_notes.append(n)
        
    for n in canon_melody_3:
        n.start += 288.0
        canon_lead_notes.append(n)
        
    for c in chords_3:
        for offset in [0.0, 1.0, 2.0, 3.0]:
            piano_notes.append(NoteInfo(pitch=c.root + 36 + int(offset * 2), start=c.start + offset + 0.25 + 288.0, duration=0.15, velocity=75))
            
    bass_params_3 = GeneratorParams(density=0.68, key_range_low=26, key_range_high=46)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="self_modifying")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_F_SHARP_PHRYGIAN, 192.0)
    for n in melody_bass_3:
        n.start += 288.0
        bass_notes.append(n)
        
    for c in chords_3:
        pad_notes.append(NoteInfo(pitch=c.root + 48, start=c.start + 288.0, duration=c.duration * 1.05, velocity=42))
        
    # D. Raven Fleeing (480.0 - 580.0)
    chords_4 = _build_chords("i i i i " * 6 + "i i ", 100.0, KEY_F_SHARP_PHRYGIAN)
    solo_params_4 = GeneratorParams(density=0.18, key_range_low=52, key_range_high=70)
    solo_gen_4 = SoloMelodyGenerator(solo_params_4, style="modal_ambient", vibrato_depth=0.8)
    melody_lead_4 = solo_gen_4.render(chords_4, KEY_F_SHARP_PHRYGIAN, 100.0)
    for n in melody_lead_4:
        n.start += 480.0
        n.velocity = 38
        lead_notes.append(n)
        
    for c in chords_4:
        piano_notes.append(NoteInfo(pitch=c.root + 36, start=c.start + 0.5 + 480.0, duration=0.4, velocity=40))
        bass_notes.append(NoteInfo(pitch=c.root + 24, start=c.start + 480.0, duration=c.duration * 0.95, velocity=42))
        pad_notes.append(NoteInfo(pitch=c.root + 48, start=c.start + 480.0, duration=c.duration * 0.98, velocity=26))
        
    return {"lead": lead_notes, "canon_lead": canon_lead_notes, "piano": piano_notes, "bass": bass_notes, "pad": pad_notes}, 98.0


# 05. The Battlefield (Interlude)
def produce_track_5():
    """Solo Upright Bass медленная импровизация, отдаленный Moog дрон."""
    print("Producing 05. The Battlefield (Solo Bass Improv + Moog Drone)...")
    total_duration = 126.0
    bass_notes = []
    pad_notes = []
    
    # A. Ash & Snow (0.0 - 48.0)
    chords_1 = _build_chords("i i iv iv " * 3, 48.0, KEY_F_SHARP_MINOR)
    bass_params_1 = GeneratorParams(density=0.4, key_range_low=32, key_range_high=55)
    bass_gen_1 = ModernBass2025Generator(bass_params_1, style="adaptive")
    melody_bass_1 = bass_gen_1.render(chords_1, KEY_F_SHARP_MINOR, 48.0)
    for n in melody_bass_1:
        n.duration *= 1.4
        n.velocity = random.randint(38, 48)
        bass_notes.append(n)
    for c in chords_1:
        pad_notes.append(NoteInfo(pitch=c.root + 24, start=c.start, duration=c.duration * 1.1, velocity=26))
        
    # B. Wounded Cries (48.0 - 96.0)
    chords_2 = _build_chords("i i iv iv v v i i " * 3, 48.0, KEY_F_SHARP_MINOR)
    bass_params_2 = GeneratorParams(density=0.55, key_range_low=32, key_range_high=62)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="adaptive")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_F_SHARP_MINOR, 48.0)
    for n in melody_bass_2:
        n.duration *= 1.2
        n.start += 48.0
        n.velocity = random.randint(46, 58)
        bass_notes.append(n)
    for c in chords_2:
        pad_notes.append(NoteInfo(pitch=c.root + 24, start=c.start + 48.0, duration=c.duration * 1.15, velocity=34))
        
    # C. Silence Returns (96.0 - 126.0)
    chords_3 = _build_chords("i i i i " * 3 + "i i ", 30.0, KEY_F_SHARP_MINOR)
    bass_params_3 = GeneratorParams(density=0.25, key_range_low=28, key_range_high=50)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="adaptive")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_F_SHARP_MINOR, 30.0)
    for n in melody_bass_3:
        n.duration *= 1.5
        n.start += 96.0
        n.velocity = random.randint(30, 42)
        bass_notes.append(n)
    for c in chords_3:
        pad_notes.append(NoteInfo(pitch=c.root + 24, start=c.start + 96.0, duration=c.duration * 1.05, velocity=20))
        
    return {"bass": bass_notes, "pad": pad_notes}, 58.0


# ---------------------------------------------------------------------------
# SIDE B — "Descent" (Нисхождение)
# ---------------------------------------------------------------------------

# 06. Valhalla Calling
def produce_track_6():
    """Standard jazz trio + Harmon-muted trumpet entering at 2:30 + string quartet at 4:00."""
    print("Producing 06. Valhalla Calling (Jazz Trio + Harmon Mute + Cinematic Strings)...")
    total_duration = 646.0
    piano_notes = []
    bass_notes = []
    lead_notes = []
    pad_notes = []
    drums_notes = []
    prev_voicing = None
    
    # A. Earthly Trio (0.0 - 220.0)
    chords_1 = _build_chords("i iv VII III VI ii V i " * 3 + "i iv VII III ", 220.0, KEY_B_FLAT_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_1, base_octave=4, velocity=64, prev_voicing=prev_voicing)
    piano_notes.extend(comp_notes)
    
    bass_params_1 = GeneratorParams(density=0.5, key_range_low=28, key_range_high=48)
    bass_gen_1 = ModernBass2025Generator(bass_params_1, style="walking")
    melody_bass_1 = bass_gen_1.render(chords_1, KEY_B_FLAT_DORIAN, 220.0)
    bass_notes.extend(melody_bass_1)
    
    drums_notes.extend(generate_drum_pattern("swing_brushed", 220.0, velocity_scale=0.8))
    
    # B. Muted Whispers (220.0 - 352.0)
    chords_2 = _build_chords("VI ii V i i iv VII III " * 2, 132.0, KEY_B_FLAT_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_2, base_octave=4, velocity=70, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 220.0
    piano_notes.extend(comp_notes)
    
    solo_params_2 = GeneratorParams(density=0.48, key_range_low=58, key_range_high=78)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="bebop_horn", vibrato_depth=0.8)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_B_FLAT_DORIAN, 132.0)
    for n in melody_lead_2:
        n.start += 220.0
        n.velocity = int(n.velocity * 0.85)
        lead_notes.append(n)
        
    bass_params_2 = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="walking")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_B_FLAT_DORIAN, 132.0)
    for n in melody_bass_2:
        n.start += 220.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 220.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 132.0, velocity_scale=0.9)
    ])
    
    # C. Gates Open (352.0 - 544.0)
    chords_3 = _build_chords("VI ii V i i iv VII III " * 3, 192.0, KEY_B_FLAT_DORIAN)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_3, base_octave=4, velocity=78, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 352.0
    piano_notes.extend(comp_notes)
    
    solo_params_3 = GeneratorParams(density=0.55, key_range_low=58, key_range_high=80)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="bebop_horn", vibrato_depth=0.8)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_B_FLAT_DORIAN, 192.0)
    for n in melody_lead_3:
        n.start += 352.0
        lead_notes.append(n)
        
    for c in chords_3:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start + 352.0, duration=c.duration * 1.05, velocity=52),
            NoteInfo(pitch=c.root + 52, start=c.start + 352.0, duration=c.duration * 1.05, velocity=52),
            NoteInfo(pitch=c.root + 55, start=c.start + 352.0, duration=c.duration * 1.05, velocity=52),
        ])
        
    bass_params_3 = GeneratorParams(density=0.6, key_range_low=28, key_range_high=48)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="walking")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_B_FLAT_DORIAN, 192.0)
    for n in melody_bass_3:
        n.start += 352.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 352.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 192.0, velocity_scale=1.0)
    ])
    
    # D. Ascending the Rainbow Bridge (544.0 - 646.0)
    chords_4 = _build_chords("i i iv iv V V i i " * 3 + "i i ", 102.0, KEY_B_FLAT_DORIAN)
    comp_notes, _ = generate_voice_led_comping(chords_4, base_octave=4, velocity=48, duration_ratio=0.9, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 544.0
    piano_notes.extend(comp_notes)
    
    for c in chords_4:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start + 544.0, duration=c.duration * 1.02, velocity=42),
            NoteInfo(pitch=c.root + 55, start=c.start + 544.0, duration=c.duration * 1.02, velocity=42),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start + 544.0, duration=c.duration * 0.95, velocity=42))
    drums_notes.extend([
        NoteInfo(pitch=38, start=i * 2.0 + 544.0, duration=0.2, velocity=36)
        for i in range(int(102.0 / 2.0))
    ])
    
    return {"piano": piano_notes, "bass": bass_notes, "lead": lead_notes, "pad": pad_notes, "drums": drums_notes}, 88.0


# 07. Winged Fury
def produce_track_7():
    """Baritone Sax, Hammond B3, Hard Bop high-energy drums."""
    print("Producing 07. Winged Fury (Baritone Sax + Hammond B3 Organ Max Energy)...")
    total_duration = 781.0
    lead_notes = []
    piano_notes = []
    bass_notes = []
    drums_notes = []
    prev_voicing = None
    
    # A. Ignition (0.0 - 96.0)
    chords_1 = _build_chords("i i iv iv " * 6, 96.0, KEY_B_FLAT_MINOR)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_1, base_octave=3, velocity=82, prev_voicing=prev_voicing)
    piano_notes.extend(comp_notes)
    
    solo_params_1 = GeneratorParams(density=0.45, key_range_low=36, key_range_high=64)
    solo_gen_1 = SoloMelodyGenerator(solo_params_1, style="shred_guitar", vibrato_depth=0.8)
    melody_lead_1 = solo_gen_1.render(chords_1, KEY_B_FLAT_MINOR, 96.0)
    for n in melody_lead_1:
        n.pitch -= 12
        n.velocity = min(115, n.velocity + 10)
        lead_notes.append(n)
        
    bass_params_1 = GeneratorParams(density=0.6, key_range_low=24, key_range_high=44)
    bass_gen_1 = ModernBass2025Generator(bass_params_1, style="saw")
    melody_bass_1 = bass_gen_1.render(chords_1, KEY_B_FLAT_MINOR, 96.0)
    bass_notes.extend(melody_bass_1)
    drums_notes.extend(generate_drum_pattern("hard_bop", 96.0, velocity_scale=0.95))
    
    # B. Screaming Organ (96.0 - 288.0)
    chords_2 = _build_chords("i i iv iv " * 12, 192.0, KEY_B_FLAT_MINOR)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_2, base_octave=4, velocity=95, duration_ratio=0.7, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 96.0
    piano_notes.extend(comp_notes)
    
    solo_params_2 = GeneratorParams(density=0.55, key_range_low=36, key_range_high=64)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="shred_guitar", vibrato_depth=0.85)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_B_FLAT_MINOR, 192.0)
    for n in melody_lead_2:
        n.pitch -= 12
        n.start += 96.0
        n.velocity = min(115, n.velocity + 8)
        lead_notes.append(n)
        
    bass_params_2 = GeneratorParams(density=0.72, key_range_low=24, key_range_high=44)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="saw")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_B_FLAT_MINOR, 192.0)
    for n in melody_bass_2:
        n.start += 96.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 96.0, duration=d.duration, velocity=min(127, d.velocity + 8))
        for d in generate_drum_pattern("hard_bop", 192.0, velocity_scale=1.05)
    ])
    
    # C. Bari Fury (288.0 - 576.0)
    chords_3 = _build_chords("i iv v i " * 18, 288.0, KEY_B_FLAT_MINOR)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_3, base_octave=3, velocity=85, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 288.0
    piano_notes.extend(comp_notes)
    
    solo_params_3 = GeneratorParams(density=0.78, key_range_low=36, key_range_high=64)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="shred_guitar", vibrato_depth=0.9)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_B_FLAT_MINOR, 288.0)
    for n in melody_lead_3:
        n.pitch -= 12
        n.start += 288.0
        n.velocity = min(125, n.velocity + 25)
        lead_notes.append(n)
        
    bass_params_3 = GeneratorParams(density=0.8, key_range_low=24, key_range_high=44)
    bass_gen_3 = ModernBass2025Generator(bass_params_3, style="saw")
    melody_bass_3 = bass_gen_3.render(chords_3, KEY_B_FLAT_MINOR, 288.0)
    for n in melody_bass_3:
        n.start += 288.0
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 288.0, duration=d.duration, velocity=min(127, d.velocity + 15))
        for d in generate_drum_pattern("hard_bop", 288.0, velocity_scale=1.15)
    ])
    
    # D. Burnout (576.0 - 781.0)
    chords_4 = _build_chords("i i iv iv " * 12 + "i i i i i ", 205.0, KEY_B_FLAT_MINOR)
    comp_notes, _ = generate_voice_led_comping(chords_4, base_octave=3, velocity=52, prev_voicing=prev_voicing)
    for n in comp_notes:
        n.start += 576.0
    piano_notes.extend(comp_notes)
    
    solo_params_4 = GeneratorParams(density=0.22, key_range_low=36, key_range_high=58)
    solo_gen_4 = SoloMelodyGenerator(solo_params_4, style="modal_ambient", vibrato_depth=0.8)
    melody_lead_4 = solo_gen_4.render(chords_4, KEY_B_FLAT_MINOR, 205.0)
    for n in melody_lead_4:
        n.pitch -= 12
        n.start += 576.0
        n.velocity = 54
        lead_notes.append(n)
        
    bass_params_4 = GeneratorParams(density=0.35, key_range_low=24, key_range_high=40)
    bass_gen_4 = ModernBass2025Generator(bass_params_4, style="saw")
    melody_bass_4 = bass_gen_4.render(chords_4, KEY_B_FLAT_MINOR, 205.0)
    for n in melody_bass_4:
        n.start += 576.0
        n.velocity = 56
        bass_notes.append(n)
    drums_notes.extend([
        NoteInfo(pitch=45, start=i * 2.0 + 576.0, duration=0.4, velocity=48)
        for i in range(int(205.0 / 2.0))
    ])
    
    return {"lead": lead_notes, "piano": piano_notes, "bass": bass_notes, "drums": drums_notes}, 142.0


# 08. Between Worlds
def produce_track_8():
    """Lyrical Tenor Sax, Marimba woody comp, Arco bowed bass, mallets."""
    print("Producing 08. Between Worlds (Tenor Sax + Marimba + Arco Bass)...")
    total_duration = 472.0
    lead_notes = []
    piano_notes = []
    bass_notes = []
    drums_notes = []
    
    # A. Shimmering Gate (0.0 - 64.0)
    chords_1 = _build_chords("i i iv iv " * 4, 64.0, KEY_B_FLAT_MINOR)
    for c in chords_1:
        piano_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=0.3, velocity=48),
            NoteInfo(pitch=c.root + 52, start=c.start + 1.0, duration=0.3, velocity=48),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.02, velocity=45))
    drums_notes.extend([
        NoteInfo(pitch=42, start=i * 2.0 + 0.5, duration=0.1, velocity=38)
        for i in range(int(64.0 / 2.0))
    ])
    
    # B. The Crossing (64.0 - 256.0)
    chords_2 = _build_chords("i i iv iv VI VI i i " * 6, 192.0, KEY_B_FLAT_MINOR)
    solo_params_2 = GeneratorParams(density=0.38, key_range_low=52, key_range_high=74)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="modal_ambient", vibrato_depth=0.7)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_B_FLAT_MINOR, 192.0)
    for n in melody_lead_2:
        n.start += 64.0
        lead_notes.append(n)
        
    for c in chords_2:
        c.start += 64.0
        piano_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start + 0.5, duration=0.3, velocity=56),
            NoteInfo(pitch=c.root + 52, start=c.start + 1.5, duration=0.3, velocity=54),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 1.02, velocity=52))
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 64.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("ambient_brushed", 192.0, velocity_scale=0.85)
    ])
    
    # C. Starlight Dance (256.0 - 384.0)
    chords_3 = _build_chords("VI VII i iv " * 8, 128.0, KEY_B_FLAT_MINOR)
    solo_params_3 = GeneratorParams(density=0.48, key_range_low=52, key_range_high=74)
    solo_gen_3 = SoloMelodyGenerator(solo_params_3, style="modal_ambient", vibrato_depth=0.75)
    melody_lead_3 = solo_gen_3.render(chords_3, KEY_B_FLAT_MINOR, 128.0)
    for n in melody_lead_3:
        n.start += 256.0
        lead_notes.append(n)
        
    for c in chords_3:
        c.start += 256.0
        piano_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=0.25, velocity=65),
            NoteInfo(pitch=c.root + 52, start=c.start + 0.5, duration=0.25, velocity=62),
            NoteInfo(pitch=c.root + 55, start=c.start + 1.0, duration=0.25, velocity=60),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 40, start=c.start, duration=c.duration * 1.05, velocity=58))
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 256.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("ambient_brushed", 128.0, velocity_scale=1.0)
    ])
    
    # D. Dissolving (384.0 - 472.0)
    chords_4 = _build_chords("i i i i " * 5 + "i i ", 88.0, KEY_B_FLAT_MINOR)
    solo_params_4 = GeneratorParams(density=0.2, key_range_low=52, key_range_high=70)
    solo_gen_4 = SoloMelodyGenerator(solo_params_4, style="modal_ambient", vibrato_depth=0.75)
    melody_lead_4 = solo_gen_4.render(chords_4, KEY_B_FLAT_MINOR, 88.0)
    for n in melody_lead_4:
        n.start += 384.0
        n.velocity = 38
        lead_notes.append(n)
        
    for c in chords_4:
        c.start += 384.0
        piano_notes.append(NoteInfo(pitch=c.root + 48, start=c.start + 1.0, duration=0.5, velocity=40))
        bass_notes.append(NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 0.95, velocity=42))
    drums_notes.extend([
        NoteInfo(pitch=42, start=i * 2.0 + 384.0, duration=0.2, velocity=34)
        for i in range(int(88.0 / 2.0))
    ])
    
    return {"lead": lead_notes, "piano": piano_notes, "bass": bass_notes, "drums": drums_notes}, 70.0


# 09. Norns' Thread
def produce_track_9():
    """Solo Piano with complex extensions, Upright bass entering late, soft snare."""
    print("Producing 09. Norns' Thread (Solo Piano fate chords + Late Bass)...")
    total_duration = 314.0
    piano_notes = []
    bass_notes = []
    drums_notes = []
    
    # A. Spinning Silk (0.0 - 130.0 / First 2 Minutes)
    chords_1 = _build_chords("i iv VII III VI ii V i " * 2 + "i iv ", 130.0, KEY_D_MINOR)
    comp_notes, _ = generate_voice_led_comping(chords_1, base_octave=4, velocity=62, duration_ratio=0.95)
    piano_notes.extend(comp_notes)
    
    # B. Tightening Knot (130.0 - 265.0)
    chords_2 = _build_chords("VII III VI ii V i i iv VII III VI ii V i " * 2, 135.0, KEY_D_MINOR)
    comp_notes_2, _ = generate_voice_led_comping(chords_2, base_octave=4, velocity=72, duration_ratio=0.9)
    for n in comp_notes_2:
        n.start += 130.0
    piano_notes.extend(comp_notes_2)
    
    bass_params_2 = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="walking")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_D_MINOR, 135.0)
    for n in melody_bass_2:
        n.start += 130.0
        n.velocity = int(n.velocity * 0.8)
        bass_notes.append(n)
        
    for c in chords_2:
        c.start += 130.0
        
    # C. The Cut (265.0 - 314.0 / Final 45 Seconds)
    chords_3 = _build_chords("i i i i " * 3 + "i ", 49.0, KEY_D_MINOR)
    comp_notes_3, _ = generate_voice_led_comping(chords_3, base_octave=4, velocity=50, duration_ratio=0.95)
    for n in comp_notes_3:
        n.start += 265.0
    piano_notes.extend(comp_notes_3)
    
    for c in chords_3:
        c.start += 265.0
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start, duration=c.duration * 0.95, velocity=42))
    drums_notes.extend([
        NoteInfo(pitch=38, start=i * 1.0 + 265.0 + 0.5, duration=0.1, velocity=25)
        for i in range(49)
    ])
    
    return {"piano": piano_notes, "bass": bass_notes, "drums": drums_notes}, 65.0


# 10. Valkyrie's Return (Outro)
def produce_track_10():
    """Full ensemble homecoming, Rhodes, Upright, Drums, Flugelhorn, Strings. Rhodes fade."""
    print("Producing 10. Valkyrie's Return (Outro / Full Ensemble Homecoming)...")
    total_duration = 264.0
    lead_notes = []
    piano_notes = []
    bass_notes = []
    pad_notes = []
    drums_notes = []
    prev_voicing = None
    
    # A. The Gathering (0.0 - 64.0)
    chords_1 = _build_chords("i v i v " * 4, 64.0, KEY_D_MINOR)
    comp_notes, prev_voicing = generate_voice_led_comping(chords_1, base_octave=4, velocity=60, prev_voicing=prev_voicing)
    piano_notes.extend(comp_notes)
    for c in chords_1:
        pad_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 0.95, velocity=42),
            NoteInfo(pitch=c.root + 55, start=c.start, duration=c.duration * 0.95, velocity=42),
        ])
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start, duration=c.duration * 0.95, velocity=45))
    drums_notes.extend([
        NoteInfo(pitch=38, start=i * 2.0, duration=0.2, velocity=32)
        for i in range(int(64.0 / 2.0))
    ])
    
    # B. Hero's Return (64.0 - 218.0)
    chords_2 = _build_chords("i v i v " * 9 + "i v ", 154.0, KEY_D_MINOR)
    
    # 1. Comping
    comp_notes_2, prev_voicing = generate_voice_led_comping(chords_2, base_octave=4, velocity=76, prev_voicing=prev_voicing)
    for n in comp_notes_2:
        n.start += 64.0
    piano_notes.extend(comp_notes_2)
    
    # 2. Lead solo
    solo_params_2 = GeneratorParams(density=0.45, key_range_low=55, key_range_high=76)
    solo_gen_2 = SoloMelodyGenerator(solo_params_2, style="cinematic_strings", vibrato_depth=0.9)
    melody_lead_2 = solo_gen_2.render(chords_2, KEY_D_MINOR, 154.0)
    for n in melody_lead_2:
        n.start += 64.0
        lead_notes.append(n)
        
    # 3. Bass
    bass_params_2 = GeneratorParams(density=0.55, key_range_low=28, key_range_high=48)
    bass_gen_2 = ModernBass2025Generator(bass_params_2, style="fingerstyle")
    melody_bass_2 = bass_gen_2.render(chords_2, KEY_D_MINOR, 154.0)
    for n in melody_bass_2:
        n.start += 64.0
        bass_notes.append(n)
        
    # 4. Pad & chords shifting
    for c in chords_2:
        c.start += 64.0
        pad_notes.extend([
            NoteInfo(pitch=c.root + 48, start=c.start, duration=c.duration * 1.02, velocity=52),
            NoteInfo(pitch=c.root + 55, start=c.start, duration=c.duration * 1.02, velocity=52),
        ])
        
    # 5. Drums
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 64.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 154.0, velocity_scale=0.95)
    ])
    
    # C. Fade to Silence (218.0 - 264.0 / Final 45 Seconds)
    chords_3 = _build_chords("i v i v " * 2 + "i i ", 46.0, KEY_D_MINOR)
    for c in chords_3:
        c.start += 218.0
        # Rhodes fades out gently from 72 to 10 velocity
        vel = int(72 * (264.0 - c.start) / 46.0)
        vel = max(10, vel)
        # Using voice leading for the fade
        voicing = voice_lead(prev_voicing, c)
        for p in voicing:
            piano_notes.append(NoteInfo(pitch=p, start=c.start, duration=c.duration * 0.95, velocity=vel))
        prev_voicing = voicing
        
    return {"lead": lead_notes, "piano": piano_notes, "bass": bass_notes, "pad": pad_notes, "drums": drums_notes}, 62.0


# ---------------------------------------------------------------------------
# Post-production
# ---------------------------------------------------------------------------

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.88,
        "lead": 0.92,
        "canon_lead": 0.88,
        "bass": 1.12,  # Warm acoustic/upright presence
        "pad": 0.44,
        "drums": 0.70,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)

    # Legato humanization: slightly extend note durations for solos and pad lines
    # to avoid dry gaps between notes, creating smooth transitions.
    for name, notes in mastered.items():
        if name in ["lead", "canon_lead", "pad"]:
            for n in notes:
                n.duration *= 1.08  # 8% sustain bleed to emulate legato articulation

    # Inject high-fidelity spatial controllers section-by-section
    # CC 91: Reverb Send Level (spacious room/hall)
    # CC 93: Chorus Send Level (thickness, stereo spread, warmth)
    spatial_pan = {}
    for name in mastered.keys():
        spatial_pan[name] = list(pan_events.get(name, []))
        
        reverb_val = 0
        chorus_val = 0
        
        if name in ["lead", "canon_lead"]:
            reverb_val = 92   # Wet hall reverb for solo saxophones and horns
            chorus_val = 20   # Tiny chorus for ensemble widening
        elif name == "piano":
            reverb_val = 80   # Lush grand piano/Rhodes space
            chorus_val = 45   # Rich chorus for warm Rhodes & Hammond organ modulation
        elif name == "pad":
            reverb_val = 115  # Celestial, massive room decay for vibraphones & string pads
            chorus_val = 55   # Wide ensemble chorusing
        elif name == "bass":
            reverb_val = 32   # Tiny spatial room reflections for natural bass placement
            chorus_val = 35   # Subtle chorusing for sliding fretless & bowed arco lines
        elif name == "drums":
            reverb_val = 38   # Warm room drum reverb

        if reverb_val > 0:
            spatial_pan[name].append((0.0, 91, reverb_val))
        if chorus_val > 0:
            spatial_pan[name].append((0.0, 93, chorus_val))
            
        # Add dynamic CC automation (LFO-like swells) over time to avoid dryness
        notes = mastered[name]
        if name in ["pad", "canon_lead", "lead"]:
            total_duration = max(n.start + n.duration for n in notes) if notes else 100.0
            beat = 0.0
            while beat < total_duration:
                # CC 11 (Expression) sweeps between 60 and 95
                val = int(77 + 18 * math.sin(beat * 2 * math.pi / 16.0))
                spatial_pan[name].append((beat, 11, val))
                beat += 1.0
                
        if name == "piano":
            total_duration = max(n.start + n.duration for n in notes) if notes else 100.0
            beat = 0.0
            while beat < total_duration:
                # CC 74 (Filter Cutoff) swells for warm texture changes
                val = int(70 + 20 * math.sin(beat * 2 * math.pi / 24.0))
                spatial_pan[name].append((beat, 74, val))
                beat += 2.0

    return mastered, spatial_pan


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    album_dir = Path("output/album_valkyrie_lp2")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   VALKYRIE LP2 — Cinematic Jazz-Noir Masterpiece")
    print("   Scandinavian Mythology x Modern Jazz")
    print("=" * 60 + "\n")

    # 01. Iron Wings
    t1_raw, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-18.0) # ppp
    export_multitrack_midi(
        t1_m, str(album_dir / "01_Iron_Wings.mid"),
        bpm=t1_bpm, cc_events=t1_pan,
        instruments={"piano": 5, "bass": 33, "drums": 117},
    )

    # 02. Chooser of the Slain
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-12.0) # fff
    export_multitrack_midi(
        t2_m, str(album_dir / "02_Chooser_of_the_Slain.mid"),
        bpm=t2_bpm, cc_events=t2_pan,
        instruments={"lead": 67, "piano": 5, "bass": 37, "drums": 117},
    )

    # 03. Mist & Armor
    t3_raw, t3_bpm = produce_track_3()
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-15.0)
    export_multitrack_midi(
        t3_m, str(album_dir / "03_Mist_&_Armor.mid"),
        bpm=t3_bpm, cc_events=t3_pan,
        instruments={"lead": 57, "pad": 12, "bass": 33, "drums": 117},
    )

    # 04. Raven Protocol
    t4_raw, t4_bpm = produce_track_4()
    t4_m, t4_pan = apply_post_production(t4_raw, t4_bpm, lufs=-14.0)
    export_multitrack_midi(
        t4_m, str(album_dir / "04_Raven_Protocol.mid"),
        bpm=t4_bpm, cc_events=t4_pan,
        instruments={"lead": 66, "canon_lead": 65, "piano": 1, "bass": 36, "pad": 91},
    )

    # 05. The Battlefield
    t5_raw, t5_bpm = produce_track_5()
    t5_m, t5_pan = apply_post_production(t5_raw, t5_bpm, lufs=-19.0) # ppp
    export_multitrack_midi(
        t5_m, str(album_dir / "05_The_Battlefield.mid"),
        bpm=t5_bpm, cc_events=t5_pan,
        instruments={"bass": 33, "pad": 81},
    )

    # 06. Valhalla Calling
    t6_raw, t6_bpm = produce_track_6()
    t6_m, t6_pan = apply_post_production(t6_raw, t6_bpm, lufs=-14.0)
    export_multitrack_midi(
        t6_m, str(album_dir / "06_Valhalla_Calling.mid"),
        bpm=t6_bpm, cc_events=t6_pan,
        instruments={"piano": 1, "bass": 33, "lead": 60, "pad": 49, "drums": 117},
    )

    # 07. Winged Fury
    t7_raw, t7_bpm = produce_track_7()
    t7_m, t7_pan = apply_post_production(t7_raw, t7_bpm, lufs=-11.0) # fff organized hammer
    export_multitrack_midi(
        t7_m, str(album_dir / "07_Winged_Fury.mid"),
        bpm=t7_bpm, cc_events=t7_pan,
        instruments={"lead": 68, "piano": 17, "bass": 39, "drums": 117},
    )

    # 08. Between Worlds
    t8_raw, t8_bpm = produce_track_8()
    t8_m, t8_pan = apply_post_production(t8_raw, t8_bpm, lufs=-15.0)
    export_multitrack_midi(
        t8_m, str(album_dir / "08_Between_Worlds.mid"),
        bpm=t8_bpm, cc_events=t8_pan,
        instruments={"lead": 67, "piano": 13, "bass": 41, "drums": 117},
    )

    # 09. Norns' Thread
    t9_raw, t9_bpm = produce_track_9()
    t9_m, t9_pan = apply_post_production(t9_raw, t9_bpm, lufs=-16.0)
    export_multitrack_midi(
        t9_m, str(album_dir / "09_Norns'_Thread.mid"),
        bpm=t9_bpm, cc_events=t9_pan,
        instruments={"piano": 1, "bass": 33, "drums": 117},
    )

    # 10. Valkyrie's Return
    t10_raw, t10_bpm = produce_track_10()
    t10_m, t10_pan = apply_post_production(t10_raw, t10_bpm, lufs=-14.0)
    export_multitrack_midi(
        t10_m, str(album_dir / "10_Valkyrie's_Return.mid"),
        bpm=t10_bpm, cc_events=t10_pan,
        instruments={"lead": 57, "piano": 5, "bass": 33, "pad": 49, "drums": 117},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: VALKYRIE LP2")
    print(f"   MIDI output saved under: {album_dir.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
