"""Infrastructure templates and blueprint generation."""

from __future__ import annotations
import logging
from enum import Enum
from typing import Any


class TemplateCategory(str, Enum):
    """Blueprint template categories."""

    WEB = "web"
    DATABASE = "database"
    MICROSERVICES = "microservices"
    DATA = "data"
    ML = "ml"
    SECURITY = "security"
    NETWORKING = "networking"
    MONITORING = "monitoring"


class BlueprintTemplates:
    """
    Library of pre-built blueprint templates for common patterns.

    Templates are production-ready and follow best practices.
    """

    @staticmethod
    def get_all_templates() -> list[dict[str, Any]]:
        """
        Get list of all available templates.

        Returns:
            List of template metadata
        """
        return [
            {
                "id": "simple-web-app",
                "name": "Simple Web Application",
                "category": TemplateCategory.WEB,
                "description": "Basic web app with load balancer and database",
                "complexity": "simple",
                "estimated_cost": "$100-200/month",
            },
            {
                "id": "ha-web-app",
                "name": "High-Availability Web Application",
                "category": TemplateCategory.WEB,
                "description": "HA web app with autoscaling, CDN, and failover",
                "complexity": "medium",
                "estimated_cost": "$500-1000/month",
            },
            {
                "id": "microservices-k8s",
                "name": "Kubernetes Microservices Platform",
                "category": TemplateCategory.MICROSERVICES,
                "description": "Full microservices platform with service mesh",
                "complexity": "advanced",
                "estimated_cost": "$1000-2000/month",
            },
            {
                "id": "postgres-ha",
                "name": "PostgreSQL High Availability Cluster",
                "category": TemplateCategory.DATABASE,
                "description": "PostgreSQL with replication and automated backup",
                "complexity": "medium",
                "estimated_cost": "$300-600/month",
            },
            {
                "id": "data-pipeline",
                "name": "Data Processing Pipeline",
                "category": TemplateCategory.DATA,
                "description": "ETL pipeline with data warehouse and analytics",
                "complexity": "advanced",
                "estimated_cost": "$800-1500/month",
            },
            {
                "id": "ml-training",
                "name": "ML Training Infrastructure",
                "category": TemplateCategory.ML,
                "description": "GPU cluster for ML model training",
                "complexity": "advanced",
                "estimated_cost": "$2000-5000/month",
            },
            {
                "id": "zero-trust-network",
                "name": "Zero-Trust Network",
                "category": TemplateCategory.SECURITY,
                "description": "Zero-trust architecture with mTLS and segmentation",
                "complexity": "advanced",
                "estimated_cost": "$400-800/month",
            },
            {
                "id": "observability-stack",
                "name": "Full Observability Stack",
                "category": TemplateCategory.MONITORING,
                "description": "Metrics, logs, traces with Prometheus/Grafana/Jaeger",
                "complexity": "medium",
                "estimated_cost": "$200-400/month",
            },
            {
                "id": "api-gateway",
                "name": "API Gateway Platform",
                "category": TemplateCategory.NETWORKING,
                "description": "Kong-based API gateway with rate limiting",
                "complexity": "medium",
                "estimated_cost": "$300-500/month",
            },
            {
                "id": "redis-cluster",
                "name": "Redis High-Performance Cache",
                "category": TemplateCategory.DATABASE,
                "description": "Redis cluster with persistence and replication",
                "complexity": "simple",
                "estimated_cost": "$100-300/month",
            },
        ]

    @staticmethod
    def get_template(template_id: str) -> dict[str, Any]:
        """
        Get specific template blueprint.

        Args:
            template_id: Template identifier

        Returns:
            Blueprint template

        Raises:
            ValueError: If template not found
        """
        # Map common aliases to actual template IDs
        template_aliases = {
            "kubernetes-cluster": "microservices-k8s",
            "microservices": "microservices-k8s",
        }

        # Use alias if available
        actual_template_id = template_aliases.get(template_id, template_id)

        templates = {
            "simple-web-app": BlueprintTemplates._simple_web_app(),
            "ha-web-app": BlueprintTemplates._ha_web_app(),
            "microservices-k8s": BlueprintTemplates._microservices_k8s(),
            "postgres-ha": BlueprintTemplates._postgres_ha(),
            "data-pipeline": BlueprintTemplates._data_pipeline(),
            "ml-training": BlueprintTemplates._ml_training(),
            "zero-trust-network": BlueprintTemplates._zero_trust_network(),
            "observability-stack": BlueprintTemplates._observability_stack(),
            "api-gateway": BlueprintTemplates._api_gateway(),
            "redis-cluster": BlueprintTemplates._redis_cluster(),
        }

        if actual_template_id not in templates:
            raise ValueError(f"Template '{template_id}' not found")

        return templates[actual_template_id]

    @staticmethod
    def list_templates(category: TemplateCategory | None = None) -> list[dict[str, Any]]:
        """
        List all available templates, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of template metadata
        """
        templates = BlueprintTemplates.get_all_templates()

        if category:
            templates = [t for t in templates if t["category"] == category]

        return templates

    @staticmethod
    def customize_template(template_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Customize a template with provided parameters.

        Args:
            template_id: Template identifier
            parameters: Customization parameters (e.g., instance_count, cpu_per_instance)

        Returns:
            Customized blueprint
        """
        template = BlueprintTemplates.get_template(template_id)
        blueprint = template.copy()

        # Apply common customizations
        if "instance_count" in parameters:
            # Scale compute resources
            compute_resources = [
                r for r in blueprint.get("resources", []) if r.get("type") == "compute"
            ]
            if compute_resources and len(compute_resources) > 0:
                # Replicate the first compute resource
                base_resource = compute_resources[0].copy()
                new_resources = []
                for r in blueprint.get("resources", []):
                    if r.get("type") != "compute":
                        new_resources.append(r)

                for i in range(parameters["instance_count"]):
                    resource = base_resource.copy()
                    resource["name"] = f"{base_resource['name']}-{i+1}"
                    new_resources.append(resource)

                blueprint["resources"] = new_resources

        if "cpu_per_instance" in parameters:
            for resource in blueprint.get("resources", []):
                if resource.get("type") == "compute" and "specs" in resource:
                    resource["specs"]["cpu"] = parameters["cpu_per_instance"]

        if "memory_per_instance" in parameters:
            for resource in blueprint.get("resources", []):
                if resource.get("type") == "compute" and "specs" in resource:
                    resource["specs"]["memory"] = parameters["memory_per_instance"]

        if "environment" in parameters:
            if "metadata" not in blueprint:
                blueprint["metadata"] = {}
            blueprint["metadata"]["environment"] = parameters["environment"]

        return blueprint

    @staticmethod
    def _simple_web_app() -> dict[str, Any]:
        """Simple web application template."""
        return {
            "version": "1.0",
            "name": "simple-web-app",
            "description": "Simple web application with load balancer and database",
            "resources": [
                {
                    "type": "network",
                    "name": "load-balancer",
                    "provider": "fake",
                    "specs": {
                        "type": "http",
                        "algorithm": "round-robin",
                        "health_check": "/health",
                        "backends": ["web-server-1", "web-server-2"],
                    },
                },
                {
                    "type": "compute",
                    "name": "web-server-1",
                    "provider": "proxmox",
                    "specs": {"cpu": 2, "memory": "4GB", "storage": "50GB", "os": "ubuntu-22.04"},
                    "dependencies": ["postgres-db"],
                },
                {
                    "type": "compute",
                    "name": "web-server-2",
                    "provider": "proxmox",
                    "specs": {"cpu": 2, "memory": "4GB", "storage": "50GB", "os": "ubuntu-22.04"},
                    "dependencies": ["postgres-db"],
                },
                {
                    "type": "compute",
                    "name": "postgres-db",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "8GB", "storage": "200GB", "storage_type": "SSD"},
                },
            ],
            "metadata": {"template": "simple-web-app", "category": "web", "complexity": "simple"},
        }

    @staticmethod
    def _ha_web_app() -> dict[str, Any]:
        """High-availability web application template."""
        return {
            "version": "1.0",
            "name": "ha-web-app",
            "description": "High-availability web application with autoscaling",
            "resources": [
                {
                    "type": "network",
                    "name": "cdn",
                    "provider": "fake",
                    "specs": {"type": "cdn", "caching": True, "ssl": True, "waf": True},
                },
                {
                    "type": "network",
                    "name": "primary-lb",
                    "provider": "fake",
                    "specs": {
                        "type": "application",
                        "algorithm": "least-connections",
                        "ssl_termination": True,
                        "health_check": "/health",
                        "backends": ["web-1", "web-2", "web-3"],
                    },
                },
                {
                    "type": "compute",
                    "name": "web-1",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 4,
                        "memory": "8GB",
                        "storage": "100GB",
                        "autoscaling": {"min": 2, "max": 10, "target_cpu": 70},
                    },
                    "dependencies": ["db-primary", "redis-cache"],
                },
                {
                    "type": "compute",
                    "name": "web-2",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "8GB", "storage": "100GB"},
                    "dependencies": ["db-primary", "redis-cache"],
                },
                {
                    "type": "compute",
                    "name": "web-3",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "8GB", "storage": "100GB"},
                    "dependencies": ["db-primary", "redis-cache"],
                },
                {
                    "type": "compute",
                    "name": "db-primary",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 8,
                        "memory": "32GB",
                        "storage": "1TB",
                        "storage_type": "NVMe",
                        "replication": {"standby": "db-standby", "type": "streaming"},
                    },
                },
                {
                    "type": "compute",
                    "name": "db-standby",
                    "provider": "proxmox",
                    "specs": {"cpu": 8, "memory": "32GB", "storage": "1TB", "storage_type": "NVMe"},
                },
                {
                    "type": "compute",
                    "name": "redis-cache",
                    "provider": "proxmox",
                    "specs": {"cpu": 2, "memory": "16GB", "storage": "100GB"},
                },
            ],
            "metadata": {
                "template": "ha-web-app",
                "category": "web",
                "complexity": "medium",
                "availability": "99.9%",
            },
        }

    @staticmethod
    def _microservices_k8s() -> dict[str, Any]:
        """Kubernetes microservices platform template."""
        return {
            "version": "1.0",
            "name": "microservices-k8s",
            "description": "Kubernetes-based microservices platform with service mesh",
            "resources": [
                {
                    "type": "compute",
                    "name": "k8s-master-1",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 4,
                        "memory": "16GB",
                        "storage": "200GB",
                        "role": "control-plane",
                    },
                },
                {
                    "type": "compute",
                    "name": "k8s-master-2",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 4,
                        "memory": "16GB",
                        "storage": "200GB",
                        "role": "control-plane",
                    },
                },
                {
                    "type": "compute",
                    "name": "k8s-master-3",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 4,
                        "memory": "16GB",
                        "storage": "200GB",
                        "role": "control-plane",
                    },
                },
                {
                    "type": "compute",
                    "name": "k8s-worker-pool",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 8,
                        "memory": "32GB",
                        "storage": "500GB",
                        "role": "worker",
                        "count": 5,
                        "autoscaling": {"min": 3, "max": 20},
                    },
                },
                {
                    "type": "service",
                    "name": "istio-service-mesh",
                    "provider": "fake",
                    "specs": {
                        "type": "service-mesh",
                        "mTLS": True,
                        "tracing": True,
                        "traffic_management": True,
                    },
                },
                {
                    "type": "storage",
                    "name": "persistent-storage",
                    "provider": "proxmox",
                    "specs": {"type": "ceph", "size": "10TB", "replicas": 3},
                },
            ],
            "metadata": {
                "template": "microservices-k8s",
                "category": "microservices",
                "complexity": "advanced",
            },
        }

    @staticmethod
    def _postgres_ha() -> dict[str, Any]:
        """PostgreSQL HA cluster template."""
        return {
            "version": "1.0",
            "name": "postgres-ha",
            "description": "PostgreSQL high-availability cluster with automated failover",
            "resources": [
                {
                    "type": "compute",
                    "name": "pg-primary",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 8,
                        "memory": "32GB",
                        "storage": "2TB",
                        "storage_type": "NVMe",
                        "role": "primary",
                    },
                },
                {
                    "type": "compute",
                    "name": "pg-replica-1",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 8,
                        "memory": "32GB",
                        "storage": "2TB",
                        "storage_type": "NVMe",
                        "role": "replica",
                    },
                    "dependencies": ["pg-primary"],
                },
                {
                    "type": "compute",
                    "name": "pg-replica-2",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 8,
                        "memory": "32GB",
                        "storage": "2TB",
                        "storage_type": "NVMe",
                        "role": "replica",
                    },
                    "dependencies": ["pg-primary"],
                },
                {
                    "type": "service",
                    "name": "pgpool",
                    "provider": "fake",
                    "specs": {
                        "type": "connection-pooler",
                        "load_balancing": True,
                        "failover": "automatic",
                    },
                },
                {
                    "type": "storage",
                    "name": "backup-storage",
                    "provider": "proxmox",
                    "specs": {"type": "s3-compatible", "size": "5TB", "retention": "30 days"},
                },
            ],
            "metadata": {"template": "postgres-ha", "category": "database", "complexity": "medium"},
        }

    @staticmethod
    def _data_pipeline() -> dict[str, Any]:
        """Data processing pipeline template."""
        return {
            "version": "1.0",
            "name": "data-pipeline",
            "description": "ETL pipeline with data warehouse and analytics",
            "resources": [
                {
                    "type": "service",
                    "name": "airflow",
                    "provider": "fake",
                    "specs": {"type": "workflow-orchestrator", "workers": 5, "scheduler_ha": True},
                },
                {
                    "type": "service",
                    "name": "kafka-cluster",
                    "provider": "fake",
                    "specs": {
                        "type": "message-queue",
                        "brokers": 3,
                        "partitions": 100,
                        "replication": 3,
                    },
                },
                {
                    "type": "compute",
                    "name": "spark-cluster",
                    "provider": "proxmox",
                    "specs": {"cpu": 32, "memory": "128GB", "storage": "2TB", "workers": 10},
                },
                {
                    "type": "storage",
                    "name": "data-lake",
                    "provider": "fake",
                    "specs": {
                        "type": "object-storage",
                        "size": "100TB",
                        "lifecycle": "intelligent-tiering",
                    },
                },
                {
                    "type": "service",
                    "name": "clickhouse",
                    "provider": "fake",
                    "specs": {"type": "data-warehouse", "shards": 4, "replicas": 2},
                },
            ],
            "metadata": {"template": "data-pipeline", "category": "data", "complexity": "advanced"},
        }

    @staticmethod
    def _ml_training() -> dict[str, Any]:
        """ML training infrastructure template."""
        return {
            "version": "1.0",
            "name": "ml-training",
            "description": "GPU cluster for machine learning model training",
            "resources": [
                {
                    "type": "compute",
                    "name": "gpu-node-1",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 32,
                        "memory": "256GB",
                        "storage": "4TB",
                        "gpu": "NVIDIA A100",
                        "gpu_count": 8,
                    },
                },
                {
                    "type": "compute",
                    "name": "gpu-node-2",
                    "provider": "proxmox",
                    "specs": {
                        "cpu": 32,
                        "memory": "256GB",
                        "storage": "4TB",
                        "gpu": "NVIDIA A100",
                        "gpu_count": 8,
                    },
                },
                {
                    "type": "service",
                    "name": "mlflow",
                    "provider": "fake",
                    "specs": {
                        "type": "ml-platform",
                        "experiment_tracking": True,
                        "model_registry": True,
                    },
                },
                {
                    "type": "storage",
                    "name": "dataset-storage",
                    "provider": "fake",
                    "specs": {"type": "high-throughput", "size": "50TB", "iops": 100000},
                },
            ],
            "metadata": {"template": "ml-training", "category": "ml", "complexity": "advanced"},
        }

    @staticmethod
    def _zero_trust_network() -> dict[str, Any]:
        """Zero-trust network template."""
        return {
            "version": "1.0",
            "name": "zero-trust-network",
            "description": "Zero-trust architecture with mTLS and micro-segmentation",
            "resources": [
                {
                    "type": "service",
                    "name": "identity-provider",
                    "provider": "fake",
                    "specs": {"type": "idp", "mfa": True, "sso": True},
                },
                {
                    "type": "network",
                    "name": "service-mesh",
                    "provider": "fake",
                    "specs": {
                        "type": "zero-trust-mesh",
                        "mTLS": "enforced",
                        "authorization": "fine-grained",
                    },
                },
                {
                    "type": "service",
                    "name": "policy-engine",
                    "provider": "fake",
                    "specs": {"type": "opa", "policies": "least-privilege"},
                },
                {
                    "type": "service",
                    "name": "certificate-manager",
                    "provider": "fake",
                    "specs": {"type": "vault", "auto_rotation": True, "ttl": "24h"},
                },
            ],
            "metadata": {
                "template": "zero-trust-network",
                "category": "security",
                "complexity": "advanced",
            },
        }

    @staticmethod
    def _observability_stack() -> dict[str, Any]:
        """Full observability stack template."""
        return {
            "version": "1.0",
            "name": "observability-stack",
            "description": "Complete observability with metrics, logs, and traces",
            "resources": [
                {
                    "type": "service",
                    "name": "prometheus",
                    "provider": "fake",
                    "specs": {"type": "metrics", "retention": "90 days", "ha": True, "replicas": 2},
                },
                {
                    "type": "service",
                    "name": "grafana",
                    "provider": "fake",
                    "specs": {
                        "type": "visualization",
                        "dashboards": "pre-configured",
                        "alerting": True,
                    },
                },
                {
                    "type": "service",
                    "name": "loki",
                    "provider": "fake",
                    "specs": {"type": "logs", "retention": "30 days", "compression": True},
                },
                {
                    "type": "service",
                    "name": "jaeger",
                    "provider": "fake",
                    "specs": {
                        "type": "tracing",
                        "sampling": "adaptive",
                        "storage": "elasticsearch",
                    },
                },
                {
                    "type": "service",
                    "name": "alertmanager",
                    "provider": "fake",
                    "specs": {"type": "alerting", "integrations": ["slack", "pagerduty", "email"]},
                },
            ],
            "metadata": {
                "template": "observability-stack",
                "category": "monitoring",
                "complexity": "medium",
            },
        }

    @staticmethod
    def _api_gateway() -> dict[str, Any]:
        """API gateway platform template."""
        return {
            "version": "1.0",
            "name": "api-gateway",
            "description": "Kong-based API gateway with rate limiting and authentication",
            "resources": [
                {
                    "type": "service",
                    "name": "kong-gateway",
                    "provider": "fake",
                    "specs": {
                        "type": "api-gateway",
                        "instances": 3,
                        "plugins": ["rate-limiting", "jwt-auth", "cors", "request-transformer"],
                    },
                },
                {
                    "type": "compute",
                    "name": "kong-db",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "16GB", "storage": "500GB", "type": "postgresql"},
                },
                {
                    "type": "service",
                    "name": "redis-cache",
                    "provider": "fake",
                    "specs": {"type": "cache", "size": "8GB", "eviction": "lru"},
                },
            ],
            "metadata": {
                "template": "api-gateway",
                "category": "networking",
                "complexity": "medium",
            },
        }

    @staticmethod
    def _redis_cluster() -> dict[str, Any]:
        """Redis high-performance cache template."""
        return {
            "version": "1.0",
            "name": "redis-cluster",
            "description": "Redis cluster with persistence and replication",
            "resources": [
                {
                    "type": "compute",
                    "name": "redis-master-1",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "master"},
                },
                {
                    "type": "compute",
                    "name": "redis-master-2",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "master"},
                },
                {
                    "type": "compute",
                    "name": "redis-master-3",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "master"},
                },
                {
                    "type": "compute",
                    "name": "redis-replica-1",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "replica"},
                    "dependencies": ["redis-master-1"],
                },
                {
                    "type": "compute",
                    "name": "redis-replica-2",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "replica"},
                    "dependencies": ["redis-master-2"],
                },
                {
                    "type": "compute",
                    "name": "redis-replica-3",
                    "provider": "proxmox",
                    "specs": {"cpu": 4, "memory": "32GB", "storage": "200GB", "role": "replica"},
                    "dependencies": ["redis-master-3"],
                },
                {
                    "type": "service",
                    "name": "redis-sentinel",
                    "provider": "fake",
                    "specs": {"type": "failover-manager", "instances": 3, "quorum": 2},
                },
            ],
            "metadata": {
                "template": "redis-cluster",
                "category": "database",
                "complexity": "simple",
            },
        }
