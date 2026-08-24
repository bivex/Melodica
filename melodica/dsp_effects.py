# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
melodica/dsp_effects.py — Custom Commercial DSP Effects.

A suite of high-end mixing tools built purely on NumPy math, bypassing the need
for heavy VST plugins. Implements industry-standard secrets like Auto-Ducking
(Sidechain), the Haas Stereo Effect, and Drum Clipping.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
import numpy as np


def normalize_peak(audio: np.ndarray, peak_target: float = 0.9) -> np.ndarray:
    """Normalize audio array to peak_target (e.g. 0.9 for -0.92 dBFS headroom)."""
    if audio.size == 0:
        return audio
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio / peak * peak_target
    return audio


class AudioEffect(typing.Protocol):
    """Protocol for all DSP audio effects and processors."""

    def process(self, audio: np.ndarray) -> np.ndarray: ...


@dataclass
class EffectSlot:
    """An effect slot in the DSPPipeline with independent dry/wet and bypass."""

    effect: AudioEffect
    dry_wet: float = 1.0  # 0.0 = 100% dry, 1.0 = 100% wet
    bypassed: bool = False


class DSPPipeline:
    """
    Non-destructive Pipes & Filters chain for audio effects and DSP processors.
    Supports dynamic reordering, per-effect dry/wet blending, and bypass.
    """

    def __init__(self, effects: list[AudioEffect | tuple[AudioEffect, float]] | None = None) -> None:
        self.slots: list[EffectSlot] = []
        if effects:
            for item in effects:
                if isinstance(item, tuple):
                    self.add(item[0], dry_wet=item[1])
                else:
                    self.add(item)

    def add(self, effect: AudioEffect, dry_wet: float = 1.0) -> DSPPipeline:
        """Appends an effect to the end of the chain. Returns self for fluent chaining."""
        self.slots.append(EffectSlot(effect=effect, dry_wet=max(0.0, min(1.0, dry_wet))))
        return self

    def insert(self, index: int, effect: AudioEffect, dry_wet: float = 1.0) -> DSPPipeline:
        """Inserts an effect at the specified position."""
        self.slots.insert(index, EffectSlot(effect=effect, dry_wet=max(0.0, min(1.0, dry_wet))))
        return self

    def remove(self, index: int) -> AudioEffect:
        """Removes and returns the effect at the specified position."""
        return self.slots.pop(index).effect

    def set_bypass(self, index: int, bypass: bool = True) -> DSPPipeline:
        """Toggles bypass state for the effect at index."""
        if 0 <= index < len(self.slots):
            self.slots[index].bypassed = bypass
        return self

    def set_dry_wet(self, index: int, dry_wet: float) -> DSPPipeline:
        """Sets dry/wet blend factor (0.0 to 1.0) for the effect at index."""
        if 0 <= index < len(self.slots):
            self.slots[index].dry_wet = max(0.0, min(1.0, dry_wet))
        return self

    def clear(self) -> DSPPipeline:
        """Clears all effects from the pipeline."""
        self.slots.clear()
        return self

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Processes the stereo audio array through all active effect slots."""
        if audio.size == 0:
            return audio

        current = audio
        for slot in self.slots:
            if slot.bypassed or slot.dry_wet <= 0.0:
                continue

            processed = slot.effect.process(current)

            if slot.dry_wet >= 1.0:
                current = processed
            else:
                # Dry / Wet linear blend
                current = (current * (1.0 - slot.dry_wet)) + (processed * slot.dry_wet)

        return current


class ParallelDSP:
    """
    Parallel signal splitter and summing bus.
    Applies multiple audio effects to clones of the input signal in parallel and sums the result.
    """

    def __init__(self, branches: list[tuple[AudioEffect, float]] | None = None) -> None:
        # List of (effect, gain_multiplier)
        self.branches: list[tuple[AudioEffect, float]] = list(branches) if branches else []

    def add_branch(self, effect: AudioEffect, mix: float = 1.0) -> ParallelDSP:
        self.branches.append((effect, mix))
        return self

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0 or not self.branches:
            return audio

        summed = np.zeros_like(audio)
        for effect, mix in self.branches:
            branch_out = effect.process(audio) * mix
            summed += branch_out

        # Peak limiter ceiling to prevent digital clipping
        peak = np.max(np.abs(summed))
        if peak > 0.99:
            summed = summed / peak * 0.99

        return summed


class AutoPumper:
    """
    Rhythmic Sidechain/Volume Ducking Simulator.

    Creates that classic EDM/Trap "pumping" effect by rhythmically dipping
    the volume at the start of every beat and smoothly recovering it.
    """

    def __init__(
        self, bpm: float, depth: float = 1.0, shape: float = 2.0, sample_rate: int = 44100
    ):
        """
        Parameters
        ----------
        bpm : float
            Tempo of the track in Beats Per Minute.
        depth : float
            How deep the volume ducks. 1.0 means complete silence at the hit,
            0.5 means it only ducks by half. (Range: 0.0 to 1.0)
        shape : float
            Curve shape. 1.0 = linear rise, >1.0 = stays down longer then snaps up,
            <1.0 = recovers instantly. 2.0 to 4.0 is standard for a bouncy feel.
        sample_rate : int
            Audio sample rate.
        """
        self.bpm = bpm
        self.depth = np.clip(depth, 0.0, 1.0)
        self.shape = shape
        self.sample_rate = sample_rate

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio

        samples = audio.shape[1]
        samples_per_beat = self.sample_rate * (60.0 / self.bpm)

        # Create a repeating normalized time array (0.0 to 1.0 for every beat)
        t = (np.arange(samples) % samples_per_beat) / samples_per_beat

        # Envelope curve: starts at 0.0, curves up to 1.0
        # np.sin(t * np.pi / 2) creates a smooth quarter-sine curve
        rise_curve = np.sin(t * np.pi / 2.0) ** self.shape

        # Mix the depth: if depth=1.0, volume multiplier goes 0.0 -> 1.0.
        # If depth=0.5, volume multiplier goes 0.5 -> 1.0.
        envelope = (1.0 - self.depth) + (self.depth * rise_curve)

        # Apply envelope to both Left and Right channels
        return audio * envelope


class HaasWidener:
    """
    Haas Effect Psychoacoustic Stereo Widener.

    Creates an impossibly wide stereo image by delaying one channel by a few
    milliseconds. Extremely effective on pads, plucks, and background vocals.
    WARNING: Do not use on low bass, as it destroys mono compatibility!
    """

    def __init__(self, delay_ms: float = 15.0, delay_right: bool = True, sample_rate: int = 44100):
        """
        Parameters
        ----------
        delay_ms : float
            Delay time in milliseconds (typically 10 to 30 ms).
        delay_right : bool
            If True, delays the right channel. If False, delays the left.
        sample_rate : int
            Audio sample rate.
        """
        self.delay_ms = delay_ms
        self.delay_right = delay_right
        self.sample_rate = sample_rate

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0 or audio.shape[0] < 2:
            return audio

        delay_samples = int((self.delay_ms / 1000.0) * self.sample_rate)
        if delay_samples == 0:
            return audio

        processed = np.copy(audio)

        # We need to shift one channel to the right (delay it) by `delay_samples`.
        # We pad the beginning with zeros and truncate the end to maintain length.
        channel_to_delay = 1 if self.delay_right else 0

        delayed_signal = np.zeros_like(processed[channel_to_delay])
        delayed_signal[delay_samples:] = processed[channel_to_delay][:-delay_samples]

        processed[channel_to_delay] = delayed_signal

        return processed


class HardClipper:
    """
    Drum Hard Clipper.

    Instantly shaves off transient peaks above a certain threshold, generating
    aggressive digital harmonics and allowing for massive volume boosts on
    drums without the "pumping" artifacts of a traditional limiter.
    """

    def __init__(self, threshold_db: float = -3.0, makeup_db: float = 3.0):
        self.threshold_linear = 10 ** (threshold_db / 20.0)
        self.makeup_linear = 10 ** (makeup_db / 20.0)

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio

        soft_clipped = np.tanh(audio / self.threshold_linear) * self.threshold_linear
        return soft_clipped * self.makeup_linear


class TransientShaper:
    """
    Transient Exciter / Shaper.

    Adds "snap" and "smack" to drums by extracting the high-frequency attack
    transients, creating an envelope, and mixing them back into the signal.
    """

    def __init__(self, attack_boost: float = 2.0, sample_rate: int = 44100):
        self.attack_boost = attack_boost
        self.sample_rate = sample_rate

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio

        try:
            import scipy.signal

            # High-pass filter to isolate the "click" of the transients (> 5000 Hz)
            b, a = scipy.signal.butter(1, 5000.0 / (self.sample_rate / 2.0), btype="high")
            transients = scipy.signal.lfilter(b, a, audio)

            # Create a simple envelope (rectify and smooth)
            envelope = np.abs(transients)

            # Boost the original signal where the transient envelope is high
            return audio + (audio * envelope * self.attack_boost)
        except ImportError:
            # Fallback if scipy is not installed
            return audio


class MultibandSaturator:
    """
    808 / Sub-Bass Multiband Saturator.

    Splits the audio into sub-bass (clean) and mid/high frequencies (distorted).
    Allows sub-bass to remain pure (no mud) while generating upper harmonics
    so the bass can be heard on smartphone speakers.
    """

    def __init__(
        self, crossover_hz: float = 150.0, drive_db: float = 12.0, sample_rate: int = 44100
    ):
        self.crossover_hz = crossover_hz
        self.drive_linear = 10 ** (drive_db / 20.0)
        self.sample_rate = sample_rate

    def process(self, audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio

        try:
            import scipy.signal

            nyq = self.sample_rate / 2.0

            # Split into Low and High bands
            b_low, a_low = scipy.signal.butter(2, self.crossover_hz / nyq, btype="low")
            b_high, a_high = scipy.signal.butter(2, self.crossover_hz / nyq, btype="high")

            low_band = scipy.signal.lfilter(b_low, a_low, audio)
            high_band = scipy.signal.lfilter(b_high, a_high, audio)

            # Apply heavy Tanh saturation ONLY to the high band
            driven_high = high_band * self.drive_linear
            saturated_high = np.tanh(driven_high)

            # Recombine the pristine low band with the saturated high band
            return low_band + saturated_high
        except ImportError:
            # Fallback analog saturation on the whole signal
            driven = audio * self.drive_linear
            return np.tanh(driven)
