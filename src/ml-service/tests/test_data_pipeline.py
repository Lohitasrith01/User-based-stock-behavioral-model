import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.data_pipeline import DataPipeline
import sqlite3
import os
import threading
import time

@pytest.fixture
def pipeline():
    """Create a test pipeline instance."""
    return DataPipeline(config_path="test_config.json")

@pytest.fixture
def test_symbols():
    """Return test stock symbols."""
    return ["AAPL", "MSFT"]

@pytest.fixture
def test_dates():
    """Return test date range."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after tests."""
    yield
    if os.path.exists("data/market_data.db"):
        os.remove("data/market_data.db")

def test_database_initialization(pipeline):
    """Test database initialization."""
    assert os.path.exists(pipeline.db_path)
    
    conn = sqlite3.connect(pipeline.db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    assert 'stock_prices' in tables
    assert 'news_sentiment' in tables
    assert 'trading_volume' in tables
    
    conn.close()

def test_collect_stock_data(pipeline, test_symbols, test_dates):
    """Test stock data collection."""
    start_date, _ = test_dates
    pipeline.collect_stock_data(test_symbols, start_date)
    
    conn = sqlite3.connect(pipeline.db_path)
    for symbol in test_symbols:
        df = pd.read_sql_query(
            f"SELECT * FROM stock_prices WHERE symbol = '{symbol}'",
            conn
        )
        assert not df.empty
        assert 'close' in df.columns
        assert 'volume' in df.columns
    conn.close()

def test_collect_news_sentiment(pipeline, test_symbols):
    """Test news sentiment collection."""
    pipeline.collect_news_sentiment(test_symbols)
    
    conn = sqlite3.connect(pipeline.db_path)
    for symbol in test_symbols:
        df = pd.read_sql_query(
            f"SELECT * FROM news_sentiment WHERE symbol = '{symbol}'",
            conn
        )
        assert not df.empty
        assert 'sentiment_score' in df.columns
    conn.close()

def test_process_trading_data(pipeline, test_symbols):
    """Test trading data processing."""
    pipeline.process_trading_data(test_symbols)
    
    conn = sqlite3.connect(pipeline.db_path)
    for symbol in test_symbols:
        df = pd.read_sql_query(
            f"SELECT * FROM trading_volume WHERE symbol = '{symbol}'",
            conn
        )
        assert not df.empty
        assert 'trades' in df.columns
        assert 'avg_trade_size' in df.columns
    conn.close()

def test_get_training_data(pipeline, test_symbols, test_dates):
    """Test training data retrieval."""
    start_date, end_date = test_dates
    data = pipeline.get_training_data(test_symbols[0], start_date, end_date)
    
    assert isinstance(data, dict)
    assert 'prices' in data
    assert 'sentiment' in data
    assert 'volume' in data
    assert 'trades' in data
    assert 'dates' in data
    
    # Check data types
    assert isinstance(data['prices'], np.ndarray)
    assert isinstance(data['sentiment'], np.ndarray)
    assert isinstance(data['volume'], np.ndarray)
    assert isinstance(data['trades'], np.ndarray)
    assert isinstance(data['dates'], np.ndarray)

def test_error_handling(pipeline):
    """Test error handling for invalid inputs."""
    # Test invalid symbol
    with pytest.raises(Exception):
        pipeline.collect_stock_data(["INVALID_SYMBOL"])
    
    # Test invalid date format
    with pytest.raises(Exception):
        pipeline.get_training_data("AAPL", "invalid-date", "2023-12-31")
    
    # Test invalid database path
    pipeline.db_path = "invalid/path.db"
    with pytest.raises(Exception):
        pipeline._init_database()

def test_data_validation(pipeline, test_symbols):
    """Test data validation."""
    # Test data type validation
    with pytest.raises(ValueError):
        pipeline.collect_stock_data([123])  # Invalid symbol type
    
    # Test date range validation
    with pytest.raises(ValueError):
        pipeline.get_training_data("AAPL", "2023-12-31", "2023-01-01")  # Invalid date range
    
    # Test data completeness
    data = pipeline.get_training_data(test_symbols[0], "2023-01-01", "2023-12-31")
    assert not np.isnan(data['prices']).any()
    assert not np.isnan(data['sentiment']).any()
    assert not np.isnan(data['volume']).any()

def test_concurrent_operations(pipeline, test_symbols):
    """Test concurrent operations."""
    def collect_data(symbol):
        pipeline.collect_stock_data([symbol])
        pipeline.collect_news_sentiment([symbol])
        pipeline.process_trading_data([symbol])
    
    # Create multiple threads
    threads = []
    for symbol in test_symbols:
        thread = threading.Thread(target=collect_data, args=(symbol,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify data was collected correctly
    conn = sqlite3.connect(pipeline.db_path)
    for symbol in test_symbols:
        # Check stock prices
        df_prices = pd.read_sql_query(
            f"SELECT * FROM stock_prices WHERE symbol = '{symbol}'",
            conn
        )
        assert not df_prices.empty
        
        # Check news sentiment
        df_news = pd.read_sql_query(
            f"SELECT * FROM news_sentiment WHERE symbol = '{symbol}'",
            conn
        )
        assert not df_news.empty
        
        # Check trading volume
        df_volume = pd.read_sql_query(
            f"SELECT * FROM trading_volume WHERE symbol = '{symbol}'",
            conn
        )
        assert not df_volume.empty
    
    conn.close() 