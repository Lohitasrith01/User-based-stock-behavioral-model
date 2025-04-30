import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

class StockPricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 60  # Number of time steps to look back
        
    def build_model(self, input_shape):
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        self.model = model
        
    def prepare_data(self, data):
        # Scale the data
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
            
        return np.array(X), np.array(y)
    
    def train(self, historical_data):
        # Prepare data
        X, y = self.prepare_data(historical_data)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Build and train model
        self.build_model((X.shape[1], 1))
        self.model.fit(X, y, epochs=50, batch_size=32, verbose=0)
        
    def predict(self, recent_data):
        # Scale the data
        scaled_data = self.scaler.transform(recent_data.reshape(-1, 1))
        
        # Prepare sequence
        X = scaled_data[-self.sequence_length:].reshape(1, self.sequence_length, 1)
        
        # Make prediction
        scaled_prediction = self.model.predict(X)
        prediction = self.scaler.inverse_transform(scaled_prediction)
        
        return prediction[0][0] 