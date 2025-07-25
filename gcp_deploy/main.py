from flask import Flask, request, jsonify
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.predict import load_model, predict_delay
from src.scraper import FlightDataFetcher

app = Flask(__name__)

# Load model and encoders once on startup
MODEL_PATH = os.path.join("model", "model.pkl")
model, encoders = load_model(MODEL_PATH)

# Set path to mock flight data
MOCK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mock_flights'))

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    flight_number = data.get("flight_number")
    use_mock = data.get("mock", False)

    if not flight_number:
        return jsonify({"error": "Missing flight_number"}), 400

    fetcher = FlightDataFetcher(mock_mode=use_mock, mock_dir=MOCK_DIR)
    flight_data = fetcher.get_flight_info(flight_number)

    if flight_data is None:
        return jsonify({"error": "Could not fetch flight data"}), 500

    delay = predict_delay(model, flight_data, encoders)

    if delay < 0:
        status = f"~{abs(delay):.0f} min early (EARLY)"
    elif delay < 10:
        status = f"~{delay:.0f} min late (ON TIME)"
    else:
        status = f"~{delay:.0f} min late (DELAYED)"

    return jsonify({
        "flight_number": flight_number,
        "predicted_delay_minutes": round(delay, 2),
        "status": status
    })
