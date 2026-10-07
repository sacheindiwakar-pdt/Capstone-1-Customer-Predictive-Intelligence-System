from fastapi import FastAPI
from routes.network import router as network_router
from routes.grid import router as grid_router
from routes.hotspot_alert_route import router as hotspot_router
from routes.features import router as feature_router
from routes.prediction import router as prediction_router
from routes.operations import (router as operations_router)

app = FastAPI(
    title="Telecom Analytics API"
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(network_router)
app.include_router(grid_router)
app.include_router(hotspot_router)
app.include_router(feature_router)
app.include_router(prediction_router)
app.include_router(operations_router)