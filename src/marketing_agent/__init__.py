"""Public boundary for the Marketing Agent bounded context."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Protocol
from urllib.parse import urlparse


class SoftwareSourceKind(str, Enum):
    """Supported source kinds for software submitted to the Marketing Agent."""

    GITHUB_REPOSITORY = "github_repository"
    WEBSITE = "website"


class GenerationStageStatus(str, Enum):
    """Visible workflow status for a Generation Stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"


class TaskType(str, Enum):
    """Model-routed task types owned by the Marketing Agent."""

    MARKET_RESEARCH = "market_research"
    CAMPAIGN_ORCHESTRATION = "campaign_orchestration"
    MONETIZATION_EXPERIMENT = "monetization_experiment"
    CONTENT_GENERATION = "content_generation"


@dataclass(frozen=True)
class SoftwareSource:
    """User-provided GitHub repository or website URL representing the product."""

    url: str
    kind: SoftwareSourceKind
    product_name: str

    @classmethod
    def from_url(cls, raw_url: str) -> "SoftwareSource":
        sanitized = _sanitize_url(raw_url)
        parsed = urlparse(sanitized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(char.isspace() for char in parsed.netloc):
            raise ValueError("SoftwareSource must be an http(s) GitHub repository or website URL.")

        kind = SoftwareSourceKind.WEBSITE
        if parsed.netloc.lower() == "github.com":
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) < 2:
                raise ValueError("GitHub SoftwareSource must include owner and repository name.")
            kind = SoftwareSourceKind.GITHUB_REPOSITORY
            product_name = _title_from_slug(parts[1])
        else:
            product_name = _title_from_slug(parsed.netloc.split(":")[0].split(".")[0])

        return cls(url=sanitized, kind=kind, product_name=product_name)


@dataclass(frozen=True)
class UserIntervention:
    """User feedback or edits accepted by the Marketing Agent workflow."""

    stage_name: str
    feedback: str


@dataclass(frozen=True)
class GenerationStage:
    """Visible phase in the Marketing Agent workflow."""

    name: str
    status: GenerationStageStatus
    summary: str
    intervention_prompt: str


@dataclass(frozen=True)
class MarketResearch:
    """Evidence used to find paying customers and channels."""

    audience_segments: tuple[str, ...]
    competitive_signals: tuple[str, ...]
    channels: tuple[str, ...]
    content_patterns: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "audience_segments", _non_empty_strings(self.audience_segments, "audience_segments"))
        object.__setattr__(self, "competitive_signals", _non_empty_strings(self.competitive_signals, "competitive_signals"))
        object.__setattr__(self, "channels", _non_empty_strings(self.channels, "channels"))
        object.__setattr__(self, "content_patterns", _non_empty_strings(self.content_patterns, "content_patterns"))


@dataclass(frozen=True)
class CampaignOrchestration:
    """Campaign structure and material plan for monetization."""

    objective: str
    sequence: tuple[str, ...]
    channel_plan: tuple[str, ...]
    required_materials: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "objective", _non_empty_string(self.objective, "objective"))
        object.__setattr__(self, "sequence", _non_empty_strings(self.sequence, "sequence"))
        object.__setattr__(self, "channel_plan", _non_empty_strings(self.channel_plan, "channel_plan"))
        object.__setattr__(self, "required_materials", _non_empty_strings(self.required_materials, "required_materials"))


@dataclass(frozen=True)
class ContentGeneration:
    """Multimodal campaign assets generated from the campaign plan."""

    text_assets: tuple[str, ...]
    image_briefs: tuple[str, ...]
    video_briefs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "text_assets", _non_empty_strings(self.text_assets, "text_assets"))
        object.__setattr__(self, "image_briefs", _non_empty_strings(self.image_briefs, "image_briefs"))
        object.__setattr__(self, "video_briefs", _non_empty_strings(self.video_briefs, "video_briefs"))


@dataclass(frozen=True)
class CampaignVariant:
    """A proposed campaign structure for monetization experiments."""

    variant_id: str
    name: str
    audience_segment: str
    channel: str
    message_angle: str

    def __post_init__(self) -> None:
        for field_name in ("variant_id", "name", "audience_segment", "channel", "message_angle"):
            object.__setattr__(self, field_name, _non_empty_string(getattr(self, field_name), field_name))


@dataclass(frozen=True)
class OfferVariant:
    """A proposed offer shape for monetization experiments."""

    variant_id: str
    name: str
    pricing_angle: str
    incentive: str
    call_to_action: str

    def __post_init__(self) -> None:
        for field_name in ("variant_id", "name", "pricing_angle", "incentive", "call_to_action"):
            object.__setattr__(self, field_name, _non_empty_string(getattr(self, field_name), field_name))


@dataclass(frozen=True)
class RubricScore:
    """Strict score for a campaign and offer recommendation."""

    conversion_potential: int
    cac_risk: int
    channel_fit: int
    rationale: str

    def __post_init__(self) -> None:
        for field_name in ("conversion_potential", "cac_risk", "channel_fit"):
            score = getattr(self, field_name)
            if not isinstance(score, int) or score < 1 or score > 5:
                raise ValueError(f"RubricScore {field_name} must be an integer from 1 to 5.")
        object.__setattr__(self, "rationale", _non_empty_string(self.rationale, "rationale"))

    @property
    def weighted_score(self) -> int:
        """Higher is better; CAC risk is subtracted because it is downside risk."""

        return self.conversion_potential + self.channel_fit - self.cac_risk


