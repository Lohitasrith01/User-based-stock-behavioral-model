from flask import Flask, request, jsonify
import json
import requests
import numpy as np
import pandas as pd
from models.price_predictor import StockPricePredictor
from models.recommender import StockRecommender
from models.anomaly_detector import TradingAnomalyDetector

app = Flask(__name__)

# Initialize ML models
price_predictor = StockPricePredictor()
stock_recommender = StockRecommender()
anomaly_detector = TradingAnomalyDetector()

# Load configuration
with open('../config.json', 'r') as file:
    config = json.load(file)

# API endpoint for price predictions
@app.get("/ml/predictions/<stock_name>")
def get_price_prediction(stock_name):
    try:
        # Get historical data from catalog service
        catalog_host = config['catalog']['host']
        catalog_port = str(config['catalog']['port'])
        url = f'http://{catalog_host}:{catalog_port}/catalog/{stock_name}'
        
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch stock data'}), 400
            
        stock_data = response.json()
        historical_prices = np.array(stock_data['data']['prices'])
        
        # Make prediction
        prediction = price_predictor.predict(historical_prices)
        
        return jsonify({
            'stock_name': stock_name,
            'predicted_price': float(prediction),
            'confidence': 0.85  # This could be calculated based on model metrics
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for stock recommendations
@app.get("/ml/recommendations")
def get_recommendations():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
            
        # Get user history from order service
        order_host = config['order']['nodes'][0]['host']
        order_port = str(config['order']['nodes'][0]['port'])
        url = f'http://{order_host}:{order_port}/orders/user/{user_id}'
        
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch user history'}), 400
            
        user_history = response.json()
        
        # Get stock data from catalog service
        catalog_host = config['catalog']['host']
        catalog_port = str(config['catalog']['port'])
        url = f'http://{catalog_host}:{catalog_port}/catalog/all'
        
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch stock data'}), 400
            
        stock_data = response.json()
        
        # Get recommendations
        recommendations = stock_recommender.get_user_recommendations(user_id)
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for anomaly detection
@app.post("/ml/anomalies")
def detect_anomalies():
    try:
        trading_data = request.json
        if not trading_data:
            return jsonify({'error': 'Trading data is required'}), 400
            
        # Convert to DataFrame
        df = pd.DataFrame(trading_data)
        
        # Detect anomalies
        anomaly_details = anomaly_detector.get_anomaly_details(df)
        
        return jsonify({
            'anomalies': anomaly_details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000) 