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
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import auto_cmd
import subprocess_utils


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


# ----- iter 2 finding #1 + #7: production wiring of streaming -----
#
# The v0.3.0 baseline shipped _stream_subprocess + _build_run_sbtdd_argv
# as helpers BUT no production caller used them. Every dispatch
# subprocess invocation flowed through subprocess_utils.run_with_timeout
# which used subprocess.run(..., capture_output=True) -- a blocking call
# that returned one CompletedProcess after EOF.
#
# Iter 2 fix: subprocess_utils.run_with_timeout gains an optional
# stream_prefix kwarg. With stream_prefix=None (default) behavior is
# byte-identical to v0.2.x. With stream_prefix set, the helper switches
# to subprocess.Popen + auto_cmd._stream_subprocess(proc, prefix). The
# returned object is still CompletedProcess for compat with all 30+
# existing callers.


def test_run_with_timeout_no_stream_prefix_uses_subprocess_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Iter 2 finding #1: stream_prefix=None preserves v0.2.x subprocess.run path.

    The helper must call subprocess.run -- NOT subprocess.Popen -- when
    no stream_prefix is supplied. This guarantees byte-identical
    behavior for the 30+ callers that did not opt into streaming
    (commits, dependency_check, drift, finalize, resume, etc.).
    """
    captured: dict[str, Any] = {}

    class _CompletedStub:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = "ok"
            self.stderr = ""

    def fake_run(cmd: list[str], **kwargs: Any) -> _CompletedStub:
        captured["called_run"] = True
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return _CompletedStub()

    def fake_popen(*args: Any, **kwargs: Any) -> Any:
        captured["called_popen"] = True
        raise AssertionError("Popen must not be called when stream_prefix is None")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    result = subprocess_utils.run_with_timeout(["echo", "hi"], timeout=5)
    assert captured.get("called_run") is True
    assert captured.get("called_popen") is None
    assert result.returncode == 0


def test_run_with_timeout_with_stream_prefix_uses_popen_and_stream(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """Iter 2 finding #1 + #7: stream_prefix triggers Popen + _stream_subprocess.

    This is the END-TO-END regression: when a caller opts into
    streaming via the new stream_prefix kwarg, the helper MUST switch
    to Popen + the existing auto_cmd._stream_subprocess pump. This is
    what wires the line-buffered output guarantee from D1.x scenarios
    into the production auto path.
    """
    proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys; sys.stdout.write('hello\\n'); sys.stdout.flush(); "
            "sys.stderr.write('err1\\n'); sys.stderr.flush()",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
    )

    invoked: dict[str, Any] = {}

    class _RecordingPopen:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            invoked["popen_args"] = args
            invoked["popen_kwargs"] = kwargs
            # Hand off to the real pre-spawned process so the streamer
            # has actual data to consume.
            self._inner = proc

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

    monkeypatch.setattr(subprocess, "Popen", _RecordingPopen)

    result = subprocess_utils.run_with_timeout(
        [sys.executable, "-u", "-c", "print('inert')"],
        timeout=5,
        stream_prefix="[sbtdd test wiring]",
    )
    proc.wait(timeout=5)

    captured = capfd.readouterr()
    assert "popen_args" in invoked, "Popen was not used when stream_prefix supplied"
    assert "[sbtdd test wiring] hello" in captured.err
    assert "[sbtdd test wiring] err1" in captured.err
    assert result.returncode == 0


def test_invoke_skill_propagates_stream_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Iter 2 finding #1 + #7: superpowers_dispatch.invoke_skill threads stream_prefix.

    Verifies the kwarg is forwarded from the dispatch wrapper into
    subprocess_utils.run_with_timeout so the auto path's
    'invoke skill with prefix' contract reaches the underlying
    subprocess machinery without being silently dropped.
    """
    import superpowers_dispatch

    received: dict[str, Any] = {}

    class _CompletedStub:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(cmd: list[str], **kwargs: Any) -> _CompletedStub:  # noqa: ARG001
        received["kwargs"] = kwargs
        return _CompletedStub()

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)

    superpowers_dispatch.invoke_skill(
        "test-driven-development",
        args=["--phase=red"],
        timeout=10,
        stream_prefix="[sbtdd task-7 red]",
    )
    assert received.get("kwargs", {}).get("stream_prefix") == "[sbtdd task-7 red]"


def test_invoke_magi_propagates_stream_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Iter 2 finding #1 + #7: magi_dispatch.invoke_magi threads stream_prefix."""
    import magi_dispatch

    received: dict[str, Any] = {}

    class _CompletedStub:
        returncode = 1  # short-circuit early so we don't need a real magi-report.json
        stdout = ""
        # Match quota_detector.QUOTA_PATTERNS["rate_limit_429"] so the
        # MAGIGateError is suppressed in favor of QuotaExhaustedError;
        # we want to assert the kwarg propagated BEFORE the error fires.
        stderr = "Request rejected (429)"

    def fake_run(cmd: list[str], **kwargs: Any) -> _CompletedStub:  # noqa: ARG001
        received["kwargs"] = kwargs
        return _CompletedStub()

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)

    # We expect QuotaExhaustedError because we faked a quota match in stderr;
    # the streamer kwarg propagation is what we are asserting (it must reach
    # run_with_timeout BEFORE the error is raised).
    from errors import QuotaExhaustedError

    with pytest.raises(QuotaExhaustedError):
        magi_dispatch.invoke_magi(
            ["spec-behavior.md"],
            timeout=10,
            stream_prefix="[sbtdd magi loop2]",
        )
    assert received.get("kwargs", {}).get("stream_prefix") == "[sbtdd magi loop2]"
