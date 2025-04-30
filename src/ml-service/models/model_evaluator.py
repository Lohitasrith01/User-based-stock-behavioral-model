import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
import logging

class ModelEvaluator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history = {}
        
    def evaluate_regression(self, y_true, y_pred, model_name):
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }
        
        self._update_metrics_history(model_name, metrics)
        return metrics
        
    def detect_drift(self, model_name, current_data, historical_data, threshold=0.05):
        # Calculate distribution statistics
        current_stats = self._calculate_distribution_stats(current_data)
        historical_stats = self._calculate_distribution_stats(historical_data)
        
        # Perform Kolmogorov-Smirnov test
        ks_statistic, p_value = stats.ks_2samp(current_data, historical_data)
        
        drift_detected = p_value < threshold
        
        if drift_detected:
            self.logger.warning(f"Data drift detected for model {model_name}")
            
        return {
            'drift_detected': drift_detected,
            'ks_statistic': ks_statistic,
            'p_value': p_value,
            'current_stats': current_stats,
            'historical_stats': historical_stats
        }
        
    def _calculate_distribution_stats(self, data):
        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'skew': stats.skew(data),
            'kurtosis': stats.kurtosis(data)
        }
        
    def _update_metrics_history(self, model_name, metrics):
        if model_name not in self.metrics_history:
            self.metrics_history[model_name] = []
            
        self.metrics_history[model_name].append({
            'timestamp': pd.Timestamp.now(),
            'metrics': metrics
        })
        
    def get_metrics_history(self, model_name):
        return self.metrics_history.get(model_name, [])
        
    def plot_metrics_trend(self, model_name, metric_name):
        if model_name not in self.metrics_history:
            return None
            
        history = self.metrics_history[model_name]
        timestamps = [h['timestamp'] for h in history]
        values = [h['metrics'][metric_name] for h in history]
        
        return pd.Series(values, index=timestamps) 