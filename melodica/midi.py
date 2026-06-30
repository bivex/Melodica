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
from typing import TYPE_CHECKING

import math
import random

import mido  # type: ignore

from melodica.types import ChordLabel, Note, NoteInfo, Track, Scale, MusicTimeline

if TYPE_CHECKING:
    from melodica.form import MusicalForm


# ---------------------------------------------------------------------------
# GM Instrument Map — track name → GM program number (0-127)
# ---------------------------------------------------------------------------
GM_INSTRUMENTS: dict[str, int] = {
    # Standard
    "piano": 0,
    "bright_piano": 1,
    "electric_piano": 4,
    "harpsichord": 6,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "organ": 19,
    "accordion": 21,
    "harmonica": 22,
    "nylon_guitar": 24,
    "guitar": 25,
    "steel_guitar": 25,
    "jazz_guitar": 26,
    "electric_guitar": 27,
    "muted_guitar": 28,
    "overdrive_guitar": 29,
    "distortion_guitar": 30,
    "acoustic_bass": 32,
    "bass": 33,
    "electric_bass": 34,
    "fretless_bass": 35,
    "slap_bass": 36,
    "synth_bass": 38,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_strings": 44,
    "pizzicato": 45,
    "harp": 46,
    "timpani": 47,
    "strings": 48,
    "choir": 52,
    "voice": 54,
    "synth_voice": 54,
    "orchestra_hit": 55,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "french_horn": 60,
    "brass": 61,
    "synth_brass": 62,
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    "synth_lead": 80,
    "pad": 89,
    "dark_pad": 88,
    "synth_fx": 102,
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    "tinkle_bell": 112,
    "steel_drums": 114,
    "taiko": 116,
    "drums": 0,
    "percussion": 0,
}


# ---------------------------------------------------------------------------
# Style Instrument Overrides — per-style GM program overrides
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
# MATHEMATICAL GUARANTEE AGAINST PITCH BEND CLIPPING
# ---------------------------------------------------------------------------
# When exporting microtonal notes (e.g., quarter-tones or neutral intervals):
# 1. Any fractional note pitch P is rounded to the nearest integer semitone:
#    R = round(P)
# 2. This guarantees that the fractional deviation D = P - R is strictly bounded:
#    |D| <= 0.5 semitones (50 cents).
# 3. Our MIDI track RPN initialization establishes a Pitch Bend Range of ±B semitones,
#    where B >= 1 (default B = 2 semitones, which is ±200 cents).
# 4. The pitchwheel value is scaled precisely as:
#    bend_value = int(D * (8192.0 / B))
# 5. Since |D| <= 0.5 and B >= 1, the maximum bend value is:
#    |bend_value| <= 0.5 * (8192.0 / B) <= 4096.0
# 6. Since the MIDI pitchwheel range is [-8192, 8191], our maximum deviation of ±4096
#    occupies at most 50% of the available range (and only 25% under the default B = 2).
# 7. Therefore, pitch bend values will NEVER clip or exceed MIDI boundary limits,
#    regardless of the microtonal interval or tuning system used.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Write — NoteInfo list (from generators / Idea Tool)
# ---------------------------------------------------------------------------


