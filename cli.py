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

if __name__ == "__main__":
    main()
