"""
mitmproxy addon for serving mock HTTP responses from file-based specifications.

Mock files are stored in a mocks directory as .mako templates with the format:
    <METHOD> <URL>

    <STATUS_CODE>
    Header-Name: value

    <%
        # Optional Mako preprocessing block
        computed_value = some_function()
    %>
    ---
    <RESPONSE_BODY>

The separator '---' marks the start of the response body.
Everything before '---' (after headers) can contain Mako preprocessing blocks.
URLs starting with '~' are treated as wildcard patterns (shell-style glob matching).
Bodies starting with '@@<url>' fetch and proxy content from the specified URL.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from fnmatch import fnmatch
import urllib.request
import os

from mitmproxy import http, ctx
from mako.template import Template


@dataclass
class MockSpec:
    """Specification for a mocked HTTP response."""

    status: int
    headers: Dict[str, str]
    remainder: str  # The raw remainder to be processed with Mako later


class MockKey(NamedTuple):
    """Unique identifier for an exact-match mock."""

    method: str
    url: str


class WildcardMock(NamedTuple):
    """Specification for a wildcard pattern mock."""

    method: str
    pattern: str
    spec: MockSpec


class MockFileParser:
    """Parses mock specification files into structured data."""

    # Headers that should not be copied from proxied responses
    EXCLUDED_HEADERS = frozenset(["transfer-encoding", "content-length", "connection"])

    @staticmethod
    def parse(path: Path) -> Optional[Tuple[str, str, MockSpec]]:
        """
        Parse a mock file into (method, url, spec).

        Returns None if the file cannot be parsed.
        Raises ValueError with descriptive message on parse errors.
        """
        try:
            content = path.read_text(encoding="utf-8")
            return MockFileParser._parse_content(content, path.name)
        except Exception as e:
            ctx.log.warn(f"Failed to parse mock file {path.name}: {e}")
            return None

    @staticmethod
    def _parse_content(content: str, filename: str) -> Tuple[str, str, MockSpec]:
        """Parse the content of a mock file."""
        sections = content.split("\n\n", 2)

        if len(sections) < 2:
            raise ValueError(
                "Mock file must have at least request line and status sections"
            )

        method, url = MockFileParser._parse_request_line(sections[0])
        status, headers = MockFileParser._parse_status_and_headers(
            sections[1], filename
        )

        # Store the raw remainder - will be processed with Mako later
        remainder = sections[2] if len(sections) == 3 else ""

        return (
            method,
            url,
            MockSpec(status=status, headers=headers, remainder=remainder),
        )

    @staticmethod
    def _extract_body(remainder: str) -> str:
        """
        Extract the body from the remainder section.

        Body starts after the '---' separator. Everything before '---'
        (which may include Mako preprocessing blocks) is included in the body
        template so it can be executed during rendering.

        The line containing '---' is removed, and we strip one leading newline
        from the body to avoid adding unwanted whitespace.
        """
        if "---" not in remainder:
            # No separator found - treat entire remainder as body for backwards compatibility
            return remainder

        # Split on first occurrence of '---'
        before_separator, after_separator = remainder.split("---", 1)

        # Strip the newline that's on the line with '---' from after_separator
        # This prevents adding an extra blank line at the start of the body
        if after_separator.startswith("\n"):
            after_separator = after_separator[1:]

        # Include preprocessing block + body content for Mako rendering
        # The preprocessing (before ---) will execute when template renders
        return before_separator + after_separator

    @staticmethod
    def _parse_request_line(section: str) -> Tuple[str, str]:
        """Parse the first line: 'METHOD URL'."""
        first_line = section.strip().split("\n")[0]

        if not first_line:
            raise ValueError("Missing request line (METHOD URL)")

        parts = first_line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"Request line must be 'METHOD URL', got: {first_line}")

        return parts[0].upper(), parts[1]

    @staticmethod
    def _parse_status_and_headers(
        section: str, filename: str
    ) -> Tuple[int, Dict[str, str]]:
        """Parse status code and headers from the second section."""
        lines = [line.strip() for line in section.splitlines() if line.strip()]

        if not lines:
            raise ValueError("Missing status code")

        # First line is status code
        try:
            status = int(lines[0])
        except ValueError:
            raise ValueError(f"Invalid status code: {lines[0]}")

        # Remaining lines are headers
        headers = {}
        for line in lines[1:]:
            if ":" not in line:
                ctx.log.warn(f"Skipping malformed header in {filename}: '{line}'")
                continue

            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        return status, headers


class ExternalContentFetcher:
    """Handles fetching content from external URLs."""

    @staticmethod
    def should_fetch_external(rendered_content: str) -> bool:
        """Check if rendered content starts with '@@' indicating external fetch."""
        return rendered_content.lstrip().startswith("@@")

    @staticmethod
    def fetch(
        rendered_content: str, mock_headers: Dict[str, str]
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Fetch external content specified by '@@<url>' in rendered content.

        Returns: (status_code, merged_headers, response_body)
        """
        target_url = rendered_content.lstrip().split("\n")[0][2:].strip()

        ctx.log.info(f"Fetching external content from: {target_url}")

        try:
            with urllib.request.urlopen(target_url) as response:
                status = response.getcode()
                remote_headers = ExternalContentFetcher._clean_headers(
                    dict(response.getheaders())
                )
                body_bytes = response.read()

                # Mock headers override remote headers
                merged_headers = {**remote_headers, **mock_headers}

                return status, merged_headers, body_bytes

        except Exception as e:
            ctx.log.error(f"Failed to fetch from {target_url}: {e}")
            # Return empty response on error, preserving mock status/headers
            return 200, mock_headers, b""

    @staticmethod
    def _clean_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Remove headers that shouldn't be forwarded."""
        return {
            k: v
            for k, v in headers.items()
            if k.lower() not in MockFileParser.EXCLUDED_HEADERS
        }


