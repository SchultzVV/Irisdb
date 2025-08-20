"""
Iris Pipeline Monitoring Utilities
Provides ElasticSearch logging and Teams notifications for the MLOps pipeline
"""

import json
import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pyspark.sql import SparkSession
import os

class TeamsNotifier:
    """
    Microsoft Teams webhook notifier for pipeline events
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def send_notification(self, title: str, message: str, color: str = "0078d4", facts: Optional[Dict] = None):
        """
        Send notification to Teams channel
        
        Args:
            title: Notification title
            message: Main message content
            color: Hex color code (blue=0078d4, green=36c5f0, red=e74c3c)
            facts: Additional key-value pairs to display
        """
        try:
            facts_list = []
            if facts:
                for key, value in facts.items():
                    facts_list.append({"name": key, "value": str(value)})
            
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": color,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": f"Iris MLOps Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "text": message,
                    "facts": facts_list
                }]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Teams notification sent: {title}")
            else:
                print(f"❌ Failed to send Teams notification: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending Teams notification: {str(e)}")

class PipelineMonitor:
    """
    Central monitoring class for the Iris ML pipeline
    """
    
    def __init__(self, spark: SparkSession, elasticsearch_host: str = None, teams_webhook: str = None):
        self.spark = spark
        self.elasticsearch_host = elasticsearch_host
        self.teams_webhook = teams_webhook
        self.teams_notifier = TeamsNotifier(teams_webhook) if teams_webhook else None
        
        # Setup logging
        self.logger = logging.getLogger("iris.monitoring")
        self.logger.setLevel(logging.INFO)
        
        # Create metrics logger
        self.metrics_logger = logging.getLogger("iris.metrics")
        self.metrics_logger.setLevel(logging.INFO)
        
    def log_pipeline_start(self, pipeline_name: str, parameters: Dict[str, Any] = None):
        """Log pipeline start event"""
        message = f"Pipeline {pipeline_name} started"
        self.logger.info(message)
        
        if self.teams_notifier:
            facts = {
                "Pipeline": pipeline_name,
                "Status": "Started",
                "Timestamp": datetime.now().isoformat()
            }
            if parameters:
                facts.update(parameters)
                
            self.teams_notifier.send_notification(
                title=f"🚀 Pipeline Started: {pipeline_name}",
                message=message,
                color="0078d4",  # Blue
                facts=facts
            )
    
    def log_pipeline_success(self, pipeline_name: str, metrics: Dict[str, Any] = None):
        """Log pipeline success event"""
        message = f"Pipeline {pipeline_name} completed successfully"
        self.logger.info(message)
        
        if metrics:
            # Log metrics
            for key, value in metrics.items():
                self.metrics_logger.info(f"{key}={value}")
        
        if self.teams_notifier:
            facts = {
                "Pipeline": pipeline_name,
                "Status": "Success",
                "Timestamp": datetime.now().isoformat()
            }
            if metrics:
                facts.update({k: str(v) for k, v in metrics.items()})
                
            self.teams_notifier.send_notification(
                title=f"✅ Pipeline Success: {pipeline_name}",
                message=message,
                color="36c5f0",  # Green
                facts=facts
            )
    
    def log_pipeline_error(self, pipeline_name: str, error: str, details: Dict[str, Any] = None):
        """Log pipeline error event"""
        message = f"Pipeline {pipeline_name} failed: {error}"
        self.logger.error(message)
        
        if self.teams_notifier:
            facts = {
                "Pipeline": pipeline_name,
                "Status": "Failed",
                "Error": error,
                "Timestamp": datetime.now().isoformat()
            }
            if details:
                facts.update({k: str(v) for k, v in details.items()})
                
            self.teams_notifier.send_notification(
                title=f"❌ Pipeline Failed: {pipeline_name}",
                message=message,
                color="e74c3c",  # Red
                facts=facts
            )
    
    def log_data_quality_check(self, table_name: str, passed: bool, checks: Dict[str, Any]):
        """Log data quality check results"""
        status = "PASSED" if passed else "FAILED"
        message = f"Data quality check for {table_name}: {status}"
        
        if passed:
            self.logger.info(message)
        else:
            self.logger.warning(message)
        
        # Log individual check metrics
        for check_name, result in checks.items():
            self.metrics_logger.info(f"data_quality.{table_name}.{check_name}={result}")
        
        if self.teams_notifier and not passed:
            facts = {
                "Table": table_name,
                "Status": status,
                "Timestamp": datetime.now().isoformat()
            }
            facts.update({f"Check_{k}": str(v) for k, v in checks.items()})
            
            self.teams_notifier.send_notification(
                title=f"⚠️ Data Quality Alert: {table_name}",
                message=message,
                color="e74c3c",  # Red
                facts=facts
            )
    
    def log_model_metrics(self, model_name: str, metrics: Dict[str, float]):
        """Log model performance metrics"""
        message = f"Model metrics logged for {model_name}"
        self.logger.info(message)
        
        # Log individual metrics
        for metric_name, value in metrics.items():
            self.metrics_logger.info(f"model.{model_name}.{metric_name}={value}")
        
        if self.teams_notifier:
            facts = {
                "Model": model_name,
                "Timestamp": datetime.now().isoformat()
            }
            facts.update({k: f"{v:.4f}" for k, v in metrics.items()})
            
            self.teams_notifier.send_notification(
                title=f"📊 Model Metrics: {model_name}",
                message=message,
                color="0078d4",  # Blue
                facts=facts
            )

def get_pipeline_monitor(spark: SparkSession) -> PipelineMonitor:
    """
    Factory function to create a PipelineMonitor with configuration from environment
    """
    elasticsearch_host = spark.conf.get("spark.iris.elasticsearch.host", None)
    teams_webhook = spark.conf.get("spark.iris.teams.webhook", None)
    
    return PipelineMonitor(
        spark=spark,
        elasticsearch_host=elasticsearch_host,
        teams_webhook=teams_webhook
    )

# Decorator for monitoring pipeline functions
def monitor_pipeline(pipeline_name: str):
    """
    Decorator to automatically monitor pipeline execution
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            spark = None
            # Try to get spark from args or kwargs
            for arg in args:
                if isinstance(arg, SparkSession):
                    spark = arg
                    break
            
            if spark is None and 'spark' in kwargs:
                spark = kwargs['spark']
            
            if spark is None:
                # Fallback: create or get existing spark session
                spark = SparkSession.getActiveSession()
                if spark is None:
                    spark = SparkSession.builder.appName("iris_monitoring").getOrCreate()
            
            monitor = get_pipeline_monitor(spark)
            
            try:
                monitor.log_pipeline_start(pipeline_name)
                start_time = time.time()
                
                result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                metrics = {"execution_time_seconds": execution_time}
                
                monitor.log_pipeline_success(pipeline_name, metrics)
                return result
                
            except Exception as e:
                monitor.log_pipeline_error(pipeline_name, str(e))
                raise
        
        return wrapper
    return decorator
