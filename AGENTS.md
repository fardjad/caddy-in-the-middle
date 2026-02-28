# Agent Instructions

Before starting work, dynamically discover and read every Markdown rule file in
`.agent/rules/`.

Use this command to get the full set of rules:

```bash
find .agent/rules -type f -name "*.md" | sort
```

Read and follow every file returned by that command.

These rules are always-on for this repository and must be treated as required.
