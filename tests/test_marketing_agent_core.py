import unittest

from src.marketing_agent import (
    GenerationStageStatus,
    MarketingAgent,
    SoftwareSource,
    SoftwareSourceKind,
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
            ["Market Research", "Campaign Orchestration", "Content Generation"],
        )
        self.assertTrue(
            all(stage.status == GenerationStageStatus.COMPLETE for stage in plan.generation_stages)
        )
        self.assertGreaterEqual(len(plan.market_research.audience_segments), 3)
        self.assertGreaterEqual(len(plan.campaign_orchestration.sequence), 4)
        self.assertGreaterEqual(len(plan.content_generation.text_assets), 4)
        self.assertIn("## Market Research", plan.editable_markdown)
        self.assertIn("## Campaign Orchestration", plan.editable_markdown)
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


if __name__ == "__main__":
    unittest.main()
