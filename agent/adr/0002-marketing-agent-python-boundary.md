# ADR 0002: Marketing Agent Python Boundary

## Status

Accepted

## Context

The product needs a web experience where users submit a GitHub repository or website, intervene during visible generation stages, edit the resulting plan, and receive market research, campaign orchestration, and multimodal content. The design tree already leans toward Python for the core agent logic and a separate front end for user interaction.

External providers such as OpenAI API and Gemini API are named in the project brief, but local development and deterministic checks cannot depend on secrets, network access, or mutable provider output.

## Decision

Implement `MarketingAgent` as the first bounded context with a single Python public entry point at `src/marketing_agent/__init__.py`.

Keep `MarketResearch`, `CampaignOrchestration`, and `ContentGeneration` as internal workflow capabilities owned by `MarketingAgent` until repeated behavior proves separate bounded contexts are needed.

Expose provider access through a `ModelAdapter` protocol. Use `DeterministicModelAdapter` for local development and tests, and add OpenAI or Gemini adapters later behind the same protocol.

Implement the initial `WebInterface` as a thin standard-library HTTP adapter in `web_app/server.py` that serves static assets and delegates plan generation to the `MarketingAgent` public entry point.

## Consequences

- **Benefit:** The app runs locally without dependency installation, secrets, or remote calls.
- **Benefit:** Tests can verify the complete first workflow deterministically.
- **Benefit:** The UI can evolve independently as long as it calls the public Marketing Agent boundary.
- **Tradeoff:** Generated marketing quality is heuristic until provider-backed adapters are implemented.
- **Tradeoff:** The standard-library web adapter is intentionally small and may need replacement when production deployment, auth, streaming, or persistence become requirements.
