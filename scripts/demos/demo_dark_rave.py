"""Dark rave — 2 minutes, structured sections, D Phrygian, 140 BPM."""

import os
import mido
from melodica import Scale, Mode
from melodica.types import parse_progression, NoteInfo, TICKS_PER_BEAT
from melodica.generators.melody import MelodyGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators import GeneratorParams
from melodica.midi import export_multitrack_midi
from melodica.utils import chord_at

OUT = "output/melody_demos"
os.makedirs(OUT, exist_ok=True)

KEY = Scale(root=2, mode=Mode.PHRYGIAN)  # D Phrygian
BPM = 140

# GM drums
KICK = 36; SNARE = 38; HH_C = 42; HH_O = 46
CLAP = 39; CRASH = 49; RIDE = 51; RIM = 37

# GM instruments
SYNTH_BASS = 38; LEAD_SAW = 81; DARK_PAD = 92
ATMOS = 99; LEAD_SQ = 80; PAD_WARM = 90

# ---- Structure ----
# Intro (8 bars) → Build (8 bars) → Drop (16 bars) → Breakdown (8 bars) → Drop2 (8 bars) → Outro (4 bars)
# Total: 52 bars = 208 beats ≈ 1:29 at 140 BPM
# Extend to ~64 bars for ~2:00

SECTIONS = [
    ("intro",      8),   # sparse: pad + atmo + rim only
    ("build",      8),   # add kick, bass, hats growing
    ("drop1",     16),   # full energy: all elements
    ("breakdown",  8),   # strip back: pad + lead + sparse drums
    ("drop2",     16),   # full energy, different progression
    ("outro",      8),   # fade: bass + pad + diminishing drums
]
TOTAL_BARS = sum(bars for _, bars in SECTIONS)
TOTAL_BEATS = TOTAL_BARS * 4.0

# Progressions
prog_main = parse_progression("i bvII bIII iv v bVI bvII i", KEY)
prog_drop2 = parse_progression("i bvII bvII i iv v bvII i", KEY)
prog_full = (prog_main * 2 + prog_drop2 * 2) * 6  # enough for all sections


def _bar_onset(section_idx):
    """Get beat offset for section start."""
    offset = 0
    for i in range(section_idx):
        offset += SECTIONS[i][1] * 4.0
    return offset


# ---- Drums per section ----
def drums_intro(start, bars):
    notes = []
    for bar in range(bars):
        bs = start + bar * 4.0
        # Just rim on beat 1, soft
        notes.append(NoteInfo(pitch=RIM, start=bs, duration=0.1, velocity=45))
        if bar % 2 == 1:
            notes.append(NoteInfo(pitch=RIM, start=bs + 2.0, duration=0.1, velocity=35))
    return notes


def drums_build(start, bars):
    notes = []
    for bar in range(bars):
        bs = start + bar * 4.0
        # Kick starts on bar 4 of build
        if bar >= 4:
            for beat in range(4):
                notes.append(NoteInfo(pitch=KICK, start=bs + beat, duration=0.25,
                                      velocity=90 + bar * 3))
        # Hats from bar 2, increasing density
        if bar >= 2:
            for i in range(4 + min(bar, 4)):
                onset = bs + i * (4.0 / (4 + min(bar, 4)))
                notes.append(NoteInfo(pitch=HH_C, start=onset, duration=0.1, velocity=40 + bar * 4))
        # Snare on 2+4 from bar 6
        if bar >= 6:
            for beat in (1, 3):
                notes.append(NoteInfo(pitch=SNARE, start=bs + beat, duration=0.2, velocity=85))
        # Crash on bar 4
        if bar == 4:
            notes.append(NoteInfo(pitch=CRASH, start=bs, duration=1.5, velocity=80))
    return notes


def drums_drop(start, bars, energy=1.0):
    notes = []
    for bar in range(bars):
        bs = start + bar * 4.0
        # Four on the floor kick
        for beat in range(4):
            vel = int(110 * energy)
            notes.append(NoteInfo(pitch=KICK, start=bs + beat, duration=0.25, velocity=vel))
            # Ghost kick on "and" of 1,3
            if beat in (0, 2) and bar % 2 == 0:
                notes.append(NoteInfo(pitch=KICK, start=bs + beat + 0.5, duration=0.15,
                                      velocity=int(65 * energy)))
        # Snare + clap on 2, 4
        for beat in (1, 3):
            notes.append(NoteInfo(pitch=SNARE, start=bs + beat, duration=0.2,
                                  velocity=int(105 * energy)))
            notes.append(NoteInfo(pitch=CLAP, start=bs + beat, duration=0.12,
                                  velocity=int(75 * energy)))
        # 8th hats with open on offbeats
        for i in range(8):
            onset = bs + i * 0.5
            if i in (3, 7):
                notes.append(NoteInfo(pitch=HH_O, start=onset, duration=0.3,
                                      velocity=int(55 * energy)))
            else:
                vel = int((60 if i % 2 == 0 else 45) * energy)
                notes.append(NoteInfo(pitch=HH_C, start=onset, duration=0.1, velocity=vel))
        # Ride layer on offbeat quarter notes every other bar
        if bar % 2 == 1:
            for beat in (0, 2):
                notes.append(NoteInfo(pitch=RIDE, start=bs + beat + 0.5, duration=0.3,
                                      velocity=int(40 * energy)))
        # Fill on last 2 bars
        if bar >= bars - 2:
            for i in range(4):
                notes.append(NoteInfo(pitch=SNARE, start=bs + 3.0 + i * 0.25, duration=0.1,
                                      velocity=int(80 * energy)))
        # Crash every 4 bars
        if bar % 4 == 0:
            notes.append(NoteInfo(pitch=CRASH, start=bs, duration=1.0, velocity=int(85 * energy)))
    return notes