class TemplateRenderer:
    """Handles Mako template rendering and body extraction."""

    @staticmethod
    def render_and_extract_body(remainder: str, flow: http.HTTPFlow) -> str:
        """
        Render the remainder section with Mako and extract the body.

        The body is everything after the first '---\n' separator in the rendered output.
        If no separator is found, the entire rendered content is returned as the body.
        """
        try:
            rendered = Template(remainder).render(flow=flow)
        except Exception as e:
            ctx.log.warn(f"Mako render error for {flow.request.url}: {e}")
            # Fallback to unrendered template on error
            rendered = remainder

        # Split on first occurrence of '---\n'
        separator = "---\n"
        if separator in rendered:
            _, body = rendered.split(separator, 1)
            return body
        else:
            # No separator found - return entire rendered content
            return rendered


class MockStore:
    """Storage and retrieval of mock specifications."""

    def __init__(self):
        self.exact_matches: Dict[MockKey, MockSpec] = {}
        self.wildcard_matches: List[WildcardMock] = []

    def clear(self) -> None:
        """Clear all stored mocks."""
        self.exact_matches.clear()
        self.wildcard_matches.clear()

    def add_exact(self, method: str, url: str, spec: MockSpec) -> None:
        """Add an exact-match mock."""
        key = MockKey(method, url)
        self.exact_matches[key] = spec
        ctx.log.info(f"Loaded exact mock: {method} {url}")

    def add_wildcard(self, method: str, pattern: str, spec: MockSpec) -> None:
        """Add a wildcard pattern mock."""
        self.wildcard_matches.append(WildcardMock(method, pattern, spec))
        ctx.log.info(f"Loaded wildcard mock: {method} ~{pattern}")

    def find_mock(self, method: str, url: str) -> Optional[MockSpec]:
        """
        Find a mock matching the given method and URL.

        Checks exact matches first, then wildcard patterns.
        """
        # Try exact match first
        key = MockKey(method, url)
        if key in self.exact_matches:
            ctx.log.info(f"Exact match found for: {method} {url}")
            return self.exact_matches[key]

        # Try wildcard patterns
        for wildcard in self.wildcard_matches:
            if wildcard.method == method and fnmatch(url, wildcard.pattern):
                ctx.log.info(
                    f"Wildcard match found for: {method} {url} (pattern: {wildcard.pattern})"
                )
                return wildcard.spec

        return None


