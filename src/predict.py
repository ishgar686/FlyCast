import pickle
import argparse
import os
from datetime import datetime
from typing import Optional, Any, Dict, List
from scraper import FlightDataFetcher
import pandas as pd

def load_model(model_path: str = 'model.pkl') -> tuple[Optional[Any], Dict[str, Any]]:
    """Load the trained machine learning model and encoders."""
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Handle different model save formats
        if isinstance(model_data, dict):
            # If model was saved with encoders and other data
            model = model_data.get('model')
            encoders = model_data.get('encoders', {})
            print(f"Model and encoders loaded successfully from {model_path}")
            return model, encoders
        else:
            # If only the model was saved
            print(f"Model loaded successfully from {model_path}")
            return model_data, {}
            
    except FileNotFoundError:
        print(f"Model file {model_path} not found. Please run train_model.py first.")
        return None, {}
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, {}

def preprocess_flight_data(flight_data: Dict[str, Any], encoders: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Preprocess flight data to match model's expected features."""
    try:
        # Extract basic features
        origin = flight_data.get('origin', 'Unknown')
        destination = flight_data.get('destination', 'Unknown')
        airline = flight_data.get('airline', 'Unknown')
        scheduled_departure = flight_data.get('scheduled_departure', 'Unknown')
        
        # Parse scheduled departure time
        if scheduled_departure != 'Unknown':
            try:
                # Handle ISO format: "2025-07-08T15:00:00+00:00"
                dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                hour = dt.hour
                weekday = dt.weekday()  # 0=Monday, 6=Sunday
            except:
                print("Warning: Could not parse scheduled departure time, using defaults")
                hour = 12
                weekday = 0
        else:
            hour = 12
            weekday = 0
        
        # Encode categorical variables if encoders are available
        if encoders and isinstance(encoders, dict):
            origin_encoded = encoders.get('origin', {}).get(origin, 0)
            destination_encoded = encoders.get('destination', {}).get(destination, 0)
            airline_encoded = encoders.get('airline', {}).get(airline, 0)
        else:
            # Fallback: use simple integer encoding
            origin_encoded = hash(origin) % 1000
            destination_encoded = hash(destination) % 1000
            airline_encoded = hash(airline) % 1000
        
        # Return features in the order expected by the model
        features = [
            origin_encoded,
            destination_encoded,
            airline_encoded,
            hour,
            weekday
        ]
        
        print(f"Preprocessed features: origin={origin}({origin_encoded}), "
              f"destination={destination}({destination_encoded}), "
              f"airline={airline}({airline_encoded}), hour={hour}, weekday={weekday}")
        
        return features
        
    except Exception as e:
        print(f"Error preprocessing flight data: {e}")
        return [0, 0, 0, 12, 0]  # Return default features instead of None

def predict_delay(model: Any, flight_data: Dict[str, Any], encoders: Optional[Dict[str, Any]] = None) -> float:
    """Predict flight delay using the trained model."""
    try:
        # Preprocess the flight data
        features = preprocess_flight_data(flight_data, encoders)
        
        if features is None:
            print("Failed to preprocess flight data")
            return 0
        
        # Make prediction
        prediction = model.predict([features])[0]
        
        return prediction
        
    except Exception as e:
        print(f"Error making prediction: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Predict flight delays using trained model')
    parser.add_argument('flight_number', help='Flight number (e.g., WN673)')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API')
    parser.add_argument('--model', default='model.pkl', help='Path to trained model file')
    
    args = parser.parse_args()
    
    # Load the trained model and encoders
    model, encoders = load_model(args.model)
    if model is None:
        return
    
    # Fetch flight data
    try:
        fetcher = FlightDataFetcher(mock_mode=args.mock)
        flight_data = fetcher.get_flight_info(args.flight_number)
        
        if flight_data is None:
            print("Failed to fetch flight data")
            return
        
        print("\nFlight Information:")
        for key, value in flight_data.items():
            print(f"  {key}: {value}")
        
        # Make prediction
        print("\nMaking delay prediction...")
        delay_prediction = predict_delay(model, flight_data, encoders)
        
        if delay_prediction is not None:
            print(f"\nPredicted Delay: {delay_prediction:.2f} minutes")
            
            if delay_prediction > 0:
                print(f"Status: DELAYED ({delay_prediction:.2f} minutes late)")
            elif delay_prediction < 0:
                print(f"Status: EARLY ({abs(delay_prediction):.2f} minutes early)")
            else:
                print("Status: ON TIME")
        else:
            print("Failed to make prediction")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 