@dataclass(frozen=True)
class RankedRecommendation:
    """Ranked monetization recommendation derived from a rubric score."""

    rank: int
    campaign_variant: CampaignVariant
    offer_variant: OfferVariant
    score: RubricScore
    next_action: str

    def __post_init__(self) -> None:
        if not isinstance(self.rank, int) or self.rank < 1:
            raise ValueError("RankedRecommendation rank must be a positive integer.")
        object.__setattr__(self, "next_action", _non_empty_string(self.next_action, "next_action"))


@dataclass(frozen=True)
class MonetizationExperiment:
    """Campaign and offer variants with ranked monetization recommendations."""

    campaign_variants: tuple[CampaignVariant, ...]
    offer_variants: tuple[OfferVariant, ...]
    ranked_recommendations: tuple[RankedRecommendation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "campaign_variants", _non_empty_items(self.campaign_variants, CampaignVariant, "campaign_variants"))
        object.__setattr__(self, "offer_variants", _non_empty_items(self.offer_variants, OfferVariant, "offer_variants"))
        object.__setattr__(
            self,
            "ranked_recommendations",
            _non_empty_items(self.ranked_recommendations, RankedRecommendation, "ranked_recommendations"),
        )
        ranks = tuple(item.rank for item in self.ranked_recommendations)
        if ranks != tuple(range(1, len(ranks) + 1)):
            raise ValueError("MonetizationExperiment ranked_recommendations must have contiguous ranks.")
        weighted_scores = tuple(item.score.weighted_score for item in self.ranked_recommendations)
        if weighted_scores != tuple(sorted(weighted_scores, reverse=True)):
            raise ValueError("MonetizationExperiment ranked_recommendations must be sorted by weighted score.")


@dataclass(frozen=True)
class RetryBudget:
    """Bounded retry allowance for each provider in a live model route."""

    attempts_per_provider: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.attempts_per_provider, int) or self.attempts_per_provider < 1:
            raise ValueError("RetryBudget attempts_per_provider must be at least 1.")


@dataclass(frozen=True)
class ProviderRoute:
    """Single provider/model choice inside a fallback chain."""

    provider: str
    model: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _non_empty_string(self.provider, "provider"))
        object.__setattr__(self, "model", _non_empty_string(self.model, "model"))


@dataclass(frozen=True)
class LiveModelRoute:
    """Route table entry for a task type."""

    task_type: TaskType
    providers: tuple[ProviderRoute, ...]
    retry_budget: RetryBudget = field(default_factory=RetryBudget)

    def __post_init__(self) -> None:
        object.__setattr__(self, "providers", _non_empty_items(self.providers, ProviderRoute, "providers"))


@dataclass(frozen=True)
class ModelTaskRequest:
    """Context sent to a provider for one model-routed task."""

    task_type: TaskType
    software_source: SoftwareSource
    user_interventions: tuple[UserIntervention, ...] = ()
    stage_inputs: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderAttempt:
    """Observable provider attempt made while routing a task."""

    task_type: TaskType
    provider: str
    model: str
    attempt: int
    status: str
    message: str


@dataclass(frozen=True)
class StageRunResult:
    """Validated artifact and attempts for a routed task."""

    artifact: object
    attempts: tuple[ProviderAttempt, ...]


class ModelRoutingError(RuntimeError):
    """Raised when all providers fail or return invalid artifacts."""


class ProviderExecutionError(RuntimeError):
    """Raised by provider clients for normalized provider failures."""


class ProviderClient(Protocol):
    """Provider boundary used by the PydanticAI Model Gateway."""

    def complete(
        self,
        provider_route: ProviderRoute,
        request: ModelTaskRequest,
        output_type: type[object],
    ) -> object:
        """Return raw or typed provider output for one task attempt."""


class PydanticAIProviderClient:
    """Live provider client that calls OpenAI/Gemini through PydanticAI only."""

    def complete(
        self,
        provider_route: ProviderRoute,
        request: ModelTaskRequest,
        output_type: type[object],
    ) -> object:
        try:
            from pydantic_ai import Agent
        except ImportError as exc:
            raise ProviderExecutionError(
                "pydantic_ai is required for live model routing. Install pydantic-ai and configure provider API keys."
            ) from exc

        agent = Agent(
            model=provider_route.model,
            output_type=output_type,
            system_prompt=_system_prompt_for(request.task_type),
        )
        try:
            result = agent.run_sync(_prompt_for(request))
        except Exception as exc:  # pragma: no cover - exercised only with live provider credentials.
            raise ProviderExecutionError(str(exc)) from exc
        return getattr(result, "output", getattr(result, "data", result))


class DeterministicModelDouble:
    """Provider double that exercises routing without live network calls."""

    def complete(
        self,
        provider_route: ProviderRoute,
        request: ModelTaskRequest,
        output_type: type[object],
    ) -> object:
        if output_type is MarketResearch:
            return _deterministic_market_research(request.software_source, request.user_interventions)
        if output_type is CampaignOrchestration:
            research = _require_stage_input(request, "market_research", MarketResearch)
            return _deterministic_campaign_orchestration(
                request.software_source,
                research,
                request.user_interventions,
            )
        if output_type is MonetizationExperiment:
            research = _require_stage_input(request, "market_research", MarketResearch)
            campaign = _require_stage_input(request, "campaign_orchestration", CampaignOrchestration)
            return _deterministic_monetization_experiment(
                request.software_source,
                research,
                campaign,
                request.user_interventions,
            )
        if output_type is ContentGeneration:
            campaign = _require_stage_input(request, "campaign_orchestration", CampaignOrchestration)
            experiment = _require_stage_input(request, "monetization_experiment", MonetizationExperiment)
            return _deterministic_content_generation(
                request.software_source,
                campaign,
                experiment,
                request.user_interventions,
            )
        raise ProviderExecutionError(f"No deterministic provider output for {output_type!r}.")


