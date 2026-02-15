from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProviderServices:
    lb: str
    compute: str
    database: str
    cache: str
    queue: str
    object_store: str
    observability: str
    waf: str
    dns: str


PROVIDER_MAP: Dict[str, ProviderServices] = {
    "aws": ProviderServices(
        lb="Application Load Balancer",
        compute="Amazon EKS",
        database="Amazon Aurora (PostgreSQL)",
        cache="Amazon ElastiCache (Redis)",
        queue="Amazon SQS + SNS",
        object_store="Amazon S3",
        observability="CloudWatch + X-Ray",
        waf="AWS WAF",
        dns="Amazon Route 53",
    ),
    "azure": ProviderServices(
        lb="Azure Application Gateway",
        compute="Azure Kubernetes Service (AKS)",
        database="Azure Database for PostgreSQL",
        cache="Azure Cache for Redis",
        queue="Azure Service Bus",
        object_store="Azure Blob Storage",
        observability="Azure Monitor + Application Insights",
        waf="Azure WAF",
        dns="Azure Traffic Manager",
    ),
    "gcp": ProviderServices(
        lb="Cloud Load Balancing",
        compute="Google Kubernetes Engine (GKE)",
        database="Cloud SQL (PostgreSQL)",
        cache="Memorystore (Redis)",
        queue="Pub/Sub",
        object_store="Cloud Storage",
        observability="Cloud Monitoring + Cloud Trace",
        waf="Cloud Armor",
        dns="Cloud DNS",
    ),
}


BASE_QUESTIONS: List[dict] = [
    {
        "id": "cloud_provider",
        "label": "Which cloud provider should be used?",
        "options": ["aws", "azure", "gcp"],
    },
    {
        "id": "target_users",
        "label": "Expected user scale?",
        "options": ["<10k users", "10k-200k users", "200k-5m users", ">5m users"],
    },
    {
        "id": "peak_rps",
        "label": "Peak requests per second (RPS)?",
        "options": ["<100", "100-1k", "1k-10k", ">10k"],
    },
    {
        "id": "data_profile",
        "label": "Primary workload profile?",
        "options": ["read-heavy", "write-heavy", "balanced", "event-streaming"],
    },
    {
        "id": "consistency",
        "label": "Consistency expectations?",
        "options": ["strong", "eventual", "mixed"],
    },
    {
        "id": "regions",
        "label": "Multi-region strategy?",
        "options": ["single-region", "active-passive", "active-active"],
    },
    {
        "id": "compliance",
        "label": "Compliance constraints?",
        "options": ["none", "pci", "hipaa", "gdpr"],
    },
]


DOMAIN_HINTS = {
    "ecommerce": [
        "Do you need inventory reservation during checkout?",
        "Should recommendation/search be real-time personalized?",
    ],
    "saas": [
        "Do you need tenant-level data isolation?",
        "Should billing events be processed asynchronously?",
    ],
    "stream": [
        "Should live playback support sub-second latency?",
        "Is transcoding done near-real-time or batch?",
    ],
    "iot": [
        "Should device ingestion tolerate bursts and offline replay?",
        "Do you need time-series optimized storage?",
    ],
}


def infer_domain(app_idea: str) -> str:
    idea = (app_idea or "").lower()
    if any(word in idea for word in ["shop", "cart", "checkout", "order", "marketplace"]):
        return "ecommerce"
    if any(word in idea for word in ["stream", "video", "music", "realtime content"]):
        return "stream"
    if any(word in idea for word in ["device", "sensor", "telemetry", "iot"]):
        return "iot"
    return "saas"


def get_questions(app_idea: str | None = None) -> List[dict]:
    app_idea = app_idea or ""
    domain = infer_domain(app_idea)
    hints = DOMAIN_HINTS.get(domain, DOMAIN_HINTS["saas"])
    extra = {
        "id": "domain_priority",
        "label": f"{hints[0]}",
        "options": ["yes", "no", "not-sure"],
    }
    extra_2 = {
        "id": "domain_priority_2",
        "label": f"{hints[1]}",
        "options": ["yes", "no", "not-sure"],
    }
    return [{"id": "app_idea", "label": "What app do you want to design?", "options": []}] + BASE_QUESTIONS + [extra, extra_2]


def build_design_options(app_idea: str, answers: Dict[str, str]) -> Dict[str, object]:
    provider = answers.get("cloud_provider", "aws")
    services = PROVIDER_MAP.get(provider, PROVIDER_MAP["aws"])
    domain = infer_domain(app_idea)

    designs = [
        _simple_design(app_idea, domain, answers, services),
        _medium_design(app_idea, domain, answers, services),
        _highly_complex_design(app_idea, domain, answers, services),
    ]

    return {
        "app_idea": app_idea,
        "domain": domain,
        "clarifying_summary": _summary(answers),
        "designs": designs,
    }


