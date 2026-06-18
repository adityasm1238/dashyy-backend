import os
import json
import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("dashyy-backend")
router = APIRouter()

# Configuration Directory Paths
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
CARDS_DIR = os.path.join(CONFIG_DIR, "cards")

@router.get("/api/dashboard")
async def get_dashboard():
    """
    Reads the main dashboard grid config and compiles it with individual cards in the /config/cards directory.
    """
    try:
        db_path = os.path.join(CONFIG_DIR, "dashboard.json")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail=f"Main dashboard layout config not found at {db_path}")
        
        with open(db_path, "r") as f:
            dashboard = json.load(f)
            
        # Dynamically load card layout widgets
        cards = {}
        if os.path.exists(CARDS_DIR):
            for filename in os.listdir(CARDS_DIR):
                if filename.endswith(".json"):
                    card_id = filename.replace(".json", "")
                    card_path = os.path.join(CARDS_DIR, filename)
                    with open(card_path, "r") as cf:
                        cards[card_id] = json.load(cf)
                        
        dashboard["cards"] = cards
        return dashboard
    except Exception as e:
        logger.error(f"Error loading config layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))