class PydanticAIModelGateway:
    """Runs routed model tasks with validation, retries, and provider fallback."""

    def __init__(
        self,
        routes: dict[TaskType, LiveModelRoute] | None = None,
        provider_client: ProviderClient | None = None,
    ) -> None:
        route_table = _default_routes()
        route_table.update(routes or {})
        self._routes = route_table
        self._provider_client = provider_client or PydanticAIProviderClient()

    def run_task(self, request: ModelTaskRequest, output_type: type[object]) -> StageRunResult:
        route = self._routes.get(request.task_type)
        if route is None:
            raise ModelRoutingError(f"No LiveModelRoute configured for {request.task_type.value}.")

        attempts: list[ProviderAttempt] = []
        for provider_route in route.providers:
            for attempt_number in range(1, route.retry_budget.attempts_per_provider + 1):
                try:
                    raw_artifact = self._provider_client.complete(provider_route, request, output_type)
                    artifact = _coerce_stage_artifact(output_type, raw_artifact)
                except ProviderExecutionError as exc:
                    attempts.append(
                        _provider_attempt(request, provider_route, attempt_number, "provider_error", str(exc))
                    )
                    continue
                except ValueError as exc:
                    attempts.append(
                        _provider_attempt(request, provider_route, attempt_number, "validation_error", str(exc))
                    )
                    continue

                attempts.append(
                    _provider_attempt(request, provider_route, attempt_number, "success", "validated")
                )
                return StageRunResult(artifact=artifact, attempts=tuple(attempts))

        last_message = attempts[-1].message if attempts else "no provider attempts were made"
        raise ModelRoutingError(
            f"{request.task_type.value} failed after {len(attempts)} provider attempt(s): {last_message}"
        )


@dataclass(frozen=True)
class MarketingPlan:
    """Editable monetization-oriented plan returned by the Marketing Agent."""

    plan_id: str
    software_source: SoftwareSource
    generated_on: str
    monetization_goal: str
    executive_summary: str
    generation_stages: tuple[GenerationStage, ...]
    user_interventions: tuple[UserIntervention, ...]
    market_research: MarketResearch
    campaign_orchestration: CampaignOrchestration
    monetization_experiment: MonetizationExperiment
    content_generation: ContentGeneration
    provider_attempts: tuple[ProviderAttempt, ...]
    editable_markdown: str

    def to_dict(self) -> dict[str, object]:
        """Return JSON-serializable MarketingPlan data for adapters."""

        return {
            "plan_id": self.plan_id,
            "software_source": {
                "url": self.software_source.url,
                "kind": self.software_source.kind.value,
                "product_name": self.software_source.product_name,
            },
            "generated_on": self.generated_on,
            "monetization_goal": self.monetization_goal,
            "executive_summary": self.executive_summary,
            "generation_stages": [
                {
                    "name": stage.name,
                    "status": stage.status.value,
                    "summary": stage.summary,
                    "intervention_prompt": stage.intervention_prompt,
                }
                for stage in self.generation_stages
            ],
            "user_interventions": [
                {"stage_name": item.stage_name, "feedback": item.feedback}
                for item in self.user_interventions
            ],
            "market_research": {
                "audience_segments": list(self.market_research.audience_segments),
                "competitive_signals": list(self.market_research.competitive_signals),
                "channels": list(self.market_research.channels),
                "content_patterns": list(self.market_research.content_patterns),
            },
            "campaign_orchestration": {
                "objective": self.campaign_orchestration.objective,
                "sequence": list(self.campaign_orchestration.sequence),
                "channel_plan": list(self.campaign_orchestration.channel_plan),
                "required_materials": list(self.campaign_orchestration.required_materials),
            },
            "monetization_experiment": {
                "campaign_variants": [
                    {
                        "variant_id": variant.variant_id,
                        "name": variant.name,
                        "audience_segment": variant.audience_segment,
                        "channel": variant.channel,
                        "message_angle": variant.message_angle,
                    }
                    for variant in self.monetization_experiment.campaign_variants
                ],
                "offer_variants": [
                    {
                        "variant_id": variant.variant_id,
                        "name": variant.name,
                        "pricing_angle": variant.pricing_angle,
                        "incentive": variant.incentive,
                        "call_to_action": variant.call_to_action,
                    }
                    for variant in self.monetization_experiment.offer_variants
                ],
                "ranked_recommendations": [
                    {
                        "rank": recommendation.rank,
                        "campaign_variant_id": recommendation.campaign_variant.variant_id,
                        "offer_variant_id": recommendation.offer_variant.variant_id,
                        "score": {
                            "conversion_potential": recommendation.score.conversion_potential,
                            "cac_risk": recommendation.score.cac_risk,
                            "channel_fit": recommendation.score.channel_fit,
                            "weighted_score": recommendation.score.weighted_score,
                            "rationale": recommendation.score.rationale,
                        },
                        "next_action": recommendation.next_action,
                    }
                    for recommendation in self.monetization_experiment.ranked_recommendations
                ],
            },
            "content_generation": {
                "text_assets": list(self.content_generation.text_assets),
                "image_briefs": list(self.content_generation.image_briefs),
                "video_briefs": list(self.content_generation.video_briefs),
            },
            "provider_attempts": [
                {
                    "task_type": attempt.task_type.value,
                    "provider": attempt.provider,
                    "model": attempt.model,
                    "attempt": attempt.attempt,
                    "status": attempt.status,
                    "message": attempt.message,
                }
                for attempt in self.provider_attempts
            ],
            "editable_markdown": self.editable_markdown,
        }


