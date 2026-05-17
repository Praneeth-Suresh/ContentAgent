# Design Tree

## Current Design Concept

There should be a separation between the front end which deals with the user interaction segment and the core agent logic which is done using Python. Refer to agent-build-instructions.md for the process of building the agent and strictly adhere to the principles it outlines.

The first bounded context is the Marketing Agent. It owns orchestration of the monetization-focused marketing plan workflow: accepting a software source, exposing transparent generation stages, incorporating user feedback between stages, and producing an editable complete marketing plan plus campaign content. Research, campaign orchestration, and content generation should be modeled as internal workflow capabilities behind the Marketing Agent public boundary until repeated behavior proves they need separate bounded contexts.

## Open Decisions

| Decision | Options | Current Lean | Why |
| --- | --- | --- | --- |
| External model provider implementation. | A. OpenAI adapter first, B. Gemini adapter first, C. Keep deterministic adapter until credentials/config exist | C | The app must not require secrets for local checks; provider-specific work can implement the existing `ModelAdapter` protocol later. |

## Settled Decisions

| Decision | Choice | Date | ADR |
| --- | --- | --- | --- |
| Use Python or Typescript to interface with API. | Python | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Marketing Agent public interface shape. | Python orchestration module exposed to Web Interface adapter | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Sub-agent boundaries for initial slice. | Internal workflow capabilities inside Marketing Agent | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |
| Web Interface implementation. | Standard-library HTTP adapter serving static assets and JSON API | 2026-05-17 | [ADR 0002](adr/0002-marketing-agent-python-boundary.md) |

## Pressure Points

- The Marketing Agent must preserve user intervention points without letting UI state leak into domain orchestration.
- OpenAI and Gemini access must stay behind adapters so prompts, credentials, and vendor client types do not become domain dependencies.
- The deterministic local plan generator is useful for development and tests but should be replaced or augmented by provider-backed `ModelAdapter` implementations when credentials and prompt policies are defined.

## Recording Rule (Design Tree vs ADR)

Add or update this file when:

- A decision is still evolving.
- You are comparing options before implementation.
- The choice may still change after one or two slices.

Create an ADR when:

- The decision changes module boundaries, persistence shape, adapter contracts, security model, naming conventions used across contexts, or test strategy.
- Future contributors are likely to revisit the choice without clear repo history.
