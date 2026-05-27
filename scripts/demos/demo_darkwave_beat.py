"""Dark wave beat — 140 BPM, Phrygian, proper drums + bass + synths."""

import os
import mido
from melodica import Scale, Mode
from melodica.types import parse_progression, NoteInfo, TICKS_PER_BEAT
from melodica.generators.melody import MelodyGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators import GeneratorParams
from melodica.midi import export_multitrack_midi

OUT = "output/melody_demos"
os.makedirs(OUT, exist_ok=True)

# D Phrygian — one of the darkest keys
KEY = Scale(root=2, mode=Mode.PHRYGIAN)
BPM = 140
BARS = 8
DUR = BARS * 4.0  # 32 beats

# GM drums on channel 10 (9)
KICK = 36
SNARE = 38
HH_C = 42
HH_O = 46
CLAP = 39
CRASH = 49
RIDE = 51
RIM = 37

# GM instruments
SYNTH_BASS = 38   # Synth Bass 1
LEAD_SAW = 81     # Lead 2 (sawtooth)
DARK_PAD = 92     # Halo Pad
ATMOS = 99        # Atmosphere


# ---- Progressions ----
chords = parse_progression("i bvII bIII iv v bVI bvII i", KEY)


def make_drums():
    """Darkwave drum pattern — 140 BPM four-on-the-floor with dark feel."""
    notes = []

    for bar in range(BARS):
        bs = bar * 4.0  # bar start

        # Kick: four on the floor, but bar 1 of every 4 has a fill
        for beat in range(4):
            onset = bs + beat
            vel = 110 if beat % 2 == 0 else 100
            notes.append(NoteInfo(pitch=KICK, start=onset, duration=0.25, velocity=vel))
            # Ghost kick on "and" of beats 1,3
            if beat in (0, 2) and bar % 2 == 0:
                notes.append(NoteInfo(pitch=KICK, start=onset + 0.5, duration=0.15, velocity=70))

        # Snare/clap: beats 2 and 4, plus occasional ghost
        for beat in (1, 3):
            onset = bs + beat
            notes.append(NoteInfo(pitch=SNARE, start=onset, duration=0.2, velocity=105))
            notes.append(NoteInfo(pitch=CLAP, start=onset, duration=0.12, velocity=80))
        # Ghost snare on "and" of beat 4 every other bar
        if bar % 2 == 1:
            notes.append(NoteInfo(pitch=SNARE, start=bs + 3.5, duration=0.12, velocity=55))

        # Hi-hats: 8th notes, with occasional 16th stutter
        for i in range(8):
            onset = bs + i * 0.5
            is_open = (i == 3 or i == 7) and bar % 4 != 3
            if is_open:
                notes.append(NoteInfo(pitch=HH_O, start=onset, duration=0.3, velocity=60))
            else:
                vel = 65 if i % 2 == 0 else 50
                notes.append(NoteInfo(pitch=HH_C, start=onset, duration=0.1, velocity=vel))

        # 16th hat burst in last bar
        if bar == BARS - 1:
            for i in range(4):
                onset = bs + 3.75 + i * 0.0625
                notes.append(NoteInfo(pitch=HH_C, start=onset, duration=0.05, velocity=75))

        # Crash on bar 1, 5
        if bar % 4 == 0:
            notes.append(NoteInfo(pitch=CRASH, start=bs, duration=1.0, velocity=85))

        # Rim click on beat 3 of even bars (subtle)
        if bar % 2 == 0:
            notes.append(NoteInfo(pitch=RIM, start=bs + 2.0, duration=0.1, velocity=50))

    return notes


def make_darkwave_beat():
    """Build full darkwave track with drums on channel 10."""
    tracks = {}
    instruments = {}

    # Drums
    tracks["Drums"] = make_drums()

    # Dark bass: industrial pulse — octave=2 gives D2+ range
    tracks["Bass"] = DarkBassGenerator(
        GeneratorParams(density=0.55, key_range_low=30, key_range_high=46),
        mode="dark_pulse", octave=2, note_duration=1.0,
        velocity_level=0.75, movement="root_fifth",
    ).render(chords, KEY, DUR)
    instruments["Bass"] = SYNTH_BASS

    # Lead melody: Phrygian, spiraling, dark
    tracks["Lead"] = MelodyGenerator(
        GeneratorParams(density=0.50, key_range_low=60, key_range_high=80),
        phrase_contour="spiral", direction_bias=-0.1,
        motif_probability=0.55, syncopation=0.30,
        rhythm_variety=0.50, harmony_note_probability=0.50,
        ornament_probability=0.06,
    ).render(chords, KEY, DUR)
    instruments["Lead"] = LEAD_SAW

    # Dark pad: Phrygian texture
    tracks["Pad"] = DarkPadGenerator(
        GeneratorParams(density=0.20, key_range_low=36, key_range_high=60),
        mode="phrygian_pad", chord_dur=4.0,
        velocity_level=0.30, register="low", overlap=0.4,
    ).render(chords, KEY, DUR)
    instruments["Pad"] = DARK_PAD

    # Atmosphere layer
    tracks["Atmo"] = MelodyGenerator(
        GeneratorParams(density=0.15, key_range_low=48, key_range_high=72),
        harmony_note_probability=0.90, random_movement=0.10,
        note_repetition_probability=0.35, rhythm_variety=0.05,
    ).render(chords, KEY, DUR)
    instruments["Atmo"] = ATMOS

    # Write with drums on channel 10
    path = os.path.join(OUT, "darkwave_beat_140.mid")
    _export_with_drums(tracks, path, bpm=BPM, instruments=instruments, drum_track="Drums")
    print(f"  darkwave beat: {len(tracks)} tracks, {len(tracks['Drums'])} drum hits -> {path}")


def _export_with_drums(tracks_data, path, *, bpm, instruments, drum_track="Drums"):
    """Export MIDI with the drum track forced to channel 10 (9)."""
    tempo = mido.bpm2tempo(bpm)
    tpb = TICKS_PER_BEAT
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)

    # Meta track
    meta = mido.MidiTrack()
    mid.tracks.append(meta)
    meta.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    meta.append(mido.MetaMessage("track_name", name="Global", time=0))

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
    print(f"Dark wave beat — {BPM} BPM, D Phrygian, {BARS} bars")
    make_darkwave_beat()
    print("Done.")
