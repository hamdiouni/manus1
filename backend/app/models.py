"""
SQLAlchemy ORM models for the SLA Violation Prediction platform.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .database import Base

class Telemetry(Base):
    """
    Network telemetry data model with SLA violation predictions and anomaly flags.
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Network metrics from the dataset
    bandwidth = Column(Float, nullable=False)
    throughput = Column(Float, nullable=False)
    congestion = Column(Float, nullable=False)
    packet_loss = Column(Float, nullable=False)
    latency = Column(Float, nullable=False)
    jitter = Column(Float, nullable=False)
    
    # Network topology information
    routers = Column(String(100), nullable=True)
    planned_route = Column(String(100), nullable=True)
    network_measure = Column(String(50), nullable=True)
    network_target = Column(String(50), nullable=True)
    
    # Video-related metrics
    video_target = Column(String(50), nullable=True)
    percentage_video_occupancy = Column(Float, nullable=True)
    bitrate_video = Column(Float, nullable=True)
    number_videos = Column(Integer, nullable=True)
    
    # ML predictions and flags
    sla_violation = Column(Boolean, nullable=True)  # Predicted SLA violation
    sla_risk_score = Column(Float, nullable=True)   # Risk score (0-1)
    anomaly_flag = Column(Boolean, default=False)   # Anomaly detection flag
    anomaly_score = Column(Float, nullable=True)    # Anomaly score
    
    # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ModelMetrics(Base):
    """
    Model performance metrics and metadata.
    """
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_score = Column(Float, nullable=True)
    training_data_size = Column(Integer, nullable=True)
    feature_importance = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AlertLog(Base):
    """
    Alert log for tracking sent notifications.
    """
    __tablename__ = "alert_log"
    
    id = Column(Integer, primary_key=True, index=True)
    telemetry_id = Column(Integer, nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'sla_violation', 'anomaly'
    alert_channel = Column(String(50), nullable=False)  # 'telegram', 'email'
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='sent')  # 'sent', 'failed'

