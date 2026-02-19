from service_discovery import get_citm_dns_entries, watch_container_lifecycle
import docker
import threading
import functools
import subprocess
import time
import queue
from typing import Any, Callable

docker_client = docker.from_env()
previous_dnsmasq_config = ""


class EventEmitter:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., None]]] = {}
        self._queue: (
            "queue.SimpleQueue[tuple[str, tuple[Any, ...], dict[str, Any]]]"
        ) = queue.SimpleQueue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        # Unblock the queue consumer
        self.emit("__stop__")
        self._thread.join(timeout=2)

    def on(self, event: str, handler: Callable[..., None]) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._queue.put((event, args, kwargs))

    def _run(self) -> None:
        while not self._stop.is_set():
            event, args, kwargs = self._queue.get()
            if event == "__stop__":
                continue
            for handler in self._handlers.get(event, []):
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    # Keep the event loop alive even if a handler fails
                    print(f"Event handler error for '{event}': {e}", flush=True)


def debounce(wait_seconds):
    def decorator(fn):
        timer = None
        lock = threading.Lock()

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            nonlocal timer

            def call():
                fn(*args, **kwargs)

            with lock:
                if timer is not None:
                    timer.cancel()
                timer = threading.Timer(wait_seconds, call)
                timer.daemon = True
                timer.start()

        return wrapped

    return decorator


def citm_dns_entries_to_dnsmasq_config(citm_dns_entries: dict[str, str]):
    lines = []
    for hostname, ip in citm_dns_entries.items():
        lines.append(f"address=/{hostname}/{ip}")
    return "\n".join(lines)


@debounce(1)
def reload_services():
    global previous_dnsmasq_config

    entries = get_citm_dns_entries(docker_client)
    config = citm_dns_entries_to_dnsmasq_config(entries)
    with open("/etc/dnsmasq.d/citm.conf", "w", encoding="utf-8") as f:
        f.write(config)

    if previous_dnsmasq_config != config:
        subprocess.call(["supervisorctl", "signal", "SIGHUP", "dnsmasq"])

        # Caddy keeps the connection open and doesn't do a hostname resolution until
        # it's restarted
        print("Restarting Caddy...", flush=True)
        subprocess.call(["supervisorctl", "restart", "caddy"])

        previous_dnsmasq_config = config


if __name__ == "__main__":
    stop_event = threading.Event()
    events = EventEmitter()

    events.on("change", lambda: reload_services())

    # FIXME: this a workaround for a hard to reproduce case where the IP
    # address ends up being empty or wrong. There should be a better way to
    # address this
    def timer_loop():
        while not stop_event.is_set():
            events.emit("change")
            time.sleep(1)

    timer_thread = threading.Thread(target=timer_loop, daemon=True)

    try:
        events.start()
        timer_thread.start()

        # Initial run
        events.emit("change")

        print(
            "dnsmasq updater is listening for container lifecycle changes and timer ticks.",
            flush=True,
        )

        def on_exit(_):
            stop_event.set()
            print("\nExiting...", flush=True)

        watch_container_lifecycle(
            docker_client, lambda *_: events.emit("change"), on_exit
        )
    finally:
        stop_event.set()
        try:
            events.stop()
        finally:
            docker_client.close()