class ModelAdapter(Protocol):
    """Boundary around external model providers."""

    def summarize_source(self, software_source: SoftwareSource) -> str:
        """Return a model summary without exposing provider client types."""


class DeterministicModelAdapter:
    """Local Model Adapter used when no external provider is configured."""

    def summarize_source(self, software_source: SoftwareSource) -> str:
        source_type = "GitHub repository" if software_source.kind == SoftwareSourceKind.GITHUB_REPOSITORY else "website"
        return f"{software_source.product_name} is a submitted {source_type} ready for monetization planning."


class MarketingAgent:
    """Orchestrates the monetization-focused marketing workflow."""

    def __init__(
        self,
        model_adapter: ModelAdapter | None = None,
        model_gateway: PydanticAIModelGateway | None = None,
    ) -> None:
        self._model_adapter = model_adapter or DeterministicModelAdapter()
        self._model_gateway = model_gateway or _default_model_gateway()

    def generate_marketing_plan(
        self,
        software_source: SoftwareSource | str,
        user_interventions: tuple[UserIntervention, ...] | list[UserIntervention] | None = None,
    ) -> MarketingPlan:
        source = (
            SoftwareSource.from_url(software_source)
            if isinstance(software_source, str)
            else software_source
        )
        interventions = tuple(user_interventions or ())
        _validate_interventions(interventions)

        source_summary = self._model_adapter.summarize_source(source)
        provider_attempts: list[ProviderAttempt] = []

        research_result = self._model_gateway.run_task(
            ModelTaskRequest(TaskType.MARKET_RESEARCH, source, interventions),
            MarketResearch,
        )
        provider_attempts.extend(research_result.attempts)
        research = _typed_artifact(research_result.artifact, MarketResearch)

        campaign_result = self._model_gateway.run_task(
            ModelTaskRequest(
                TaskType.CAMPAIGN_ORCHESTRATION,
                source,
                interventions,
                {"market_research": research},
            ),
            CampaignOrchestration,
        )
        provider_attempts.extend(campaign_result.attempts)
        campaign = _typed_artifact(campaign_result.artifact, CampaignOrchestration)

        experiment_result = self._model_gateway.run_task(
            ModelTaskRequest(
                TaskType.MONETIZATION_EXPERIMENT,
                source,
                interventions,
                {"market_research": research, "campaign_orchestration": campaign},
            ),
            MonetizationExperiment,
        )
        provider_attempts.extend(experiment_result.attempts)
        experiment = _typed_artifact(experiment_result.artifact, MonetizationExperiment)

        content_result = self._model_gateway.run_task(
            ModelTaskRequest(
                TaskType.CONTENT_GENERATION,
                source,
                interventions,
                {"campaign_orchestration": campaign, "monetization_experiment": experiment},
            ),
            ContentGeneration,
        )
        provider_attempts.extend(content_result.attempts)
        content = _typed_artifact(content_result.artifact, ContentGeneration)

        stages = self._build_generation_stages(research, campaign, experiment, content)
        executive_summary = (
            f"{source.product_name} should monetize by focusing on paying users who need a clear, "
            f"low-friction reason to try the product, then converting that attention into product-led offers."
        )
        editable_markdown = self._build_editable_markdown(
            source_summary=source_summary,
            source=source,
            interventions=interventions,
            research=research,
            campaign=campaign,
            experiment=experiment,
            content=content,
            executive_summary=executive_summary,
        )

        return MarketingPlan(
            plan_id=_plan_id_for(source),
            software_source=source,
            generated_on=date.today().isoformat(),
            monetization_goal="Monetize the submitted software by attracting and converting paying customers.",
            executive_summary=executive_summary,
            generation_stages=stages,
            user_interventions=interventions,
            market_research=research,
            campaign_orchestration=campaign,
            monetization_experiment=experiment,
            content_generation=content,
            provider_attempts=tuple(provider_attempts),
            editable_markdown=editable_markdown,
        )

    def _build_market_research(
        self, source: SoftwareSource, interventions: tuple[UserIntervention, ...]
    ) -> MarketResearch:
        return _deterministic_market_research(source, interventions)

    def _build_campaign_orchestration(
        self,
        source: SoftwareSource,
        research: MarketResearch,
        interventions: tuple[UserIntervention, ...],
    ) -> CampaignOrchestration:
        return _deterministic_campaign_orchestration(source, research, interventions)

    def _build_content_generation(
        self,
        source: SoftwareSource,
        campaign: CampaignOrchestration,
        experiment: MonetizationExperiment,
        interventions: tuple[UserIntervention, ...],
    ) -> ContentGeneration:
        return _deterministic_content_generation(source, campaign, experiment, interventions)

    def _build_generation_stages(
        self,
        research: MarketResearch,
        campaign: CampaignOrchestration,
        experiment: MonetizationExperiment,
        content: ContentGeneration,
    ) -> tuple[GenerationStage, ...]:
        return (
            GenerationStage(
                name="Market Research",
                status=GenerationStageStatus.COMPLETE,
                summary=f"Identified {len(research.audience_segments)} paying audience segments and {len(research.channels)} channels.",
                intervention_prompt="Refine the target customer, channel priority, or competitive positioning.",
            ),
            GenerationStage(
                name="Campaign Orchestration",
                status=GenerationStageStatus.COMPLETE,
                summary=f"Created a {len(campaign.sequence)}-step campaign sequence with {len(campaign.required_materials)} required materials.",
                intervention_prompt="Adjust campaign timing, offer shape, or launch channel.",
            ),
            GenerationStage(
                name="Monetization Experiment",
                status=GenerationStageStatus.COMPLETE,
                summary=(
                    f"Ranked {len(experiment.ranked_recommendations)} campaign and offer recommendations "
                    "with conversion potential, CAC risk, and channel fit scores."
                ),
                intervention_prompt="Adjust offer shape, scoring assumptions, or the channel to prioritize.",
            ),
            GenerationStage(
                name="Content Generation",
                status=GenerationStageStatus.COMPLETE,
                summary=(
                    f"Generated {len(content.text_assets)} text assets, {len(content.image_briefs)} image briefs, "
                    f"and {len(content.video_briefs)} video briefs."
                ),
                intervention_prompt="Edit the tone, format, or creative direction for generated assets.",
            ),
        )

    def _build_editable_markdown(
        self,
        source_summary: str,
        source: SoftwareSource,
        interventions: tuple[UserIntervention, ...],
        research: MarketResearch,
        campaign: CampaignOrchestration,
        experiment: MonetizationExperiment,
        content: ContentGeneration,
        executive_summary: str,
    ) -> str:
        intervention_lines = (
            [f"- {item.stage_name}: {item.feedback}" for item in interventions]
            if interventions
            else ["- No user intervention supplied yet."]
        )
        lines = [
            f"# Marketing Plan for {source.product_name}",
            "",
            f"Source: {source.url}",
            f"Goal: Monetize the submitted software by attracting and converting paying customers.",
            "",
            "## Executive Summary",
            executive_summary,
            source_summary,
            "",
            "## User Intervention Notes",
            *intervention_lines,
            "",
            "## Market Research",
            "Audience segments:",
            *[f"- {item}" for item in research.audience_segments],
            "",
            "Competitive signals:",
            *[f"- {item}" for item in research.competitive_signals],
            "",
            "Channels:",
            *[f"- {item}" for item in research.channels],
            "",
            "Content patterns:",
            *[f"- {item}" for item in research.content_patterns],
            "",
            "## Campaign Orchestration",
            campaign.objective,
            "",
            "Sequence:",
            *[f"- {item}" for item in campaign.sequence],
            "",
            "Channel plan:",
            *[f"- {item}" for item in campaign.channel_plan],
            "",
            "Required materials:",
            *[f"- {item}" for item in campaign.required_materials],
            "",
            "## Monetization Experiment",
            "Ranked recommendations:",
            *[
                (
                    f"- #{item.rank}: {item.campaign_variant.name} + {item.offer_variant.name} "
                    f"(score {item.score.weighted_score}; conversion {item.score.conversion_potential}, "
                    f"CAC risk {item.score.cac_risk}, channel fit {item.score.channel_fit}). "
                    f"{item.score.rationale} Next: {item.next_action}"
                )
                for item in experiment.ranked_recommendations
            ],
            "",
            "## Content Generation",
            "Text assets:",
            *[f"- {item}" for item in content.text_assets],
            "",
            "Image briefs:",
            *[f"- {item}" for item in content.image_briefs],
            "",
            "Video briefs:",
            *[f"- {item}" for item in content.video_briefs],
        ]
        return "\n".join(lines)


