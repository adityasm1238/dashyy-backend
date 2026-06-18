import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.state import initialize_card_data, sync_default_extensions
from src.scheduler import metrics_broadcast_loop
from src.routes.dashboard import router as dashboard_router
from src.routes.actions import router as actions_router
from src.routes.websocket import router as ws_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashyy-backend")

app = FastAPI(title="Dashyy Backend", version="1.0.0")

# Enable CORS for local network dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(dashboard_router)
app.include_router(actions_router)
app.include_router(ws_router)

@app.on_event("startup")
async def startup_event():
    # Sync default extensions to extensions folder
    sync_default_extensions()
    
    # Load initial mock state in memory
    initialize_card_data()
    
    # Start the async broadcast task on app initialization
    asyncio.create_task(metrics_broadcast_loop())
    logger.info("FastAPI dashboard backend modular server initialized.")
