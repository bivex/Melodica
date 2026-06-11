import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from melodica.types import NoteInfo
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def print_banner(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def main():
    print_banner("SHORTS AUDIO PIPELINE TRACER: MIXING & MASTERING DIAGNOSTIC")
    
    print("""
[Audio Engine Architecture Review]
1. Mixing Desk (Gain Staging):
   - Applies track-specific gain staging multipliers (e.g. bass, drums, lead).
   - Dynamically scales note velocities.
2. Mastering Desk (LUFS-to-RMS Normalization):
   - Computes combined RMS velocity of all tracks.
   - Maps target LUFS (e.g. -14.0 dB) to target RMS velocity (standard is 86).
   - Calculates a global gain boost factor to hit target loudness (max 5.0x).
3. Multiband Compression:
   - Splits notes into 4 frequency bands: sub, low, mid, high based on pitch.
   - Applies downward compression on velocities exceeding the band thresholds.
4. Limiter:
   - Applies soft-knee limiting at 90% of the ceiling (125), and hard limiting at 125.
5. Stereo Panning:
   - Emits MIDI CC10 events per track based on pan profiles to separate voices.
""")

    # 1. Create mock tracks with realistic velocities
    # Let's create two tracks: 'sax' (midrange melody) and 'vibes' (with low density/velocities)
    raw_tracks = {
        "sax": [
            NoteInfo(pitch=72, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=76, start=1.0, duration=1.0, velocity=82),
            NoteInfo(pitch=79, start=2.0, duration=1.0, velocity=85),
        ],
        "vibes": [
            # Low initial velocities (like SwingGenerator with low density before our fix)
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=6),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=5),
            NoteInfo(pitch=67, start=1.0, duration=0.5, velocity=6),
        ]
    }

    print_banner("STEP 1: RAW TRACK INPUTS")
    for name, notes in raw_tracks.items():
        print(f"Track: '{name}'")
        for i, n in enumerate(notes):
            print(f"  Note {i}: pitch={n.pitch}, start={n.start}, duration={n.duration}, velocity={n.velocity}")

    # 2. Run Mixing Desk
    print_banner("STEP 2: MIXING DESK (GAIN STAGING)")
    desk = MixingDesk()
    # Explicitly configure track gains to show multiplier effect
    desk.track_gains.update({
        "sax": 0.7,
        "vibes": 0.55,
    })
    
    print(f"Track Gain Profiles:")
    print(f"  sax   -> {desk.track_gains['sax']}")
    print(f"  vibes -> {desk.track_gains['vibes']}")
    print()

    mixed_tracks = desk.apply_mixing(raw_tracks, [], bpm=120)
    for name, notes in mixed_tracks.items():
        print(f"Mixed Track: '{name}'")
        for i, n in enumerate(notes):
            orig_vel = raw_tracks[name][i].velocity
            gain = desk.track_gains[name]
            print(f"  Note {i}: raw_vel={orig_vel} * gain={gain} -> mixed_vel={n.velocity}")

    # 3. Run Mastering Desk
    print_banner("STEP 3: MASTERING DESK (LOUDNESS & RMS MAPPING)")
    master = MasteringDesk(target_lufs=-14.0)
    
    target_rms = master.target_rms_velocity
    print(f"Target LUFS: {master.target_lufs}")
    print(f"Target RMS Velocity: {target_rms}")
    
    # Trace the RMS calculation
    all_notes = []
    for tn, notes in mixed_tracks.items():
        all_notes.extend(notes)
    
    overall_rms = master._compute_rms(all_notes)
    global_gain = target_rms / overall_rms if overall_rms > 5 else 1.0
    clamped_gain = min(5.0, max(0.2, global_gain))
    
    print(f"Combined Track Notes Count: {len(all_notes)}")
    print(f"Computed Combined RMS Velocity: {overall_rms:.4f}")
    print(f"Required Loudness Boost Factor: {global_gain:.4f}")
    print(f"Clamped Boost Factor (max 5.0x): {clamped_gain:.4f}")

    # Run the mastering process
    mastered_tracks, pan_events = master.apply_mastering(mixed_tracks)

    # 4. Trace Multiband Compression & Limiting per Note
    print_banner("STEP 4: DETAILED NOTE TRACER (COMPRESSION -> BOOST -> LIMITER)")
    for name, notes in mastered_tracks.items():
        print(f"Track: '{name}' (Boost Factor: {clamped_gain:.4f})")
        for i, n in enumerate(notes):
            mixed_n = mixed_tracks[name][i]
            band = master._split_band(mixed_n.pitch)
            comp_cfg = master.band_compression[band]
            
            # Recreate internal steps
            compressed = master._compress(mixed_n.velocity, band)
            boosted = int(round(compressed * clamped_gain))
            final_vel = master._apply_limiter(boosted)
            
            print(f"  Note {i} (pitch={mixed_n.pitch}, band={band}):")
            print(f"    1. Mixed Velocity: {mixed_n.velocity}")
            print(f"    2. Multiband Compress: threshold={comp_cfg['threshold']}, ratio={comp_cfg['ratio']} -> compressed_vel={compressed}")
            print(f"    3. Apply Global Boost: {compressed} * {clamped_gain:.4f} -> boosted_vel={boosted}")
            print(f"    4. Limiter (ceiling={master.limiter_threshold}): boosted_vel={boosted} -> final_vel={final_vel}")
            print()

    # 5. Stereo Panning Events
    print_banner("STEP 5: STEREO IMAGING (CC10 PAN EVENTS)")
    for name, events in pan_events.items():
        pan_norm = master._get_pan(name)
        print(f"Track: '{name}'")
        print(f"  Pan Profile: {pan_norm:.2f} (-1.0=Left, 0.0=Center, 1.0=Right)")
        for time, cc, val in events:
            print(f"  MIDI Event: beat={time}, CC={cc} (Pan Control), Value={val} (0-127 scale)")

    # 6. Quality Report Summary
    print_banner("STEP 6: MASTERING QUALITY REPORT SUMMARY")
    report = master.quality_report(mastered_tracks)
    for k, v in report.items():
        print(f"  {k:<20}: {v}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
