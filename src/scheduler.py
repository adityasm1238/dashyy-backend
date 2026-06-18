import os
import json
import asyncio
import logging
import inspect
import src.state as state

logger = logging.getLogger("dashyy-backend")

# MARK: - Dynamic Extensions Loader

async def run_extension_function(extension_str: str, current_state: dict, card_id: str, card_config: dict) -> dict:
    """
    Dynamically loads a python module from the extensions directory and executes the specified function,
    passing the current persistent state of the card and config arguments if accepted.
    """
    if not extension_str or "." not in extension_str:
        raise ValueError(f"Invalid extension config format: '{extension_str}'. Expected 'module.function'")
        
    module_name, function_name = extension_str.split(".", 1)
    
    module = state.get_extension_module(module_name)
    if module is None:
        raise FileNotFoundError(f"Extension module '{module_name}' not found or failed to load")
        
    # Resolve function inside the loaded module
    func = getattr(module, function_name, None)
    if func is None:
        raise AttributeError(f"Function '{function_name}' not found in extension module '{module_name}'")
        
    # Inspect arguments to support flexible signatures (e.g. including config or card_id)
    sig = inspect.signature(func)
    kwargs = {}
    if "card_config" in sig.parameters:
        kwargs["card_config"] = card_config
    if "card_id" in sig.parameters:
        kwargs["card_id"] = card_id
        
    # Execute (supports both async def and def functions)
    if inspect.iscoroutinefunction(func):
        result = await func(current_state, **kwargs)
    else:
        result = func(current_state, **kwargs)
        
    if not isinstance(result, dict):
        raise TypeError(f"Extension function '{function_name}' must return a dictionary, got {type(result)}")
        
    return result

# MARK: - Telemetry Main Async loop

async def metrics_broadcast_loop():
    """
    Background scheduler thread that executes layout card extensions and pushes live status updates
    to the connected clients over WebSockets.
    """
    await asyncio.sleep(1.0) # startup delay
    
    while True:
        try:
            # Dynamically scan all configurations in /config/cards and run mapped extensions
            if os.path.exists(state.CARDS_DIR):
                for filename in os.listdir(state.CARDS_DIR):
                    if filename.endswith(".json"):
                        card_id = filename.replace(".json", "")
                        card_path = os.path.join(state.CARDS_DIR, filename)
                        
                        try:
                            with open(card_path, "r") as cf:
                                card_config = json.load(cf)
                            
                            extension_str = card_config.get("extension")
                            if extension_str:
                                current_state = state.card_data.get(card_id, {})
                                result = await run_extension_function(
                                    extension_str, 
                                    current_state, 
                                    card_id, 
                                    card_config
                                )
                                state.card_data[card_id] = result
                        except Exception as ext_err:
                            logger.error(f"Error running extension for card {card_id}: {ext_err}")
                            # Keep user-friendly error message
                            error_msg = str(ext_err)
                            if "credentials not configured" in error_msg.lower():
                                error_msg = "Credentials not configured"
                            elif "connection failed" in error_msg.lower() or "unable to connect" in error_msg.lower():
                                service_name = card_id.replace("_", " ").title()
                                error_msg = f"Unable to connect to {service_name} service"
                            state.card_data[card_id] = {"error": error_msg}
                            
            # Broadcast update packet to all active WS listeners
            await state.broadcast_update()
            
        except Exception as e:
            logger.error(f"Error in metrics loop thread: {e}")
            
        await asyncio.sleep(2.5)
