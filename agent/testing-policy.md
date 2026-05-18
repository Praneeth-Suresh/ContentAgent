# Testing Policy

## Command Matrix

| Check | Command | Status | Notes |
| --- | --- | --- | --- |
| Markdown sanity | `./scripts/check-md.sh` | available | Unclosed fences and tabs |
| Test manifest immutability check | `./scripts/check-tests-unchanged.sh` | available | Detects changes in configured test scope from `agent/test-manifest.conf` |
| Aggregate deterministic gate | `./scripts/check.sh` | available | Runs all deterministic checks |
| Format | `not available yet` | unavailable | No formatter configured yet |
| Lint | `not available yet` | unavailable | No linter configured yet |
| Typecheck | `not available yet` | unavailable | No typed code configured yet |
| Unit tests | `python3 -m unittest tests.test_marketing_agent_core` | available | Narrow Marketing Agent behavior checks |
| Integration tests | `python3 -m unittest discover -s tests -p 'test_*.py'` | available | Deterministic adapter/API checks; live providers must be replaced with fakes unless running an opt-in credentialed smoke |
| E2E smoke | `not available yet` | unavailable | When web runtime exists, use Microsoft Playwright MCP for deterministic browser feedback |
| Live provider smoke | `not available yet` | unavailable | Future opt-in check only; must require explicit credentials and must not run in the default deterministic gate |

## Default Loop

1. Identify or add the failing behavior.
2. Select the smallest useful test level.
3. Implement one vertical slice.
4. Run narrow checks first, then broader checks.
5. Repair from actual tool output.
6. For web UI or HTML/CSS work, include a Playwright MCP browser verification step.

## PydanticAI Routing Test Rules

- Add deterministic tests before implementing live routing behavior.
- Use provider doubles at the PydanticAI Model Gateway boundary for default unit and integration tests.
- Cover at least one successful preferred-provider route for each new `TaskType`.
- Cover fallback after provider failure and fallback after structured validation failure.
- Cover retry budget exhaustion without making network calls.
- Cover schema validation for every new `StageArtifact`.
- Cover monetization experiment ranking, including conversion potential, CAC risk, and channel fit.
- Keep live OpenAI/Gemini smoke tests opt-in and outside `./scripts/check.sh` unless the project later defines a credential-safe CI profile.

## testing-vertical-slices Output

```yaml
skill: testing-vertical-slices
status: success
chosen_test_level: "integration"
selection_reason: "The first behavior crosses the Marketing Agent workflow and provider boundary, but it can remain deterministic by using provider doubles at the PydanticAI Model Gateway boundary."
behavior_under_test: "A market research task selects its configured live model route, rejects an invalid preferred-provider artifact, spends bounded retry budget, falls back to the alternate provider, validates the returned StageArtifact, and exposes it to the next Marketing Agent stage."
edge_case_targeted: "All providers return schema-invalid artifacts until retry budgets are exhausted, producing a typed failure instead of an unvalidated MarketingPlan."
narrow_checks_first:
  - "python3 -m unittest tests.test_marketing_agent_core"
broader_checks_after:
  - "./scripts/check.sh"
test_files_expected_to_change:
  - "tests/test_marketing_agent_core.py"
manifest_update_required: true
notes: "No implementation is being added in this documentation pass; these checks define the first required behavior slice for the later backend change."
```

## Test Modification Rule

Existing tests may not be weakened to make implementation pass.

Intentional test changes are allowed only when all conditions are met:

1. The behavior change is explicit in the task or design artifact.
2. `./scripts/update-test-manifest.sh` is run after the intentional change.
3. The manifest update is committed with the test change.
4. The final response explains why tests changed.
5. `agent/test-manifest.conf` is updated if new test locations/patterns are introduced.

## Immutability Enforcement Scope

- The SHA manifest mechanism provides deterministic **change detection**, not cryptographic immutability guarantees against privileged users.
- Enforce stronger controls in CI/review policy (branch protection, required status checks, code review).

## Mocking Rules

- Mock external systems (network, clocks, randomness, payment/email providers).
- Do not mock domain logic in the same bounded context.
- Do not call live OpenAI or Gemini services in deterministic tests.
- Mock or fake only the provider boundary; validation, route selection, retry budgets, fallback decisions, scoring, and ranking remain real Marketing Agent behavior in tests.