def notes_to_midi(
    notes: list[NoteInfo],
    path: str | Path,
    *,
    bpm: float = 120.0,
    humanize: bool = True,
) -> None:
    """
    Write a single list of NoteInfo objects to a single-track MIDI file.
    """
    export_multitrack_midi({"Track 1": notes}, path, bpm=bpm, humanize=humanize)


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
    volumes: dict[str, int] | None = None,
    diagnose: bool = True,
    humanize: bool = True,
    tempo_events: list[tuple[float, float]] | None = None,
    pitch_bend_range: int = 2,
    mpe_tracks: set[str] | None = None,
    reaper_project: bool = False,
    validate_form: bool = True,
    form: "MusicalForm | None" = None,
    strict_validation: bool = False,
    postprocess_arr: bool = False,
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
    diagnose: if True, run diagnostic analysis on tracks and print fix suggestions.
    mpe_tracks: set of track names that should get MPE (per-note expression) treatment.
        These tracks get larger voice pools and MPE zone RPN setup.
    reaper_project: if True (default), write a .rpp file next to the .mid file
        with the same stem name. The project contains one MIDI track per
        instrument, colour-coded by family, ready to open in REAPER for
        mixing/mastering. Pass False to skip .rpp generation.
    validate_form: if True, run the form/arrangement validator and print warnings.
        Defaults to True when form is provided, False otherwise.
    form: optional MusicalForm — enables form-level checks (sonata, ternary, etc.)
        in addition to arrangement checks.
    postprocess_arr: if True, apply lightweight ARR-12/ARR-13 fixes
        (melodic-leap resolution + breathing-room rests) before writing the
        MIDI file.  Use this on the compact path (IdeaTool.generate() →
        export_multitrack_midi()) to get the same correctness guarantees as
        the full produce_track() pipeline, without requiring rhythm/mixing
        stages.  Tracks are selected by GM program number: programs 0–79
        (piano, strings, brass, woodwinds, etc.) are processed; programs
        80–127 (pads, percussion, SFX) are left untouched.  Defaults to
        False to preserve backward-compatibility.
    """
    from melodica.types import TICKS_PER_BEAT, MIDI_MAX

    # Optional: lightweight ARR-12/ARR-13 repair (compact path opt-in).
    # Runs before the `_`-prefix filter so internal keys are transparently skipped
    # inside fix_arr_lite itself.
    if postprocess_arr:
        from melodica._postprocess import fix_arr_lite
        tracks_data = fix_arr_lite(tracks_data, instruments=instruments)

    tracks_data = {k: v for k, v in tracks_data.items() if not k.startswith("_")}
    tpb = TICKS_PER_BEAT
    tempo = mido.bpm2tempo(bpm)
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)

    # 1. Global Meta Track
    meta_track = mido.MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage("track_name", name="Global", time=0))

    meta_events: list[tuple[int, mido.MetaMessage]] = []

    # Initial tempo at beat 0
    meta_events.append((0, mido.MetaMessage("set_tempo", tempo=tempo, time=0)))

    # Additional tempo events
    if tempo_events:
        for beat, event_bpm in tempo_events:
            if beat <= 0.0:
                meta_events[0] = (0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(event_bpm), time=0))
            else:
                tick = round(beat * tpb)
                meta_events.append((tick, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(event_bpm), time=0)))

    if timeline is not None:
        # Full timeline: key changes, time-signature changes, markers
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
    else:
        # Simple key + time signature
        if key is not None:
            key_str = key if isinstance(key, str) else _scale_to_key_sig(key)
            meta_events.append((0, mido.MetaMessage("key_signature", key=key_str, time=0)))
        meta_events.append(
            (
                0,
                mido.MetaMessage(
                    "time_signature",
                    numerator=time_sig[0],
                    denominator=time_sig[1],
                    time=0,
                ),
            )
        )

    # Sort all meta events by tick and append to meta track
    meta_events.sort(key=lambda x: x[0])
    last_tick = 0
    for tick, msg in meta_events:
        msg.time = max(0, tick - last_tick)
        meta_track.append(msg)
        last_tick = tick


    # 1b. Voice-leading correction — resolve parallel fifths/octaves before MIDI write.
    from melodica.voice_leading import correct_parallels as _correct_parallels
    tracks_data = _correct_parallels(tracks_data, instruments=instruments)

    # 2. Dynamic voice channel pool allocation to prevent polyphonic pitch bend overlap.
    # Identify which tracks in tracks_data contain microtonal notes.
    mpe_set = mpe_tracks or set()
    microtonal_tracks = []
    for name, notes in tracks_data.items():
        has_micro = False
        for n in notes:
            if abs(n.pitch - round(n.pitch)) > 0.001:
                has_micro = True
                break
        if has_micro:
            microtonal_tracks.append(name)

    # Identify percussion tracks — these must live on GM channel 9 (the
    # dedicated drum channel) so synths/soundfonts play them as the unpitched
    # drum kit rather than as a pitched instrument. A track is percussion if
    # its name matches a drum-kit keyword.
    # IMPORTANT: only UNPITCHED percussion belongs on channel 9. Pitched
    # tuned percussion (timpani, glockenspiel, marimba, tubular bells, etc.)
    # plays real notes and must stay on a normal channel with its GM program,
    # so those keywords are deliberately excluded here.
    DRUM_CHANNEL = 9
    _PERC_KEYWORDS = ("drum", "percussion", "perc", "kit", "taiko", "ghost")

    def _is_percussion(name: str) -> bool:
        low = name.lower()
        if any(kw in low for kw in _PERC_KEYWORDS):
            return True
        # Explicit GM program mapping to a known percussion alias
        if instruments and name in instruments:
            # GM has no pitched program for raw drum kits; callers signal
            # percussion by routing through the drums/percussion name path,
            # so an explicit program means a pitched instrument — not perc.
            return False
        return False

    percussion_tracks = {name for name in tracks_data if _is_percussion(name)}

    track_channels: dict[str, list[int]] = {}
    next_chan = 0
    mpe_zone_channels = []  # Collect all MPE member channels for zone setup

    def _advance_past_drum_channel() -> None:
        """Skip channel 9 for pitched tracks — it's reserved for percussion."""
        nonlocal next_chan
        if next_chan == DRUM_CHANNEL:
            next_chan += 1

    for name in tracks_data.keys():
        # Percussion always goes to the dedicated drum channel.
        if name in percussion_tracks:
            track_channels[name] = [DRUM_CHANNEL]
            continue

        is_mpe = name in mpe_set
        _advance_past_drum_channel()
        if is_mpe:
            # MPE tracks: 7 channels for full polyphonic expression
            pool_size = 7
            remaining_tracks = len(tracks_data) - len(track_channels) - 1
            if next_chan + pool_size + remaining_tracks > 15:
                pool_size = max(1, 15 - next_chan - remaining_tracks)
            pool = list(range(next_chan, next_chan + pool_size))
            track_channels[name] = pool
            mpe_zone_channels.extend(pool[1:])  # Member channels (not master)
            next_chan += pool_size
        elif name in microtonal_tracks:
            # Give a pool of 3 channels for polyphonic microtonal voice allocation
            pool_size = 3
            remaining_tracks = len(tracks_data) - len(track_channels) - 1
            if next_chan + pool_size + remaining_tracks > 16:
                pool_size = max(1, 16 - next_chan - remaining_tracks)

            track_channels[name] = list(range(next_chan, next_chan + pool_size))
            next_chan += pool_size
        else:
            # Diatonic tracks only need 1 channel
            track_channels[name] = [next_chan]
            next_chan += 1
        # Clamp channels to range 0-15
        track_channels[name] = [min(15, ch) for ch in track_channels[name]]

    # 3. Add individual tracks
    for i, (name, notes) in enumerate(tracks_data.items()):
        if i >= 16:
            break  # MIDI limit

        pool = track_channels.get(name, [i])

        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name, time=0))

        # Program change and controllers: broadcast to all channels in the pool
        is_mpe_track = name in mpe_set
        for ci, channel in enumerate(pool):
            # Resolve GM program:
            # 1. Explicit instruments map
            # 2. Case-insensitive track name lookup in GM_INSTRUMENTS
            # 3. Substring match in GM_INSTRUMENTS (e.g. "Solo_Oud" -> "oud" if added)
            # 4. Fallback to 0 (Piano)
            program = 0
            if instruments and name in instruments:
                program = instruments[name]
            else:
                low_name = name.lower()
                # Exact match
                if low_name in GM_INSTRUMENTS:
                    program = GM_INSTRUMENTS[low_name]
                else:
                    # Fuzzy match: find if any GM key is part of the track name
                    # Sort keys by length descending to match "dark_pad" before "pad"
                    for key in sorted(GM_INSTRUMENTS.keys(), key=len, reverse=True):
                        if key in low_name:
                            program = GM_INSTRUMENTS[key]
                            break

            tr.append(mido.Message("program_change", program=program, channel=channel, time=0))


            if volumes and name in volumes:
                tr.append(
                    mido.Message(
                        "control_change",
                        control=7,
                        value=max(0, min(127, volumes[name])),
                        channel=channel,
                        time=0,
                    )
                )

            # RPN 0x0000 — Pitch Bend Range (semitones)
            tr.append(mido.Message("control_change", control=101, value=0, channel=channel, time=0))
            tr.append(mido.Message("control_change", control=100, value=0, channel=channel, time=0))
            tr.append(
                mido.Message(
                    "control_change", control=6, value=pitch_bend_range, channel=channel, time=0
                )
            )
            tr.append(mido.Message("control_change", control=38, value=0, channel=channel, time=0))
            # Null RPN to prevent accidental CC6 overrides later
            tr.append(mido.Message("control_change", control=101, value=127, channel=channel, time=0))
            tr.append(mido.Message("control_change", control=100, value=127, channel=channel, time=0))

        # MPE zone setup: RPN 0x0006 on master channel (first in pool)
        # Declares the number of member channels for MPE-aware synths
        if is_mpe_track and len(pool) > 1:
            master_ch = pool[0]
            member_count = len(pool) - 1  # All channels except master
            tr.append(mido.Message("control_change", control=101, value=0, channel=master_ch, time=0))
            tr.append(mido.Message("control_change", control=100, value=6, channel=master_ch, time=0))
            tr.append(mido.Message("control_change", control=6, value=member_count, channel=master_ch, time=0))
            tr.append(mido.Message("control_change", control=38, value=0, channel=master_ch, time=0))
            # Null RPN
            tr.append(mido.Message("control_change", control=101, value=127, channel=master_ch, time=0))
            tr.append(mido.Message("control_change", control=100, value=127, channel=master_ch, time=0))

            # MPE per-note pitch bend range (+/- 48 semitones for maximum expression)
            for ch in pool[1:]:
                tr.append(mido.Message("control_change", control=101, value=0, channel=ch, time=0))
                tr.append(mido.Message("control_change", control=100, value=0, channel=ch, time=0))
                tr.append(mido.Message("control_change", control=6, value=48, channel=ch, time=0))
                tr.append(mido.Message("control_change", control=38, value=0, channel=ch, time=0))
                tr.append(mido.Message("control_change", control=101, value=127, channel=ch, time=0))
                tr.append(mido.Message("control_change", control=100, value=127, channel=ch, time=0))

        # Build all events: note_on, note_off, control_change, pitchwheel
        # Format: (tick, msg_type, val1, val2, channel)
        events: list[tuple[int, str, int, int, int]] = []

        # 3.1. Calculate jittered onsets first to handle timing changes deterministically
        jittered_notes = []
        for n in notes:
            onset = max(0.0, n.start)
            if humanize:
                jitter_beats = random.uniform(-0.015, 0.015) * (bpm / 60.0)
                onset = max(0.0, onset + jitter_beats)
            jittered_notes.append({
                "onset": onset,
                "duration": n.duration,
                "note": n
            })

        # Sort chronologically by onset
        jittered_notes.sort(key=lambda jn: jn["onset"])

        # 3.1.5 Deduplicate identical or near-identical notes (same pitch, same onset)
        deduped = []
        for jn in jittered_notes:
            pitch = jn["note"].pitch
            is_duplicate = False
            # Look backwards in deduped. We only need to look at recent notes since it's sorted by onset.
            for i in range(len(deduped) - 1, -1, -1):
                d = deduped[i]
                if jn["onset"] - d["onset"] >= 0.05:  # Too far apart, stop looking back
                    break
                if d["note"].pitch == pitch and abs(d["onset"] - jn["onset"]) < 0.05:
                    is_duplicate = True
                    # Merge attributes: keep the highest velocity and longest duration
                    d["note"].velocity = max(d["note"].velocity, jn["note"].velocity)
                    d["duration"] = max(d["duration"], jn["duration"])
                    break
            if not is_duplicate:
                deduped.append(jn)
        jittered_notes = deduped

        # 3.2. Prevent same-pitch note overlaps by trimming overlapping note durations
        pitch_last_note = {}
        for jn in jittered_notes:
            pitch = jn["note"].pitch
            if pitch in pitch_last_note:
                prev_jn = pitch_last_note[pitch]
                prev_end = prev_jn["onset"] + prev_jn["duration"]
                # If notes overlap or trigger closer than 0.02 beats, create a 0.02 beat gap
                if prev_end >= jn["onset"] - 0.02:
                    prev_jn["duration"] = max(0.01, jn["onset"] - prev_jn["onset"] - 0.02)
            pitch_last_note[pitch] = jn

        # Polyphonic voice channel allocation tracker for the pool
        channel_busy_until = {ch: -1.0 for ch in pool}
        channel_active_events = {ch: [] for ch in pool}

        # 3.3. Generate events
        for jn in jittered_notes:
            n = jn["note"]
            onset = jn["onset"]
            duration = jn["duration"]

            # Dynamic voice allocation
            if len(pool) == 1:
                assigned_ch = pool[0]
            else:
                assigned_ch = None
                for ch in pool:
                    if channel_busy_until[ch] <= onset:
                        assigned_ch = ch
                        break
                if assigned_ch is None:
                    # Steal the voice that becomes free earliest
                    assigned_ch = min(pool, key=lambda ch: channel_busy_until[ch])
                    # Deterministic voice stealing truncation:
                    # Truncate the stolen note's duration to the onset tick of the stealing note
                    on_tick = round(onset * tpb)
                    for ev in channel_active_events[assigned_ch]:
                        if ev[0] > on_tick:
                            if ev[1] in ("note_off", "pitchwheel_reset"):
                                ev[0] = on_tick
                            else:
                                ev[1] = "discard"
            
            channel_busy_until[assigned_ch] = onset + duration

            on_tick = round(onset * tpb)
            off_tick = round((onset + duration) * tpb)

            # Математика pitch bend верна и корректна для ладов с минимальным интервалом ≥ 50 cents (0.5 semitones)
            rounded_pitch = int(round(n.pitch))
            deviation = n.pitch - rounded_pitch
            bend_value = int(deviation * (8192.0 / pitch_bend_range))

            note_events = []

            # Note on/off
            note_events.append([on_tick, "note_on", rounded_pitch, n.velocity, assigned_ch])
            note_events.append([off_tick, "note_off", rounded_pitch, 0, assigned_ch])

            has_cc11 = False
            custom_bend = 0
            has_custom_bend = False
            has_dynamic_bend = False
            # CC and pitchwheel events from note.expression
            if getattr(n, "expression", None):
                for cc_num, cc_val in n.expression.items():
                    if cc_num == 11:
                        has_cc11 = True
                    if isinstance(cc_num, int) and 0 <= cc_num <= 127:
                        if isinstance(cc_val, list):
                            for rel_time, val in cc_val:
                                note_events.append([round((onset + rel_time) * tpb), "control_change", cc_num, max(0, min(127, int(val))), assigned_ch])
                        else:
                            note_events.append([on_tick, "control_change", cc_num, max(0, min(127, int(cc_val))), assigned_ch])
                    elif cc_num == "pitch_bend":
                        if isinstance(cc_val, list):
                            for rel_time, val in cc_val:
                                t_bend = max(-8192, min(8191, bend_value + int(val)))
                                note_events.append([round((onset + rel_time) * tpb), "pitchwheel", t_bend, 0, assigned_ch])
                            has_dynamic_bend = True
                        else:
                            custom_bend = int(cc_val)
                            has_custom_bend = True

            if not has_dynamic_bend:
                total_bend = max(-8192, min(8191, bend_value + custom_bend))
                if bend_value != 0 or has_custom_bend:
                    note_events.append([on_tick, "pitchwheel", total_bend, 0, assigned_ch])
                    note_events.append([off_tick, "pitchwheel_reset", 0, 0, assigned_ch])
            else:
                note_events.append([off_tick, "pitchwheel_reset", 0, 0, assigned_ch])

            # Advanced humanized CC11 (Expression) and CC1 (Modulation) for long notes
            if humanize and duration > 1.5:
                if not has_cc11:
                    cc_steps = max(3, int(duration / 0.25))
                    for step in range(cc_steps + 1):
                        t_beat = onset + (step / cc_steps) * duration
                        phase = (t_beat - onset) * math.pi / 2.0
                        jitter = random.uniform(-4, 4)
                        val = 75 + int(math.sin(phase) * 30) + int(jitter)
                        note_events.append([round(t_beat * tpb), "control_change", 11, max(0, min(127, val)), assigned_ch])

                # Modulation / Vibrato / Filter sweeps LFO on CC1 for solo & pad instruments
                is_expressive_solo = any(
                    k in name.lower()
                    for k in ["cello", "viola", "flute", "clarinet", "voice", "choir", "strings", "pad"]
                )
                if is_expressive_solo:
                    cc_steps = max(3, int(duration / 0.25))
                    for step in range(cc_steps + 1):
                        t_beat = onset + (step / cc_steps) * duration
                        time_since_start = t_beat - onset
                        ramp = min(1.0, time_since_start / 1.0)

                        if "pad" in name.lower() or "choir" in name.lower():
                            phase = time_since_start * math.pi / 4.0  # 8 beats per cycle
                            val = 45 + int(math.sin(phase) * 25)
                        else:
                            cycles_per_beat = 6.0 * (60.0 / bpm)
                            phase = time_since_start * 2.0 * math.pi * cycles_per_beat
                            val = int(ramp * (35 + int(math.sin(phase) * 15)))

                        note_events.append([round(t_beat * tpb), "control_change", 1, max(0, min(127, val)), assigned_ch])

            for ev in note_events:
                events.append(ev)
            channel_active_events[assigned_ch] = note_events

        # Auto sustain pedal (CC64) automation for piano, harp, arpeggios: broadcast to pool
        is_pedal_inst = any(k in name.lower() for k in ["harp", "piano", "arp"])
        if humanize and is_pedal_inst and notes:
            max_end = max(n.start + n.duration for n in notes)
            t_pedal = 0.0
            has_manual_pedal = False
            if cc_events and name in cc_events:
                if any(ev[1] == 64 for ev in cc_events[name]):
                    has_manual_pedal = True
            
            if not has_manual_pedal:
                while t_pedal < max_end:
                    for ch in pool:
                        events.append([round(t_pedal * tpb), "control_change", 64, 127, ch])
                        release_time = min(t_pedal + 3.95, max_end)
                        events.append([round(release_time * tpb), "control_change", 64, 0, ch])
                    t_pedal += 4.0

        # Standalone CC events: broadcast to all channels in pool
        if cc_events and name in cc_events:
            for beat, cc_num, cc_val in cc_events[name]:
                tick = round(max(0.0, beat) * tpb)
                for ch in pool:
                    events.append([tick, "control_change", cc_num, max(0, min(127, cc_val)), ch])

        # Filter out any events marked as discarded by voice stealing truncation
        events = [ev for ev in events if ev[1] != "discard"]

        # Sort using type_order to prevent note start/end artifacts and tail-bend issues
        type_order = {
            "note_off": 0,
            "pitchwheel_reset": 1,
            "pitchwheel": 2,
            "control_change": 3,
            "note_on": 4,
        }
        events.sort(key=lambda e: (e[0], type_order.get(e[1], 5)))

        prev_tick = 0
        for tick, msg_type, data1, data2, ch in events:
            delta = max(0, tick - prev_tick)
            if msg_type == "control_change":
                tr.append(
                    mido.Message(
                        "control_change",
                        control=int(data1),
                        value=int(data2),
                        time=delta,
                        channel=ch,
                    )
                )
            elif msg_type in ("pitchwheel", "pitchwheel_reset"):
                tr.append(mido.Message("pitchwheel", pitch=int(data1), time=delta, channel=ch))
            else:
                tr.append(
                    mido.Message(
                        msg_type,
                        note=int(data1),
                        velocity=int(data2),
                        time=delta,
                        channel=ch,
                    )
                )
            prev_tick = tick

    if isinstance(path, (str, Path)):
        mid.save(path)
    else:
        mid._save(path)

    if diagnose:
        from melodica.composer.diagnostics import diagnose_tracks

        label = str(path) if isinstance(path, (str, Path)) else None
        diagnose_tracks(tracks_data, bpm=bpm, label=label)

    # Optional: form/arrangement validation
    if validate_form:
        from melodica.form_validator import validate as _validate_form
        _label = str(path) if isinstance(path, (str, Path)) else None
        _validate_form(tracks_data, bpm=bpm, form=form, label=_label, strict=strict_validation)

    # Optional: generate a REAPER .RPP project file next to the .mid
    if reaper_project and isinstance(path, (str, Path)):
        from melodica.reaper_project import export_reaper_project
        rpp_path = Path(path).with_suffix(".rpp")
        export_reaper_project(
            tracks_data,
            rpp_path,
            bpm=bpm,
            time_sig=time_sig,
            instruments=instruments,
            volumes=volumes,
        )


