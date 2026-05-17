# Agent Run-Through

This document explains how the theory in `agent/agent-build-instructions.md` shaped the design of the core agent structure in this repository.

## Product Shape

The project needs a Marketing Agent that accepts a `SoftwareSource` as either a GitHub repository URL or a website URL, then produces a monetization-focused `MarketingPlan`. The plan includes transparent `GenerationStage` output, editable markdown, user feedback via `UserIntervention`, `MarketResearch`, `CampaignOrchestration`, and `ContentGeneration` assets.

The core design follows one main idea from the build instructions: choose the smallest agent architecture that gives control over state, tools, retries, review gates, and traces. For the current implementation, the workflow is deterministic and local, so the first version uses ordinary Python boundaries instead of adopting an agent framework before it is needed.

## Framework Choice

`agent-build-instructions.md` recommends choosing a framework based on autonomy versus control:

- PydanticAI for typed production agent services.
- LangGraph for explicit state machines with loops, checkpoints, and interrupts.
- CrewAI or AutoGen for multi-agent experiments.
- No agent framework when the task is a simple workflow.

The current implementation chose the fourth option. The app has a clear first workflow: validate a `SoftwareSource`, create a structured `MarketingPlan`, expose stages, accept feedback, and render the result. Because there are no live model calls, persistent runs, autonomous tool choice, or multi-agent collaboration yet, adding PydanticAI, LangGraph, or CrewAI would add operational complexity before the product needs it.

The design still leaves a framework-friendly path open. The public boundary is `src/marketing_agent/__init__.py`, and provider access is hidden behind the `ModelAdapter` protocol. A later PydanticAI implementation can replace or augment `DeterministicModelAdapter` without moving UI code or changing the Web Interface contract.

## Memory And State

The build instructions distinguish several kinds of memory:

- user-visible memory
- private scratchpad
- workflow state
- audit logs
- persisted conversation history

The current implementation sets up state at the workflow level rather than as long-term persistent memory:

- `SoftwareSource` is the user-visible input.
- `UserIntervention` records user feedback that should influence later plan generation.
- `GenerationStage` records visible workflow state for the UI.
- `MarketingPlan` is the structured output and editable user-facing artifact.
- `editable_markdown` is the user-editable plan surface.

This was a deliberate choice. The product needs users to intervene during generation, but the repository does not yet define authentication, accounts, storage, conversation IDs, retention rules, or privacy policy details for durable memory. Persisting state prematurely would create schema and security decisions without enough product information.

The design keeps a clean upgrade path for durable memory:

- Add a `PlanRepository` adapter when plans need saving.
- Store a schema version with persisted plans and interventions.
- Separate user-visible edits from private model scratchpad and audit records.
- Add trace IDs for each `MarketingAgent` run.

## Tool Setup

The build instructions emphasize narrow, typed, boring tools with clear input and output schemas. They also recommend treating MCP as an agent-facing adapter layer, not as the place where core business rules live.

The current implementation does not expose MCP tools yet. Instead, it uses internal typed Python functions and a `ModelAdapter` protocol:

- `MarketingAgent.generate_marketing_plan(...)` is the public domain operation.
- `DeterministicModelAdapter.summarize_source(...)` is the current provider seam.
- `web_app/server.py` is a thin Web Interface adapter that parses HTTP requests, calls the public Marketing Agent boundary, and serializes JSON.

This matches the guide's advice that not every tool needs MCP. The current tools are private to one service, and standard Python is easier to test than a tool server while the core domain is still stabilizing.

Future tool setup can follow the guide directly:

- Add an MCP server for reusable read tools such as repository inspection, website scraping, market signal lookup, or analytics retrieval.
- Prefix tools by capability, for example `repo_*`, `web_*`, or `market_*`.
- Keep write tools, such as publishing content, behind approval gates.
- Return structured tool results with useful validation errors instead of stack traces.

## Core Structure

The core structure reflects the boundary rules in the project architecture:

- `MarketingAgent` owns domain orchestration.
- `WebInterface` owns browser and HTTP concerns.
- `ModelAdapter` owns the external model provider seam.
- OpenAI and Gemini SDK details are not domain types.
- Browser state does not leak into the Marketing Agent.

The main public entry point is:

```text
src/marketing_agent/__init__.py
```

That file exposes the domain symbols that other contexts may use. The Web Interface imports from this public boundary only. This follows the guide's theme of having explicit interfaces and escape hatches back to normal Python when an abstraction becomes too heavy.

## Design Choices

### Python Core

The design chose Python for the core agent logic because the build instructions are Python-oriented and recommend Python frameworks such as PydanticAI, LangGraph, CrewAI, and FastMCP. Keeping the core in Python makes a future migration to one of those frameworks straightforward.

### No Live Model Calls In The First Slice

The project brief names OpenAI API and Gemini API as external systems, but the security policy says secrets must not be stored in prompts, source files, tests, or logs. The first implementation therefore uses `DeterministicModelAdapter` so tests and local development do not need credentials or network access.

This also supports the build guide's point that deterministic checks and evals should exist before adding more capabilities.

### Internal Sub-Agent Capabilities

The project brief names competitive intelligence, social media management, campaign orchestration, and content generation agents. The design keeps these as internal workflow capabilities for now:

- `MarketResearch`
- `CampaignOrchestration`
- `ContentGeneration`

This follows the guide's recommendation to avoid agent abstractions that are not needed yet. Separate bounded contexts or role-based agents can be introduced later if the workflows gain independent lifecycles, toolsets, memory, or evaluation criteria.

