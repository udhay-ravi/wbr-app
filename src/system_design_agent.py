from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProviderServices:
    lb: str
    compute: str
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
        waf="Azure WAF",
        dns="Azure Traffic Manager",
    ),
    "gcp": ProviderServices(
        lb="Cloud Load Balancing",
        compute="Google Kubernetes Engine (GKE)",
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
        "required_answers": [q["id"] for q in BASE_QUESTIONS],
        "designs": designs,
    }


def _domain_components(domain: str) -> List[str]:
    if domain == "ecommerce":
        return ["Catalog Service", "Checkout Service", "Inventory Service"]
    if domain == "stream":
        return ["Ingestion Service", "Transcoding Pipeline", "Session Service"]
    if domain == "iot":
        return ["Device Gateway", "Telemetry Rules Engine", "Time-series Query Service"]
    return ["Tenant Service", "Billing Service", "Notification Service"]


def _domain_user_actions(domain: str) -> List[str]:
    if domain == "ecommerce":
        return [
            "User searches products, reviews details, and adds items to cart.",
            "Checkout requests reserve inventory, validate payment, and create order records.",
        ]
    if domain == "stream":
        return [
            "Creator uploads media; ingestion validates and sends content to processing.",
            "Viewers request playback; service returns optimized stream variants by device/network.",
        ]
    if domain == "iot":
        return [
            "Devices publish telemetry bursts through secure gateway endpoints.",
            "Rules engine evaluates thresholds and triggers notifications/automation actions.",
        ]
    return [
        "User signs in to tenant workspace and performs business operations.",
        "Billing and notification workflows are triggered from product usage events.",
    ]


def _summary(answers: Dict[str, str]) -> List[str]:
    return [
        f"Cloud: {answers.get('cloud_provider', 'aws')}",
        f"User scale: {answers.get('target_users', '10k-200k users')}",
        f"Peak RPS: {answers.get('peak_rps', '100-1k')}",
        f"Regions: {answers.get('regions', 'single-region')}",
        f"Consistency: {answers.get('consistency', 'mixed')}",
    ]


def _simple_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    domain_components = _domain_components(domain)
    domain_actions = _domain_user_actions(domain)
    return {
        "level": "Simple design",
        "goal": f"Fast launch for {app_idea} with minimal operational complexity.",
        "components": [
            s.waf,
            s.lb,
            "Single API service",
            *domain_components,
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
            *domain_actions,
        ],
        "traffic_flow": [
            "Mostly synchronous request-response path.",
            "Cache absorbs repeated reads to reduce DB load.",
            "Single-region deployment with backup snapshots.",
        ],
        "why_this_level": "Best for MVP or early traction where simplicity and delivery speed matter most.",
    }


def _medium_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    domain_components = _domain_components(domain)
    domain_actions = _domain_user_actions(domain)
    return {
        "level": "Complex design (Medium scale)",
        "goal": f"Scale {app_idea} for growing traffic with bounded service decomposition.",
        "components": [
            s.dns,
            s.waf,
            s.lb,
            s.compute,
            "API Gateway + Auth Service + Domain Services",
            *domain_components,
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
            *domain_actions,
        ],
        "traffic_flow": [
            "Mixed synchronous + asynchronous traffic pattern.",
            "Burst traffic is buffered by queue to protect database and downstream services.",
            "Read-heavy endpoints use cache and read replicas to keep latency stable.",
        ],
        "why_this_level": "Best for teams with medium scale needing flexibility, resilience, and independent service scaling.",
    }


def _highly_complex_design(app_idea: str, domain: str, answers: Dict[str, str], s: ProviderServices) -> dict:
    domain_components = _domain_components(domain)
    domain_actions = _domain_user_actions(domain)
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
            *domain_components,
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
            *domain_actions,
        ],
        "traffic_flow": [
            "Global edge ingress with region-aware routing and automated health checks.",
            "Command and query traffic separated to optimize consistency and performance.",
            "Event streams replicate state updates to search, analytics, notifications, and audit pipelines.",
            "Cross-region replication and DR workflows enforce RPO/RTO objectives.",
        ],
        "why_this_level": "Best for mission-critical, high-volume systems needing multi-region high availability and rapid failover.",
    }
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