class MockResponder:
    """
    mitmproxy addon that serves responses from mock files.

    Mock files should be placed in directories specified by the MOCK_PATHS
    environment variable (comma-separated list of glob patterns).
    Example: MOCK_PATHS="/mocks/*.mako,/app/tests/mocks/**/*.mako"

    The addon is disabled if MOCK_PATHS is not set.
    The addon rescans all paths on every request to allow hot-reloading.
    """

    def __init__(self) -> None:
        self.mock_patterns = self._get_mock_patterns()
        self.enabled = len(self.mock_patterns) > 0
        self.store = MockStore()

        if not self.enabled:
            ctx.log.info(
                "MockResponder disabled: MOCK_PATHS environment variable not set"
            )

    @staticmethod
    def _get_mock_patterns() -> List[str]:
        """
        Get mock file patterns from MOCK_PATHS environment variable.

        Returns a list of glob patterns to search for mock files.
        Returns empty list if MOCK_PATHS is not set (disabling the addon).
        """
        mock_paths_env = os.environ.get("MOCK_PATHS")

        if not mock_paths_env:
            return []

        patterns = [p.strip() for p in mock_paths_env.split(",") if p.strip()]
        ctx.log.info(f"Mock patterns configured: {patterns}")
        return patterns

    def load(self, loader) -> None:
        """Called when the addon is loaded by mitmproxy."""
        if self.enabled:
            self._load_mocks()

    def request(self, flow: http.HTTPFlow) -> None:
        """
        Intercept requests and serve mocked responses if available.

        Rescans the mocks on each request to enable hot-reloading.
        Does nothing if the addon is disabled.
        """
        if not self.enabled:
            return

        self._load_mocks()

        method = flow.request.method.upper()
        url = flow.request.url

        ctx.log.info(f"Checking for mock: {method} {url}")

        spec = self.store.find_mock(method, url)
        if not spec:
            return  # No mock found, let request proceed normally

        # Build response from mock specification
        status, headers, body = self._build_response(spec, flow)

        ctx.log.info(f"Serving mock response: {method} {url} -> {status}")
        flow.response = http.Response.make(status, body, headers)

    def _load_mocks(self) -> None:
        """Scan all configured patterns and load all mock specifications."""
        self.store.clear()

        all_mock_files = []

        for pattern in self.mock_patterns:
            mock_files = self._find_files_by_pattern(pattern)
            all_mock_files.extend(mock_files)

        if not all_mock_files:
            ctx.log.info(f"No mock files found matching patterns: {self.mock_patterns}")
            return

        ctx.log.info(f"Found {len(all_mock_files)} mock file(s)")

        for mock_file in sorted(all_mock_files):
            self._load_mock_file(mock_file)

    @staticmethod
    def _find_files_by_pattern(pattern: str) -> List[Path]:
        """
        Find all files matching a glob pattern.

        Supports both simple patterns (*.mako) and recursive patterns (**/*.mako).
        """
        # Handle absolute vs relative patterns
        if pattern.startswith("/"):
            # Absolute path pattern
            base_path = Path("/")
            relative_pattern = pattern[1:]  # Remove leading slash for glob
        else:
            # Relative path pattern
            base_path = Path.cwd()
            relative_pattern = pattern

        try:
            # Use rglob for recursive patterns, glob otherwise
            if "**" in relative_pattern:
                # For recursive patterns, we need to separate the base path from the pattern
                parts = relative_pattern.split("**", 1)
                base_dir = base_path / parts[0].strip("/")
                sub_pattern = parts[1].strip("/")

                if base_dir.exists():
                    matches = list(base_dir.rglob(sub_pattern))
                else:
                    matches = []
            else:
                # For non-recursive patterns
                parent = base_path / Path(relative_pattern).parent
                if parent.exists():
                    matches = list(parent.glob(Path(relative_pattern).name))
                else:
                    matches = []

            ctx.log.info(f"Pattern '{pattern}' matched {len(matches)} file(s)")
            return [m for m in matches if m.is_file()]

        except Exception as e:
            ctx.log.warn(f"Error processing pattern '{pattern}': {e}")
            return []

    def _load_mock_file(self, path: Path) -> None:
        """Load a single mock file and add it to the store."""
        parsed = MockFileParser.parse(path)

        if parsed is None:
            return

        method, url, spec = parsed

        if url.startswith("~"):
            pattern = url[1:].strip()
            self.store.add_wildcard(method, pattern, spec)
        else:
            self.store.add_exact(method, url, spec)

    def _build_response(
        self, spec: MockSpec, flow: http.HTTPFlow
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Build an HTTP response from a mock specification.

        Process:
        1. Render the remainder with Mako (executes preprocessing blocks)
        2. Split rendered output on '---\n' to extract body
        3. Check if body is external fetch (@@url) and handle accordingly

        Returns: (status_code, headers, body_bytes)
        """
        # Step 1 & 2: Render with Mako and extract body after '---\n'
        rendered_body = TemplateRenderer.render_and_extract_body(spec.remainder, flow)

        # Step 3: Check for external content fetch
        if ExternalContentFetcher.should_fetch_external(rendered_body):
            return ExternalContentFetcher.fetch(rendered_body, spec.headers)
        else:
            # Normal path: return rendered body as bytes
            body_bytes = rendered_body.encode("utf-8")
            return spec.status, spec.headers, body_bytes


# mitmproxy entry point
addons = [MockResponder()]
