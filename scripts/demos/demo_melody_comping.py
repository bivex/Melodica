# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
demo_melody_comping.py — Single-Song Album Demo.

This script demonstrates the interaction between:
1. The **Main Solo Melody** (using SoloMelodyGenerator with multiple styles: vocal_mimic, jazz_fusion, modal_ambient)
2. The **Chord Accompaniment** (using generate_voice_led_comping with voice_lead and jazz extensions)
3. The **Bassline** (using ModernBass2025Generator sync'd to the chords)
4. The **Drum groove** (swing_brushed and hard_bop patterns)

It serves as a perfect showcase of the chord-melody-accompaniment coordination engine.
"""

import math
import random
from pathlib import Path

from melodica import types
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.rhythm import get_rhythm
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.theory.chords import Quality
from melodica.theory.voicing import voice_lead, chord_to_notes

# Keys & Scale Setup
KEY_D_MINOR = Scale(root=2, mode=Mode.AEOLIAN)       # D minor (Aeolian)
KEY_D_DORIAN = Scale(root=2, mode=Mode.DORIAN)       # D Dorian

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
        c.extensions = orig_ext
        
    return notes, prev_voicing

def generate_drum_pattern(style: str, duration: float) -> list[NoteInfo]:
    """
    Advanced humanized and phrase-aware drum pattern generator.
    Implements:
    - Micro-timing micro-delays (laid-back / behind the beat lazy feel)
    - Dynamic timing jitter (random deviation to emulate touch)
    - Dynamic velocity variations (human stroke velocity emulation)
    - Phrase-aware structural transitions (automatic drum fills at phrase boundaries)
    """
    notes = []
    t = 0.0
    
    # Humanization parameters
    timing_jitter = 0.008      # Max random timing deviation in beats (~10ms)
    velocity_jitter = 6        # Random velocity deviation range (+/-)
    laid_back_delay = 0.015    # Lazy jazz feel (delays snare and ride/hats slightly)
    
    def add_hit(pitch, start_beat, note_dur, base_vel, is_ride_or_hat=False, is_snare=False):
        # 1. Apply laid-back micro-delays
        offset = 0.0
        if is_snare:
            offset += laid_back_delay
        elif is_ride_or_hat:
            offset += laid_back_delay * 0.5
            
        # 2. Add random human jitter
        offset += random.uniform(-timing_jitter, timing_jitter)
        final_start = max(0.0, start_beat + offset)
        
        # 3. Add random velocity jitter
        final_vel = int(base_vel + random.randint(-velocity_jitter, velocity_jitter))
        final_vel = max(1, min(127, final_vel))
        
        notes.append(NoteInfo(
            pitch=pitch, 
            start=round(final_start, 6), 
            duration=round(note_dur, 6), 
            velocity=final_vel
        ))

    if style == "swing_brushed":
        while t < duration:
            # Detect phrase end boundary (last 2 beats of an 8-bar section, i.e., every 16 beats)
            is_phrase_end = (t % 16.0 >= 14.0) and (t + 2.0 <= duration)
            
            if is_phrase_end:
                # Play a beautiful soft drum fill: snare roll swelling in volume
                fill_offsets = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]
                for off in fill_offsets:
                    vel = int(35 + 25 * (off / 2.0))
                    add_hit(38, t + off, 0.12, vel, is_snare=True)
                # Crash cymbal on next downbeat
                add_hit(49, t + 2.0, 1.5, 80)
            else:
                # Brushed snare (pitch 38) swing tap
                add_hit(38, t, 0.15, 45, is_snare=True)
                add_hit(38, t + 0.66, 0.1, 30, is_snare=True)
                add_hit(38, t + 1.0, 0.15, 40, is_snare=True)
                add_hit(38, t + 1.66, 0.1, 30, is_snare=True)
                
                # Soft kick drum (pitch 36) on 1 and 3
                add_hit(36, t, 0.2, 50)
                add_hit(36, t + 1.0, 0.2, 48)
                
                # Hi-hat foot (pitch 44) on 2 and 4
                add_hit(44, t + 0.5, 0.15, 55, is_ride_or_hat=True)
                add_hit(44, t + 1.5, 0.15, 55, is_ride_or_hat=True)
            t += 2.0
            
    elif style == "hard_bop":
        while t < duration:
            # Detect phrase end boundary (last 2 beats of an 8-bar section, i.e., every 16 beats)
            is_phrase_end = (t % 16.0 >= 14.0) and (t + 2.0 <= duration)
            
            if is_phrase_end:
                # Energetic hard bop fill: tom cascades + snare roll
                add_hit(38, t, 0.12, 75, is_snare=True)
                add_hit(38, t + 0.25, 0.12, 85, is_snare=True)
                # High tom (pitch 50)
                add_hit(50, t + 0.5, 0.15, 80)
                add_hit(50, t + 0.75, 0.15, 85)
                # Floor tom (pitch 41)
                add_hit(41, t + 1.0, 0.18, 90)
                add_hit(41, t + 1.25, 0.18, 95)
                # Snare accents
                add_hit(38, t + 1.5, 0.12, 110, is_snare=True)
                add_hit(38, t + 1.75, 0.12, 115, is_snare=True)
                # Downbeat crash (pitch 49)
                add_hit(49, t + 2.0, 2.0, 105)
            else:
                # Ride cymbal (pitch 51) active bop
                add_hit(51, t, 0.2, 68, is_ride_or_hat=True)
                add_hit(51, t + 0.5, 0.15, 55, is_ride_or_hat=True)
                add_hit(51, t + 0.66, 0.12, 72, is_ride_or_hat=True)
                add_hit(51, t + 1.0, 0.2, 65, is_ride_or_hat=True)
                add_hit(51, t + 1.5, 0.15, 58, is_ride_or_hat=True)
                add_hit(51, t + 1.66, 0.12, 75, is_ride_or_hat=True)
                
                # Snare comps (pitch 38) on offbeats
                if random.random() < 0.45:
                    add_hit(38, t + 0.33, 0.1, 60, is_snare=True)
                if random.random() < 0.45:
                    add_hit(38, t + 1.25, 0.1, 62, is_snare=True)
                    
                # Hi-hat pedal on 2 and 4
                add_hit(44, t + 0.5, 0.1, 65, is_ride_or_hat=True)
                add_hit(44, t + 1.5, 0.1, 65, is_ride_or_hat=True)
            t += 2.0
            
    notes.sort(key=lambda n: n.start)
    return notes

def produce_demo_track():
    """
    Produces a showcase song "Harmony & Fire" with explicit sections:
    - Section A: Intro (0 - 16 beats) -> Pure voice-led chord accompaniment (D minor), no melody.
    - Section B: Verse (16 - 48 beats) -> Lyrical vocal-style melody (vocal_mimic) + comping + walking bass + swing brushes.
    - Section C: Bridge (48 - 80 beats) -> Fast Jazz Fusion solo melody + B3 Organ comping + electric slap bass + hard bop drums.
    - Section D: Outro (80 - 96 beats) -> Soft ambient modal sax solo + fading Rhodes comping + simple slow bass.
    """
    print("Producing Demo Track: 'Harmony & Fire'...")
    lead_notes = []
    counter_notes = []
    piano_notes = []
    bass_notes = []
    drums_notes = []
    prev_voicing = None
    
    # -----------------------------------------------------------------------
    # Section A: Intro (0.0 - 16.0)
    # -----------------------------------------------------------------------
    print("  - Section A: Intro (Pure voice-led comping, no melody)")
    chords_A = _build_chords("i iv VII III i iv V i", 16.0, KEY_D_MINOR)
    # Generate clean voice-led chords with extensions
    comp_A, prev_voicing = generate_voice_led_comping(
        chords_A, base_octave=4, velocity=60, prev_voicing=prev_voicing
    )
    piano_notes.extend(comp_A)
    # Simple low roots on bass
    for c in chords_A:
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start, duration=c.duration * 0.95, velocity=45))
    # Ambient brushed drums
    drums_notes.extend(generate_drum_pattern("swing_brushed", 16.0))

    # -----------------------------------------------------------------------
    # Section B: Verse (16.0 - 48.0)
    # -----------------------------------------------------------------------
    print("  - Section B: Verse (Lyrical vocal_mimic solo melody + countermelody + comping + walking bass)")
    chords_B = _build_chords("i iv VII III VI ii V i " * 2, 32.0, KEY_D_MINOR)
    
    # Render comping chords locally, then shift
    comp_B, prev_voicing = generate_voice_led_comping(
        chords_B, base_octave=4, velocity=65, prev_voicing=prev_voicing
    )
    for n in comp_B:
        n.start += 16.0
    piano_notes.extend(comp_B)
    
    # Soulful, syncopated jazz hook in D minor pentatonic
    hook_pitches = [69, 72, 74, 72, 69]       # A4, C5, D5, C5, A4
    hook_rhythm_ratio = [0.75, 0.25, 1.0, 0.5, 0.5] # Dotted quarter, sixteenth, quarter, eighth, eighth
    rhythm_motif = [1.5, 0.5, 1.0, 1.0]        # guides structural rhythms outside hook

    # Solo Melody: Lyrical, motif-driven vocal mimic style
    solo_params_B = GeneratorParams(density=0.40, complexity=0.6, key_range_low=58, key_range_high=78)
    solo_gen_B = MelodyGenerator(
        solo_params_B,
        phrase_length=8.0,              # 2-bar call-and-response phrase boundaries
        phrase_contour="arch",          # lyrical arch phrasing
        motif_probability=0.8,          # high chance of reusing/varying hook motif
        harmony_note_probability=0.75,  # smooth chord-tone flow
        drama_shape="tension_release",             # gentle expressive dynamics
        ornament_probability=0.25,      # rich vocal/sax grace notes and turns
        syncopation=0.2,                # swing syncopation
        base_motif=hook_pitches,
        base_motif_rhythm=hook_rhythm_ratio,
        rhythm_motif=rhythm_motif,
    )
    # Render with local chords, then shift note start times
    melody_B = solo_gen_B.render(chords_B, KEY_D_MINOR, 32.0)
    
    # Countermelody: Swing style counterpoint against melody_B
    counter_params_B = GeneratorParams(density=0.35, key_range_low=50, key_range_high=68, complexity=0.5)
    counter_rhythm_B = get_rhythm("markov:swing", syncopation=0.25, seed=42)
    counter_gen_B = CountermelodyGenerator(
        counter_params_B,
        primary_melody=melody_B,
        motion_preference="mixed",
        rhythm=counter_rhythm_B
    )
    counter_B = counter_gen_B.render(chords_B, KEY_D_MINOR, 32.0)
    
    for n in melody_B:
        n.start += 16.0
        lead_notes.append(n)
        
    for n in counter_B:
        n.start += 16.0
        counter_notes.append(n)
        
    # Walking Bassline
    bass_params_B = GeneratorParams(density=0.6, key_range_low=28, key_range_high=48)
    bass_gen_B = ModernBass2025Generator(bass_params_B, style="walking")
    melody_bass_B = bass_gen_B.render(chords_B, KEY_D_MINOR, 32.0)
    for n in melody_bass_B:
        n.start += 16.0
        bass_notes.append(n)
        
    # Swing brushes
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 16.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("swing_brushed", 32.0)
    ])

    # -----------------------------------------------------------------------
    # Section C: Bridge (48.0 - 80.0)
    # -----------------------------------------------------------------------
    print("  - Section C: Bridge (High-energy jazz_fusion solo + contrary countermelody + B3 Organ comping + Slap Bass)")
    # Modulate to Dorian for bright energy
    chords_C = _build_chords("i i iv iv VI VI i i " * 2, 32.0, KEY_D_DORIAN)
    
    # Hammond B3 Organ chords (higher velocity, shorter ratio for staccato comping)
    comp_C, prev_voicing = generate_voice_led_comping(
        chords_C, base_octave=4, velocity=85, duration_ratio=0.6, prev_voicing=prev_voicing
    )
    for n in comp_C:
        n.start += 48.0
    piano_notes.extend(comp_C)
    
    # Solo Melody: Fast Jazz Fusion style (virtuoso, syncopated runs with epic peak drama)
    solo_params_C = GeneratorParams(density=0.65, complexity=0.8, key_range_low=55, key_range_high=80)
    solo_gen_C = MelodyGenerator(
        solo_params_C,
        phrase_length=4.0,              # rapid, shorter phrases
        phrase_contour="rise",          # intense upward climbing register
        motif_probability=0.6,          # balanced motivic sequences
        harmony_note_probability=0.68,  # coloristic extensions & scale runs
        steps_probability=0.6,          # fluid cascading runs
        drama_shape="epic",             # epic building late climax with subdivisions accelerando
        syncopation=0.3,                # heavy syncopation
    )
    melody_C = solo_gen_C.render(chords_C, KEY_D_DORIAN, 32.0)
    
    # Countermelody: Active contrary motion counterpoint against melody_C
    counter_params_C = GeneratorParams(density=0.5, key_range_low=48, key_range_high=65, complexity=0.6)
    counter_rhythm_C = get_rhythm("markov:swing", syncopation=0.3, seed=43)
    counter_gen_C = CountermelodyGenerator(
        counter_params_C,
        primary_melody=melody_C,
        motion_preference="contrary",
        rhythm=counter_rhythm_C
    )
    counter_C = counter_gen_C.render(chords_C, KEY_D_DORIAN, 32.0)
    
    for n in melody_C:
        n.start += 48.0
        n.velocity = min(115, n.velocity + 15)  # Make the solo pierce through
        lead_notes.append(n)
        
    for n in counter_C:
        n.start += 48.0
        counter_notes.append(n)
        
    # Slap Bassline
    bass_params_C = GeneratorParams(density=0.72, key_range_low=28, key_range_high=48)
    bass_gen_C = ModernBass2025Generator(bass_params_C, style="slap")
    melody_bass_C = bass_gen_C.render(chords_C, KEY_D_DORIAN, 32.0)
    for n in melody_bass_C:
        n.start += 48.0
        bass_notes.append(n)
        
    # Hard Bop aggressive drums
    drums_notes.extend([
        NoteInfo(pitch=d.pitch, start=d.start + 48.0, duration=d.duration, velocity=d.velocity)
        for d in generate_drum_pattern("hard_bop", 32.0)
    ])

    # -----------------------------------------------------------------------
    # Section D: Outro (80.0 - 96.0)
    # -----------------------------------------------------------------------
    print("  - Section D: Outro (Ambient modal_ambient solo sax + oblique countermelody + fading comping)")
    chords_D = _build_chords("i i iv iv V V i i", 16.0, KEY_D_MINOR)
    
    # Comping Rhodes fades out gently from 70 to 15 velocity
    for c in chords_D:
        c.start += 80.0
    for c in chords_D:
        vel = int(70 * (96.0 - c.start) / 16.0)
        vel = max(15, vel)
        voicing = voice_lead(prev_voicing, c)
        for p in voicing:
            piano_notes.append(NoteInfo(
                pitch=p, start=c.start, duration=c.duration * 0.95, velocity=vel
            ))
        prev_voicing = voicing
        
    # Restore chords_D to local temporarily to render solo melody, then shift
    for c in chords_D:
        c.start -= 80.0
    solo_params_D = GeneratorParams(density=0.25, key_range_low=58, key_range_high=72)
    solo_gen_D = MelodyGenerator(
        solo_params_D,
        phrase_length=16.0,             # extremely wide, spacious phrasing
        phrase_contour="flat",          # flat register for drone vibe
        motif_probability=0.4,          # spacious modal wandering
        harmony_note_probability=0.8,   # very stable drone scale steps
        phrase_rest_probability=0.4,    # lets the trumpet breathe and fade away
        ornament_probability=0.15,      # simple closing ornaments
    )
    melody_D = solo_gen_D.render(chords_D, KEY_D_MINOR, 16.0)
    
    # Countermelody: Oblique holding voice for spacious closing outro
    counter_params_D = GeneratorParams(density=0.2, key_range_low=50, key_range_high=68, complexity=0.3)
    counter_rhythm_D = get_rhythm("markov:ballad", syncopation=0.1, seed=44)
    counter_gen_D = CountermelodyGenerator(
        counter_params_D,
        primary_melody=melody_D,
        motion_preference="oblique",
        rhythm=counter_rhythm_D
    )
    counter_D = counter_gen_D.render(chords_D, KEY_D_MINOR, 16.0)
    
    for n in melody_D:
        n.start += 80.0
        n.velocity = 45  # Quiet closing solo
        lead_notes.append(n)
        
    for n in counter_D:
        n.start += 80.0
        n.velocity = 40  # Quiet countermelody
        counter_notes.append(n)
        
    # Bass fades out slowly
    for c in chords_D:
        c.start += 80.0
        bass_notes.append(NoteInfo(pitch=c.root + 28, start=c.start, duration=c.duration * 1.0, velocity=35))
        
    # Minimal drum closing cymbal
    drums_notes.append(NoteInfo(pitch=51, start=80.0, duration=3.0, velocity=35))

    raw_tracks = {
        "lead": lead_notes,
        "counter": counter_notes,
        "piano": piano_notes,
        "bass": bass_notes,
        "drums": drums_notes
    }
    return raw_tracks, 85.0  # Song is in 85 BPM

def apply_post_production(raw_tracks, bpm, lufs=-14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.88,
        "lead": 0.92,
        "counter": 0.86,  # Perfectly balanced counter-lead volume
        "bass": 1.10,
        "drums": 0.70,
    })

    mixed = desk.apply_mixing(raw_tracks, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    mastered, pan_events = master.apply_mastering(mixed)

    # Legato humanization: slightly extend note durations for solo lead and counter tracks
    for name, notes in mastered.items():
        if name in ("lead", "counter"):
            for n in notes:
                n.duration *= 1.08  # 8% sustain bleed to emulate legato articulation

    # Spatial configuration
    spatial_pan = {}
    for name in mastered.keys():
        spatial_pan[name] = list(pan_events.get(name, []))
        
        reverb_val = 0
        chorus_val = 0
        
        if name == "lead":
            reverb_val = 90   # Warm hall reverb for the main solo melody
            chorus_val = 20
        elif name == "counter":
            reverb_val = 95   # Deep rich reverb for the counter-melody (e.g. Alto Sax)
            chorus_val = 25
        elif name == "piano":
            reverb_val = 80   # Spacious Grand Piano/Rhodes
            chorus_val = 40   # Chorus widening
        elif name == "bass":
            reverb_val = 30
            chorus_val = 25
        elif name == "drums":
            reverb_val = 38

        if reverb_val > 0:
            spatial_pan[name].append((0.0, 91, reverb_val))
        if chorus_val > 0:
            spatial_pan[name].append((0.0, 93, chorus_val))
            
        # Add dynamic CC automation (expression and cutoff filter sweeps) over time
        notes = mastered[name]
        if name in ("lead", "counter"):
            total_duration = max(n.start + n.duration for n in notes) if notes else 100.0
            beat = 0.0
            phase_offset = 0.0 if name == "lead" else math.pi  # Out of phase for independent breathing!
            while beat < total_duration:
                # CC 11 expression breathing swell
                val = int(77 + 15 * math.sin(beat * 2 * math.pi / 8.0 + phase_offset))
                spatial_pan[name].append((beat, 11, val))
                beat += 1.0
                
        if name == "piano":
            total_duration = max(n.start + n.duration for n in notes) if notes else 100.0
            beat = 0.0
            while beat < total_duration:
                # CC 74 filter cutoff swelling for keyboard warmth
                val = int(70 + 20 * math.sin(beat * 2 * math.pi / 16.0))
                spatial_pan[name].append((beat, 74, val))
                beat += 2.0

    return mastered, spatial_pan

def main():
    demo_dir = Path("output/demo_melody_comping")
    demo_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   MELODY & ACCOMPANIMENT COORDINATION DEMO")
    print("   Showcasing Interaction of Solo Melody + Countermelody + Comp Chords + Bass")
    print("=" * 60 + "\n")

    t_raw, t_bpm = produce_demo_track()
    t_m, t_pan = apply_post_production(t_raw, t_bpm, lufs=-14.0)
    
    export_multitrack_midi(
        t_m, str(demo_dir / "01_Harmony_&_Fire.mid"),
        bpm=t_bpm, cc_events=t_pan,
        instruments={"lead": 57, "counter": 65, "piano": 5, "bass": 33, "drums": 117},
    )

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: DEMO SONG")
    print(f"   MIDI output saved under: {demo_dir.resolve()}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
