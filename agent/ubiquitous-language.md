# Ubiquitous Language

| Business Term | Technical Symbol | Definition | Constraints | Avoid |
| --- | --- | --- | --- | --- |
| Design Concept | `DesignConcept` | The shared organizing model guiding architecture and implementation choices. | Must be coherent across contexts. | `Idea`, `GeneralModel` |
| Design Tree | `DesignTree` | Living map of open and settled decisions. | Updated when design moves. | `PlanDump` |
| Bounded Context | `BoundedContext` | A domain boundary with explicit ownership and language. | Owns its internal model and API. | `Module` (too generic) |
| Ubiquitous Language | `UbiquitousLanguage` | Shared domain vocabulary in docs and code. | Terms must be stable and explicit. | Ambiguous nouns like `Data` |
| Feedback Loop | `FeedbackLoop` | Generate-check-fix cycle using deterministic tools. | Must include real tool output. | `TryAgainLoop` |
| Entropy Hotspot | `EntropyHotspot` | High-churn and high-complexity area likely to degrade maintainability. | Used for targeted refactoring. | `MessyFile` |
| Vertical Slice | `VerticalSlice` | Smallest end-to-end behavior change through one boundary. | Must be testable in isolation. | `BigRefactor` |
| Adapter | `Adapter` | Boundary object that isolates external systems from domain logic. | Domain must not depend on vendor details. | `ServiceHelper` |
| Seam | `Seam` | Intentional change point for behavior substitution without invasive edits. | Should be protected by tests. | `HackPoint` |
| ADR | `ADR` | Architecture Decision Record for durable decisions. | Required for lasting boundary changes. | `RandomNote` |
| Marketing Agent | `MarketingAgent` | Primary orchestrator that turns a software source into a monetization-focused marketing plan and campaign content. | Owns workflow coordination, stage visibility, and feedback incorporation. | `MainBot`, `FrontendAgent` |
| Software Source | `SoftwareSource` | User-provided GitHub repository or website URL representing the product to market. | Must be validated before analysis and must not expose secrets in logs or prompts. | `Input`, `Link` |
| Marketing Plan | `MarketingPlan` | Complete monetization-oriented plan for attracting paying customers to the submitted software. | Must remain editable before downstream content generation uses it. | `Output`, `StrategyDump` |
| Generation Stage | `GenerationStage` | Visible phase of the Marketing Agent workflow, such as research, campaign orchestration, or content generation. | Must expose status and intervention points to the UI. | `Step`, `PhaseThing` |
| User Intervention | `UserIntervention` | User feedback or edits applied while a generation stage is active or between stages. | Later workflow work must incorporate accepted feedback. | `ManualOverride`, `Comment` |
| Market Research | `MarketResearch` | Discovery of paying customer segments, competitive signals, channels, and content patterns for the software source. | Must produce evidence usable by campaign orchestration. | `ResearchStuff` |
| Campaign Orchestration | `CampaignOrchestration` | Planning of campaign structure, channel sequence, and required campaign materials. | Consumes market research and feeds content generation. | `CampaignIdeas` |
| Content Generation | `ContentGeneration` | Creation of text, image, and video campaign assets from the campaign plan. | Must stay downstream of approved plan and feedback. | `AssetMaker` |
| Model Adapter | `ModelAdapter` | Integration boundary around external model providers such as OpenAI API and Gemini API. | Must keep credentials, SDK types, and provider-specific failures outside domain logic. | `OpenAIClient` as domain type |
| Web Interface | `WebInterface` | Browser and HTTP adapter that captures Software Source and User Intervention data, then renders the Marketing Plan. | Must call the Marketing Agent public entry point instead of owning domain generation rules. | `FrontendAgent`, `UIBrain` |
| Deterministic Model Adapter | `DeterministicModelAdapter` | Local Model Adapter that produces stable development and test summaries without external calls. | Must not require secrets or network access. | `MockAgent` |
