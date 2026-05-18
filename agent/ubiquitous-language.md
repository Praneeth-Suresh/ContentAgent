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
| Model Adapter | `ModelAdapter` | Legacy name for the model-provider integration boundary around external model providers such as OpenAI API and Gemini API. | New production work should express this boundary as the PydanticAI Model Gateway. Must keep credentials, SDK types, and provider-specific failures outside domain logic. | `OpenAIClient` as domain type |
| Web Interface | `WebInterface` | Browser and HTTP adapter that captures Software Source and User Intervention data, then renders the Marketing Plan. | Must call the Marketing Agent public entry point instead of owning domain generation rules. | `FrontendAgent`, `UIBrain` |
| Deterministic Model Double | `DeterministicModelDouble` | Local test/development double that produces stable provider outcomes without external calls. | Must not require secrets or network access. Must not be the production route. | `MockAgent`, `DeterministicModelAdapter` as production behavior |
| PydanticAI Model Gateway | `PydanticAIModelGateway` | Production adapter that runs OpenAI and Gemini calls through PydanticAI and returns typed stage artifacts or typed failures. | Must own provider configuration, credentials lookup, retry execution, fallback execution, and schema validation at the provider boundary. | `LangGraphRunner`, direct SDK calls from workflow code |
| Task Type | `TaskType` | Classification of model work such as market research, campaign orchestration, experiment scoring, or content generation. | Must select an explicit Live Model Route before calling a provider. | `PromptKind`, `StepName` |
| Live Model Route | `LiveModelRoute` | Provider route for a Task Type, including preferred provider, model identifier, fallback chain, timeout, and retry budget. | Must be auditable and bounded before execution. | `RandomProviderChoice` |
| Reliability Policy | `ReliabilityPolicy` | Rules that govern retries, fallback, validation failure handling, and typed provider errors. | Must prevent unbounded cost and hidden failure loops. | `TryUntilItWorks` |
| Retry Budget | `RetryBudget` | Maximum retry allowance for a provider route or stage. | Must be finite and visible in tests. | `RetryCountMaybe` |
| Fallback Chain | `FallbackChain` | Ordered provider sequence used after provider errors or validation failures exhaust the current route budget. | Must include termination behavior when all providers fail. | `BackupModel` |
| Stage Artifact | `StageArtifact` | Typed output accepted from a Generation Stage, such as research findings, campaign plan, experiment scores, or content briefs. | Must pass structured validation before downstream stages consume it. | `LLMOutput`, `Blob` |
| Structured Validation | `StructuredValidation` | Pydantic-backed validation of provider output against the expected artifact schema. | Validation errors must be observable and may spend retry budget. | `ParseLater` |
| Monetization Experiment | `MonetizationExperiment` | A set of campaign and offer variants generated and evaluated to improve the chance of monetizing the submitted software. | Must produce ranked recommendations, not just unscored ideas. | `GrowthHackList` |
| Campaign Variant | `CampaignVariant` | A proposed campaign structure, audience, channel mix, and message angle for a monetization experiment. | Must be comparable through rubric scoring. | `CampaignIdea` |
| Offer Variant | `OfferVariant` | A proposed monetization offer, packaging, pricing angle, or incentive to test. | Must connect to a campaign variant or recommendation. | `DealIdea` |
| Rubric Score | `RubricScore` | Structured scoring result for a variant using conversion potential, CAC risk, and channel fit. | Must include numeric scores and rationale. | `VibeScore` |
| Conversion Potential | `ConversionPotential` | Rubric dimension estimating how likely a variant is to convert qualified users into paying customers. | Must be scored explicitly. | `Appeal` |
| CAC Risk | `CACRisk` | Rubric dimension estimating customer acquisition cost risk for a variant or channel mix. | Must be scored explicitly and interpreted so high risk does not look like high quality. | `CostConcern` |
| Channel Fit | `ChannelFit` | Rubric dimension estimating whether a variant fits the audience and distribution channel. | Must be scored explicitly. | `PlatformMatchMaybe` |
| Ranked Recommendation | `RankedRecommendation` | Ordered monetization experiment recommendation with scores, rationale, and next action. | Must be derived from validated variant scores. | `TopIdea` |
