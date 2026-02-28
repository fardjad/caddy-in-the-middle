from __future__ import annotations

import fcntl
import subprocess

import pytest

from mitmproxy.har import (
    HarGenerationInProgressError,
    build_har_command,
    generate_har,
)


def test_build_har_command_uses_flow_and_output_paths():
    command = build_har_command(
        flow_path="/tmp/input.flow",
        output_path="/tmp/output.har",
    )
    assert command == [
        "mitmdump",
        "-nr",
        "/tmp/input.flow",
        "--set",
        "hardump=/tmp/output.har",
    ]


def test_generate_har_runs_runner_and_returns_output_path(tmp_path):
    command_calls: list[list[str]] = []

    def fake_runner(command):
        command_calls.append(list(command))

    lock_path = tmp_path / "har.lock"
    flow_path = tmp_path / "dump.flow"
    output_path = tmp_path / "dump.har"

    result = generate_har(
        runner=fake_runner,
        lock_path=str(lock_path),
        flow_path=str(flow_path),
        output_path=str(output_path),
    )

    assert result == str(output_path)
    assert command_calls == [
        [
            "mitmdump",
            "-nr",
            str(flow_path),
            "--set",
            f"hardump={output_path}",
        ]
    ]


def test_generate_har_raises_when_generation_is_in_progress(tmp_path):
    lock_path = tmp_path / "har.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

        with pytest.raises(HarGenerationInProgressError):
            generate_har(
                runner=lambda _command: None,
                lock_path=str(lock_path),
                flow_path=str(tmp_path / "dump.flow"),
                output_path=str(tmp_path / "dump.har"),
            )


def test_generate_har_bubbles_runner_failures(tmp_path):
    lock_path = tmp_path / "har.lock"

    def failing_runner(command):
        raise subprocess.CalledProcessError(1, command)

    with pytest.raises(subprocess.CalledProcessError):
        generate_har(
            runner=failing_runner,
            lock_path=str(lock_path),
            flow_path=str(tmp_path / "dump.flow"),
            output_path=str(tmp_path / "dump.har"),
        )
