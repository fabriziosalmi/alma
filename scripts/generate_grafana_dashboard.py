"""Grafana dashboard configuration for ALMA metrics."""

import json
from typing import Dict, Any


def generate_grafana_dashboard() -> Dict[str, Any]:
    """
    Generate Grafana dashboard JSON for ALMA.
    
    Returns:
        Grafana dashboard configuration
    """
    return {
        "dashboard": {
            "title": "ALMA Metrics Dashboard",
            "tags": ["ALMA", "infrastructure", "llm"],
            "timezone": "browser",
            "schemaVersion": 16,
            "version": 0,
            "refresh": "10s",
            "panels": [
                # HTTP Requests
                {
                    "id": 1,
                    "title": "HTTP Requests (rate)",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "rate(aicdn_http_requests_total[5m])",
                            "legendFormat": "{{method}} {{endpoint}} ({{status}})"
                        }
                    ]
                },
                # HTTP Response Time
                {
                    "id": 2,
                    "title": "HTTP Response Time (p95)",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(aicdn_http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "{{method}} {{endpoint}}"
                        }
                    ]
                },
                # LLM Requests
                {
                    "id": 3,
                    "title": "LLM Requests",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "rate(aicdn_llm_requests_total[5m])",
                            "legendFormat": "{{operation}} ({{status}})"
                        }
                    ]
                },
                # LLM Generation Time
                {
                    "id": 4,
                    "title": "LLM Generation Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(aicdn_llm_generation_duration_seconds_bucket[5m]))",
                            "legendFormat": "{{model}} {{operation}}"
                        }
                    ]
                },
                # Rate Limiting
                {
                    "id": 5,
                    "title": "Rate Limit Hits",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                    "targets": [
                        {
                            "expr": "rate(aicdn_rate_limit_hits_total[5m])",
                            "legendFormat": "{{endpoint}}"
                        }
                    ]
                },
                # Blueprint Operations
                {
                    "id": 6,
                    "title": "Blueprint Operations",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                    "targets": [
                        {
                            "expr": "rate(aicdn_blueprint_operations_total[5m])",
                            "legendFormat": "{{operation}} ({{status}})"
                        }
                    ]
                },
                # Tool Executions
                {
                    "id": 7,
                    "title": "Tool Executions",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
                    "targets": [
                        {
                            "expr": "rate(aicdn_tool_executions_total[5m])",
                            "legendFormat": "{{tool_name}} ({{status}})"
                        }
                    ]
                },
                # Active Connections
                {
                    "id": 8,
                    "title": "Active Connections",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
                    "targets": [
                        {
                            "expr": "aicdn_active_connections",
                            "legendFormat": "Active Connections"
                        }
                    ]
                },
                # Deployment Duration
                {
                    "id": 9,
                    "title": "Deployment Duration (p95)",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 32},
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(aicdn_deployment_duration_seconds_bucket[5m]))",
                            "legendFormat": "{{engine}}"
                        }
                    ]
                }
            ]
        }
    }


def save_dashboard(filepath: str = "grafana-dashboard.json") -> None:
    """
    Save Grafana dashboard to file.
    
    Args:
        filepath: Output file path
    """
    dashboard = generate_grafana_dashboard()
    
    with open(filepath, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"✓ Grafana dashboard saved to {filepath}")
    print("\nTo import:")
    print("1. Open Grafana")
    print("2. Go to Dashboards > Import")
    print(f"3. Upload {filepath}")


if __name__ == "__main__":
    save_dashboard()
