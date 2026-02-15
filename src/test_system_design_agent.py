import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

import src.system_design_agent as system_design_agent


def test_questions_present():
    questions = system_design_agent.get_questions()
    assert len(questions) >= 5
    assert questions[0]["id"] == "app_type"


def test_build_options_returns_three_choices_with_provider_details():
    options = system_design_agent.build_design_options({
        "cloud_provider": "aws",
        "monthly_active_users": "1m-10m",
        "peak_rps": "1k-10k",
        "regions": "active-active",
    })
    assert len(options) == 3
    assert any("Amazon" in component for component in options[0]["components"])
    assert "Global DNS" in options[2]["diagram"]
