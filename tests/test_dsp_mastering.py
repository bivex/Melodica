# Copyright (c) 2026 Bivex
#
# Licensed: MIT

import pytest
import numpy as np
from pathlib import Path
from melodica.dsp_mastering import DSPMasteringDesk, PEDALBOARD_AVAILABLE

def test_dsp_mastering_init():
    """Verify that the mastering desk initializes correctly for all styles."""
    for style in ["pop_synthwave", "trap_drill", "ambient_classical", "lofi"]:
        desk = DSPMasteringDesk(style=style, target_lufs=-12.0, true_peak_ceiling=-1.0)
        assert desk.style == style
        assert desk.target_lufs == -12.0
        assert desk.ceiling == -1.0
        assert desk.sample_rate == 44100

def test_dsp_mastering_presets():
    """Ensure that the correct pedalboard plugin chain is constructed if available."""
    if not PEDALBOARD_AVAILABLE:
        pytest.skip("pedalboard library is not installed.")

    # 1. Pop Synthwave (Default SSL / clipping / high shelf)
    desk_pop = DSPMasteringDesk(style="pop_synthwave")
    plugins_pop = desk_pop._get_preset_chain()
    assert len(plugins_pop) >= 3
    plugin_names_pop = [type(p).__name__ for p in plugins_pop]
    assert any("Highpass" in name for name in plugin_names_pop)
    assert any("Compressor" in name for name in plugin_names_pop)
    assert any("Clipping" in name for name in plugin_names_pop)

    # 2. Trap/Drill (deep sub preservation, hard clipping)
    desk_trap = DSPMasteringDesk(style="trap_drill")
    plugins_trap = desk_trap._get_preset_chain()
    plugin_names_trap = [type(p).__name__ for p in plugins_trap]
    assert any("Clipping" in name for name in plugin_names_trap)

    # 3. Ambient/Classical (no saturation, wide premium space reverb)
    desk_ambient = DSPMasteringDesk(style="ambient_classical")
    plugins_ambient = desk_ambient._get_preset_chain()
    plugin_names_ambient = [type(p).__name__ for p in plugins_ambient]
    assert any("Reverb" in name for name in plugin_names_ambient)
    assert not any("Clipping" in name for name in plugin_names_ambient)
    assert not any("Distortion" in name for name in plugin_names_ambient)

    # 4. Lo-Fi (vintage roll-off, distortion, bitcrusher sampler grit)
    desk_lofi = DSPMasteringDesk(style="lofi")
    plugins_lofi = desk_lofi._get_preset_chain()
    plugin_names_lofi = [type(p).__name__ for p in plugins_lofi]
    assert any("Bitcrush" in name for name in plugin_names_lofi)
    assert any("Distortion" in name for name in plugin_names_lofi)

def test_dsp_mastering_normalization_gain():
    """Verify that loudness normalization works correctly."""
    desk = DSPMasteringDesk(target_lufs=-12.0)
    
    # Generate quiet stereo sine wave
    t = np.linspace(0, 1, 44100, endpoint=False)
    sine = np.sin(2 * np.pi * 440 * t) * 0.05
    stereo = np.vstack([sine, sine])
    
    rms_before = np.sqrt(np.mean(stereo ** 2))
    
    # Process loudness normalization math manually or through helper
    normalized = desk._normalize_loudness(stereo)
    rms_after = np.sqrt(np.mean(normalized ** 2))
    
    # The normalized audio should have a significantly larger RMS amplitude to match the target
    assert rms_after > rms_before
    # Target -12.0 LUFS maps to ~ -12.0 dBFS RMS
    expected_rms = 10 ** (-12.0 / 20.0)
    assert np.allclose(rms_after, expected_rms, rtol=1e-2)

def test_dsp_mastering_limiting_and_ceiling():
    """Verify that the brickwall limiter strictly honors the output ceiling."""
    # Let's target a very loud LUFS and ceiling of -1.5 dBFS (approx 0.84 amplitude)
    desk = DSPMasteringDesk(target_lufs=-6.0, true_peak_ceiling=-1.5)
    
    # Generate massive stereo sine wave with huge overload peaks (+2.0 amplitude)
    t = np.linspace(0, 1, 44100, endpoint=False)
    overload = np.sin(2 * np.pi * 440 * t) * 2.0
    stereo_overload = np.vstack([overload, overload])
    
    mastered = desk.process(stereo_overload)
    
    # Max peak amplitude must not exceed the ceiling factor
    ceiling_factor = 10 ** (-1.5 / 20.0)
    max_peak = np.max(np.abs(mastered))
    
    assert max_peak <= ceiling_factor + 1e-5
    # Ensure there is no massive clipping artifacts and the signal remains bounded
    assert max_peak > 0.5

def test_dsp_mastering_silent_or_empty_audio():
    """Ensure that empty or completely silent audio does not trigger division by zero."""
    desk = DSPMasteringDesk()
    
    # Empty audio
    empty = np.array([[], []], dtype=np.float32)
    res_empty = desk.process(empty)
    assert res_empty.size == 0
    
    # Silent audio
    silent = np.zeros((2, 1000), dtype=np.float32)
    res_silent = desk.process(silent)
    assert np.all(res_silent == 0.0)
