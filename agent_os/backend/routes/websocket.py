from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import time
from agent_os.backend.store import runs
from agent_os.backend.services.langgraph_engine import LangGraphEngine

router = APIRouter(prefix="/ws", tags=["websocket"])

engine = LangGraphEngine()

@router.websocket("/stream/{run_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    run_id: str,
):
    await websocket.accept()
    print(f"WebSocket client connected to run: {run_id}")
    
    if run_id not in runs:
        await websocket.send_json({"type": "system", "message": f"Error: Run {run_id} not found."})
        await websocket.close()
        return

    run_info = runs[run_id]
    run_type = run_info["type"]
    params = run_info.get("params", {})

    try:
        stream_gen = None
        if run_type == "scan":
            stream_gen = engine.run_scan(run_id, params)
        elif run_type == "pipeline":
            stream_gen = engine.run_pipeline(run_id, params)
        elif run_type == "portfolio":
            stream_gen = engine.run_portfolio(run_id, params)
        elif run_type == "auto":
            stream_gen = engine.run_auto(run_id, params)
        
        if stream_gen:
            async for payload in stream_gen:
                # Add timestamp if not present
                if "timestamp" not in payload:
                    payload["timestamp"] = time.strftime("%H:%M:%S")
                await websocket.send_json(payload)
        else:
            await websocket.send_json({"type": "system", "message": f"Error: Run type {run_type} streaming not yet implemented."})
            
        await websocket.send_json({"type": "system", "message": "Run completed."})
        
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected from run {run_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "system", "message": f"Error: {str(e)}"})
            await websocket.close()
        except Exception:
            pass
