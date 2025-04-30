import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class TradingAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
    def prepare_features(self, trading_data):
        # Extract relevant features
        features = pd.DataFrame({
            'volume': trading_data['volume'],
            'price_change': trading_data['price_change'],
            'trade_frequency': trading_data['trade_frequency'],
            'order_size': trading_data['order_size']
        })
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        return scaled_features
        
    def train(self, historical_trading_data):
        # Prepare features
        X = self.prepare_features(historical_trading_data)
        
        # Train the model
        self.model.fit(X)
        
    def detect_anomalies(self, trading_data):
        # Prepare features
        X = self.prepare_features(trading_data)
        
        # Predict anomalies
        predictions = self.model.predict(X)
        
        # Convert predictions to boolean (True for anomalies)
        anomalies = predictions == -1
        
        # Calculate anomaly scores
        scores = self.model.score_samples(X)
        
        return {
            'is_anomaly': anomalies,
            'anomaly_score': scores
        }
        
    def get_anomaly_details(self, trading_data):
        results = self.detect_anomalies(trading_data)
        
        # Get details of anomalous trades
        anomaly_details = []
        for i, is_anomaly in enumerate(results['is_anomaly']):
            if is_anomaly:
                anomaly_details.append({
                    'trade_id': trading_data.iloc[i]['trade_id'],
                    'timestamp': trading_data.iloc[i]['timestamp'],
                    'score': results['anomaly_score'][i],
                    'details': {
                        'volume': trading_data.iloc[i]['volume'],
                        'price_change': trading_data.iloc[i]['price_change'],
                        'trade_frequency': trading_data.iloc[i]['trade_frequency'],
                        'order_size': trading_data.iloc[i]['order_size']
                    }
                })
                
        return anomaly_details 