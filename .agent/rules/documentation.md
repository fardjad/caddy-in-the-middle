______________________________________________________________________

## trigger: always_on

# Documentation Rules

These rules dictate the strict structural, stylistic, and operational guidelines
required for managing the `Caddy in the Middle` (CITM) documentation site.

## 1. Information Architecture

- **Framework**: Documentation MUST adhere strictly to the
  [Diátaxis framework](https://diataxis.fr/) (Tutorials, How-To guides,
  Reference, Explanation).
- **Directory Structure**: All Markdown source content resides strictly inside
  the `docs/src/` directory.

## 2. Writing Style and Tone

- **Strictly Factual**: The tone of the documentation must be strictly factual,
  objective, and technical.
- **Prohibited Patterns**: Conversational filler, marketing language, and
  AI-like present participle clauses (e.g., using "...domains, removing the
  need...") are prohibited. Sentences must be direct and definitive (e.g.,
  "...domains. This removes the need...").

## 3. Tooling and Operations

- **System Stack**: The documentation relies on Zensical (a zero-config wrapper
  around MkDocs and Material for MkDocs). Dependencies are managed via `uv`
  within the `docs/pyproject.toml` file.
- **Formatting Constraints**: Markdown files require automatic formatting using
  `mdformat` with a strict hard line wrap at 80 characters. The `just format`
  (or `just format-markdown`) command enforces this.
- **Local Building**: The `just docs-build` command must be used to generate the
  static site.
- **Live Preview**: The `just docs-serve` command must be used for a local
  live-reloading development server. As this is a blocking command, it must be
  run in the background if the terminal output needs to be reviewed
  concurrently.
- **Build Caching**: Build caching may cause issues, particularly when modifying
  or introducing dependencies such as `caddy_lexer` (used for highlighting caddy
  blocks). Clearing the cache is required if syntax highlighting fails to
  update.