def _default_model_gateway() -> PydanticAIModelGateway:
    if os.environ.get("CONTENT_AGENT_LIVE_MODELS", "").strip().lower() in {"1", "true", "yes"}:
        return PydanticAIModelGateway(provider_client=PydanticAIProviderClient())
    return PydanticAIModelGateway(provider_client=DeterministicModelDouble())


def _default_routes() -> dict[TaskType, LiveModelRoute]:
    openai = ProviderRoute(
        provider="openai",
        model=os.environ.get("CONTENT_AGENT_OPENAI_MODEL", "openai:gpt-4o-mini"),
    )
    gemini = ProviderRoute(
        provider="gemini",
        model=os.environ.get("CONTENT_AGENT_GEMINI_MODEL", "google-gla:gemini-1.5-flash"),
    )
    return {
        TaskType.MARKET_RESEARCH: LiveModelRoute(
            task_type=TaskType.MARKET_RESEARCH,
            providers=(gemini, openai),
            retry_budget=RetryBudget(attempts_per_provider=1),
        ),
        TaskType.CAMPAIGN_ORCHESTRATION: LiveModelRoute(
            task_type=TaskType.CAMPAIGN_ORCHESTRATION,
            providers=(openai, gemini),
            retry_budget=RetryBudget(attempts_per_provider=1),
        ),
        TaskType.MONETIZATION_EXPERIMENT: LiveModelRoute(
            task_type=TaskType.MONETIZATION_EXPERIMENT,
            providers=(openai, gemini),
            retry_budget=RetryBudget(attempts_per_provider=1),
        ),
        TaskType.CONTENT_GENERATION: LiveModelRoute(
            task_type=TaskType.CONTENT_GENERATION,
            providers=(gemini, openai),
            retry_budget=RetryBudget(attempts_per_provider=1),
        ),
    }


