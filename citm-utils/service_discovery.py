from docker import DockerClient


def get_citm_dns_entries(docker_client: DockerClient):
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


def watch_container_lifecycle(
    docker_client: DockerClient, callback: function, exit_callback: function
):
    api = docker_client.api

    try:
        for event in api.events(decode=True):
            if event["Type"] != "container":
                continue

            if event["Action"] not in set(["start", "stop"]):
                continue

            callback()
    except KeyboardInterrupt:
        exit_callback()
    finally:
        api.close()