### Thin Web Interface

The Web Interface is a standard-library HTTP adapter. It serves static files and exposes `POST /api/marketing-plan`. It does not contain marketing rules.

This follows the tool-interface guidance: adapters should be narrow and boring, with core behavior behind explicit service boundaries.

### Deterministic Evaluation First

The project check script runs unit and integration tests with `unittest`. The tests cover:

- valid GitHub `SoftwareSource` generation
- valid website `SoftwareSource` parsing
- feedback incorporation through `UserIntervention`
- invalid source rejection
- malformed JSON handling
- Web Interface JSON behavior

This maps to the guide's recommendation to assert invariants even when full agent trajectories are not available yet.

## How Choices Were Made

The design choices were made by applying the framework selection checklist from `agent-build-instructions.md`:

| Question | Current answer | Design result |
| --- | --- | --- |
| Can inputs and outputs be represented as schemas? | Yes, with dataclasses and enums. | Use explicit domain types such as `SoftwareSource` and `MarketingPlan`. |
| Does the run need persistence today? | No product-level persistence requirements exist yet. | Keep memory in structured request/response state. |
| Does the agent need autonomous tool discovery today? | No. The first workflow is known. | Avoid MCP until reusable external tools are needed. |
| Are external providers required for local checks? | No, and requiring secrets would violate security constraints. | Use `DeterministicModelAdapter`. |
| Does the UI need to own generation rules? | No. | Keep the Web Interface thin and delegate to `MarketingAgent`. |
| Are there enough separate lifecycles for multiple bounded contexts? | Not yet. | Keep research, campaign orchestration, and content generation inside `MarketingAgent`. |

## Good Practices Used

- **Explicit public boundary:** `src/marketing_agent/__init__.py` is the only public entry point for the Marketing Agent context.
- **Typed domain language:** domain terms from `agent/ubiquitous-language.md` appear directly in code and tests.
- **Adapter isolation:** HTTP and future model-provider concerns are outside the domain model.
- **No secrets required:** local development and tests do not need OpenAI, Gemini, or any other credentials.
- **Deterministic checks:** `./scripts/check.sh` runs markdown checks, test manifest validation, and Python behavior tests.
- **Edge case tests:** invalid URLs, malformed JSON, incomplete GitHub URLs, and empty feedback are covered.
- **Design memory:** architecture decisions are recorded in `agent/design-tree.md`, `agent/architecture.md`, and `agent/adr/0002-marketing-agent-python-boundary.md`.
- **Browser verification:** the UI was verified with Playwright MCP rather than only by inspecting files.
- **Small tool surface:** the Web Interface exposes one JSON API for plan generation.
- **Framework escape hatch:** the code is ordinary Python, but the `ModelAdapter` seam leaves room for PydanticAI, MCP, or provider-backed agents later.

## Ideas From `agent-build-instructions.md` Not Used Yet

### PydanticAI

Not used because the first version does not call an LLM or need model-output validation retries. The current dataclass boundary gives enough structure for deterministic local behavior. PydanticAI becomes useful when provider-backed generation is added.

### FastMCP Tool Server

Not used because there are no reusable external tools yet. The current Web Interface and model seam are local to this app. MCP should be added when the agent needs reusable repository, website, analytics, market research, or observability tools.

### LangGraph

Not used because the current workflow has known linear stages and no checkpointed loop, resume behavior, or branching state machine. If human review gates, long-running jobs, retries, or resumable stages become central, LangGraph may fit.

### CrewAI Or AutoGen

Not used because named sub-agents do not yet have independent goals, memory, tools, or evaluation sets. The design keeps them as internal workflow capabilities until the boundaries prove durable.

### Persistent Postgres Or Redis Memory

Not used because the product does not yet define users, sessions, retention, plan history, or privacy rules. Persisting memory before those decisions would create accidental policy and schema commitments.

### Trace Platforms Such As LangSmith Or Langfuse

Not used because there are no model or tool trajectories yet. The current substitute is deterministic unit and integration tests. Tracing should be added when LLM calls and tool calls are introduced.

### Fallback Models

Not used because there is no live model provider in the current app. The `ModelAdapter` protocol is the place to add fallback behavior later, such as Gemini fallback after OpenAI failure or vice versa.

### Circuit Breakers And Tool Budgets

Not used because the current generation is deterministic and finite. These become important when the agent can loop, retry provider calls, or call external tools autonomously.

### Sandboxed Code Execution

Not used because the Marketing Agent does not execute user-provided code. If repository analysis later runs builds, tests, or arbitrary scripts, sandboxing becomes mandatory.

### Golden Trajectory Evals

Not used because there are no autonomous tool trajectories yet. The current tests assert final structured behavior. Golden trajectories should be introduced when the agent can choose between tools or multi-step model actions.

### Approval-Gated Write Tools

Not used because automatic publishing is explicitly a non-goal. The app generates plans and content, but it does not post, deploy, charge customers, mutate repositories, or perform production writes.

## Recommended Next Steps

1. Add provider-backed `ModelAdapter` implementations for OpenAI and Gemini with credentials loaded from environment variables.
2. Add prompt versioning and trace IDs before enabling live model calls.
3. Add a repository or website read tool only after defining exactly what evidence the Marketing Agent needs.
4. Add persistence only after user/session and retention rules are clear.
5. Add eval cases for prompt injection, unsupported sources, budget exhaustion, and provider fallback behavior.
