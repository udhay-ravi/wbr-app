import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

import src.system_design_agent as system_design_agent


def test_questions_include_repo_and_region():
    questions = system_design_agent.get_questions("repo deployer")
    ids = [q["id"] for q in questions]
    assert "repo_url" in ids
    assert "region" in ids


def test_build_returns_digitalocean_design():
    recommendation = system_design_agent.build_design_options(
        "analytics app",
        {
            "repo_url": "https://github.com/octocat/Hello-World",
            "region": "nyc3",
            "scale": "medium",
        },
    )

    assert recommendation["target"]["provider"] == "digitalocean"
    assert len(recommendation["designs"]) == 1
    components = recommendation["designs"][0]["components"]
    assert any("DigitalOcean" in component for component in components)


def test_invalid_repo_url_raises_value_error():
    try:
        system_design_agent.build_design_options("app", {"repo_url": "https://example.com/a/b"})
    except ValueError as error:
        assert "GitHub" in str(error)
    else:
        raise AssertionError("Expected ValueError for invalid repo")


def test_doctl_commands_include_auth_and_cluster_create():
    commands = system_design_agent.build_doctl_commands("org/repo", "nyc3")
    assert commands[0].startswith("doctl auth init")
    assert any("kubernetes cluster create" in command for command in commands)
