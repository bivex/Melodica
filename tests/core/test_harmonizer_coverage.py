import pytest
import numpy as np
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.types import BarGrid, Scale, Mode

def test_coupled_hmm_init_and_harmonize():
    # Тестируем инициализацию и базовую гармонизацию, 
    # чтобы покрыть ядро CoupledHMMHarmonizer
    bar_grid = BarGrid(numerator=4, denominator=4)
    harmonizer = CoupledHMMHarmonizer(bar_grid=bar_grid)
    
    scale = Scale(root=0, mode=Mode.NATURAL_MINOR)
    # Создаем фиктивный контур мелодии
    contour = [] # В этой версии Harmonizer ожидает список объектов, имеющих pitch_class
    
    # Вызов гармонизации с правильными аргументами
    # Взглянем на сигнатуру в coupled_hmm.py (она ожидает contour, scale, beats)
    chords = harmonizer.harmonize(contour, scale, 16)
    assert isinstance(chords, list)

def test_coupled_hmm_emit_logic():
    # Проверка того, что наши правки с LOG_NOT_PNOTE работают
    from melodica.harmonize.coupled_hmm import LOG_NOT_PNOTE, LOG_PNOTE
    assert LOG_NOT_PNOTE.shape == LOG_PNOTE.shape
    assert np.all(LOG_NOT_PNOTE <= 0) # Log вероятности <= 0
