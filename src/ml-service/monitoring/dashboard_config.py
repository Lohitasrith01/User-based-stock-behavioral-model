from grafana_api_client import GrafanaClient
import json

class MLMonitoringDashboard:
    def __init__(self, grafana_url, api_key):
        self.client = GrafanaClient(grafana_url, api_key)
        
    def create_dashboards(self):
        # Model Performance Dashboard
        model_performance = {
            "dashboard": {
                "title": "ML Model Performance",
                "panels": [
                    {
                        "title": "Model Accuracy Over Time",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "model_accuracy{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    },
                    {
                        "title": "Prediction Latency",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "model_prediction_latency_seconds{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    },
                    {
                        "title": "Data Drift Detection",
                        "type": "stat",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "data_drift_detected{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    }
                ]
            }
        }
        
        # Model Metrics Dashboard
        model_metrics = {
            "dashboard": {
                "title": "ML Model Metrics",
                "panels": [
                    {
                        "title": "MSE Over Time",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "model_mse{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    },
                    {
                        "title": "R2 Score",
                        "type": "gauge",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "model_r2_score{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    },
                    {
                        "title": "Anomaly Detection Rate",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "anomaly_detection_rate{model=\"anomaly_detector\"}",
                                "legendFormat": "Anomaly Rate"
                            }
                        ]
                    }
                ]
            }
        }
        
        # System Health Dashboard
        system_health = {
            "dashboard": {
                "title": "ML System Health",
                "panels": [
                    {
                        "title": "CPU Usage",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "process_cpu_seconds_total{job=\"ml_service\"}",
                                "legendFormat": "CPU Usage"
                            }
                        ]
                    },
                    {
                        "title": "Memory Usage",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "process_resident_memory_bytes{job=\"ml_service\"}",
                                "legendFormat": "Memory Usage"
                            }
                        ]
                    },
                    {
                        "title": "Model Load Time",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "model_load_time_seconds{model=~\"price_predictor|recommender|anomaly_detector\"}",
                                "legendFormat": "{{model}}"
                            }
                        ]
                    }
                ]
            }
        }
        
        # Create dashboards
        self.client.dashboards.create(model_performance)
        self.client.dashboards.create(model_metrics)
        self.client.dashboards.create(system_health) 