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


def get_citm_dns_entries():
    containers = docker_client.containers.list(
        all=False, filters={"label": ["citm_network", "citm_dns_names"]}
    )

    def to_dns_entries(container):
        network_name = container.labels.get("citm_network")
        if not network_name:
            return {}

        network = container.attrs["NetworkSettings"]["Networks"].get(network_name)
        if not network:
            return {}

        ip = network["IPAddress"]

        dns_names = [
            name.strip()
            for name in container.labels.get("citm_dns_names", "").split(",")
            if len(name.strip()) > 0
        ]

        return {name: ip for name in dns_names}

    return {
        name: ip
        for container in containers
        for name, ip in to_dns_entries(container).items()
    }


def citm_dns_entries_to_dnsmasq_config(citm_dns_entries: dict[str, str]):
    lines = []
    for hostname, ip in citm_dns_entries.items():
        lines.append(f"address=/{hostname}/{ip}")
    return "\n".join(lines)


@debounce(1)
def reload_services():
    global previous_dnsmasq_config

    entries = get_citm_dns_entries()
    config = citm_dns_entries_to_dnsmasq_config(entries)
    with open("/etc/dnsmasq.d/citm.conf", "w", encoding="utf-8") as f:
        f.write(config)
    subprocess.call(["supervisorctl", "signal", "SIGHUP", "dnsmasq"])

    # Caddy keeps he connection open and doesn't do a hostname resolution until 
    # it's restarted
    if previous_dnsmasq_config != config:
        print("Restarting Caddy...", flush=True)
        subprocess.call(["supervisorctl", "restart", "caddy"])
        previous_dnsmasq_config = config


def watch_container_lifecycle(callback: function):
    api = docker_client.api

    try:
        for event in api.events(decode=True):
            if event["Type"] != "container":
                continue

            if event["Action"] not in set(["start", "stop"]):
                continue

            callback()
    except KeyboardInterrupt:
        print("\nExiting...", flush=True)
    finally:
        api.close()


if __name__ == "__main__":
    try:
        reload_services()
        print("dnsmasq updater is listening for container lifecycle changes.", flush=True)
        watch_container_lifecycle(reload_services)
    finally:
        docker_client.close()
