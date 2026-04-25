#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.3.0 Feature D auto streaming primitives."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import auto_cmd


def test_stream_subprocess_flushes_lines_individually(tmp_path, capfd):
    """D1.1: streaming flushes subprocess output line-by-line within 250ms."""
    script = tmp_path / "emit5.py"
    script.write_text(
        "import sys, time\n"
        "for i in range(5):\n"
        "    print(f'line{i}', flush=True)\n"
        "    time.sleep(0.05)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
    )
    start = time.monotonic()
    auto_cmd._stream_subprocess(proc, prefix="[sbtdd test phase]")
    elapsed = time.monotonic() - start
    proc.wait(timeout=2)
    captured = capfd.readouterr()
    assert "line0" in captured.err
    assert "line4" in captured.err
    assert elapsed < 1.0  # 5 lines * 50ms + slack, not blocking till end


def test_stream_subprocess_applies_prefix(tmp_path, capfd):
    """D1.2: stderr lines carry the supplied prefix."""
    script = tmp_path / "emit_to_stderr.py"
    script.write_text(
        "import sys\nsys.stderr.write('[skill] starting red phase\\n')\nsys.stderr.flush()\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
    )
    auto_cmd._stream_subprocess(proc, prefix="[sbtdd task-7 green]")
    proc.wait(timeout=2)
    captured = capfd.readouterr()
    assert "[sbtdd task-7 green] [skill] starting red phase" in captured.err


def test_subprocess_argv_includes_dash_u():
    """D2.1: auto_cmd subprocess argv is prefixed with python -u."""
    argv = auto_cmd._build_run_sbtdd_argv(subcommand="close-phase", extra_args=["--variant", "fix"])
    assert argv[0:2] == [sys.executable, "-u"]
    assert "run_sbtdd.py" in argv[2]
    assert "close-phase" in argv
    assert "--variant" in argv
    assert "fix" in argv


def test_breadcrumb_on_red_to_green_transition(capfd):
    """D3.1: state-machine emits breadcrumb before phase advance dispatch."""
    auto_cmd._emit_phase_breadcrumb(
        phase=2, total_phases=5, task_index=14, task_total=36, sub_phase="green"
    )
    captured = capfd.readouterr()
    assert "[sbtdd] phase 2/5: task loop -- task 14/36 (green)" in captured.err


def test_breadcrumb_on_task_close_advance(capfd):
    """D3.2: state machine emits breadcrumb when advancing task index."""
    auto_cmd._emit_phase_breadcrumb(
        phase=2, total_phases=5, task_index=15, task_total=36, sub_phase="red"
    )
    captured = capfd.readouterr()
    assert "[sbtdd] phase 2/5: task loop -- task 15/36 (red)" in captured.err


def test_stream_subprocess_flushes_on_sigterm(tmp_path, capfd):
    """D1.3: streaming flushes pending buffers on subprocess termination.

    MAGI iter 1 finding #9 (WARNING) flagged the v0.3.0 baseline as
    not load-bearing: it called ``proc.terminate()`` BEFORE invoking
    ``_stream_subprocess``, so by the time the helper ran the OS
    pipes were already closed and the threads merely drained whatever
    the OS had buffered. That tests "drain closed pipes after
    subprocess exit", a much weaker property than the spec scenario
    D1.3 ("streaming flushes pending buffers a stderr orquestador
    antes de exit 130", i.e. while orchestrator is catching SIGINT
    and subprocess is mid-flight).

    Iter 2 redesign: run ``_stream_subprocess`` on a daemon thread
    BEFORE terminating; assert the pre-terminate output ("first")
    reaches stderr. The streamer is concurrent with the SIGTERM,
    matching the production scenario where the orchestrator catches
    SIGINT mid-stream.
    """
    import threading as _thr

    script = tmp_path / "emit_then_hang.py"
    script.write_text("import sys, time\nprint('first', flush=True)\ntime.sleep(60)\n")
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
    )
    streamer = _thr.Thread(
        target=auto_cmd._stream_subprocess,
        args=(proc, "[sbtdd]"),
        daemon=True,
    )
    streamer.start()
    # Give the streamer time to read and emit "first" while the
    # subprocess is still alive (it then sleeps 60s).
    time.sleep(0.5)
    proc.terminate()
    proc.wait(timeout=5)
    # SIGTERM closes the pipes; iter(stream.readline, "") returns "",
    # the pump exits, and the streamer thread completes.
    streamer.join(timeout=5)
    assert not streamer.is_alive(), "streamer thread did not unwind after terminate"
    captured = capfd.readouterr()
    assert "first" in captured.err
