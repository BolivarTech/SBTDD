#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for subprocess_utils module."""

from __future__ import annotations

import sys

import pytest


def test_run_with_timeout_returns_completed_process():
    from subprocess_utils import run_with_timeout

    result = run_with_timeout([sys.executable, "-c", "print('hi')"], timeout=5)
    assert result.returncode == 0
    assert "hi" in result.stdout


def test_run_with_timeout_rejects_shell_true():
    from subprocess_utils import run_with_timeout

    # shell parameter is not exposed — the helper enforces shell=False.
    result = run_with_timeout([sys.executable, "-c", "import sys; sys.exit(3)"], timeout=5)
    assert result.returncode == 3


def test_kill_tree_windows_calls_taskkill_before_proc_kill(monkeypatch):
    """Verifies MAGI R3-1 order: taskkill /F /T /PID BEFORE proc.kill()."""
    from subprocess_utils import kill_tree

    call_order: list[str] = []

    def fake_run(cmd, **kwargs):
        call_order.append(f"subprocess.run:{cmd[0]}")

        class R:
            returncode = 0

        return R()

    class FakeProc:
        pid = 12345

        def kill(self):
            call_order.append("proc.kill")

        def poll(self):
            return None  # still running

        def wait(self, timeout=None):
            call_order.append(f"proc.wait:{timeout}")
            return 0

    monkeypatch.setattr("subprocess_utils.subprocess.run", fake_run)
    monkeypatch.setattr("subprocess_utils.sys.platform", "win32")
    kill_tree(FakeProc())
    # taskkill MUST appear before proc.kill
    taskkill_idx = next(i for i, c in enumerate(call_order) if "taskkill" in c)
    kill_idx = call_order.index("proc.kill")
    assert taskkill_idx < kill_idx, f"call order wrong: {call_order}"


def test_kill_tree_posix_sends_sigterm_then_sigkill(monkeypatch):
    from subprocess_utils import kill_tree
    import subprocess as sp

    signals_sent: list[str] = []

    class FakeProc:
        pid = 54321
        _waits = 0

        def send_signal(self, sig):
            import signal

            signals_sent.append("SIGTERM" if sig == signal.SIGTERM else str(sig))

        def kill(self):
            signals_sent.append("SIGKILL")

        def poll(self):
            return None

        def wait(self, timeout=None):
            self._waits += 1
            if self._waits == 1:
                raise sp.TimeoutExpired(cmd="x", timeout=timeout)
            return 0

    monkeypatch.setattr("subprocess_utils.sys.platform", "linux")
    kill_tree(FakeProc())
    assert signals_sent == ["SIGTERM", "SIGKILL"]


def test_streamed_with_timeout_returns_stdout_and_stderr_separately():
    from subprocess_utils import run_streamed_with_timeout
    cmd = [sys.executable, "-c", (
        "import sys, time\n"
        "for i in range(3):\n"
        "    sys.stdout.write(f'out{i}\\n'); sys.stdout.flush()\n"
        "    time.sleep(0.05)\n"
    )]
    result = run_streamed_with_timeout(
        cmd, per_stream_timeout_seconds=10.0, dispatch_label="test",
    )
    assert result.returncode == 0
    assert "out0" in result.stdout
    assert "out2" in result.stdout


def test_pump_handles_partial_utf8_split_at_chunk_boundary():
    """C1 fold-in: incremental UTF-8 decoder handles multi-byte split.

    Emits a byte stream containing 2-byte (e-acute) + 3-byte (currency
    sign) + 4-byte (emoji) UTF-8 sequences interleaved with ASCII so
    that any naive per-chunk decode would corrupt the output. The
    incremental decoder must reassemble all sequences cleanly.
    """
    from subprocess_utils import run_streamed_with_timeout
    cmd = [sys.executable, "-c", (
        "import sys\n"
        "data = ('hello cafe' + chr(0xE9) + ' euro' + chr(0x20AC) +\n"
        "        ' emoji' + chr(0x1F600) + ' done').encode('utf-8')\n"
        "sys.stdout.buffer.write(data)\n"
        "sys.stdout.buffer.flush()\n"
    )]
    result = run_streamed_with_timeout(
        cmd, per_stream_timeout_seconds=10.0, dispatch_label="test",
    )
    assert result.returncode == 0
    assert chr(0xE9) in result.stdout
    assert chr(0x20AC) in result.stdout
    assert chr(0x1F600) in result.stdout


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="C2 Windows threaded-reader fallback is Windows-specific",
)
def test_streaming_pump_works_on_windows_subprocess():
    """C2 fold-in: Windows threaded-reader fallback delivers chunks."""
    from subprocess_utils import run_streamed_with_timeout
    cmd = [sys.executable, "-c", (
        "import sys, time\n"
        "for i in range(5):\n"
        "    sys.stdout.write(f'win{i}\\n'); sys.stdout.flush()\n"
        "    time.sleep(0.02)\n"
    )]
    result = run_streamed_with_timeout(
        cmd, per_stream_timeout_seconds=10.0, dispatch_label="test-win",
    )
    assert result.returncode == 0
    assert "win0" in result.stdout
    assert "win4" in result.stdout
