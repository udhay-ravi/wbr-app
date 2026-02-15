import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

import src.system_design_agent as system_design_agent


def test_questions_include_dynamic_domain_clarifications():
    questions = system_design_agent.get_questions("ecommerce app with checkout")
    ids = [q["id"] for q in questions]
    assert "app_idea" in ids
    assert "domain_priority" in ids
    assert "domain_priority_2" in ids


def test_build_returns_three_levels_with_user_actions_and_traffic_flow():
    recommendation = system_design_agent.build_design_options(
        "food delivery app",
        {
            "cloud_provider": "aws",
            "target_users": "200k-5m users",
            "peak_rps": "1k-10k",
            "regions": "active-active",
        },
    )

    assert len(recommendation["designs"]) == 3
    levels = [d["level"] for d in recommendation["designs"]]
    assert levels == [
        "Simple design",
        "Complex design (Medium scale)",
        "Highly complex design",
    ]
    assert all(recommendation["designs"][i]["user_actions"] for i in range(3))
    assert all(recommendation["designs"][i]["traffic_flow"] for i in range(3))
    assert any("Amazon" in component for component in recommendation["designs"][1]["components"])


def test_recommendation_contains_required_answers_and_domain_specific_components():
    recommendation = system_design_agent.build_design_options(
        "ecommerce marketplace with checkout",
        {"cloud_provider": "aws"},
    )

    assert "required_answers" in recommendation
    assert "cloud_provider" in recommendation["required_answers"]
    assert any(
        "Checkout Service" in component
        for component in recommendation["designs"][0]["components"]
    )
