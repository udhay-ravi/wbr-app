from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests


@dataclass(frozen=True)
class ProviderServices:
    ingress: str
    compute: str
    database: str
    cache: str
    queue: str
    object_store: str
    observability: str
    ci_cd: str


DIGITALOCEAN = ProviderServices(
    ingress="DigitalOcean Load Balancer + Cloud Firewall",
    compute="DigitalOcean Kubernetes (DOKS)",
    database="DigitalOcean Managed PostgreSQL",
    cache="DigitalOcean Managed Redis",
    queue="NATS or RabbitMQ on Kubernetes",
    object_store="DigitalOcean Spaces",
    observability="DigitalOcean Monitoring + Prometheus/Grafana",
    ci_cd="GitHub Actions + doctl",
)


def get_questions(app_idea: str | None = None) -> List[dict]:
    idea = app_idea or ""
    return [
        {"id": "repo_url", "label": "GitHub repository URL", "type": "text", "placeholder": "https://github.com/org/repo"},
        {
            "id": "environment",
            "label": "Deployment environment",
            "options": ["dev", "staging", "production"],
        },
        {
            "id": "scale",
            "label": "Expected scale in 12 months",
            "options": ["small", "medium", "large"],
        },
        {
            "id": "data_needs",
            "label": "Primary data profile",
            "options": ["read-heavy", "write-heavy", "balanced"],
        },
        {
            "id": "region",
            "label": "Preferred DigitalOcean region",
            "options": ["nyc1", "nyc3", "sfo3", "ams3", "blr1", "sgp1"],
        },
        {
            "id": "app_idea",
            "label": "App description",
            "type": "text",
            "placeholder": idea or "Example: SaaS analytics app",
        },
    ]


def _parse_github_repo(repo_url: str) -> Tuple[str, str]:
    parsed = urlparse(repo_url.strip())
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc not in {"github.com", "www.github.com"} or len(parts) < 2:
        raise ValueError("repo_url must be a valid GitHub repository URL")
    return parts[0], parts[1].removesuffix(".git")


def _fetch_repo_metadata(owner: str, repo: str) -> Dict[str, str]:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        resp = requests.get(api, timeout=8)
    except requests.RequestException:
        return {"visibility": "unknown", "default_branch": "main", "language": "unknown"}

    if resp.status_code != 200:
        return {"visibility": "unknown", "default_branch": "main", "language": "unknown"}

    payload = resp.json()
    return {
        "visibility": "private" if payload.get("private") else "public",
        "default_branch": payload.get("default_branch", "main"),
        "language": payload.get("language") or "unknown",
    }


def build_design_options(app_idea: str, answers: Dict[str, str]) -> Dict[str, object]:
    repo_url = answers.get("repo_url", "")
    owner, repo = _parse_github_repo(repo_url)
    metadata = _fetch_repo_metadata(owner, repo)

    services = DIGITALOCEAN
    scale = answers.get("scale", "medium")
    region = answers.get("region", "nyc3")
    env = answers.get("environment", "staging")

    base_components = [
        f"GitHub Repo ({owner}/{repo})",
        services.ci_cd,
        services.ingress,
        services.compute,
        services.database,
        services.cache,
        services.object_store,
        services.observability,
    ]

    node_sizes = {
        "small": "2x s-2vcpu-4gb worker nodes",
        "medium": "3x s-4vcpu-8gb worker nodes",
        "large": "6x s-8vcpu-16gb worker nodes across 3 AZs",
    }

    diagram = (
        "Developer -> GitHub Push -> GitHub Actions\n"
        "GitHub Actions -> Container Registry -> doctl deploy\n"
        "Internet Users -> DO Firewall/LB -> DOKS Ingress -> Web/API Pods\n"
        "Web/API Pods -> Managed PostgreSQL + Managed Redis\n"
        "Web/API Pods -> Spaces (assets/backups)\n"
        "Cluster + DB metrics -> DO Monitoring / Prometheus"
    )

    deployment_steps = [
        "User connects GitHub repository URL in the app.",
        "App inspects repository metadata and proposes DigitalOcean architecture.",
        "User provides a DigitalOcean API token (doctl auth token).",
        "Deploy button triggers backend deployment workflow using doctl.",
    ]

    return {
        "app_idea": app_idea,
        "repository": {"owner": owner, "repo": repo, "url": repo_url, **metadata},
        "target": {"provider": "digitalocean", "region": region, "environment": env},
        "designs": [
            {
                "level": "DigitalOcean production baseline",
                "goal": f"Deploy {app_idea or repo} from GitHub to DigitalOcean with one-click automation.",
                "components": base_components,
                "diagram": diagram,
                "user_flow": deployment_steps,
                "sizing": node_sizes.get(scale, node_sizes["medium"]),
                "notes": [
                    f"Repository visibility: {metadata['visibility']}.",
                    f"Default branch: {metadata['default_branch']}.",
                    "Store DO token in backend session only; never persist plaintext token.",
                ],
            }
        ],
    }


def build_doctl_commands(repo_full_name: str, region: str) -> List[str]:
    return [
        "doctl auth init --access-token $DIGITALOCEAN_ACCESS_TOKEN",
        "doctl kubernetes cluster create app-cluster --region " + region + " --count 3 --size s-4vcpu-8gb",
        "doctl kubernetes cluster kubeconfig save app-cluster",
        "kubectl create namespace app-prod",
        "kubectl -n app-prod apply -f k8s/deployment.yaml",
        "kubectl -n app-prod apply -f k8s/service.yaml",
        f"echo 'Configure GitHub Actions for {repo_full_name} with DIGITALOCEAN_ACCESS_TOKEN secret'",
    ]
