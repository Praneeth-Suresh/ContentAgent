import unittest

from src.marketing_agent import (
    DeterministicModelDouble,
    GenerationStageStatus,
    LiveModelRoute,
    MarketResearch,
    MarketingAgent,
    ModelRoutingError,
    PydanticAIModelGateway,
    ProviderRoute,
    RetryBudget,
    SoftwareSource,
    SoftwareSourceKind,
    TaskType,
    UserIntervention,
)


class MarketingAgentCoreTests(unittest.TestCase):
    def test_valid_github_source_generates_complete_marketing_plan(self):
        agent = MarketingAgent()

        plan = agent.generate_marketing_plan("https://github.com/acme/revenue-dashboard")

        self.assertEqual(plan.software_source.kind, SoftwareSourceKind.GITHUB_REPOSITORY)
        self.assertEqual(plan.software_source.product_name, "Revenue Dashboard")
        self.assertIn("Monetize", plan.monetization_goal)
        self.assertEqual(
            [stage.name for stage in plan.generation_stages],
            [
                "Market Research",
                "Campaign Orchestration",
                "Monetization Experiment",
                "Content Generation",
            ],
        )
        self.assertTrue(
            all(stage.status == GenerationStageStatus.COMPLETE for stage in plan.generation_stages)
        )
        self.assertGreaterEqual(len(plan.market_research.audience_segments), 3)
        self.assertGreaterEqual(len(plan.campaign_orchestration.sequence), 4)
        self.assertGreaterEqual(len(plan.monetization_experiment.ranked_recommendations), 3)
        self.assertGreaterEqual(len(plan.content_generation.text_assets), 4)
        self.assertEqual(
            [item.rank for item in plan.monetization_experiment.ranked_recommendations],
            [1, 2, 3],
        )
        self.assertGreater(
            plan.monetization_experiment.ranked_recommendations[0].score.weighted_score,
            plan.monetization_experiment.ranked_recommendations[-1].score.weighted_score,
        )
        self.assertIn("## Market Research", plan.editable_markdown)
        self.assertIn("## Campaign Orchestration", plan.editable_markdown)
        self.assertIn("## Monetization Experiment", plan.editable_markdown)
        self.assertIn("## Content Generation", plan.editable_markdown)

    def test_valid_website_source_generates_website_plan(self):
        source = SoftwareSource.from_url("https://example-saas.com")

        self.assertEqual(source.kind, SoftwareSourceKind.WEBSITE)
        self.assertEqual(source.product_name, "Example Saas")

    def test_user_intervention_is_incorporated_into_plan(self):
        agent = MarketingAgent()
        intervention = UserIntervention(
            stage_name="Campaign Orchestration",
            feedback="Focus on paid pilots for agencies before self-serve subscriptions.",
        )

        plan = agent.generate_marketing_plan(
            "github.com/acme/content-agent",
            user_interventions=[intervention],
        )

        self.assertEqual(plan.user_interventions, (intervention,))
        self.assertIn(intervention.feedback, plan.editable_markdown)
        self.assertTrue(
            any(intervention.feedback in item for item in plan.campaign_orchestration.channel_plan)
        )

    def test_invalid_software_source_is_rejected(self):
        agent = MarketingAgent()

        with self.assertRaisesRegex(ValueError, "SoftwareSource"):
            agent.generate_marketing_plan("not a valid url")

    def test_incomplete_github_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "owner and repository"):
            SoftwareSource.from_url("https://github.com/acme")

    def test_empty_user_intervention_is_rejected(self):
        agent = MarketingAgent()

        with self.assertRaisesRegex(ValueError, "feedback"):
            agent.generate_marketing_plan(
                "https://example.com",
                user_interventions=[UserIntervention(stage_name="Market Research", feedback=" ")],
            )

    def test_market_research_route_falls_back_after_validation_failure(self):
        invalid_research = {
            "audience_segments": [],
            "competitive_signals": ["OpenAI returned an incomplete artifact."],
            "channels": ["Founder communities"],
            "content_patterns": ["Demo post"],
        }
        valid_research = MarketResearch(
            audience_segments=("Fallback buyers with budget authority",),
            competitive_signals=("Gemini returned a complete validated artifact.",),
            channels=("Founder communities",),
            content_patterns=("Offer-led demo post",),
        )
        gateway = PydanticAIModelGateway(
            routes={
                TaskType.MARKET_RESEARCH: LiveModelRoute(
                    task_type=TaskType.MARKET_RESEARCH,
                    providers=(
                        ProviderRoute(provider="openai", model="test-openai"),
                        ProviderRoute(provider="gemini", model="test-gemini"),
                    ),
                    retry_budget=RetryBudget(attempts_per_provider=1),
                )
            },
            provider_client=ScriptedProviderClient(
                {
                    (TaskType.MARKET_RESEARCH, "openai"): [invalid_research],
                    (TaskType.MARKET_RESEARCH, "gemini"): [valid_research],
                }
            ),
        )
        agent = MarketingAgent(model_gateway=gateway)

        plan = agent.generate_marketing_plan("https://github.com/acme/revenue-dashboard")

        research_attempts = [
            attempt
            for attempt in plan.provider_attempts
            if attempt.task_type == TaskType.MARKET_RESEARCH
        ]
        self.assertEqual([attempt.provider for attempt in research_attempts], ["openai", "gemini"])
        self.assertEqual(research_attempts[0].status, "validation_error")
        self.assertEqual(research_attempts[1].status, "success")
        self.assertEqual(plan.market_research, valid_research)
        self.assertIn("Fallback buyers with budget authority", plan.editable_markdown)

    def test_route_failure_is_typed_when_retry_budget_is_exhausted(self):
        invalid_research = {
            "audience_segments": [],
            "competitive_signals": [],
            "channels": [],
            "content_patterns": [],
        }
        gateway = PydanticAIModelGateway(
            routes={
                TaskType.MARKET_RESEARCH: LiveModelRoute(
                    task_type=TaskType.MARKET_RESEARCH,
                    providers=(
                        ProviderRoute(provider="openai", model="test-openai"),
                        ProviderRoute(provider="gemini", model="test-gemini"),
                    ),
                    retry_budget=RetryBudget(attempts_per_provider=1),
                )
            },
            provider_client=ScriptedProviderClient(
                {
                    (TaskType.MARKET_RESEARCH, "openai"): [invalid_research],
                    (TaskType.MARKET_RESEARCH, "gemini"): [invalid_research],
                }
            ),
        )
        agent = MarketingAgent(model_gateway=gateway)

        with self.assertRaisesRegex(ModelRoutingError, "market_research"):
            agent.generate_marketing_plan("https://github.com/acme/revenue-dashboard")


class ScriptedProviderClient:
    def __init__(self, scripted_results):
        self.scripted_results = {
            key: list(values)
            for key, values in scripted_results.items()
        }
        self.fallback = DeterministicModelDouble()

    def complete(self, provider_route, request, output_type):
        key = (request.task_type, provider_route.provider)
        values = self.scripted_results.get(key)
        if values:
            return values.pop(0)
        return self.fallback.complete(provider_route, request, output_type)


if __name__ == "__main__":
    unittest.main()
