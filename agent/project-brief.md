# Project Brief

## Product Goal

It should take in a software that I've built as either a GitHub repository or a link to a website. Then it should come up with a complete marketing plan for the software that I've built. The goal of marketing should be hard coded into the app as being to monetise these products.

The Marketing Agent must use PydanticAI as the only production agent framework. It must not use LangGraph. Production generation should use live OpenAI and Gemini model calls through PydanticAI, routed by task type with fallback, retry budgets, and structured validation for every stage artifact.

## Primary Workflows

0. **Marketing Agent**: This is the core agent that orchestrates the other workflow capabilities and manages the primary monetization workflow. The backend owns the agent behavior; the front end presents the input field, transparent stage progress, intervention points, and the final editable marketing plan plus content.
1. **UI/UX**: The site needs to be designed in such a way that the user can intervene at any moment. The different stages of the generation of the plan should be presented transparently to the user and the content should be editable so that the subsequent work done by agents can incorporate the creative feedback from the user. Before building the application do a rendering of what the app should look like and then build the app on to match that rendering.
2. **Live Multi-Model Routing**: For each task type, route the request through PydanticAI to the preferred live provider model, starting with OpenAI and Gemini. Each route must define a fallback chain, retry budget, timeout/error handling behavior, and structured output schema for the stage artifact it returns.
3. **Market Research**: The Competitive Intelligence and Social Media Management capabilities do extensive research on how it is possible to gain the attention of customers who might pay for the product. They identify where customers are available, what content they respond to, and which evidence should be passed to Campaign Orchestration.
4. **Campaign Orchestration**: This comes up with a plan of how the campaign should be structured and the material that will be presented in the campaign. It consumes validated research artifacts and feeds Content Generation.
5. **Monetization Experiment Engine**: Generate multiple campaign and offer variants, score them with a strict rubric covering conversion potential, CAC risk, and channel fit, then output ranked recommendations with rationale and next actions.
6. **Content Generation**: This capability is responsible for generating multimodal content across text, image, and video from the selected campaign and offer recommendations.

## Success Conditions

The application succeeds when a user can submit a software source and receive a monetization-focused plan that was produced through validated stage artifacts, live routed OpenAI/Gemini calls with reliable fallback behavior, and ranked monetization recommendations based on explicit rubric scores.

## Non-Goals

- Build a system that automatically takes the actions by posting the content.
- Use LangGraph or any other graph orchestration framework for the production Marketing Agent workflow.

## External Systems

| System | Why it exists | Interface owner | Failure fallback |
| --- | --- | --- | --- |
| OpenAI API | Live model provider for routed task types where OpenAI is preferred or used as fallback. | Marketing Agent PydanticAI adapter | Retry within route budget, validate structured output, then fall back to configured Gemini route or return a typed provider failure. |
| Gemini API | Live model provider for routed task types where Gemini is preferred or used as fallback. | Marketing Agent PydanticAI adapter | Retry within route budget, validate structured output, then fall back to configured OpenAI route or return a typed provider failure. |

## Definition Of Done

A feature is complete only when it has all of the following:

1. A small design artifact update (`design-tree.md` and/or ADR) when design changes.
2. Clear boundary types/interfaces (where language supports this).
3. Behavior tests plus at least one edge case test.
4. Deterministic checks run (`./scripts/check.sh` and relevant project checks).
5. No new illegal boundary crossings.
6. Production agent behavior uses PydanticAI only and does not introduce LangGraph.
7. Any live model stage has typed schemas, validation failure handling, retry-budget coverage, and fallback behavior tests.
8. Monetization experiment output includes ranked recommendations with conversion potential, CAC risk, and channel fit scores.
