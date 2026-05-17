"""Public boundary for the Marketing Agent bounded context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Protocol
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


@dataclass(frozen=True)
class CampaignOrchestration:
    """Campaign structure and material plan for monetization."""

    objective: str
    sequence: tuple[str, ...]
    channel_plan: tuple[str, ...]
    required_materials: tuple[str, ...]


@dataclass(frozen=True)
class ContentGeneration:
    """Multimodal campaign assets generated from the campaign plan."""

    text_assets: tuple[str, ...]
    image_briefs: tuple[str, ...]
    video_briefs: tuple[str, ...]


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
    content_generation: ContentGeneration
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
            "content_generation": {
                "text_assets": list(self.content_generation.text_assets),
                "image_briefs": list(self.content_generation.image_briefs),
                "video_briefs": list(self.content_generation.video_briefs),
            },
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

    def __init__(self, model_adapter: ModelAdapter | None = None) -> None:
        self._model_adapter = model_adapter or DeterministicModelAdapter()

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
        research = self._build_market_research(source, interventions)
        campaign = self._build_campaign_orchestration(source, research, interventions)
        content = self._build_content_generation(source, campaign, interventions)
        stages = self._build_generation_stages(research, campaign, content)
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
            content_generation=content,
            editable_markdown=editable_markdown,
        )

    def _build_market_research(
        self, source: SoftwareSource, interventions: tuple[UserIntervention, ...]
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

    def _build_campaign_orchestration(
        self,
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

    def _build_content_generation(
        self,
        source: SoftwareSource,
        campaign: CampaignOrchestration,
        interventions: tuple[UserIntervention, ...],
    ) -> ContentGeneration:
        product = source.product_name
        feedback_focus = _feedback_focus(interventions)
        return ContentGeneration(
            text_assets=(
                f"Headline: Monetize your workflow faster with {product}",
                f"Social post: The costly part is not the task. It is repeating it without a system. {product} turns that into a repeatable output.",
                f"Email opener: You are likely losing time or revenue in the workflow {product} was built to improve.",
                f"Call to action: Start with a paid pilot focused on {feedback_focus}.",
            ),
            image_briefs=(
                f"Before-and-after workflow diagram showing the manual path replaced by {product}.",
                f"Carousel showing audience pain, proof point, feature moment, and monetization offer for {product}.",
            ),
            video_briefs=(
                f"45-second product walkthrough: problem, first action, generated result, paid next step for {product}.",
                f"Founder explainer: why {product} exists, who pays for it, and what outcome they should expect.",
            ),
        )

    def _build_generation_stages(
        self,
        research: MarketResearch,
        campaign: CampaignOrchestration,
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


def _plan_id_for(source: SoftwareSource) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in source.product_name)
    normalized = "-".join(part for part in normalized.split("-") if part)
    return f"marketing-plan-{normalized or 'submitted-software'}"
