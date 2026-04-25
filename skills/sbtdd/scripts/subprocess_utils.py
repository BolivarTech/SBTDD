#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.1.0
# Date: 2026-04-25
"""Subprocess wrappers enforcing sec.S.8.6 conventions.

- shell=False always.
- Arguments as lists, not strings.
- Explicit timeouts.
- Windows kill-tree via taskkill /F /T /PID BEFORE proc.kill() (MAGI R3-1).

v0.3.0 (MAGI iter 2 finding #1 + #7 fix): :func:`run_with_timeout`
gains an optional ``stream_prefix`` kwarg. With ``stream_prefix=None``
(default) behavior is byte-identical to v0.2.x (``subprocess.run``
with ``capture_output=True``). With ``stream_prefix`` set, the helper
switches to ``subprocess.Popen`` + :func:`auto_cmd._stream_subprocess`
so subprocess output reaches the operator's stderr line-by-line during
execution. The returned object remains :class:`subprocess.CompletedProcess`
for compat with all 30+ existing callers.
"""

from __future__ import annotations

import signal
import subprocess
import sys
from typing import Any


def run_with_timeout(
    cmd: list[str],
    timeout: int,
    capture: bool = True,
    cwd: str | None = None,
    *,
    stream_prefix: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with shell=False and an explicit timeout.

    Args:
        cmd: Command as list of strings (never a single string).
        timeout: Wall-clock seconds before SIGTERM.
        capture: If True, capture stdout/stderr as text. Ignored when
            ``stream_prefix`` is set (streaming mode always captures and
            tees the output to stderr).
        cwd: Working directory (None = current).
        stream_prefix: When set, switch to ``subprocess.Popen`` +
            :func:`auto_cmd._stream_subprocess` so subprocess output
            reaches the operator's stderr line-by-line during execution.
            The accumulated ``(stdout, stderr)`` strings are still
            returned via the :class:`subprocess.CompletedProcess` shape
            so callers stay compatible. When ``None`` (default) the
            helper preserves the v0.2.x ``subprocess.run`` path
            byte-identically.

    Returns:
        CompletedProcess with returncode, stdout, stderr.

    Raises:
        subprocess.TimeoutExpired: If the process did not finish in time.
    """
    if stream_prefix is None:
        return subprocess.run(
            cmd,
            shell=False,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )

    # Streaming path: spawn via Popen with line-buffered text pipes,
    # delegate the read+tee to auto_cmd._stream_subprocess (already
    # battle-tested by the D1.x unit tests), then synthesise a
    # CompletedProcess so existing callers see the v0.2.x return shape.
    #
    # Lazy-import auto_cmd to avoid a circular import: subprocess_utils
    # is imported by auto_cmd at module level; importing auto_cmd here
    # at call time breaks the cycle.
    from auto_cmd import _stream_subprocess

    proc: subprocess.Popen[str] = subprocess.Popen(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=cwd,
    )
    try:
        stdout_text, stderr_text = _stream_subprocess(proc, stream_prefix)
        # Wait with the wall-clock timeout enforced. The streamer has
        # already drained the pipes (they returned EOF), so this call
        # is normally non-blocking; the timeout is belt-and-suspenders
        # for the pathological 'subprocess wrote to closed pipe but
        # never exited' edge case.
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        raise
    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode,
        stdout=stdout_text,
        stderr=stderr_text,
    )


def kill_tree(proc: subprocess.Popen[Any]) -> None:
    """Terminate process and all children cross-platform.

    Windows: taskkill /F /T /PID <pid> BEFORE proc.kill() (MAGI R3-1 —
    parent must still be alive for taskkill to enumerate its descendants).
    POSIX: SIGTERM + 3-second wait + SIGKILL fallback.

    Args:
        proc: Running Popen instance. Generic parameter is :data:`Any` to
            accept both ``Popen[str]`` (text mode) and ``Popen[bytes]``
            (binary pipelines, e.g. ``rust_reporter`` piping JSON bytes
            from ``cargo nextest`` into ``tdd-guard-rust``).
    """
    if proc.poll() is not None:
        return  # Already exited.
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                shell=False,
                capture_output=True,
                timeout=5,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Fall through to proc.kill as belt-and-suspenders.
        proc.kill()
        proc.wait(timeout=5)
    else:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
