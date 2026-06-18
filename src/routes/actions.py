import inspect
import logging
from fastapi import APIRouter, HTTPException
import src.state as state

logger = logging.getLogger("dashyy-backend")
router = APIRouter()

@router.post("/api/actions/{card_id}/{action}")
async def post_action(card_id: str, action: str, id: str = None):
    logger.info(f"Action triggered: {card_id} -> {action} for ID: {id}")
    
    card_config = state.get_card_config(card_id)
    extension_str = card_config.get("extension")
    
    if not extension_str or "." not in extension_str:
        raise HTTPException(
            status_code=400, 
            detail=f"Card '{card_id}' does not support dynamic actions (no extension configured)."
        )
        
    module_name, _ = extension_str.split(".", 1)
    module = state.get_extension_module(module_name)
    if module is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Extension module '{module_name}' not found for card '{card_id}'."
        )
        
    handle_action_func = getattr(module, "handle_action", None)
    if handle_action_func is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Extension module '{module_name}' does not implement 'handle_action'."
        )
        
    try:
        # Check signature to see what parameters handle_action expects
        sig = inspect.signature(handle_action_func)
        kwargs = {}
        if "card_config" in sig.parameters:
            kwargs["card_config"] = card_config
            
        # Execute the action handler (handles both async def and def handlers)
        if inspect.iscoroutinefunction(handle_action_func):
            await handle_action_func(action, id, **kwargs)
        else:
            handle_action_func(action, id, **kwargs)
            
    except Exception as e:
        logger.error(f"Action execution failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to execute action '{action}' on service '{card_id}': {str(e)}"
        )
        
    # Trigger an immediate broadcast of updated states
    await state.broadcast_update()
    return {"status": "success", "action": action}
