import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import src.state as state

logger = logging.getLogger("dashyy-backend")
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(state.active_connections)}")
    
    try:
        # Push initial layout data states on connect
        await websocket.send_json({"type": "layout_config", "cardData": state.card_data})
        while True:
            # Keep connection alive, listen for any messages
            data = await websocket.receive_text()
            logger.info(f"Received WS msg: {data}")
    except WebSocketDisconnect:
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(state.active_connections)}")
    except Exception as e:
        logger.error(f"WS error: {e}")
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)
