import pytest
from melodica.midi import export_multitrack_midi
from melodica.types import NoteInfo

def test_midi_export_structure():
    # Покрытие модуля midi.py
    tracks_data = {
        "TestTrack": [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100)
        ]
    }
    # Тестируем, что экспорт не падает на пустых или простых данных
    try:
        export_multitrack_midi(tracks_data, "test_output.mid", bpm=120, instruments={"TestTrack": 0})
    except Exception as e:
        pytest.fail(f"export_multitrack_midi failed: {e}")