def _provider_attempt(
    request: ModelTaskRequest,
    provider_route: ProviderRoute,
    attempt: int,
    status: str,
    message: str,
) -> ProviderAttempt:
    return ProviderAttempt(
        task_type=request.task_type,
        provider=provider_route.provider,
        model=provider_route.model,
        attempt=attempt,
        status=status,
        message=message,
    )


def _system_prompt_for(task_type: TaskType) -> str:
    return (
        "You are the ContentAgent Marketing Agent backend. "
        "Return only a structured artifact matching the requested output schema. "
        "The goal is to monetize the submitted software. "
        f"Current task type: {task_type.value}."
    )


def _prompt_for(request: ModelTaskRequest) -> str:
    interventions = [
        {"stage_name": item.stage_name, "feedback": item.feedback}
        for item in request.user_interventions
    ]
    return "\n".join(
        [
            f"Software source URL: {request.software_source.url}",
            f"Software source kind: {request.software_source.kind.value}",
            f"Product name: {request.software_source.product_name}",
            f"Task type: {request.task_type.value}",
            f"User interventions: {interventions}",
            f"Validated prior stage inputs: {request.stage_inputs}",
            "Produce a monetization-focused artifact with concrete, ranked, and channel-aware recommendations.",
        ]
    )


def _coerce_stage_artifact(output_type: type[object], raw_artifact: object) -> object:
    if isinstance(raw_artifact, output_type):
        return raw_artifact
    if hasattr(raw_artifact, "model_dump"):
        raw_artifact = raw_artifact.model_dump()
    if not isinstance(raw_artifact, dict):
        raise ValueError(f"{output_type.__name__} artifact must be an object.")

    if output_type is MarketResearch:
        return MarketResearch(
            audience_segments=_raw_strings(raw_artifact, "audience_segments"),
            competitive_signals=_raw_strings(raw_artifact, "competitive_signals"),
            channels=_raw_strings(raw_artifact, "channels"),
            content_patterns=_raw_strings(raw_artifact, "content_patterns"),
        )
    if output_type is CampaignOrchestration:
        return CampaignOrchestration(
            objective=str(raw_artifact.get("objective", "")),
            sequence=_raw_strings(raw_artifact, "sequence"),
            channel_plan=_raw_strings(raw_artifact, "channel_plan"),
            required_materials=_raw_strings(raw_artifact, "required_materials"),
        )
    if output_type is ContentGeneration:
        return ContentGeneration(
            text_assets=_raw_strings(raw_artifact, "text_assets"),
            image_briefs=_raw_strings(raw_artifact, "image_briefs"),
            video_briefs=_raw_strings(raw_artifact, "video_briefs"),
        )
    if output_type is MonetizationExperiment:
        campaign_variants = tuple(
            _coerce_campaign_variant(item)
            for item in _raw_sequence(raw_artifact, "campaign_variants")
        )
        offer_variants = tuple(
            _coerce_offer_variant(item)
            for item in _raw_sequence(raw_artifact, "offer_variants")
        )
        recommendations = tuple(
            _coerce_ranked_recommendation(item)
            for item in _raw_sequence(raw_artifact, "ranked_recommendations")
        )
        return MonetizationExperiment(
            campaign_variants=campaign_variants,
            offer_variants=offer_variants,
            ranked_recommendations=recommendations,
        )
    raise ValueError(f"Unsupported stage artifact type {output_type!r}.")


def _coerce_campaign_variant(raw_variant: object) -> CampaignVariant:
    if isinstance(raw_variant, CampaignVariant):
        return raw_variant
    if hasattr(raw_variant, "model_dump"):
        raw_variant = raw_variant.model_dump()
    if not isinstance(raw_variant, dict):
        raise ValueError("CampaignVariant artifact must be an object.")
    return CampaignVariant(
        variant_id=str(raw_variant.get("variant_id", "")),
        name=str(raw_variant.get("name", "")),
        audience_segment=str(raw_variant.get("audience_segment", "")),
        channel=str(raw_variant.get("channel", "")),
        message_angle=str(raw_variant.get("message_angle", "")),
    )


def _coerce_offer_variant(raw_variant: object) -> OfferVariant:
    if isinstance(raw_variant, OfferVariant):
        return raw_variant
    if hasattr(raw_variant, "model_dump"):
        raw_variant = raw_variant.model_dump()
    if not isinstance(raw_variant, dict):
        raise ValueError("OfferVariant artifact must be an object.")
    return OfferVariant(
        variant_id=str(raw_variant.get("variant_id", "")),
        name=str(raw_variant.get("name", "")),
        pricing_angle=str(raw_variant.get("pricing_angle", "")),
        incentive=str(raw_variant.get("incentive", "")),
        call_to_action=str(raw_variant.get("call_to_action", "")),
    )


def _coerce_rubric_score(raw_score: object) -> RubricScore:
    if isinstance(raw_score, RubricScore):
        return raw_score
    if hasattr(raw_score, "model_dump"):
        raw_score = raw_score.model_dump()
    if not isinstance(raw_score, dict):
        raise ValueError("RubricScore artifact must be an object.")
    return RubricScore(
        conversion_potential=int(raw_score.get("conversion_potential", 0)),
        cac_risk=int(raw_score.get("cac_risk", 0)),
        channel_fit=int(raw_score.get("channel_fit", 0)),
        rationale=str(raw_score.get("rationale", "")),
    )


