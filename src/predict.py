import pickle
import argparse
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from datetime import datetime
from typing import Optional, Any, Dict, List
from scraper import FlightDataFetcher
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

__version__ = "1.0.0"



# Known popular airports (safe list)
KNOWN_AIRPORTS = {
    "SAN", "LAX", "SFO", "SJC", "SEA", "PHX", "DEN", "ORD", "ATL", "DFW", "JFK", "LAS"
}


def load_model(model_path: str = 'model/model.pkl') -> tuple[Optional[Any], Dict[str, Any]]:
    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        if isinstance(model_data, dict):
            model = model_data.get('model')
            encoders = model_data.get('encoders', {})
            return model, encoders
        else:
            return model_data, {}
    except FileNotFoundError:
        print(f"Model file {model_path} not found. Please run train_model.py first.")
        return None, {}
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, {}


def preprocess_flight_data(flight_data: Dict[str, Any], encoders: Optional[Dict[str, Any]] = None) -> List[Any]:
    try:
        origin = flight_data.get('origin', 'Unknown')
        destination = flight_data.get('destination', 'Unknown')
        airline = flight_data.get('airline', 'Unknown')
        scheduled_departure = flight_data.get('scheduled_departure', 'Unknown')

        # Hardcode fallback if origin/destination not in KNOWN_AIRPORTS
        origin = origin if origin in KNOWN_AIRPORTS else 'SAN'
        destination = destination if destination in KNOWN_AIRPORTS else 'SFO'

        if scheduled_departure != 'Unknown':
            try:
                dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
                hour = dt.hour
                weekday = dt.weekday()
            except:
                hour, weekday = 12, 0
        else:
            hour, weekday = 12, 0

        if encoders and isinstance(encoders, dict):
            origin_encoded = encoders.get('origin', {}).get(origin, 0)
            destination_encoded = encoders.get('destination', {}).get(destination, 0)
            airline_encoded = encoders.get('airline', {}).get(airline, 0)
        else:
            origin_encoded = hash(origin) % 1000
            destination_encoded = hash(destination) % 1000
            airline_encoded = hash(airline) % 1000

        return [origin_encoded, destination_encoded, airline_encoded, hour, weekday]
    except Exception as e:
        return [0, 0, 0, 12, 0]


def predict_delay(model: Any, flight_data: Dict[str, Any], encoders: Optional[Dict[str, Any]] = None) -> float:
    try:
        features = preprocess_flight_data(flight_data, encoders)
        return model.predict([features])[0]
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description='Predict flight delays using trained model')
    parser.add_argument('--version', action='store_true', help='Show script version and exit')
    parser.add_argument('flight_number', help='Flight number (e.g., WN673)')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of live API')
    parser.add_argument('--model', default='model.pkl', help='Path to trained model file')
    args = parser.parse_args()
    if args.version:
        print(f"FlyCast Predictor Version: {__version__}")
        return


    model, encoders = load_model(args.model)
    if model is None:
        return

    mock_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_flights'))

    try:
        fetcher = FlightDataFetcher(mock_mode=args.mock, mock_dir=mock_dir)
        flight_data = fetcher.get_flight_info(args.flight_number)

        if flight_data is None:
            print("Failed to fetch flight data")
            return

        delay_prediction = predict_delay(model, flight_data, encoders)
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        RESET = "\033[0m"

        if delay_prediction < 0:
            print(f"{BLUE}Status: ~{abs(delay_prediction):.2f} minutes early (EARLY){RESET}")
        elif delay_prediction < 10:
            print(f"{GREEN}Status: ~{delay_prediction:.2f} minutes late (ON TIME){RESET}")
        else:
            print(f"{YELLOW}Status: ~{delay_prediction:.2f} minutes late (DELAYED){RESET}")


    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
