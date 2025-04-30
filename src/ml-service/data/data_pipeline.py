import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import sqlite3
import json

class DataPipeline:
    def __init__(self, config_path: str = "../config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self._setup_nltk()
        self.db_path = "data/market_data.db"
        self._init_database()
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
            
    def _setup_nltk(self):
        """Download required NLTK data."""
        nltk.download('vader_lexicon')
        self.sia = SentimentIntensityAnalyzer()
        
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                date TEXT,
                symbol TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (date, symbol)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sentiment (
                date TEXT,
                symbol TEXT,
                title TEXT,
                sentiment_score REAL,
                source TEXT,
                PRIMARY KEY (date, symbol, title)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_volume (
                date TEXT,
                symbol TEXT,
                volume INTEGER,
                trades INTEGER,
                avg_trade_size REAL,
                PRIMARY KEY (date, symbol)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def collect_stock_data(self, symbols: List[str], start_date: Optional[str] = None):
        """Collect historical stock data using yfinance."""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(start=start_date)
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                hist.to_sql('stock_prices', conn, if_exists='append', index=True)
                conn.close()
                
                self.logger.info(f"Collected data for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
                
    def collect_news_sentiment(self, symbols: List[str]):
        """Collect and analyze news sentiment for stocks."""
        for symbol in symbols:
            try:
                # Get news from multiple sources
                news_data = self._get_news_data(symbol)
                
                # Analyze sentiment
                for news in news_data:
                    sentiment = self.sia.polarity_scores(news['title'])
                    
                    # Store in database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO news_sentiment 
                        (date, symbol, title, sentiment_score, source)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        news['date'],
                        symbol,
                        news['title'],
                        sentiment['compound'],
                        news['source']
                    ))
                    conn.commit()
                    conn.close()
                    
            except Exception as e:
                self.logger.error(f"Error collecting news for {symbol}: {str(e)}")
                
    def _get_news_data(self, symbol: str) -> List[Dict]:
        """Get news data from various sources."""
        news_data = []
        
        # Example: Get news from Yahoo Finance
        try:
            stock = yf.Ticker(symbol)
            news = stock.news
            
            for item in news:
                news_data.append({
                    'date': datetime.fromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d'),
                    'title': item['title'],
                    'source': item['publisher']
                })
                
        except Exception as e:
            self.logger.error(f"Error getting news from Yahoo Finance: {str(e)}")
            
        return news_data
        
    def process_trading_data(self, symbols: List[str]):
        """Process and aggregate trading data."""
        for symbol in symbols:
            try:
                # Get raw trading data
                conn = sqlite3.connect(self.db_path)
                df = pd.read_sql_query(
                    f"SELECT * FROM stock_prices WHERE symbol = '{symbol}'",
                    conn
                )
                
                # Calculate trading metrics
                trading_metrics = {
                    'date': df['date'],
                    'symbol': symbol,
                    'volume': df['volume'],
                    'trades': df['volume'] / df['volume'].mean(),  # Approximate number of trades
                    'avg_trade_size': df['volume'] * df['close'] / (df['volume'] / df['volume'].mean())
                }
                
                # Store in database
                pd.DataFrame(trading_metrics).to_sql(
                    'trading_volume',
                    conn,
                    if_exists='append',
                    index=False
                )
                conn.close()
                
            except Exception as e:
                self.logger.error(f"Error processing trading data for {symbol}: {str(e)}")
                
    def get_training_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Get processed data for model training."""
        conn = sqlite3.connect(self.db_path)
        
        # Get stock prices
        prices_df = pd.read_sql_query(
            f"""
            SELECT * FROM stock_prices 
            WHERE symbol = '{symbol}' 
            AND date BETWEEN '{start_date}' AND '{end_date}'
            """,
            conn
        )
        
        # Get news sentiment
        sentiment_df = pd.read_sql_query(
            f"""
            SELECT date, AVG(sentiment_score) as avg_sentiment 
            FROM news_sentiment 
            WHERE symbol = '{symbol}' 
            AND date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY date
            """,
            conn
        )
        
        # Get trading volume
        volume_df = pd.read_sql_query(
            f"""
            SELECT * FROM trading_volume 
            WHERE symbol = '{symbol}' 
            AND date BETWEEN '{start_date}' AND '{end_date}'
            """,
            conn
        )
        
        conn.close()
        
        # Merge all data
        merged_data = prices_df.merge(sentiment_df, on='date', how='left')
        merged_data = merged_data.merge(volume_df, on=['date', 'symbol'], how='left')
        
        return {
            'prices': merged_data['close'].values,
            'sentiment': merged_data['avg_sentiment'].fillna(0).values,
            'volume': merged_data['volume'].values,
            'trades': merged_data['trades'].values,
            'dates': merged_data['date'].values
        }
        
    def run_pipeline(self, symbols: List[str]):
        """Run the complete data pipeline."""
        self.logger.info("Starting data pipeline...")
        
        # Collect data
        self.collect_stock_data(symbols)
        self.collect_news_sentiment(symbols)
        
        # Process data
        self.process_trading_data(symbols)
        
        self.logger.info("Data pipeline completed successfully") 