import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class StockRecommender:
    def __init__(self):
        self.user_stock_matrix = None
        self.stock_features = None
        self.vectorizer = TfidfVectorizer()
        
    def prepare_data(self, user_history, stock_data):
        # Create user-stock interaction matrix
        self.user_stock_matrix = pd.DataFrame(user_history)
        
        # Prepare stock features
        stock_descriptions = [f"{data['sector']} {data['industry']} {data['description']}" 
                            for data in stock_data]
        self.stock_features = self.vectorizer.fit_transform(stock_descriptions)
        
    def get_user_recommendations(self, user_id, n_recommendations=5):
        if user_id not in self.user_stock_matrix.index:
            return []
            
        # Get user's stock preferences
        user_preferences = self.user_stock_matrix.loc[user_id]
        
        # Calculate similarity between user preferences and stock features
        user_vector = self.vectorizer.transform([user_preferences])
        similarities = cosine_similarity(user_vector, self.stock_features)
        
        # Get top N recommendations
        top_indices = similarities[0].argsort()[-n_recommendations:][::-1]
        recommendations = [self.user_stock_matrix.columns[i] for i in top_indices]
        
        return recommendations
    
    def get_similar_stocks(self, stock_id, n_recommendations=5):
        if stock_id not in self.user_stock_matrix.columns:
            return []
            
        # Get stock features
        stock_idx = self.user_stock_matrix.columns.get_loc(stock_id)
        stock_vector = self.stock_features[stock_idx]
        
        # Calculate similarity with other stocks
        similarities = cosine_similarity(stock_vector, self.stock_features)
        
        # Get top N similar stocks
        top_indices = similarities[0].argsort()[-n_recommendations-1:][::-1]
        similar_stocks = [self.user_stock_matrix.columns[i] for i in top_indices 
                         if i != stock_idx]
        
        return similar_stocks[:n_recommendations] 