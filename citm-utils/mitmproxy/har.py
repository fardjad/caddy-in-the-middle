import fcntl
import subprocess
from collections.abc import Callable, Sequence

MITMPROXY_DATA_DIR = "/var/lib/mitmproxy"
HAR_LOCK_PATH = f"{MITMPROXY_DATA_DIR}/har.lock"
MITM_FLOW_PATH = f"{MITMPROXY_DATA_DIR}/dump.flow"
HAR_OUTPUT_PATH = f"{MITMPROXY_DATA_DIR}/dump.har"


class HarGenerationInProgressError(Exception):
    pass


def build_har_command(*, flow_path: str, output_path: str) -> list[str]:
    return [
        "uv",
        "tool",
        "run",
        "--from",
        "mitmproxy",
        "mitmdump",
        "-nr",
        flow_path,
        "--set",
        f"hardump={output_path}",
    ]


def generate_har(
    *,
    runner: Callable[[Sequence[str]], None] = subprocess.check_call,
    lock_path: str = HAR_LOCK_PATH,
    flow_path: str = MITM_FLOW_PATH,
    output_path: str = HAR_OUTPUT_PATH,
) -> str:
    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HarGenerationInProgressError() from exc

        runner(build_har_command(flow_path=flow_path, output_path=output_path))

    return output_path
