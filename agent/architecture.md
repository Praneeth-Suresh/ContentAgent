# Architecture

## Bounded Contexts

| Context | Owns | Does Not Own | Public Entry Point |
| --- | --- | --- | --- |
| Marketing Agent | `SoftwareSource`, `MarketingPlan`, `GenerationStage`, `UserIntervention`, `MarketResearch`, `CampaignOrchestration`, `MonetizationExperiment`, `CampaignVariant`, `OfferVariant`, `RubricScore`, `RankedRecommendation`, `ContentGeneration`, `TaskType`, `LiveModelRoute`, `ReliabilityPolicy`, `RetryBudget`, `FallbackChain`, `StageArtifact`, PydanticAI agent configuration | Browser state, HTTP request/response objects, raw provider SDK clients, persistence, automatic publishing, LangGraph graphs or checkpoints | `src/marketing_agent/__init__.py` |

## Adapters

| Adapter | Owns | Calls | Notes |
| --- | --- | --- | --- |
| Web Interface | Static app shell, HTTP request parsing, JSON serialization, browser feedback capture | `src/marketing_agent/__init__.py` | Implemented with standard-library HTTP in `web_app/server.py`; does not own domain generation rules. |
| PydanticAI Model Gateway | Live OpenAI/Gemini agent calls, provider route execution, structured output validation, retry budget enforcement, fallback selection, provider error normalization | PydanticAI provider integrations | The production provider boundary. Must keep credentials, SDK types, provider prompts, and provider failures outside UI and workflow orchestration. |
| Deterministic Model Double | Stable provider responses and failures for local tests and development checks | PydanticAI Model Gateway boundary | Allowed only for deterministic checks; must not become the production route. |

## Marketing Agent Internal Workflow

1. Validate the `SoftwareSource`.
2. Select a `LiveModelRoute` for the current `TaskType`.
3. Run the route through PydanticAI with typed output for the expected `StageArtifact`.
4. Apply structured validation before accepting the artifact.
5. Spend retries only within the route's `RetryBudget`.
6. Move to the next provider in the `FallbackChain` when provider errors or validation failures exhaust the current provider budget.
7. Generate monetization experiment variants from validated research and campaign context.
8. Score each variant with the rubric fields `conversion_potential`, `cac_risk`, and `channel_fit`.
9. Return ranked recommendations as part of the `MarketingPlan`.

## Boundary Rules

1. A context may import only another context's public entry point.
2. Internal files of another context are forbidden imports.
3. External APIs, SDKs, and persistence details must be accessed through adapters.
4. Domain logic must not depend directly on HTTP objects, ORM records, UI state, or vendor client types.
5. Production agent behavior must use PydanticAI only.
6. LangGraph must not be introduced as a production dependency, import, orchestration runtime, or state checkpoint mechanism.
7. Provider route attempts, validation failures, retry exhaustion, and fallback decisions must be representable as typed domain results or typed adapter errors.
8. A stage artifact must not flow into a later stage until it passes its structured validation schema.

## Public Interface Rule

Each context exposes one explicit public entry point:

- TypeScript: `src/<context>/index.ts`
- Python: `src/<context>/__init__.py`
- Go: exported symbols in `internal/<context>` via deliberate package API

## Forbidden Import Policy

Record concrete forbidden import patterns here once contexts exist:

- `web_app/** -> src/marketing_agent/*` except `src/marketing_agent/__init__.py`
- `src/marketing_agent/** -> web_app/**`
- `src/** -> langgraph/**`
- `src/** -> langchain/**` for orchestration behavior that would bypass the PydanticAI-only rule

Keep this list small and high-signal. Add rules only after repeated boundary mistakes.