def drums_breakdown(start, bars):
    notes = []
    for bar in range(bars):
        bs = start + bar * 4.0
        # Sparse: kick on 1, rim on 3, very light hats
        notes.append(NoteInfo(pitch=KICK, start=bs, duration=0.25, velocity=70))
        notes.append(NoteInfo(pitch=RIM, start=bs + 2.0, duration=0.1, velocity=45))
        if bar % 2 == 0:
            notes.append(NoteInfo(pitch=HH_O, start=bs + 1.0, duration=0.5, velocity=35))
            notes.append(NoteInfo(pitch=HH_O, start=bs + 3.0, duration=0.5, velocity=35))
    return notes


def drums_outro(start, bars):
    notes = []
    for bar in range(bars):
        bs = start + bar * 4.0
        fade = 1.0 - bar / bars  # fade out
        if bar < bars - 2:
            notes.append(NoteInfo(pitch=KICK, start=bs, duration=0.25,
                                  velocity=int(80 * fade)))
        if bar < bars // 2:
            for i in range(0, 8, 2):  # sparse hats
                notes.append(NoteInfo(pitch=HH_C, start=bs + i * 0.5, duration=0.1,
                                      velocity=int(40 * fade)))
    return notes


def make_dark_rave():
    all_drums = []
    all_bass = []
    all_lead = []
    all_pad = []
    all_atmo = []
    all_lead2 = []

    for si, (name, bars) in enumerate(SECTIONS):
        offset = _bar_onset(si)
        dur = bars * 4.0

        # Drums
        if name == "intro":
            all_drums.extend(drums_intro(offset, bars))
        elif name == "build":
            all_drums.extend(drums_build(offset, bars))
        elif name in ("drop1", "drop2"):
            all_drums.extend(drums_drop(offset, bars, energy=1.0))
        elif name == "breakdown":
            all_drums.extend(drums_breakdown(offset, bars))
        elif name == "outro":
            all_drums.extend(drums_outro(offset, bars))

        # Bass: not in intro, light in build/breakdown, full in drops
        if name in ("drop1", "drop2", "outro"):
            bass = DarkBassGenerator(
                GeneratorParams(density=0.6, key_range_low=30, key_range_high=46),
                mode="dark_pulse", octave=2, note_duration=1.0,
                velocity_level=0.80 if "drop" in name else 0.50,
                movement="root_fifth",
            ).render(prog_full, KEY, dur)
            for n in bass:
                all_bass.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                         duration=n.duration, velocity=n.velocity))

        elif name == "build" and bars > 4:
            # Bass comes in at bar 4 of build
            bass = DarkBassGenerator(
                GeneratorParams(density=0.5, key_range_low=30, key_range_high=46),
                mode="dark_pulse", octave=2, note_duration=1.0,
                velocity_level=0.60, movement="root_fifth",
            ).render(prog_full, KEY, (bars - 4) * 4.0)
            for n in bass:
                all_bass.append(NoteInfo(pitch=n.pitch, start=n.start + offset + 16.0,
                                         duration=n.duration, velocity=n.velocity))

        elif name == "breakdown":
            bass = DarkBassGenerator(
                GeneratorParams(density=0.3, key_range_low=34, key_range_high=46),
                mode="doom", octave=2, note_duration=4.0,
                velocity_level=0.40, movement="root_only",
            ).render(prog_full, KEY, dur)
            for n in bass:
                all_bass.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                         duration=n.duration, velocity=n.velocity))

        # Pad: all sections, varying intensity
        pad_mode = "phrygian_pad" if name in ("intro", "breakdown") else "minor_pad"
        pad_vel = {"intro": 0.20, "build": 0.28, "drop1": 0.35, "breakdown": 0.25,
                   "drop2": 0.38, "outro": 0.18}[name]
        pad = DarkPadGenerator(
            GeneratorParams(density=0.2, key_range_low=36, key_range_high=60),
            mode=pad_mode, chord_dur=4.0, velocity_level=pad_vel,
            register="low" if name in ("intro", "outro") else "mid", overlap=0.4,
        ).render(prog_full, KEY, dur)
        for n in pad:
            all_pad.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                    duration=n.duration, velocity=n.velocity))

        # Lead melody: not in intro, sparse in build, full in drops, ethereal in breakdown
        if name in ("build", "drop1", "drop2", "breakdown"):
            density = {"build": 0.35, "drop1": 0.55, "drop2": 0.60, "breakdown": 0.30}[name]
            lead = MelodyGenerator(
                GeneratorParams(density=density, key_range_low=60, key_range_high=80),
                phrase_contour="spiral" if "drop" in name else "wave",
                direction_bias=-0.1,
                motif_probability=0.55, syncopation=0.30,
                rhythm_variety=0.50, harmony_note_probability=0.50,
                ornament_probability=0.06,
            ).render(prog_full, KEY, dur)
            for n in lead:
                all_lead.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                         duration=n.duration, velocity=n.velocity))

        # Lead 2 (counter): drops only, higher register
        if name in ("drop1", "drop2"):
            lead2 = MelodyGenerator(
                GeneratorParams(density=0.40, key_range_low=67, key_range_high=88),
                phrase_contour="wave", direction_bias=0.05,
                motif_probability=0.45, syncopation=0.35,
                rhythm_variety=0.45, harmony_note_probability=0.55,
            ).render(prog_full, KEY, dur)
            for n in lead2:
                all_lead2.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                          duration=n.duration, velocity=n.velocity))

        # Atmosphere: intro + breakdown + outro
        if name in ("intro", "breakdown", "outro"):
            atmo = MelodyGenerator(
                GeneratorParams(density=0.12, key_range_low=48, key_range_high=72),
                harmony_note_probability=0.90, random_movement=0.10,
                note_repetition_probability=0.35, rhythm_variety=0.05,
            ).render(prog_full, KEY, dur)
            for n in atmo:
                all_atmo.append(NoteInfo(pitch=n.pitch, start=n.start + offset,
                                         duration=n.duration, velocity=n.velocity))

    # Assemble
    tracks = {"Drums": all_drums, "Bass": all_bass, "Lead": all_lead,
              "Lead 2": all_lead2, "Pad": all_pad, "Atmo": all_atmo}
    instruments = {"Bass": SYNTH_BASS, "Lead": LEAD_SAW, "Lead 2": LEAD_SQ,
                   "Pad": DARK_PAD, "Atmo": ATMOS}

    path = os.path.join(OUT, "dark_rave_140.mid")
    _export_with_drums(tracks, path, bpm=BPM, instruments=instruments, drum_track="Drums")

    total_sec = TOTAL_BEATS / BPM * 60
    print(f"  dark rave: {TOTAL_BARS} bars ({total_sec:.0f}s), {len(all_drums)} drums, "
          f"{len(all_bass)} bass, {len(all_lead)}+{len(all_lead2)} lead, "
          f"{len(all_pad)} pad, {len(all_atmo)} atmo -> {path}")


