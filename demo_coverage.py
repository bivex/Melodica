import os
from pathlib import Path

from melodica import types
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.generators import GeneratorParams

from melodica.composer.album_pipeline import produce_track, Mood, _sidechain_duck, _generate_entry_fades, _generate_delay_sends, _compute_tension
from melodica.composer.automation import AutomationCurve
from melodica.composer.non_chord_tones import NonChordToneGenerator
from melodica.composer.phrase_memory import PhraseMemory, Phrase, Transform
from melodica.composer.tension_curve import TensionCurve
from melodica.composer.voice_leading import VoiceLeadingEngine
from melodica.composer.harmonic_awareness import guide_tone_resolution, weight_pitch, chord_tone_pcs, best_chord_tone
from melodica.composer.harmonic_verifier import detect_clashes, detect_parallel_fifths, verify_and_fix, VerifierConfig, detect_voice_crossing, detect_spacing_errors
from melodica.composer.transition_coordinator import TransitionCoordinator
from melodica.composer.style_profiles import StyleProfile
from melodica.composer.candidate_scorer import CandidateScorer, ScoringContext
from melodica.composer.diagnostics import diagnose_tracks
from melodica.composer.texture_controller import TextureController, TextureLevel
from melodica.composer.articulations import ArticulationEngine

def run_demo():
    print("Starting maximized coverage test...")
    
    # 1. Setup Scales and Progressions
    KEY = types.Scale(root=0, mode=types.Mode.NATURAL_MINOR)
    # Using more exotic chords to trigger harmonic awareness logic
    chords = types.parse_progression("i:4.0 - VI:4.0 - iv:4.0 - V7:4.0 - bVII:4.0", KEY)
    
    full_chords = []
    dur = 20.0
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # 2. Voice Leading
    print("Testing VoiceLeadingEngine...")
    vle = VoiceLeadingEngine(strict_mode=True, max_voice_gap=10)
    voiced_tracks = vle.voicize_progression(full_chords, KEY)

    # 3. Candidate Scorer
    print("Testing CandidateScorer...")
    scorer = CandidateScorer()
    ctx = ScoringContext(chord_root=full_chords[0].root, chord_quality=full_chords[0].quality, scale_pcs=KEY.degrees())
    score = scorer.score(60, ctx)
    from melodica.types import NoteInfo
    scorer.pick_best_note([NoteInfo(60, 0, 1), NoteInfo(62, 0, 1), NoteInfo(64, 0, 1)], ctx)

    # 4. Non-Chord Tones
    print("Testing NonChordToneGenerator...")
    nct_gen = NonChordToneGenerator(passing_prob=1.0, neighbor_prob=1.0, suspension_prob=1.0)
    soprano_with_nct = nct_gen.add_non_chord_tones(voiced_tracks["soprano"], full_chords, KEY)
    pedal = nct_gen.add_pedal_point(full_chords, KEY, duration_beats=4.0)

    # 5. Phrase Memory
    print("Testing PhraseMemory...")
    memory = PhraseMemory()
    memory.store(Phrase(notes=tuple(soprano_with_nct), section="test", tag="main"))
    recalled_inversion = memory.recall(transform="inversion", transpose=1)
    recalled_retro = memory.recall(transform="retrograde", transpose=2)
    recalled_aug = memory.recall(transform="augmentation")
    recalled_dim = memory.recall(transform="diminution")
    memory.recall_as_new_sequence(transform="original", start_at=10.0)
    memory.find_similar(Phrase(notes=tuple(soprano_with_nct)))

    # 6. Tension Curve
    print("Testing TensionCurve...")
    curves = ["classical", "edm", "ambient", "build_release"]
    for c_type in curves:
        curve = TensionCurve(total_beats=dur, curve_type=c_type)
        t_points = curve.generate()
        curve.tension_at(2.5)
        curve.phase_at(2.5)

    # 7. Harmonic Verifier
    print("Testing HarmonicVerifier...")
    clashes = detect_clashes({"soprano": soprano_with_nct, "bass": voiced_tracks["bass"]}, VerifierConfig())
    parallels = detect_parallel_fifths(voiced_tracks)
    detect_voice_crossing(voiced_tracks)
    detect_spacing_errors(voiced_tracks)
    fixed_tracks, report = verify_and_fix({"soprano": soprano_with_nct, "bass": voiced_tracks["bass"]}, VerifierConfig())

    # 8. Harmonic Awareness
    print("Testing Harmonic Awareness...")
    w = weight_pitch(60, 0, types.Quality.MAJOR, beat_strength=1.0)
    pcs = chord_tone_pcs(0, types.Quality.MAJOR)
    res = best_chord_tone(61, 0, types.Quality.MAJOR)

    # 9. Transitions & Automation
    print("Testing Transitions and Automation...")
    cc_events = {}
    TransitionCoordinator.apply_ducking({"bass": voiced_tracks["bass"]}, ["bass"], 0.0, 4.0, duck_factor=0.5)
    TransitionCoordinator.apply_sweeps({"bass": voiced_tracks["bass"]}, cc_events, ["bass"], 11, 0, 127, 0.0, 4.0, curve_type="linear")
    TransitionCoordinator.apply_sweeps({"bass": voiced_tracks["bass"]}, cc_events, ["bass"], 11, 0, 127, 0.0, 4.0, curve_type="sine")
    
    # Try all automations
    AutomationCurve.exponential(11, 0, 127, 0.0, 4.0, exponent=2.0)

    # 10. Texture Controller
    print("Testing Texture Controller...")
    texture = TextureController(base_texture=TextureLevel.THIN)
    tracks_for_texture = {"melody": soprano_with_nct, "bass": voiced_tracks["bass"]}
    texture.apply_texture(tracks_for_texture, dur)

    # 11. Articulations
    print("Testing Articulations...")
    ae = ArticulationEngine()
    ae.apply(soprano_with_nct, "staccato", dur)
    ae.add_sustain_pedal_events(voiced_tracks["bass"], 4.0)

    # 12. Diagnostics
    print("Testing Diagnostics...")
    diagnostics_report = diagnose_tracks(tracks_for_texture)

    # 13. Album Pipeline (Full rendering, mixing, mastering, psychoacoustics)
    print("Testing Album Pipeline & Psychoacoustics with specific names for effects...")
    
    # Add fake percussion and echo tracks to trigger sidechain and delay sends
    piano = ArpeggiatorGenerator(GeneratorParams(density=0.8, velocity_range=(60, 80), key_range_low=48, key_range_high=72), pattern="up_down").render(full_chords, KEY, dur)
    pad = AmbientPadGenerator(GeneratorParams(density=0.5, velocity_range=(40, 60), key_range_low=48, key_range_high=72)).render(full_chords, KEY, dur)
    bass = BassGenerator(GeneratorParams(density=0.5, velocity_range=(70, 90), key_range_low=24, key_range_high=36)).render(full_chords, KEY, dur)
    perc = RhythmicAccentGenerator(preset="gallop", pitch=36).render(full_chords, KEY, dur)
    
    # Force extreme polyphony to trigger the limiter
    heavy_chords = StringsEnsembleGenerator(GeneratorParams(density=1.0, velocity_range=(80, 100), key_range_low=36, key_range_high=84)).render(full_chords, KEY, dur)

    out_dir = Path("output/coverage_demo")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    produce_track(
        tracks={
            "piano_echo": piano, 
            "pad": pad, 
            "bass": bass, 
            "melody": recalled_inversion,
            "drum": perc,
            "heavy": heavy_chords
        },
        bpm=120,
        instruments={"piano_echo": 0, "pad": 88, "bass": 32, "melody": 73, "drum": 115, "heavy": 48},
        path=out_dir / "coverage_test.mid",
        mood=Mood.CINEMATIC,
        key=KEY,
        chords=full_chords
    )
    
    print("Coverage Demo completed successfully!")

if __name__ == "__main__":
    run_demo()
