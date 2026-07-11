"""
Browser WebSocket API – Live browser screenshot streaming
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.api.tasks import _active_orchestrators

router = APIRouter()


@router.websocket("/ws/live/{task_id}")
async def browser_live_stream(websocket: WebSocket, task_id: int, token: str):
    """
    WebSocket endpoint for live browser screenshot streaming.
    
    Streams base64-encoded JPEG screenshots at ~500ms intervals.
    Each message is JSON:
    {
        "type": "frame",
        "data": {
            "screenshot": "<base64>",
            "url": "https://...",
            "title": "Page Title"
        }
    }
    """
    await websocket.accept()
    
    try:
        # Authenticate
        from app.core.security import decode_token
        payload = decode_token(token)
        
        # Find active orchestrator
        orchestrator = _active_orchestrators.get(task_id)
        if not orchestrator:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "No active browser session for this task"},
            })
            return
        
        # Stream frames until browser stops
        while orchestrator.browser._is_running:
            try:
                b64 = await orchestrator.browser.take_screenshot_base64()
                page_info = await orchestrator.browser.get_page_info()
                
                await websocket.send_json({
                    "type": "frame",
                    "data": {
                        "screenshot": b64,
                        "url": page_info.get("url", ""),
                        "title": page_info.get("title", ""),
                    },
                })
            except Exception as e:
                logger.debug(f"Browser stream frame error: {e}")
            
            await asyncio.sleep(0.5)
        
        await websocket.send_json({
            "type": "session_ended",
            "data": {"message": "Browser session completed"},
        })
        
    except WebSocketDisconnect:
        logger.info(f"Browser stream client disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"Browser stream error: {e}")
