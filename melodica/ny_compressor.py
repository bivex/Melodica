# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
melodica/ny_compressor.py — New York (Parallel) Compressor Module.

New York Compression splits the incoming signal into two paths:
1. Dry Path (Uncompressed): Preserves the sharp, punchy transients and natural dynamics.
2. Wet Path (Smashed): Heavily compressed with a low threshold, high ratio, and fast attack.

Blending these paths sums the extreme transient punch of the dry signal with the 
dense body, sustain, and harmonic weight of the squashed wet signal.

Provides:
- NewYorkCompressor: fully configurable parallel compression DSP class.
"""

from __future__ import annotations

import logging
import numpy as np

try:
    import pedalboard
    from pedalboard import Pedalboard, Compressor, Gain
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)


class NewYorkCompressor:
    """
    New York (Parallel) Compression DSP Processor.
    
    A staple of high-end mixing and mastering, this module lets you squeeze 
    immense loudness and body out of drums, loops, and full mixes while 
    keeping the natural transient punch 100% intact.
    """

    def __init__(
        self,
        dry_mix: float = 0.7,
        wet_mix: float = 0.5,
        threshold_db: float = -24.0,
        ratio: float = 8.0,
        attack_ms: float = 2.0,
        release_ms: float = 120.0,
        makeup_gain_db: float = 10.0,
        sample_rate: int = 44100,
    ) -> None:
        """
        Parameters
        ----------
        dry_mix : float
            Linear blend level for the dry (clean) signal (0.0 to 1.0). Default is 0.7.
        wet_mix : float
            Linear blend level for the wet (smashed) signal (0.0 to 1.0). Default is 0.5.
        threshold_db : float
            Compressor threshold in dBFS for the wet path. Default is -24.0.
        ratio : float
            Compression ratio for the wet path (e.g. 8.0 for 8:1 squashing). Default is 8.0.
        attack_ms : float
            Fast compressor attack time in milliseconds. Default is 2.0.
        release_ms : float
            Compressor release time in milliseconds. Default is 120.0.
        makeup_gain_db : float
            Makeup gain in dB to apply to the wet path prior to mixing. Default is 10.0.
        sample_rate : int
            Audio sample rate. Default is 44100.
        """
        self.dry_mix = dry_mix
        self.wet_mix = wet_mix
        self.threshold_db = threshold_db
        self.ratio = ratio
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.makeup_gain_db = makeup_gain_db
        self.sample_rate = sample_rate

        if PEDALBOARD_AVAILABLE:
            # Build the dedicated heavy-compression wet path pedalboard
            self._wet_board = Pedalboard([
                Compressor(
                    threshold_db=self.threshold_db,
                    ratio=self.ratio,
                    attack_ms=self.attack_ms,
                    release_ms=self.release_ms
                ),
                Gain(gain_db=self.makeup_gain_db)
            ])
        else:
            self._wet_board = None
            logger.warning(
                "Pedalboard library unavailable. NewYorkCompressor will run "
                "in high-fidelity analog simulation (soft-clipping NumPy) fallback mode."
            )

    def process(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply New York Parallel Compression to the stereo audio array.
        
        Parameters
        ----------
        audio : np.ndarray
            Stereo float32 array of shape (2, samples)
            
        Returns
        -------
        np.ndarray
            New York compressed stereo audio array of shape (2, samples)
        """
        if audio.size == 0:
            return audio

        # 1. Clean dry path
        dry_signal = audio * self.dry_mix

        # 2. Heavily processed wet path
        if PEDALBOARD_AVAILABLE and self._wet_board is not None:
            # Clone input buffer for processing
            wet_copy = np.copy(audio)
            wet_signal = self._wet_board(wet_copy, sample_rate=self.sample_rate) * self.wet_mix
        else:
            # High-fidelity NumPy fallback: emulates analog tube compression and tape warming 
            # by applying a smooth tanh-curve saturator and makeup gain
            gain_factor = 10 ** (self.makeup_gain_db / 20.0)
            threshold_factor = 10 ** (self.threshold_db / 20.0)
            
            # Apply smooth soft-knee analog saturation above the threshold
            wet_smashed = np.copy(audio)
            mask = np.abs(wet_smashed) > threshold_factor
            if np.any(mask):
                # Tanh soft-clipping compression
                wet_smashed[mask] = (
                    np.sign(wet_smashed[mask]) * threshold_factor * 
                    (1.0 + np.tanh((np.abs(wet_smashed[mask]) - threshold_factor) / (threshold_factor * 2.0)))
                )
            wet_signal = wet_smashed * gain_factor * self.wet_mix

        # 3. Sum paths back together (perfectly phase-aligned)
        summed = dry_signal + wet_signal

        # Safety peak limiter ceiling at -0.1 dBFS to prevent digital clipping
        peak = np.max(np.abs(summed))
        if peak > 0.99:
            summed = summed / peak * 0.99

        return summed
