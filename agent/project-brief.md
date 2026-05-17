# Project Brief

## Product Goal

It should take in a software that I've built as either a Github repository or a link to a website. Then it should come up with a complete marketing plan for the software that I've built. The goal of marketing should be hard coded into the app as being to monetise these products.

## Primary Workflows

0. **Marketing Agent**: This is the core agent that needs to be built which orchestrates all the other agents and manages all the other workflows as in how it deems necessary. This agent represents the front end of the application where the input field is presented along with the final output of the marketing agent which is a complete plan plus the content. 
1. **UI/UX**: The site needs to be designed in such a way that the user can intervene at any moment. The different stages of the generation of the plan should be presented transparently to the user and the content should be editable so that the subsequent work done by agents can incorporate the creative feedback from the user. Before building the application do a rendering of what the app should look like and then build the app on to match that rendering.
2. **Market Research**: The Competitive intelligence agent and the Social media management agent will Do extensive research on how it is possible to gain the attention of customers who might pay for the product. Figure out the platforms where they're available and what kind of content they respond to and make a detailed content plan that will be passed on to the Campaign orchestration agent.
3. **Campaign Orchestration**: This comes up with a plan of how the campaign should be structured and the material that will be presented in the campaign. This gets passed onto the content generation agent.
4. **Content Generation**: This agent is responsible for generating multi-modal content across text image and video. 

## Non-Goals

- Build a system that automatically takes the actions by posting the content.
- 

## External Systems

| System | Why it exists | Interface owner | Failure fallback |
| --- | --- | --- | --- |
| OpenAI API | To power the agent. | Agent | [Behavior on failure] |
| Gemini API | To assist the agent with certain tasks. | Agent | Fall-back on the OpenAI API. |

## Definition Of Done

A feature is complete only when it has all of the following:

1. A small design artifact update (`design-tree.md` and/or ADR) when design changes.
2. Clear boundary types/interfaces (where language supports this).
3. Behavior tests plus at least one edge case test.
4. Deterministic checks run (`./scripts/check.sh` and relevant project checks).
5. No new illegal boundary crossings.

