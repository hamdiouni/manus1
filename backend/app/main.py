"""
FastAPI main application for SLA Violation Prediction and Anomaly Detection platform.
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime, timedelta
import logging
import os
from contextlib import asynccontextmanager

from .database import SessionLocal, engine, get_db
from .models import Base
from .schemas import (
    TelemetryCreate, Telemetry, TelemetryUpdate, PredictionRequest, PredictionResponse,
    AnomalyRequest, AnomalyResponse, ExplanationResponse, ModelMetricsResponse,
    AlertRequest, WebSocketMessage, HealthResponse
)
from .crud import TelemetryCRUD, ModelMetricsCRUD, AlertLogCRUD
from ml.predictor import MLPredictor
from .alerts import AlertManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for background tasks
alert_manager = None
ml_predictor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global alert_manager, ml_predictor
    
    # Startup
    logger.info("Starting SLA Violation Prediction API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize ML predictor
    try:
        ml_predictor = MLPredictor()
        logger.info("ML predictor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML predictor: {e}")
        ml_predictor = None
    
    # Initialize alert manager
    try:
        alert_manager = AlertManager()
        logger.info("Alert manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize alert manager: {e}")
        alert_manager = None
    
    logger.info("API startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SLA Violation Prediction API...")

# Create FastAPI app
app = FastAPI(
    title="SLA Violation Prediction API",
    description="Machine Learning platform for predicting SLA violations and detecting anomalies in network telemetry",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Test ML model status
    try:
        ml_predictor.health_check()
        model_status = "healthy"
    except Exception as e:
        model_status = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" and model_status == "healthy" else "degraded",
        version="1.0.0",
        database_status=db_status,
        model_status=model_status
    )

# Telemetry CRUD endpoints
@app.post("/telemetry/", response_model=Telemetry)
async def create_telemetry(
    telemetry: TelemetryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new telemetry record."""
    crud = TelemetryCRUD(db)
    db_telemetry = crud.create_telemetry(telemetry)
    
    # Broadcast to WebSocket clients
    background_tasks.add_task(
        broadcast_telemetry_update,
        {"type": "telemetry_created", "data": db_telemetry.id}
    )
    
    return db_telemetry

