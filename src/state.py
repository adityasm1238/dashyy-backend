import os
import json
import time
import logging
import random
import importlib.util
import shutil
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("dashyy-backend")

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
CARDS_DIR = os.path.join(CONFIG_DIR, "cards")
DEFAULT_EXTENSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "default_extensions"))
EXTENSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extensions"))

def get_card_config(card_id: str) -> dict:
    try:
        card_path = os.path.join(CARDS_DIR, f"{card_id}.json")
        if os.path.exists(card_path):
            with open(card_path, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config for card {card_id}: {e}")
    return {}

def get_api_config(card_id: str) -> dict:
    return get_card_config(card_id).get("apiConfig", {})

def get_extension_module(module_name: str):
    """
    Dynamically imports a python module from the extensions directory.
    """
    file_name = f"{module_name}.py"
    file_path = os.path.join(EXTENSIONS_DIR, file_name)
    if not os.path.exists(file_path):
        logger.error(f"Extension file '{file_name}' not found in {EXTENSIONS_DIR}")
        return None
        
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to dynamically load extension module '{module_name}': {e}")
        return None

def sync_default_extensions():
    """
    Ensures that default extensions are synced to the extensions directory.
    This prevents users from losing default extensions when mounting empty volumes.
    """
    if not os.path.exists(EXTENSIONS_DIR):
        os.makedirs(EXTENSIONS_DIR, exist_ok=True)
    if os.path.exists(DEFAULT_EXTENSIONS_DIR):
        for item in os.listdir(DEFAULT_EXTENSIONS_DIR):
            src_path = os.path.join(DEFAULT_EXTENSIONS_DIR, item)
            dest_path = os.path.join(EXTENSIONS_DIR, item)
            if os.path.isfile(src_path) and not os.path.exists(dest_path):
                logger.info(f"Provisioning default extension: {item}")
                shutil.copy2(src_path, dest_path)

# Active WebSockets clients
active_connections: List[WebSocket] = []

# Cached dynamic metrics & card payloads
card_data: Dict[str, Dict[str, Any]] = {}

def initialize_card_data():
    global card_data
    card_data = {}

async def broadcast_update():
    """
    Sends updated data packets to all connected dashboard client sessions.
    """
    if not active_connections:
        return
    
    payload = {
        "type": "card_update",
        "timestamp": time.time(),
        "cardData": card_data
    }
    
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except Exception:
            disconnected.append(ws)
            
    for ws in disconnected:
        if ws in active_connections:
            active_connections.remove(ws)
