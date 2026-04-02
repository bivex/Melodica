# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
midi.py — MIDI I/O adapter.

Layer: Infrastructure (adapter)
Port defined by: public signatures only — domain code uses these signatures,
                 never imports mido directly.

Rules:
  - Only this module imports mido.
  - Domain types (Note, NoteInfo, ChordLabel) cross this boundary as plain data.
  - No business logic here; pure translation between domain objects and MIDI bytes.
"""

from __future__ import annotations

from pathlib import Path

import mido

from melodica.types import ChordLabel, Note, NoteInfo, Track


# ---------------------------------------------------------------------------
# GM Instrument Map — track name → GM program number (0-127)
# ---------------------------------------------------------------------------
GM_INSTRUMENTS: dict[str, int] = {
    # Melody / Lead
    "melody": 49,  # String Ensemble 1
    "melody2": 51,  # Synth Strings 1
    "counter": 52,  # Synth Strings 2
    "lead": 80,  # Lead Square
    # Bass
    "bass": 33,  # Electric Bass (finger)
    "walking_bass": 32,  # Acoustic Bass
    "dark_bass": 38,  # Synth Bass 1
    # Chords / Pads
    "chords": 49,  # String Ensemble 1
    "dark_pad": 88,  # New Age Pad
    "ambient": 89,  # Warm Pad
    "pad": 89,  # Warm Pad
    "supersaw_pad": 81,  # Sawtooth Lead
    # Arpeggio
    "arp": 46,  # Harp
    "harp_gliss": 46,  # Harp
    # Percussion
    "percussion": 0,  # Channel 10 for drums
    # Other
    "ostinato": 45,  # Pizzicato Strings
    "dyads": 46,  # Harp
    "riff": 30,  # Overdriven Guitar
    "fingerpicking": 25,  # Nylon Guitar
    "piano_sweep": 0,  # Acoustic Grand Piano
    "call_response": 49,  # String Ensemble 1
    "groove": 45,  # Pizzicato Strings
    "swing": 45,  # Pizzicato Strings
    "choir": 52,  # Synth Choir
    "tremolo": 44,  # Tremolo Strings
    "staccato": 45,  # Pizzicato Strings
    "canon": 49,  # String Ensemble 1
    "strum": 25,  # Nylon Guitar
    "neural_melody": 54,  # Synth Voice
}


# ---------------------------------------------------------------------------
# Default instrument maps per style
# ---------------------------------------------------------------------------
STYLE_INSTRUMENTS: dict[str, dict[str, int]] = {
    "downtempo": {
        "melody": 88,  # New Age Pad (soft)
        "melody2": 54,  # Synth Voice
        "counter": 89,  # Warm Pad
        "walking_bass": 32,  # Acoustic Bass
        "dark_bass": 38,  # Synth Bass 1
        "chords": 88,  # New Age Pad
        "dark_pad": 92,  # Halo Pad
        "ambient": 89,  # Warm Pad
        "arp": 46,  # Harp
        "ostinato": 45,  # Pizzicato Strings
        "dyads": 46,  # Harp
        "fingerpicking": 25,  # Nylon Guitar
        "percussion": 0,  # Drums
        "groove": 45,  # Pizzicato Strings
        "swing": 45,  # Pizzicato Strings
        "call_response": 49,  # String Ensemble 1
    },
    "dark_fantasy": {
        "melody": 49,  # String Ensemble 1
        "melody2": 52,  # Synth Strings 2
        "counter": 51,  # Synth Strings 1
        "bass": 43,  # Contrabass
        "chords": 48,  # String Ensemble 2
        "dark_pad": 88,  # New Age Pad
        "ambient": 91,  # Sweep Pad
        "arp": 46,  # Harp
        "harp_gliss": 46,  # Harp
        "ostinato": 45,  # Pizzicato Strings
        "dyads": 46,  # Harp
        "riff": 30,  # Overdriven Guitar
        "fingerpicking": 25,  # Nylon Guitar
        "percussion": 0,  # Drums
        "groove": 45,  # Pizzicato Strings
        "call_response": 49,  # String Ensemble 1
        "canon": 49,  # String Ensemble 1
        "piano_sweep": 0,  # Acoustic Grand Piano
        "choir": 52,  # Synth Choir
        "tremolo": 44,  # Tremolo Strings
        "staccato": 45,  # Pizzicato Strings
        "strum": 25,  # Nylon Guitar
    },
}
from melodica.theory import Mode
from melodica.utils import chord_pitches_closed, chord_pitches_open, chord_pitches_spread


# ---------------------------------------------------------------------------
# Key signature helpers
# ---------------------------------------------------------------------------

_MAJOR_KEY_SIG = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}
_MINOR_KEY_SIG = {
    0: "Cm",
    1: "C#m",
    2: "Dm",
    3: "Ebm",
    4: "Em",
    5: "Fm",
    6: "F#m",
    7: "Gm",
    8: "G#m",
    9: "Am",
    10: "Bbm",
    11: "Bm",
}
_MINOR_MODES = frozenset(
    {
        Mode.NATURAL_MINOR,
        Mode.HARMONIC_MINOR,
        Mode.MELODIC_MINOR,
        Mode.DORIAN,
        Mode.PHRYGIAN,
        Mode.LOCRIAN,
    }
)


def _scale_to_key_sig(scale: "Scale") -> str:
    """Return a mido key_signature string for a Scale (e.g. 'Ebm', 'F#')."""
    if scale.mode in _MINOR_MODES:
        return _MINOR_KEY_SIG[scale.root]
    return _MAJOR_KEY_SIG[scale.root]


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def from_midi(path: str | Path, track: int | None = None) -> list[Note]:
    """
    Parse a MIDI file and return notes from a track.
    If track is None, search for the first track containing notes.
    """
    mid = mido.MidiFile(path)
    if track is not None:
        return _extract_notes(mid, track)

    # Auto-find first non-empty track
    for i in range(len(mid.tracks)):
        notes = _extract_notes(mid, i)
        if notes:
            return notes
    return []


def from_midi_bytes(data: bytes, track: int = 0) -> list[Note]:
    """
    Parse MIDI from raw bytes.
    Useful for in-memory round-trips and tests.
    """
    import io

    mid = mido.MidiFile(file=io.BytesIO(data))
    return _extract_notes(mid, track)


def _extract_notes(mid: mido.MidiFile, track_index: int) -> list[Note]:
    tpb = mid.ticks_per_beat
    if track_index >= len(mid.tracks):
        raise IndexError(
            f"Track index {track_index} out of range (file has {len(mid.tracks)} tracks)"
        )
    track = mid.tracks[track_index]

    notes: list[Note] = []
    pending: dict[int, tuple[float, int]] = {}  # pitch → (start_beat, velocity)
    current_tick = 0

    for msg in track:
        current_tick += msg.time
        beat = current_tick / tpb

        if msg.type == "note_on" and msg.velocity > 0:
            pending[msg.note] = (beat, msg.velocity)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in pending:
                start_beat, velocity = pending.pop(msg.note)
                duration = max(beat - start_beat, 1 / tpb)
                notes.append(
                    Note(
                        pitch=msg.note,
                        start=start_beat,
                        duration=duration,
                        velocity=velocity,
                        channel=getattr(msg, "channel", 0),
                    )
                )

    # Close any notes that never received note_off (edge case)
    last_beat = current_tick / tpb
    for pitch, (start_beat, velocity) in pending.items():
        notes.append(
            Note(
                pitch=pitch,
                start=start_beat,
                duration=max(last_beat - start_beat, 0.25),
                velocity=velocity,
            )
        )

    return sorted(notes, key=lambda n: n.start)


# ---------------------------------------------------------------------------
# Write — NoteInfo list (from generators / Idea Tool)
# ---------------------------------------------------------------------------


def notes_to_midi(
    notes: list[NoteInfo],
    path: str | Path,
    *,
    bpm: float = 120.0,
) -> None:
    """
    Write a single list of NoteInfo objects to a single-track MIDI file.
    """
    export_multitrack_midi({"Track 1": notes}, path, bpm=bpm)


def export_multitrack_midi(
    tracks_data: dict[str, list[NoteInfo]],
    path: str | Path,
    *,
    bpm: float = 120.0,
    key: "Scale | str | None" = None,
    time_sig: tuple[int, int] = (4, 4),
    timeline: "MusicTimeline | None" = None,
    cc_events: "dict[str, list[tuple[float, int, int]]] | None" = None,
    instruments: "dict[str, int] | None" = None,
) -> None:
    """
    Write multiple tracks to a Type 1 MIDI file.
    tracks_data: { "Bass": [NoteInfo...], "Melody": [NoteInfo...] }

    key: Scale object or string like "Am", "C" — writes key signature meta event.
    time_sig: (numerator, denominator) — writes time signature meta event.
    timeline: MusicTimeline — full timeline with key/time-signature changes and markers.
    cc_events: { "TrackName": [(beat, cc_num, cc_val), ...] } — standalone CC events.
    instruments: { "TrackName": gm_program_number } — GM instrument per track.
        Default: 0 (Acoustic Grand Piano). Keys not found default to 0.
    """
    from melodica.types import TICKS_PER_BEAT, MIDI_MAX

    tpb = TICKS_PER_BEAT
    tempo = mido.bpm2tempo(bpm)
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)

    # 1. Global Meta Track
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    meta_track.append(mido.MetaMessage("track_name", name="Global", time=0))

    if timeline is not None:
        # Full timeline: key changes, time-signature changes, markers
        meta_events: list[tuple[int, mido.MetaMessage]] = []
        for kl in timeline.keys:
            tick = round(kl.start * tpb)
            key_str = _scale_to_key_sig(kl.scale)
            meta_events.append((tick, mido.MetaMessage("key_signature", key=key_str, time=0)))
        for ts in timeline.time_signatures:
            tick = round(ts.start * tpb)
            meta_events.append(
                (
                    tick,
                    mido.MetaMessage(
                        "time_signature",
                        numerator=ts.numerator,
                        denominator=ts.denominator,
                        time=0,
                    ),
                )
            )
        for m in timeline.markers:
            tick = round(m.start * tpb)
            meta_events.append((tick, mido.MetaMessage("marker", text=m.text, time=0)))
        meta_events.sort(key=lambda x: x[0])
        last_tick = 0
        for tick, msg in meta_events:
            msg.time = max(0, tick - last_tick)
            meta_track.append(msg)
            last_tick = tick
    else:
        # Simple key + time signature
        if key is not None:
            key_str = key if isinstance(key, str) else _scale_to_key_sig(key)
            meta_track.append(mido.MetaMessage("key_signature", key=key_str, time=0))
        meta_track.append(
            mido.MetaMessage(
                "time_signature",
                numerator=time_sig[0],
                denominator=time_sig[1],
                time=0,
            )
        )

    # 2. Add individual tracks
    for i, (name, notes) in enumerate(tracks_data.items()):
        if i >= 16:
            break  # MIDI limit

        channel = i

        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name, time=0))

        # Program change: use instruments map if provided, else default to 0
        program = (instruments or {}).get(name, 0)
        tr.append(mido.Message("program_change", program=program, channel=channel, time=0))

        # Build all events: note_on, note_off, control_change, pitchwheel
        events: list[tuple[int, str, int, int]] = []
        for n in notes:
            onset = max(0.0, n.start)
            on_tick = round(onset * tpb)
            off_tick = round((onset + n.duration) * tpb)

            # Note on/off
            events.append((on_tick, "note_on", n.pitch, n.velocity))
            events.append((off_tick, "note_off", n.pitch, 0))

            # CC and pitchwheel events from note.expression
            if n.expression:
                for cc_num, cc_val in n.expression.items():
                    if isinstance(cc_num, int) and 0 <= cc_num <= 127:
                        events.append((on_tick, "control_change", cc_num, max(0, min(127, cc_val))))
                    elif cc_num == "pitch_bend":
                        bend = max(-8192, min(8191, int(cc_val)))
                        events.append((on_tick, "pitchwheel", bend, 0))

        # Standalone CC events (e.g. sustain pedal boundaries)
        if cc_events and name in cc_events:
            for beat, cc_num, cc_val in cc_events[name]:
                tick = round(max(0.0, beat) * tpb)
                events.append((tick, "control_change", cc_num, max(0, min(127, cc_val))))

        # Sort: control_change before note_off before note_on at same tick; pitchwheel before note_on
        type_order = {"pitchwheel": 0, "control_change": 1, "note_off": 2, "note_on": 3}
        events.sort(key=lambda e: (e[0], type_order.get(e[1], 4)))

        prev_tick = 0
        for tick, msg_type, data1, data2 in events:
            delta = max(0, tick - prev_tick)
            if msg_type == "control_change":
                tr.append(
                    mido.Message(
                        "control_change",
                        control=int(data1),
                        value=int(data2),
                        time=delta,
                        channel=channel,
                    )
                )
            elif msg_type == "pitchwheel":
                tr.append(mido.Message("pitchwheel", pitch=int(data1), time=delta, channel=channel))
            else:
                tr.append(
                    mido.Message(
                        msg_type,
                        note=int(data1),
                        velocity=int(data2),
                        time=delta,
                        channel=channel,
                    )
                )
            prev_tick = tick

    if isinstance(path, (str, Path)):
        mid.save(path)
    else:
        mid._save(path)


def export_midi(
    tracks: list[Track],
    path: str | Path,
    *,
    bpm: float = 120.0,
    timeline: "MusicTimeline" | None = None,
) -> None:
    """
    Write a list of high-level Track objects to a MIDI file.
    Respects track.name, track.channel, track.program, and track.volume.
    """
    from melodica.types import TICKS_PER_BEAT

    tpb = TICKS_PER_BEAT
    tempo = mido.bpm2tempo(bpm)
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)

    # 1. Global Meta Track
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    meta_track.append(mido.MetaMessage("track_name", name="Global", time=0))

    if timeline:
        # Collect all meta events as (abs_tick, MetaMessage)
        meta_events: list[tuple[int, mido.MetaMessage]] = []

        # 1a. Key Signatures — one per key region
        for kl in timeline.keys:
            tick = round(kl.start * tpb)
            key_str = _scale_to_key_sig(kl.scale)
            meta_events.append((tick, mido.MetaMessage("key_signature", key=key_str, time=0)))

        # 1b. Time Signatures
        for ts in timeline.time_signatures:
            tick = round(ts.start * tpb)
            meta_events.append(
                (
                    tick,
                    mido.MetaMessage(
                        "time_signature",
                        numerator=ts.numerator,
                        denominator=ts.denominator,
                        time=0,
                    ),
                )
            )

        # 1c. Section Markers
        for m in timeline.markers:
            tick = round(m.start * tpb)
            meta_events.append((tick, mido.MetaMessage("marker", text=m.text, time=0)))

        # Sort by absolute tick, then write with delta times
        meta_events.sort(key=lambda x: x[0])
        last_tick = 0
        for tick, msg in meta_events:
            msg.time = max(0, tick - last_tick)
            meta_track.append(msg)
            last_tick = tick

    # 2. Individual Tracks
    for i, t in enumerate(tracks):
        if i >= 16:
            break

        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=t.name, time=0))
        if t.instrument_name:
            tr.append(mido.MetaMessage("instrument_name", name=t.instrument_name, time=0))

        # Program Change (instrument selection)
        tr.append(mido.Message("program_change", program=t.program, channel=t.channel, time=0))

        # CC 7  — Channel Volume (static mix level — do not automate)
        tr.append(
            mido.Message("control_change", control=7, value=t.volume, channel=t.channel, time=0)
        )
        # CC 10 — Pan
        tr.append(
            mido.Message("control_change", control=10, value=t.pan, channel=t.channel, time=0)
        )
        # CC 11 — Expression (dynamic shaping within volume)
        tr.append(
            mido.Message(
                "control_change", control=11, value=t.expression, channel=t.channel, time=0
            )
        )
        # CC 1  — Modulation (vibrato depth; 0 = off at start, shaped by automation)
        tr.append(
            mido.Message("control_change", control=1, value=t.modulation, channel=t.channel, time=0)
        )
        # CC 73 — Attack Time
        tr.append(
            mido.Message("control_change", control=73, value=t.attack, channel=t.channel, time=0)
        )
        # CC 72 — Release Time
        tr.append(
            mido.Message("control_change", control=72, value=t.release, channel=t.channel, time=0)
        )
        # CC 74 is NOT written here — apply_articulation provides per-note CC74.
        # Writing it here would conflict with articulation-driven brightness.
        # CC 91 — Reverb Send
        tr.append(
            mido.Message("control_change", control=91, value=t.reverb, channel=t.channel, time=0)
        )
        # CC 93 — Chorus Send
        tr.append(
            mido.Message("control_change", control=93, value=t.chorus, channel=t.channel, time=0)
        )
        # CC 3  — Vibrato depth (0=off at start; automation/apply_articulation shapes it)
        tr.append(
            mido.Message("control_change", control=3, value=t.vibrato, channel=t.channel, time=0)
        )
        # CC 64 — Sustain Pedal / Articulation Trigger
        tr.append(
            mido.Message(
                "control_change", control=64, value=t.sustain_pedal, channel=t.channel, time=0
            )
        )

        # RPN 0x0000 — Pitch Bend Range (semitones)
        # Protocol: CC101=0, CC100=0 selects the parameter; CC6=semitones, CC38=cents
        tr.append(mido.Message("control_change", control=101, value=0, channel=t.channel, time=0))
        tr.append(mido.Message("control_change", control=100, value=0, channel=t.channel, time=0))
        tr.append(
            mido.Message(
                "control_change", control=6, value=t.pitch_bend_range, channel=t.channel, time=0
            )
        )
        tr.append(mido.Message("control_change", control=38, value=0, channel=t.channel, time=0))
        # Null RPN — deselect active parameter to prevent accidental CC6 overrides later
        tr.append(mido.Message("control_change", control=101, value=127, channel=t.channel, time=0))
        tr.append(mido.Message("control_change", control=100, value=127, channel=t.channel, time=0))

        # Build relative events
        events: list[tuple[int, str, int, int]] = []
        for n in t.notes:
            onset = max(0.0, n.start)
            on_tick = round(onset * tpb)
            off_tick = round((onset + n.duration) * tpb)

            # Emit Expression (CC) data
            for cc_num, cc_val in n.expression.items():
                if cc_num == "pitch_bend":
                    events.append((on_tick, "pitchwheel", cc_val, 0))  # val2 ignored for pitchwheel
                else:
                    events.append((on_tick, "control_change", cc_num, cc_val))

            events.append((on_tick, "note_on", n.pitch, n.velocity))
            events.append((off_tick, "note_off", n.pitch, 0))

        events.sort(key=lambda e: (e[0], 0 if e[1] == "note_off" else 1))

        # Keyswitch events: 1-tick note_on/note_off at the specified beat positions
        for ks_beat, ks_pitch in t.keyswitch_events:
            ks_tick = round(ks_beat * tpb)
            events.append((ks_tick, "note_on", ks_pitch, 64))
            events.append((ks_tick + 1, "note_off", ks_pitch, 0))
        # Re-sort after adding keyswitches
        events.sort(key=lambda e: (e[0], 0 if e[1] == "note_off" else 1))

        prev_tick = 0
        for tick, msg_type, val1, val2 in events:
            delta = max(0, tick - prev_tick)
            if msg_type == "control_change":
                tr.append(
                    mido.Message(
                        "control_change",
                        control=int(val1),
                        value=int(val2),
                        time=delta,
                        channel=t.channel,
                    )
                )
            elif msg_type == "pitchwheel":
                tr.append(
                    mido.Message("pitchwheel", pitch=int(val1), time=delta, channel=t.channel)
                )
            else:
                tr.append(
                    mido.Message(
                        msg_type, note=int(val1), velocity=int(val2), time=delta, channel=t.channel
                    )
                )
            prev_tick = tick

    if isinstance(path, (str, Path)):
        mid.save(path)
    else:
        # mido.MidiFile.save() tries to open() strings; for buffers we use _save()
        mid._save(path)


# ---------------------------------------------------------------------------
# Write — ChordLabel list (as block chords)
# ---------------------------------------------------------------------------

_VOICING_FN = {
    "closed": chord_pitches_closed,
    "open": chord_pitches_open,
    "spread": chord_pitches_spread,
}


def chords_to_midi(
    chords: list[ChordLabel],
    path: str | Path,
    *,
    bpm: float = 120.0,
    velocity: int = 80,
    voicing: str = "closed",
) -> None:
    """
    Write chord labels as block notes (all tones simultaneous) to a MIDI file.

    voicing: "closed" | "open" | "spread"
    """
    if voicing not in _VOICING_FN:
        raise ValueError(f"voicing must be one of {list(_VOICING_FN)}; got {voicing!r}")

    voicing_fn = _VOICING_FN[voicing]
    note_infos: list[NoteInfo] = []

    for chord in chords:
        pitches = voicing_fn(chord)
        for pitch in pitches:
            note_infos.append(
                NoteInfo(
                    pitch=pitch,
                    start=chord.start,
                    duration=chord.duration,
                    velocity=velocity,
                )
            )

    notes_to_midi(note_infos, path, bpm=bpm)
