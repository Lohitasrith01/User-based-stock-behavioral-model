import json
import os
from datetime import datetime
import mlflow
import mlflow.sklearn
import mlflow.tensorflow

class ModelRegistry:
    def __init__(self, registry_path="model_registry"):
        self.registry_path = registry_path
        os.makedirs(registry_path, exist_ok=True)
        mlflow.set_tracking_uri(f"file:{registry_path}/mlruns")
        
    def log_model(self, model, model_name, metrics, params):
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params(params)
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            if isinstance(model, mlflow.tensorflow.Model):
                mlflow.tensorflow.log_model(model, model_name)
            else:
                mlflow.sklearn.log_model(model, model_name)
                
            # Save metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "metrics": metrics,
                "parameters": params
            }
            
            with open(f"{self.registry_path}/{model_name}_metadata.json", "w") as f:
                json.dump(metadata, f)
                
    def get_best_model(self, model_name, metric="accuracy"):
        runs = mlflow.search_runs(filter_string=f"tags.model_name = '{model_name}'")
        if runs.empty:
            return None
            
        best_run = runs.loc[runs[f"metrics.{metric}"].idxmax()]
        return mlflow.sklearn.load_model(f"runs:/{best_run.run_id}/{model_name}")
        
    def get_model_metadata(self, model_name):
        try:
            with open(f"{self.registry_path}/{model_name}_metadata.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return None 