@app.get("/telemetry/", response_model=List[Telemetry])
async def get_telemetry_list(
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sla_violation: Optional[bool] = None,
    anomaly_flag: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of telemetry records with optional filters."""
    crud = TelemetryCRUD(db)
    return crud.get_telemetry_list(
        skip=skip, limit=limit, start_time=start_time, end_time=end_time,
        sla_violation=sla_violation, anomaly_flag=anomaly_flag
    )

@app.get("/telemetry/{telemetry_id}", response_model=Telemetry)
async def get_telemetry(telemetry_id: int, db: Session = Depends(get_db)):
    """Get a specific telemetry record."""
    crud = TelemetryCRUD(db)
    db_telemetry = crud.get_telemetry(telemetry_id)
    if db_telemetry is None:
        raise HTTPException(status_code=404, detail="Telemetry record not found")
    return db_telemetry

@app.put("/telemetry/{telemetry_id}", response_model=Telemetry)
async def update_telemetry(
    telemetry_id: int,
    telemetry_update: TelemetryUpdate,
    db: Session = Depends(get_db)
):
    """Update a telemetry record."""
    crud = TelemetryCRUD(db)
    db_telemetry = crud.update_telemetry(telemetry_id, telemetry_update)
    if db_telemetry is None:
        raise HTTPException(status_code=404, detail="Telemetry record not found")
    return db_telemetry

@app.delete("/telemetry/{telemetry_id}")
async def delete_telemetry(telemetry_id: int, db: Session = Depends(get_db)):
    """Delete a telemetry record."""
    crud = TelemetryCRUD(db)
    if not crud.delete_telemetry(telemetry_id):
        raise HTTPException(status_code=404, detail="Telemetry record not found")
    return {"message": "Telemetry record deleted successfully"}

# ML prediction endpoints
@app.post("/predict/", response_model=PredictionResponse)
async def predict_sla_violation(
    prediction_request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Predict SLA violation for given telemetry data."""
    crud = TelemetryCRUD(db)
    return crud.predict_sla_violation(prediction_request)

@app.post("/predict-and-store/", response_model=Telemetry)
async def predict_and_store(
    telemetry: TelemetryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Predict SLA violation and store the result with telemetry data."""
    crud = TelemetryCRUD(db)
    db_telemetry = crud.predict_and_store(telemetry)
    
    # Check for high-risk predictions and trigger alerts
    if db_telemetry.sla_risk_score and db_telemetry.sla_risk_score > 0.8:
        background_tasks.add_task(
            trigger_sla_alert,
            db_telemetry.id,
            db_telemetry.sla_risk_score
        )
    
    # Broadcast to WebSocket clients
    background_tasks.add_task(
        broadcast_telemetry_update,
        {"type": "prediction_stored", "data": {
            "id": db_telemetry.id,
            "sla_violation": db_telemetry.sla_violation,
            "sla_risk_score": db_telemetry.sla_risk_score
        }}
    )
    
    return db_telemetry

@app.post("/anomaly/", response_model=AnomalyResponse)
async def detect_anomaly(
    anomaly_request: AnomalyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Detect anomalies in telemetry data."""
    crud = TelemetryCRUD(db)
    anomaly_response = crud.detect_anomaly(anomaly_request)
    
    # If anomaly detected, trigger alert
    if anomaly_response.anomaly_flag:
        background_tasks.add_task(
            trigger_anomaly_alert,
            anomaly_response.anomaly_score
        )
    
    return anomaly_response

@app.get("/explain/{telemetry_id}", response_model=ExplanationResponse)
async def get_explanation(telemetry_id: int, db: Session = Depends(get_db)):
    """Get SHAP explanation for a telemetry record."""
    crud = TelemetryCRUD(db)
    explanation = crud.get_explanation(telemetry_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="Explanation not available")
    return explanation

# Analytics endpoints
@app.get("/analytics/high-risk")
async def get_high_risk_telemetry(
    hours: int = 24,
    risk_threshold: float = 0.7,
    db: Session = Depends(get_db)
):
    """Get recent high-risk telemetry records."""
    crud = TelemetryCRUD(db)
    return crud.get_recent_high_risk(hours, risk_threshold)

@app.get("/analytics/anomalies")
async def get_recent_anomalies(hours: int = 24, db: Session = Depends(get_db)):
    """Get recent anomalies."""
    crud = TelemetryCRUD(db)
    return crud.get_recent_anomalies(hours)

@app.get("/analytics/model-metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(model_name: str = "xgboost", db: Session = Depends(get_db)):
    """Get latest model performance metrics."""
    crud = ModelMetricsCRUD(db)
    metrics = crud.get_latest_metrics(model_name)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Model metrics not found")
    
    # Parse feature importance JSON
    feature_importance = json.loads(metrics.feature_importance) if metrics.feature_importance else {}
    
    return ModelMetricsResponse(
        model_name=metrics.model_name,
        model_version=metrics.model_version,
        accuracy=metrics.accuracy,
        precision=metrics.precision,
        recall=metrics.recall,
        f1_score=metrics.f1_score,
        auc_score=metrics.auc_score,
        training_data_size=metrics.training_data_size,
        feature_importance=feature_importance,
        created_at=metrics.created_at
    )

# Manual retraining endpoint
@app.post("/retrain/trigger")
async def trigger_retrain():
    """Manually trigger model retraining."""
    try:
        result = await trigger_manual_retrain()
        return {"message": "Retraining triggered", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

# Alert configuration endpoint
@app.post("/alerts/configure")
async def configure_alerts(alert_config: AlertRequest):
    """Configure alert settings."""
    global alert_manager
    if alert_manager:
        alert_manager.update_config(alert_config.dict())
        return {"message": "Alert configuration updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Alert manager not initialized")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task functions
async def broadcast_telemetry_update(message: Dict[str, Any]):
    """Broadcast telemetry updates to WebSocket clients."""
    await manager.broadcast(json.dumps(message))

async def trigger_sla_alert(telemetry_id: int, risk_score: float):
    """Trigger SLA violation alert."""
    global alert_manager
    if alert_manager:
        await alert_manager.send_sla_alert(telemetry_id, risk_score)

async def trigger_anomaly_alert(anomaly_score: float):
    """Trigger anomaly detection alert."""
    global alert_manager
    if alert_manager:
        await alert_manager.send_anomaly_alert(anomaly_score)

async def background_model_retraining():
    """Background task for automatic model retraining."""
    while True:
        try:
            # Wait 24 hours between retraining attempts
            await asyncio.sleep(24 * 60 * 60)
            
            logger.info("Starting automatic model retraining...")
            
            # Get database session
            db = SessionLocal()
            try:
                # Check if we have enough new data for retraining
                crud = TelemetryCRUD(db)
                recent_data = crud.get_telemetry_list(limit=1000)
                
                if len(recent_data) >= 100:  # Minimum data threshold
                    # Trigger retraining (implement in ML module)
                    global ml_predictor
                    if ml_predictor:
                        await ml_predictor.retrain_models(recent_data)
                        logger.info("Model retraining completed successfully")
                else:
                    logger.info("Insufficient data for retraining")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in background model retraining: {str(e)}")

async def background_alert_monitoring():
    """Background task for monitoring and sending alerts."""
    while True:
        try:
            # Check every 5 minutes
            await asyncio.sleep(5 * 60)
            
            # Get database session
            db = SessionLocal()
            try:
                crud = TelemetryCRUD(db)
                
                # Check for high-risk records in the last 5 minutes
                recent_high_risk = crud.get_recent_high_risk(hours=0.083, risk_threshold=0.8)  # 5 minutes
                
                for record in recent_high_risk:
                    await trigger_sla_alert(record.id, record.sla_risk_score)
                
                # Check for recent anomalies
                recent_anomalies = crud.get_recent_anomalies(hours=0.083)  # 5 minutes
                
                for record in recent_anomalies:
                    await trigger_anomaly_alert(record.anomaly_score or 0.0)
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in background alert monitoring: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

