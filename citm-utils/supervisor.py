import os
import socket
import http.client
import xmlrpc.client
import time
from typing import Any, Dict, List, Optional

# Internal: processes we never want to manage via the UI/API
_EXCLUDED_PROCESSES = {"citm-utils-web", "caddy"}


def _is_managed(proc_info: Dict[str, Any]) -> bool:
    return proc_info.get("name") not in _EXCLUDED_PROCESSES


class _UnixSocketTransport(xmlrpc.client.Transport):
    def __init__(self, socket_path: str):
        super().__init__()
        self.socket_path = socket_path

    def make_connection(self, host):
        conn = http.client.HTTPConnection("localhost")
        conn.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.sock.connect(self.socket_path)
        return conn


def _rpc():
    socket_path = os.environ.get("SUPERVISOR_SOCKET", "/var/run/supervisor.sock")
    transport = _UnixSocketTransport(socket_path)
    return xmlrpc.client.ServerProxy("http://localhost/RPC2", transport=transport)


def _start_with_retry(
    server, name: str, *, retries: int = 5, delay_s: float = 0.3
) -> None:
    """Start a Supervisor program with small retries for transient STOPPING states."""
    for attempt in range(retries):
        try:
            server.supervisor.startProcess(name, False)
            return
        except xmlrpc.client.Fault as fe:
            msg = fe.faultString or ""
            if "ALREADY_STARTED" in msg:
                return
            if "STILL_STOPPING" in msg or "STOPPING" in msg:
                if attempt < retries - 1:
                    time.sleep(delay_s)
                    continue
                raise
            raise
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay_s)
                continue
            raise


def _get_process(server, name: str) -> Dict[str, Any]:
    return server.supervisor.getProcessInfo(name)


def _stop_if_running(server, name: str) -> None:
    info = _get_process(server, name)
    if info.get("statename") == "RUNNING":
        # wait=True so a subsequent start is not racing STOPPING
        server.supervisor.stopProcess(name, True)


class SupervisorError(Exception):
    def __init__(
        self, message: str, *, status_code: int = 502, details: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or ""


def list_services() -> List[Dict[str, str]]:
    try:
        server = _rpc()
        procs = server.supervisor.getAllProcessInfo()
    except Exception as e:
        raise SupervisorError(
            "Failed to read supervisor status via RPC",
            status_code=502,
            details=str(e),
        )

    services: List[Dict[str, str]] = []
    for p in procs:
        if not _is_managed(p):
            continue
        services.append(
            {
                "name": (p.get("name") or ""),
                "state": (p.get("statename") or ""),
                "description": (p.get("description") or "").strip(),
            }
        )
    return services


def service_action(name: str, action: str) -> None:
    if action not in {"start", "stop", "restart"}:
        raise SupervisorError("Unsupported action", status_code=400)
    if name in _EXCLUDED_PROCESSES:
        raise SupervisorError("Unsupported service", status_code=400)

    try:
        server = _rpc()
        if action == "start":
            _start_with_retry(server, name)

        elif action == "stop":
            # Only stop if currently running; EXITED/STOPPED/FATAL are already not running.
            _stop_if_running(server, name)

        elif action == "restart":
            info = _get_process(server, name)
            state = info.get("statename")

            # If it's running, stop first then start.
            if state == "RUNNING":
                _stop_if_running(server, name)
                _start_with_retry(server, name)

            # If it's not running (EXITED/STOPPED/FATAL/UNKNOWN), just start it.
            elif state in {"EXITED", "STOPPED", "FATAL", "UNKNOWN"}:
                _start_with_retry(server, name)

            # Transient states: try to start with retry; if still not possible, bubble error.
            elif state in {"STARTING", "STOPPING", "BACKOFF"}:
                _start_with_retry(server, name)

            else:
                # Default: attempt a start, letting Supervisor raise if invalid.
                _start_with_retry(server, name)

    except Exception as e:
        raise SupervisorError(
            "Supervisor action failed via RPC",
            status_code=502,
            details=str(e),
        )


def restart_all() -> None:
    try:
        server = _rpc()
        procs = server.supervisor.getAllProcessInfo()
        managed = [p for p in procs if _is_managed(p)]

        for p in managed:
            name = p.get("name")
            if not name:
                continue
            if p.get("statename") == "RUNNING":
                server.supervisor.stopProcess(name, True)

        for p in managed:
            name = p.get("name")
            if not name:
                continue
            _start_with_retry(server, name)

    except Exception as e:
        raise SupervisorError(
            "Supervisor action failed via RPC",
            status_code=502,
            details=str(e),
        )
