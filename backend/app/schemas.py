"""
Pydantic schemas for request/response validation in the SLA Violation Prediction platform.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class TelemetryBase(BaseModel):
    """Base schema for telemetry data."""
    bandwidth: float = Field(..., description="Network bandwidth")
    throughput: float = Field(..., description="Network throughput")
    congestion: float = Field(..., description="Network congestion level")
    packet_loss: float = Field(..., description="Packet loss percentage")
    latency: float = Field(..., description="Network latency in ms")
    jitter: float = Field(..., description="Network jitter in ms")
    routers: Optional[str] = Field(None, description="Router information")
    planned_route: Optional[str] = Field(None, description="Planned network route")
    network_measure: Optional[str] = Field(None, description="Network measurement point")
    network_target: Optional[str] = Field(None, description="Network target")
    video_target: Optional[str] = Field(None, description="Video target")
    percentage_video_occupancy: Optional[float] = Field(None, description="Video occupancy percentage")
    bitrate_video: Optional[float] = Field(None, description="Video bitrate")
    number_videos: Optional[int] = Field(None, description="Number of videos")

class TelemetryCreate(TelemetryBase):
    """Schema for creating new telemetry records."""
    pass

class TelemetryUpdate(BaseModel):
    """Schema for updating telemetry records."""
    sla_violation: Optional[bool] = None
    sla_risk_score: Optional[float] = None
    anomaly_flag: Optional[bool] = None
    anomaly_score: Optional[float] = None

class Telemetry(TelemetryBase):
    """Schema for telemetry response with all fields."""
    id: int
    timestamp: datetime
    sla_violation: Optional[bool] = None
    sla_risk_score: Optional[float] = None
    anomaly_flag: Optional[bool] = False
    anomaly_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class PredictionRequest(TelemetryBase):
    """Schema for SLA violation prediction requests."""
    pass

class PredictionResponse(BaseModel):
    """Schema for SLA violation prediction responses."""
    sla_violation: bool = Field(..., description="Predicted SLA violation (0 or 1)")
    sla_risk_score: float = Field(..., description="Risk score between 0 and 1")
    confidence: float = Field(..., description="Model confidence")
    features_used: List[str] = Field(..., description="Features used in prediction")

class AnomalyRequest(TelemetryBase):
    """Schema for anomaly detection requests."""
    pass

class AnomalyResponse(BaseModel):
    """Schema for anomaly detection responses."""
    anomaly_flag: bool = Field(..., description="Anomaly detected flag")
    anomaly_score: float = Field(..., description="Anomaly score")
    threshold: float = Field(..., description="Anomaly threshold used")

class ExplanationResponse(BaseModel):
    """Schema for SHAP explanation responses."""
    telemetry_id: int
    shap_values: Dict[str, float] = Field(..., description="SHAP values for each feature")
    base_value: float = Field(..., description="Base prediction value")
    prediction: float = Field(..., description="Final prediction")

class ModelMetricsResponse(BaseModel):
    """Schema for model performance metrics."""
    model_name: str
    model_version: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_score: Optional[float] = None
    training_data_size: Optional[int] = None
    feature_importance: Optional[Dict[str, float]] = None
    created_at: datetime

    model_config = {
        'protected_namespaces': (),
        'from_attributes': True
    }

class AlertRequest(BaseModel):
    """Schema for alert configuration."""
    alert_type: str = Field(..., description="Type of alert: 'sla_violation' or 'anomaly'")
    threshold: float = Field(..., description="Threshold for triggering alerts")
    channels: List[str] = Field(..., description="Alert channels: ['telegram', 'email']")
    message_template: Optional[str] = Field(None, description="Custom message template")

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    """Schema for health check responses."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database connection status")
    model_status: str = Field(..., description="ML model status")

    model_config = {'protected_namespaces': ()}
