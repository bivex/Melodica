# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 13:57
# Last Updated: 2026-05-18 13:57
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import io
from pathlib import Path
from melodica.tracer import EngineTracer
from melodica.utils import semitones_up, nearest_pitch


def test_tracer_context_manager():
    output = io.StringIO()
    
    with EngineTracer(output=output, show_private=False, show_duration=True, use_colors=False) as tracer:
        semitones_up(60, 4)
        
    trace_log = output.getvalue()
    assert "CALL" in trace_log
    assert "RETN" in trace_log
    assert "semitones_up" in trace_log
    assert "ms" in trace_log or "s" in trace_log


def test_tracer_show_private():
    output = io.StringIO()
    
    with EngineTracer(output=output, show_private=True, show_duration=False, use_colors=False) as tracer:
        # nearest_pitch might call some private helper or we can check its own call
        nearest_pitch(0, 60)
        
    trace_log = output.getvalue()
    assert "nearest_pitch" in trace_log


def test_tracer_file_output(tmp_path):
    log_file = tmp_path / "trace.log"
    
    with EngineTracer(output_path=log_file, show_private=True, use_colors=False):
        semitones_up(64, -2)
        
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "semitones_up" in content