def _summary(answers: Dict[str, str]) -> List[str]:
    return [
        f"Cloud: {answers.get('cloud_provider', 'aws')}",
        f"User scale: {answers.get('target_users', '10k-200k users')}",
        f"Peak RPS: {answers.get('peak_rps', '100-1k')}",
        f"Regions: {answers.get('regions', 'single-region')}",
        f"Consistency: {answers.get('consistency', 'mixed')}",
    ]


def _simple_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    return {
        "level": "Simple design",
        "goal": f"Fast launch for {app_idea} with minimal operational complexity.",
        "components": [
            s.waf,
            s.lb,
            "Single API service",
            s.database,
            s.cache,
            s.object_store,
            s.observability,
        ],
        "diagram": (
            "Users -> WAF -> LB -> API Service\n"
            "API Service -> Database\n"
            "API Service -> Cache\n"
            "API Service -> Object Storage\n"
            "API Service -> Observability"
        ),
        "user_actions": [
            "User opens app and sends request to API through WAF and load balancer.",
            "API validates auth, serves data from cache when possible, and falls back to DB.",
            "Media/files are fetched from object storage and returned to clients.",
        ],
        "traffic_flow": [
            "Mostly synchronous request-response path.",
            "Cache absorbs repeated reads to reduce DB load.",
            "Single-region deployment with backup snapshots.",
        ],
        "why_this_level": "Best for MVP or early traction where simplicity and delivery speed matter most.",
    }


def _medium_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    return {
        "level": "Complex design (Medium scale)",
        "goal": f"Scale {app_idea} for growing traffic with bounded service decomposition.",
        "components": [
            s.dns,
            s.waf,
            s.lb,
            s.compute,
            "API Gateway + Auth Service + Domain Services",
            s.queue,
            s.database,
            s.cache,
            s.object_store,
            s.observability,
        ],
        "diagram": (
            "Users -> DNS -> WAF -> LB -> API Gateway\n"
            "API Gateway -> Auth Service\n"
            "API Gateway -> Domain Services (on Kubernetes)\n"
            "Domain Services -> Queue -> Worker Services\n"
            "Domain Services -> Database / Cache / Object Storage\n"
            "All services -> Observability"
        ),
        "user_actions": [
            "User login and app interactions route through API gateway for auth, throttling, and routing.",
            "Core business action is written to DB and emits event to queue for async tasks (notifications, indexing, billing).",
            "Background workers consume queue, process tasks, and update read models/cache.",
        ],
        "traffic_flow": [
            "Mixed synchronous + asynchronous traffic pattern.",
            "Burst traffic is buffered by queue to protect database and downstream services.",
            "Read-heavy endpoints use cache and read replicas to keep latency stable.",
        ],
        "why_this_level": "Best for teams with medium scale needing flexibility, resilience, and independent service scaling.",
    }


def _highly_complex_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    return {
        "level": "Highly complex design",
        "goal": f"Global, resilient architecture for very high-scale {app_idea} traffic and strict uptime targets.",
        "components": [
            s.dns,
            "Global traffic management",
            s.waf,
            s.lb,
            f"Multi-region {s.compute}",
            "Service mesh",
            "CQRS read/write services",
            s.queue,
            f"Global primary + regional replicas of {s.database}",
            s.cache,
            s.object_store,
            "Disaster recovery automation",
            s.observability,
        ],
        "diagram": (
            "Users -> Global DNS/Traffic Manager\n"
            "      -> Region A: WAF -> LB -> Kubernetes Cluster A\n"
            "      -> Region B: WAF -> LB -> Kubernetes Cluster B\n"
            "Clusters -> Service Mesh -> Write Services -> Primary DB\n"
            "Clusters -> Read Services -> Regional Read Replicas + Cache\n"
            "Clusters -> Event Bus/Queue -> Stream Processors/Workers\n"
            "Clusters -> Object Storage + Global Observability + DR"
        ),
        "user_actions": [
            "User is routed to nearest healthy region based on latency and failover policy.",
            "Write actions go through idempotent write services; events are published for downstream projections and analytics.",
            "Read actions are served by regional read stacks and cache for low-latency responses.",
            "If a region degrades, traffic shifts automatically with minimal user-visible disruption.",
        ],
        "traffic_flow": [
            "Global edge ingress with region-aware routing and automated health checks.",
            "Command and query traffic separated to optimize consistency and performance.",
            "Event streams replicate state updates to search, analytics, notifications, and audit pipelines.",
            "Cross-region replication and DR workflows enforce RPO/RTO objectives.",
        ],
        "why_this_level": "Best for mission-critical, high-volume systems needing multi-region high availability and rapid failover.",
    }
