
"""GraphQL Schema definition."""

import strawberry
from typing import Optional

@strawberry.type
class BlueprintType:
    id: strawberry.ID
    name: str
    description: Optional[str]
    version: str

@strawberry.type
class SystemStatus:
    status: str
    uptime_seconds: float
    active_connections: int

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello from ALMA GraphQL!"

    @strawberry.field
    def system_status(self) -> SystemStatus:
        from alma.middleware.metrics import get_metrics_collector
        collector = get_metrics_collector()
        summary = collector.get_summary()
        return SystemStatus(
            status="operational", 
            uptime_seconds=summary["uptime_seconds"],
            active_connections=int(summary["custom_metrics"].get("active_connections", 0))
        )

schema = strawberry.Schema(query=Query)
