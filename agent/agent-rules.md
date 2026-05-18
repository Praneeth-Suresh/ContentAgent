# Agent Rules

## Before Coding

1. Read the minimum relevant canonical files in `agent/`.
2. Identify the bounded context and intended public interface.
3. For non-trivial or ambiguous work, run `grill-me` (the `grill-me` review alias).
4. Choose the smallest deterministic check that can prove behavior.
5. For Marketing Agent model behavior, confirm the design uses PydanticAI only and does not introduce LangGraph.
6. For live provider behavior, define the `TaskType`, `LiveModelRoute`, typed `StageArtifact`, `RetryBudget`, and `FallbackChain` before implementation.

## While Coding

1. Work in one vertical slice at a time.
2. Prefer existing patterns over new abstractions.
3. Define types/interfaces before implementation where possible.
4. Keep public interfaces small; hide detail behind boundaries.
5. Do not reach into another bounded context's internals.
6. Do not weaken tests to pass implementation.
7. For web app or HTML/CSS tasks, use Microsoft Playwright MCP for browser verification instead of screenshot-only assumptions.
8. Keep OpenAI and Gemini calls behind the PydanticAI Model Gateway.
9. Do not import or configure LangGraph.
10. Validate every provider-produced stage artifact before downstream use.
11. Enforce retry budgets and fallback chains as typed behavior, not ad hoc exception handling.
12. Keep monetization experiment scoring strict: variants need conversion potential, CAC risk, channel fit, rationale, and ranked recommendations.

## Before Finishing

1. Run `./scripts/check.sh`.
2. Run any task-specific checks defined in `agent/testing-policy.md`.
3. Update glossary/design tree/architecture/ADRs if durable design changed.
4. For live provider work, report whether credentialed smoke checks were skipped, unavailable, or run explicitly.

## Final Response Contract

Final response must include:

- What changed.
- Which checks ran.
- Which checks were skipped or unavailable.
- Whether tests changed.
- Whether `tests/.manifest.sha256` changed.
- Which skill(s) were used.
- Whether PydanticAI-only and no-LangGraph constraints were preserved.
