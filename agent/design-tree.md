# Design Tree

## Current Design Concept

There should be a separation between the front end which deals with the user interaction segment and the core agent logic which is done using Python. Refer to agent-build-instructions.md for the process of building the agent and strictly adhere to the principles it outlines.

The first bounded context is the Marketing Agent. It owns orchestration of the monetization-focused marketing plan workflow: accepting a software source, exposing transparent generation stages, incorporating user feedback between stages, routing live model calls by task type, validating every stage artifact, and producing an editable complete marketing plan plus campaign content.

Research, campaign orchestration, monetization experiments, and content generation should be modeled as internal workflow capabilities behind the Marketing Agent public boundary until repeated behavior proves they need separate bounded contexts. Production agent behavior must use PydanticAI only. LangGraph is not an allowed production dependency for this application.

## Open Decisions

| Decision | Options | Current Lean | Why |
| --- | --- | --- | --- |
| Task type to provider routing map. | A. OpenAI primary for all stages with Gemini fallback, B. Gemini primary for research and OpenAI primary for planning/content, C. Configurable route table per task type | C | The requirement is live multi-model routing per task type; a route table keeps provider choice explicit without spreading provider logic across workflow stages. |
| Retry budget defaults. | A. One retry per provider, B. Stage-specific retry budgets, C. Global budget shared by a full run | B | Research, scoring, and content stages have different cost and reliability profiles, so defaults should be stage-specific while remaining bounded. |
| Live provider checks in CI. | A. Required in every deterministic gate, B. Optional credentialed smoke suite, C. Manual-only verification | B | Local and CI checks should not require secrets or network, but live routing still needs an opt-in verification path. |

## Settled Decisions

| Decision | Choice | Date | ADR |
| --- | --- | --- | --- |
| Use Python or Typescript to interface with API. | Python | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Marketing Agent public interface shape. | Python orchestration module exposed to Web Interface adapter | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Sub-agent boundaries for initial slice. | Internal workflow capabilities inside Marketing Agent | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Web Interface implementation. | Standard-library HTTP adapter serving static assets and JSON API | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Web Interface visual direction. | Dark, technical operator workspace with mono controls, compact stage visibility, and a product-preview workflow canvas inspired by Hacktron's dark UI | 2026-05-17 | N/A |
| Production agent framework. | PydanticAI only; do not use LangGraph. | 2026-05-18 | N/A |
| Provider access posture. | Live OpenAI and Gemini calls are production behavior behind PydanticAI adapters; deterministic doubles remain only for local tests and development checks. | 2026-05-18 | N/A |
| Monetization experiment scope. | Generate campaign and offer variants, score conversion potential, CAC risk, and channel fit, then rank recommendations. | 2026-05-18 | N/A |

## Pressure Points

- The Marketing Agent must preserve user intervention points without letting UI state leak into domain orchestration.
- The Web Interface visual treatment should stay dense and operator-focused while keeping Software Source submission, User Intervention capture, stage visibility, and editable Marketing Plan output immediately discoverable.
- OpenAI and Gemini access must stay behind PydanticAI adapters so prompts, credentials, retry policies, provider SDK types, and provider failures do not become UI or domain leaks.
- Structured validation must happen at every stage boundary before an artifact is accepted into the Marketing Plan.
- Retry budgets and fallback chains must prevent unbounded cost, repeated invalid responses, and hidden provider lock-in.
- Deterministic local checks still need provider doubles, but those doubles must not become the production path.
- Monetization scoring should be strict enough to compare variants without pretending provider output is deterministic truth.
- UX changes beyond text that outlines the new capabilities require explicit user permission before implementation.

## Skill Pre-Flight Outputs

```yaml
skill: grill-me
status: success
chosen_approach: "Use a PydanticAI-only Marketing Agent backend with a route table per task type, typed stage artifact schemas, bounded retry budgets, provider fallback chains, and a monetization experiment engine that ranks campaign and offer variants."
rejected_alternatives:
  - option: "LangGraph workflow orchestration"
    reason: "The current requirement explicitly forbids LangGraph, and the needed reliability controls can live in PydanticAI route policies without adding a graph runtime."
  - option: "Single-provider OpenAI-only or Gemini-only implementation"
    reason: "It does not satisfy live multi-model routing or cross-provider fallback."
  - option: "Keep deterministic generation as production behavior"
    reason: "The requested production behavior requires real OpenAI and Gemini calls per task type."
main_risks:
  - "Live provider output may fail schema validation repeatedly and consume retry budget without producing a usable artifact."
  - "Fallback behavior may hide quality regressions unless route attempts and validation failures are observable."
  - "Experiment scoring can look precise while still depending on model judgment unless rubric fields and rationale are explicit."
assumption_that_can_break_plan: "PydanticAI can support the required OpenAI and Gemini provider calls, typed outputs, retries, and fallback policies cleanly enough without introducing another orchestration framework."
first_vertical_slice: "Route one market research task through a PydanticAI live-provider route with typed artifact validation, one fallback provider, a bounded retry budget, and a deterministic test double proving fallback after validation failure."
checks_to_run:
  narrow: ["python3 -m unittest tests.test_marketing_agent_core"]
  broad: ["./scripts/check.sh"]
likely_files_to_change:
  - "src/marketing_agent/__init__.py"
  - "tests/test_marketing_agent_core.py"
  - "agent/project-brief.md"
  - "agent/design-tree.md"
  - "agent/architecture.md"
  - "agent/ubiquitous-language.md"
  - "agent/testing-policy.md"
  - "agent/agent-rules.md"
design_updates:
  update_design_tree: true
  update_architecture: true
  create_or_update_adr: false
notes: "This keeps the bounded context stable while replacing the provider seam with PydanticAI-backed live routing and adding monetization experiments as an internal capability."
```

## Recording Rule (Design Tree vs ADR)

Add or update this file when:

- A decision is still evolving.
- You are comparing options before implementation.
- The choice may still change after one or two slices.

Create an ADR when:

- The decision changes module boundaries, persistence shape, adapter contracts, security model, naming conventions used across contexts, or test strategy.
- Future contributors are likely to revisit the choice without clear repo history.
