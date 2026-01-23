from service_discovery import get_citm_dns_entries, watch_container_lifecycle
import docker
import threading
import functools
import subprocess

docker_client = docker.from_env()
previous_dnsmasq_config = ""


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
    subprocess.call(["supervisorctl", "signal", "SIGHUP", "dnsmasq"])

    # Caddy keeps the connection open and doesn't do a hostname resolution until
    # it's restarted
    if previous_dnsmasq_config != config:
        print("Restarting Caddy...", flush=True)
        subprocess.call(["supervisorctl", "restart", "caddy"])
        previous_dnsmasq_config = config


if __name__ == "__main__":
    try:
        reload_services()
        print(
            "dnsmasq updater is listening for container lifecycle changes.", flush=True
        )
        watch_container_lifecycle(
            docker_client, reload_services, lambda _: print("\nExiting...", flush=True)
        )
    finally:
        docker_client.close()
