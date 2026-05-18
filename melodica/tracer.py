# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18 13:56
# Last Updated: 2026-05-18 13:56
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
tracer.py — Unified hierarchical system tracer for Melodica.

Enables context-manager based function call tracing with colors, indentation,
file/line markers, and automatic performance profiling (execution duration).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import FrameType
from typing import Any, Callable, List, Optional, TextIO


class EngineTracer:
    """
    EngineTracer — Unified hierarchical system tracer for Melodica.
    Can be used as a context manager or started/stopped manually.
    
    Usage:
        from melodica.tracer import EngineTracer
        
        with EngineTracer(show_duration=True):
            # Your code to debug/trace
    """
    
    def __init__(
        self,
        output: Optional[TextIO] = None,
        output_path: Optional[str | Path] = None,
        show_private: bool = False,
        show_duration: bool = True,
        max_depth: Optional[int] = None,
        package_name: str = "melodica",
        use_colors: bool = True,
    ) -> None:
        self.output = output or sys.stdout
        self.output_path = Path(output_path) if output_path else None
        self.show_private = show_private
        self.show_duration = show_duration
        self.max_depth = max_depth
        self.package_name = package_name
        self.use_colors = use_colors and self.output.isatty() and not self.output_path
        
        self._file_handle: Optional[TextIO] = None
        self._stack: List[tuple[FrameType, float]] = []
        self._orig_trace: Optional[Callable] = None
        
    def start(self) -> None:
        """Start tracing."""
        if self.output_path:
            self._file_handle = open(self.output_path, "w", encoding="utf-8")
            self.output = self._file_handle
            self.use_colors = False
            
        self._stack = []
        self._orig_trace = sys.gettrace()
        sys.settrace(self._trace_callback)
        
    def stop(self) -> None:
        """Stop tracing."""
        sys.settrace(self._orig_trace)
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
            
    def __enter__(self) -> EngineTracer:
        self.start()
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()
        
    def _trace_callback(self, frame: FrameType, event: str, arg: Any) -> Optional[Callable]:
        if event not in ("call", "return"):
            return self._trace_callback
            
        code = frame.f_code
        func_name = code.co_name
        file_name = code.co_filename
        
        # Check if the file is inside the target package
        package_marker = f"/{self.package_name}/"
        if package_marker not in file_name:
            return None
            
        # Exclude common internal midi files if desired
        if "melodica/midi.py" in file_name:
            return None
            
        # Filter private functions unless requested
        if not self.show_private:
            if func_name.startswith("_") or func_name.startswith("<"):
                return self._trace_callback
                
        # Depth calculation
        depth = 0
        tmp_frame = frame
        while tmp_frame:
            depth += 1
            tmp_frame = tmp_frame.f_back
            
        if self.max_depth is not None and depth > self.max_depth:
            return None
            
        module_path = file_name.split(package_marker)[-1]
        line_no = frame.f_lineno
        
        if event == "call":
            start_time = time.perf_counter()
            self._stack.append((frame, start_time))
            
            indent = "  " * (len(self._stack) - 1)
            
            if self.use_colors:
                # Color code call in cyan (96) and yellow (93) for path, green (92) for function
                msg = f"{indent}\033[96m--> CALL\033[0m [\033[93m{module_path}:{line_no}\033[0m]: \033[92m{func_name}()\033[0m"
            else:
                msg = f"{indent}--> CALL [{module_path}:{line_no}]: {func_name}()"
                
            self.output.write(msg + "\n")
            
        elif event == "return":
            # Match call frame to calculate duration
            duration_str = ""
            if self.show_duration:
                # Find matching frame in stack
                match_idx = -1
                for idx, (f, _) in enumerate(reversed(self._stack)):
                    if f is frame:
                        match_idx = len(self._stack) - 1 - idx
                        break
                        
                if match_idx != -1:
                    _, start_time = self._stack.pop(match_idx)
                    dur = time.perf_counter() - start_time
                    duration_str = f" ({dur * 1000.0:.2f}ms)"
                else:
                    # If matching frame not found in stack, clean up stack if overflow
                    if self._stack:
                        self._stack.pop()
            else:
                if self._stack:
                    self._stack.pop()
                    
            indent = "  " * len(self._stack)
            
            if self.use_colors:
                # Color code return in magenta (95) and gray (90) for duration
                msg = f"{indent}\033[95m<-- RETN\033[0m [\033[93m{module_path}\033[0m]: \033[92m{func_name}()\033[0m\033[90m{duration_str}\033[0m"
            else:
                msg = f"{indent}<-- RETN [{module_path}]: {func_name}(){duration_str}"
                
            self.output.write(msg + "\n")
            
        return self._trace_callback