def _coerce_ranked_recommendation(raw_recommendation: object) -> RankedRecommendation:
    if isinstance(raw_recommendation, RankedRecommendation):
        return raw_recommendation
    if hasattr(raw_recommendation, "model_dump"):
        raw_recommendation = raw_recommendation.model_dump()
    if not isinstance(raw_recommendation, dict):
        raise ValueError("RankedRecommendation artifact must be an object.")
    return RankedRecommendation(
        rank=int(raw_recommendation.get("rank", 0)),
        campaign_variant=_coerce_campaign_variant(raw_recommendation.get("campaign_variant")),
        offer_variant=_coerce_offer_variant(raw_recommendation.get("offer_variant")),
        score=_coerce_rubric_score(raw_recommendation.get("score")),
        next_action=str(raw_recommendation.get("next_action", "")),
    )


def _typed_artifact(raw_artifact: object, artifact_type: type[Any]) -> Any:
    if not isinstance(raw_artifact, artifact_type):
        raise ModelRoutingError(f"Expected {artifact_type.__name__}, got {type(raw_artifact).__name__}.")
    return raw_artifact


def _require_stage_input(
    request: ModelTaskRequest,
    key: str,
    expected_type: type[Any],
) -> Any:
    value = request.stage_inputs.get(key)
    if not isinstance(value, expected_type):
        raise ProviderExecutionError(f"{request.task_type.value} requires validated {key}.")
    return value


def _deterministic_market_research(
    source: SoftwareSource,
    interventions: tuple[UserIntervention, ...],
) -> MarketResearch:
    product = source.product_name
    feedback_focus = _feedback_focus(interventions)
    return MarketResearch(
        audience_segments=(
            f"Founders and solo builders evaluating tools like {product}",
            f"Small teams with an urgent workflow that {product} can simplify",
            f"Technical buyers looking for proof that {product} saves time or creates revenue",
        ),
        competitive_signals=(
            "Position against manual spreadsheets, generic automation tools, and incumbent SaaS workflows.",
            "Lead with a concrete before-and-after workflow instead of broad productivity claims.",
            f"Use {feedback_focus} as a differentiator in customer-facing messaging.",
        ),
        channels=(
            "Founder communities and indie software forums",
            "LinkedIn posts aimed at operators and technical buyers",
            "Search-focused comparison pages and launch directories",
            "Short demo clips for social channels",
        ),
        content_patterns=(
            "Pain-point post that names the expensive workflow being replaced",
            "Product walkthrough showing the first valuable output in under one minute",
            "Comparison content that clarifies why paying is cheaper than staying manual",
            "Customer-style scenario with pricing and return-on-investment framing",
        ),
    )


def _deterministic_campaign_orchestration(
    source: SoftwareSource,
    research: MarketResearch,
    interventions: tuple[UserIntervention, ...],
) -> CampaignOrchestration:
    product = source.product_name
    feedback_focus = _feedback_focus(interventions)
    return CampaignOrchestration(
        objective=f"Turn qualified attention for {product} into paid trials or sales calls.",
        sequence=(
            "Week 1: validate positioning with audience-specific pain posts and direct feedback requests.",
            "Week 2: publish proof assets, comparisons, and a product walkthrough landing page.",
            "Week 3: retarget engaged prospects with offer-led posts and founder-led outreach.",
            "Week 4: convert with a limited beta, paid pilot, or annual-plan incentive.",
        ),
        channel_plan=tuple(
            f"{channel}: publish assets emphasizing {feedback_focus} and measurable commercial value."
            for channel in research.channels
        ),
        required_materials=(
            "Positioning brief",
            "Landing page copy",
            "Three short social post variants per audience segment",
            "One demo video outline",
            "One image or carousel brief for each main channel",
            "Offer and follow-up email sequence",
        ),
    )


def _deterministic_monetization_experiment(
    source: SoftwareSource,
    research: MarketResearch,
    campaign: CampaignOrchestration,
    interventions: tuple[UserIntervention, ...],
) -> MonetizationExperiment:
    product = source.product_name
    feedback_focus = _feedback_focus(interventions)
    channels = _pad_tuple(research.channels, "Primary channel")
    audiences = _pad_tuple(research.audience_segments, "Qualified buyer")

    campaign_variants = (
        CampaignVariant(
            variant_id="campaign-1",
            name="Proof-led paid pilot",
            audience_segment=audiences[2],
            channel=channels[1],
            message_angle=f"Show the revenue or time saved by using {product} before asking for a paid pilot.",
        ),
        CampaignVariant(
            variant_id="campaign-2",
            name="Founder community validation",
            audience_segment=audiences[0],
            channel=channels[0],
            message_angle=f"Invite builders to compare their current workflow against {product}.",
        ),
        CampaignVariant(
            variant_id="campaign-3",
            name="Search comparison capture",
            audience_segment=audiences[1],
            channel=channels[2],
            message_angle=f"Position {product} against the expensive manual alternatives buyers already know.",
        ),
    )
    offer_variants = (
        OfferVariant(
            variant_id="offer-1",
            name="Paid pilot with implementation review",
            pricing_angle="Time-boxed paid pilot tied to one measurable workflow outcome.",
            incentive=f"Includes a review focused on {feedback_focus}.",
            call_to_action="Book a paid pilot review.",
        ),
        OfferVariant(
            variant_id="offer-2",
            name="Beta annual discount",
            pricing_angle="Discounted annual plan for early qualified teams.",
            incentive="Lock in early pricing for one year.",
            call_to_action="Join the paid beta.",
        ),
        OfferVariant(
            variant_id="offer-3",
            name="Self-serve starter plan",
            pricing_angle="Low-friction monthly plan for users ready to try without a call.",
            incentive="Start with a template or guided first output.",
            call_to_action="Start the first paid workflow.",
        ),
    )
    ranked = (
        RankedRecommendation(
            rank=1,
            campaign_variant=campaign_variants[0],
            offer_variant=offer_variants[0],
            score=RubricScore(
                conversion_potential=5,
                cac_risk=2,
                channel_fit=5,
                rationale="Highest intent audience, strong proof requirement, and a bounded offer reduce buying friction.",
            ),
            next_action=f"Build the pilot landing section from: {campaign.objective}",
        ),
        RankedRecommendation(
            rank=2,
            campaign_variant=campaign_variants[1],
            offer_variant=offer_variants[1],
            score=RubricScore(
                conversion_potential=4,
                cac_risk=3,
                channel_fit=4,
                rationale="Good audience access and feedback density, with moderate CAC risk from lower buyer intent.",
            ),
            next_action="Publish three validation posts and invite qualified comments into the beta offer.",
        ),
        RankedRecommendation(
            rank=3,
            campaign_variant=campaign_variants[2],
            offer_variant=offer_variants[2],
            score=RubricScore(
                conversion_potential=3,
                cac_risk=4,
                channel_fit=4,
                rationale="Useful capture path, but search content takes longer to compound and has higher CAC risk.",
            ),
            next_action="Draft one comparison page and test a self-serve call to action.",
        ),
    )
    return MonetizationExperiment(
        campaign_variants=campaign_variants,
        offer_variants=offer_variants,
        ranked_recommendations=ranked,
    )


