
"""WebSocket routes."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from alma.api.websocket_manager import manager

router = APIRouter(tags=["websockets"])


@router.websocket("/ws/deployments")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time deployment updates.
    
    Clients connect here to receive 'DeploymentStarted', 'DeploymentCompleted',
    and other infrastructure events.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for optional control messages
            # In a real scenario, we might handle incoming pings or auth tokens here
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
