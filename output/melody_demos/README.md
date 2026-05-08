# LeadSynth Generator Demo

## What it does

`LeadSynthGenerator` from Melodica SDK generates melodic lead lines that follow chord progressions.

**Input:**
- Chord progression (I–V–vi–IV by default)
- Style (retro/techno/trance/supersaw)
- Note length (legato/staccato/mixed)
- BPM, bars, scale

**Output:**
- MIDI notes (pitch, velocity, duration) on GM channel 81 (Sawtooth Lead)

---

## How to run

```bash
# Generate a melody (16 bars, techno style)
python3.11 scripts/demo_melody_generator.py --style techno --bars 16 --bpm 150 --output my_melody.mid

# Inspect note patterns in console
python3.11 scripts/inspect_melody.py
```

**Arguments:**
- `--style` : retro, techno, trance, supersaw
- `--note-length` : legato, staccato, mixed
- `--bars` : number of bars (default 16)
- `--bpm` : tempo (default 140)
- `--output` : output MIDI path

---

## Style differences

| Style | Characteristics | Notes/bar | BPM range |
|-------|-----------------|-----------|-----------|
| retro | 80s synth, melodic, moderate density | ~2-4 | 100-130 |
| techno | high-energy, staccato, arpeggiated | 12-16 | 140-160 |
| trance | flowing, legato, wide intervals | 6-10 | 130-150 |
| supersaw | bright, detuned sawtooth, rich harmonics | 8-12 | 140-160 |

Note length:
- `staccato` — short, separated (0.05–0.2 beats)
- `legato` — long, connected (1.0–1.5 beats, overlapping)
- `mixed` — combination (some short, some long)

---

## How it works (inside SDK)

`LeadSynthGenerator` in `melodica/generators/lead_synth.py`:

1. **Chord-tone selection** — picks notes from current chord (1-3-5 or 1-3-5-7 depending on mode)
2. **Rhythm generation** — Markov-chain or pattern-based rhythm (different per style)
3. **Contour shaping** — rising/falling patterns, octave jumps
4. **Portamento & vibrato** — added via expression attributes
5. **Velocity humanization** — random variation + accent on downbeats

The generator respects the chord progression: each bar's melody notes belong to that bar's chord.

---

## Example output (retro, staccato, 8 bars)

```
Time  | Note  | Vel | Dur
------+-------+-----+------
0.00  | E4    | 90  | 0.200
1.00  | C4    | 80  | 0.200
2.00  | C4    | 87  | 0.200
3.00  | E4    | 74  | 0.200
4.00  | G4    | 90  | 0.200
...
```

This plays chord tones (E, G, C, B) from C major scale over I–V–vi–IV progression.

---

## Listening

Open generated `.mid` file in:
- Any DAW (Ableton Live, FL Studio, Reaper, Logic Pro)
- MIDI player (MuseScore, VLC, Winamp with MIDI plugin)
- Online MIDI viewer (m SheetMusic, MIDIPlayer)

For audio rendering, load a General MIDI SoundFont (e.g., `GeneralUser GS`, `Timbres of Heaven`).
