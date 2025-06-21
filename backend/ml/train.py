"""
Machine Learning training pipeline for SLA Violation Prediction and Anomaly Detection.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score
import xgboost as xgb
import joblib
import json
import shap
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MLTrainer:
    """Machine Learning trainer for SLA violation prediction and anomaly detection."""
    
    def __init__(self, data_path='network_dataset.csv'):
        self.data_path = data_path
        self.df = None
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.models = {}
        self.model_metrics = {}
        self.feature_importance = {}
        self.shap_explainers = {}
        
    def load_and_preprocess_data(self):
        """Load and preprocess the network dataset."""
        print("Loading and preprocessing data...")
        
        # Load data
        self.df = pd.read_csv(self.data_path)
        print(f"Loaded dataset with shape: {self.df.shape}")
        
        # Convert timestamp to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # Handle missing values
        self.df['Video target'] = self.df['Video target'].fillna('none')
        
        # Create synthetic SLA violation labels based on network conditions
        # SLA violation occurs when:
        # - High latency (>10ms) OR
        # - High packet loss (>5%) OR
        # - High congestion (>0.5) OR
        # - Low throughput relative to bandwidth (<50%)
        self.df['sla_violation'] = (
            (self.df['latency'] > 10) |
            (self.df['packet_loss'] > 5) |
            (self.df['congestion'] > 0.5) |
            (self.df['throughput'] / self.df['bandwidth'] < 0.5)
        ).astype(int)
        
        # Create additional features
        self.df['throughput_bandwidth_ratio'] = self.df['throughput'] / self.df['bandwidth']
        self.df['latency_jitter_ratio'] = self.df['latency'] / (self.df['jitter'] + 0.001)  # Avoid division by zero
        self.df['congestion_packet_loss_combined'] = self.df['congestion'] * self.df['packet_loss']
        self.df['video_load'] = self.df['Percentage video occupancy'] * self.df['Number videos']
        
        # Extract time-based features
        self.df['hour'] = self.df['timestamp'].dt.hour
        self.df['minute'] = self.df['timestamp'].dt.minute
        self.df['day_of_week'] = self.df['timestamp'].dt.dayofweek
        
        print(f"SLA violation distribution: {self.df['sla_violation'].value_counts().to_dict()}")
        
        # Prepare features for ML
        self._prepare_features()
        
    def _prepare_features(self):
        """Prepare features for machine learning."""
        # Select numerical features
        numerical_features = [
            'bandwidth', 'throughput', 'congestion', 'packet_loss', 'latency', 'jitter',
            'Percentage video occupancy', 'Bitrate video', 'Number videos',
            'throughput_bandwidth_ratio', 'latency_jitter_ratio', 
            'congestion_packet_loss_combined', 'video_load',
            'hour', 'minute', 'day_of_week'
        ]
        
        # Select categorical features
        categorical_features = ['Routers', 'Planned route', 'Network measure', 'Network target', 'Video target']
        
        # Encode categorical features
        for feature in categorical_features:
            le = LabelEncoder()
            self.df[f'{feature}_encoded'] = le.fit_transform(self.df[feature])
            self.label_encoders[feature] = le
            numerical_features.append(f'{feature}_encoded')
        
        # Prepare feature matrix
        self.X = self.df[numerical_features].copy()
        self.y = self.df['sla_violation'].copy()
        
        # Handle any remaining missing values
        self.X = self.X.fillna(0)
        
        print(f"Feature matrix shape: {self.X.shape}")
        print(f"Features: {list(self.X.columns)}")
        
    def train_models(self):
        """Train multiple ML models for SLA violation prediction."""
        print("Training ML models...")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        # Scale features
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        
        # Train Random Forest (baseline)
        print("Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(self.X_train, self.y_train)
        self.models['random_forest'] = rf_model
        
        # Train XGBoost (production model)
        print("Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        xgb_model.fit(self.X_train, self.y_train)
        self.models['xgboost'] = xgb_model
        
        # Hyperparameter tuning for XGBoost
        print("Performing hyperparameter tuning for XGBoost...")
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 6, 9],
            'learning_rate': [0.01, 0.1, 0.2]
        }
        
        grid_search = GridSearchCV(
            xgb.XGBClassifier(random_state=42, eval_metric='logloss'),
            param_grid,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(self.X_train, self.y_train)
        
        self.models['xgboost_tuned'] = grid_search.best_estimator_
        print(f"Best XGBoost parameters: {grid_search.best_params_}")
        
        # Evaluate models
        self._evaluate_models()
        
        # Train SHAP explainers
        self._train_explainers()
        
    def train_anomaly_detection(self):
        """Train anomaly detection model."""
        print("Training anomaly detection model...")
        
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_jobs=-1
        )
        
        # Train on scaled features
        iso_forest.fit(self.X_train_scaled)
        self.models['isolation_forest'] = iso_forest
        
        # Evaluate anomaly detection
        anomaly_scores = iso_forest.decision_function(self.X_test_scaled)
        anomaly_predictions = iso_forest.predict(self.X_test_scaled)
        
        # Convert to binary (1 for normal, -1 for anomaly)
        anomaly_binary = (anomaly_predictions == -1).astype(int)
        
        print(f"Anomalies detected in test set: {anomaly_binary.sum()} out of {len(anomaly_binary)}")
        print(f"Anomaly detection rate: {anomaly_binary.mean():.2%}")
        
        # Store anomaly detection metrics
        self.model_metrics['isolation_forest'] = {
            'anomaly_rate': float(anomaly_binary.mean()),
            'anomaly_count': int(anomaly_binary.sum()),
            'total_samples': int(len(anomaly_binary))
        }
        
    def _evaluate_models(self):
        """Evaluate trained models."""
        print("Evaluating models...")
        
        for model_name, model in self.models.items():
            if model_name == 'isolation_forest':
                continue  # Skip anomaly detection model
                
            print(f"\\nEvaluating {model_name}...")
            
            # Predictions
            y_pred = model.predict(self.X_test)
            y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            
            # Metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            auc_score = roc_auc_score(self.y_test, y_pred_proba)
            
            # Classification report
            report = classification_report(self.y_test, y_pred, output_dict=True)
            
            # Store metrics
            self.model_metrics[model_name] = {
                'accuracy': float(accuracy),
                'auc_score': float(auc_score),
                'precision': float(report['1']['precision']),
                'recall': float(report['1']['recall']),
                'f1_score': float(report['1']['f1-score']),
                'training_data_size': int(len(self.X_train))
            }
            
            print(f"Accuracy: {accuracy:.4f}")
            print(f"AUC Score: {auc_score:.4f}")
            print(f"Precision: {report['1']['precision']:.4f}")
            print(f"Recall: {report['1']['recall']:.4f}")
            print(f"F1 Score: {report['1']['f1-score']:.4f}")
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(self.X.columns, model.feature_importances_))
                # Sort by importance
                importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
                self.feature_importance[model_name] = importance
                
                print(f"Top 5 important features for {model_name}:")
                for i, (feature, imp) in enumerate(list(importance.items())[:5]):
                    print(f"  {i+1}. {feature}: {imp:.4f}")
    
    def _train_explainers(self):
        """Train SHAP explainers for model interpretability."""
        print("Training SHAP explainers...")
        
        # Train explainer for XGBoost
        if 'xgboost_tuned' in self.models:
            explainer = shap.TreeExplainer(self.models['xgboost_tuned'])
            self.shap_explainers['xgboost_tuned'] = explainer
            
            # Calculate SHAP values for a sample
            shap_values = explainer.shap_values(self.X_test.iloc[:100])
            
            # Save SHAP summary plot
            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, self.X_test.iloc[:100], show=False)
            plt.tight_layout()
            plt.savefig('shap_summary_plot.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print("SHAP explainer trained and summary plot saved")
    
    def save_models_with_timestamp(self, timestamp: str):
        """Save trained models with timestamp."""
        print(f"Saving models with timestamp {timestamp}...")
        
        # Create timestamped directory
        model_dir = f"models_{timestamp}"
        os.makedirs(model_dir, exist_ok=True)
        
        # Save models
        for model_name, model in self.models.items():
            filename = os.path.join(model_dir, f"{model_name}_model.pkl")
            joblib.dump(model, filename)
            print(f"Saved {model_name} to {filename}")
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
        
        # Save label encoders
        joblib.dump(self.label_encoders, os.path.join(model_dir, 'label_encoders.pkl'))
        
        # Save feature names
        with open(os.path.join(model_dir, 'feature_names.json'), 'w') as f:
            json.dump(list(self.X.columns), f)
        
        # Save model metrics
        with open(os.path.join(model_dir, 'model_metrics.json'), 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        
        # Save feature importance
        feature_importance_serializable = {}
        for model_name, importance_dict in self.feature_importance.items():
            feature_importance_serializable[model_name] = {
                k: float(v) for k, v in importance_dict.items()
            }
        
        with open(os.path.join(model_dir, 'feature_importance.json'), 'w') as f:
            json.dump(feature_importance_serializable, f, indent=2)
        
        # Save SHAP explainers
        for explainer_name, explainer in self.shap_explainers.items():
            joblib.dump(explainer, os.path.join(model_dir, f'shap_explainer_{explainer_name}.pkl'))
        
        # Copy models to main directory for production use
        for model_name, model in self.models.items():
            filename = f"{model_name}_model.pkl"
            joblib.dump(model, filename)
        
        joblib.dump(self.scaler, 'scaler.pkl')
        joblib.dump(self.label_encoders, 'label_encoders.pkl')
        
        with open('feature_names.json', 'w') as f:
            json.dump(list(self.X.columns), f)
        
        print(f"All models saved with timestamp {timestamp} and copied to production directory!")
    
    def save_models(self):
        """Save trained models and artifacts."""
        print("Saving models and artifacts...")
        
        # Save models
        for model_name, model in self.models.items():
            filename = f"{model_name}_model.pkl"
            joblib.dump(model, filename)
            print(f"Saved {model_name} to {filename}")
        
        # Save scaler
        joblib.dump(self.scaler, 'scaler.pkl')
        
        # Save label encoders
        joblib.dump(self.label_encoders, 'label_encoders.pkl')
        
        # Save feature names
        with open('feature_names.json', 'w') as f:
            json.dump(list(self.X.columns), f)
        
        # Save model metrics
        with open('model_metrics.json', 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        
        # Save feature importance
        feature_importance_serializable = {}
        for model_name, importance_dict in self.feature_importance.items():
            feature_importance_serializable[model_name] = {
                k: float(v) for k, v in importance_dict.items()
            }
        
        with open('feature_importance.json', 'w') as f:
            json.dump(feature_importance_serializable, f, indent=2)
        
        # Save SHAP explainers
        for explainer_name, explainer in self.shap_explainers.items():
            joblib.dump(explainer, f'shap_explainer_{explainer_name}.pkl')
        
        print("All models and artifacts saved successfully!")
    
    def generate_training_report(self):
        """Generate a comprehensive training report."""
        print("Generating training report...")
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj
        
        report = {
            'training_timestamp': datetime.now().isoformat(),
            'dataset_info': {
                'total_samples': int(len(self.df)),
                'features': list(self.X.columns),
                'target_distribution': {str(k): int(v) for k, v in self.df['sla_violation'].value_counts().to_dict().items()}
            },
            'model_performance': convert_numpy_types(self.model_metrics),
            'feature_importance': convert_numpy_types(self.feature_importance),
            'best_model': 'xgboost_tuned',
            'production_ready': True
        }
        
        with open('training_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("Training report saved to training_report.json")
        
        return report

def main():
    """Main training pipeline."""
    print("Starting ML training pipeline...")
    
    # Initialize trainer
    trainer = MLTrainer()
    
    # Load and preprocess data
    trainer.load_and_preprocess_data()
    
    # Train models
    trainer.train_models()
    
    # Train anomaly detection
    trainer.train_anomaly_detection()
    
    # Save models
    trainer.save_models()
    
    # Generate report
    report = trainer.generate_training_report()
    
    print("\\n" + "="*50)
    print("TRAINING COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"Best model: {report['best_model']}")
    print(f"Best accuracy: {report['model_performance'][report['best_model']]['accuracy']:.4f}")
    print(f"Best AUC score: {report['model_performance'][report['best_model']]['auc_score']:.4f}")
    print("="*50)

if __name__ == "__main__":
    main()

