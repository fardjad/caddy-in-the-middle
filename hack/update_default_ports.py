#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Port:
    env: str
    default: int
    scope: str
    service: str
    purpose: str
    protocol: str = "tcp"


PORTS = (
    Port("CADDY_HTTP_PORT", 80, "Exposed", "caddy", "HTTP ingress"),
    Port("CADDY_HTTPS_PORT", 443, "Exposed", "caddy", "HTTPS ingress"),
    Port(
        "CADDY_ADMIN_PORT",
        63858,
        "Exposed",
        "caddy",
        "Admin and utility virtual hosts",
    ),
    Port(
        "MITMPROXY_HTTP_PROXY_PORT",
        19080,
        "Exposed",
        "mitmproxy",
        "HTTP proxy listener",
    ),
    Port(
        "MITMPROXY_SOCKS_PROXY_PORT",
        19081,
        "Exposed",
        "mitmproxy",
        "SOCKS5 proxy listener",
    ),
    Port(
        "MITMPROXY_WEB_PORT",
        19082,
        "Internal",
        "mitmweb",
        "Web UI backend",
    ),
    Port(
        "CITM_UTILS_WEB_PORT",
        19000,
        "Internal",
        "citm-utils-web",
        "Utility API listener",
    ),
    Port(
        "SUPERVISOR_WEBUI_PORT",
        19001,
        "Internal",
        "supervisor-webui",
        "Supervisor UI listener",
    ),
    Port(
        "CITM_DNS_LISTEN_PORT",
        53,
        "Internal",
        "citm-utils-dns-forwarder",
        "DNS listener",
        protocol="tcp/udp",
    ),
)

PORT_BY_ENV = {port.env: port for port in PORTS}


def wrap_bullet(text: str) -> str:
    return textwrap.fill(text, width=80, subsequent_indent="  ")


def render_dockerfile_env_block() -> str:
    env_names = [port.env for port in PORTS]
    first_env = env_names[0]
    lines = [f"ENV {first_env}={PORT_BY_ENV[first_env].default} \\"]
    for index, env_name in enumerate(env_names[1:], start=1):
        port = PORT_BY_ENV[env_name]
        suffix = " \\" if index < len(env_names) - 1 else ""
        lines.append(f"    {env_name}={port.default}{suffix}")
    return "\n".join(lines)


def render_shell_defaults_block() -> str:
    return "\n".join(
        [
            f'HTTP_PROXY_PORT="${{MITMPROXY_HTTP_PROXY_PORT:-{PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default}}}"',
            f'SOCKS_PROXY_PORT="${{MITMPROXY_SOCKS_PROXY_PORT:-{PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default}}}"',
            f'WEB_PORT="${{MITMPROXY_WEB_PORT:-{PORT_BY_ENV["MITMPROXY_WEB_PORT"].default}}}"',
            f'DNS_LISTEN_PORT="${{CITM_DNS_LISTEN_PORT:-{PORT_BY_ENV["CITM_DNS_LISTEN_PORT"].default}}}"',
        ]
    )


def render_citm_utils_python_constants() -> str:
    return "\n".join(
        [
            f'DEFAULT_CADDY_ADMIN_PORT = {PORT_BY_ENV["CADDY_ADMIN_PORT"].default}',
            f'DEFAULT_CITM_UTILS_WEB_PORT = {PORT_BY_ENV["CITM_UTILS_WEB_PORT"].default}',
            f'DEFAULT_MITMPROXY_WEB_PORT = {PORT_BY_ENV["MITMPROXY_WEB_PORT"].default}',
        ]
    )


def render_supervisor_webui_python_constants() -> str:
    return (
        f"DEFAULT_SUPERVISOR_WEBUI_PORT = "
        f'{PORT_BY_ENV["SUPERVISOR_WEBUI_PORT"].default}'
    )


