"""
CRUD operations and business logic for the SLA Violation Prediction platform.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from . import models, schemas
from backend.ml.predictor import MLPredictor

class TelemetryCRUD:
    """CRUD operations for telemetry data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_predictor = MLPredictor()
    
    def create_telemetry(self, telemetry: schemas.TelemetryCreate) -> models.Telemetry:
        """Create a new telemetry record."""
        db_telemetry = models.Telemetry(**telemetry.dict())
        self.db.add(db_telemetry)
        self.db.commit()
        self.db.refresh(db_telemetry)
        return db_telemetry
    
    def get_telemetry(self, telemetry_id: int) -> Optional[models.Telemetry]:
        """Get a telemetry record by ID."""
        return self.db.query(models.Telemetry).filter(models.Telemetry.id == telemetry_id).first()
    
    def get_telemetry_list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sla_violation: Optional[bool] = None,
        anomaly_flag: Optional[bool] = None
    ) -> List[models.Telemetry]:
        """Get a list of telemetry records with optional filters."""
        query = self.db.query(models.Telemetry)
        
        if start_time:
            query = query.filter(models.Telemetry.timestamp >= start_time)
        if end_time:
            query = query.filter(models.Telemetry.timestamp <= end_time)
        if sla_violation is not None:
            query = query.filter(models.Telemetry.sla_violation == sla_violation)
        if anomaly_flag is not None:
            query = query.filter(models.Telemetry.anomaly_flag == anomaly_flag)
        
        return query.order_by(desc(models.Telemetry.timestamp)).offset(skip).limit(limit).all()
    
    def update_telemetry(
        self, 
        telemetry_id: int, 
        telemetry_update: schemas.TelemetryUpdate
    ) -> Optional[models.Telemetry]:
        """Update a telemetry record."""
        db_telemetry = self.get_telemetry(telemetry_id)
        if db_telemetry:
            update_data = telemetry_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_telemetry, field, value)
            self.db.commit()
            self.db.refresh(db_telemetry)
        return db_telemetry
    
    def delete_telemetry(self, telemetry_id: int) -> bool:
        """Delete a telemetry record."""
        db_telemetry = self.get_telemetry(telemetry_id)
        if db_telemetry:
            self.db.delete(db_telemetry)
            self.db.commit()
            return True
        return False
    
    def predict_sla_violation(self, telemetry_data: schemas.PredictionRequest) -> schemas.PredictionResponse:
        """Predict SLA violation for given telemetry data."""
        try:
            # Convert telemetry data to the format expected by ML model
            features = self._telemetry_to_features(telemetry_data)
            
            # Get prediction from ML model
            prediction_result = self.ml_predictor.predict_sla_violation(features)
            
            return schemas.PredictionResponse(
                sla_violation=bool(prediction_result['prediction']),
                sla_risk_score=float(prediction_result['probability']),
                confidence=float(prediction_result['confidence']),
                features_used=prediction_result['features_used']
            )
        except Exception as e:
            # Fallback prediction if ML model fails
            return schemas.PredictionResponse(
                sla_violation=False,
                sla_risk_score=0.0,
                confidence=0.0,
                features_used=[]
            )
    
    def predict_and_store(self, telemetry_data: schemas.TelemetryCreate) -> models.Telemetry:
        """Predict SLA violation and store the result with telemetry data."""
        # Get prediction
        prediction = self.predict_sla_violation(telemetry_data)
        
        # Create telemetry record with prediction
        db_telemetry = models.Telemetry(
            **telemetry_data.dict(),
            sla_violation=prediction.sla_violation,
            sla_risk_score=prediction.sla_risk_score
        )
        
        self.db.add(db_telemetry)
        self.db.commit()
        self.db.refresh(db_telemetry)
        
        return db_telemetry
    
    def detect_anomaly(self, telemetry_data: schemas.AnomalyRequest) -> schemas.AnomalyResponse:
        """Detect anomalies in telemetry data."""
        try:
            # Convert telemetry data to features
            features = self._telemetry_to_features(telemetry_data)
            
            # Get anomaly detection result
            anomaly_result = self.ml_predictor.detect_anomaly(features)
            
            return schemas.AnomalyResponse(
                anomaly_flag=bool(anomaly_result['anomaly']),
                anomaly_score=float(anomaly_result['score']),
                threshold=float(anomaly_result['threshold'])
            )
        except Exception as e:
            # Fallback response if anomaly detection fails
            return schemas.AnomalyResponse(
                anomaly_flag=False,
                anomaly_score=0.0,
                threshold=0.5
            )
    
    def get_explanation(self, telemetry_id: int) -> Optional[schemas.ExplanationResponse]:
        """Get SHAP explanation for a telemetry record."""
        db_telemetry = self.get_telemetry(telemetry_id)
        if not db_telemetry:
            return None
        
        try:
            # Convert telemetry to features
            features = self._telemetry_to_features(db_telemetry)
            
            # Get SHAP explanation
            explanation = self.ml_predictor.explain_prediction(features)
            
            return schemas.ExplanationResponse(
                telemetry_id=telemetry_id,
                shap_values=explanation['shap_values'],
                base_value=explanation['base_value'],
                prediction=explanation['prediction']
            )
        except Exception as e:
            return None
    
    def get_recent_high_risk(self, hours: int = 24, risk_threshold: float = 0.7) -> List[models.Telemetry]:
        """Get recent high-risk telemetry records."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(models.Telemetry).filter(
            and_(
                models.Telemetry.timestamp >= cutoff_time,
                models.Telemetry.sla_risk_score >= risk_threshold
            )
        ).order_by(desc(models.Telemetry.sla_risk_score)).all()
    
    def get_recent_anomalies(self, hours: int = 24) -> List[models.Telemetry]:
        """Get recent anomalies."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(models.Telemetry).filter(
            and_(
                models.Telemetry.timestamp >= cutoff_time,
                models.Telemetry.anomaly_flag == True
            )
        ).order_by(desc(models.Telemetry.timestamp)).all()
    
    def _telemetry_to_features(self, telemetry) -> Dict[str, float]:
        """Convert telemetry data to feature dictionary for ML models."""
        if isinstance(telemetry, models.Telemetry):
            return {
                'bandwidth': telemetry.bandwidth,
                'throughput': telemetry.throughput,
                'congestion': telemetry.congestion,
                'packet_loss': telemetry.packet_loss,
                'latency': telemetry.latency,
                'jitter': telemetry.jitter,
                'percentage_video_occupancy': telemetry.percentage_video_occupancy or 0.0,
                'bitrate_video': telemetry.bitrate_video or 0.0,
                'number_videos': telemetry.number_videos or 0
            }
        else:
            return {
                'bandwidth': telemetry.bandwidth,
                'throughput': telemetry.throughput,
                'congestion': telemetry.congestion,
                'packet_loss': telemetry.packet_loss,
                'latency': telemetry.latency,
                'jitter': telemetry.jitter,
                'percentage_video_occupancy': telemetry.percentage_video_occupancy or 0.0,
                'bitrate_video': telemetry.bitrate_video or 0.0,
                'number_videos': telemetry.number_videos or 0
            }

