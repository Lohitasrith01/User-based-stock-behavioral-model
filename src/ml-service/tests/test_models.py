import pytest
import numpy as np
import os
import json
from models.price_predictor import PricePredictor
from models.recommender import Recommender
from models.anomaly_detector import AnomalyDetector
from data.data_pipeline import DataPipeline

@pytest.fixture
def data_pipeline():
    """Create a test data pipeline instance."""
    return DataPipeline(config_path="test_config.json")

@pytest.fixture
def price_predictor():
    """Create a test price predictor instance."""
    return PricePredictor()

@pytest.fixture
def recommender():
    """Create a test recommender instance."""
    return Recommender()

@pytest.fixture
def anomaly_detector():
    """Create a test anomaly detector instance."""
    return AnomalyDetector()

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after tests."""
    yield
    # Cleanup model files
    for model_file in ["price_predictor.json", "recommender.json", "anomaly_detector.json"]:
        if os.path.exists(f"models/{model_file}"):
            os.remove(f"models/{model_file}")

def test_price_prediction(price_predictor, data_pipeline):
    """Test price prediction functionality."""
    # Get test data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Test prediction
    prediction = price_predictor.predict(data)
    
    assert isinstance(prediction, dict)
    assert 'predicted_price' in prediction
    assert 'confidence' in prediction
    assert 0 <= prediction['confidence'] <= 1
    assert prediction['predicted_price'] > 0

def test_recommendations(recommender, data_pipeline):
    """Test stock recommendations."""
    # Test user recommendations
    user_id = "test_user"
    recommendations = recommender.get_recommendations(user_id)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    for rec in recommendations:
        assert 'symbol' in rec
        assert 'score' in rec
        assert 0 <= rec['score'] <= 1

def test_anomaly_detection(anomaly_detector, data_pipeline):
    """Test anomaly detection."""
    # Get test data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Test anomaly detection
    anomalies = anomaly_detector.detect(data)
    
    assert isinstance(anomalies, list)
    for anomaly in anomalies:
        assert 'timestamp' in anomaly
        assert 'score' in anomaly
        assert 'type' in anomaly
        assert 0 <= anomaly['score'] <= 1

def test_model_training(price_predictor, recommender, anomaly_detector, data_pipeline):
    """Test model training functionality."""
    # Get training data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Test training
    price_predictor.train(data)
    recommender.train(data)
    anomaly_detector.train(data)
    
    # Verify models are trained
    assert price_predictor.is_trained
    assert recommender.is_trained
    assert anomaly_detector.is_trained

def test_model_evaluation(price_predictor, recommender, anomaly_detector, data_pipeline):
    """Test model evaluation metrics."""
    # Get test data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Test evaluation metrics
    price_metrics = price_predictor.evaluate(data)
    rec_metrics = recommender.evaluate(data)
    anomaly_metrics = anomaly_detector.evaluate(data)
    
    # Check price prediction metrics
    assert 'mse' in price_metrics
    assert 'mae' in price_metrics
    assert 'r2' in price_metrics
    
    # Check recommendation metrics
    assert 'precision' in rec_metrics
    assert 'recall' in rec_metrics
    assert 'ndcg' in rec_metrics
    
    # Check anomaly detection metrics
    assert 'f1_score' in anomaly_metrics
    assert 'precision' in anomaly_metrics
    assert 'recall' in anomaly_metrics

def test_model_persistence(price_predictor, recommender, anomaly_detector, data_pipeline):
    """Test model persistence."""
    # Get training data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Train models
    price_predictor.train(data)
    recommender.train(data)
    anomaly_detector.train(data)
    
    # Save models
    price_predictor.save("models/price_predictor.json")
    recommender.save("models/recommender.json")
    anomaly_detector.save("models/anomaly_detector.json")
    
    # Verify files exist
    assert os.path.exists("models/price_predictor.json")
    assert os.path.exists("models/recommender.json")
    assert os.path.exists("models/anomaly_detector.json")
    
    # Load models
    new_price_predictor = PricePredictor()
    new_recommender = Recommender()
    new_anomaly_detector = AnomalyDetector()
    
    new_price_predictor.load("models/price_predictor.json")
    new_recommender.load("models/recommender.json")
    new_anomaly_detector.load("models/anomaly_detector.json")
    
    # Verify models are loaded
    assert new_price_predictor.is_trained
    assert new_recommender.is_trained
    assert new_anomaly_detector.is_trained

def test_model_versioning(price_predictor, data_pipeline):
    """Test model versioning."""
    # Get training data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Train model
    price_predictor.train(data)
    
    # Save model with version
    version = "1.0.0"
    price_predictor.save(f"models/price_predictor_v{version}.json")
    
    # Verify version file exists
    assert os.path.exists(f"models/price_predictor_v{version}.json")
    
    # Load model with version
    new_price_predictor = PricePredictor()
    new_price_predictor.load(f"models/price_predictor_v{version}.json")
    
    # Verify model is loaded
    assert new_price_predictor.is_trained
    assert new_price_predictor.version == version

def test_model_retraining(price_predictor, data_pipeline):
    """Test model retraining."""
    # Get initial training data
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-06-30"
    initial_data = data_pipeline.get_training_data(symbol, start_date, end_date)
    
    # Train model
    price_predictor.train(initial_data)
    initial_metrics = price_predictor.evaluate(initial_data)
    
    # Get new training data
    new_start_date = "2023-07-01"
    new_end_date = "2023-12-31"
    new_data = data_pipeline.get_training_data(symbol, new_start_date, new_end_date)
    
    # Retrain model
    price_predictor.retrain(new_data)
    new_metrics = price_predictor.evaluate(new_data)
    
    # Verify metrics have changed
    assert initial_metrics['mse'] != new_metrics['mse']
    assert initial_metrics['mae'] != new_metrics['mae']
    assert initial_metrics['r2'] != new_metrics['r2'] 