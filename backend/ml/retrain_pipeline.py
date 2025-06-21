"""
Automatic model retraining pipeline for the SLA Violation Prediction platform.
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from backend.app.database import SessionLocal, get_db
from backend.app.models import Telemetry, ModelMetrics
from backend.ml.train import MLTrainer
from backend.ml.predictor import MLPredictor
import json
import os

logger = logging.getLogger(__name__)

class AutoRetrainPipeline:
    """Automatic model retraining pipeline."""
    
    def __init__(self, min_new_samples=100, retrain_interval_hours=24):
        self.min_new_samples = min_new_samples
        self.retrain_interval_hours = retrain_interval_hours
        self.last_retrain_time = None
        self.is_retraining = False
        
    def should_retrain(self, db: Session) -> bool:
        """Check if model should be retrained."""
        if self.is_retraining:
            return False
            
        # Check if enough time has passed
        if self.last_retrain_time:
            time_since_last = datetime.utcnow() - self.last_retrain_time
            if time_since_last.total_seconds() < self.retrain_interval_hours * 3600:
                return False
        
        # Check if we have enough new data
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retrain_interval_hours)
        new_samples_count = db.query(Telemetry).filter(
            Telemetry.created_at >= cutoff_time
        ).count()
        
        logger.info(f"Found {new_samples_count} new samples since {cutoff_time}")
        
        return new_samples_count >= self.min_new_samples
    
    async def retrain_models(self, db: Session) -> Dict[str, Any]:
        """Retrain ML models with new data."""
        if self.is_retraining:
            return {"status": "already_retraining"}
            
        self.is_retraining = True
        retrain_start_time = datetime.utcnow()
        
        try:
            logger.info("Starting automatic model retraining...")
            
            # Export recent telemetry data to CSV
            await self._export_telemetry_data(db)
            
            # Initialize trainer with new data
            trainer = MLTrainer('retrain_dataset.csv')
            
            # Load and preprocess data
            trainer.load_and_preprocess_data()
            
            # Train models
            trainer.train_models()
            trainer.train_anomaly_detection()
            
            # Save models with timestamp
            timestamp = retrain_start_time.strftime("%Y%m%d_%H%M%S")
            trainer.save_models_with_timestamp(timestamp)
            
            # Generate training report
            report = trainer.generate_training_report()
            
            # Update model metrics in database
            await self._save_model_metrics(db, report, retrain_start_time)
            
            # Update last retrain time
            self.last_retrain_time = retrain_start_time
            
            logger.info("Model retraining completed successfully")
            
            return {
                "status": "success",
                "retrain_time": retrain_start_time.isoformat(),
                "best_model": report.get('best_model'),
                "accuracy": report.get('model_performance', {}).get(report.get('best_model'), {}).get('accuracy'),
                "training_samples": report.get('dataset_info', {}).get('total_samples')
            }
            
        except Exception as e:
            logger.error(f"Error during model retraining: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "retrain_time": retrain_start_time.isoformat()
            }
        finally:
            self.is_retraining = False
    
    async def _export_telemetry_data(self, db: Session):
        """Export telemetry data to CSV for retraining."""
        # Get recent telemetry data (last 30 days or 10000 records, whichever is smaller)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        telemetry_data = db.query(Telemetry).filter(
            Telemetry.created_at >= cutoff_time
        ).limit(10000).all()
        
        # Convert to DataFrame
        data_list = []
        for record in telemetry_data:
            data_list.append({
                'timestamp': record.timestamp.isoformat() if record.timestamp else datetime.utcnow().isoformat(),
                'bandwidth': record.bandwidth,
                'throughput': record.throughput,
                'congestion': record.congestion,
                'packet_loss': record.packet_loss,
                'latency': record.latency,
                'jitter': record.jitter,
                'Routers': record.routers or 'up xrv6',
                'Planned route': record.planned_route or 'Best effort',
                'Network measure': record.network_measure or 'S1',
                'Network target': record.network_target or 'S2',
                'Video target': record.video_target or '',
                'Percentage video occupancy': record.percentage_video_occupancy or 0,
                'Bitrate video': record.bitrate_video or 0,
                'Number videos': record.number_videos or 0
            })
        
        df = pd.DataFrame(data_list)
        df.to_csv('retrain_dataset.csv', index=False)
        
        logger.info(f"Exported {len(data_list)} records for retraining")
    
    async def _save_model_metrics(self, db: Session, report: Dict[str, Any], retrain_time: datetime):
        """Save model metrics to database."""
        try:
            best_model = report.get('best_model', 'xgboost_tuned')
            model_performance = report.get('model_performance', {}).get(best_model, {})
            feature_importance = report.get('feature_importance', {}).get(best_model, {})
            
            model_metrics = ModelMetrics(
                model_name=best_model,
                model_version=retrain_time.strftime("%Y%m%d_%H%M%S"),
                accuracy=model_performance.get('accuracy'),
                precision=model_performance.get('precision'),
                recall=model_performance.get('recall'),
                f1_score=model_performance.get('f1_score'),
                auc_score=model_performance.get('auc_score'),
                training_data_size=model_performance.get('training_data_size'),
                feature_importance=json.dumps(feature_importance)
            )
            
            db.add(model_metrics)
            db.commit()
            
            logger.info("Model metrics saved to database")
            
        except Exception as e:
            logger.error(f"Error saving model metrics: {str(e)}")
            db.rollback()

class RetrainScheduler:
    """Scheduler for automatic model retraining."""
    
    def __init__(self):
        self.pipeline = AutoRetrainPipeline()
        self.is_running = False
    
    def start_scheduler(self):
        """Start the retraining scheduler."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Schedule retraining every 24 hours
        schedule.every(24).hours.do(self._run_retrain_check)
        
        # Also schedule a check every hour for immediate retraining needs
        schedule.every().hour.do(self._run_retrain_check)
        
        logger.info("Retraining scheduler started")
        
        # Run scheduler in background
        asyncio.create_task(self._scheduler_loop())
    
    def stop_scheduler(self):
        """Stop the retraining scheduler."""
        self.is_running = False
        schedule.clear()
        logger.info("Retraining scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def _run_retrain_check(self):
        """Check if retraining is needed and run it."""
        asyncio.create_task(self._async_retrain_check())
    
    async def _async_retrain_check(self):
        """Async wrapper for retrain check."""
        db = SessionLocal()
        try:
            if self.pipeline.should_retrain(db):
                logger.info("Triggering automatic model retraining")
                result = await self.pipeline.retrain_models(db)
                logger.info(f"Retraining result: {result}")
            else:
                logger.debug("Retraining not needed at this time")
        except Exception as e:
            logger.error(f"Error in retrain check: {str(e)}")
        finally:
            db.close()
    
    async def manual_retrain(self) -> Dict[str, Any]:
        """Manually trigger model retraining."""
        db = SessionLocal()
        try:
            logger.info("Manual retraining triggered")
            result = await self.pipeline.retrain_models(db)
            return result
        finally:
            db.close()

# Global scheduler instance
retrain_scheduler = RetrainScheduler()

def start_retrain_scheduler():
    """Start the global retraining scheduler."""
    retrain_scheduler.start_scheduler()

def stop_retrain_scheduler():
    """Stop the global retraining scheduler."""
    retrain_scheduler.stop_scheduler()

async def trigger_manual_retrain() -> Dict[str, Any]:
    """Trigger manual retraining."""
    return await retrain_scheduler.manual_retrain()

if __name__ == "__main__":
    # For testing the retraining pipeline
    import asyncio
    
    async def test_retrain():
        scheduler = RetrainScheduler()
        result = await scheduler.manual_retrain()
        print(f"Retraining result: {result}")
    
    asyncio.run(test_retrain())