class ModelMetricsCRUD:
    """CRUD operations for model metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_model_metrics(self, metrics_data: Dict[str, Any]) -> models.ModelMetrics:
        """Create new model metrics record."""
        db_metrics = models.ModelMetrics(
            model_name=metrics_data['model_name'],
            model_version=metrics_data['model_version'],
            accuracy=metrics_data.get('accuracy'),
            precision=metrics_data.get('precision'),
            recall=metrics_data.get('recall'),
            f1_score=metrics_data.get('f1_score'),
            auc_score=metrics_data.get('auc_score'),
            training_data_size=metrics_data.get('training_data_size'),
            feature_importance=json.dumps(metrics_data.get('feature_importance', {}))
        )
        self.db.add(db_metrics)
        self.db.commit()
        self.db.refresh(db_metrics)
        return db_metrics
    
    def get_latest_metrics(self, model_name: str) -> Optional[models.ModelMetrics]:
        """Get latest metrics for a model."""
        return self.db.query(models.ModelMetrics).filter(
            models.ModelMetrics.model_name == model_name
        ).order_by(desc(models.ModelMetrics.created_at)).first()

class AlertLogCRUD:
    """CRUD operations for alert logs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_alert(
        self, 
        telemetry_id: int, 
        alert_type: str, 
        alert_channel: str, 
        message: str, 
        status: str = 'sent'
    ) -> models.AlertLog:
        """Log an alert."""
        db_alert = models.AlertLog(
            telemetry_id=telemetry_id,
            alert_type=alert_type,
            alert_channel=alert_channel,
            message=message,
            status=status
        )
        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)
        return db_alert
    
    def get_recent_alerts(self, hours: int = 24) -> List[models.AlertLog]:
        """Get recent alerts."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(models.AlertLog).filter(
            models.AlertLog.sent_at >= cutoff_time
        ).order_by(desc(models.AlertLog.sent_at)).all()

