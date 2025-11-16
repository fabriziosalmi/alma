"""
AI-CDN: Autonomous Infrastructure CDN
Infrastructure as Conversation Platform
"""

__version__ = "0.1.0"
__author__ = "AI-CDN Team"

from aicdn.models.blueprint import SystemBlueprint
from aicdn.models.resources import ComputeNode, NetworkLink, ServiceInstance

__all__ = [
    "SystemBlueprint",
    "ComputeNode",
    "NetworkLink",
    "ServiceInstance",
]
