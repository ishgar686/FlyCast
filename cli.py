import re
import subprocess
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def main():
    pattern = r"^[A-Z]{2,3}\d{1,4}$"  # Airline code (2–3 letters) + flight number (1–4 digits)

    flight_number = input("Enter flight number (e.g., WN1254): ").strip().upper()

    if not re.match(pattern, flight_number):
        print("⚠️  Invalid flight number format. Please enter something like 'WN1254'.")
        return

    subprocess.run([
        "python", "src/predict.py",
        flight_number,
        "--mock",
        "--model", "model/model.pkl"
    ])

    save = input("Save this flight query to the database? (y/n): ").strip().lower()
    if save == "y":
        from src.db import get_db_connection
        from src.scraper import FlightDataFetcher
        from src.predict import load_model, predict_delay

        # Load model & encoders
        model, encoders = load_model("model/model.pkl")

        # Fetch the mock flight data
        mock_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_flights"))
        fetcher = FlightDataFetcher(mock_mode=True, mock_dir=mock_dir)
        flight_data = fetcher.get_flight_info(flight_number)

        if model and flight_data:
            delay_prediction = predict_delay(model, flight_data, encoders)
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO user_flights (flight_number, airline, predicted_delay_minutes)
                    VALUES (%s, %s, %s)
                """, (
                    flight_number,
                    flight_data.get("airline", "Unknown"),
                    round(delay_prediction, 2)
                ))
                conn.commit()
                conn.close()
                print("✅ Flight saved to database.")

if __name__ == "__main__":
    main()