def _export_with_drums(tracks_data, path, *, bpm, instruments, drum_track="Drums"):
    tempo = mido.bpm2tempo(bpm)
    tpb = TICKS_PER_BEAT
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)

    meta = mido.MidiTrack()
    mid.tracks.append(meta)
    meta.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    meta.append(mido.MetaMessage("track_name", name="Global", time=0))

    # Section markers
    for si, (name, bars) in enumerate(SECTIONS):
        tick = round(_bar_onset(si) * tpb)
        meta.append(mido.MetaMessage("marker", text=name.upper(), time=tick))

    for i, (name, notes) in enumerate(tracks_data.items()):
        is_drums = (name == drum_track)
        channel = 9 if is_drums else min(i, 15)

        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name, time=0))

        if not is_drums:
            program = (instruments or {}).get(name, 0)
            tr.append(mido.Message("program_change", program=program, channel=channel, time=0))

        events = []
        for n in notes:
            on_tick = round(max(0.0, n.start) * tpb)
            off_tick = round((max(0.0, n.start) + n.duration) * tpb)
            events.append((on_tick, "note_on", n.pitch, n.velocity))
            events.append((off_tick, "note_off", n.pitch, 0))

        events.sort(key=lambda e: (e[0], 1 if e[1] == "note_off" else 2))

        prev_tick = 0
        for tick, msg_type, pitch, vel in events:
            delta = max(0, tick - prev_tick)
            tr.append(mido.Message(msg_type, note=pitch, velocity=vel, time=delta, channel=channel))
            prev_tick = tick

    mid.save(path)


if __name__ == "__main__":
    print(f"Dark Rave — {BPM} BPM, D Phrygian")
    make_dark_rave()
    print("Done.")