def _deterministic_content_generation(
    source: SoftwareSource,
    campaign: CampaignOrchestration,
    experiment: MonetizationExperiment,
    interventions: tuple[UserIntervention, ...],
) -> ContentGeneration:
    product = source.product_name
    feedback_focus = _feedback_focus(interventions)
    top_recommendation = experiment.ranked_recommendations[0]
    return ContentGeneration(
        text_assets=(
            f"Headline: Monetize your workflow faster with {product}",
            f"Social post: The costly part is not the task. It is repeating it without a system. {product} turns that into a repeatable output.",
            f"Email opener: You are likely losing time or revenue in the workflow {product} was built to improve.",
            f"Call to action: {top_recommendation.offer_variant.call_to_action} focused on {feedback_focus}.",
        ),
        image_briefs=(
            f"Before-and-after workflow diagram showing the manual path replaced by {product}.",
            f"Carousel showing {top_recommendation.campaign_variant.name}, proof point, offer, and next action for {product}.",
        ),
        video_briefs=(
            f"45-second product walkthrough: problem, first action, generated result, paid next step for {product}.",
            f"Founder explainer: why {product} exists, who pays for it, and what outcome they should expect.",
        ),
    )


def _sanitize_url(raw_url: str) -> str:
    candidate = raw_url.strip()
    if not candidate:
        raise ValueError("SoftwareSource URL is required.")
    parsed = urlparse(candidate)
    if not parsed.scheme:
        candidate = f"https://{candidate}"
    return candidate


def _title_from_slug(slug: str) -> str:
    clean = slug.strip().replace("_", "-")
    words = [word for word in clean.split("-") if word]
    if not words:
        return "Submitted Software"
    return " ".join(word.capitalize() for word in words)


def _validate_interventions(interventions: tuple[UserIntervention, ...]) -> None:
    for intervention in interventions:
        if not intervention.stage_name.strip():
            raise ValueError("UserIntervention stage_name is required.")
        if not intervention.feedback.strip():
            raise ValueError("UserIntervention feedback is required.")


def _feedback_focus(interventions: tuple[UserIntervention, ...]) -> str:
    if not interventions:
        return "the fastest path from first attention to paid conversion"
    latest = interventions[-1].feedback.strip()
    return latest[:120]


def _non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _non_empty_strings(values: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise ValueError(f"{field_name} must be a non-empty sequence of strings.")
    cleaned = tuple(_non_empty_string(value, field_name) for value in values)
    if not cleaned:
        raise ValueError(f"{field_name} must contain at least one item.")
    return cleaned


def _non_empty_items(values: object, expected_type: type[Any], field_name: str) -> tuple[Any, ...]:
    if not isinstance(values, (tuple, list)):
        raise ValueError(f"{field_name} must be a non-empty sequence.")
    cleaned = tuple(values)
    if not cleaned:
        raise ValueError(f"{field_name} must contain at least one item.")
    if not all(isinstance(item, expected_type) for item in cleaned):
        raise ValueError(f"{field_name} must contain only {expected_type.__name__} items.")
    return cleaned


def _raw_sequence(raw: dict[str, object], field_name: str) -> tuple[object, ...]:
    value = raw.get(field_name, ())
    if not isinstance(value, (tuple, list)):
        raise ValueError(f"{field_name} must be a sequence.")
    return tuple(value)


def _raw_strings(raw: dict[str, object], field_name: str) -> tuple[str, ...]:
    return _non_empty_strings(_raw_sequence(raw, field_name), field_name)


def _pad_tuple(values: tuple[str, ...], fallback: str) -> tuple[str, str, str]:
    padded = tuple(values) + (fallback, fallback, fallback)
    return padded[0], padded[1], padded[2]


def _plan_id_for(source: SoftwareSource) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in source.product_name)
    normalized = "-".join(part for part in normalized.split("-") if part)
    return f"marketing-plan-{normalized or 'submitted-software'}"