def export_midi(
    tracks: list[Track],
    path: str | Path,
    *,
    bpm: float = 120.0,
    timeline: MusicTimeline | None = None,
    humanize: bool = True,
    tempo_events: list[tuple[float, float]] | None = None,
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

    # Collect all meta events as (abs_tick, MetaMessage)
    meta_events: list[tuple[int, mido.MetaMessage]] = []
    meta_events.append((0, mido.MetaMessage("set_tempo", tempo=tempo, time=0)))
    meta_events.append((0, mido.MetaMessage("track_name", name="Global", time=0)))

    if timeline:
        # Key Signatures — one per key region
        for kl in timeline.keys:
            tick = round(kl.start * tpb)
            key_str = _scale_to_key_sig(kl.scale)
            meta_events.append((tick, mido.MetaMessage("key_signature", key=key_str, time=0)))

        # Time Signatures
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

        # Section Markers
        for m in timeline.markers:
            tick = round(m.start * tpb)
            meta_events.append((tick, mido.MetaMessage("marker", text=m.text, time=0)))

        # Tempos from timeline
        if hasattr(timeline, "tempos") and timeline.tempos:
            for t in timeline.tempos:
                tick = round(t.start * tpb)
                if tick == 0:
                    for idx, (mt_t, mt_msg) in enumerate(meta_events):
                        if mt_t == 0 and mt_msg.type == "set_tempo":
                            meta_events[idx] = (0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(t.bpm), time=0))
                            break
                else:
                    meta_events.append((tick, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(t.bpm), time=0)))

    # Additional tempo events
    if tempo_events:
        for beat, event_bpm in tempo_events:
            tick = round(beat * tpb)
            if tick == 0:
                # Update the initial set_tempo event
                for idx, (t, msg) in enumerate(meta_events):
                    if t == 0 and msg.type == "set_tempo":
                        meta_events[idx] = (0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(event_bpm), time=0))
                        break
            else:
                meta_events.append((tick, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(event_bpm), time=0)))

    # Sort by absolute tick, then write with delta times
    meta_events.sort(key=lambda x: x[0])
    last_tick = 0
    for tick, msg in meta_events:
        msg.time = max(0, tick - last_tick)
        meta_track.append(msg)
        last_tick = tick

    # 2. Dynamic voice channel pool allocation to prevent polyphonic pitch bend overlap.
    # Pre-assigned channels in the Track objects
    used_channels = {t.channel for t in tracks}
    # Unused channels we can borrow for polyphonic pitch bends
    free_channels = [ch for ch in range(16) if ch not in used_channels]

    track_pools: dict[int, list[int]] = {}
    for idx, t in enumerate(tracks):
        pool = [t.channel]
        has_micro = False
        for n in t.notes:
            if abs(n.pitch - round(n.pitch)) > 0.001:
                has_micro = True
                break
        if has_micro:
            # Borrow up to 2 free channels for the pool to support polyphony
            borrow_count = min(2, len(free_channels))
            for _ in range(borrow_count):
                pool.append(free_channels.pop(0))
        track_pools[idx] = pool

    # 3. Individual Tracks
    for i, t in enumerate(tracks):
        if i >= 16:
            break

        pool = track_pools.get(i, [t.channel])

        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=t.name, time=0))
        if t.instrument_name:
            tr.append(mido.MetaMessage("instrument_name", name=t.instrument_name, time=0))

        # Program changes and controllers: broadcast to all channels in the pool
        for channel in pool:
            tr.append(mido.Message("program_change", program=t.program, channel=channel, time=0))

            # CC 7  — Channel Volume (static mix level — do not automate)
            tr.append(
                mido.Message("control_change", control=7, value=t.volume, channel=channel, time=0)
            )
            # CC 10 — Pan
            tr.append(
                mido.Message("control_change", control=10, value=t.pan, channel=channel, time=0)
            )
            # CC 11 — Expression (dynamic shaping within volume)
            tr.append(
                mido.Message(
                    "control_change", control=11, value=t.expression, channel=channel, time=0
                )
            )
            # CC 1  — Modulation (vibrato depth)
            tr.append(
                mido.Message("control_change", control=1, value=t.modulation, channel=channel, time=0)
            )
            # CC 73 — Attack Time
            tr.append(
                mido.Message("control_change", control=73, value=t.attack, channel=channel, time=0)
            )
            # CC 72 — Release Time
            tr.append(
                mido.Message("control_change", control=72, value=t.release, channel=channel, time=0)
            )
            # CC 91 — Reverb Send
            tr.append(
                mido.Message("control_change", control=91, value=t.reverb, channel=channel, time=0)
            )
            # CC 93 — Chorus Send
            tr.append(
                mido.Message("control_change", control=93, value=t.chorus, channel=channel, time=0)
            )
            # CC 3  — Vibrato depth
            tr.append(
                mido.Message("control_change", control=3, value=t.vibrato, channel=channel, time=0)
            )
            # CC 64 — Sustain Pedal / Articulation Trigger
            tr.append(
                mido.Message(
                    "control_change", control=64, value=t.sustain_pedal, channel=channel, time=0
                )
            )

            # RPN 0x0000 — Pitch Bend Range (semitones)
            tr.append(mido.Message("control_change", control=101, value=0, channel=channel, time=0))
            tr.append(mido.Message("control_change", control=100, value=0, channel=channel, time=0))
            tr.append(
                mido.Message(
                    "control_change", control=6, value=t.pitch_bend_range, channel=channel, time=0
                )
            )
            tr.append(mido.Message("control_change", control=38, value=0, channel=channel, time=0))
            # Null RPN to prevent accidental CC6 overrides later
            tr.append(mido.Message("control_change", control=101, value=127, channel=channel, time=0))
            tr.append(mido.Message("control_change", control=100, value=127, channel=channel, time=0))

        # Build relative events
        # Format: (tick, msg_type, val1, val2, channel)
        events: list[tuple[int, str, int, int, int]] = []

        # 3.1. Calculate jittered onsets first to handle timing changes deterministically
        jittered_notes = []
        for n in t.notes:
            onset = max(0.0, n.start)
            if humanize:
                jitter_beats = random.uniform(-0.015, 0.015) * (bpm / 60.0)
                onset = max(0.0, onset + jitter_beats)
            jittered_notes.append({
                "onset": onset,
                "duration": n.duration,
                "note": n
            })

        # Sort chronologically by onset
        jittered_notes.sort(key=lambda jn: jn["onset"])

        # 3.1.5 Deduplicate identical or near-identical notes (same pitch, same onset)
        deduped = []
        for jn in jittered_notes:
            pitch = jn["note"].pitch
            is_duplicate = False
            # Look backwards in deduped. We only need to look at recent notes since it's sorted by onset.
            for i in range(len(deduped) - 1, -1, -1):
                d = deduped[i]
                if jn["onset"] - d["onset"] >= 0.05:  # Too far apart, stop looking back
                    break
                if d["note"].pitch == pitch and abs(d["onset"] - jn["onset"]) < 0.05:
                    is_duplicate = True
                    # Merge attributes: keep the highest velocity and longest duration
                    d["note"].velocity = max(d["note"].velocity, jn["note"].velocity)
                    d["duration"] = max(d["duration"], jn["duration"])
                    break
            if not is_duplicate:
                deduped.append(jn)
        jittered_notes = deduped

        # 3.2. Prevent same-pitch note overlaps by trimming overlapping note durations
        pitch_last_note = {}
        for jn in jittered_notes:
            pitch = jn["note"].pitch
            if pitch in pitch_last_note:
                prev_jn = pitch_last_note[pitch]
                prev_end = prev_jn["onset"] + prev_jn["duration"]
                # If notes overlap or trigger closer than 0.02 beats, create a 0.02 beat gap
                if prev_end >= jn["onset"] - 0.02:
                    prev_jn["duration"] = max(0.01, jn["onset"] - prev_jn["onset"] - 0.02)
            pitch_last_note[pitch] = jn

        # Polyphonic voice channel allocation tracker for the pool
        channel_busy_until = {ch: -1.0 for ch in pool}
        channel_active_events = {ch: [] for ch in pool}

        # 3.3. Generate events
        for jn in jittered_notes:
            n = jn["note"]
            onset = jn["onset"]
            duration = jn["duration"]

            # Dynamic voice allocation
            if len(pool) == 1:
                assigned_ch = pool[0]
            else:
                assigned_ch = None
                for ch in pool:
                    if channel_busy_until[ch] <= onset:
                        assigned_ch = ch
                        break
                if assigned_ch is None:
                    # Steal the voice that becomes free earliest
                    assigned_ch = min(pool, key=lambda ch: channel_busy_until[ch])
                    # Deterministic voice stealing truncation:
                    # Truncate the stolen note's duration to the onset tick of the stealing note
                    on_tick = round(onset * tpb)
                    for ev in channel_active_events[assigned_ch]:
                        if ev[0] > on_tick:
                            if ev[1] in ("note_off", "pitchwheel_reset"):
                                ev[0] = on_tick
                            else:
                                ev[1] = "discard"
            
            channel_busy_until[assigned_ch] = onset + duration

            on_tick = round(onset * tpb)
            off_tick = round((onset + duration) * tpb)

            # Математика pitch bend верна и корректна для ладов с минимальным интервалом ≥ 50 cents (0.5 semitones)
            rounded_pitch = int(round(n.pitch))
            deviation = n.pitch - rounded_pitch
            bend_value = int(deviation * (8192.0 / t.pitch_bend_range))

            note_events = []

            note_events.append([on_tick, "note_on", rounded_pitch, n.velocity, assigned_ch])
            note_events.append([off_tick, "note_off", rounded_pitch, 0, assigned_ch])

            has_cc11 = False
            custom_bend = 0
            has_custom_bend = False
            has_dynamic_bend = False
            # Emit Expression (CC) data
            if getattr(n, "expression", None):
                for cc_num, cc_val in n.expression.items():
                    if cc_num == 11:
                        has_cc11 = True
                    if isinstance(cc_num, int) and 0 <= cc_num <= 127:
                        if isinstance(cc_val, list):
                            for rel_time, val in cc_val:
                                note_events.append([round((onset + rel_time) * tpb), "control_change", cc_num, max(0, min(127, int(val))), assigned_ch])
                        else:
                            note_events.append([on_tick, "control_change", cc_num, max(0, min(127, int(cc_val))), assigned_ch])
                    elif cc_num == "pitch_bend":
                        if isinstance(cc_val, list):
                            for rel_time, val in cc_val:
                                t_bend = max(-8192, min(8191, bend_value + int(val)))
                                note_events.append([round((onset + rel_time) * tpb), "pitchwheel", t_bend, 0, assigned_ch])
                            has_dynamic_bend = True
                        else:
                            custom_bend = int(cc_val)
                            has_custom_bend = True

            if not has_dynamic_bend:
                total_bend = max(-8192, min(8191, bend_value + custom_bend))
                if bend_value != 0 or has_custom_bend:
                    note_events.append([on_tick, "pitchwheel", total_bend, 0, assigned_ch])
                    note_events.append([off_tick, "pitchwheel_reset", 0, 0, assigned_ch])
            else:
                note_events.append([off_tick, "pitchwheel_reset", 0, 0, assigned_ch])

            # Auto CC11 for long notes
            if humanize and duration > 1.5 and not has_cc11:
                cc_steps = max(3, int(duration / 0.25))
                for i in range(cc_steps + 1):
                    t_beat = onset + (i / cc_steps) * duration
                    phase = (i / cc_steps) * math.pi
                    val = 60 + int(math.sin(phase) * 60)
                    note_events.append([round(t_beat * tpb), "control_change", 11, val, assigned_ch])

            for ev in note_events:
                events.append(ev)
            channel_active_events[assigned_ch] = note_events

        # Keyswitch events: broadcast to all channels in the pool to ensure correct articulation on all voices
        for ks_beat, ks_pitch in t.keyswitch_events:
            ks_tick = round(ks_beat * tpb)
            for ch in pool:
                events.append([ks_tick, "note_on", ks_pitch, 64, ch])
                events.append([ks_tick + 1, "note_off", ks_pitch, 0, ch])

        # Filter out any events marked as discarded by voice stealing truncation
        events = [ev for ev in events if ev[1] != "discard"]

        # Sort using type_order to prevent note start/end artifacts and tail-bend issues
        type_order = {
            "note_off": 0,
            "pitchwheel_reset": 1,
            "pitchwheel": 2,
            "control_change": 3,
            "note_on": 4,
        }
        events.sort(key=lambda e: (e[0], type_order.get(e[1], 5)))

        prev_tick = 0
        for tick, msg_type, val1, val2, ch in events:
            delta = max(0, tick - prev_tick)
            if msg_type == "control_change":
                tr.append(
                    mido.Message(
                        "control_change",
                        control=int(val1),
                        value=int(val2),
                        time=delta,
                        channel=ch,
                    )
                )
            elif msg_type in ("pitchwheel", "pitchwheel_reset"):
                tr.append(
                    mido.Message("pitchwheel", pitch=int(val1), time=delta, channel=ch)
                )
            else:
                tr.append(
                    mido.Message(
                        msg_type, note=int(val1), velocity=int(val2), time=delta, channel=ch
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
    humanize: bool = True,
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

    notes_to_midi(note_infos, path, bpm=bpm, humanize=humanize)


def slice_notes_with_tying(notes: list[NoteInfo], boundaries: list[float]) -> list[list[NoteInfo]]:
    """
    Slice a list of notes by time boundaries, splitting notes that cross boundaries with ties.
    
    boundaries: sorted list of boundary timestamps (e.g. [0.0, 16.0, 32.0, 48.0])
    Returns: list of NoteInfo lists, one for each boundary interval.
    """
    if not boundaries or len(boundaries) < 2:
        return [[NoteInfo(
            pitch=n.pitch,
            start=n.start,
            duration=n.duration,
            velocity=n.velocity,
            absolute=n.absolute,
            articulation=n.articulation,
            expression=dict(n.expression) if n.expression else None
        ) for n in notes]]

    result = [[] for _ in range(len(boundaries) - 1)]
    
    for note in notes:
        start_idx = -1
        for i in range(len(boundaries) - 1):
            if boundaries[i] <= note.start < boundaries[i+1]:
                start_idx = i
                break
        
        if start_idx == -1:
            continue
            
        note_end = note.start + note.duration
        current_idx = start_idx
        current_start = note.start
        
        while current_idx < len(boundaries) - 1 and current_start < note_end:
            boundary_end = boundaries[current_idx + 1]
            if note_end <= boundary_end:
                sliced_note = NoteInfo(
                    pitch=note.pitch,
                    start=current_start - boundaries[current_idx],
                    duration=note_end - current_start,
                    velocity=note.velocity,
                    absolute=note.absolute,
                    articulation=note.articulation,
                    expression=dict(note.expression) if note.expression else None
                )
                result[current_idx].append(sliced_note)
                break
            else:
                # Note crosses the boundary! Split it with tie
                duration_in_slice = boundary_end - current_start
                sliced_note = NoteInfo(
                    pitch=note.pitch,
                    start=current_start - boundaries[current_idx],
                    duration=duration_in_slice,
                    velocity=note.velocity,
                    absolute=note.absolute,
                    articulation="legato",
                    expression=dict(note.expression) if note.expression else None
                )
                result[current_idx].append(sliced_note)
                
                current_start = boundary_end
                current_idx += 1
                
    return result
