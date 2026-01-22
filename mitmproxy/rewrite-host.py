class RewriteHost:
    def request(self, flow):
        headers = {k.lower(): v for k, v in flow.request.headers.items()}
        emoji = headers.get("x-mitm-emoji", "")
        to = headers.get("x-mitm-to", "")

        if to == "":
            return

        to_host, _, to_port = to.partition(":")

        if emoji != "":
            flow.marked = emoji

        pretty_host = flow.request.pretty_host
        flow.comment = f"Rewriting host {pretty_host} -> {to}"

        flow.server_conn.sni = pretty_host

        host_header = f"{pretty_host}:{flow.request.port}"
        flow.request.host = to_host
        flow.request.port = int(to_port)
        flow.request.host_header = host_header


addons = [RewriteHost()]
