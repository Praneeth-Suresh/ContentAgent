# Architecture

## Bounded Contexts

| Context | Owns | Does Not Own | Public Entry Point |
| --- | --- | --- | --- |
| Marketing Agent | `SoftwareSource`, `MarketingPlan`, `GenerationStage`, `UserIntervention`, `MarketResearch`, `CampaignOrchestration`, `ContentGeneration`, `ModelAdapter` protocol | Browser state, HTTP request/response objects, provider SDK clients, persistence, automatic publishing | `src/marketing_agent/__init__.py` |

## Adapters

| Adapter | Owns | Calls | Notes |
| --- | --- | --- | --- |
| Web Interface | Static app shell, HTTP request parsing, JSON serialization, browser feedback capture | `src/marketing_agent/__init__.py` | Implemented with standard-library HTTP in `web_app/server.py`; does not own domain generation rules. |
| Deterministic Model Adapter | Local source summary when no external provider is configured | `ModelAdapter` protocol | Keeps development and tests deterministic. |
| External Model Adapter | Future OpenAI API or Gemini API access | `ModelAdapter` protocol | Must keep credentials, SDK types, provider prompts, and provider failures outside domain logic. |

## Boundary Rules

1. A context may import only another context's public entry point.
2. Internal files of another context are forbidden imports.
3. External APIs, SDKs, and persistence details must be accessed through adapters.
4. Domain logic must not depend directly on HTTP objects, ORM records, UI state, or vendor client types.

## Public Interface Rule

Each context exposes one explicit public entry point:

- TypeScript: `src/<context>/index.ts`
- Python: `src/<context>/__init__.py`
- Go: exported symbols in `internal/<context>` via deliberate package API

## Forbidden Import Policy

Record concrete forbidden import patterns here once contexts exist:

- `web_app/** -> src/marketing_agent/*` except `src/marketing_agent/__init__.py`
- `src/marketing_agent/** -> web_app/**`

Keep this list small and high-signal. Add rules only after repeated boundary mistakes.
