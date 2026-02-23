import re
from pygments.lexer import RegexLexer
from pygments.token import (
    Comment,
    Keyword,
    Name,
    String,
    Number,
    Text,
    Punctuation,
    Whitespace,
)


class CaddyLexer(RegexLexer):
    name = "Caddy"
    aliases = ["caddy", "caddyfile", "Caddyfile"]
    filenames = ["Caddyfile", "*.Caddyfile", "Caddyfile.*"]
    flags = re.MULTILINE | re.UNICODE

    _dq = r'"(?:[^"\\]|\\.|\\\n|\n)*"'  # double-quoted token (can be multiline)
    _bt = r"`(?:[^`]|``|\n)*`"  # backtick token (can be multiline)
    _ph = r"\{[^{}\s][^{}]*\}"  # placeholder token: {uri}, {$ENV}, {http.request.uri}, ...

    tokens = {
        "root": [
            (r"[ \t]+", Whitespace),
            (r"#.*?$", Comment),
            # snippet definitions: (name)
            (r"^\s*(\([A-Za-z_][\w-]*\))", Name.Label),
            (r"^\s*([^#{\n]+)", Name.Namespace),
            (_dq, String.Double),
            (_bt, String.Backtick),
            (_ph, String.Interpol),
            (r"\{", Punctuation, "block"),
            (r"\}", Punctuation),
            (r"\b\d+\b", Number),
            (r"\n", Whitespace),
            (r"[^\s#\{\}]+", Text),
        ],
        "block": [
            (r"[ \t]+", Whitespace),
            (r"#.*?$", Comment),
            (_dq, String.Double),
            (_bt, String.Backtick),
            (_ph, String.Interpol),
            (r"\{", Punctuation, "block"),
            (r"\}", Punctuation, "#pop"),
            # matcher definitions / usage
            (r"(@[A-Za-z_][\w-]*)", Name.Label),
            # directive/subdirective: first token on a line (best-effort)
            (r"^\s*([A-Za-z_][\w-]*)", Keyword),
            (r"\b\d+\b", Number),
            (r"\n", Whitespace),
            (r"[^\s#\{\}]+", Text),
        ],
    }