def render_testcontainers_python_constants() -> str:
    names = [
        "CADDY_HTTP_PORT",
        "CADDY_HTTPS_PORT",
        "MITMPROXY_HTTP_PROXY_PORT",
        "MITMPROXY_SOCKS_PROXY_PORT",
        "CADDY_ADMIN_PORT",
    ]
    mapping = {
        "CADDY_HTTP_PORT": "HTTP_PORT",
        "CADDY_HTTPS_PORT": "HTTPS_PORT",
        "MITMPROXY_HTTP_PROXY_PORT": "HTTP_PROXY_PORT",
        "MITMPROXY_SOCKS_PROXY_PORT": "SOCKS_PROXY_PORT",
        "CADDY_ADMIN_PORT": "ADMIN_PORT",
    }
    return "\n".join(
        [f"    {mapping[name]} = {PORT_BY_ENV[name].default}" for name in names]
    )


def render_dotnet_constants() -> str:
    return "\n".join(
        [
            "    /// <summary>",
            f'    /// The exposed HTTP port ({PORT_BY_ENV["CADDY_HTTP_PORT"].default}).',
            "    /// </summary>",
            f'    public const ushort HttpPort = {PORT_BY_ENV["CADDY_HTTP_PORT"].default};',
            "",
            "    /// <summary>",
            f'    /// The exposed HTTPS port ({PORT_BY_ENV["CADDY_HTTPS_PORT"].default}).',
            "    /// </summary>",
            f'    public const ushort HttpsPort = {PORT_BY_ENV["CADDY_HTTPS_PORT"].default};',
            "",
            "    /// <summary>",
            "    /// The user-mapped port for the HTTP proxy.",
            "    /// </summary>",
            f'    public const ushort HttpProxyPort = {PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default};',
            "",
            "    /// <summary>",
            "    /// The user-mapped port for the SOCKS5 proxy.",
            "    /// </summary>",
            f'    public const ushort SocksProxyPort = {PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default};',
            "",
            "    /// <summary>",
            "    /// The user-mapped port for the Admin API.",
            "    /// </summary>",
            f'    public const ushort AdminPort = {PORT_BY_ENV["CADDY_ADMIN_PORT"].default};',
        ]
    )


def render_testcontainers_port_section() -> str:
    rows = [
        "",
        f'- `{PORT_BY_ENV["CADDY_HTTP_PORT"].default}`: HTTP traffic (incoming to Caddy)',
        f'- `{PORT_BY_ENV["CADDY_HTTPS_PORT"].default}`: HTTPS traffic (incoming to Caddy)',
        f'- `{PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default}`: HTTP proxy',
        f'- `{PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default}`: SOCKS5 proxy',
        (
            f'- `{PORT_BY_ENV["CADDY_ADMIN_PORT"].default}`: '
            "Admin and utility virtual hosts through Caddy"
        ),
        "",
        "The container also supports runtime port overrides through environment",
        "variables. The defaults are:",
        "",
    ]
    rows.extend(f"- `{port.env}={port.default}`" for port in PORTS)
    rows.append("")
    rows.append("")
    return "\n".join(rows)


def render_testcontainers_helper_methods() -> str:
    return "\n".join(
        [
            "",
            "- **`GetCaddyHttpBaseUrl(subdomains...)`**: Returns",
            "  `http://[subdomains.]<host>:<mapped_port_80>`.",
            "- **`GetCaddyHttpsBaseUrl(subdomains...)`**: Returns",
            "  `https://[subdomains.]<host>:<mapped_port_443>`.",
            (
                "- **`GetHttpProxyAddress()`**: Returns "
                f'`http://<host>:<mapped_port_{PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default}>`.'
            ),
            (
                "- **`GetSocksProxyAddress()`**: Returns "
                f'`socks5://<host>:<mapped_port_{PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default}>`.'
            ),
            "- **`GetAdminBaseUrl(subdomains...)`**: Returns",
            (
                "  `https://[subdomains.]<host>:"
                f'<mapped_port_{PORT_BY_ENV["CADDY_ADMIN_PORT"].default}>`.'
            ),
            "",
            "",
        ]
    )


