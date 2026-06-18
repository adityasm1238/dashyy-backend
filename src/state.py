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
    card_data["cpu_temp"] = {
        "value": 35.0,
        "trend": "stable"
    }
    
    card_data["ram_usage"] = {
        "value": 50.0,
        "trend": "stable"
    }
    
    now = time.time()
    history_points = []
    for i in range(15):
        history_points.append({
            "timestamp": now - (15 - i) * 10,
            "download": random.uniform(15.0, 45.0),
            "upload": random.uniform(2.0, 8.0)
        })
    card_data["network_chart"] = {
        "history": history_points
    }
    
    card_data["jellyfin_playback"] = {
        "activeStreams": [
            {
                "id": "stream1",
                "title": "Dune: Part Two",
                "subtitle": "1080p H264 • Direct Play",
                "user": "Aditya",
                "progress": 0.35,
                "status": "Playing",
                "imageUrl": "https://image.tmdb.org/t/p/w500/8b8e8YIEqf64zFv8oExIYtdlggC.jpg"
            },
            {
                "id": "stream2",
                "title": "Severance",
                "subtitle": "S01E09 • The We We Are • 4K HEVC",
                "user": "Mom & Dad",
                "progress": 0.82,
                "status": "Paused",
                "imageUrl": "https://image.tmdb.org/t/p/w500/l3K3Rt9YA285gh54u7vA8719q6.jpg"
            }
        ],
        "recentlyAdded": [
            {"id": "m1", "title": "Furiosa: A Mad Max Saga", "type": "Movie", "imageUrl": "https://image.tmdb.org/t/p/w500/iADOZ8zG4clnFSCcmglozNN4CnC.jpg"},
            {"id": "m2", "title": "The Boys", "type": "Series", "imageUrl": "https://image.tmdb.org/t/p/w500/25CcR26V9s7u7t0qn6HqUF2cx2d.jpg"},
            {"id": "m3", "title": "Sh\u014dgun", "type": "Series", "imageUrl": "https://image.tmdb.org/t/p/w500/7O4iV21qn03m1Gp4n4NsZ5HEU6h.jpg"}
        ]
    }
    
    card_data["overseerr_requests"] = {
        "pendingCount": 3,
        "approvedCount": 24,
        "requests": [
            {"id": "req1", "title": "Deadpool & Wolverine", "requester": "Alice", "imageUrl": "https://image.tmdb.org/t/p/w500/8cdWjvZqMSd2trgIL3lh6w6tyaT.jpg"},
            {"id": "req2", "title": "House of the Dragon", "requester": "Bob", "imageUrl": "https://image.tmdb.org/t/p/w500/7xy695szIM6VD16C1R5n6Fc4rS5.jpg"},
            {"id": "req3", "title": "Inside Out 2", "requester": "Charlie", "imageUrl": "https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQjVoZ0gvtBGBnJv4.jpg"}
        ]
    }
    
    card_data["deluge_torrents"] = {
        "downloadSpeedText": "12.4 MB/s",
        "uploadSpeedText": "1.8 MB/s",
        "torrents": [
            {
                "id": "tor1",
                "name": "ubuntu-24.04-live-server.iso",
                "progress": 0.684,
                "progressPercentText": "68.4%",
                "status": "Downloading",
                "speedDown": 8.5,
                "speedText": "DL: 8.5 MB/s • ETA: 2m 14s"
            },
            {
                "id": "tor2",
                "name": "archlinux-2026.06.01.iso",
                "progress": 0.991,
                "progressPercentText": "99.1%",
                "status": "Downloading",
                "speedDown": 3.9,
                "speedText": "DL: 3.9 MB/s • ETA: 15s"
            },
            {
                "id": "tor3",
                "name": "debian-12.5.0-netinst.iso",
                "progress": 1.0,
                "progressPercentText": "100.0%",
                "status": "Seeding",
                "speedUp": 1.5,
                "speedText": "UL: 1.5 MB/s"
            }
        ]
    }

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
