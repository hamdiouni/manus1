"""
ML Predictor module for SLA Violation Prediction and Anomaly Detection.
"""

import joblib
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import shap
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class MLPredictor:
    """ML Predictor for SLA violations and anomaly detection."""
    
    def __init__(self, model_dir='./'):
        self.model_dir = model_dir
        self.models = {}
        self.scaler = None
        self.label_encoders = {}
        self.feature_names = []
        self.shap_explainers = {}
        self.model_metrics = {}
        self.is_loaded = False
        
        # Try to load models on initialization
        self._load_models()
    
    def _load_models(self):
        """Load trained models and artifacts."""
        try:
            # Load main models
            model_files = {
                'xgboost_tuned': 'xgboost_tuned_model.pkl',
                'xgboost': 'xgboost_model.pkl',
                'random_forest': 'random_forest_model.pkl',
                'isolation_forest': 'isolation_forest_model.pkl'
            }
            
            for model_name, filename in model_files.items():
                filepath = os.path.join(self.model_dir, filename)
                if os.path.exists(filepath):
                    self.models[model_name] = joblib.load(filepath)
                    logger.info(f"Loaded {model_name} model")
            
            # Load scaler
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded scaler")
            
            # Load label encoders
            encoders_path = os.path.join(self.model_dir, 'label_encoders.pkl')
            if os.path.exists(encoders_path):
                self.label_encoders = joblib.load(encoders_path)
                logger.info("Loaded label encoders")
            
            # Load feature names
            features_path = os.path.join(self.model_dir, 'feature_names.json')
            if os.path.exists(features_path):
                with open(features_path, 'r') as f:
                    self.feature_names = json.load(f)
                logger.info(f"Loaded {len(self.feature_names)} feature names")
            
            # Load model metrics
            metrics_path = os.path.join(self.model_dir, 'model_metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    self.model_metrics = json.load(f)
                logger.info("Loaded model metrics")
            
            # Load SHAP explainers
            shap_files = [f for f in os.listdir(self.model_dir) if f.startswith('shap_explainer_')]
            for shap_file in shap_files:
                model_name = shap_file.replace('shap_explainer_', '').replace('.pkl', '')
                filepath = os.path.join(self.model_dir, shap_file)
                self.shap_explainers[model_name] = joblib.load(filepath)
                logger.info(f"Loaded SHAP explainer for {model_name}")
            
            self.is_loaded = len(self.models) > 0
            if self.is_loaded:
                logger.info("ML models loaded successfully")
            else:
                logger.warning("No models loaded - using fallback predictions")
                
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self.is_loaded = False
    
    def _prepare_features(self, telemetry_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features from telemetry data for prediction."""
        if not self.feature_names:
            # Fallback feature preparation if feature names not loaded
            features = [
                telemetry_data.get('bandwidth', 2.0),
                telemetry_data.get('throughput', 2.0),
                telemetry_data.get('congestion', 0.1),
                telemetry_data.get('packet_loss', 0.0),
                telemetry_data.get('latency', 6.0),
                telemetry_data.get('jitter', 0.4),
                telemetry_data.get('percentage_video_occupancy', 0.0),
                telemetry_data.get('bitrate_video', 0.0),
                telemetry_data.get('number_videos', 0)
            ]
            return np.array(features).reshape(1, -1)
        
        # Create feature vector based on trained feature names
        feature_vector = []
        
        # Basic numerical features
        basic_features = {
            'bandwidth': telemetry_data.get('bandwidth', 2.0),
            'throughput': telemetry_data.get('throughput', 2.0),
            'congestion': telemetry_data.get('congestion', 0.1),
            'packet_loss': telemetry_data.get('packet_loss', 0.0),
            'latency': telemetry_data.get('latency', 6.0),
            'jitter': telemetry_data.get('jitter', 0.4),
            'Percentage video occupancy': telemetry_data.get('percentage_video_occupancy', 0.0),
            'Bitrate video': telemetry_data.get('bitrate_video', 0.0),
            'Number videos': telemetry_data.get('number_videos', 0)
        }
        
        # Derived features
        bandwidth = basic_features['bandwidth']
        throughput = basic_features['throughput']
        latency = basic_features['latency']
        jitter = basic_features['jitter']
        congestion = basic_features['congestion']
        packet_loss = basic_features['packet_loss']
        
        derived_features = {
            'throughput_bandwidth_ratio': throughput / bandwidth if bandwidth > 0 else 0,
            'latency_jitter_ratio': latency / (jitter + 0.001),
            'congestion_packet_loss_combined': congestion * packet_loss,
            'video_load': basic_features['Percentage video occupancy'] * basic_features['Number videos']
        }
        
        # Time-based features (use current time as default)
        current_time = datetime.now()
        time_features = {
            'hour': current_time.hour,
            'minute': current_time.minute,
            'day_of_week': current_time.weekday()
        }
        
        # Categorical features (encoded)
        categorical_defaults = {
            'Routers_encoded': 0,
            'Planned route_encoded': 0,
            'Network measure_encoded': 0,
            'Network target_encoded': 0,
            'Video target_encoded': 0
        }
        
        # Combine all features
        all_features = {**basic_features, **derived_features, **time_features, **categorical_defaults}
        
        # Create feature vector in the same order as training
        for feature_name in self.feature_names:
            feature_vector.append(all_features.get(feature_name, 0.0))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def predict_sla_violation(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict SLA violation probability."""
        try:
            if not self.is_loaded:
                # Fallback prediction
                return {
                    'prediction': 0,
                    'probability': 0.1,
                    'confidence': 0.0,
                    'features_used': [],
                    'model_used': 'fallback'
                }
            
            # Prepare features
            features = self._prepare_features(telemetry_data)
            
            # Use best available model
            model_name = 'xgboost_tuned' if 'xgboost_tuned' in self.models else 'xgboost'
            if model_name not in self.models:
                model_name = list(self.models.keys())[0]  # Use any available model
            
            model = self.models[model_name]
            
            # Make prediction
            prediction = model.predict(features)[0]
            probability = model.predict_proba(features)[0, 1]
            
            # Calculate confidence (distance from decision boundary)
            confidence = abs(probability - 0.5) * 2
            
            return {
                'prediction': int(prediction),
                'probability': float(probability),
                'confidence': float(confidence),
                'features_used': self.feature_names[:9],  # Return main features
                'model_used': model_name
            }
            
        except Exception as e:
            logger.error(f"Error in SLA prediction: {str(e)}")
            # Return safe fallback
            return {
                'prediction': 0,
                'probability': 0.1,
                'confidence': 0.0,
                'features_used': [],
                'model_used': 'error_fallback'
            }
    
    def detect_anomaly(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in telemetry data."""
        try:
            if not self.is_loaded or 'isolation_forest' not in self.models:
                # Fallback anomaly detection based on simple rules
                latency = telemetry_data.get('latency', 6.0)
                packet_loss = telemetry_data.get('packet_loss', 0.0)
                congestion = telemetry_data.get('congestion', 0.1)
                
                # Simple rule-based anomaly detection
                is_anomaly = (latency > 15) or (packet_loss > 10) or (congestion > 0.8)
                anomaly_score = max(latency/20, packet_loss/20, congestion)
                
                return {
                    'anomaly': bool(is_anomaly),
                    'score': float(min(anomaly_score, 1.0)),
                    'threshold': 0.5,
                    'model_used': 'rule_based_fallback'
                }
            
            # Prepare features
            features = self._prepare_features(telemetry_data)
            
            # Scale features if scaler is available
            if self.scaler:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features
            
            # Get anomaly prediction
            model = self.models['isolation_forest']
            anomaly_prediction = model.predict(features_scaled)[0]
            anomaly_score = model.decision_function(features_scaled)[0]
            
            # Convert to binary (True for anomaly)
            is_anomaly = anomaly_prediction == -1
            
            # Normalize score to 0-1 range (higher = more anomalous)
            normalized_score = max(0, min(1, (0.5 - anomaly_score) / 1.0))
            
            return {
                'anomaly': bool(is_anomaly),
                'score': float(normalized_score),
                'threshold': 0.5,
                'model_used': 'isolation_forest'
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            # Return safe fallback
            return {
                'anomaly': False,
                'score': 0.0,
                'threshold': 0.5,
                'model_used': 'error_fallback'
            }
    
    def explain_prediction(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SHAP explanation for a prediction."""
        try:
            if not self.is_loaded or not self.shap_explainers:
                return {
                    'shap_values': {},
                    'base_value': 0.0,
                    'prediction': 0.0,
                    'explanation_available': False
                }
            
            # Prepare features
            features = self._prepare_features(telemetry_data)
            
            # Use best available explainer
            explainer_name = 'xgboost_tuned' if 'xgboost_tuned' in self.shap_explainers else list(self.shap_explainers.keys())[0]
            explainer = self.shap_explainers[explainer_name]
            
            # Get SHAP values
            shap_values = explainer.shap_values(features)
            base_value = explainer.expected_value
            
            # Create feature-value mapping
            shap_dict = {}
            for i, feature_name in enumerate(self.feature_names):
                if i < len(shap_values[0]):
                    shap_dict[feature_name] = float(shap_values[0][i])
            
            # Get prediction
            model = self.models[explainer_name]
            prediction = model.predict_proba(features)[0, 1]
            
            return {
                'shap_values': shap_dict,
                'base_value': float(base_value),
                'prediction': float(prediction),
                'explanation_available': True
            }
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return {
                'shap_values': {},
                'base_value': 0.0,
                'prediction': 0.0,
                'explanation_available': False
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health status of the ML predictor."""
        status = {
            'models_loaded': len(self.models),
            'scaler_loaded': self.scaler is not None,
            'feature_names_loaded': len(self.feature_names),
            'explainers_loaded': len(self.shap_explainers),
            'is_ready': self.is_loaded
        }
        
        if not self.is_loaded:
            raise Exception("ML models not loaded properly")
        
        return status
    
    async def retrain_models(self, new_data: List[Any]):
        """Retrain models with new data (placeholder for future implementation)."""
        logger.info(f"Retraining requested with {len(new_data)} new samples")
        # This would implement incremental learning or full retraining
        # For now, just log the request
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            'loaded_models': list(self.models.keys()),
            'feature_count': len(self.feature_names),
            'model_metrics': self.model_metrics,
            'last_loaded': datetime.now().isoformat()
        }