def render_default_ports_doc() -> str:
    lines = [
        "# Default Ports",
        "",
        "## What it is",
        "",
        textwrap.fill(
            "This reference defines the default runtime ports for CITM. The source "
            "of truth is `hack/update_default_ports.py`.",
            width=80,
        ),
        "",
        "## Defaults",
        "",
    ]
    for port in PORTS:
        lines.append(
            wrap_bullet(
                f"- `{port.env}={port.default}`: {port.scope} port for "
                f"`{port.service}`. {port.purpose}."
            )
        )
    lines.extend(
        [
            "",
            "## Overrides",
            "",
            textwrap.fill(
                "Override any of these defaults by setting environment variables on "
                "the CITM container.",
                width=80,
            ),
            "",
            "```yaml",
            "services:",
            "  citm:",
            "    image: fardjad/citm:latest",
            "    environment:",
            "      - CADDY_ADMIN_PORT=29058",
            "      - MITMPROXY_HTTP_PROXY_PORT=29080",
            "      - MITMPROXY_SOCKS_PROXY_PORT=29081",
            "      - MITMPROXY_WEB_PORT=29082",
            "      - CITM_UTILS_WEB_PORT=29000",
            "      - SUPERVISOR_WEBUI_PORT=29001",
            "      - CITM_DNS_LISTEN_PORT=5300",
            "```",
            "",
            "Container-side port overrides do not change host-side `ports:` mappings in",
            "Compose. Update host mappings separately when you need fixed host ports.",
            "",
            "If `CITM_DNS_LISTEN_PORT=53`, CITM rewrites `/etc/resolv.conf` to use",
            "`127.0.0.1`. If `CITM_DNS_LISTEN_PORT` is not `53`, CITM leaves",
            "`/etc/resolv.conf` unchanged and logs a startup warning.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_devcontainer_ports_block() -> str:
    lines = [
        f'- \'0.0.0.0:${{CADDY_ADMIN_PORT:-{PORT_BY_ENV["CADDY_ADMIN_PORT"].default}}}:{PORT_BY_ENV["CADDY_ADMIN_PORT"].default}\'',
        f'- \'0.0.0.0:${{CADDY_HTTP_PORT:-{PORT_BY_ENV["CADDY_HTTP_PORT"].default}}}:{PORT_BY_ENV["CADDY_HTTP_PORT"].default}\'',
        f'- \'0.0.0.0:${{CADDY_HTTPS_PORT:-{PORT_BY_ENV["CADDY_HTTPS_PORT"].default}}}:{PORT_BY_ENV["CADDY_HTTPS_PORT"].default}/udp\'',
        f'- \'0.0.0.0:${{CADDY_HTTPS_PORT:-{PORT_BY_ENV["CADDY_HTTPS_PORT"].default}}}:{PORT_BY_ENV["CADDY_HTTPS_PORT"].default}\'',
        f'- \'0.0.0.0:${{CITM_UTILS_WEB_PORT:-{PORT_BY_ENV["CITM_UTILS_WEB_PORT"].default}}}:{PORT_BY_ENV["CITM_UTILS_WEB_PORT"].default}\'',
        f'- \'0.0.0.0:${{MITMPROXY_HTTP_PROXY_PORT:-{PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default}}}:{PORT_BY_ENV["MITMPROXY_HTTP_PROXY_PORT"].default}\'',
        f'- \'0.0.0.0:${{MITMPROXY_SOCKS_PROXY_PORT:-{PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default}}}:{PORT_BY_ENV["MITMPROXY_SOCKS_PROXY_PORT"].default}\'',
        f'- \'0.0.0.0:${{MITMPROXY_WEB_PORT:-{PORT_BY_ENV["MITMPROXY_WEB_PORT"].default}}}:{PORT_BY_ENV["MITMPROXY_WEB_PORT"].default}\'',
        f'- \'0.0.0.0:${{SUPERVISOR_WEBUI_PORT:-{PORT_BY_ENV["SUPERVISOR_WEBUI_PORT"].default}}}:{PORT_BY_ENV["SUPERVISOR_WEBUI_PORT"].default}\'',
    ]
    return "\n".join(f"      {line}" for line in lines)


def replace_block(
    text: str, begin_marker: str, end_marker: str, replacement: str
) -> str:
    start = text.index(begin_marker) + len(begin_marker)
    end = text.index(end_marker)
    replacement_text = replacement if replacement.endswith("\n") else replacement + "\n"
    return text[:start] + "\n" + replacement_text + text[end:]


def update_block(
    path: str,
    begin_marker: str,
    end_marker: str,
    replacement: str,
) -> tuple[str, str]:
    file_path = ROOT / path
    original = file_path.read_text(encoding="utf-8")
    updated = replace_block(original, begin_marker, end_marker, replacement)
    return path, updated


def update_text_block(
    text: str,
    begin_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    return replace_block(text, begin_marker, end_marker, replacement)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    updates: list[tuple[str, str]] = []
    updates.append(
        update_block(
            "Dockerfile",
            "# BEGIN GENERATED DEFAULT PORT ENV",
            "# END GENERATED DEFAULT PORT ENV",
            render_dockerfile_env_block(),
        )
    )
    updates.append(
        update_block(
            ".devcontainer/compose.yml",
            "      # BEGIN GENERATED EXPOSED PORTS",
            "      # END GENERATED EXPOSED PORTS",
            render_devcontainer_ports_block(),
        )
    )
    updates.append(
        update_block(
            "mitmproxy/start-mitmproxy.sh",
            "# BEGIN GENERATED DEFAULT PORTS",
            "# END GENERATED DEFAULT PORTS",
            render_shell_defaults_block(),
        )
    )
    updates.append(
        update_block(
            "citm-utils/app.py",
            "# BEGIN GENERATED DEFAULT PORTS",
            "# END GENERATED DEFAULT PORTS",
            render_citm_utils_python_constants(),
        )
    )
    updates.append(
        update_block(
            "supervisor/webui/supervisor_webui/app.py",
            "# BEGIN GENERATED DEFAULT PORTS",
            "# END GENERATED DEFAULT PORTS",
            render_supervisor_webui_python_constants(),
        )
    )
    updates.append(
        update_block(
            "testcontainers/python/caddy_in_the_middle/container.py",
            "    # BEGIN GENERATED DEFAULT PORTS",
            "    # END GENERATED DEFAULT PORTS",
            render_testcontainers_python_constants(),
        )
    )
    updates.append(
        update_block(
            "testcontainers/dotnet/CaddyInTheMiddle.Testcontainers/CaddyInTheMiddleBuilder.cs",
            "    // BEGIN GENERATED DEFAULT PORTS",
            "    // END GENERATED DEFAULT PORTS",
            render_dotnet_constants(),
        )
    )
    specification_path = "testcontainers/specification.md"
    specification_text = (ROOT / specification_path).read_text(encoding="utf-8")
    specification_text = update_text_block(
        specification_text,
        "<!-- BEGIN GENERATED DEFAULT PORTS -->",
        "<!-- END GENERATED DEFAULT PORTS -->",
        render_testcontainers_port_section(),
    )
    specification_text = update_text_block(
        specification_text,
        "<!-- BEGIN GENERATED DEFAULT PORT HELPERS -->",
        "<!-- END GENERATED DEFAULT PORT HELPERS -->",
        render_testcontainers_helper_methods(),
    )
    updates.append((specification_path, specification_text))

    default_ports_doc = render_default_ports_doc()
    default_ports_path = ROOT / "docs/src/reference/default-ports.md"
    existing_default_ports_doc = (
        default_ports_path.read_text(encoding="utf-8")
        if default_ports_path.exists()
        else None
    )

    stale_files: list[str] = []
    for path, updated in updates:
        file_path = ROOT / path
        original = file_path.read_text(encoding="utf-8")
        if original != updated:
            if args.check:
                stale_files.append(path)
            else:
                file_path.write_text(updated, encoding="utf-8")

    if existing_default_ports_doc != default_ports_doc:
        if args.check:
            stale_files.append("docs/src/reference/default-ports.md")
        else:
            default_ports_path.write_text(default_ports_doc, encoding="utf-8")

    if stale_files:
        print("Default port files are out of date:", file=sys.stderr)
        for path in stale_files:
            print(f"  - {path}", file=sys.stderr)
        print("Run `python3 hack/update_default_ports.py`.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
