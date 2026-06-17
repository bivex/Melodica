# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_downtempo_trap.py — "New Wave Downtempo Trap" Album.

An album leveraging the new modern trap generators (CloudRapGenerator,
PluggnbGenerator, PhonkGenerator) to create lush, masterfully mixed
downtempo tracks.

Tracks:
  1. Cloud Ethereal — 72 BPM — F# Aeolian (Atmospheric wave & airy arps)
  2. Plugg Wave      — 80 BPM — D# Aeolian (Ninth chords pluggnb & sliding 808)
  3. Drift Ghost      — 68 BPM — A Aeolian (Dark, heavy cowbell drift phonk)
"""

import random
from pathlib import Path

from melodica.types import Scale, Mode, ChordLabel, NoteInfo, parse_progression
from melodica.generators import GeneratorParams
from melodica.generators.cloud_rap import CloudRapGenerator
from melodica.generators.pluggnb import PluggnbGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# ------------------------------------------------------------------
# GM Programs
# ------------------------------------------------------------------
PIANO = 0
STRINGS = 48
CHOIR = 52
PAD_WARM = 89
PAD_SPACE = 91
COWBELL_BLOCK = 14  # Tubular bells for melodic cowbell phonk texture
SYNTH_BASS = 38
SYNTH_LEAD = 80
DRUMS = 0

random.seed(2026)
OUT = Path("output/album_downtempo_trap")
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Intercepting Generators for Accurate Track Separation
# ------------------------------------------------------------------

class InterceptCloudRapGenerator(CloudRapGenerator):
    def render_separated(self, chords: list[ChordLabel], key: Scale, duration_beats: float) -> dict[str, list[NoteInfo]]:
        pads_list = []
        drums_list = []
        leads_list = []
        
        orig_pad = self._render_pad
        orig_drums = self._render_drums
        orig_arp = self._render_arp
        
        self._render_pad = lambda notes, *args: orig_pad(pads_list, *args)
        self._render_drums = lambda notes, *args: orig_drums(drums_list, *args)
        self._render_arp = lambda notes, *args: orig_arp(leads_list, *args)
        
        self.render(chords, key, duration_beats)
        
        self._render_pad = orig_pad
        self._render_drums = orig_drums
        self._render_arp = orig_arp
        
        return {"pads": pads_list, "drums": drums_list, "leads": leads_list}


class InterceptPluggnbGenerator(PluggnbGenerator):
    def render_separated(self, chords: list[ChordLabel], key: Scale, duration_beats: float) -> dict[str, list[NoteInfo]]:
        pads_list = []
        bass_list = []
        drums_list = []
        leads_list = []
        
        orig_pad = self._render_pad
        orig_808 = self._render_808
        orig_drums = self._render_drums
        orig_melody = self._render_melody
        
        self._render_pad = lambda notes, *args: orig_pad(pads_list, *args)
        self._render_808 = lambda notes, *args: orig_808(bass_list, *args)
        self._render_drums = lambda notes, *args: orig_drums(drums_list, *args)
        self._render_melody = lambda notes, *args: orig_melody(leads_list, *args)
        
        self.render(chords, key, duration_beats)
        
        self._render_pad = orig_pad
        self._render_808 = orig_808
        self._render_drums = orig_drums
        self._render_melody = orig_melody
        
        return {"pads": pads_list, "synth_bass": bass_list, "drums": drums_list, "leads": leads_list}


class InterceptPhonkGenerator(PhonkGenerator):
    def render_separated(self, chords: list[ChordLabel], key: Scale, duration_beats: float) -> dict[str, list[NoteInfo]]:
        bass_list = []
        drums_list = []
        cowbell_list = []
        pads_list = []
        
        orig_bass = self._render_bass
        orig_kick = self._render_kick
        orig_snare = self._render_snare
        orig_hihats = self._render_hihats
        orig_cowbell = self._render_cowbell
        orig_memphis = self._render_memphis
        
        self._render_bass = lambda notes, *args: orig_bass(bass_list, *args)
        self._render_kick = lambda notes, *args: orig_kick(drums_list, *args)
        self._render_snare = lambda notes, *args: orig_snare(drums_list, *args)
        self._render_hihats = lambda notes, *args: orig_hihats(drums_list, *args)
        self._render_cowbell = lambda notes, *args: orig_cowbell(cowbell_list, *args)
        self._render_memphis = lambda notes, *args: orig_memphis(pads_list, *args)
        
        self.render(chords, key, duration_beats)
        
        self._render_bass = orig_bass
        self._render_kick = orig_kick
        self._render_snare = orig_snare
        self._render_hihats = orig_hihats
        self._render_cowbell = orig_cowbell
        self._render_memphis = orig_memphis
        
        return {"synth_bass": bass_list, "drums": drums_list, "phonk_cowbells": cowbell_list, "pads": pads_list}


# =====================================================================
# Track 1: Cloud Ethereal — 72 BPM — F# Aeolian
# =====================================================================
def produce_cloud_ethereal():
    print("  1. Cloud Ethereal [F# Aeolian — 72 BPM]")
    key = Scale(root=6, mode=Mode.AEOLIAN)  # F# Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 III:4 VII:4 " * 6, key)

    # Use the new CloudRapGenerator to render the core notes
    gen = InterceptCloudRapGenerator(
        variant="ethereal",
        pad_density=0.7,
        drum_sparseness=0.3,
        arp_speed="slow"
    )
    parted = gen.render_separated(chords, key, dur)

    # Add a deep clean sub-bass line underneath (sine wave sub-bass)
    sub_bass = SynthBassGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        waveform="sine",
        pattern="sub_kick"
    ).render(chords, key, dur)

    pads = parted["pads"]
    leads = parted["leads"]
    drums = parted["drums"]

    # Scale velocities to resolve warnings and improve mix
    for n in pads:
        n.scale_velocity(1.5)
    for n in leads:
        n.scale_velocity(1.6)

    # Stagger entrances to avoid uniform density
    # Pads start immediately at beat 0
    # Drums enter at beat 8.0 (bar 2)
    # Arpeggios/leads enter at beat 16.0 (bar 4)
    drums = [n for n in drums if n.start >= 8.0]
    leads = [n for n in leads if n.start >= 16.0]

    tracks = {
        "pads": pads,
        "leads": leads,
        "drums": drums,
        "synth_bass": sub_bass,
    }

    inst = {
        "pads": PAD_SPACE,
        "leads": SYNTH_LEAD,
        "drums": DRUMS,
        "synth_bass": SYNTH_BASS,
    }

    produce_track(
        tracks=tracks,
        bpm=72.0,
        instruments=inst,
        path=OUT / "01_Cloud_Ethereal.mid",
        mood=Mood.AMBIENT,
        key=key,
        genre="trap",
    )


# =====================================================================
# Track 2: Plugg Wave — 80 BPM — D# Aeolian
# =====================================================================
def produce_plugg_wave():
    print("  2. Plugg Wave [D# Aeolian — 80 BPM]")
    key = Scale(root=3, mode=Mode.AEOLIAN)  # D# Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("iadd9:4 iv7:4 VII7:4 III7:4 " * 6, key)

    # Instantiate generator with lower key range to force 808 sub-bass low
    gen = InterceptPluggnbGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        variant="pluggnb",
        pad_voicing="ninth",
        include_808=True,
        hat_style="gentle",
        melody_register=5
    )
    parted = gen.render_separated(chords, key, dur)

    pads = parted["pads"]
    bass = parted["synth_bass"]
    drums = parted["drums"]
    leads = parted["leads"]

    # Scale velocities
    for n in pads:
        n.scale_velocity(1.4)
    for n in leads:
        n.scale_velocity(1.5)

    # Stagger entrances
    # Pads start immediately
    # Bass enters at beat 8.0
    # Drums enter at beat 16.0
    # Lead melody enters at beat 24.0
    bass = [n for n in bass if n.start >= 8.0]
    drums = [n for n in drums if n.start >= 16.0]
    leads = [n for n in leads if n.start >= 24.0]

    tracks = {
        "pads": pads,
        "synth_bass": bass,
        "drums": drums,
        "leads": leads,
    }

    inst = {
        "pads": PAD_WARM,
        "synth_bass": SYNTH_BASS,
        "drums": DRUMS,
        "leads": CHOIR,  # Choir vocal chops style
    }

    produce_track(
        tracks=tracks,
        bpm=80.0,
        instruments=inst,
        path=OUT / "02_Plugg_Wave.mid",
        mood=Mood.INTIMATE,
        key=key,
        genre="trap",
    )


# =====================================================================
# Track 3: Drift Ghost — 68 BPM — A Aeolian
# =====================================================================
def produce_drift_ghost():
    print("  3. Drift Ghost [A Aeolian — 68 BPM]")
    key = Scale(root=9, mode=Mode.AEOLIAN)  # A Aeolian
    dur = 96.0  # 24 bars
    chords = parse_progression("i:4 VI:4 v7:4 i:4 " * 6, key)

    # Instantiate generator with lower key range to force phonk bass low
    gen = InterceptPhonkGenerator(
        params=GeneratorParams(key_range_low=24, key_range_high=42),
        variant="drift_phonk",
        cowbell_density=0.8,
        bass_slide_amount=6,
        filter_cutoff=0.4,
        memphis_chops=True,
        aggression=0.7
    )
    parted = gen.render_separated(chords, key, dur)

    bass = parted["synth_bass"]
    drums = parted["drums"]
    cowbells = parted["phonk_cowbells"]
    pads = parted["pads"]

    # Scale velocities to resolve low velocity warnings and match phonk aggression
    for n in cowbells:
        n.scale_velocity(1.3)
    for n in pads:
        # Memphis chops style
        n.scale_velocity(1.5)
    for n in bass:
        # Beef up the sliding bass
        n.scale_velocity(1.1)

    # Stagger entrances
    # Bass starts immediately (drift intro)
    drums = [n for n in drums if n.start >= 8.0]
    cowbells = [n for n in cowbells if n.start >= 16.0]
    pads = [n for n in pads if n.start >= 24.0]

    tracks = {
        "synth_bass": bass,
        "drums": drums,
        "phonk_cowbells": cowbells,
        "pads": pads,
    }

    inst = {
        "synth_bass": SYNTH_BASS,
        "drums": DRUMS,
        "phonk_cowbells": COWBELL_BLOCK,
        "pads": PAD_SPACE,
    }

    produce_track(
        tracks=tracks,
        bpm=68.0,
        instruments=inst,
        path=OUT / "03_Drift_Ghost.mid",
        mood=Mood.EXPERIMENTAL,
        key=key,
        genre="trap",
    )


# ------------------------------------------------------------------
# Main production loop
# ------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("   SAKINFO PART II: NEW WAVE DOWNTEMPO TRAP")
    print("   Leveraging Modern Algorithmic Trap Generators")
    print("=" * 60 + "\n")

    produce_cloud_ethereal()
    produce_plugg_wave()
    produce_drift_ghost()

    print("\n" + "=" * 60)
    print("   PRODUCTION COMPLETE: NEW DOWNTEMPO TRAP")
    print(f"   MIDI output saved to: {OUT.absolute()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
