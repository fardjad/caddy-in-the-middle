______________________________________________________________________

## trigger: always_on

# Rule Authoring Rules

These rules define how repository rule files must be written and maintained.

## 1. Rule Purpose and Scope

- Rules define required constraints, not suggestions.
- Each rule file must state a clear scope boundary and avoid overlap with
  unrelated areas.
- When two rules touch adjacent areas, each rule must keep non-overlapping
  responsibilities.

## 2. Writing Style

- Language must be factual, direct, and technical.
- Sentences must describe required behavior and expected outcomes.
- Conversational phrasing, motivational phrasing, and speculative wording must
  not be used.
- Use concrete terms for commands, paths, interfaces, and artifacts when those
  details are contractual.

## 3. Specificity Level

- Encode principles by default.
- Include implementation-specific details only when they are contractual for
  runtime compatibility, safety, or toolchain behavior.
- Avoid brittle lists of module-specific test cases unless those cases are
  required contracts.

## 4. Consistency and Maintenance

- New rule files must follow the existing file structure used in `.agent/rules/`
  (separator, `trigger`, title, numbered sections).
- Rule updates must remove or replace stale statements that no longer match the
  repository.
- Conflicting statements across rule files must not be introduced.

## 5. Validation

- After modifying rule files, run `just format`.
- After formatting, run `just check`.
