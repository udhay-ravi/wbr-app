from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


QUESTIONS = [
    {
        "id": "app_type",
        "label": "What type of application are you designing?",
        "options": ["ecommerce", "saas", "streaming", "iot", "internal_tool"],
    },
    {
        "id": "cloud_provider",
        "label": "Which cloud provider should the design target?",
        "options": ["aws", "azure", "gcp"],
    },
    {
        "id": "monthly_active_users",
        "label": "How many monthly active users (MAU) do you expect?",
        "options": ["<100k", "100k-1m", "1m-10m", ">10m"],
    },
    {
        "id": "peak_rps",
        "label": "What is the expected peak requests per second (RPS)?",
        "options": ["<100", "100-1k", "1k-10k", ">10k"],
    },
    {
        "id": "consistency",
        "label": "What consistency profile do you need?",
        "options": ["strong", "eventual", "mixed"],
    },
    {
        "id": "regions",
        "label": "How many regions should be active?",
        "options": ["single", "active-passive", "active-active"],
    },
    {
        "id": "compliance",
        "label": "Do you have compliance constraints?",
        "options": ["none", "pci", "hipaa", "gdpr"],
    },
]


@dataclass
class ProviderServices:
    lb: str
    k8s: str
    database: str
    cache: str
    queue: str
    object_store: str
    observability: str
    waf: str


PROVIDER_MAP: Dict[str, ProviderServices] = {
    "aws": ProviderServices(
        lb="Application Load Balancer",
        k8s="Amazon EKS",
        database="Amazon Aurora",
        cache="Amazon ElastiCache (Redis)",
        queue="Amazon SQS",
        object_store="Amazon S3",
        observability="Amazon CloudWatch + AWS X-Ray",
        waf="AWS WAF",
    ),
    "azure": ProviderServices(
        lb="Azure Application Gateway",
        k8s="Azure Kubernetes Service (AKS)",
        database="Azure Database for PostgreSQL",
        cache="Azure Cache for Redis",
        queue="Azure Service Bus",
        object_store="Azure Blob Storage",
        observability="Azure Monitor + Application Insights",
        waf="Azure Web Application Firewall",
    ),
    "gcp": ProviderServices(
        lb="Cloud Load Balancing",
        k8s="Google Kubernetes Engine (GKE)",
        database="Cloud SQL (PostgreSQL)",
        cache="Memorystore (Redis)",
        queue="Pub/Sub",
        object_store="Cloud Storage",
        observability="Cloud Monitoring + Cloud Trace",
        waf="Cloud Armor",
    ),
}


def get_questions() -> List[dict]:
    return QUESTIONS


def _scale_tier(answers: Dict[str, str]) -> str:
    mau = answers.get("monthly_active_users", "<100k")
    rps = answers.get("peak_rps", "<100")
    if mau == ">10m" or rps == ">10k":
        return "planet"
    if mau == "1m-10m" or rps == "1k-10k":
        return "hyper"
    if mau == "100k-1m" or rps == "100-1k":
        return "growth"
    return "starter"


def build_design_options(answers: Dict[str, str]) -> List[dict]:
    provider = answers.get("cloud_provider", "aws")
    services = PROVIDER_MAP.get(provider, PROVIDER_MAP["aws"])
    tier = _scale_tier(answers)

    options = [
        _base_option(answers, services, tier),
        _event_driven_option(answers, services, tier),
        _global_option(answers, services, tier),
    ]
    return options


def _base_option(answers: Dict[str, str], services: ProviderServices, tier: str) -> dict:
    return {
        "name": "Modular Monolith + Managed Data",
        "best_for": "Fast MVPs and small teams that still need strong foundations.",
        "tradeoffs": [
            "Simpler operational model and lower costs.",
            "Vertical scalability limits sooner than distributed services.",
        ],
        "components": [
            services.waf,
            services.lb,
            "App Service (single deployable)",
            services.database,
            services.cache,
            services.object_store,
            services.observability,
        ],
        "diagram": _diagram(services, multi_region=answers.get("regions") != "single"),
        "sizing_notes": _sizing(tier, "base"),
    }


def _event_driven_option(answers: Dict[str, str], services: ProviderServices, tier: str) -> dict:
    return {
        "name": "Microservices + Event-Driven Backbone",
        "best_for": "High change velocity domains like ecommerce, SaaS platforms, and IoT ingestion.",
        "tradeoffs": [
            "Independent service scaling and deployment.",
            "Higher complexity in observability and data consistency.",
        ],
        "components": [
            services.waf,
            services.lb,
            services.k8s,
            services.queue,
            services.database,
            services.cache,
            services.object_store,
            services.observability,
        ],
        "diagram": _diagram(services, event_driven=True, multi_region=answers.get("regions") == "active-active"),
        "sizing_notes": _sizing(tier, "event"),
    }


def _global_option(answers: Dict[str, str], services: ProviderServices, tier: str) -> dict:
    return {
        "name": "Globally Distributed + Read Locality",
        "best_for": "Large user bases requiring low latency and resilient multi-region operations.",
        "tradeoffs": [
            "Improves availability and user latency worldwide.",
            "Needs disciplined data partitioning and failover testing.",
        ],
        "components": [
            "Global DNS / Traffic Manager",
            services.waf,
            services.lb,
            services.k8s,
            f"Primary {services.database}",
            f"Read replicas of {services.database}",
            services.cache,
            services.queue,
            services.observability,
        ],
        "diagram": _diagram(services, global_mode=True),
        "sizing_notes": _sizing(tier, "global"),
    }


def _diagram(
    services: ProviderServices,
    event_driven: bool = False,
    multi_region: bool = False,
    global_mode: bool = False,
) -> str:
    if global_mode:
        return (
            "Users\n"
            "  |\n"
            "Global DNS / Traffic Manager\n"
            "  |\n"
            f"{services.waf} -> {services.lb} -> {services.k8s}\n"
            "  |               |\n"
            f"Primary {services.database}   Read Replicas\n"
            f"  |               |\n{services.cache}      {services.queue}\n"
        )

    if event_driven:
        secondary = "\n(Active secondary region ready)" if multi_region else ""
        return (
            "Users\n"
            f"  |\n{services.waf}\n"
            f"  |\n{services.lb}\n"
            f"  |\n{services.k8s} (multiple services)\n"
            f"  |\\\n  | \\--> {services.queue} -> Async workers\n"
            f"  |----> {services.database}\n"
            f"  |----> {services.cache}\n"
            f"  |----> {services.object_store}{secondary}\n"
        )

    replica = "\nReplica region (warm standby)" if multi_region else ""
    return (
        "Users\n"
        f"  |\n{services.waf} -> {services.lb} -> App Service\n"
        f"  |\n{services.database} <-> {services.cache}\n"
        f"  |\n{services.object_store}\n"
        f"  |\n{services.observability}{replica}\n"
    )


def _sizing(tier: str, architecture: str) -> List[str]:
    profiles = {
        "starter": "2-3 app nodes, single primary DB, cache optional",
        "growth": "4-8 app nodes, DB read replica, mandatory cache",
        "hyper": "12-30 app nodes, sharded data model, queue buffering",
        "planet": "50+ app nodes per region, active-active regions, automated failover",
    }

    notes = [f"Scale profile: {profiles[tier]}"]
    if architecture == "event":
        notes.append("Adopt idempotent consumers and dead-letter queues.")
    elif architecture == "global":
        notes.append("Use region-aware routing and clear write ownership boundaries.")
    else:
        notes.append("Keep service boundaries modular to ease migration to microservices later.")
    return notes
